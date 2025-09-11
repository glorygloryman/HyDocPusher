"""
源消息数据模型模块
定义来自Pulsar的消息数据结构和验证规则
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json


class AppendixInfo(BaseModel):
    """传统附件信息模型"""
    APPFILE: str = Field(..., alias="APPFILE", description="附件文件路径或URL")
    APPFLAG: str = Field(..., alias="APPFLAG", description="附件类型标识")
    
    @field_validator('APPFLAG')
    @classmethod
    def validate_appflag(cls, v):
        """验证附件类型标识"""
        valid_flags = ['20', '50', '140', '30', '40', '60', '70', '80', '90', '100', '110', '120', '130']
        if v not in valid_flags:
            raise ValueError(f"Invalid APPFLAG: {v}. Must be one of {valid_flags}")
        return v
    
    @property
    def attachment_type(self) -> str:
        """根据APPFLAG获取附件类型"""
        flag_mapping = {
            '20': '图片',
            '50': '视频',
            '140': '视频播放页',
            '30': '音频',
            '40': '文档',
            '60': '压缩包',
            '70': '其他',
            '80': 'Flash',
            '90': '流媒体',
            '100': '外部链接',
            '110': '内部链接',
            '120': '应用',
            '130': '小程序'
        }
        return flag_mapping.get(self.APPFLAG, '其他')


class AttachmentItem(BaseModel):
    """JSON格式附件项模型"""
    APPDESC: str = Field(..., alias="APPDESC", description="附件描述")
    APPURL: str = Field(..., alias="APPURL", description="附件URL")
    APPENDIXID: int = Field(..., alias="APPENDIXID", description="附件ID")
    
    @property
    def attachment_type(self) -> str:
        """根据URL推断附件类型"""
        url = self.APPURL.lower()
        if any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
            return '图片'
        elif any(ext in url for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']):
            return '视频'
        elif any(ext in url for ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg']):
            return '音频'
        elif any(ext in url for ext in ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx']):
            return '文档'
        else:
            return '其他'


class AttachmentField(BaseModel):
    """附件字段容器模型"""
    APPENDIX: List[AppendixInfo] = Field(default_factory=list, alias="APPENDIX", description="传统附件数组")
    appdix: Optional[List[AppendixInfo]] = Field(default=None, alias="Appdix", description="新增Appdix字段")
    attachments: Optional[List[AttachmentItem]] = Field(default=None, alias="attachments", description="JSON格式附件字段")
    
    @property
    def has_traditional_appendix(self) -> bool:
        """是否有传统附件"""
        return bool(self.APPENDIX)
    
    @property
    def has_appdix(self) -> bool:
        """是否有Appdix附件"""
        return bool(self.appdix)
    
    @property
    def has_attachments(self) -> bool:
        """是否有JSON格式附件"""
        return bool(self.attachments)
    
    @property
    def has_any_attachments(self) -> bool:
        """是否有任何附件"""
        return self.has_traditional_appendix or self.has_appdix or self.has_attachments


class DocumentData(BaseModel):
    """文档数据模型"""
    ISFOCUSIMAGE: str = Field(default="否", alias="ISFOCUSIMAGE")
    DOCUMENTLABELS: str = Field(default="", alias="DOCUMENTLABELS")
    CLASSINFO_ID_PATHS: List[Any] = Field(default_factory=list, alias="CLASSINFO_ID_PATHS")
    CHANNELID: str = Field(..., alias="CHANNELID")
    DOCAUTHOR: str = Field(default="", alias="DOCAUTHOR")
    DOCCOVERPIC: str = Field(default="[]", alias="DOCCOVERPIC")
    ATTACHPIC: str = Field(default="0", alias="ATTACHPIC")
    DOCSOURCENAME: str = Field(default="", alias="DOCSOURCENAME")
    LISTSTYLE: str = Field(default="4", alias="LISTSTYLE")
    PARENTCHNLDESC: str = Field(default="", alias="PARENTCHNLDESC")
    COMMENTFLAG: str = Field(default="0", alias="COMMENTFLAG")
    CLASSINFO_NAMES: List[Any] = Field(default_factory=list, alias="CLASSINFO_NAMES")
    CHNLHASCHILDREN: str = Field(default="0", alias="CHNLHASCHILDREN")
    THUMBFILES: str = Field(default="", alias="THUMBFILES")
    LABEL: str = Field(default="", alias="LABEL")
    DOCTYPE: str = Field(..., alias="DOCTYPE")
    LISTTITLE: str = Field(..., alias="LISTTITLE")
    LISTPICS: str = Field(default="[]", alias="LISTPICS")
    SITENAME: str = Field(..., alias="SITENAME")
    DOCUMENT_RELATED_APPENDIX: str = Field(default="[]", alias="DOCUMENT_RELATED_APPENDIX")
    CHANNELTYPE: str = Field(default="", alias="CHANNELTYPE")
    SEARCHWORDVALUE: str = Field(default="", alias="SEARCHWORDVALUE")
    DOCORDER: str = Field(..., alias="DOCORDER")
    RECID: str = Field(..., alias="RECID")
    ACTIONTYPE: str = Field(..., alias="ACTIONTYPE")
    DOCUMENT_CONTENT_APPENDIX: str = Field(default="[]", alias="DOCUMENT_CONTENT_APPENDIX")
    FOCUSIMG: str = Field(default="", alias="FOCUSIMG")
    LISTIMGURLS: str = Field(default="", alias="LISTIMGURLS")
    METADATAID: str = Field(..., alias="METADATAID")
    CLASSINFO_IDS: List[Any] = Field(default_factory=list, alias="CLASSINFO_IDS")
    DEFAULTRELDOCS: List[Any] = Field(default_factory=list, alias="DEFAULTRELDOCS")
    DOCFILENAME: str = Field(default="", alias="DOCFILENAME")
    SITEDESC: str = Field(..., alias="SITEDESC")
    DOCHTMLCON: str = Field(default="", alias="DOCHTMLCON")
    DOCUMENT_RELATED_VIDEO: str = Field(default="[]", alias="DOCUMENT_RELATED_VIDEO")
    CRUSER: str = Field(..., alias="CRUSER")
    DOCUMENT_DOCRELTIME: str = Field(..., alias="DOCUMENT_DOCRELTIME")
    DEFAULTRELDOCS_IRS: str = Field(default="[]", alias="DEFAULTRELDOCS_IRS")
    DOCUMENT_CONTENT_PIC: str = Field(default="[]", alias="DOCUMENT_CONTENT_PIC")
    SHORTTITLE: str = Field(default="", alias="SHORTTITLE")
    CRTIME: str = Field(..., alias="CRTIME")  # 恢复原始字段名，DOCFIRSTPUBTIME只在CHNLDOC中
    MEDIATYPE: str = Field(..., alias="MEDIATYPE")
    DOCPEOPLE: str = Field(default="", alias="DOCPEOPLE")
    DOCRELTIME: str = Field(..., alias="DOCRELTIME")
    DOCCONTENT: str = Field(default="", alias="DOCCONTENT")
    CHNLDOC_OPERTIME: str = Field(..., alias="CHNLDOC_OPERTIME")
    FOCUSFILENAME: str = Field(default="", alias="FOCUSFILENAME")
    DOCTITLE: str = Field(..., alias="DOCTITLE")
    TXY: str = Field(default="", alias="TXY")
    DOCPUBURL: str = Field(..., alias="DOCPUBURL")
    DOCUMENT_CONTENT_VIDEO: str = Field(default="[]", alias="DOCUMENT_CONTENT_VIDEO")
    DOCLINK: str = Field(default="", alias="DOCLINK")
    VERSIONNUM: str = Field(default="0", alias="VERSIONNUM")
    FOCUSIMAGE: str = Field(default="[]", alias="FOCUSIMAGE")
    FROMID: str = Field(default="", alias="FROMID")
    CLASSINFO_NAME_PATHS: List[Any] = Field(default_factory=list, alias="CLASSINFO_NAME_PATHS")
    SUBDOCTITLE: str = Field(default="", alias="SUBDOCTITLE")
    DOCKEYWORDS: str = Field(default="", alias="DOCKEYWORDS")
    TITLECOLOR: str = Field(default="", alias="TITLECOLOR")
    CLASSIFICATIONID: str = Field(..., alias="CLASSIFICATIONID")
    ORIGINMETADATAID: str = Field(..., alias="ORIGINMETADATAID")
    SITEID: str = Field(..., alias="SITEID")
    CHNLDESC: str = Field(..., alias="CHNLDESC")
    PUBSTATUS: str = Field(..., alias="PUBSTATUS")
    MODAL: str = Field(..., alias="MODAL")
    ATTACHVIDEO: str = Field(default="0", alias="ATTACHVIDEO")
    DOCUMENT_DOCCONTENT: str = Field(default="", alias="DOCUMENT_DOCCONTENT")
    CHNLNAME: str = Field(..., alias="CHNLNAME")
    DOCPLACE: str = Field(default="", alias="DOCPLACE")
    DOCUMENT_RELATED_PIC: str = Field(default="[]", alias="DOCUMENT_RELATED_PIC")
    DOCABSTRACT: str = Field(default="", alias="DOCABSTRACT")
    FOCUSTITLE: str = Field(default="", alias="FOCUSTITLE")
    FOCUSDESC: str = Field(default="", alias="FOCUSDESC")
    WCMMETATABLEGOVDOCNEWSAPPID: str = Field(default="", alias="WCMMETATABLEGOVDOCNEWSAPPID")
    WEBHTTP: str = Field(..., alias="WEBHTTP")
    FOCUSIMAGETITLE: str = Field(default="", alias="FOCUSIMAGETITLE")
    
    @field_validator('CRTIME', 'DOCRELTIME', 'DOCUMENT_DOCRELTIME', 'CHNLDOC_OPERTIME')
    @classmethod
    def validate_datetime_format(cls, v):
        """验证日期时间格式"""
        if v and v.strip():
            try:
                datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    raise ValueError(f"Invalid datetime format: {v}. Expected YYYY-MM-DD HH:MM:SS or YYYY-MM-DD")
        return v


class ChannelDoc(BaseModel):
    """频道文档信息模型"""
    ISARCHIVE: str = Field(default="0", alias="ISARCHIVE")
    DOCINFLOW: str = Field(default="0", alias="DOCINFLOW")
    TIMEDSTATUS: str = Field(default="0", alias="TIMEDSTATUS")
    OTHERVIEWMODE: str = Field(default="0", alias="OTHERVIEWMODE")
    POSCHNLID: str = Field(default="0", alias="POSCHNLID")
    SRCSITEID: str = Field(..., alias="SRCSITEID")
    DOCAUTHOR: str = Field(default="", alias="DOCAUTHOR")
    CARBONCOPYRECEIVERACTIONTYPE: str = Field(default="0", alias="CARBONCOPYRECEIVERACTIONTYPE")
    ISREAD: str = Field(default="1", alias="ISREAD")
    ABOLITION: str = Field(default="0", alias="ABOLITION")
    ATTACHPIC: str = Field(default="1", alias="ATTACHPIC")
    DOCSOURCENAME: str = Field(default="", alias="DOCSOURCENAME")
    FLOWID: str = Field(default="", alias="FLOWID")
    GDORDER: str = Field(default="0", alias="GDORDER")
    DATASENDMODE: str = Field(default="0", alias="DATASENDMODE")
    ISTIMINGPUBLISH: str = Field(default="0", alias="ISTIMINGPUBLISH")
    DOCTYPE: str = Field(..., alias="DOCTYPE")
    DOCFIRSTPUBTIME: str = Field(..., alias="DOCFIRSTPUBTIME")
    CANPUB: str = Field(default="1", alias="CANPUB")
    CANEDIT: str = Field(default="true", alias="CANEDIT")
    DOCORDER: str = Field(..., alias="DOCORDER")
    PUBQUOTEDOC: str = Field(default="0", alias="PUBQUOTEDOC")
    RECID: str = Field(..., alias="RECID")
    ACTIONTYPE: str = Field(..., alias="ACTIONTYPE")
    DOCCHANNEL: str = Field(..., alias="DOCCHANNEL")
    PUSHUIRBSTATUS: str = Field(default="1", alias="PUSHUIRBSTATUS")
    CANCELPUBTIME: str = Field(default="", alias="CANCELPUBTIME")
    PUSHRECEIVERACTIONTYPE: str = Field(default="0", alias="PUSHRECEIVERACTIONTYPE")
    ISDELETED: str = Field(default="0", alias="ISDELETED")
    INVALIDTIME: str = Field(default="", alias="INVALIDTIME")
    CRUSER: str = Field(..., alias="CRUSER")
    DOCORDERPRI: str = Field(default="0", alias="DOCORDERPRI")
    NEEDMANUALSYNC: str = Field(default="0", alias="NEEDMANUALSYNC")
    OPERUSER: str = Field(..., alias="OPERUSER")
    CRTIME: str = Field(..., alias="CRTIME")  # 频道文档创建时间
    OPERTIME: str = Field(..., alias="OPERTIME")
    DOCPUBTIME: str = Field(..., alias="DOCPUBTIME")
    DOCSTATUS: str = Field(..., alias="DOCSTATUS")
    CRDEPT: str = Field(..., alias="CRDEPT")
    DOCRELTIME: str = Field(..., alias="DOCRELTIME")
    DOCLEVEL: str = Field(default="0", alias="DOCLEVEL")
    REFUSESTATUS: str = Field(default="0", alias="REFUSESTATUS")
    ORIGINRECID: str = Field(..., alias="ORIGINRECID")
    DOCID: str = Field(..., alias="DOCID")
    CHNLID: str = Field(..., alias="CHNLID")
    DISTRECEIVERACTIONTYPE: str = Field(default="0", alias="DISTRECEIVERACTIONTYPE")
    DOCPUBURL: str = Field(..., alias="DOCPUBURL")
    ACTIONUSER: str = Field(..., alias="ACTIONUSER")
    ISMASTERCHNL: str = Field(default="0", alias="ISMASTERCHNL")
    ARCHIVETIME: str = Field(default="", alias="ARCHIVETIME")
    DOCOUTUPID: str = Field(..., alias="DOCOUTUPID")
    DISTSENDERACTIONTYPE: str = Field(default="0", alias="DISTSENDERACTIONTYPE")
    DOCKIND: str = Field(..., alias="DOCKIND")
    CARBONCOPYSENDERACTIONTYPE: str = Field(default="0", alias="CARBONCOPYSENDERACTIONTYPE")
    SITEID: str = Field(..., alias="SITEID")
    PUBSTATUS: str = Field(..., alias="PUBSTATUS")
    MODAL: str = Field(..., alias="MODAL")
    PUSHSENDERACTIONTYPE: str = Field(default="0", alias="PUSHSENDERACTIONTYPE")


class MessageData(BaseModel):
    """消息数据模型"""
    SITENAME: str = Field(..., alias="SITENAME")
    CRTIME: str = Field(..., alias="CRTIME")  # 消息创建时间，DOCFIRSTPUBTIME只在CHNLDOC中
    CHANNELID: str = Field(..., alias="CHANNELID")
    VIEWID: str = Field(..., alias="VIEWID")
    VIEWNAME: str = Field(..., alias="VIEWNAME")
    SITEID: str = Field(..., alias="SITEID")
    DOCID: str = Field(..., alias="DOCID")
    OPERTYPE: str = Field(..., alias="OPERTYPE")
    CHANNELNAV: str = Field(..., alias="CHANNELNAV")
    DATA: DocumentData = Field(..., alias="DATA")
    CHNLDOC: ChannelDoc = Field(..., alias="CHNLDOC")
    CRUSER: str = Field(..., alias="CRUSER")
    APPENDIX: List[AppendixInfo] = Field(default_factory=list, alias="APPENDIX")
    appdix: Optional[List[AppendixInfo]] = Field(default=None, alias="Appdix")
    attachments: Optional[List[AttachmentItem]] = Field(default=None, alias="attachments")
    ID: str = Field(..., alias="ID")
    CHANNELDESCNAV: str = Field(..., alias="CHANNELDESCNAV")
    TYPE: str = Field(..., alias="TYPE")
    
    @field_validator('CRTIME')
    @classmethod
    def validate_crtime(cls, v):
        """验证创建时间格式"""
        if v and v.strip():
            try:
                datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError(f"Invalid CRTIME format: {v}. Expected YYYY-MM-DD HH:MM:SS")
        return v
    
    @property
    def parsed_crtime(self) -> Optional[datetime]:
        """解析CRTIME为datetime对象"""
        if self.CRTIME and self.CRTIME.strip():
            try:
                return datetime.strptime(self.CRTIME, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
        return None
    
    @property
    def attachment_fields(self) -> AttachmentField:
        """获取附件字段容器"""
        return AttachmentField(
            APPENDIX=self.APPENDIX,
            appdix=self.appdix,
            attachments=self.attachments
        )
    
    @property
    def has_attachments(self) -> bool:
        """是否有任何附件"""
        return self.attachment_fields.has_any_attachments


class SourceMessageSchema(BaseModel):
    """源消息主模型"""
    MSG: str = Field(..., alias="MSG", description="消息内容")
    DATA: MessageData = Field(..., alias="DATA", description="消息数据")
    ISSUCCESS: str = Field(..., alias="ISSUCCESS", description="是否成功")
    
    @field_validator('ISSUCCESS')
    @classmethod
    def validate_is_success(cls, v):
        """验证成功标志"""
        if v.lower() not in ['true', 'false', '1', '0']:
            raise ValueError(f"Invalid ISSUCCESS value: {v}. Must be 'true', 'false', '1', or '0'")
        return v
    
    @property
    def is_success(self) -> bool:
        """获取是否成功的布尔值"""
        return self.ISSUCCESS.lower() in ['true', '1']
    
    @property
    def document_id(self) -> str:
        """获取文档ID"""
        return self.DATA.DOCID
    
    @property
    def channel_id(self) -> str:
        """获取频道ID"""
        return self.DATA.CHANNELID
    
    @property
    def document_title(self) -> str:
        """获取文档标题"""
        return self.DATA.DATA.DOCTITLE
    
    @property
    def publish_time(self) -> Optional[datetime]:
        """获取发布时间"""
        return self.DATA.parsed_crtime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SourceMessageSchema':
        """从JSON字符串创建模型实例"""
        try:
            data = json.loads(json_str)
            return cls(**data)
        except json.JSONDecodeError as e:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Invalid JSON format: {str(e)}", cause=e)
        except Exception as e:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Failed to parse message: {str(e)}", cause=e)
    
    def validate_for_processing(self) -> None:
        """验证消息是否可以处理"""
        if not self.is_success:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Message indicates failure: {self.MSG}")
        
        required_fields = [
            ('DOCID', self.DATA.DOCID),
            ('DOCTITLE', self.DATA.DATA.DOCTITLE),
            ('CHANNELID', self.DATA.CHANNELID),
            ('DOCPUBURL', self.DATA.DATA.DOCPUBURL),
        ]
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value or not str(field_value).strip():
                missing_fields.append(field_name)
        
        if missing_fields:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Missing required fields for processing: {', '.join(missing_fields)}")