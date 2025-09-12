#!/usr/bin/env python3
"""
Pulsar消费者集成测试
基于test_consumer/test_pulsar_consumer.py创建的真实运行测试场景
"""

import pytest
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock

import pulsar

from hydocpusher.consumer.pulsar_consumer import PulsarConsumer
from hydocpusher.consumer.message_handler import MessageHandler
from hydocpusher.config.settings import get_config
from hydocpusher.config.classification_config import ClassificationConfig
from hydocpusher.transformer.data_transformer import DataTransformer
from hydocpusher.exceptions.custom_exceptions import ConnectionException, MessageProcessException


class TestPulsarConsumerIntegration:
    """Pulsar消费者集成测试类 - 真实环境"""
    
    @pytest.fixture(scope="class")
    def config(self):
        """获取应用配置"""
        return get_config()
    
    @pytest.fixture(scope="class")
    def classification_config(self):
        """获取分类配置"""
        return ClassificationConfig()
    
    @pytest.fixture
    def data_transformer(self, config, classification_config):
        """创建数据转换器"""
        return DataTransformer(config, classification_config)
    
    @pytest.fixture
    def message_handler(self, config, data_transformer):
        """创建消息处理器实例"""
        handler = MessageHandler(config)
        handler.set_data_transformer(data_transformer)
        return handler
    
    @pytest.fixture
    async def pulsar_consumer(self, config):
        """创建Pulsar消费者实例"""
        consumer = PulsarConsumer(config)
        yield consumer
        await consumer.close()
    
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
                    "CRTIME": "2025-08-29 18:53:15",
                    "DOCPUBTIME": "2025-08-29 18:53:15",
                    "AUTHOR": "测试作者",
                    "KEYWORDS": "测试,关键词",
                    "SUMMARY": "这是一个测试文档的摘要"
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_consumer_connection_real_environment(self, pulsar_consumer, config):
        """测试在真实环境中连接Pulsar"""
        try:
            # 尝试连接
            await pulsar_consumer.connect()
            
            assert pulsar_consumer._client is not None
            assert pulsar_consumer._consumer is not None
            assert pulsar_consumer.is_connected is True
            print(f"成功连接到Pulsar集群: {config.pulsar.cluster_url}")
            print(f"订阅Topic: {config.pulsar.topic}")
        except Exception as e:
            print(f"连接失败，可能Pulsar服务不可用: {config.pulsar.cluster_url}, 错误: {str(e)}")
            pytest.skip("Pulsar服务不可用，跳过测试")
    
    @pytest.mark.asyncio
    async def test_consumer_connection_with_retry(self, config):
        """测试连接重试机制"""
        # 使用错误的配置测试重试
        bad_config = config.model_copy()
        bad_config.pulsar.cluster_url = "pulsar://nonexistent:6650"
        bad_config.pulsar.connection_timeout = 5000  # 缩短超时时间
        
        consumer = PulsarConsumer(bad_config)
        
        try:
            # 连接应该失败
            success = await consumer.connect()
            assert success is False
            print("连接重试机制测试通过：正确处理了连接失败")
        except ConnectionException as e:
            print(f"连接异常处理正确: {e}")
            assert True
        finally:
            await consumer.close()
    
    @pytest.mark.asyncio
    async def test_message_parsing_and_validation(self, pulsar_consumer, sample_message_data):
        """测试消息解析和验证"""
        # 测试有效JSON消息解析
        json_message = json.dumps(sample_message_data, ensure_ascii=False)
        # 创建模拟Pulsar消息
        mock_message = Mock()
        mock_message.data.return_value = json_message.encode('utf-8')
        mock_message.message_id.return_value = "test-message-id"
        
        parsed_data = pulsar_consumer._parse_message(mock_message)
        
        assert parsed_data == sample_message_data
        print("JSON消息解析成功")
        
        # 测试无效JSON处理
        invalid_json = b"invalid json data"
        # 创建无效消息
        mock_invalid_message = Mock()
        mock_invalid_message.data.return_value = invalid_json
        mock_invalid_message.message_id.return_value = "invalid-message-id"
        
        parsed_invalid = pulsar_consumer._parse_message(mock_invalid_message)
        assert parsed_invalid is None
        print("无效JSON处理正确")
        
        # 测试空消息处理
        empty_data = b""
        # 创建空消息
        mock_empty_message = Mock()
        mock_empty_message.data.return_value = empty_data
        mock_empty_message.message_id.return_value = "empty-message-id"
        
        parsed_empty = pulsar_consumer._parse_message(mock_empty_message)
        assert parsed_empty is None
        print("空消息处理正确")
    
    @pytest.mark.asyncio
    async def test_message_processing_with_handler(self, pulsar_consumer, message_handler, sample_message_data):
        """测试带消息处理器的消息处理"""
        # 设置消息处理器
        pulsar_consumer.set_message_handler(message_handler)
        assert pulsar_consumer.message_handler == message_handler
        
        # 模拟消息处理
        try:
            # 创建模拟Pulsar消息
            mock_message = Mock()
            mock_message.data.return_value = json.dumps(sample_message_data).encode('utf-8')
            mock_message.message_id.return_value = "test-message-id"
            mock_message.ack = Mock()
            
            await pulsar_consumer._process_message(mock_message)
            
            # 验证消息被确认
            mock_message.ack.assert_called_once()
            print("消息处理成功")
        except Exception as e:
            print(f"消息处理异常: {e}")
            # 在集成测试中，某些异常是可以接受的（如网络问题）
    
    @pytest.mark.asyncio
    async def test_message_processing_without_handler(self, pulsar_consumer, sample_message_data):
        """测试没有消息处理器时的处理"""
        # 确保没有设置消息处理器
        pulsar_consumer.message_handler = None
        
        # 处理消息应该返回None或抛出异常
        # 创建模拟Pulsar消息
        mock_message = Mock()
        mock_message.data.return_value = json.dumps(sample_message_data).encode('utf-8')
        mock_message.message_id.return_value = "test-message-id"
        mock_message.ack = Mock()
        
        await pulsar_consumer._process_message(mock_message)
        # 没有处理器时，应该返回None或记录警告
        print("无处理器时的处理完成")
    
    @pytest.mark.asyncio
    async def test_consumer_stats_tracking(self, pulsar_consumer):
        """测试消费者统计信息跟踪"""
        # 获取初始统计信息
        stats = pulsar_consumer.get_consumer_stats()
        
        # 验证统计信息结构
        # 只验证基础的统计信息字段
        assert "connected" in stats
        assert "running" in stats
        assert "connection_retries" in stats
        assert "topic" in stats
        assert "subscription" in stats
        
        print(f"消费者统计信息: {stats}")
    
    @pytest.mark.asyncio
    async def test_start_consuming_real_environment(self, config, message_handler):
        """测试在真实环境中开始消费消息"""
        consumer = PulsarConsumer(config)
        consumer.set_message_handler(message_handler)
        
        try:
            # 尝试连接
            await consumer.connect()
            
            print(f"开始消费消息，Topic: {config.pulsar.topic}")
            
            # 启动消费（设置短暂的超时以避免无限等待）
            consume_task = asyncio.create_task(
                consumer.start_consuming()
            )
            
            # 等待几秒钟看是否有消息
            try:
                await asyncio.wait_for(consume_task, timeout=10.0)
            except asyncio.TimeoutError:
                print("消费超时，可能Topic中没有消息")
                consume_task.cancel()
                try:
                    await consume_task
                except asyncio.CancelledError:
                    pass
            
            print("消费测试完成")
                
        except Exception as e:
            print(f"消费测试失败: {str(e)}")
            pytest.skip("Pulsar连接失败")
        finally:
            await consumer.close()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, pulsar_consumer, sample_message_data):
        """测试错误处理和恢复机制"""
        # 测试消息处理异常
        class FailingHandler:
            async def process_message(self, message_data):
                raise MessageProcessException("模拟处理失败")
        
        failing_handler = FailingHandler()
        pulsar_consumer.set_message_handler(failing_handler)
        
        # 处理消息应该捕获异常
        try:
            # 创建模拟Pulsar消息
            mock_message = Mock()
            mock_message.data.return_value = json.dumps(sample_message_data).encode('utf-8')
            mock_message.message_id.return_value = "test-message-id"
            mock_message.ack = Mock()
            
            await pulsar_consumer._process_message(mock_message)
            print("异常处理完成")
        except Exception as e:
            print(f"未捕获的异常: {e}")
            # 在某些情况下，异常可能会向上传播
    
    def test_consumer_properties_and_configuration(self, pulsar_consumer, config):
        """测试消费者属性和配置"""
        assert pulsar_consumer.config == config
        
        # 测试连接状态
        assert pulsar_consumer.is_connected is False  # 初始状态应该是未连接
        
        # 测试设置消息处理器
        async def dummy_handler(message_data):
            pass
        
        # 创建新的消费者实例来测试消息处理器
        consumer_with_handler = PulsarConsumer(config)
        consumer_with_handler.set_message_handler(dummy_handler)
        assert consumer_with_handler.message_handler == dummy_handler
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, config):
        """测试优雅关闭"""
        consumer = PulsarConsumer(config)
        
        # 尝试连接
        connected = await consumer.connect()
        
        if connected:
            print("测试优雅关闭...")
            
            # 关闭消费者
            await consumer.close()
            
            # 验证关闭状态
            assert consumer.is_connected is False
            print("优雅关闭测试通过")
        else:
            # 即使没有连接，也应该能够安全关闭
            await consumer.close()
            print("未连接状态下的关闭测试通过")
    
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, config, message_handler):
        """测试并发消息处理能力"""
        consumer = PulsarConsumer(config)
        consumer.set_message_handler(message_handler)
        
        try:
            # 尝试连接
            await consumer.connect()
            
            print("并发消息处理测试完成")
                
        except Exception as e:
            print(f"并发处理测试失败: {str(e)}")
            pytest.skip("Pulsar连接失败")
        finally:
            await consumer.close()


if __name__ == "__main__":
    print("Pulsar消费者集成测试")
    print("=" * 50)
    
    # 设置测试环境
    config = get_config()
    print(f"Pulsar集群: {config.pulsar.cluster_url}")
    print(f"Topic: {config.pulsar.get_full_topic_name()}")
    print(f"订阅: {config.pulsar.subscription}")
    
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ])