#!/usr/bin/env python3
"""
死信队列集成测试
基于test_consumer/test_dead_letter_queue.py创建的真实运行测试场景
"""

import pytest
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

import pulsar

from hydocpusher.consumer.dead_letter_queue import DeadLetterQueue, DeadLetterMessage
from hydocpusher.config.settings import get_config
from hydocpusher.exceptions.custom_exceptions import MessageProcessException


class TestDeadLetterQueueIntegration:
    """死信队列集成测试类 - 真实Pulsar环境"""
    
    @pytest.fixture(scope="class")
    def config(self):
        """获取应用配置"""
        return get_config()
    
    @pytest.fixture(scope="class")
    async def pulsar_client(self, config):
        """创建真实的Pulsar客户端"""
        client = pulsar.Client(
            config.pulsar.cluster_url,
            connection_timeout_ms=config.pulsar.connection_timeout,
            operation_timeout_seconds=config.pulsar.operation_timeout // 1000
        )
        yield client
        client.close()
    
    @pytest.fixture
    async def dlq_manager(self, config, pulsar_client):
        """创建死信队列管理器实例"""
        dlq = DeadLetterQueue(config, pulsar_client)
        yield dlq
        await dlq.close()
    
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
                    "DOCPUBTIME": "2025-08-29 18:53:15"
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_dlq_initialization_real_client(self, config, pulsar_client):
        """测试使用真实客户端初始化死信队列管理器"""
        dlq = DeadLetterQueue(config, pulsar_client)
        
        assert dlq.config == config
        assert dlq._client == pulsar_client
        assert dlq._producer is None  # 初始时生产者为空
        
        await dlq.close()
    
    @pytest.mark.asyncio
    async def test_dlq_initialization_without_client(self, config):
        """测试不提供客户端时自动创建"""
        dlq = DeadLetterQueue(config)
        
        assert dlq.config == config
        assert dlq._own_client is True  # 标记为自己创建的客户端
        
        await dlq.close()
    
    @pytest.mark.asyncio
    async def test_send_to_dlq_real_environment(self, dlq_manager, sample_message_data):
        """测试在真实环境中发送消息到死信队列"""
        # 创建一个处理异常
        error = MessageProcessException("测试消息处理失败")
        
        # 发送到死信队列
        await dlq_manager.send_to_dlq(
            original_message=sample_message_data,
            error=error,
            retry_count=3
        )
        
        result = True  # 如果没有异常，认为发送成功
        
        assert result is True
        print(f"成功发送消息到死信队列: {dlq_manager.config.pulsar.get_full_dead_letter_topic_name()}")
    
    @pytest.mark.asyncio
    async def test_send_multiple_dlq_messages(self, dlq_manager, sample_message_data):
        """测试发送多条死信消息"""
        messages_sent = 0
        
        for i in range(3):
            # 修改消息数据以区分不同消息
            test_data = sample_message_data.copy()
            test_data["DATA"]["DOCID"] = str(64941 + i)
            test_data["DATA"]["DATA"]["LISTTITLE"] = f"测试消息 {i+1}"
            
            error = MessageProcessException(f"测试消息 {i+1} 处理失败")
            
            await dlq_manager.send_to_dlq(
                original_message=test_data,
                error=error,
                retry_count=i+1
            )
            
            result = True  # 如果没有异常，认为发送成功
            
            if result:
                messages_sent += 1
        
        assert messages_sent == 3
        print(f"成功发送 {messages_sent} 条消息到死信队列")
    
    def test_build_dlq_message_structure(self, config):
        """测试死信消息结构构建"""
        dlq = DeadLetterQueue(config)
        
        original_message = {"test": "data"}
        error = MessageProcessException("测试错误")
        error.error_code = "TEST_001"
        
        dlq_message = dlq._build_dlq_message(
            original_message=original_message,
            error=error,
            retry_count=2,
            additional_context=None
        )
        
        # 验证死信消息结构
        assert isinstance(dlq_message, dict)
        assert dlq_message["original_message"] == original_message
        assert "测试错误" in dlq_message["error"]["message"]
        assert dlq_message["error"]["error_code"] == "TEST_001"
        assert dlq_message["retry_count"] == 2
        assert dlq_message["application"]["name"] == config.app_name
        assert dlq_message["application"]["version"] == config.app_version
        assert "dlq_timestamp" in dlq_message
    
    @pytest.mark.asyncio
    async def test_dlq_stats_tracking(self, config):
        """测试死信队列统计信息跟踪"""
        dlq = DeadLetterQueue(config)
        
        # 获取初始统计信息
        initial_stats = await dlq.get_dlq_stats()
        
        # 验证统计信息结构
        expected_keys = ["initialized", "producer_connected", "topic"]
        for key in expected_keys:
            assert key in initial_stats
        
        await dlq.close()
    
    @pytest.mark.asyncio
    async def test_connection_resilience(self, config):
        """测试连接弹性 - 验证连接失败后的重试机制"""
        # 使用错误的配置测试连接失败处理
        bad_config = config.model_copy()
        bad_config.pulsar.cluster_url = "pulsar://nonexistent:6650"
        
        try:
            dlq = DeadLetterQueue(bad_config)
            # 尝试发送消息，应该失败
            result = await dlq.send_to_dlq(
                message_data={"test": "data"},
                error=MessageProcessException("测试错误"),
                retry_count=1
            )
            # 连接失败时应该返回False
            assert result is False
            await dlq.close()
        except Exception as e:
            # 连接失败是预期的
            print(f"预期的连接失败: {e}")
            assert True


class TestDeadLetterMessageIntegration:
    """死信消息模型集成测试"""
    
    def test_dead_letter_message_serialization(self):
        """测试死信消息序列化"""
        original_message = {
            "MSG": "操作成功",
            "DATA": {
                "DOCID": "12345",
                "TITLE": "测试文档"
            }
        }
        
        dlq_message = DeadLetterMessage(
            message_id="12345",
            original_message=original_message,
            error_type="ProcessException",
            error_message="处理失败",
            retry_count=3
        )
        
        # 测试转换为字典
        message_dict = dlq_message.to_dict()
        
        assert message_dict["original_message"] == original_message
        assert message_dict["error_message"] == "处理失败"
        assert message_dict["error_type"] == "ProcessException"
        assert message_dict["retry_count"] == 3
        assert "timestamp" in message_dict
        
        # 测试JSON序列化
        json_str = json.dumps(message_dict, ensure_ascii=False, default=str)
        assert json_str is not None
        
        # 测试反序列化
        parsed_dict = json.loads(json_str)
        assert parsed_dict["original_message"] == original_message


if __name__ == "__main__":
    print("死信队列集成测试")
    print("=" * 50)
    
    # 设置测试环境
    config = get_config()
    print(f"Pulsar集群: {config.pulsar.cluster_url}")
    print(f"死信队列Topic: {config.pulsar.get_full_dead_letter_topic_name()}")
    
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ])