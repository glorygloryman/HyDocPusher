"""
Pulsar消费者类测试
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, Any

import pulsar

from hydocpusher.consumer.pulsar_consumer import PulsarConsumer
from hydocpusher.config.settings import AppConfig
from hydocpusher.exceptions.custom_exceptions import ConnectionException, MessageProcessException


class TestPulsarConsumer:
    """Pulsar消费者测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        config = Mock(spec=AppConfig)
        
        # 创建模拟的Pulsar配置
        mock_pulsar_config = Mock()
        mock_pulsar_config.cluster_url = "pulsar://localhost:6650"
        mock_pulsar_config.topic = "persistent://public/default/content-publish"
        mock_pulsar_config.subscription = "hydocpusher-subscription"
        mock_pulsar_config.dead_letter_topic = "persistent://public/default/hydocpusher-dlq"
        
        config.pulsar = mock_pulsar_config
        config.app_name = "HyDocPusher"
        config.app_version = "1.0.0"
        return config
    
    @pytest.fixture
    def pulsar_consumer(self, mock_config):
        """创建Pulsar消费者实例"""
        return PulsarConsumer(mock_config)
    
    @pytest.fixture
    def sample_message_data(self):
        """示例消息数据"""
        return {
            "MSG": "操作成功",
            "DATA": {
                "SITENAME": "测试推送",
                "CRTIME": "2025-08-29 18:53:15",
                "CHANNELID": "2240",
                "VIEWID": "11",
                "VIEWNAME": "GovDocNewsAPP",
                "SITEID": "33",
                "DOCID": "64941",
                "OPERTYPE": "1",
                "CHANNELNAV": "2240",
                "DATA": {
                    "DOCTYPE": "20",
                    "LISTTITLE": "测试 裸眼3D看云能",
                    "SITENAME": "测试推送",
                    "DOCHTMLCON": "<div>测试内容</div>",
                    "CRUSER": "dev",
                    "DOCUMENT_DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCTITLE": "裸眼3D看云能",
                    "TXY": "集团党群部",
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html",
                    "CLASSIFICATIONID": "6",
                    "ORIGINMETADATAID": "61261",
                    "SITEID": "33",
                    "CHNLDESC": "数字能投推送测试",
                    "PUBSTATUS": "1",
                    "MODAL": "1",
                    "CHNLNAME": "新闻头条_2240",
                    "DOCABSTRACT": "",
                    "WCMMETATABLEGOVDOCNEWSAPPID": "68",
                    "WEBHTTP": "https://www.cnyeig.com/csts"
                },
                "CHNLDOC": {
                    "DOCTYPE": "20",
                    "DOCFIRSTPUBTIME": "2025-08-29 18:54:06",
                    "DOCORDER": "34",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "DOCCHANNEL": "2240",
                    "CRUSER": "dev",
                    "CRTIME": "2025-08-29 18:53:15",
                    "OPERTIME": "2025-08-29 18:54:06",
                    "DOCPUBTIME": "2025-08-29 18:54:06",
                    "DOCSTATUS": "10",
                    "CRDEPT": "云南省能源投资集团有限公司~云南能投信息产业开发有限公司~",
                    "DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCID": "64941",
                    "CHNLID": "2240",
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html",
                    "ACTIONUSER": "dev",
                    "DOCOUTUPID": "61261",
                    "DOCKIND": "11",
                    "SITEID": "33",
                    "PUBSTATUS": "1",
                    "MODAL": "1"
                },
                "CRUSER": "dev",
                "APPENDIX": [{
                    "APPFILE": "/masvod/public/2025/04/09/20250409_196198623cd_r1_1200k.mp4",
                    "APPFLAG": "50"
                }],
                "ID": "84085",
                "CHANNELDESCNAV": "数字能投推送测试",
                "TYPE": "1"
            },
            "ISSUCCESS": "true"
        }
    
    @pytest.mark.asyncio
    async def test_successful_connection(self, pulsar_consumer, mock_config):
        """测试成功连接到Pulsar"""
        with patch('pulsar.Client') as mock_client_class:
            # 设置模拟客户端
            mock_client = Mock()
            mock_consumer = Mock()
            mock_client.subscribe.return_value = mock_consumer
            mock_client_class.return_value = mock_client
            
            # 执行连接
            await pulsar_consumer.connect()
            
            # 验证调用
            mock_client_class.assert_called_once()
            call_args = mock_client_class.call_args
            assert call_args.kwargs['service_url'] == mock_config.pulsar.cluster_url
            assert call_args.kwargs['operation_timeout_seconds'] == 30
            assert call_args.kwargs['connection_timeout_ms'] == 10000
            assert call_args.kwargs['authentication'] is None
            
            mock_client.subscribe.assert_called_once_with(
                topic=mock_config.pulsar.topic,
                subscription_name=mock_config.pulsar.subscription,
                consumer_type=pulsar.ConsumerType.Shared,
                initial_position=pulsar.InitialPosition.Earliest,
                negative_ack_redelivery_delay_ms=60000,
                ack_timeout_ms=300000,
                max_total_receiver_queue_size_across_partitions=50000
            )
            
            assert pulsar_consumer.is_connected
    
    @pytest.mark.asyncio
    async def test_connection_failure_with_retry(self, pulsar_consumer, mock_config):
        """测试连接失败后的重试逻辑"""
        with patch('pulsar.Client') as mock_client_class:
            # 模拟连接失败
            mock_client_class.side_effect = Exception("Connection failed")
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                with pytest.raises(ConnectionException) as exc_info:
                    await pulsar_consumer.connect()
                
                # 验证重试次数
                assert mock_client_class.call_count == 3  # 最大重试次数
                assert mock_sleep.call_count == 2  # 重试间隔等待
                
                assert "Failed to connect to Pulsar after 3 attempts" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_start_consuming_success(self, pulsar_consumer, mock_config):
        """测试开始消费消息"""
        with patch.object(pulsar_consumer, '_consumer') as mock_consumer:
            # 模拟消息接收
            mock_message = Mock()
            mock_message.message_id.return_value = "test-message-id"
            mock_message.data.return_value = json.dumps({"test": "data"}).encode('utf-8')
            
            # 设置receive方法返回消息
            mock_consumer.receive.side_effect = [
                mock_message,
                pulsar.Timeout()  # 第二次调用超时
            ]
            
            # 设置消息处理器
            mock_handler = AsyncMock()
            pulsar_consumer.set_message_handler(mock_handler)
            
            # 运行消费循环（将在超时后停止）
            with patch.object(pulsar_consumer, '_running', side_effect=[True, False]):
                await pulsar_consumer.start_consuming()
            
            # 验证消息处理
            mock_handler.assert_called_once()
            mock_consumer.acknowledge.assert_called_once_with(mock_message)
    
    @pytest.mark.asyncio
    async def test_message_parsing_success(self, pulsar_consumer):
        """测试成功解析消息"""
        # 创建模拟消息
        mock_message = Mock()
        mock_message.message_id.return_value = "test-message-id"
        
        sample_data = {"MSG": "test", "DATA": {"test": "data"}, "ISSUCCESS": "true"}
        mock_message.data.return_value = json.dumps(sample_data).encode('utf-8')
        
        # 解析消息
        result = pulsar_consumer._parse_message(mock_message)
        
        assert result == sample_data
    
    @pytest.mark.asyncio
    async def test_message_parsing_invalid_json(self, pulsar_consumer):
        """测试解析无效JSON消息"""
        # 创建模拟消息
        mock_message = Mock()
        mock_message.message_id.return_value = "test-message-id"
        mock_message.data.return_value = b"invalid json"
        
        # 解析消息
        result = pulsar_consumer._parse_message(mock_message)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_message_parsing_empty_data(self, pulsar_consumer):
        """测试解析空数据消息"""
        # 创建模拟消息
        mock_message = Mock()
        mock_message.message_id.return_value = "test-message-id"
        mock_message.data.return_value = b""
        
        # 解析消息
        result = pulsar_consumer._parse_message(mock_message)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_message_processing_with_handler(self, pulsar_consumer, sample_message_data):
        """测试使用消息处理器处理消息"""
        # 创建模拟消息
        mock_message = Mock()
        mock_message.message_id.return_value = "test-message-id"
        mock_message.data.return_value = json.dumps(sample_message_data).encode('utf-8')
        
        # 设置消息处理器
        mock_handler = AsyncMock()
        pulsar_consumer.set_message_handler(mock_handler)
        
        # 处理消息
        await pulsar_consumer._process_message(mock_message)
        
        # 验证处理
        mock_handler.assert_called_once_with(sample_message_data)
        pulsar_consumer._consumer.acknowledge.assert_called_once_with(mock_message)
    
    @pytest.mark.asyncio
    async def test_message_processing_without_handler(self, pulsar_consumer, sample_message_data):
        """测试无消息处理器的情况"""
        # 创建模拟消息
        mock_message = Mock()
        mock_message.message_id.return_value = "test-message-id"
        mock_message.data.return_value = json.dumps(sample_message_data).encode('utf-8')
        
        # 处理消息（无处理器）
        await pulsar_consumer._process_message(mock_message)
        
        # 验证消息仍然被确认
        pulsar_consumer._consumer.acknowledge.assert_called_once_with(mock_message)
    
    @pytest.mark.asyncio
    async def test_message_processing_error_handling(self, pulsar_consumer, sample_message_data):
        """测试消息处理错误处理"""
        # 创建模拟消息
        mock_message = Mock()
        mock_message.message_id.return_value = "test-message-id"
        mock_message.data.return_value = json.dumps(sample_message_data).encode('utf-8')
        
        # 设置抛出异常的消息处理器
        mock_handler = AsyncMock(side_effect=Exception("Processing error"))
        pulsar_consumer.set_message_handler(mock_handler)
        
        # 处理消息
        await pulsar_consumer._process_message(mock_message)
        
        # 验证否定确认
        pulsar_consumer._consumer.negative_acknowledge.assert_called_once_with(mock_message)
    
    def test_consumer_stats(self, pulsar_consumer, mock_config):
        """测试消费者统计信息"""
        stats = pulsar_consumer.get_consumer_stats()
        
        assert stats["connected"] == pulsar_consumer.is_connected
        assert stats["running"] == pulsar_consumer.is_running
        assert stats["connection_retries"] == 0
        assert stats["topic"] == mock_config.pulsar.topic
        assert stats["subscription"] == mock_config.pulsar.subscription
    
    def test_graceful_close(self, pulsar_consumer):
        """测试优雅关闭"""
        # 设置模拟对象
        pulsar_consumer._consumer = Mock()
        pulsar_consumer._client = Mock()
        pulsar_consumer._running = True
        
        # 关闭
        asyncio.run(pulsar_consumer.close())
        
        # 验证关闭调用
        pulsar_consumer._consumer.close.assert_called_once()
        pulsar_consumer._client.close.assert_called_once()
        assert not pulsar_consumer._running
    
    def test_properties(self, pulsar_consumer):
        """测试属性访问"""
        assert pulsar_consumer.is_connected == pulsar_consumer.is_connected
        assert pulsar_consumer.is_running == pulsar_consumer.is_running
        
        # 测试设置消息处理器
        mock_handler = AsyncMock()
        pulsar_consumer.set_message_handler(mock_handler)
        assert pulsar_consumer.message_handler == mock_handler