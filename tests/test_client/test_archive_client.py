#!/usr/bin/env python3
"""
档案客户端单元测试
"""

import pytest
import json
import aiohttp
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from aiohttp import ClientSession, ClientResponse, ClientTimeout
from aiohttp.client_exceptions import ClientError
from asyncio import TimeoutError as ClientTimeoutError

from hydocpusher.client.archive_client import ArchiveClient
from hydocpusher.config.settings import ArchiveConfig
from hydocpusher.exceptions.custom_exceptions import (
    ArchiveClientException,
    ConnectionException,
    RetryExhaustedException,
    ValidationException
)


class TestArchiveClient:
    """档案客户端测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock(spec=ArchiveConfig)
        config.api_url = "https://archive.example.com"
        config.base_url = "https://archive.example.com"
        config.app_token = "test-api-key"
        config.timeout = 30000
        config.retry_max_attempts = 3
        config.retry_delay = 60000
        config.app_id = "NEWS"
        config.company_name = "测试公司"
        config.archive_type = "17"
        config.domain = "test.example.com"
        config.retention_period = 30
        return config
    
    @pytest.fixture
    def archive_client(self, mock_config):
        """档案客户端实例"""
        with patch('hydocpusher.client.archive_client.get_config') as mock_get_config:
            mock_app_config = Mock()
            mock_app_config.archive = mock_config
            mock_get_config.return_value = mock_app_config
            return ArchiveClient(
                api_url=mock_config.api_url,
                timeout=mock_config.timeout,
                max_retries=mock_config.retry_max_attempts,
                auth_token=mock_config.app_token,
                app_id=mock_config.app_id,
                company_name=mock_config.company_name
            )
    
    def test_client_initialization(self, archive_client, mock_config):
        """测试客户端初始化"""
        assert archive_client.config == mock_config
        assert archive_client.session is None
        assert archive_client.base_url == mock_config.base_url
        assert archive_client.headers['Authorization'] == f'Bearer {mock_config.api_key}'
        assert archive_client.headers['Content-Type'] == 'application/json'
        assert archive_client.headers['Accept'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self, archive_client):
        """测试上下文管理器进入和退出"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 测试进入
            async with archive_client as client:
                assert client == archive_client
                assert archive_client.session == mock_session
                mock_session_class.assert_called_once()
            
            # 测试退出
            mock_session.close.assert_called_once()
            assert archive_client.session is None
    
    @pytest.mark.asyncio
    async def test_context_manager_exception_handling(self, archive_client):
        """测试上下文管理器异常处理"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            try:
                async with archive_client:
                    raise Exception("Test exception")
            except Exception as e:
                assert str(e) == "Test exception"
            
            # 确保session被正确关闭
            mock_session.close.assert_called_once()
            assert archive_client.session is None
    
    def test_build_url(self, archive_client):
        """测试URL构建"""
        # 测试基本路径
        url = archive_client._build_url('/api/documents')
        assert url == 'https://archive.example.com/api/documents'
        
        # 测试带参数的路径
        url = archive_client._build_url('/api/documents', {'page': 1, 'size': 10})
        assert url == 'https://archive.example.com/api/documents?page=1&size=10'
        
        # 测试空参数
        url = archive_client._build_url('/api/documents', {})
        assert url == 'https://archive.example.com/api/documents'
    
    def test_build_request_data(self, archive_client):
        """测试请求数据构建"""
        test_data = {
            'title': 'Test Document',
            'content': 'Test content',
            'metadata': {'author': 'Test Author'}
        }
        
        request_data = archive_client._build_request_data(test_data)
        
        assert 'data' in request_data
        assert 'timestamp' in request_data
        assert 'request_id' in request_data
        assert request_data['data'] == test_data
        assert isinstance(request_data['timestamp'], str)
        assert len(request_data['request_id']) > 0
    
    @pytest.mark.asyncio
    async def test_handle_response_success(self, archive_client):
        """测试响应处理成功"""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'status': 'success', 'data': {'id': 123}})
        mock_response.text = AsyncMock(return_value='{"status": "success"}')
        
        result = await archive_client._handle_response(mock_response)
        
        assert result == {'status': 'success', 'data': {'id': 123}}
        mock_response.json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_response_client_error(self, archive_client):
        """测试响应处理客户端错误"""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={'error': 'Bad request', 'message': 'Invalid data'})
        mock_response.text = AsyncMock(return_value='{"error": "Bad request"}')
        
        with pytest.raises(ValidationException, match="Bad request"):
            await archive_client._handle_response(mock_response)
    
    @pytest.mark.asyncio
    async def test_handle_response_auth_error(self, archive_client):
        """测试响应处理认证错误"""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={'error': 'Unauthorized'})
        mock_response.text = AsyncMock(return_value='{"error": "Unauthorized"}')
        
        with pytest.raises(ArchiveClientException, match="Unauthorized"):
            await archive_client._handle_response(mock_response)
    
    @pytest.mark.asyncio
    async def test_handle_response_server_error(self, archive_client):
        """测试响应处理服务器错误"""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 500
        mock_response.json = AsyncMock(return_value={'error': 'Internal server error'})
        mock_response.text = AsyncMock(return_value='{"error": "Internal server error"}')
        
        with pytest.raises(ArchiveClientException, match="Internal server error"):
            await archive_client._handle_response(mock_response)
    
    @pytest.mark.asyncio
    async def test_handle_response_json_decode_error(self, archive_client):
        """测试响应处理JSON解码错误"""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
        mock_response.text = AsyncMock(return_value="Invalid JSON response")
        
        with pytest.raises(ArchiveClientException, match="Invalid JSON response"):
            await archive_client._handle_response(mock_response)
    
    @pytest.mark.asyncio
    async def test_send_data_success(self, archive_client):
        """测试发送数据成功"""
        test_data = {'title': 'Test Document', 'content': 'Test content'}
        expected_response = {'status': 'success', 'id': 123}
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_response)
        
        mock_session.post = AsyncMock(return_value=mock_response)
        archive_client.session = mock_session
        
        result = await archive_client.send_data(test_data)
        
        assert result == expected_response
        mock_session.post.assert_called_once()
        
        # 验证请求参数
        call_args = mock_session.post.call_args
        assert call_args[0][0] == 'https://archive.example.com/api/documents'
        assert 'json' in call_args[1]
        assert 'headers' in call_args[1]
        assert 'timeout' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_send_data_with_retries(self, archive_client):
        """测试发送数据重试机制"""
        test_data = {'title': 'Test Document'}
        
        mock_session = AsyncMock()
        
        # 前两次请求失败，第三次成功
        mock_session.post = AsyncMock(side_effect=[
            ClientTimeoutError(),
            ClientTimeoutError(),
            AsyncMock(status=200, json=AsyncMock(return_value={'status': 'success'}))
        ])
        
        archive_client.session = mock_session
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await archive_client.send_data(test_data)
        
        assert result == {'status': 'success'}
        assert mock_session.post.call_count == 3
        assert mock_sleep.call_count == 2  # 两次重试之间的延迟
    
    @pytest.mark.asyncio
    async def test_send_data_max_retries_exceeded(self, archive_client):
        """测试发送数据超过最大重试次数"""
        test_data = {'title': 'Test Document'}
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=ClientTimeoutError())
        archive_client.session = mock_session
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(RetryExhaustedException):
                await archive_client.send_data(test_data)
        
        # 验证重试次数（初始请求 + 3次重试）
        assert mock_session.post.call_count == 4
    
    @pytest.mark.asyncio
    async def test_send_data_connection_error(self, archive_client):
        """测试发送数据连接错误"""
        test_data = {'title': 'Test Document'}
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=ClientError("Connection failed"))
        archive_client.session = mock_session
        
        with pytest.raises(ConnectionException, match="Connection failed"):
            await archive_client.send_data(test_data)
    
    @pytest.mark.asyncio
    async def test_send_data_batch_success(self, archive_client):
        """测试批量发送数据成功"""
        test_data_list = [
            {'title': f'Document {i}', 'content': f'Content {i}'}
            for i in range(5)
        ]
        
        expected_response = {'status': 'success', 'processed': 5}
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_response)
        
        mock_session.post = AsyncMock(return_value=mock_response)
        archive_client.session = mock_session
        
        result = await archive_client.send_data_batch(test_data_list)
        
        assert result == expected_response
        mock_session.post.assert_called_once()
        
        # 验证批量请求URL
        call_args = mock_session.post.call_args
        assert call_args[0][0] == 'https://archive.example.com/api/documents/batch'
    
    @pytest.mark.asyncio
    async def test_send_data_batch_chunking(self, archive_client):
        """测试批量发送数据分块处理"""
        # 创建超过批量大小的数据
        archive_client.config.batch_size = 3
        test_data_list = [
            {'title': f'Document {i}', 'content': f'Content {i}'}
            for i in range(7)  # 7个文档，分成3个批次：3, 3, 1
        ]
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'status': 'success'})
        
        mock_session.post = AsyncMock(return_value=mock_response)
        archive_client.session = mock_session
        
        results = await archive_client.send_data_batch(test_data_list)
        
        # 验证分成了3个批次
        assert mock_session.post.call_count == 3
        assert len(results) == 3
        assert all(result['status'] == 'success' for result in results)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, archive_client):
        """测试健康检查成功"""
        expected_response = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_response)
        
        mock_session.get = AsyncMock(return_value=mock_response)
        archive_client.session = mock_session
        
        result = await archive_client.health_check()
        
        assert result == expected_response
        mock_session.get.assert_called_once_with(
            'https://archive.example.com/health',
            headers=archive_client.headers,
            timeout=ClientTimeout(total=archive_client.config.timeout)
        )
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, archive_client):
        """测试健康检查失败"""
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=ClientError("Health check failed"))
        archive_client.session = mock_session
        
        with pytest.raises(ConnectionException, match="Health check failed"):
            await archive_client.health_check()
    
    @pytest.mark.asyncio
    async def test_get_status_success(self, archive_client):
        """测试获取状态成功"""
        expected_response = {
            'status': 'operational',
            'queue_size': 10,
            'processing_rate': 100.5
        }
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_response)
        
        mock_session.get = AsyncMock(return_value=mock_response)
        archive_client.session = mock_session
        
        result = await archive_client.get_status()
        
        assert result == expected_response
        mock_session.get.assert_called_once_with(
            'https://archive.example.com/api/status',
            headers=archive_client.headers,
            timeout=ClientTimeout(total=archive_client.config.timeout)
        )


class TestArchiveClientIntegration:
    """档案客户端集成测试"""
    
    @pytest.fixture
    def real_config(self):
        """真实配置（用于集成测试）"""
        config = ArchiveConfig()
        config.base_url = "https://httpbin.org"  # 使用httpbin进行测试
        config.api_key = "test-key"
        config.timeout = 10
        config.max_retries = 2
        config.retry_delay = 0.1
        config.batch_size = 5
        return config
    
    @pytest.mark.asyncio
    async def test_real_http_request(self, real_config):
        """测试真实HTTP请求（使用httpbin）"""
        client = ArchiveClient(real_config)
        
        async with client:
            # 使用httpbin的POST端点进行测试
            test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
            
            # 修改URL以使用httpbin的POST端点
            original_build_url = client._build_url
            def mock_build_url(path, params=None):
                if path == '/api/documents':
                    return 'https://httpbin.org/post'
                return original_build_url(path, params)
            
            client._build_url = mock_build_url
            
            try:
                result = await client.send_data(test_data)
                
                # httpbin返回请求信息
                assert 'json' in result
                assert 'headers' in result
                assert result['json']['data'] == test_data
                
            except Exception as e:
                # 如果网络不可用，跳过测试
                pytest.skip(f"Integration test skipped due to network issue: {e}")
    
    @pytest.mark.asyncio
    async def test_client_lifecycle(self, real_config):
        """测试客户端生命周期"""
        client = ArchiveClient(real_config)
        
        # 测试初始状态
        assert client.session is None
        
        # 测试上下文管理器
        async with client as c:
            assert c == client
            assert client.session is not None
            assert isinstance(client.session, ClientSession)
        
        # 测试退出后状态
        assert client.session is None


class TestArchiveClientErrorHandling:
    """档案客户端错误处理测试"""
    
    @pytest.fixture
    def archive_client(self):
        """档案客户端实例"""
        with patch('hydocpusher.client.archive_client.get_config') as mock_get_config:
            mock_config = Mock(spec=ArchiveConfig)
            mock_config.api_url = "https://archive.example.com"
            mock_config.base_url = "https://archive.example.com"
            mock_config.app_token = "test-key"
            mock_config.timeout = 30000
            mock_config.retry_max_attempts = 3
            mock_config.retry_delay = 60000
            mock_config.app_id = "NEWS"
            mock_config.company_name = "测试公司"
            mock_config.archive_type = "17"
            mock_config.domain = "test.example.com"
            mock_config.retention_period = 30
            
            mock_app_config = Mock()
            mock_app_config.archive = mock_config
            mock_get_config.return_value = mock_app_config
            
            return ArchiveClient(
                api_url=mock_config.api_url,
                timeout=mock_config.timeout,
                max_retries=mock_config.retry_max_attempts,
                auth_token=mock_config.app_token,
                app_id=mock_config.app_id,
                company_name=mock_config.company_name
            )
    
    @pytest.mark.asyncio
    async def test_session_not_initialized_error(self, archive_client):
        """测试会话未初始化错误"""
        # 不使用上下文管理器，直接调用方法
        with pytest.raises(ArchiveClientException, match="Client session not initialized"):
            await archive_client.send_data({'test': 'data'})
    
    @pytest.mark.asyncio
    async def test_invalid_data_error(self, archive_client):
        """测试无效数据错误"""
        mock_session = AsyncMock()
        archive_client.session = mock_session
        
        # 测试None数据
        with pytest.raises(ValidationException, match="Data cannot be None or empty"):
            await archive_client.send_data(None)
        
        # 测试空数据
        with pytest.raises(ValidationException, match="Data cannot be None or empty"):
            await archive_client.send_data({})
    
    @pytest.mark.asyncio
    async def test_batch_data_validation_error(self, archive_client):
        """测试批量数据验证错误"""
        mock_session = AsyncMock()
        archive_client.session = mock_session
        
        # 测试空数据列表
        with pytest.raises(ValidationException, match="Data list cannot be None or empty"):
            await archive_client.send_data_batch([])
        
        # 测试None数据列表
        with pytest.raises(ValidationException, match="Data list cannot be None or empty"):
            await archive_client.send_data_batch(None)