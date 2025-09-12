"""
消息处理器类测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from hydocpusher.consumer.message_handler import MessageHandler, MessageProcessor
from hydocpusher.config.settings import AppConfig
from hydocpusher.models.message_models import SourceMessageSchema
from hydocpusher.exceptions.custom_exceptions import (
    ValidationException, MessageProcessException, DataTransformException
)


class TestMessageHandler:
    """消息处理器测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        config = Mock(spec=AppConfig)
        config.app_name = "HyDocPusher"
        config.app_version = "1.0.0"
        config.pulsar = Mock()
        config.archive = Mock()
        return config
    
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
    
    @pytest.fixture
    def message_handler(self, mock_config):
        """创建消息处理器实例"""
        return MessageHandler(mock_config)
    
    @pytest.mark.asyncio
    async def test_successful_message_processing(self, message_handler):
        """测试成功处理消息"""
        # 简化但完整的消息数据
        simple_message_data = {
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
                    "CHANNELID": "2240",
                    "DOCTYPE": "20",
                    "LISTTITLE": "测试 裸眼3D看云能",
                    "SITENAME": "测试推送",
                    "DOCHTMLCON": "<div>测试内容</div>",
                    "CRUSER": "dev",
                    "DOCUMENT_DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCORDER": "34",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "METADATAID": "64941",
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
                    "WEBHTTP": "https://www.cnyeig.com/csts",
                    "CRTIME": "2025-08-29 18:53:16",
                    "SITEDESC": "数字能投订阅号推送",
                    "MEDIATYPE": "2",
                    "DOCRELTIME": "2025-04-09 15:46:25",
                    "CHNLDOC_OPERTIME": "2025-08-29 18:54:06"
                },
                "CHNLDOC": {
                    "DOCTYPE": "20",
                    "DOCFIRSTPUBTIME": "2025-08-29 18:54:06",
                    "DOCORDER": "34",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "DOCCHANNEL": "2240",
                    "SRCSITEID": "33",
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
                    "OPERUSER": "dev",
                    "ORIGINRECID": "76655",
                    "DOCOUTUPID": "61261",
                    "DOCKIND": "11",
                    "SITEID": "33",
                    "PUBSTATUS": "1",
                    "MODAL": "1",
                    "ACTIONUSER": "dev"
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
        
        # 模拟数据转换器
        mock_transformer = AsyncMock()
        mock_transformer.transform.return_value = {
            "AppId": "NEWS",
            "AppToken": "TmV3cytJbnRlcmZhY2U=",
            "CompanyName": "云南省能源投资集团有限公司",
            "ArchiveType": "17",
            "ArchiveData": {
                "did": "64941",
                "wzmc": "测试推送",
                "title": "裸眼3D看云能",
                "author": "集团党群部"
            }
        }
        message_handler.data_transformer = mock_transformer
        
        # 处理消息
        result = await message_handler.handle_message(simple_message_data)
        
        # 验证结果
        assert result["success"] is True
        assert result["message_id"] == "64941"
        assert "processing_time" in result
        assert "archive_data" in result
        
        # 验证转换器被调用
        mock_transformer.transform.assert_called_once()
        
        # 验证统计信息
        stats = message_handler.get_processing_stats()
        assert stats["processed"] == 1
        assert stats["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_message_validation_missing_required_fields(self, message_handler):
        """测试验证缺少必需字段的消息"""
        invalid_message = {
            "MSG": "操作成功",
            # 缺少 DATA 字段
            "ISSUCCESS": "true"
        }
        
        with pytest.raises(MessageProcessException) as exc_info:
            await message_handler.handle_message(invalid_message)
        
        assert "Missing required fields: DATA" in str(exc_info.value)
        
        # 验证统计信息
        stats = message_handler.get_processing_stats()
        assert stats["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_message_validation_invalid_format(self, message_handler):
        """测试验证格式无效的消息"""
        invalid_message = {
            "MSG": "操作成功",
            "DATA": "invalid_data_format",  # 应该是字典
            "ISSUCCESS": "true"
        }
        
        with pytest.raises(MessageProcessException) as exc_info:
            await message_handler.handle_message(invalid_message)
        
        assert "Message validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_data_transformation_failure(self, message_handler):
        """测试数据转换失败的情况"""
        # 使用完整的消息数据
        complete_message_data = {
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
                    "CHANNELID": "2240",
                    "DOCTYPE": "20",
                    "LISTTITLE": "测试 裸眼3D看云能",
                    "SITENAME": "测试推送",
                    "DOCHTMLCON": "<div>测试内容</div>",
                    "CRUSER": "dev",
                    "DOCUMENT_DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCORDER": "34",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "METADATAID": "64941",
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
                    "WEBHTTP": "https://www.cnyeig.com/csts",
                    "CRTIME": "2025-08-29 18:53:16",
                    "SITEDESC": "数字能投订阅号推送",
                    "MEDIATYPE": "2",
                    "DOCRELTIME": "2025-04-09 15:46:25",
                    "CHNLDOC_OPERTIME": "2025-08-29 18:54:06"
                },
                "CHNLDOC": {
                    "DOCTYPE": "20",
                    "DOCFIRSTPUBTIME": "2025-08-29 18:54:06",
                    "DOCORDER": "34",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "DOCCHANNEL": "2240",
                    "SRCSITEID": "33",
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
                    "OPERUSER": "dev",
                    "ORIGINRECID": "76655",
                    "DOCOUTUPID": "61261",
                    "DOCKIND": "11",
                    "SITEID": "33",
                    "PUBSTATUS": "1",
                    "MODAL": "1",
                    "ACTIONUSER": "dev"
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
        
        # 模拟数据转换器抛出异常
        mock_transformer = AsyncMock()
        mock_transformer.transform.side_effect = DataTransformException("Transformation failed")
        message_handler.data_transformer = mock_transformer
        
        with pytest.raises(MessageProcessException) as exc_info:
            await message_handler.handle_message(complete_message_data)
        
        assert "Data transformation failed" in str(exc_info.value)
        
        # 验证统计信息
        stats = message_handler.get_processing_stats()
        assert stats["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, message_handler, sample_message_data):
        """测试未预期异常的处理"""
        # 模拟数据转换器抛出意外异常
        mock_transformer = AsyncMock()
        mock_transformer.transform.side_effect = Exception("Unexpected error")
        message_handler.data_transformer = mock_transformer
        
        with pytest.raises(MessageProcessException) as exc_info:
            await message_handler.handle_message(sample_message_data)
        
        assert "Unexpected error processing message" in str(exc_info.value)
        
        # 验证统计信息
        stats = message_handler.get_processing_stats()
        assert stats["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_message_with_failed_status(self, message_handler):
        """测试处理失败状态的消息"""
        failed_message = {
            "MSG": "操作失败",
            "DATA": {
                "SITENAME": "测试推送",
                "CRTIME": "2025-08-29 18:53:15",
                "CHANNELID": "2240",
                "DOCID": "64941",
                "DATA": {
                    "DOCTYPE": "20",
                    "DOCTITLE": "裸眼3D看云能",
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html"
                },
                "CHNLDOC": {
                    "DOCTYPE": "20",
                    "DOCID": "64941",
                    "CHNLID": "2240"
                }
            },
            "ISSUCCESS": "false"
        }
        
        with pytest.raises(MessageProcessException) as exc_info:
            await message_handler.handle_message(failed_message)
        
        assert "Message indicates failure" in str(exc_info.value)
    
    def test_set_data_transformer(self, message_handler, mock_config):
        """测试设置数据转换器"""
        new_transformer = Mock()
        message_handler.set_data_transformer(new_transformer)
        
        assert message_handler.data_transformer == new_transformer
    
    def test_get_processing_stats(self, message_handler):
        """测试获取处理统计信息"""
        stats = message_handler.get_processing_stats()
        
        assert isinstance(stats, dict)
        assert "processed" in stats
        assert "failed" in stats
        assert "retried" in stats
        assert stats["processed"] == 0
        assert stats["failed"] == 0
        assert stats["retried"] == 0
    
    def test_reset_stats(self, message_handler):
        """测试重置统计信息"""
        # 修改统计信息
        message_handler._processing_stats["processed"] = 5
        message_handler._processing_stats["failed"] = 2
        message_handler._processing_stats["retried"] = 1
        
        # 重置
        message_handler.reset_stats()
        
        stats = message_handler.get_processing_stats()
        assert stats["processed"] == 0
        assert stats["failed"] == 0
        assert stats["retried"] == 0
    
    @pytest.mark.asyncio
    async def test_validate_message_success(self, message_handler, sample_message_data):
        """测试消息验证成功"""
        result = await message_handler._validate_message(sample_message_data)
        
        assert isinstance(result, SourceMessageSchema)
        assert result.document_id == "64941"
        assert result.document_title == "裸眼3D看云能"
    
    @pytest.mark.asyncio
    async def test_transform_data_success(self, message_handler, sample_message_data):
        """测试数据转换成功"""
        # 创建验证后的消息
        validated_message = SourceMessageSchema(**sample_message_data)
        
        # 模拟数据转换器
        mock_transformer = AsyncMock()
        expected_result = {"transformed": "data"}
        mock_transformer.transform.return_value = expected_result
        message_handler.data_transformer = mock_transformer
        
        result = await message_handler._transform_data(validated_message)
        
        assert result == expected_result
        mock_transformer.transform.assert_called_once_with(validated_message)


class TestMessageProcessor:
    """消息处理器兼容类测试"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        config = Mock(spec=AppConfig)
        config.app_name = "HyDocPusher"
        config.app_version = "1.0.0"
        config.pulsar = Mock()
        config.archive = Mock()
        return config
    
    @pytest.fixture
    def sample_message_data(self):
        """示例消息数据"""
        return {
            "MSG": "操作成功",
            "DATA": {
                "SITENAME": "测试推送",
                "CRTIME": "2025-08-29 18:53:15",
                "CHANNELID": "2240",
                "DOCID": "64941",
                "DATA": {
                    "DOCTYPE": "20",
                    "DOCTITLE": "裸眼3D看云能",
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html"
                },
                "CHNLDOC": {
                    "DOCTYPE": "20",
                    "DOCID": "64941",
                    "CHNLID": "2240"
                }
            },
            "ISSUCCESS": "true"
        }
    
    def test_message_processor_initialization(self, mock_config):
        """测试消息处理器初始化"""
        processor = MessageProcessor(mock_config)
        
        assert processor.config == mock_config
        assert processor.handler is not None
        assert isinstance(processor.handler, MessageHandler)
    
    @pytest.mark.asyncio
    async def test_message_processor_process_message(self, mock_config, sample_message_data):
        """测试消息处理器处理消息"""
        processor = MessageProcessor(mock_config)
        
        # 模拟处理器的handler
        with patch.object(processor.handler, 'handle_message', new_callable=AsyncMock) as mock_handle:
            expected_result = {"success": True, "message_id": "64941"}
            mock_handle.return_value = expected_result
            
            result = await processor.process_message(sample_message_data)
            
            assert result == expected_result
            mock_handle.assert_called_once_with(sample_message_data)
    
    def test_message_processor_stats(self, mock_config):
        """测试消息处理器统计信息"""
        processor = MessageProcessor(mock_config)
        
        # 模拟统计信息
        processor.handler._processing_stats = {"processed": 10, "failed": 2, "retried": 1}
        
        stats = processor.stats
        
        assert stats["processed"] == 10
        assert stats["failed"] == 2
        assert stats["retried"] == 1