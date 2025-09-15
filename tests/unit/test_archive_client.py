"""
档案系统HTTP客户端单元测试
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from httpx import Response, TimeoutException, ConnectError, HTTPStatusError
import httpx

from hydocpusher.client.archive_client import ArchiveClient
from hydocpusher.client.retry_handler import RetryExhaustedException
from hydocpusher.exceptions.custom_exceptions import (
    ArchiveClientException,
    ConfigurationException,
    ValidationException,
    ConnectionException
)
from hydocpusher.models.archive_models import ArchiveRequestSchema


class TestArchiveClient:
    """档案系统客户端测试类"""
    
    def test_init_default_values(self, monkeypatch):
        """测试默认初始化值"""
        # 直接使用自定义参数，不依赖环境变量
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        assert client.api_url == "http://test-api.com"
        assert client.timeout == 30.0  # 30000ms / 1000
        assert client.max_retries == 3
        assert client.auth_token == "test-token"
        assert client.app_id == "NEWS"
        assert client.company_name == "云南省能源投资集团有限公司"
    
    def test_init_custom_values(self):
        """测试自定义初始化值"""
        client = ArchiveClient(
            api_url="http://custom-api.com",
            timeout=15000,
            max_retries=5,
            auth_token="custom-token",
            app_id="CUSTOM_APP",
            company_name="Test Company"
        )
        
        assert client.api_url == "http://custom-api.com"
        assert client.timeout == 15.0  # 15000ms / 1000
        assert client.max_retries == 5
        assert client.auth_token == "custom-token"
        assert client.app_id == "CUSTOM_APP"
        assert client.company_name == "Test Company"
    
    def test_init_missing_required_config(self):
        """测试缺少必需配置"""
        # 测试空API URL - 应该使用默认值而不是抛出异常
        client = ArchiveClient(api_url="", auth_token="test-token")
        # 当传入空字符串时，应该使用配置中的默认值
        assert client.api_url == "http://localhost:8080"  # 配置中的默认值
        
        # 测试空认证令牌 - 应该使用默认值而不是抛出异常
        client = ArchiveClient(api_url="http://test.com", auth_token="")
        assert client.auth_token == "TmV3cytJbnRlcmZhY2U="  # 配置中的默认值
    
    def test_build_request_data(self):
        """测试构建请求数据"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        archive_data = {
            "did": "12345",
            "title": "Test Document",
            "author": "Test Author"
        }
        
        request_data = client._build_request_data(archive_data)
        
        assert request_data["AppId"] == "NEWS"
        assert request_data["AppToken"] == "test-token"
        assert request_data["CompanyName"] == "云南省能源投资集团有限公司"
        assert request_data["ArchiveType"] == "17"
        assert request_data["ArchiveData"] == archive_data
    
    def test_handle_response_success(self):
        """测试处理成功响应"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 200响应
        response = Response(200, json={"status": "success", "message": "Archive created"})
        result = client._handle_response(response)
        
        assert result["status"] == "success"
        assert result["message"] == "Archive created"
    
    def test_handle_response_success_no_json(self):
        """测试处理成功响应（非JSON）"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 200响应但内容不是JSON
        response = Response(200, text="Success")
        result = client._handle_response(response)
        
        assert result["status"] == "success"
        assert result["message"] == "Success"
    
    def test_handle_response_client_errors(self):
        """测试处理客户端错误响应"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 401认证失败
        response = Response(401, text="Unauthorized")
        with pytest.raises(ArchiveClientException) as exc_info:
            client._handle_response(response)
        assert "Authentication failed" in str(exc_info.value)
        
        # 403权限拒绝
        response = Response(403, text="Forbidden")
        with pytest.raises(ArchiveClientException) as exc_info:
            client._handle_response(response)
        assert "Permission denied" in str(exc_info.value)
        
        # 404未找到
        response = Response(404, text="Not Found")
        with pytest.raises(ArchiveClientException) as exc_info:
            client._handle_response(response)
        assert "endpoint not found" in str(exc_info.value).lower()
        
        # 422验证错误
        response = Response(422, text="Validation failed")
        with pytest.raises(ArchiveClientException) as exc_info:
            client._handle_response(response)
        assert "Validation error" in str(exc_info.value)
        
        # 其他4xx错误
        response = Response(400, text="Bad Request")
        with pytest.raises(ArchiveClientException) as exc_info:
            client._handle_response(response)
        assert "Client error 400" in str(exc_info.value)
    
    def test_handle_response_server_errors(self):
        """测试处理服务器错误响应"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 500服务器错误
        response = Response(500, text="Internal Server Error")
        with pytest.raises(ArchiveClientException) as exc_info:
            client._handle_response(response)
        assert "Server error 500" in str(exc_info.value)
        
        # 503服务不可用
        response = Response(503, text="Service Unavailable")
        with pytest.raises(ArchiveClientException) as exc_info:
            client._handle_response(response)
        assert "Server error 503" in str(exc_info.value)
    
    def test_handle_response_unexpected_status(self):
        """测试处理意外状态码"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 300重定向
        response = Response(300, text="Multiple Choices")
        with pytest.raises(ArchiveClientException) as exc_info:
            client._handle_response(response)
        assert "Unexpected status code 300" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_archive_data_async_success(self):
        """测试异步发送档案数据成功"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        archive_data = {
            "did": "12345",
            "title": "Test Document",
            "author": "Test Author"
        }
        
        # 模拟成功的HTTP响应
        mock_response = Response(200, json={"status": "success", "archive_id": "abc123"})
        
        with patch.object(client, '_ensure_async_client') as mock_ensure_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_ensure_client.return_value = mock_client
            
            result = await client.send_archive_data_async(archive_data)
            
            assert result["status"] == "success"
            assert result["archive_id"] == "abc123"
            mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_archive_data_async_with_schema(self):
        """测试异步发送档案数据（使用Schema）"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 使用ArchiveRequestSchema
        archive_schema = ArchiveRequestSchema(
            AppId="TEST_APP",
            AppToken="test-token",
            CompanyName="Test Company",
            ArchiveType="17",
            ArchiveData={
                "did": "12345",
                "title": "Test Document",
                "author": "Test Author"
            }
        )
        
        # 模拟成功的HTTP响应
        mock_response = Response(200, json={"status": "success", "archive_id": "abc123"})
        
        with patch.object(client, '_ensure_async_client') as mock_ensure_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_ensure_client.return_value = mock_client
            
            result = await client.send_archive_data_async(archive_schema)
            
            assert result["status"] == "success"
            assert result["archive_id"] == "abc123"
    
    @pytest.mark.asyncio
    async def test_send_archive_data_async_validation_error(self):
        """测试异步发送档案数据验证错误"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 使用无效的ArchiveRequestSchema数据（缺少必需字段）
        invalid_request_data = {
            "AppId": "TEST_APP",
            # 缺少其他必需字段如AppToken, CompanyName等
        }
        
        # 验证错误应该在构建ArchiveRequestSchema时发生，但由于我们修改了逻辑，
        # 现在字典数据会被当作ArchiveData处理，所以我们需要测试不同的场景
        # 让我们测试当ArchiveData字段本身无效时的情况
        invalid_archive_data = {
            "did": "",  # 空的did应该是无效的
            "title": "Test Document"
        }
        
        # 由于我们的逻辑现在将字典视为ArchiveData，验证应该在HTTP响应中处理
        # 让我们模拟一个422验证错误响应
        mock_response = Response(422, text="Validation failed: did cannot be empty")
        
        with patch.object(client, '_ensure_async_client') as mock_ensure_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_ensure_client.return_value = mock_client
            
            with pytest.raises(ArchiveClientException) as exc_info:
                await client.send_archive_data_async(invalid_archive_data)
            
            assert "Validation error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_archive_data_async_timeout(self):
        """测试异步发送档案数据超时"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        archive_data = {
            "did": "12345",
            "title": "Test Document"
        }
        
        with patch.object(client, '_ensure_async_client') as mock_ensure_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=TimeoutException("Request timeout"))
            mock_ensure_client.return_value = mock_client
            
            with pytest.raises(RetryExhaustedException) as exc_info:
                await client.send_archive_data_async(archive_data)
            
            # 验证原始异常是ConnectionException且包含timeout信息
            assert isinstance(exc_info.value.cause, ConnectionException)
            assert "timeout" in str(exc_info.value.cause).lower()
    
    @pytest.mark.asyncio
    async def test_send_archive_data_async_connection_error(self):
        """测试异步发送档案数据连接错误"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        archive_data = {
            "did": "12345",
            "title": "Test Document"
        }
        
        with patch.object(client, '_ensure_async_client') as mock_ensure_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=ConnectError("Connection failed"))
            mock_ensure_client.return_value = mock_client
            
            with pytest.raises(RetryExhaustedException) as exc_info:
                await client.send_archive_data_async(archive_data)
            
            # 验证原始异常是ConnectionException且包含连接失败信息
            assert isinstance(exc_info.value.cause, ConnectionException)
            assert "Failed to connect" in str(exc_info.value.cause)
    
    def test_send_archive_data_sync_success(self):
        """测试同步发送档案数据成功"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        archive_data = {
            "did": "12345",
            "title": "Test Document",
            "author": "Test Author"
        }
        
        # 模拟成功的HTTP响应
        mock_response = Response(200, json={"status": "success", "archive_id": "abc123"})
        
        with patch.object(client, '_ensure_sync_client') as mock_ensure_client:
            mock_client = Mock()
            mock_client.post = Mock(return_value=mock_response)
            mock_ensure_client.return_value = mock_client
            
            result = client.send_archive_data_sync(archive_data)
            
            assert result["status"] == "success"
            assert result["archive_id"] == "abc123"
            mock_client.post.assert_called_once()
    
    def test_send_archive_data_sync_validation_error(self):
        """测试同步发送档案数据验证错误"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 使用无效的ArchiveRequestSchema数据（缺少必需字段）
        invalid_request_data = {
            "AppId": "TEST_APP",
            # 缺少其他必需字段如AppToken, CompanyName等
        }
        
        # 验证错误应该在构建ArchiveRequestSchema时发生，但由于我们修改了逻辑，
        # 现在字典数据会被当作ArchiveData处理，所以我们需要测试不同的场景
        # 让我们测试当ArchiveData字段本身无效时的情况
        invalid_archive_data = {
            "did": "",  # 空的did应该是无效的
            "title": "Test Document"
        }
        
        # 由于我们的逻辑现在将字典视为ArchiveData，验证应该在HTTP响应中处理
        # 让我们模拟一个422验证错误响应
        mock_response = Response(422, text="Validation failed: did cannot be empty")
        
        with patch.object(client, '_ensure_sync_client') as mock_ensure_client:
            mock_client = Mock()
            mock_client.post = Mock(return_value=mock_response)
            mock_ensure_client.return_value = mock_client
            
            with pytest.raises(ArchiveClientException) as exc_info:
                client.send_archive_data_sync(invalid_archive_data)
            
            assert "Validation error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_archive_data_convenience_method(self):
        """测试便捷的异步发送方法"""
        archive_data = {
            "did": "12345",
            "title": "Test Document",
            "author": "Test Author"
        }
        
        # 模拟成功的HTTP响应
        mock_response = Response(200, json={"status": "success", "archive_id": "abc123"})
        
        with patch('hydocpusher.client.archive_client.ArchiveClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.send_archive_data = AsyncMock(return_value={"status": "success", "archive_id": "abc123"})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            from hydocpusher.client.archive_client import send_archive_data
            result = await send_archive_data(archive_data, api_url="http://test-api.com", auth_token="test-token")
            
            assert result["status"] == "success"
            assert result["archive_id"] == "abc123"
    
    def test_send_archive_data_sync_convenience_method(self):
        """测试便捷的同步发送方法"""
        archive_data = {
            "did": "12345",
            "title": "Test Document",
            "author": "Test Author"
        }
        
        # 模拟成功的HTTP响应
        mock_response = Response(200, json={"status": "success", "archive_id": "abc123"})
        
        with patch('hydocpusher.client.archive_client.ArchiveClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_archive_data_sync = Mock(return_value={"status": "success", "archive_id": "abc123"})
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client_class.return_value = mock_client
            
            from hydocpusher.client.archive_client import send_archive_data_sync
            result = send_archive_data_sync(archive_data, api_url="http://test-api.com", auth_token="test-token")
            
            assert result["status"] == "success"
            assert result["archive_id"] == "abc123"
    
    @pytest.mark.asyncio
    async def test_health_check_async_healthy(self):
        """测试异步健康检查：健康状态"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 模拟成功的HEAD响应
        mock_response = Response(200)
        
        with patch.object(client, '_ensure_async_client') as mock_ensure_client:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_ensure_client.return_value = mock_client
            
            result = await client.health_check_async()
            
            assert result["status"] == "healthy"
            assert result["api_url"] == "http://test-api.com"
            assert result["status_code"] == 200
    
    @pytest.mark.asyncio
    async def test_health_check_async_unhealthy(self):
        """测试异步健康检查：不健康状态"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 模拟服务器错误响应
        mock_response = Response(503, text="Service Unavailable")
        
        with patch.object(client, '_ensure_async_client') as mock_ensure_client:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_ensure_client.return_value = mock_client
            
            result = await client.health_check_async()
            
            assert result["status"] == "unhealthy"
            assert result["api_url"] == "http://test-api.com"
            assert result["status_code"] == 503
            assert "Server returned status 503" in result["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_async_connection_error(self):
        """测试异步健康检查：连接错误"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        with patch.object(client, '_ensure_async_client') as mock_ensure_client:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(side_effect=ConnectError("Connection failed"))
            mock_ensure_client.return_value = mock_client
            
            result = await client.health_check_async()
            
            assert result["status"] == "unhealthy"
            assert result["api_url"] == "http://test-api.com"
            assert "Connection failed" in result["error"]
    
    def test_health_check_sync_healthy(self):
        """测试同步健康检查：健康状态"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 模拟成功的HEAD响应
        mock_response = Response(200)
        
        with patch.object(client, '_ensure_sync_client') as mock_ensure_client:
            mock_client = Mock()
            mock_client.head = Mock(return_value=mock_response)
            mock_ensure_client.return_value = mock_client
            
            result = client.health_check_sync()
            
            assert result["status"] == "healthy"
            assert result["api_url"] == "http://test-api.com"
            assert result["status_code"] == 200
    
    @pytest.mark.asyncio
    async def test_context_manager_async(self):
        """测试异步上下文管理器"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        with patch.object(client, 'close_async') as mock_close:
            async with client:
                assert client._client is not None
            
            mock_close.assert_called_once()
    
    def test_context_manager_sync(self):
        """测试同步上下文管理器"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        with patch.object(client, 'close_sync') as mock_close:
            with client:
                assert client._sync_client is not None
            
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_async(self):
        """测试关闭异步客户端"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 先创建客户端
        client._ensure_async_client()
        assert client._client is not None
        
        # 关闭客户端
        await client.close_async()
        assert client._client.is_closed
    
    def test_close_sync(self):
        """测试关闭同步客户端"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 先创建客户端
        client._ensure_sync_client()
        assert client._sync_client is not None
        
        # 关闭客户端
        client.close_sync()
        assert client._sync_client.is_closed
    
    def test_ensure_client_headers(self):
        """测试客户端请求头设置"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token"
        )
        
        # 测试异步客户端
        async_client = client._ensure_async_client()
        assert async_client.headers["Content-Type"] == "application/json"
        assert async_client.headers["Authorization"] == "Bearer test-token"
        assert "HyDocPusher" in async_client.headers["User-Agent"]
        assert async_client.headers["Accept"] == "application/json"
        
        # 测试同步客户端
        sync_client = client._ensure_sync_client()
        assert sync_client.headers["Content-Type"] == "application/json"
        assert sync_client.headers["Authorization"] == "Bearer test-token"
        assert "HyDocPusher" in sync_client.headers["User-Agent"]
        assert sync_client.headers["Accept"] == "application/json"
    
    def test_retry_mechanism_integration(self):
        """测试重试机制集成"""
        client = ArchiveClient(
            api_url="http://test-api.com",
            auth_token="test-token",
            max_retries=2
        )
        
        archive_data = {
            "did": "12345",
            "title": "Test Document"
        }
        
        # 模拟连接错误（可重试），然后成功
        fail_exception = ConnectError("Connection failed")
        success_response = Response(200, json={"status": "success"})
        
        with patch.object(client, '_ensure_sync_client') as mock_ensure_client:
            mock_client = Mock()
            mock_client.post = Mock(side_effect=[fail_exception, success_response])
            mock_ensure_client.return_value = mock_client
            
            # 重试机制应该处理连接错误并最终成功
            result = client.send_archive_data_sync(archive_data)
            
            assert result["status"] == "success"
            # 验证调用了两次（初始尝试 + 1次重试）
            assert mock_client.post.call_count == 2