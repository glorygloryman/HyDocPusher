"""
数据模型单元测试
测试所有Pydantic数据模型的功能
"""

import pytest
import json
from datetime import datetime
from typing import Dict, Any
from hydocpusher.models.message_models import (
    SourceMessageSchema,
    MessageData,
    DocumentData,
    ChannelDoc,
    AppendixInfo
)
from hydocpusher.models.archive_models import (
    ArchiveRequestSchema,
    ArchiveData,
    AttachmentData,
    ArchiveResponseSchema
)
from hydocpusher.exceptions.custom_exceptions import ValidationException


class TestSourceMessageSchema:
    """源消息模型测试"""
    
    def test_create_valid_message(self):
        """测试创建有效消息"""
        message_data = {
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
                "CRTIME": "2025-04-09 15:46:25",  # 创建时间
                "DATA": {
                    "ISFOCUSIMAGE": "否",
                    "CHANNELID": "2240",
                    "DOCTITLE": "裸眼3D看云能",
                    "CRTIME": "2025-04-09 15:46:25",  # 创建时间
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "METADATAID": "64941",
                    "CRUSER": "dev",
                    "DOCTYPE": "20",
                    "DOCORDER": "34",
                    "SITEDESC": "数字能投订阅号推送",
                    "DOCHTMLCON": "<div>测试内容</div>",
                    "MEDIATYPE": "2",
                    "DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCCONTENT": "",
                    "CHNLDOC_OPERTIME": "2025-08-29 18:54:06",
                    "CLASSIFICATIONID": "6",
                    "ORIGINMETADATAID": "61261",
                    "SITEID": "33",
                    "CHNLDESC": "数字能投推送测试",
                    "PUBSTATUS": "1",
                    "MODAL": "1",
                    "CHNLNAME": "新闻头条_2240",
                    "DOCUMENT_RELATED_PIC": "[]",
                    "DOCUMENT_RELATED_VIDEO": "[]",
                    "DOCUMENT_CONTENT_APPENDIX": "[]",
                    "DOCUMENT_CONTENT_PIC": "[]",
                    "DOCUMENT_CONTENT_VIDEO": "[]",
                    "DOCUMENT_RELATED_APPENDIX": "[]",
                    "DOCSOURCENAME": "",
                    "DOCABSTRACT": "",
                    "DOCKEYWORDS": "",
                    "DOCPLACE": "",
                    "DOCLINK": "",
                    "DOCFILENAME": "",
                    "DOCAUTHOR": "",
                    "DOCPEOPLE": "",
                    "FOCUSFILENAME": "",
                    "FOCUSDESC": "",
                    "FOCUSIMAGETITLE": "",
                    "FOCUSTITLE": "",
                    "FROMID": "",
                    "LABEL": "",
                    "LISTIMGURLS": "",
                    "LISTPICS": "[]",
                    "LISTSTYLE": "4",
                    "PARENTCHNLDESC": "",
                    "SEARCHWORDVALUE": "",
                    "SHORTTITLE": "",
                    "SUBDOCTITLE": "",
                    "THUMBFILES": "",
                    "TITLECOLOR": "",
                    "VERSIONNUM": "0",
                    "WCMMETATABLEGOVDOCNEWSAPPID": "",
                    "WEBHTTP": "https://www.cnyeig.com/csts",
                    "ATTACHVIDEO": "1",
                    "ATTACHPIC": "1",
                    "COMMENTFLAG": "0",
                    "DEFAULTRELDOCS": [],  # 修复：应为列表类型
                    "DEFAULTRELDOCS_IRS": "[]",
                    "DOCUMENTLABELS": "",
                    "DOCUMENT_DOCCONTENT": "",
                    "FOCUSIMG": "",
                    "FOCUSIMAGE": "[]",
                    "DOCCOVERPIC": "[]",
                    "CHNLHASCHILDREN": "0",
                    "CLASSINFO_ID_PATHS": [],  # 修复：应为列表类型
                    "CLASSINFO_IDS": [],  # 修复：应为列表类型
                    "CLASSINFO_NAME_PATHS": [],  # 修复：应为列表类型
                    "CLASSINFO_NAMES": [],  # 修复：应为列表类型
                    "CHANNELTYPE": "",
                    "ISFOCUSIMAGE": "否",
                    "DOCUMENTLABELS": "",
                    "LISTTITLE": "裸眼3D看云能",
                    "SITENAME": "数字能投订阅号推送",
                    "DOCUMENT_DOCRELTIME": "2025-04-09 15:46:25"
                },
                "CHNLDOC": {
                    "ISARCHIVE": "0",
                    "DOCINFLOW": "0",
                    "TIMEDSTATUS": "0",
                    "OTHERVIEWMODE": "0",
                    "POSCHNLID": "0",
                    "SRCSITEID": "33",
                    "DOCAUTHOR": "",
                    "CARBONCOPYRECEIVERACTIONTYPE": "0",
                    "ISREAD": "1",
                    "ABOLITION": "0",
                    "ATTACHPIC": "1",
                    "DOCSOURCENAME": "",
                    "FLOWID": "",
                    "GDORDER": "0",
                    "DATASENDMODE": "0",
                    "ISTIMINGPUBLISH": "0",
                    "DOCTYPE": "20",
                    "DOCFIRSTPUBTIME": "2025-08-29 18:54:06",
                    "CANPUB": "1",
                    "CANEDIT": "true",
                    "DOCORDER": "34",
                    "PUBQUOTEDOC": "0",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "DOCCHANNEL": "2240",
                    "PUSHUIRBSTATUS": "1",
                    "CANCELPUBTIME": "",
                    "PUSHRECEIVERACTIONTYPE": "0",
                    "ISDELETED": "0",
                    "INVALIDTIME": "",
                    "CRUSER": "dev",
                    "CRTIME": "2025-04-09 15:46:25",  # 创建时间
                    "DOCORDERPRI": "0",
                    "NEEDMANUALSYNC": "0",
                    "OPERUSER": "dev",
                    "DOCFIRSTPUBTIME": "2025-08-29 18:53:15",  # 文档首次发布时间
                    "OPERTIME": "2025-08-29 18:54:06",
                    "DOCPUBTIME": "2025-08-29 18:54:06",
                    "DOCSTATUS": "10",
                    "CRDEPT": "云南省能源投资集团有限公司~云南能投信息产业开发有限公司~",
                    "DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCLEVEL": "0",
                    "REFUSESTATUS": "0",
                    "ORIGINRECID": "76655",
                    "DOCID": "64941",
                    "CHNLID": "2240",
                    "DISTRECEIVERACTIONTYPE": "0",
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html",
                    "ACTIONUSER": "dev",
                    "ISMASTERCHNL": "0",
                    "ARCHIVETIME": "",
                    "DOCOUTUPID": "61261",
                    "DISTSENDERACTIONTYPE": "0",
                    "DOCKIND": "11",
                    "CARBONCOPYSENDERACTIONTYPE": "0",
                    "SITEID": "33",
                    "PUBSTATUS": "1",
                    "MODAL": "1",
                    "PUSHSENDERACTIONTYPE": "0"
                },
                "CRUSER": "dev",
                "APPENDIX": [
                    {
                        "APPFILE": "/masvod/public/2025/04/09/20250409_196198623cd_r1_1200k.mp4",
                        "APPFLAG": "50"
                    }
                ],
                "ID": "84085",
                "CHANNELDESCNAV": "数字能投推送测试",
                "TYPE": "1"
            },
            "ISSUCCESS": "true"
        }
        
        message = SourceMessageSchema(**message_data)
        assert message.MSG == "操作成功"
        assert message.is_success is True
        assert message.document_id == "64941"
        assert message.document_title == "裸眼3D看云能"
        assert message.channel_id == "2240"
    
    def test_is_success_property(self):
        """测试is_success属性"""
        # 测试各种成功标志
        success_values = ["true", "True", "TRUE", "1"]
        for value in success_values:
            message = SourceMessageSchema(
                MSG="测试",
                DATA=self._get_minimal_message_data(),
                ISSUCCESS=value
            )
            assert message.is_success is True
        
        # 测试各种失败标志
        fail_values = ["false", "False", "FALSE", "0"]
        for value in fail_values:
            message = SourceMessageSchema(
                MSG="测试",
                DATA=self._get_minimal_message_data(),
                ISSUCCESS=value
            )
            assert message.is_success is False
    
    def test_invalid_is_success(self):
        """测试无效的ISSUCCESS值"""
        with pytest.raises(ValueError, match="Invalid ISSUCCESS value"):
            SourceMessageSchema(
                MSG="测试",
                DATA=self._get_minimal_message_data(),
                ISSUCCESS="invalid"
            )
    
    def test_missing_required_fields(self):
        """测试缺少必需字段"""
        incomplete_data = {
            "MSG": "测试",
            "DATA": self._get_minimal_message_data(),
            "ISSUCCESS": "true"
        }
        
        # 移除必需字段
        incomplete_data["DATA"]["DATA"]["DOCTITLE"] = None
        
        with pytest.raises(ValueError):
            SourceMessageSchema(**incomplete_data)
    
    def test_from_json(self):
        """测试从JSON字符串创建消息"""
        message_data = {
            "MSG": "操作成功",
            "DATA": self._get_minimal_message_data(),
            "ISSUCCESS": "true"
        }
        json_str = json.dumps(message_data)
        
        message = SourceMessageSchema.from_json(json_str)
        assert message.MSG == "操作成功"
        assert message.is_success is True
    
    def test_from_invalid_json(self):
        """测试从无效JSON创建消息"""
        with pytest.raises(ValidationException):
            SourceMessageSchema.from_json("invalid json")
    
    def test_validate_for_processing_success(self):
        """测试成功验证处理"""
        message = SourceMessageSchema(
            MSG="操作成功",
            DATA=self._get_minimal_message_data(),
            ISSUCCESS="true"
        )
        # 应该不抛出异常
        message.validate_for_processing()
    
    def test_validate_for_processing_failure(self):
        """测试失败验证处理"""
        message = SourceMessageSchema(
            MSG="操作失败",
            DATA=self._get_minimal_message_data(),
            ISSUCCESS="false"
        )
        with pytest.raises(ValidationException, match="Message indicates failure"):
            message.validate_for_processing()
    
    def test_datetime_parsing(self):
        """测试日期时间解析"""
        message_data = self._get_minimal_message_data()
        message_data["CRTIME"] = "2025-08-29 18:53:15"  # 创建时间
        
        message = SourceMessageSchema(
            MSG="测试",
            DATA=message_data,
            ISSUCCESS="true"
        )
        
        parsed_time = message.DATA.parsed_crtime
        assert parsed_time is not None
        assert parsed_time.year == 2025
        assert parsed_time.month == 8
        assert parsed_time.day == 29
    
    def _get_minimal_message_data(self) -> Dict[str, Any]:
        """获取最小消息数据"""
        return {
            "SITENAME": "测试",
            "CRTIME": "2025-08-29 18:53:15",
            "CHANNELID": "2240",
            "VIEWID": "11",
            "VIEWNAME": "测试",
            "SITEID": "33",
            "DOCID": "64941",
            "OPERTYPE": "1",
            "CHANNELNAV": "2240",
            "CRTIME": "2025-04-09 15:46:25",  # 创建时间
            "DATA": {
                "ISFOCUSIMAGE": "否",
                "CHANNELID": "2240",
                "DOCTITLE": "测试标题",
                "CRTIME": "2025-04-09 15:46:25",  # 创建时间
                "DOCPUBURL": "https://example.com/test.html",
                "RECID": "84085",
                "ACTIONTYPE": "3",
                "METADATAID": "64941",
                "CRUSER": "dev",
                "DOCTYPE": "20",
                "DOCORDER": "34",
                "SITEDESC": "测试站点",
                "DOCHTMLCON": "<div>测试</div>",
                "MEDIATYPE": "2",
                "DOCRELTIME": "2025-04-09 15:46:25",
                "DOCCONTENT": "",
                "CHNLDOC_OPERTIME": "2025-08-29 18:54:06",
                "CLASSIFICATIONID": "6",
                "ORIGINMETADATAID": "61261",
                "SITEID": "33",
                "CHNLDESC": "测试描述",
                "PUBSTATUS": "1",
                "MODAL": "1",
                "CHNLNAME": "测试频道",
                "DOCUMENT_RELATED_PIC": "[]",
                "DOCUMENT_RELATED_VIDEO": "[]",
                "DOCUMENT_CONTENT_APPENDIX": "[]",
                "DOCUMENT_CONTENT_PIC": "[]",
                "DOCUMENT_CONTENT_VIDEO": "[]",
                "DOCUMENT_RELATED_APPENDIX": "[]",
                "DOCSOURCENAME": "",
                "DOCABSTRACT": "",
                "DOCKEYWORDS": "",
                "DOCPLACE": "",
                "DOCLINK": "",
                "DOCFILENAME": "",
                "DOCAUTHOR": "",
                "DOCPEOPLE": "",
                "FOCUSFILENAME": "",
                "FOCUSDESC": "",
                "FOCUSIMAGETITLE": "",
                "FOCUSTITLE": "",
                "FROMID": "",
                "LABEL": "",
                "LISTIMGURLS": "",
                "LISTPICS": "[]",
                "LISTSTYLE": "4",
                "PARENTCHNLDESC": "",
                "SEARCHWORDVALUE": "",
                "SHORTTITLE": "",
                "SUBDOCTITLE": "",
                "THUMBFILES": "",
                "TITLECOLOR": "",
                "VERSIONNUM": "0",
                "WCMMETATABLEGOVDOCNEWSAPPID": "",
                "WEBHTTP": "https://example.com",
                "ATTACHVIDEO": "1",
                "ATTACHPIC": "1",
                "COMMENTFLAG": "0",
                "DEFAULTRELDOCS": [],  # 修复：应为列表类型
                "DEFAULTRELDOCS_IRS": "[]",
                "DOCUMENTLABELS": "",
                "DOCUMENT_DOCCONTENT": "",
                "FOCUSIMG": "",
                "FOCUSIMAGE": "[]",
                "DOCCOVERPIC": "[]",
                "CHNLHASCHILDREN": "0",
                "CLASSINFO_ID_PATHS": [],  # 修复：应为列表类型
                "CLASSINFO_IDS": [],  # 修复：应为列表类型
                "CLASSINFO_NAME_PATHS": [],  # 修复：应为列表类型
                "CLASSINFO_NAMES": [],  # 修复：应为列表类型
                "CHANNELTYPE": "",
                "ISFOCUSIMAGE": "否",
                "DOCUMENTLABELS": "",
                "LISTTITLE": "测试列表标题",
                "SITENAME": "测试网站",
                "DOCUMENT_DOCRELTIME": "2025-04-09 15:46:25"
            },
            "CHNLDOC": {
                "ISARCHIVE": "0",
                "DOCINFLOW": "0",
                "TIMEDSTATUS": "0",
                "OTHERVIEWMODE": "0",
                "POSCHNLID": "0",
                "SRCSITEID": "33",
                "DOCAUTHOR": "",
                "CARBONCOPYRECEIVERACTIONTYPE": "0",
                "ISREAD": "1",
                "ABOLITION": "0",
                "ATTACHPIC": "1",
                "DOCSOURCENAME": "",
                "FLOWID": "",
                "GDORDER": "0",
                "DATASENDMODE": "0",
                "ISTIMINGPUBLISH": "0",
                "DOCTYPE": "20",
                "DOCFIRSTPUBTIME": "2025-08-29 18:54:06",
                "CANPUB": "1",
                "CANEDIT": "true",
                "DOCORDER": "34",
                "PUBQUOTEDOC": "0",
                "RECID": "84085",
                "ACTIONTYPE": "3",
                "DOCCHANNEL": "2240",
                "PUSHUIRBSTATUS": "1",
                "CANCELPUBTIME": "",
                "PUSHRECEIVERACTIONTYPE": "0",
                "ISDELETED": "0",
                "INVALIDTIME": "",
                "CRUSER": "dev",
                "CRTIME": "2025-04-09 15:46:25",  # 创建时间
                "DOCORDERPRI": "0",
                "NEEDMANUALSYNC": "0",
                "OPERUSER": "dev",
                "DOCFIRSTPUBTIME": "2025-08-29 18:53:15",  # 文档首次发布时间
                "OPERTIME": "2025-08-29 18:54:06",
                "DOCPUBTIME": "2025-08-29 18:54:06",
                "DOCSTATUS": "10",
                "CRDEPT": "测试部门",
                "DOCRELTIME": "2025-04-09 15:46:25",
                "DOCLEVEL": "0",
                "REFUSESTATUS": "0",
                "ORIGINRECID": "76655",
                "DOCID": "64941",
                "CHNLID": "2240",
                "DISTRECEIVERACTIONTYPE": "0",
                "DOCPUBURL": "https://example.com/test.html",
                "ACTIONUSER": "dev",
                "ISMASTERCHNL": "0",
                "ARCHIVETIME": "",
                "DOCOUTUPID": "61261",
                "DISTSENDERACTIONTYPE": "0",
                "DOCKIND": "11",
                "CARBONCOPYSENDERACTIONTYPE": "0",
                "SITEID": "33",
                "PUBSTATUS": "1",
                "MODAL": "1",
                "PUSHSENDERACTIONTYPE": "0"
            },
            "CRUSER": "dev",
            "APPENDIX": [],
            "ID": "84085",
            "CHANNELDESCNAV": "测试描述",
            "TYPE": "1"
        }


class TestArchiveRequestSchema:
    """档案请求模型测试"""
    
    def test_create_valid_archive_request(self):
        """测试创建有效档案请求"""
        archive_data = ArchiveData(
            did="64941",
            wzmc="测试网站",
            dn="example.com",
            classfyname="新闻头条",
            classfy="XWTT",
            title="测试标题",
            author="测试作者",
            docdate="2025-04-09",
            year="2025",
            retentionperiod=30,
            fillingdepartment="测试部门",
            bly="testuser",
            attachment=[]
        )
        
        request = ArchiveRequestSchema.create_archive_request(
            app_id="NEWS",
            app_token="test_token",
            company_name="测试公司",
            archive_type="17",
            archive_data=archive_data
        )
        
        assert request.AppId == "NEWS"
        assert request.ArchiveData["did"] == "64941"
        assert request.ArchiveData["title"] == "测试标题"
        assert request.ArchiveData["classfyname"] == "新闻头条"
        assert request.ArchiveData["classfy"] == "XWTT"
    
    def test_invalid_docdate_format(self):
        """测试无效的文档日期格式"""
        with pytest.raises(ValueError, match="Invalid document date format"):
            ArchiveData(
                did="64941",
                wzmc="测试网站",
                dn="example.com",
                classfyname="新闻头条",
                classfy="XWTT",
                title="测试标题",
                docdate="invalid_date",
                year="2025",
                retentionperiod=30
            )
    
    def test_invalid_year(self):
        """测试无效年份"""
        with pytest.raises(ValueError, match="Invalid year format"):
            ArchiveData(
                did="64941",
                wzmc="测试网站",
                dn="example.com",
                classfyname="新闻头条",
                classfy="XWTT",
                title="测试标题",
                docdate="2025-04-09",
                year="invalid_year",
                retentionperiod=30
            )
    
    def test_invalid_retention_period(self):
        """测试无效保留期限"""
        with pytest.raises(ValueError, match="Retention period must be positive"):
            ArchiveData(
                did="64941",
                wzmc="测试网站",
                dn="example.com",
                classfyname="新闻头条",
                classfy="XWTT",
                title="测试标题",
                docdate="2025-04-09",
                year="2025",
                retentionperiod=-1
            )
    
    def test_attachment_data_creation(self):
        """测试附件数据创建"""
        attachment = AttachmentData(
            name="测试附件",
            ext=".jpg",
            file="https://example.com/test.jpg",
            type="图片"
        )
        
        assert attachment.name == "测试附件"
        assert attachment.ext == ".jpg"
        assert attachment.file == "https://example.com/test.jpg"
        assert attachment.type == "图片"
    
    def test_html_attachment_creation(self):
        """测试HTML附件创建"""
        attachment = AttachmentData.create_html_attachment(
            pub_url="https://example.com/test.html",
            title="测试标题"
        )
        
        assert attachment.name == "测试标题(正文)"
        assert attachment.ext == ".html"
        assert attachment.file == "https://example.com/test.html"
        assert attachment.type == "正文"
    
    def test_media_attachment_creation(self):
        """测试媒体附件创建"""
        # 测试图片
        image_attachment = AttachmentData.create_media_attachment(
            file_url="https://example.com/test.jpg",
            media_type="image",
            description="测试图片"
        )
        
        assert image_attachment.type == "图片"
        assert image_attachment.ext == ".jpg"
        
        # 测试视频
        video_attachment = AttachmentData.create_media_attachment(
            file_url="https://example.com/test.mp4",
            media_type="video",
            description="测试视频"
        )
        
        assert video_attachment.type == "视频"
        assert video_attachment.ext == ".mp4"
    
    def test_archive_data_attachment_management(self):
        """测试档案数据附件管理"""
        archive_data = ArchiveData(
            did="64941",
            wzmc="测试网站",
            dn="example.com",
            classfyname="新闻头条",
            classfy="XWTT",
            title="测试标题",
            docdate="2025-04-09",
            year="2025",
            retentionperiod=30
        )
        
        # 添加HTML附件
        archive_data.add_html_attachment(
            pub_url="https://example.com/test.html",
            title="测试标题"
        )
        
        assert len(archive_data.attachment) == 1
        assert archive_data.attachment[0].type == "正文"
        
        # 添加媒体附件
        archive_data.add_media_attachment(
            file_url="https://example.com/test.jpg",
            media_type="image",
            description="测试图片"
        )
        
        assert len(archive_data.attachment) == 2
        assert archive_data.get_attachment_count() == 2
        
        # 按类型获取附件
        html_attachments = archive_data.get_attachment_by_type("正文")
        assert len(html_attachments) == 1
        assert html_attachments[0].type == "正文"
    
    def test_archive_response_creation(self):
        """测试档案响应创建"""
        # 成功响应
        success_response = ArchiveResponseSchema.from_success(
            message="操作成功",
            data={"id": "123"}
        )
        
        assert success_response.success is True
        assert success_response.message == "操作成功"
        assert success_response.data == {"id": "123"}
        
        # 错误响应
        error_response = ArchiveResponseSchema.from_error(
            message="操作失败",
            error_code="ERROR_CODE",
            data={"error": "details"}
        )
        
        assert error_response.success is False
        assert error_response.message == "操作失败"
        assert error_response.error_code == "ERROR_CODE"
        assert error_response.data == {"error": "details"}
    
    def test_from_json_response(self):
        """测试从JSON创建响应"""
        response_data = {
            "success": True,
            "message": "操作成功",
            "data": {"id": "123"},
            "timestamp": "2025-01-01T00:00:00"
        }
        
        json_str = json.dumps(response_data)
        response = ArchiveResponseSchema.from_json(json_str)
        
        assert response.success is True
        assert response.message == "操作成功"
        assert response.data == {"id": "123"}