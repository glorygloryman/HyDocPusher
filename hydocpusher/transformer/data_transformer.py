"""
数据转换器主模块
协调整个数据转换过程，包括字段映射、附件构建和格式转换
"""

from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime
from ..models.message_models import SourceMessageSchema
from ..models.archive_models import ArchiveData, AttachmentData, ArchiveRequestSchema
from ..config.settings import get_config
from ..exceptions.custom_exceptions import DataTransformException, ValidationException
from .field_mapper import FieldMapper
from .attachment_builder import AttachmentBuilder

logger = logging.getLogger(__name__)


class DataTransformer:
    """数据转换器主类"""
    
    def __init__(self):
        """初始化数据转换器"""
        self.config = get_config()
        self.field_mapper = FieldMapper()
        self.attachment_builder = AttachmentBuilder()
        
        # 转换统计
        self.transform_stats = {
            'total_transformed': 0,
            'successful_transforms': 0,
            'failed_transforms': 0,
            'last_transform_time': None
        }
    
    def transform_message(self, source_message: SourceMessageSchema) -> ArchiveRequestSchema:
        """
        转换源消息为档案请求
        
        Args:
            source_message: 源消息对象
            
        Returns:
            档案请求Schema对象
            
        Raises:
            DataTransformException: 数据转换失败
            ValidationException: 数据验证失败
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting transformation for message {source_message.document_id}")
            
            # 验证源消息
            self._validate_source_message(source_message)
            
            # 提取源数据
            source_data = self._extract_source_data(source_message)
            
            # 映射字段
            mapped_data = self._map_fields(source_data)
            
            # 构建附件
            attachments = self._build_attachments(source_message)
            
            # 创建档案数据
            archive_data = self._create_archive_data(mapped_data, attachments)
            
            # 创建档案请求
            archive_request = self._create_archive_request(archive_data)
            
            # 验证结果
            self._validate_archive_request(archive_request)
            
            # 更新统计
            self._update_stats(True, start_time)
            
            logger.info(f"Successfully transformed message {source_message.document_id}")
            return archive_request
            
        except Exception as e:
            self._update_stats(False, start_time)
            if isinstance(e, (DataTransformException, ValidationException)):
                raise
            raise DataTransformException(f"Failed to transform message: {str(e)}", cause=e)
    
    def transform_message_from_dict(self, message_dict: Dict[str, Any]) -> ArchiveRequestSchema:
        """
        从字典转换消息
        
        Args:
            message_dict: 消息字典
            
        Returns:
            档案请求对象
        """
        try:
            # 创建源消息对象
            source_message = SourceMessageSchema(**message_dict)
            return self.transform_message(source_message)
            
        except Exception as e:
            # 临时显示详细错误信息用于调试
            print(f"Validation error details: {e}")
            raise DataTransformException(f"Failed to create source message from dict: {str(e)}", cause=e)
    
    def transform_message_from_json(self, json_str: str) -> ArchiveRequestSchema:
        """
        从JSON字符串转换消息
        
        Args:
            json_str: JSON字符串
            
        Returns:
            档案请求对象
        """
        try:
            # 创建源消息对象
            source_message = SourceMessageSchema.from_json(json_str)
            return self.transform_message(source_message)
            
        except Exception as e:
            raise DataTransformException(f"Failed to create source message from JSON: {str(e)}", cause=e)
    
    def _validate_source_message(self, source_message: SourceMessageSchema) -> None:
        """
        验证源消息
        
        Args:
            source_message: 源消息对象
            
        Raises:
            ValidationException: 消息验证失败
        """
        try:
            # 使用消息对象的验证方法
            source_message.validate_for_processing()
            
            # 检查消息时间
            if not source_message.publish_time:
                raise ValidationException("Message publish time is required")
            
            # 检查文档标题
            if not source_message.document_title or not source_message.document_title.strip():
                raise ValidationException("Document title cannot be empty")
            
            # 检查发布URL
            if not source_message.DATA.DATA.DOCPUBURL or not source_message.DATA.DATA.DOCPUBURL.strip():
                raise ValidationException("Document publish URL cannot be empty")
            
            logger.debug("Source message validation passed")
            
        except Exception as e:
            if isinstance(e, ValidationException):
                raise
            raise ValidationException(f"Source message validation failed: {str(e)}", cause=e)
    
    def _extract_source_data(self, source_message: SourceMessageSchema) -> Dict[str, Any]:
        """
        提取源数据
        
        Args:
            source_message: 源消息对象
            
        Returns:
            源数据字典
        """
        try:
            # 提取文档数据
            doc_data = source_message.DATA.DATA.model_dump()
            
            # 提取频道文档数据
            chnl_doc_data = source_message.DATA.CHNLDOC.model_dump()
            
            # 提取消息数据
            msg_data = source_message.DATA.model_dump()
            
            # 合并数据
            source_data = {}
            source_data.update(doc_data)
            source_data.update(chnl_doc_data)
            source_data.update(msg_data)
            
            logger.debug(f"Extracted source data with {len(source_data)} fields")
            return source_data
            
        except Exception as e:
            raise DataTransformException(f"Failed to extract source data: {str(e)}", cause=e)
    
    def _map_fields(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        映射字段
        
        Args:
            source_data: 源数据字典
            
        Returns:
            映射后的数据字典
        """
        try:
            # 使用字段映射器进行映射
            mapped_data = self.field_mapper.map_document_info(source_data)
            
            # 添加额外的映射
            mapped_data.update(self._map_additional_fields(source_data))
            
            # 验证映射后的数据
            self.field_mapper.validate_mapped_data(mapped_data)
            
            logger.debug(f"Successfully mapped {len(mapped_data)} fields")
            return mapped_data
            
        except Exception as e:
            if isinstance(e, (DataTransformException, ValidationException)):
                raise
            raise DataTransformException(f"Failed to map fields: {str(e)}", cause=e)
    
    def _map_additional_fields(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        映射额外字段
        
        Args:
            source_data: 源数据字典
            
        Returns:
            额外映射字段字典
        """
        additional_fields = {}
        
        try:
            # 映射操作员信息
            if 'CRUSER' in source_data:
                additional_fields['bly'] = source_data['CRUSER']
            
            # 映射部门信息
            if 'CRDEPT' in source_data:
                additional_fields['fillingdepartment'] = source_data['CRDEPT']
            
            # 映射作者信息
            if 'TXY' in source_data and source_data['TXY']:
                additional_fields['author'] = source_data['TXY']
            elif 'DOCAUTHOR' in source_data and source_data['DOCAUTHOR']:
                additional_fields['author'] = source_data['DOCAUTHOR']
            
            return additional_fields
            
        except Exception as e:
            logger.warning(f"Failed to map additional fields: {str(e)}")
            return {}
    
    def _build_attachments(self, source_message: SourceMessageSchema) -> List[AttachmentData]:
        """
        构建附件列表
        
        Args:
            source_message: 源消息对象
            
        Returns:
            附件数据列表
        """
        try:
            attachments = []
            
            # 构建HTML正文附件
            html_attachment = self.attachment_builder.build_html_attachment(
                source_message.DATA.DATA.DOCPUBURL,
                source_message.document_title
            )
            attachments.append(html_attachment)
            
            # 构建其他附件
            if source_message.DATA.APPENDIX:
                other_attachments = self.attachment_builder.build_attachments(
                    source_message
                )
                attachments.extend(other_attachments)
            
            # 过滤和限制附件
            filtered_attachments = self.attachment_builder.filter_attachments(
                attachments,
                max_count=10,
                max_size=50
            )
            
            logger.info(f"Built {len(filtered_attachments)} attachments")
            return filtered_attachments
            
        except Exception as e:
            logger.warning(f"Failed to build attachments: {str(e)}")
            # 返回至少HTML正文附件
            try:
                html_attachment = self.attachment_builder.build_html_attachment(
                    source_message.DATA.DATA.DOCPUBURL,
                    source_message.document_title
                )
                return [html_attachment]
            except Exception:
                return []
    
    def _create_archive_data(self, mapped_data: Dict[str, Any], attachments: List[AttachmentData]) -> ArchiveData:
        """
        创建档案数据
        
        Args:
            mapped_data: 映射后的数据
            attachments: 附件列表
            
        Returns:
            档案数据对象
        """
        try:
            # 创建档案数据对象
            archive_data = ArchiveData(
                did=mapped_data['did'],
                wzmc=mapped_data['wzmc'],
                dn=mapped_data['dn'],
                classfyname=mapped_data['classfyname'],
                classfy=mapped_data['classfy'],
                title=mapped_data['title'],
                author=mapped_data.get('author', ''),
                docdate=mapped_data['docdate'],
                year=mapped_data['year'],
                retentionperiod=mapped_data['retentionperiod'],
                fillingdepartment=mapped_data.get('fillingdepartment', ''),
                bly=mapped_data.get('bly', ''),
                attachment=attachments
            )
            
            logger.debug(f"Created archive data for document {mapped_data['did']}")
            return archive_data
            
        except Exception as e:
            raise DataTransformException(f"Failed to create archive data: {str(e)}", cause=e)
    
    def _create_archive_request(self, archive_data: ArchiveData) -> ArchiveRequestSchema:
        """
        创建档案请求
        
        Args:
            archive_data: 档案数据对象
            
        Returns:
            档案请求Schema对象
        """
        try:
            # 创建档案请求Schema对象（根据PRD文档使用固定默认值）
            archive_request = ArchiveRequestSchema.create_archive_request(
                app_id="NEWS",  # 根据PRD文档：固定值NEWS
                app_token="TmV3cytJbnRlcmZhY2U=",  # 根据PRD文档：固定值
                company_name="云南省能源投资集团有限公司",  # 根据PRD文档：固定值
                archive_type="17",  # 根据PRD文档：固定值17
                archive_data=archive_data
            )
            
            logger.debug(f"Created archive request for document {archive_data.did}")
            return archive_request
            
        except Exception as e:
            raise DataTransformException(f"Failed to create archive request: {str(e)}", cause=e)
    
    def _validate_archive_request(self, archive_request: ArchiveRequestSchema) -> None:
        """
        验证档案请求
        
        Args:
            archive_request: 档案请求对象
            
        Raises:
            ValidationException: 请求验证失败
        """
        try:
            # 使用Schema的验证方法
            archive_request.validate_for_submission()
            
            # 获取ArchiveData进行额外验证
            archive_data = archive_request.ArchiveData
            
            # 检查附件数量
            attachments = archive_data.get('attachment', [])
            if len(attachments) > 10:
                logger.warning(f"Too many attachments ({len(attachments)}), consider filtering")
            
            logger.debug("Archive request validation passed")
            
        except Exception as e:
            if isinstance(e, ValidationException):
                raise
            raise ValidationException(f"Archive request validation failed: {str(e)}", cause=e)
    
    def _update_stats(self, success: bool, start_time: datetime) -> None:
        """
        更新转换统计
        
        Args:
            success: 是否成功
            start_time: 开始时间
        """
        self.transform_stats['total_transformed'] += 1
        
        if success:
            self.transform_stats['successful_transforms'] += 1
        else:
            self.transform_stats['failed_transforms'] += 1
        
        self.transform_stats['last_transform_time'] = datetime.now()
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Transform {'successful' if success else 'failed'} in {duration:.2f}s")
    
    def get_transform_stats(self) -> Dict[str, Any]:
        """
        获取转换统计信息
        
        Returns:
            统计信息字典
        """
        return self.transform_stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.transform_stats = {
            'total_transformed': 0,
            'successful_transforms': 0,
            'failed_transforms': 0,
            'last_transform_time': None
        }
        logger.info("Transform statistics reset")
    
    def reload_config(self) -> None:
        """重新加载配置"""
        logger.info("Reloading data transformer configuration")
        self.config = get_config()
        self.field_mapper.reload_config()
        logger.info("Data transformer configuration reloaded successfully")
    
    def get_transformation_summary(self) -> Dict[str, Any]:
        """
        获取转换摘要信息
        
        Returns:
            转换摘要字典
        """
        return {
            'stats': self.get_transform_stats(),
            'field_mapper_summary': self.field_mapper.get_mapping_summary(),
            'config_loaded': bool(self.config),
            'last_reload_time': self.transform_stats['last_transform_time']
        }