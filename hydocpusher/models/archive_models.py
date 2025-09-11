"""
档案请求数据模型模块
定义发送到档案系统的请求数据结构和验证规则
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json


class AttachmentData(BaseModel):
    """附件数据模型"""
    name: str = Field(..., description="附件名称")
    ext: str = Field(..., description="附件扩展名")
    file: str = Field(..., description="附件文件路径或URL")
    type: str = Field(..., description="附件类型")
    
    @field_validator('ext')
    @classmethod
    def validate_extension(cls, v):
        """验证文件扩展名"""
        if not v or not v.strip():
            raise ValueError("File extension cannot be empty")
        if not v.startswith('.'):
            v = f".{v}"
        return v.lower()
    
    @field_validator('file')
    @classmethod
    def validate_file_url(cls, v):
        """验证文件URL或路径"""
        if not v or not v.strip():
            raise ValueError("File URL/path cannot be empty")
        return v.strip()
    
    @field_validator('type')
    @classmethod
    def validate_attachment_type(cls, v):
        """验证附件类型"""
        valid_types = ['正文', '图片', '视频', '音频', '文档', '其他']
        if v not in valid_types:
            raise ValueError(f"Invalid attachment type: {v}. Must be one of {valid_types}")
        return v
    
    @classmethod
    def create_html_attachment(cls, pub_url: str, title: str) -> 'AttachmentData':
        """创建HTML正文附件"""
        if not pub_url or not pub_url.strip():
            raise ValueError("Publication URL cannot be empty")
        
        name = f"{title}(正文)" if title else "正文"
        ext = ".html"
        
        return cls(
            name=name,
            ext=ext,
            file=pub_url,
            type="正文"
        )
    
    @classmethod
    def create_media_attachment(cls, file_url: str, media_type: str, description: str = "") -> 'AttachmentData':
        """创建媒体附件"""
        if not file_url or not file_url.strip():
            raise ValueError("Media file URL cannot be empty")
        
        # 根据文件扩展名确定类型
        if file_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
            attachment_type = '图片'
            ext = '.jpg'
        elif file_url.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv')):
            attachment_type = '视频'
            ext = '.mp4'
        elif file_url.lower().endswith(('.mp3', '.wav', '.aac', '.flac', '.ogg')):
            attachment_type = '音频'
            ext = '.mp3'
        else:
            attachment_type = '其他'
            ext = '.file'
        
        name = description if description else f"媒体文件_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return cls(
            name=name,
            ext=ext,
            file=file_url,
            type=attachment_type
        )


class ArchiveData(BaseModel):
    """档案数据模型"""
    did: str = Field(..., description="文档ID")
    wzmc: str = Field(..., description="网站名称")
    dn: str = Field(..., description="域名")
    classfyname: str = Field(..., description="分类名称")
    classfy: str = Field(..., description="分类代码")
    title: str = Field(..., description="标题")
    author: str = Field(default="", description="作者")
    docdate: str = Field(..., description="文档日期")
    year: str = Field(..., description="年份")
    retentionperiod: int = Field(..., description="保留期限")
    fillingdepartment: str = Field(default="", description="归档部门")
    bly: str = Field(default="", description="编录员")
    attachment: List[AttachmentData] = Field(default_factory=list, description="附件列表")
    
    @field_validator('did', 'wzmc', 'dn', 'classfyname', 'classfy', 'title')
    @classmethod
    def validate_required_fields(cls, v):
        """验证必需字段"""
        if not v or not str(v).strip():
            raise ValueError("Field cannot be empty")
        return str(v).strip()
    
    @field_validator('docdate')
    @classmethod
    def validate_docdate_format(cls, v):
        """验证文档日期格式"""
        if not v or not v.strip():
            raise ValueError("Document date cannot be empty")
        
        # 支持多种日期格式
        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']
        for fmt in date_formats:
            try:
                datetime.strptime(v, fmt)
                return v
            except ValueError:
                continue
        
        raise ValueError(f"Invalid document date format: {v}. Expected YYYY-MM-DD, YYYY/MM/DD, or YYYY年MM月DD日")
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        """验证年份格式"""
        if not v or not v.strip():
            raise ValueError("Year cannot be empty")
        
        try:
            year = int(v)
            if not 1900 <= year <= 2100:
                raise ValueError(f"Year must be between 1900 and 2100, got: {year}")
            return str(year)
        except ValueError:
            raise ValueError(f"Invalid year format: {v}. Must be a valid year")
    
    @field_validator('retentionperiod')
    @classmethod
    def validate_retention_period(cls, v):
        """验证保留期限"""
        if v <= 0:
            raise ValueError("Retention period must be positive")
        if v > 100:  # 限制最大100年
            raise ValueError("Retention period cannot exceed 100 years")
        return v
    
    @property
    def parsed_docdate(self) -> Optional[datetime]:
        """解析文档日期为datetime对象"""
        if not self.docdate or not self.docdate.strip():
            return None
        
        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']
        for fmt in date_formats:
            try:
                return datetime.strptime(self.docdate, fmt)
            except ValueError:
                continue
        return None
    
    def add_attachment(self, attachment: AttachmentData) -> None:
        """添加附件"""
        self.attachment.append(attachment)
    
    def add_html_attachment(self, pub_url: str, title: str) -> None:
        """添加HTML正文附件"""
        html_attachment = AttachmentData.create_html_attachment(pub_url, title)
        self.add_attachment(html_attachment)
    
    def add_media_attachment(self, file_url: str, media_type: str, description: str = "") -> None:
        """添加媒体附件"""
        media_attachment = AttachmentData.create_media_attachment(file_url, media_type, description)
        self.add_attachment(media_attachment)
    
    def get_attachment_count(self) -> int:
        """获取附件数量"""
        return len(self.attachment)
    
    def get_attachment_by_type(self, attachment_type: str) -> List[AttachmentData]:
        """根据类型获取附件"""
        return [att for att in self.attachment if att.type == attachment_type]
    
    def validate_for_submission(self) -> None:
        """验证档案数据是否可以提交"""
        # 验证必需字段
        required_fields = [
            ('did', self.did),
            ('wzmc', self.wzmc),
            ('dn', self.dn),
            ('classfyname', self.classfyname),
            ('classfy', self.classfy),
            ('title', self.title),
            ('docdate', self.docdate),
            ('year', self.year),
            ('retentionperiod', self.retentionperiod),
        ]
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value or not str(field_value).strip():
                missing_fields.append(field_name)
        
        if missing_fields:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Missing required fields for submission: {', '.join(missing_fields)}")


class ArchiveRequestSchema(BaseModel):
    """档案请求模型"""
    AppId: str = Field(..., description="应用ID")
    AppToken: str = Field(..., description="应用令牌")
    CompanyName: str = Field(..., description="公司名称")
    ArchiveType: str = Field(..., description="档案类型")
    ArchiveData: Dict[str, Any] = Field(..., description="档案数据")
    
    @field_validator('AppId', 'AppToken', 'CompanyName', 'ArchiveType')
    @classmethod
    def validate_required_fields(cls, v):
        """验证必需字段"""
        if not v or not str(v).strip():
            raise ValueError("Field cannot be empty")
        return str(v).strip()
    
    @classmethod
    def create_archive_request(
        cls, 
        app_id: str, 
        app_token: str, 
        company_name: str, 
        archive_type: str, 
        archive_data: Any
    ) -> 'ArchiveRequestSchema':
        """创建档案请求"""
        # 如果传入的是ArchiveData对象，转换为字典
        if isinstance(archive_data, ArchiveData):
            archive_dict = archive_data.model_dump()
        else:
            archive_dict = archive_data
        
        return cls(
            AppId=app_id,
            AppToken=app_token,
            CompanyName=company_name,
            ArchiveType=archive_type,
            ArchiveData=archive_dict
        )
    
    def validate_for_submission(self) -> None:
        """验证档案请求是否可以提交"""
        # 验证必需字段
        required_fields = [
            ('AppId', self.AppId),
            ('AppToken', self.AppToken),
            ('CompanyName', self.CompanyName),
            ('ArchiveType', self.ArchiveType),
        ]
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value or not str(field_value).strip():
                missing_fields.append(field_name)
        
        if missing_fields:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Missing required fields for submission: {', '.join(missing_fields)}")
        
        # 验证ArchiveData中的必需字段
        archive_data = self.ArchiveData
        required_archive_fields = [
            ('did', '文档ID'),
            ('wzmc', '网站名称'),
            ('dn', '域名'),
            ('classfyname', '分类名称'),
            ('classfy', '分类代码'),
            ('title', '标题'),
            ('docdate', '文档日期'),
            ('year', '年份'),
            ('retentionperiod', '保留期限'),
        ]
        
        missing_archive_fields = []
        for field_name, field_display in required_archive_fields:
            if field_name not in archive_data or not archive_data[field_name]:
                missing_archive_fields.append(field_display)
        
        if missing_archive_fields:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Missing required archive fields for submission: {', '.join(missing_archive_fields)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ArchiveRequestSchema':
        """从JSON字符串创建请求实例"""
        try:
            data = json.loads(json_str)
            return cls(**data)
        except json.JSONDecodeError as e:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Invalid JSON format: {str(e)}", cause=e)
        except Exception as e:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Failed to parse archive request: {str(e)}", cause=e)


class ArchiveResponseSchema(BaseModel):
    """档案响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="响应消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    timestamp: Optional[datetime] = Field(default=None, description="响应时间戳")
    
    @classmethod
    def from_success(cls, message: str = "Success", data: Dict[str, Any] = None) -> 'ArchiveResponseSchema':
        """创建成功响应"""
        return cls(
            success=True,
            message=message,
            data=data,
            timestamp=datetime.now()
        )
    
    @classmethod
    def from_error(cls, message: str, error_code: str = None, data: Dict[str, Any] = None) -> 'ArchiveResponseSchema':
        """创建错误响应"""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            data=data,
            timestamp=datetime.now()
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ArchiveResponseSchema':
        """从JSON字符串创建响应实例"""
        try:
            data = json.loads(json_str)
            return cls(**data)
        except json.JSONDecodeError as e:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Invalid JSON format: {str(e)}", cause=e)
        except Exception as e:
            from ..exceptions.custom_exceptions import ValidationException
            raise ValidationException(f"Failed to parse archive response: {str(e)}", cause=e)