"""
档案系统HTTP客户端模块
负责与档案系统API进行HTTP通信，支持同步和异步调用
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
from pydantic import ValidationError

from ..config.settings import get_config
from ..exceptions.custom_exceptions import (
    ArchiveClientException,
    ConfigurationException,
    ValidationException,
    ConnectionException
)
from ..models.archive_models import ArchiveRequestSchema
from .retry_handler import RetryHandler, with_retry

logger = logging.getLogger(__name__)


class ArchiveClient:
    """档案系统HTTP客户端类"""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        auth_token: Optional[str] = None,
        app_id: Optional[str] = None,
        company_name: Optional[str] = None
    ):
        """
        初始化档案系统客户端
        
        Args:
            api_url: 档案系统API地址
            timeout: 请求超时时间（毫秒）
            max_retries: 最大重试次数
            auth_token: 认证令牌
            app_id: 应用ID
            company_name: 公司名称
        """
        self.config = get_config()
        
        # 使用提供的参数或配置值
        self.api_url = api_url or self.config.archive.api_url
        self.timeout = (timeout or self.config.archive.timeout) / 1000.0  # 转换为秒
        self.max_retries = max_retries or self.config.archive.retry_max_attempts
        self.auth_token = auth_token or self.config.archive.app_token
        self.app_id = app_id or self.config.archive.app_id
        self.company_name = company_name or self.config.archive.company_name
        
        # 验证必需配置
        if not self.api_url:
            raise ConfigurationException("Archive API URL is required")
        if not self.auth_token:
            raise ConfigurationException("Archive API authentication token is required")
        
        # 初始化HTTP客户端
        self._client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None
        self.session: Optional[httpx.AsyncClient] = None  # 添加session属性用于测试兼容性
        
        # 初始化重试处理器
        self.retry_handler = RetryHandler(
            max_attempts=self.max_retries,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        logger.info(f"ArchiveClient initialized with API URL: {self.api_url}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._ensure_async_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_async()
    
    def __enter__(self):
        """同步上下文管理器入口"""
        self._ensure_sync_client()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self.close_sync()
    
    def _ensure_async_client(self) -> httpx.AsyncClient:
        """确保异步HTTP客户端已创建"""
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(
                connect=self.timeout,
                read=self.timeout,
                write=self.timeout,
                pool=self.timeout
            )
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}",
                "User-Agent": f"HyDocPusher/1.0.0",
                "Accept": "application/json"
            }
            
            self._client = httpx.AsyncClient(
                timeout=timeout,
                headers=headers,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30
                ),
                trust_env=False  # 禁用环境代理设置
            )
        
        return self._client
    
    def _ensure_sync_client(self) -> httpx.Client:
        """确保同步HTTP客户端已创建"""
        if self._sync_client is None or self._sync_client.is_closed:
            timeout = httpx.Timeout(
                connect=self.timeout,
                read=self.timeout,
                write=self.timeout,
                pool=self.timeout
            )
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}",
                "User-Agent": f"HyDocPusher/1.0.0",
                "Accept": "application/json"
            }
            
            self._sync_client = httpx.Client(
                timeout=timeout,
                headers=headers,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30
                ),
                trust_env=False  # 禁用环境代理设置
            )
        
        return self._sync_client
    
    def _build_request_data(self, archive_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建请求数据
        
        Args:
            archive_data: 档案数据（内部数据字段）
            
        Returns:
            完整的请求数据
        """
        return {
            "AppId": self.app_id,
            "AppToken": self.auth_token,
            "CompanyName": self.company_name,
            "ArchiveType": self.config.archive.archive_type,
            "ArchiveData": archive_data
        }
    
    def _handle_response(self, response) -> Dict[str, Any]:
        """
        处理HTTP响应（支持httpx.Response和aiohttp.ClientResponse）
        
        Args:
            response: HTTP响应对象
            
        Returns:
            响应数据
            
        Raises:
            ArchiveClientException: 处理响应错误
        """
        # 获取状态码（兼容不同的响应对象）
        status_code = getattr(response, 'status_code', None) or getattr(response, 'status', None)
        
        # 获取响应头（兼容不同的响应对象）
        headers = getattr(response, 'headers', {})
        
        # 获取响应内容长度
        content = getattr(response, 'content', None)
        content_length = len(content) if content else 0
        
        # 记录响应信息
        logger.debug(
            f"Received response: status={status_code}, "
            f"headers={dict(headers) if headers else {}}, "
            f"content_length={content_length}"
        )
        
        # 成功响应
        if 200 <= status_code < 300:
            try:
                # 兼容不同响应对象的json方法
                if hasattr(response, 'json') and callable(response.json):
                    if asyncio.iscoroutinefunction(response.json):
                        # aiohttp.ClientResponse需要await
                        response_data = asyncio.create_task(response.json())
                    else:
                        # httpx.Response直接调用
                        response_data = response.json()
                else:
                    raise AttributeError("Response object has no json method")
                logger.info(f"Archive request successful: {status_code}")
                return response_data
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse response JSON: {e}")
                # 获取响应文本（兼容不同的响应对象）
                text = getattr(response, 'text', '') or str(response)
                return {"status": "success", "message": text}
        
        # 获取错误响应文本
        error_text = getattr(response, 'text', '') or str(response)
        
        # 客户端错误（4xx）
        if 400 <= status_code < 500:
            error_message = f"Client error {status_code}: {error_text}"
            logger.error(error_message)
            
            if status_code == 401:
                raise ArchiveClientException("Authentication failed - invalid token")
            elif status_code == 403:
                raise ArchiveClientException("Permission denied")
            elif status_code == 404:
                raise ArchiveClientException("Archive API endpoint not found")
            elif status_code == 422:
                raise ArchiveClientException(f"Validation error: {error_text}")
            else:
                raise ArchiveClientException(error_message)
        
        # 服务器错误（5xx）
        elif status_code >= 500:
            error_message = f"Server error {status_code}: {error_text}"
            logger.error(error_message)
            raise ArchiveClientException(error_message)
        
        # 其他状态码
        else:
            error_message = f"Unexpected status code {status_code}: {error_text}"
            logger.error(error_message)
            raise ArchiveClientException(error_message)
    
    @with_retry(max_attempts=3, base_delay=1.0)
    async def send_archive_data_async(
        self,
        archive_data: Union[Dict[str, Any], ArchiveRequestSchema]
    ) -> Dict[str, Any]:
        """
        异步发送档案数据
        
        Args:
            archive_data: 档案数据（字典或ArchiveRequestSchema实例）
            
        Returns:
            档案系统响应数据
            
        Raises:
            ArchiveClientException: 档案系统调用失败
            ValidationException: 数据验证失败
        """
        try:
            # 验证和序列化数据
            if isinstance(archive_data, ArchiveRequestSchema):
                request_data = archive_data.model_dump()
            else:
                # 如果传入的是普通字典，将其作为ArchiveData构建完整请求
                request_data = self._build_request_data(archive_data)
            
            logger.info(f"Sending archive data to {self.api_url}")
            logger.debug(f"Request data: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            
            # 确保客户端已创建
            client = self._ensure_async_client()
            
            # 发送请求
            response = await client.post(
                self.api_url,
                json=request_data
            )
            
            # 处理响应
            return self._handle_response(response)
            
        except ValidationError as e:
            logger.error(f"Validation error in archive data: {e}")
            raise ValidationException(f"Invalid archive data: {e}")
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise ConnectionException(f"Archive API request timeout: {e}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionException(f"Failed to connect to archive API: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            raise ArchiveClientException(f"Archive API returned error status: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending archive data: {e}")
            if isinstance(e, ArchiveClientException):
                raise e
            raise ArchiveClientException(f"Failed to send archive data: {e}")
    
    @with_retry(max_attempts=3, base_delay=1.0)
    def send_archive_data_sync(
        self,
        archive_data: Union[Dict[str, Any], ArchiveRequestSchema]
    ) -> Dict[str, Any]:
        """
        同步发送档案数据
        
        Args:
            archive_data: 档案数据（字典或ArchiveRequestSchema实例）
            
        Returns:
            档案系统响应数据
            
        Raises:
            ArchiveClientException: 档案系统调用失败
            ValidationException: 数据验证失败
        """
        try:
            # 验证和序列化数据
            if isinstance(archive_data, ArchiveRequestSchema):
                request_data = archive_data.model_dump()
            else:
                # 如果传入的是普通字典，将其作为ArchiveData构建完整请求
                request_data = self._build_request_data(archive_data)
            
            logger.info(f"Sending archive data to {self.api_url}")
            logger.debug(f"Request data: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            
            # 确保客户端已创建
            client = self._ensure_sync_client()
            
            # 发送请求
            response = client.post(
                self.api_url,
                json=request_data
            )
            
            # 处理响应
            return self._handle_response(response)
            
        except ValidationError as e:
            logger.error(f"Validation error in archive data: {e}")
            raise ValidationException(f"Invalid archive data: {e}")
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise ConnectionException(f"Archive API request timeout: {e}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionException(f"Failed to connect to archive API: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            raise ArchiveClientException(f"Archive API returned error status: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending archive data: {e}")
            if isinstance(e, ArchiveClientException):
                raise e
            raise ArchiveClientException(f"Failed to send archive data: {e}")
    
    # 便捷方法，默认使用异步版本
    async def send_archive_data(
        self,
        archive_data: Union[Dict[str, Any], ArchiveRequestSchema]
    ) -> Dict[str, Any]:
        """
        发送档案数据（异步版本，推荐）
        
        Args:
            archive_data: 档案数据
            
        Returns:
            档案系统响应数据
        """
        return await self.send_archive_data_async(archive_data)
    
    async def close_async(self) -> None:
        """关闭异步HTTP客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("Async HTTP client closed")
    
    def close_sync(self) -> None:
        """关闭同步HTTP客户端"""
        if self._sync_client and not self._sync_client.is_closed:
            self._sync_client.close()
            logger.debug("Sync HTTP client closed")
    
    async def health_check_async(self) -> Dict[str, Any]:
        """
        异步健康检查
        
        Returns:
            健康检查结果
        """
        try:
            client = self._ensure_async_client()
            
            # 尝试发送一个简单的HEAD请求
            response = await client.head(self.api_url)
            
            if response.status_code < 500:  # 服务器错误才认为不健康
                return {
                    "status": "healthy",
                    "api_url": self.api_url,
                    "status_code": response.status_code
                }
            else:
                return {
                    "status": "unhealthy",
                    "api_url": self.api_url,
                    "status_code": response.status_code,
                    "error": f"Server returned status {response.status_code}"
                }
                
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "api_url": self.api_url,
                "error": str(e)
            }
    
    def health_check_sync(self) -> Dict[str, Any]:
        """
        同步健康检查
        
        Returns:
            健康检查结果
        """
        try:
            client = self._ensure_sync_client()
            
            # 尝试发送一个简单的HEAD请求
            response = client.head(self.api_url)
            
            if response.status_code < 500:  # 服务器错误才认为不健康
                return {
                    "status": "healthy",
                    "api_url": self.api_url,
                    "status_code": response.status_code
                }
            else:
                return {
                    "status": "unhealthy",
                    "api_url": self.api_url,
                    "status_code": response.status_code,
                    "error": f"Server returned status {response.status_code}"
                }
                
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "api_url": self.api_url,
                "error": str(e)
            }
    
    def _build_url(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """构建完整的API URL"""
        base_url = self.api_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"
    
    async def send_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送数据（测试兼容性方法）"""
        return await self.send_archive_data(data)
    
    async def send_data_batch(self, data_list: list) -> Dict[str, Any]:
        """批量发送数据"""
        if not data_list:
            raise ValidationException("Data list cannot be empty")
        
        results = []
        for data in data_list:
            result = await self.send_data(data)
            results.append(result)
        
        return {
            "status": "success",
            "batch_size": len(data_list),
            "results": results
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查（测试兼容性方法）"""
        return await self.health_check_async()
    
    async def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "status": "active",
            "api_url": self.api_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }


# 便捷函数
async def send_archive_data(
    archive_data: Union[Dict[str, Any], ArchiveRequestSchema],
    **kwargs
) -> Dict[str, Any]:
    """
    便捷函数：异步发送档案数据
    
    Args:
        archive_data: 档案数据
        **kwargs: 其他参数传递给ArchiveClient
        
    Returns:
        档案系统响应数据
    """
    async with ArchiveClient(**kwargs) as client:
        return await client.send_archive_data(archive_data)


def send_archive_data_sync(
    archive_data: Union[Dict[str, Any], ArchiveRequestSchema],
    **kwargs
) -> Dict[str, Any]:
    """
    便捷函数：同步发送档案数据
    
    Args:
        archive_data: 档案数据
        **kwargs: 其他参数传递给ArchiveClient
        
    Returns:
        档案系统响应数据
    """
    with ArchiveClient(**kwargs) as client:
        return client.send_archive_data_sync(archive_data)