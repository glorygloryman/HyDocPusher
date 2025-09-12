"""
死信队列管理类测试
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from hydocpusher.consumer.dead_letter_queue import DeadLetterQueue, DeadLetterMessage
from hydocpusher.config.settings import AppConfig
from hydocpusher.exceptions.custom_exceptions import MessageProcessException


class TestDeadLetterQueue:
    """死信队列测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        config = Mock(spec=AppConfig)
        
        # 创建模拟的Pulsar配置
        mock_pulsar_config = Mock()
        mock_pulsar_config.cluster_url = "pulsar://localhost:6650"
        mock_pulsar_config.dead_letter_topic = "persistent://public/default/hydocpusher-dlq"
        
        config.pulsar = mock_pulsar_config
        config.app_name = "HyDocPusher"
        config.app_version = "1.0.0"
        return config
    
    @pytest.fixture
    def mock_pulsar_client(self):
        """创建模拟Pulsar客户端"""
        client = Mock()
        return client
    
    @pytest.fixture
    def mock_pulsar_producer(self):
        """创建模拟Pulsar生产者"""
        producer = Mock()
        return producer
    
    @pytest.fixture
    def dlq_manager(self, mock_config):
        """创建死信队列管理器实例"""
        return DeadLetterQueue(mock_config)
    
    @pytest.fixture
    def sample_message_data(self):
        """示例消息数据"""
        return {
            "MSG": "操作成功",
            "DATA": {
                "DOCID": "64941",
                "SITENAME": "测试推送",
                "CRTIME": "2025-08-29 18:53:15",
                "CHANNELID": "2240"
            },
            "ISSUCCESS": "true"
        }
    
    @pytest.mark.asyncio
    async def test_initialization_with_existing_client(self, mock_config, mock_pulsar_client):
        """测试使用现有客户端初始化"""
        dlq_manager = DeadLetterQueue(mock_config, client=mock_pulsar_client)
        
        with patch.object(mock_pulsar_client, 'create_producer') as mock_create_producer:
            mock_producer = Mock()
            mock_create_producer.return_value = mock_producer
            
            await dlq_manager.initialize()
            
            mock_create_producer.assert_called_once()
            assert dlq_manager._producer == mock_producer
            assert dlq_manager._client == mock_pulsar_client
            assert not dlq_manager._own_client
    
    @pytest.mark.asyncio
    async def test_initialization_without_client(self, mock_config):
        """测试无客户端时初始化"""
        dlq_manager = DeadLetterQueue(mock_config)
        
        with patch('pulsar.Client') as mock_client_class:
            mock_client = Mock()
            mock_producer = Mock()
            mock_client.create_producer.return_value = mock_producer
            mock_client_class.return_value = mock_client
            
            await dlq_manager.initialize()
            
            mock_client_class.assert_called_once_with(
                service_url=mock_config.pulsar.cluster_url,
                operation_timeout_seconds=30,
                connection_timeout_ms=10000
            )
            
            mock_client.create_producer.assert_called_once_with(
                topic=mock_config.pulsar.dead_letter_topic,
                producer_name=f"{mock_config.app_name}-dlq-producer",
                batching_enabled=True,
                batching_max_publish_delay_ms=10,
                compression_type=pulsar.CompressionType.LZ4
            )
            
            assert dlq_manager._producer == mock_producer
            assert dlq_manager._client == mock_client
            assert dlq_manager._own_client
    
    @pytest.mark.asyncio
    async def test_send_to_dlq_success(self, dlq_manager, sample_message_data):
        """测试成功发送消息到死信队列"""
        # 设置生产者
        mock_producer = Mock()
        dlq_manager._producer = mock_producer
        
        # 创建异常
        error = MessageProcessException("Test error")
        
        # 发送消息到DLQ
        await dlq_manager.send_to_dlq(
            original_message=sample_message_data,
            error=error,
            retry_count=2,
            additional_context={"test": "context"}
        )
        
        # 验证生产者被调用
        assert mock_producer.send.called
        
        # 获取发送的消息内容
        call_args = mock_producer.send.call_args
        message_data = call_args[0][0].decode('utf-8')
        message_properties = call_args[1]['properties']
        
        # 解析消息数据
        dlq_message = json.loads(message_data)
        
        # 验证消息内容
        assert dlq_message["message_id"] == "64941"
        assert dlq_message["original_message"] == sample_message_data
        assert dlq_message["error"]["type"] == "MessageProcessException"
        assert "Test error" in dlq_message["error"]["message"]
        assert dlq_message["retry_count"] == 2
        assert dlq_message["context"] == {"test": "context"}
        assert "application" in dlq_message
        
        # 验证消息属性
        assert message_properties["original_topic"] == dlq_manager.config.pulsar.topic
        assert message_properties["error_type"] == "MessageProcessException"
        assert message_properties["retry_count"] == "2"
        assert "timestamp" in message_properties
    
    @pytest.mark.asyncio
    async def test_send_to_dlq_without_producer(self, dlq_manager, sample_message_data):
        """测试无生产者时发送消息到DLQ"""
        error = MessageProcessException("Test error")
        
        # 不应该抛出异常，只是记录警告
        await dlq_manager.send_to_dlq(
            original_message=sample_message_data,
            error=error,
            retry_count=1
        )
    
    @pytest.mark.asyncio
    async def test_send_to_dlq_with_send_failure(self, dlq_manager, sample_message_data):
        """测试发送失败的情况"""
        # 设置生产者，模拟发送失败
        mock_producer = Mock()
        mock_producer.send.side_effect = Exception("Send failed")
        dlq_manager._producer = mock_producer
        
        error = MessageProcessException("Test error")
        
        with pytest.raises(MessageProcessException) as exc_info:
            await dlq_manager.send_to_dlq(
                original_message=sample_message_data,
                error=error,
                retry_count=1
            )
        
        assert "Failed to send message to dead letter queue" in str(exc_info.value)
    
    def test_build_dlq_message_with_exception_error_code(self, mock_config):
        """测试构建带有错误码的死信消息"""
        dlq_manager = DeadLetterQueue(mock_config)
        
        original_message = {"DATA": {"DOCID": "12345"}}
        error = MessageProcessException("Test error with code")
        error.error_code = "TEST_ERROR"
        
        dlq_message = dlq_manager._build_dlq_message(
            original_message=original_message,
            error=error,
            retry_count=3,
            additional_context=None
        )
        
        assert dlq_message["error"]["error_code"] == "TEST_ERROR"
    
    def test_build_dlq_message_with_complex_original_message(self, mock_config):
        """测试构建复杂原始消息的死信消息"""
        dlq_manager = DeadLetterQueue(mock_config)
        
        # 复杂的原始消息结构
        original_message = {
            "MSG": "操作失败",
            "DATA": {
                "nested": {
                    "DOCID": "complex_id"
                }
            }
        }
        error = Exception("Complex error")
        
        dlq_message = dlq_manager._build_dlq_message(
            original_message=original_message,
            error=error,
            retry_count=0,
            additional_context={"extra": "data"}
        )
        
        assert dlq_message["message_id"] == "unknown"  # 无法解析的复杂结构
        assert dlq_message["original_message"] == original_message
        assert dlq_message["context"] == {"extra": "data"}
    
    @pytest.mark.asyncio
    async def test_get_dlq_stats(self, mock_config):
        """测试获取死信队列统计信息"""
        dlq_manager = DeadLetterQueue(mock_config)
        
        # 设置生产者
        mock_producer = Mock()
        dlq_manager._producer = mock_producer
        
        stats = await dlq_manager.get_dlq_stats()
        
        assert stats["topic"] == mock_config.pulsar.dead_letter_topic
        assert stats["initialized"] is True
        assert stats["producer_connected"] is True
        
        # 测试未初始化的情况
        dlq_manager._producer = None
        stats = await dlq_manager.get_dlq_stats()
        
        assert stats["initialized"] is False
        assert stats["producer_connected"] is False
    
    @pytest.mark.asyncio
    async def test_close_with_own_client(self, mock_config):
        """测试关闭拥有自己的客户端"""
        dlq_manager = DeadLetterQueue(mock_config)
        
        # 设置模拟对象
        mock_producer = Mock()
        mock_client = Mock()
        
        dlq_manager._producer = mock_producer
        dlq_manager._client = mock_client
        dlq_manager._own_client = True
        
        await dlq_manager.close()
        
        # 验证关闭调用
        mock_producer.close.assert_called_once()
        mock_client.close.assert_called_once()
        
        assert dlq_manager._producer is None
        assert dlq_manager._client is None
    
    @pytest.mark.asyncio
    async def test_close_with_external_client(self, mock_config, mock_pulsar_client):
        """测试关闭使用外部客户端"""
        dlq_manager = DeadLetterQueue(mock_config, client=mock_pulsar_client)
        
        # 设置模拟对象
        mock_producer = Mock()
        dlq_manager._producer = mock_producer
        dlq_manager._own_client = False
        
        await dlq_manager.close()
        
        # 验证只关闭生产者，不关闭客户端
        mock_producer.close.assert_called_once()
        assert dlq_manager._producer is None
        # 客户端不应该被关闭
        mock_pulsar_client.close.assert_not_called()


class TestDeadLetterMessage:
    """死信消息模型测试类"""
    
    def test_dead_letter_message_initialization(self):
        """测试死信消息初始化"""
        original_message = {"test": "data"}
        error_type = "ValidationException"
        error_message = "Invalid message format"
        retry_count = 3
        
        dlq_message = DeadLetterMessage(
            message_id="12345",
            original_message=original_message,
            error_type=error_type,
            error_message=error_message,
            retry_count=retry_count
        )
        
        assert dlq_message.message_id == "12345"
        assert dlq_message.original_message == original_message
        assert dlq_message.error_type == error_type
        assert dlq_message.error_message == error_message
        assert dlq_message.retry_count == retry_count
        assert isinstance(dlq_message.timestamp, datetime)
    
    def test_dead_letter_message_with_custom_timestamp(self):
        """测试使用自定义时间戳的死信消息"""
        custom_timestamp = datetime(2025, 1, 1, 12, 0, 0)
        
        dlq_message = DeadLetterMessage(
            message_id="12345",
            original_message={},
            error_type="TestError",
            error_message="Test message",
            timestamp=custom_timestamp
        )
        
        assert dlq_message.timestamp == custom_timestamp
    
    def test_dead_letter_message_to_dict(self):
        """测试死信消息转换为字典"""
        original_message = {"DATA": {"DOCID": "12345"}}
        error_type = "TestException"
        error_message = "Test error message"
        retry_count = 2
        
        dlq_message = DeadLetterMessage(
            message_id="12345",
            original_message=original_message,
            error_type=error_type,
            error_message=error_message,
            retry_count=retry_count
        )
        
        result_dict = dlq_message.to_dict()
        
        assert result_dict["message_id"] == "12345"
        assert result_dict["original_message"] == original_message
        assert result_dict["error_type"] == error_type
        assert result_dict["error_message"] == error_message
        assert result_dict["retry_count"] == retry_count
        assert "timestamp" in result_dict
        assert isinstance(result_dict["timestamp"], str)