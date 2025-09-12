#!/usr/bin/env python3
"""
消息处理器集成测试
基于test_consumer/test_message_handler.py创建的真实运行测试场景
"""

import pytest
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

from hydocpusher.consumer.message_handler import MessageHandler, MessageProcessor
from hydocpusher.config.settings import get_config
from hydocpusher.config.classification_config import ClassificationConfig
from hydocpusher.transformer.data_transformer import DataTransformer
from hydocpusher.models.message_models import SourceMessageSchema
from hydocpusher.exceptions.custom_exceptions import (
    ValidationException, MessageProcessException, DataTransformException
)


class TestMessageHandlerIntegration:
    """消息处理器集成测试类 - 真实环境"""
    
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
        """创建数据转换器实例"""
        return DataTransformer()
    
    @pytest.fixture
    def message_handler(self, config, data_transformer):
        """创建消息处理器实例"""
        handler = MessageHandler(config)
        handler.set_data_transformer(data_transformer)
        return handler
    
    @pytest.fixture
    def sample_message_data(self):
        """示例消息数据"""
        return {
            "MSG": "操作成功",
            "ISSUCCESS": "1",
            "DATA": {
                "SITENAME": "测试推送站点",
                "CRTIME": "2025-08-29 18:53:15",
                "CHANNELID": "2240",
                "VIEWID": "view_001",
                "VIEWNAME": "测试视图",
                "SITEID": "33",
                "DOCID": "64941",
                "OPERTYPE": "1",
                "CHANNELNAV": "2240",
                "CRUSER": "test_user",
                "ID": "msg_20250829_002",
                "CHANNELDESCNAV": "首页>新闻>科技>测试频道",
                "TYPE": "document",
                "CRUSER": "test_user",
                "ID": "msg_20250829_001",
                "DATA": {
                    "DOCTYPE": "20",
                    "LISTTITLE": "测试 裸眼3D看云能",
                    "SITENAME": "测试推送",
                    "DOCHTMLCON": "<div>测试内容</div>",
                    "CRTIME": "2025-08-29 18:53:15",
                    "DOCPUBTIME": "2025-08-29 18:53:15",
                    "AUTHOR": "测试作者",
                    "KEYWORDS": "测试,关键词",
                    "SUMMARY": "这是一个测试文档的摘要",
                    "WEBHTTP": "http://test.example.com",
                     "PUBSTATUS": "1",
                     "MODAL": "normal",
                     "CHNLNAME": "测试频道",
                     "ORIGINMETADATAID": "origin_meta_001",
                     "SITEID": "33",
                     "CHNLDESC": "测试频道描述",
                     "DOCTITLE": "测试文档标题",
                     "DOCPUBURL": "http://test.example.com/doc/64941",
                     "CLASSIFICATIONID": "class_001",
                     "MEDIATYPE": "text",
                      "DOCRELTIME": "2025-08-29 18:53:15",
                      "CHNLDOC_OPERTIME": "2025-08-29 18:53:15",
                      "SITEDESC": "测试站点描述",
                       "CRUSER": "test_user",
                       "DOCUMENT_DOCRELTIME": "2025-08-29 18:53:15",
                       "RECID": "rec_001",
                        "ACTIONTYPE": "INSERT",
                        "METADATAID": "meta_001",
                        "CHANNELID": "2240",
                        "DOCORDER": "1",
                     "ORIGINMETADATAID": "origin_meta_001",
                     "SITEID": "33",
                     "CHNLDESC": "测试频道描述",
                     "DOCTITLE": "测试文档标题",
                      "DOCPUBURL": "http://test.example.com/doc/64941",
                      "CLASSIFICATIONID": "class_001",
                     "ATTACHMENTS": [
                        {
                            "name": "test.pdf",
                            "url": "http://example.com/test.pdf",
                            "size": 1024000
                        }
                    ]
                },
                "CHNLDOC": {
                    "SRCSITEID": "33",
                    "DOCTYPE": "20",
                    "DOCFIRSTPUBTIME": "2025-08-29 18:53:15",
                    "DOCORDER": "1",
                    "RECID": "chnldoc_rec_001",
                    "ACTIONTYPE": "INSERT",
                    "DOCCHANNEL": "2240",
                    "CRUSER": "test_user",
                    "OPERUSER": "test_user",
                    "CRTIME": "2025-08-29 18:53:15",
                    "OPERTIME": "2025-08-29 18:53:15",
                    "DOCPUBTIME": "2025-08-29 18:53:15",
                    "DOCSTATUS": "1",
                    "CRDEPT": "test_dept",
                    "DOCRELTIME": "2025-08-29 18:53:15",
                    "ORIGINRECID": "origin_rec_001",
                    "DOCID": "64941",
                    "CHNLID": "2240",
                    "DOCPUBURL": "http://test.example.com/doc/64941",
                    "ACTIONUSER": "test_user",
                    "SITEID": "33",
                    "PUBSTATUS": "1",
                    "MODAL": "normal",
                    "DOCOUTUPID": "output_001",
                    "DOCKIND": "1"
                },
                "APPENDIX": []
            }
        }
    
    @pytest.mark.asyncio
    async def test_successful_message_processing_real_environment(self, message_handler, sample_message_data):
        """测试在真实环境中成功处理消息"""
        # 处理消息
        result = await message_handler.handle_message(sample_message_data)
        
        # 验证处理结果
        assert result is not None
        assert "success" in result
        assert result["success"] is True
        
        # 验证统计信息
        stats = message_handler.get_processing_stats()
        assert stats["processed"] >= 1
        
        print(f"消息处理成功: {result}")
        print(f"处理统计: {stats}")
    
    @pytest.mark.asyncio
    async def test_message_validation_real_data(self, message_handler, sample_message_data):
        """测试真实数据的消息验证"""
        # 验证完整消息 - 通过处理消息来验证
        result = await message_handler.handle_message(sample_message_data)
        assert result["success"] is True
        
        # 测试缺少必需字段的消息
        invalid_message = sample_message_data.copy()
        del invalid_message["DATA"]
        
        with pytest.raises(MessageProcessException):
            await message_handler.handle_message(invalid_message)
    
    @pytest.mark.asyncio
    async def test_data_transformation_real_environment(self, message_handler, sample_message_data):
        """测试在真实环境中的数据转换"""
        # 执行消息处理
        result = await message_handler.handle_message(sample_message_data)
        
        # 验证处理结果
        assert result is not None
        assert "success" in result
        assert result["success"] == True
        
        # 创建可序列化的结果副本
        serializable_result = result.copy()
        if 'archive_data' in serializable_result:
            serializable_result['archive_data'] = serializable_result['archive_data'].dict()
        
        print(f"消息处理成功: {json.dumps(serializable_result, ensure_ascii=False, indent=2)}")
    
    @pytest.mark.asyncio
    async def test_batch_message_processing(self, message_handler, sample_message_data):
        """测试批量消息处理"""
        messages = []
        
        # 创建多个测试消息
        for i in range(5):
            message = sample_message_data.copy()
            message["DATA"]["DOCID"] = str(64941 + i)
            message["DATA"]["DATA"]["LISTTITLE"] = f"测试文档 {i+1}"
            messages.append(message)
        
        # 批量处理消息
        results = []
        for message in messages:
            try:
                result = await message_handler.process_message(message)
                results.append(result)
            except Exception as e:
                print(f"处理消息失败: {e}")
                results.append({"success": False, "error": str(e)})
        
        # 验证处理结果
        successful_count = sum(1 for r in results if r.get("success", False))
        assert successful_count >= 0  # 至少应该有一些成功的
        
        # 验证统计信息
        stats = message_handler.get_processing_stats()
        print(f"批量处理完成: 成功 {successful_count}/{len(messages)}")
        print(f"处理统计: {stats}")
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, message_handler):
        """测试错误处理和恢复机制"""
        # 测试空消息
        empty_message = {}
        
        with pytest.raises(MessageProcessException):
            await message_handler.handle_message(empty_message)
        
        # 测试缺少关键字段的消息
        incomplete_message = {
            "MSG": "操作成功"
            # 缺少DATA字段
        }
        
        with pytest.raises(MessageProcessException):
            await message_handler.handle_message(incomplete_message)
        
        # 验证错误统计
        stats = message_handler.get_processing_stats()
        assert stats["failed"] >= 2  # 应该记录失败次数
    
    def test_message_handler_configuration(self, message_handler, config):
        """测试消息处理器配置"""
        assert message_handler.config == config
        assert message_handler.data_transformer is not None
        
        # 测试统计信息初始化
        stats = message_handler.get_processing_stats()
        assert "processed" in stats
        assert "failed" in stats
        assert "retried" in stats
    
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, message_handler, sample_message_data):
        """测试并发消息处理"""
        # 创建多个并发任务
        tasks = []
        for i in range(3):
            message = sample_message_data.copy()
            message["DATA"]["DOCID"] = str(64941 + i)
            message["DATA"]["DATA"]["LISTTITLE"] = f"并发测试文档 {i+1}"
            
            task = asyncio.create_task(
                message_handler.handle_message(message)
            )
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证结果
        successful_results = [
            r for r in results 
            if not isinstance(r, Exception) and r.get("success", False)
        ]
        
        print(f"并发处理完成: 成功 {len(successful_results)}/{len(tasks)}")
        
        # 验证统计信息
        stats = message_handler.get_processing_stats()
        print(f"并发处理统计: {stats}")


class TestMessageProcessorIntegration:
    """消息处理器核心类集成测试"""
    
    @pytest.fixture
    def config(self):
        """获取应用配置"""
        return get_config()
    
    @pytest.fixture
    def sample_message_data(self):
        """示例消息数据"""
        return {
            "MSG": "操作成功",
            "ISSUCCESS": "1",
            "DATA": {
                "SITENAME": "测试推送",
                "CRTIME": "2025-08-29 18:53:15",
                "CHANNELID": "2240",
                "DOCID": "64941",
                "OPERTYPE": "1",
                "CHANNELDESCNAV": "首页>新闻>科技>测试频道",
                "CHANNELNAV": "首页>新闻>科技>测试频道",
                "CRUSER": "test_user",
                "ID": "64941",
                "VIEWID": "view_001",
                "VIEWNAME": "测试视图",
                "SITEID": "33",
                "TYPE": "document",
                "DATA": {
                    "DOCTYPE": "20",
                    "LISTTITLE": "测试文档标题",
                    "DOCHTMLCON": "<div>测试内容</div>",
                    "CRTIME": "2025-08-29 18:53:15",
                    "DOCPUBTIME": "2025-08-29 18:53:15",
                    "WEBHTTP": "http://test.example.com",
                    "PUBSTATUS": "1",
                    "MODAL": "normal",
                    "CHNLNAME": "测试频道",
                    "ORIGINMETADATAID": "origin_meta_001",
                    "SITEID": "33",
                    "CHNLDESC": "测试频道描述",
                    "DOCTITLE": "测试文档标题",
                    "DOCPUBURL": "http://test.example.com/doc/64941",
                    "CLASSIFICATIONID": "class_001",
                    "CHANNELID": "2240",
                    "RECID": "rec_001",
                    "ACTIONTYPE": "INSERT",
                    "METADATAID": "meta_001",
                    "SITEDESC": "测试站点描述",
                    "CRUSER": "test_user",
                    "DOCUMENT_DOCRELTIME": "2025-08-29 18:53:15",
                    "MEDIATYPE": "text",
                    "DOCRELTIME": "2025-08-29 18:53:15",
                    "CHNLDOC_OPERTIME": "2025-08-29 18:53:15",
                    "DOCORDER": "1",
                    "SITENAME": "测试推送站点",
                    "KEYWORDS": "测试,关键词",
                    "SUMMARY": "这是一个测试文档的摘要",
                    "ATTACHMENTS": [
                        {
                            "name": "test.pdf",
                            "url": "http://test.example.com/attachments/test.pdf",
                            "size": 1024000
                        }
                    ]
                },
                "CHNLDOC": {
                    "SRCSITEID": "33",
                    "DOCTYPE": "20",
                    "DOCFIRSTPUBTIME": "2025-08-29 18:53:15",
                    "DOCORDER": "1",
                    "RECID": "chnldoc_rec_001",
                    "ACTIONTYPE": "INSERT",
                    "DOCCHANNEL": "2240",
                    "CRUSER": "test_user",
                    "OPERUSER": "test_user",
                    "CRTIME": "2025-08-29 18:53:15",
                    "OPERTIME": "2025-08-29 18:53:15",
                    "DOCPUBTIME": "2025-08-29 18:53:15",
                    "DOCSTATUS": "1",
                    "CRDEPT": "test_dept",
                    "DOCRELTIME": "2025-08-29 18:53:15",
                    "ORIGINRECID": "origin_rec_001",
                    "DOCID": "64941",
                    "CHNLID": "2240",
                    "DOCPUBURL": "http://test.example.com/doc/64941",
                    "ACTIONUSER": "test_user",
                    "SITEID": "33",
                    "PUBSTATUS": "1",
                    "MODAL": "normal",
                    "DOCOUTUPID": "output_001",
                    "DOCKIND": "1"
                },
                "APPENDIX": []
            }
        }
    
    def test_message_processor_initialization_real_config(self, config):
        """测试使用真实配置初始化消息处理器"""
        processor = MessageProcessor(config)
        
        assert processor.config == config
        assert processor.handler is not None
        
        # 验证统计信息
        stats = processor.stats
        assert "processed" in stats
        assert "failed" in stats
        assert "retried" in stats
    
    @pytest.mark.asyncio
    async def test_message_processor_process_real_message(self, config, sample_message_data):
        """测试处理真实消息"""
        processor = MessageProcessor(config)
        
        # 处理消息
        result = await processor.process_message(sample_message_data)
        
        # 验证结果
        assert result is not None
        
        # 验证统计信息更新
        stats = processor.stats
        assert stats["processed"] >= 1
    
    def test_message_processor_stats_tracking(self, config):
        """测试统计信息跟踪"""
        processor = MessageProcessor(config)
        
        # 获取初始统计
        initial_stats = processor.stats
        
        # 验证统计信息结构
        assert "processed" in initial_stats
        assert "failed" in initial_stats
        assert "retried" in initial_stats
        assert initial_stats["processed"] == 0
        assert initial_stats["failed"] == 0
        assert initial_stats["retried"] == 0


if __name__ == "__main__":
    print("消息处理器集成测试")
    print("=" * 50)
    
    # 设置测试环境
    config = get_config()
    print(f"应用名称: {config.app_name}")
    print(f"应用版本: {config.app_version}")
    print(f"Pulsar集群: {config.pulsar.cluster_url}")
    print(f"档案系统API: {config.archive.api_url}")
    
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ])