"""
数据转换器单元测试
测试FieldMapper、AttachmentBuilder和DataTransformer的功能
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json
from hydocpusher.transformer.field_mapper import FieldMapper
from hydocpusher.transformer.attachment_builder import AttachmentBuilder
from hydocpusher.transformer.data_transformer import DataTransformer
from hydocpusher.models.message_models import SourceMessageSchema, AppendixInfo, AttachmentItem
from hydocpusher.models.archive_models import ArchiveData, AttachmentData, ArchiveRequestSchema
from hydocpusher.exceptions.custom_exceptions import DataTransformException, ValidationException


class TestFieldMapper:
    """字段映射器测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.field_mapper = FieldMapper()
    
    def test_map_basic_field(self):
        """测试基本字段映射"""
        result = self.field_mapper.map_field("DOCTITLE", "测试标题")
        assert result == {"title": "测试标题"}
    
    def test_map_nonexistent_field(self):
        """测试不存在字段的映射"""
        result = self.field_mapper.map_field("NONEXISTENT", "测试值")
        assert result == {}
    
    def test_map_field_with_none_value(self):
        """测试空值字段映射"""
        result = self.field_mapper.map_field("DOCTITLE", None)
        assert result == {}
    
    def test_map_classification(self):
        """测试分类映射"""
        result = self.field_mapper.map_classification("2240")
        assert "classfyname" in result
        assert "classfy" in result
    
    def test_map_document_info(self):
        """测试文档信息映射"""
        source_data = {
            "RECID": "64941",  # 根据PRD文档更新：RECID映射到did
            "DOCTITLE": "测试标题",
            "DOCFIRSTPUBTIME": "2025-04-09 15:46:25",  # 根据PRD文档更新：DOCFIRSTPUBTIME映射到docdate
            "CHANNELID": "2240",
            "CRUSER": "testuser",
            "TXY": "测试作者",
            "CRDEPT": "测试部门"  # 添加部门字段测试
        }
        
        result = self.field_mapper.map_document_info(source_data)
        
        # 验证字段存在性
        assert "did" in result
        assert "title" in result
        assert "docdate" in result
        assert "year" in result
        assert "wzmc" in result
        assert "dn" in result
        assert "classfyname" in result
        assert "classfy" in result
        assert "retentionperiod" in result
        assert "author" in result
        assert "fillingdepartment" in result
        assert "bly" in result
        
        # 验证固定值字段
        assert result["wzmc"] == "集团门户"
        assert result["dn"] == "www.cnyeig.com"
        assert result["retentionperiod"] == 30
        
        # 验证映射字段
        assert result["did"] == "64941"
        assert result["title"] == "测试标题"
        assert result["author"] == "测试作者"
        assert result["bly"] == "testuser"
        assert result["fillingdepartment"] == "测试部门"
    
    def test_convert_date(self):
        """测试日期转换"""
        # 测试标准格式
        result = self.field_mapper._convert_date("2025-04-09 15:46:25")
        assert result == "2025-04-09"
        
        # 测试日期格式
        result = self.field_mapper._convert_date("2025-04-09")
        assert result == "2025-04-09"
        
        # 测试其他格式
        result = self.field_mapper._convert_date("2025/04/09")
        assert result == "2025-04-09"
        
        # 测试无效格式
        result = self.field_mapper._convert_date("invalid_date")
        assert result == ""
    
    def test_convert_year(self):
        """测试年份转换"""
        result = self.field_mapper._convert_year("2025-04-09 15:46:25")
        assert result == "2025"
        
        result = self.field_mapper._convert_year("invalid_date")
        assert result == ""
    
    def test_convert_retention_period(self):
        """测试保留期限转换"""
        result = self.field_mapper._convert_retention_period("30")
        assert result == 30
        
        result = self.field_mapper._convert_retention_period("invalid")
        assert isinstance(result, int)
        assert result > 0
    
    def test_convert_string(self):
        """测试字符串转换"""
        result = self.field_mapper._convert_string("  测试字符串  ")
        assert result == "测试字符串"
        
        result = self.field_mapper._convert_string("")
        assert result == ""
        
        result = self.field_mapper._convert_string(None)
        assert result == ""
    
    def test_validate_mapped_data(self):
        """测试映射数据验证"""
        # 有效数据
        valid_data = {
            "did": "64941",
            "title": "测试标题",
            "wzmc": "测试网站",
            "dn": "example.com",
            "classfyname": "新闻头条",
            "classfy": "XWTT",
            "docdate": "2025-04-09",
            "year": "2025",
            "retentionperiod": 30
        }
        
        # 应该不抛出异常
        self.field_mapper.validate_mapped_data(valid_data)
        
        # 缺少必需字段
        invalid_data = {
            "did": "64941",
            "title": "测试标题"
            # 缺少其他必需字段
        }
        
        with pytest.raises(ValidationException):
            self.field_mapper.validate_mapped_data(invalid_data)
    
    def test_get_mapping_summary(self):
        """测试获取映射摘要"""
        summary = self.field_mapper.get_mapping_summary()
        
        assert "field_mappings" in summary
        assert "default_values" in summary
        assert "company_name" in summary
        assert "domain" in summary
        assert "date_formats" in summary
        assert "classification_config_loaded" in summary


class TestAttachmentBuilder:
    """附件构建器测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.attachment_builder = AttachmentBuilder(domain="www.cnyeig.com")
    
    def test_build_html_attachment(self):
        """测试HTML附件构建"""
        attachment = self.attachment_builder.build_html_attachment(
            pub_url="https://example.com/test.html",
            document_title="测试标题"
        )
        
        assert attachment.name == "测试标题(正文)"
        assert attachment.ext == ".html"
        assert attachment.file == "https://example.com/test.html"
        assert attachment.type == "正文"
    
    def test_build_html_attachment_with_empty_url(self):
        """测试空URL的HTML附件构建"""
        with pytest.raises(ValidationException):
            self.attachment_builder.build_html_attachment(
                pub_url="",
                document_title="测试标题"
            )
    
    def test_build_attachments(self):
        """测试附件列表构建"""
        appendix_list = [
            AppendixInfo(APPFILE="/test/video.mp4", APPFLAG="50"),
            AppendixInfo(APPFILE="/test/image.jpg", APPFLAG="20")
        ]
        
        attachments = self.attachment_builder.build_attachments_legacy(
            appendix_list=appendix_list,
            document_title="测试标题"
        )
        
        assert len(attachments) == 2
        assert attachments[0].type in ["视频", "图片"]
        assert attachments[1].type in ["视频", "图片"]
    
    def test_build_attachments_with_empty_list(self):
        """测试空附件列表构建"""
        attachments = self.attachment_builder.build_attachments_legacy(
            appendix_list=[],
            document_title="测试标题"
        )
        
        assert len(attachments) == 0
    
    def test_get_attachment_type(self):
        """测试附件类型获取"""
        # 测试视频
        attachment_type = self.attachment_builder._get_attachment_type("50", "/test.mp4")
        assert attachment_type == "视频"
        
        # 测试图片
        attachment_type = self.attachment_builder._get_attachment_type("20", "/test.jpg")
        assert attachment_type == "图片"
        
        # 测试其他类型
        attachment_type = self.attachment_builder._get_attachment_type("70", "/test.file")
        assert attachment_type == "其他"
    
    def test_get_file_extension(self):
        """测试文件扩展名获取"""
        # 测试从URL获取扩展名
        ext = self.attachment_builder._get_file_extension("https://example.com/test.jpg", "图片")
        assert ext == ".jpg"
        
        # 测试没有扩展名的情况
        ext = self.attachment_builder._get_file_extension("https://example.com/test", "图片")
        assert ext == ".jpg"
    
    def test_extract_file_extension(self):
        """测试文件扩展名提取"""
        ext = self.attachment_builder._extract_file_extension("https://example.com/test.jpg")
        assert ext == "jpg"
        
        ext = self.attachment_builder._extract_file_extension("https://example.com/test.jpg?param=value")
        assert ext == "jpg"
        
        ext = self.attachment_builder._extract_file_extension("https://example.com/test")
        assert ext == ""
    
    def test_validate_url(self):
        """测试URL验证"""
        # 有效URL
        self.attachment_builder._validate_url("https://example.com/test.jpg")
        self.attachment_builder._validate_url("http://example.com/test.jpg")
        self.attachment_builder._validate_url("/relative/path/test.jpg")
        
        # 无效URL
        with pytest.raises(ValidationException):
            self.attachment_builder._validate_url("")
        with pytest.raises(ValidationException):
            self.attachment_builder._validate_url("invalid_url")
    
    def test_build_attachments_with_multiple_fields(self):
        """测试支持多种附件字段的新功能"""
        # 创建测试消息数据
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
                "DATA": {
                    "ISFOCUSIMAGE": "否",
                    "DOCUMENTLABELS": "",
                    "CLASSINFO_ID_PATHS": [],
                    "CHANNELID": "2240",
                    "DOCAUTHOR": "",
                    "DOCCOVERPIC": "[]",
                    "ATTACHPIC": "1",
                    "DOCSOURCENAME": "",
                    "LISTSTYLE": "4",
                    "PARENTCHNLDESC": "",
                    "COMMENTFLAG": "0",
                    "CLASSINFO_NAMES": [],
                    "CHNLHASCHILDREN": "0",
                    "THUMBFILES": "W020250829679959407981.jpg",
                    "LABEL": "",
                    "DOCTYPE": "20",
                    "LISTTITLE": "测试 裸眼3D看云能",
                    "LISTPICS": "[]",
                    "SITENAME": "测试推送",
                    "DOCUMENT_RELATED_APPENDIX": "[]",
                    "CHANNELTYPE": "",
                    "SEARCHWORDVALUE": "",
                    "DOCORDER": "34",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "DOCUMENT_CONTENT_APPENDIX": "[]",
                    "FOCUSIMG": "",
                    "LISTIMGURLS": "",
                    "METADATAID": "64941",
                    "CLASSINFO_IDS": [],
                    "DEFAULTRELDOCS": [],
                    "DOCFILENAME": "",
                    "SITEDESC": "数字能投订阅号推送",
                    "DOCHTMLCON": '<div><img src="/test/image.jpg" /><a href="/test/doc.pdf">链接</a></div>',
                    "DOCUMENT_RELATED_VIDEO": '[{"APPDESC":"视频1","APPURL":"/test/video1.mp4","APPENDIXID":123}]',
                    "CRUSER": "dev",
                    "DOCUMENT_DOCRELTIME": "2025-04-09 15:46:25",
                    "DEFAULTRELDOCS_IRS": "[]",
                    "DOCUMENT_CONTENT_PIC": "[]",
                    "SHORTTITLE": "",
                    "CRTIME": "2025-08-29 18:53:16",
                    "MEDIATYPE": "2",
                    "DOCPEOPLE": "",
                    "DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCCONTENT": "",
                    "CHNLDOC_OPERTIME": "2025-08-29 18:54:06",
                    "FOCUSFILENAME": "",
                    "DOCTITLE": "测试标题",
                    "TXY": "集团党群部",
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html",
                    "DOCUMENT_CONTENT_VIDEO": '[{"APPDESC":"内容视频","APPURL":"/test/video2.mp4","APPENDIXID":456}]',
                    "DOCLINK": "",
                    "VERSIONNUM": "0",
                    "FOCUSIMAGE": "[]",
                    "FROMID": "",
                    "CLASSINFO_NAME_PATHS": [],
                    "SUBDOCTITLE": "",
                    "DOCKEYWORDS": "",
                    "TITLECOLOR": "",
                    "CLASSIFICATIONID": "6",
                    "ORIGINMETADATAID": "61261",
                    "SITEID": "33",
                    "CHNLDESC": "数字能投推送测试",
                    "PUBSTATUS": "1",
                    "MODAL": "1",
                    "ATTACHVIDEO": "1",
                    "DOCUMENT_DOCCONTENT": "",
                    "CHNLNAME": "新闻头条_2240",
                    "DOCPLACE": "",
                    "DOCUMENT_RELATED_PIC": '[{"APPDESC":"图片1","APPURL":"/test/pic1.jpg","APPENDIXID":789}]',
                    "DOCABSTRACT": "",
                    "FOCUSTITLE": "",
                    "FOCUSDESC": "",
                    "WCMMETATABLEGOVDOCNEWSAPPID": "68",
                    "WEBHTTP": "https://www.cnyeig.com/csts",
                    "FOCUSIMAGETITLE": ""
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
                    "DOCORDERPRI": "0",
                    "NEEDMANUALSYNC": "0",
                    "OPERUSER": "dev",
                    "CRTIME": "2025-08-29 18:53:15",
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
                    {"APPFILE": "/masvod/public/2025/04/09/20250409_196198623cd_r1_1200k.mp4", "APPFLAG": "50"},
                    {"APPFILE": "W020250829679959407981.jpg", "APPFLAG": "20"}
                ],
                "appdix": [
                    {"APPFILE": "/test/appdix_video.mp4", "APPFLAG": "50"}
                ],
                "attachments": [
                    {"APPDESC": "新格式附件", "APPURL": "/test/new_attachment.pdf", "APPENDIXID": 999}
                ],
                "ID": "84085",
                "CHANNELDESCNAV": "数字能投推送测试",
                "TYPE": "1"
            },
            "ISSUCCESS": "true"
        }
        
        message = SourceMessageSchema(**message_data)
        
        # 测试新的附件构建方法
        attachments = self.attachment_builder.build_attachments(message)
        
        # 应该包含多种类型的附件
        assert len(attachments) > 0
        
        # 检查是否有HTML正文附件
        html_attachments = [a for a in attachments if a.type == "正文"]
        assert len(html_attachments) > 0
        
        # 检查是否有从HTML内容提取的附件
        html_extracted = [a for a in attachments if a.name in ["link附件", "image附件"]]
        assert len(html_extracted) > 0
        
        # 检查是否有JSON格式附件
        json_attachments = [a for a in attachments if "视频" in a.name or "图片" in a.name]
        assert len(json_attachments) > 0
        
        # 检查是否有传统APPENDIX附件
        traditional_attachments = [a for a in attachments if a.name.startswith("附件")]
        assert len(traditional_attachments) > 0
    
    def test_build_absolute_url(self):
        """测试绝对URL构建"""
        # 测试相对路径
        absolute_url = self.attachment_builder._build_absolute_url("/test/path/file.jpg")
        assert absolute_url == "http://www.cnyeig.com/test/path/file.jpg"
        
        # 测试W后缀图片地址
        w_suffix_url = self.attachment_builder._build_absolute_url("W020250829679959407981.jpg")
        assert w_suffix_url == "http://www.cnyeig.com/W020250829679959407981.jpg"
        
        # 测试已经是绝对URL
        full_url = self.attachment_builder._build_absolute_url("https://example.com/file.jpg")
        assert full_url == "https://example.com/file.jpg"
    
    def test_extract_html_attachments(self):
        """测试HTML内容附件提取"""
        html_content = '''
        <div>
            <a href="/test/document.pdf">文档链接</a>
            <img src="/test/image.jpg" alt="图片" />
            <iframe src="/test/video.mp4"></iframe>
        </div>
        '''
        
        attachments = self.attachment_builder._extract_html_attachments(html_content)
        
        # 应该提取到3个附件
        assert len(attachments) == 3
        
        # 检查附件类型
        types = [a.type for a in attachments]
        assert "文档" in types
        assert "图片" in types
        assert "视频" in types
    
    def test_parse_json_attachments(self):
        """测试JSON格式附件解析"""
        json_content = '[{"APPDESC":"测试视频","APPURL":"/test/video.mp4","APPENDIXID":123}]'
        
        attachments = self.attachment_builder._parse_json_attachments(json_content, "DOCUMENT_RELATED_VIDEO")
        
        assert len(attachments) == 1
        assert attachments[0].name == "测试视频"
        assert attachments[0].file == "http://www.cnyeig.com/test/video.mp4"
        assert attachments[0].type == "视频"
    
    def test_determine_attachment_type(self):
        """测试附件类型确定"""
        # 测试各种文件类型
        assert self.attachment_builder._determine_attachment_type("test.jpg") == "图片"
        assert self.attachment_builder._determine_attachment_type("test.mp4") == "视频"
        assert self.attachment_builder._determine_attachment_type("test.mp3") == "音频"
        assert self.attachment_builder._determine_attachment_type("test.pdf") == "文档"
        assert self.attachment_builder._determine_attachment_type("test.unknown") == "其他"
    
    def test_is_attachment_url(self):
        """测试附件URL判断"""
        # 测试各种文件扩展名
        assert self.attachment_builder._is_attachment_url("/test/file.pdf")
        assert self.attachment_builder._is_attachment_url("/test/file.jpg")
        assert self.attachment_builder._is_attachment_url("/test/file.mp4")
        assert not self.attachment_builder._is_attachment_url("/test/page.html")
        assert not self.attachment_builder._is_attachment_url("/test/")
    
    def test_create_attachment_from_url(self):
        """测试从URL创建附件"""
        attachment = self.attachment_builder._create_attachment_from_url("/test/file.jpg", "测试")
        
        assert attachment is not None
        assert attachment.name == "测试附件"
        assert attachment.ext == ".jpg"
        assert attachment.file == "http://www.cnyeig.com/test/file.jpg"
        assert attachment.type == "图片"
    
    def test_convert_w_suffix_address(self):
        """测试W后缀地址转换"""
        # 测试W后缀图片地址
        w_address = "W020250829679959407981.jpg"
        converted = self.attachment_builder._convert_w_suffix_address(w_address)
        assert converted == w_address  # 现阶段应该返回原地址
        
        # 测试非W后缀地址
        normal_address = "/test/normal.jpg"
        converted = self.attachment_builder._convert_w_suffix_address(normal_address)
        assert converted == normal_address
    
    def test_filter_attachments(self):
        """测试附件过滤"""
        attachments = [
            AttachmentData(name="正文", ext=".html", file="https://example.com/test.html", type="正文"),
            AttachmentData(name="图片", ext=".jpg", file="https://example.com/test.jpg", type="图片"),
            AttachmentData(name="视频", ext=".mp4", file="https://example.com/test.mp4", type="视频"),
        ]
        
        filtered = self.attachment_builder.filter_attachments(attachments, max_count=2)
        assert len(filtered) == 2
        
        # 检查优先级排序
        assert filtered[0].type == "正文"
    
    def test_get_attachment_summary(self):
        """测试附件摘要"""
        attachments = [
            AttachmentData(name="正文", ext=".html", file="https://example.com/test.html", type="正文"),
            AttachmentData(name="图片1", ext=".jpg", file="https://example.com/test1.jpg", type="图片"),
            AttachmentData(name="图片2", ext=".png", file="https://example.com/test2.png", type="图片"),
        ]
        
        summary = self.attachment_builder.get_attachment_summary(attachments)
        
        assert summary["total_count"] == 3
        assert summary["by_type"]["正文"] == 1
        assert summary["by_type"]["图片"] == 2
        assert "正文" in summary["types"]
        assert "图片" in summary["types"]


class TestDataTransformer:
    """数据转换器测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.data_transformer = DataTransformer()
    
    def test_transform_message_success(self):
        """测试成功消息转换"""
        # 创建测试消息
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
                "DATA": {
                    "ISFOCUSIMAGE": "否",
                    "DOCUMENTLABELS": "",
                    "CLASSINFO_ID_PATHS": [],
                    "CHANNELID": "2240",
                    "DOCAUTHOR": "",
                    "DOCCOVERPIC": "[]",
                    "ATTACHPIC": "1",
                    "DOCSOURCENAME": "",
                    "LISTSTYLE": "4",
                    "PARENTCHNLDESC": "",
                    "COMMENTFLAG": "0",
                    "CLASSINFO_NAMES": [],
                    "CHNLHASCHILDREN": "0",
                    "THUMBFILES": "W020250829679959407981.jpg",
                    "LABEL": "",
                    "DOCTYPE": "20",
                    "LISTTITLE": "测试 裸眼3D看云能",
                    "LISTPICS": "[]",
                    "SITENAME": "测试推送",
                    "DOCUMENT_RELATED_APPENDIX": "[]",
                    "CHANNELTYPE": "",
                    "SEARCHWORDVALUE": "",
                    "DOCORDER": "34",
                    "RECID": "84085",
                    "ACTIONTYPE": "3",
                    "DOCUMENT_CONTENT_APPENDIX": "[]",
                    "FOCUSIMG": "",
                    "LISTIMGURLS": "",
                    "METADATAID": "64941",
                    "CLASSINFO_IDS": [],
                    "DEFAULTRELDOCS": [],
                    "DOCFILENAME": "",
                    "SITEDESC": "数字能投订阅号推送",
                    "DOCHTMLCON": "<div class=\"trs_editor_view TRS_UEDITOR trs_paper_default\"><p style=\"text-align: center\"><iframe frameborder=\"0\" masid=\"186\" class=\"edui-upload-video video-js vjs-default-skin\" src=\"/mas/openapi/pages.do?method=exPlay&appKey=gov&id=186&autoPlay=false\" width=\"3840\" height=\"2160\" name=\"裸眼3d1.mp4\" appendix=\"true\" allowfullscreen=\"true\" style=\"\"></iframe></p><p><br/></p></div>",
                    "DOCUMENT_RELATED_VIDEO": "[{\"APPDESC\":\"裸眼3d1\",\"APPURL\":\"/masvod/public/2025/04/09/186.images/v186_b1744184962825.jpg\",\"APPENDIXID\":84988}]",
                    "CRUSER": "dev",
                    "DOCUMENT_DOCRELTIME": "2025-04-09 15:46:25",
                    "DEFAULTRELDOCS_IRS": "[]",
                    "DOCUMENT_CONTENT_PIC": "[]",
                    "SHORTTITLE": "",
                    "CRTIME": "2025-08-29 18:53:16",
                    "MEDIATYPE": "2",
                    "DOCPEOPLE": "",
                    "DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCCONTENT": "",
                    "CHNLDOC_OPERTIME": "2025-08-29 18:54:06",
                    "FOCUSFILENAME": "",
                    "DOCTITLE": "测试标题",
                    "TXY": "集团党群部",
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html",
                    "DOCUMENT_CONTENT_VIDEO": "[{\"APPDESC\":\"裸眼3d1\",\"APPURL\":\"/masvod/public/2025/04/09/186.images/v186_b1744184962825.jpg\",\"APPENDIXID\":84986},{\"APPDESC\":\"裸眼3d1\",\"APPURL\":\"/masvod/public/2025/04/09/186.images/v186_b1744184962825.jpg\",\"APPENDIXID\":84989}]",
                    "DOCLINK": "",
                    "VERSIONNUM": "0",
                    "FOCUSIMAGE": "[]",
                    "FROMID": "",
                    "CLASSINFO_NAME_PATHS": [],
                    "SUBDOCTITLE": "",
                    "DOCKEYWORDS": "",
                    "TITLECOLOR": "",
                    "CLASSIFICATIONID": "6",
                    "ORIGINMETADATAID": "61261",
                    "SITEID": "33",
                    "CHNLDESC": "数字能投推送测试",
                    "PUBSTATUS": "1",
                    "MODAL": "1",
                    "ATTACHVIDEO": "1",
                    "DOCUMENT_DOCCONTENT": "",
                    "CHNLNAME": "新闻头条_2240",
                    "DOCPLACE": "",
                    "DOCUMENT_RELATED_PIC": "[{\"APPDESC\":\"裸眼3d1_0001.jpg\",\"APPURL\":\"https://www.cnyeig.com/csts/test_2240/202508/W020250829679959407981.jpg\",\"APPENDIXID\":84987}]",
                    "DOCABSTRACT": "",
                    "FOCUSTITLE": "",
                    "FOCUSDESC": "",
                    "WCMMETATABLEGOVDOCNEWSAPPID": "68",
                    "WEBHTTP": "https://www.cnyeig.com/csts",
                    "FOCUSIMAGETITLE": ""
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
                    "DOCORDERPRI": "0",
                    "NEEDMANUALSYNC": "0",
                    "OPERUSER": "dev",
                    "CRTIME": "2025-08-29 18:53:15",
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
                "APPENDIX": [{
                    "APPFILE": "/masvod/public/2025/04/09/20250409_196198623cd_r1_1200k.mp4",
                    "APPFLAG": "50"
                }, {
                    "APPFILE": "/mas/openapi/pages.do?method=exPlay&appKey=gov&id=186&autoPlay=false",
                    "APPFLAG": "140"
                }, {
                    "APPFILE": "/mas/openapi/pages.do?method=exPlay&appKey=gov&id=186&autoPlay=false",
                    "APPFLAG": "140"
                }, {
                    "APPFILE": "W020250829679959407981.jpg",
                    "APPFLAG": "20"
                }],
                "ID": "84085",
                "CHANNELDESCNAV": "数字能投推送测试",
                "TYPE": "1"
            },
            "ISSUCCESS": "true"
        }
        
        source_message = SourceMessageSchema(**message_data)
        
        # 执行转换
        result = self.data_transformer.transform_message(source_message)
        
        # 打印转换结果 - 详细输出
        print("\n=== 转换结果详情 ===")
        print(f"AppId: {result.AppId}")
        print(f"ArchiveData keys: {list(result.ArchiveData.keys())}")
        print(f"Document ID: {result.ArchiveData.get('did')}")
        print(f"Document Title: {result.ArchiveData.get('title')}")
        print(f"Attachments count: {len(result.ArchiveData.get('attachment', []))}")
        import json
        print(f"Complete result (JSON): {json.dumps(result.model_dump(), indent=2, ensure_ascii=False)}")
        print("=== 转换结果结束 ===\n")
        
        # 验证结果
        assert isinstance(result, ArchiveRequestSchema)
        assert result.AppId == "NEWS"
        assert result.ArchiveData["did"] == "84085"  # 根据PRD文档，did取DATA.DATA.RECID的值
        assert result.ArchiveData["title"] == "测试标题"
        assert result.ArchiveData["wzmc"] == "集团门户"  # 验证固定值
        assert result.ArchiveData["dn"] == "www.cnyeig.com"  # 验证固定值
        assert result.ArchiveData["retentionperiod"] == 30  # 验证固定值
        assert len(result.ArchiveData["attachment"]) > 0
    
    def test_transform_message_from_dict(self):
        """测试从字典转换消息"""
        message_dict = {
            "MSG": "操作成功",
            "DATA": {
                "SITENAME": "测试推送",
                "CRTIME": "2025-08-29 18:53:15",  # 创建时间
                "CHANNELID": "2240",
                "VIEWID": "11",
                "VIEWNAME": "GovDocNewsAPP",
                "SITEID": "33",
                "DOCID": "84085",  # 修复：与ID保持一致
                "OPERTYPE": "1",
                "CHANNELNAV": "2240",
                "DATA": {
                    "ISFOCUSIMAGE": "否",
                    "DOCUMENTLABELS": "",
                    "CLASSINFO_ID_PATHS": [],
                    "CHANNELID": "2240",
                    "DOCAUTHOR": "",
                    "DOCCOVERPIC": "[]",
                    "ATTACHPIC": "1",
                    "DOCSOURCENAME": "",
                    "LISTSTYLE": "4",
                    "PARENTCHNLDESC": "",
                    "COMMENTFLAG": "0",
                    "CLASSINFO_NAMES": [],
                    "CHNLHASCHILDREN": "0",
                    "THUMBFILES": "W020250829679959407981.jpg",
                    "LABEL": "",
                    "DOCTYPE": "20",
                    "LISTTITLE": "测试 裸眼3D看云能",
                    "LISTPICS": "[]",
                    "SITENAME": "测试推送",
                    "DOCUMENT_RELATED_APPENDIX": "[]",
                    "CHANNELTYPE": "",
                    "SEARCHWORDVALUE": "",
                    "DOCORDER": "34",
                    "RECID": "84085",  # 修复：与断言期望值保持一致
                    "ACTIONTYPE": "3",
                    "DOCUMENT_CONTENT_APPENDIX": "[]",
                    "FOCUSIMG": "",
                    "LISTIMGURLS": "",
                    "METADATAID": "84085",  # 修复：与RECID保持一致
                    "CLASSINFO_IDS": [],
                    "DEFAULTRELDOCS": [],  # 修复：改为列表类型
                    "DOCFILENAME": "",
                    "SITEDESC": "数字能投订阅号推送",
                    "DOCHTMLCON": "<div class=\"trs_editor_view TRS_UEDITOR trs_paper_default\"><p style=\"text-align: center\"><iframe frameborder=\"0\" masid=\"186\" class=\"edui-upload-video video-js vjs-default-skin\" src=\"/mas/openapi/pages.do?method=exPlay&appKey=gov&id=186&autoPlay=false\" width=\"3840\" height=\"2160\" name=\"裸眼3d1.mp4\" appendix=\"true\" allowfullscreen=\"true\" style=\"\"></iframe></p><p><br/></p></div>",
                    "DOCUMENT_RELATED_VIDEO": "[{\"APPDESC\":\"裸眼3d1\",\"APPURL\":\"/masvod/public/2025/04/09/186.images/v186_b1744184962825.jpg\",\"APPENDIXID\":84988}]",
                    "CRUSER": "dev",
                    "DOCUMENT_DOCRELTIME": "2025-04-09 15:46:25",
                    "DEFAULTRELDOCS_IRS": "[]",
                    "DOCUMENT_CONTENT_PIC": "[]",
                    "SHORTTITLE": "",
                    "CRTIME": "2025-08-29 18:53:16",  # 创建时间
                    "MEDIATYPE": "2",
                    "DOCPEOPLE": "",
                    "DOCRELTIME": "2025-04-09 15:46:25",
                    "DOCCONTENT": "",
                    "CHNLDOC_OPERTIME": "2025-08-29 18:54:06",
                    "FOCUSFILENAME": "",
                    "DOCTITLE": "测试标题",  # 修复：与断言期望值保持一致
                    "TXY": "集团党群部",
                    "DOCPUBURL": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html",
                    "DOCUMENT_CONTENT_VIDEO": "[{\"APPDESC\":\"裸眼3d1\",\"APPURL\":\"/masvod/public/2025/04/09/186.images/v186_b1744184962825.jpg\",\"APPENDIXID\":84986},{\"APPDESC\":\"裸眼3d1\",\"APPURL\":\"/masvod/public/2025/04/09/186.images/v186_b1744184962825.jpg\",\"APPENDIXID\":84989}]",
                    "DOCLINK": "",
                    "VERSIONNUM": "0",
                    "FOCUSIMAGE": "[]",
                    "FROMID": "",
                    "CLASSINFO_NAME_PATHS": [],
                    "SUBDOCTITLE": "",
                    "DOCKEYWORDS": "",
                    "TITLECOLOR": "",
                    "CLASSIFICATIONID": "6",
                    "ORIGINMETADATAID": "61261",
                    "SITEID": "33",
                    "CHNLDESC": "数字能投推送测试",
                    "PUBSTATUS": "1",
                    "MODAL": "1",
                    "ATTACHVIDEO": "1",
                    "DOCUMENT_DOCCONTENT": "",
                    "CHNLNAME": "新闻头条_2240",
                    "DOCPLACE": "",
                    "DOCUMENT_RELATED_PIC": "[{\"APPDESC\":\"裸眼3d1_0001.jpg\",\"APPURL\":\"https://www.cnyeig.com/csts/test_2240/202508/W020250829679959407981.jpg\",\"APPENDIXID\":84987}]",
                    "DOCABSTRACT": "",
                    "FOCUSTITLE": "",
                    "FOCUSDESC": "",
                    "WCMMETATABLEGOVDOCNEWSAPPID": "68",
                    "WEBHTTP": "https://www.cnyeig.com/csts",
                    "FOCUSIMAGETITLE": ""
                },
                "CHNLDOC": {
                    "ISARCHIVE": "0",
                    "DOCINFLOW": "0",
                    "TIMEDSTATUS": "0",
                    "OTHERVIEWMODE": "0",
                    "POSCHNLID": "0",
                    "SRCSITEID": "33",
                    "DOCAUTHOR": "",
                    "CRTIME": "2025-04-09 15:46:25",  # 创建时间
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
                    "RECID": "84085",  # 修复：与断言期望值保持一致
                    "ACTIONTYPE": "3",
                    "DOCCHANNEL": "2240",
                    "PUSHUIRBSTATUS": "1",
                    "CANCELPUBTIME": "",
                    "PUSHRECEIVERACTIONTYPE": "0",
                    "ISDELETED": "0",
                    "INVALIDTIME": "",
                    "CRUSER": "dev",
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
                    "DOCID": "84085",  # 修复：与RECID保持一致
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
                "APPENDIX": [{
                    "APPFILE": "/masvod/public/2025/04/09/20250409_196198623cd_r1_1200k.mp4",
                    "APPFLAG": "50"
                }, {
                    "APPFILE": "/mas/openapi/pages.do?method=exPlay&appKey=gov&id=186&autoPlay=false",
                    "APPFLAG": "140"
                }, {
                    "APPFILE": "/mas/openapi/pages.do?method=exPlay&appKey=gov&id=186&autoPlay=false",
                    "APPFLAG": "140"
                }, {
                    "APPFILE": "W020250829679959407981.jpg",
                    "APPFLAG": "20"
                }],
                "ID": "84085",
                "CHANNELDESCNAV": "数字能投推送测试",
                "TYPE": "1"
            },
            "ISSUCCESS": "true"
        }
        
        result = self.data_transformer.transform_message_from_dict(message_dict)
        
        assert isinstance(result, ArchiveRequestSchema)
        assert result.ArchiveData["did"] == "84085"  # 修复：与修改后的RECID保持一致
        assert result.ArchiveData["title"] == "测试标题"
    
    def test_get_transform_stats(self):
        """测试获取转换统计"""
        stats = self.data_transformer.get_transform_stats()
        
        assert "total_transformed" in stats
        assert "successful_transforms" in stats
        assert "failed_transforms" in stats
        assert "last_transform_time" in stats
    
    def test_reset_stats(self):
        """测试重置统计"""
        # 先执行一次转换
        message_dict = {
            "MSG": "操作成功",
            "DATA": {
                "SITENAME": "测试网站",
                "CRTIME": "2025-08-29 18:53:15",
                "CHANNELID": "2240",
                "VIEWID": "11",
                "VIEWNAME": "测试视图",
                "SITEID": "33",
                "DOCID": "84085",  # 修复：与ID保持一致
                "OPERTYPE": "1",
                "CHANNELNAV": "2240",
                "CRTIME": "2025-04-09 15:46:25",  # 创建时间
                "DATA": {
                    "ISFOCUSIMAGE": "否",
                    "CHANNELID": "2240",
                    "DOCTITLE": "测试标题",
                    "CRTIME": "2025-04-09 15:46:25",  # 创建时间
                    "DOCPUBURL": "https://example.com/test.html",
                    "RECID": "84085",  # 修复：与断言期望值保持一致
                    "ACTIONTYPE": "3",
                    "METADATAID": "84085",  # 修复：与RECID保持一致
                    "CRUSER": "dev",
                    "DOCTYPE": "20",
                    "DOCORDER": "34",
                    "SITEDESC": "测试站点",
                    "DOCHTMLCON": "<div>测试内容</div>",
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
                    "TXY": "测试作者",
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
                    "CRTIME": "2025-04-09 15:46:25",  # 创建时间
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
                    "RECID": "64941",  # 修复：与断言期望值保持一致
                    "ACTIONTYPE": "3",
                    "DOCCHANNEL": "2240",
                    "PUSHUIRBSTATUS": "1",
                    "CANCELPUBTIME": "",
                    "PUSHRECEIVERACTIONTYPE": "0",
                    "ISDELETED": "0",
                    "INVALIDTIME": "",
                    "CRUSER": "dev",
                    "DOCORDERPRI": "0",
                    "NEEDMANUALSYNC": "0",
                    "OPERUSER": "dev",
                    "CRTIME": "2025-08-29 18:53:15",
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
            },
            "ISSUCCESS": "true"
        }
        
        self.data_transformer.transform_message_from_dict(message_dict)
        
        # 检查统计
        stats_before = self.data_transformer.get_transform_stats()
        assert stats_before["total_transformed"] > 0
        
        # 重置统计
        self.data_transformer.reset_stats()
        
        # 检查重置后的统计
        stats_after = self.data_transformer.get_transform_stats()
        assert stats_after["total_transformed"] == 0
        assert stats_after["successful_transforms"] == 0
        assert stats_after["failed_transforms"] == 0
    
    def test_get_transformation_summary(self):
        """测试获取转换摘要"""
        summary = self.data_transformer.get_transformation_summary()
        
        assert "stats" in summary
        assert "field_mapper_summary" in summary
        assert "config_loaded" in summary
        assert "last_reload_time" in summary