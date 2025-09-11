"""
字段映射器模块
负责将源消息字段映射到档案系统字段，包括数据类型转换和格式标准化
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import re
import logging
from ..config.settings import get_config
from ..config.classification_config import get_classification_config
from ..exceptions.custom_exceptions import DataTransformException, ValidationException

logger = logging.getLogger(__name__)


class FieldMapper:
    """字段映射器类"""
    
    def __init__(self):
        """初始化字段映射器"""
        self.config = get_config()
        self.classification_config = get_classification_config()
        
        # 定义字段映射规则
        self.field_mappings = {
            # 基本信息映射
            'RECID': 'did',  # 根据PRD文档：did取原始数据中DATA.DATA.RECID字段的值
            'DOCTITLE': 'title',  # title取原始数据中DATA.DATA.DOCTITLE字段的值
            'TXY': 'author',  # author取原始数据中DATA.DATA.TXY字段的值
            'CRUSER': 'bly',  # bly取原始数据中DATA.DATA.CRUSER字段的值
            'CRDEPT': 'fillingdepartment',  # fillingdepartment取原始数据中DATA.CHNLDOC.CRDEPT字段的值
            
            # 分类信息映射
            'CHANNELID': 'classification_id',
            'CHNLNAME': 'classification_name',
            
            # 时间信息映射
            'DOCFIRSTPUBTIME': 'docdate',  # 根据PRD文档：docdate取原始数据中DATA.CHNLDOC.DOCFIRSTPUBTIME字段的值
        }
        
        # 默认值映射
        self.default_values = {
            'author': '',
            'fillingdepartment': '',
            'bly': '',
            'retentionperiod': 30,  # 根据PRD文档：固定值30
        }
        
        # 固定值映射（根据PRD文档）
        self.company_name = '集团门户'  # wzmc固定字符串
        self.domain = 'www.cnyeig.com'  # dn固定字符串
        
        # 日期格式解析器
        self.date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y年%m月%d日',
            '%Y/%m/%d %H:%M:%S',
        ]
    
    def map_field(self, source_field: str, source_value: Any) -> Dict[str, Any]:
        """
        映射单个字段
        
        Args:
            source_field: 源字段名
            source_value: 源字段值
            
        Returns:
            映射后的字段字典
            
        Raises:
            DataTransformException: 字段映射失败
        """
        try:
            if source_value is None:
                return {}
            
            # 获取目标字段名
            target_field = self.field_mappings.get(source_field)
            if not target_field:
                logger.debug(f"No mapping found for field: {source_field}")
                return {}
            
            # 根据字段类型进行转换
            converted_value = self._convert_field_value(target_field, source_value)
            
            return {target_field: converted_value}
            
        except Exception as e:
            raise DataTransformException(f"Failed to map field {source_field}: {str(e)}", cause=e)
    
    def map_classification(self, channel_id: str) -> Dict[str, str]:
        """
        映射分类信息
        
        Args:
            channel_id: 频道ID
            
        Returns:
            分类信息字典
        """
        try:
            # 获取分类配置
            classfyname, classfy = self.classification_config.get_classification(channel_id)
            
            return {
                'classfyname': classfyname,
                'classfy': classfy
            }
            
        except Exception as e:
            logger.warning(f"Failed to map classification for channel {channel_id}: {str(e)}")
            # 返回默认分类
            default_rule = self.classification_config.default_rule
            return {
                'classfyname': default_rule.classfyname,
                'classfy': default_rule.classfy
            }
    
    def map_document_info(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        映射文档基本信息
        
        Args:
            source_data: 源数据字典
            
        Returns:
            映射后的文档信息字典
        """
        mapped_data = {}
        
        try:
            # 映射基本字段
            for source_field, target_field in self.field_mappings.items():
                if source_field in source_data:
                    field_mapping = self.map_field(source_field, source_data[source_field])
                    mapped_data.update(field_mapping)
            
            # 设置固定值（根据PRD文档）
            mapped_data['wzmc'] = self.company_name  # 固定字符串'集团门户'
            mapped_data['dn'] = self.domain  # 固定字符串'www.cnyeig.com'
            
            # 映射分类信息
            if 'CHANNELID' in source_data:
                classification_mapping = self.map_classification(source_data['CHANNELID'])
                mapped_data.update(classification_mapping)
            
            # 设置保留期限（根据PRD文档：固定值30）
            mapped_data['retentionperiod'] = 30
            
            # 生成年份字段
            if 'docdate' in mapped_data and mapped_data['docdate']:
                mapped_data['year'] = self._convert_year(mapped_data['docdate'])
            
            return mapped_data
            
        except Exception as e:
            raise DataTransformException(f"Failed to map document info: {str(e)}", cause=e)
    
    def _convert_field_value(self, target_field: str, source_value: Any) -> Any:
        """
        转换字段值
        
        Args:
            target_field: 目标字段名
            source_value: 源字段值
            
        Returns:
            转换后的值
        """
        if source_value is None or source_value == '':
            return self.default_values.get(target_field, '')
        
        source_value = str(source_value).strip()
        if not source_value:
            return self.default_values.get(target_field, '')
        
        # 根据目标字段类型进行转换
        if target_field in ['docdate']:
            return self._convert_date(source_value)
        elif target_field in ['year']:
            return self._convert_year(source_value)
        elif target_field in ['retentionperiod']:
            return self._convert_retention_period(source_value)
        elif target_field in ['did', 'title', 'author', 'bly', 'wzmc', 'dn', 'fillingdepartment']:
            return self._convert_string(source_value)
        else:
            return source_value
    
    def _convert_date(self, date_str: str) -> str:
        """
        转换日期格式
        
        Args:
            date_str: 日期字符串
            
        Returns:
            转换后的日期字符串 (YYYY-MM-DD)
        """
        if not date_str or not date_str.strip():
            return ''
        
        date_str = date_str.strip()
        
        # 尝试各种日期格式
        for fmt in self.date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # 如果都无法解析，尝试提取日期部分
        date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        logger.warning(f"Failed to parse date: {date_str}")
        return ''
    
    def _convert_year(self, date_str: str) -> str:
        """
        从日期字符串中提取年份
        
        Args:
            date_str: 日期字符串
            
        Returns:
            年份字符串
        """
        if not date_str or not date_str.strip():
            return ''
        
        date_str = date_str.strip()
        
        # 尝试解析日期然后提取年份
        for fmt in self.date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return str(dt.year)
            except ValueError:
                continue
        
        # 尝试直接提取年份
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = year_match.group(1)
            if 1900 <= int(year) <= 2100:
                return year
        
        logger.warning(f"Failed to extract year from: {date_str}")
        return ''
    
    def _convert_retention_period(self, value: str) -> int:
        """
        转换保留期限
        
        Args:
            value: 保留期限值
            
        Returns:
            保留期限整数
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid retention period: {value}, using default")
            return self.config.archive.retention_period
    
    def _convert_string(self, value: str) -> str:
        """
        转换字符串值
        
        Args:
            value: 字符串值
            
        Returns:
            处理后的字符串
        """
        if not value or not value.strip():
            return ''
        
        # 清理字符串
        cleaned = str(value).strip()
        
        # 移除多余的空格
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 限制长度
        max_length = 1000  # 根据实际需求调整
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
            logger.warning(f"String truncated to {max_length} characters")
        
        return cleaned
    
    def validate_mapped_data(self, mapped_data: Dict[str, Any]) -> None:
        """
        验证映射后的数据
        
        Args:
            mapped_data: 映射后的数据字典
            
        Raises:
            ValidationException: 数据验证失败
        """
        required_fields = [
            ('did', '文档ID'),
            ('title', '标题'),
            ('wzmc', '网站名称'),
            ('dn', '域名'),
            ('classfyname', '分类名称'),
            ('classfy', '分类代码'),
            ('docdate', '文档日期'),
            ('year', '年份'),
            ('retentionperiod', '保留期限'),
        ]
        
        missing_fields = []
        for field_name, field_display in required_fields:
            if field_name not in mapped_data or not mapped_data[field_name]:
                missing_fields.append(field_display)
        
        if missing_fields:
            raise ValidationException(f"Missing required fields after mapping: {', '.join(missing_fields)}")
        
        # 验证数据类型
        if 'retentionperiod' in mapped_data:
            try:
                retention_period = int(mapped_data['retentionperiod'])
                if retention_period <= 0:
                    raise ValidationException("Retention period must be positive")
                if retention_period > 100:
                    raise ValidationException("Retention period cannot exceed 100 years")
            except (ValueError, TypeError):
                raise ValidationException("Invalid retention period value")
        
        # 验证日期格式
        if 'docdate' in mapped_data and mapped_data['docdate']:
            try:
                datetime.strptime(mapped_data['docdate'], '%Y-%m-%d')
            except ValueError:
                raise ValidationException(f"Invalid document date format: {mapped_data['docdate']}")
        
        # 验证年份格式
        if 'year' in mapped_data and mapped_data['year']:
            try:
                year = int(mapped_data['year'])
                if not 1900 <= year <= 2100:
                    raise ValidationException(f"Invalid year: {year}. Must be between 1900 and 2100")
            except (ValueError, TypeError):
                raise ValidationException(f"Invalid year format: {mapped_data['year']}")
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """
        获取映射规则摘要
        
        Returns:
            映射规则摘要字典
        """
        return {
            'field_mappings': self.field_mappings,
            'default_values': self.default_values,
            'company_name': self.company_name,
            'domain': self.domain,
            'date_formats': self.date_formats,
            'classification_config_loaded': len(self.classification_config.rules) > 0
        }
    
    def reload_config(self) -> None:
        """重新加载配置"""
        logger.info("Reloading field mapper configuration")
        self.config = get_config()
        self.classification_config = get_classification_config()
        
        # 固定值不需要从配置文件更新（根据PRD文档）
        # retentionperiod、wzmc、dn都是固定值
        
        logger.info("Field mapper configuration reloaded successfully")