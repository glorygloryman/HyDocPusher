"""
附件构建器模块
负责从源消息中提取和构建附件信息，支持多种附件类型和格式转换
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re
import json
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from ..models.archive_models import AttachmentData
from ..models.message_models import AppendixInfo, AttachmentItem, SourceMessageSchema
from ..exceptions.custom_exceptions import DataTransformException, ValidationException

logger = logging.getLogger(__name__)


class AttachmentBuilder:
    """附件构建器类"""
    
    def __init__(self, domain: str = "www.cnyeig.com"):
        """
        初始化附件构建器
        
        Args:
            domain: 系统域名配置，用于构建附件绝对地址
        """
        self.domain = domain.rstrip('/')
        
        # 附件类型映射
        self.attachment_type_mapping = {
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
        
        # 文件扩展名映射
        self.extension_mapping = {
            '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'],
            '视频': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
            '音频': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'],
            '文档': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            '压缩包': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Flash': ['.swf', '.fla'],
            '其他': ['.file']
        }
        
        # 附件类型优先级
        self.attachment_priority = {
            '正文': 1,
            '视频': 2,
            '图片': 3,
            '音频': 4,
            '文档': 5,
            '其他': 6
        }
    
    def build_attachments(self, source_message: SourceMessageSchema) -> List[AttachmentData]:
        """
        构建附件列表 - 支持多种附件字段
        
        Args:
            source_message: 源消息对象
            
        Returns:
            附件数据列表
            
        Raises:
            DataTransformException: 附件构建失败
        """
        if not source_message.DATA.has_attachments:
            logger.info("No attachments found in message")
            return []
        
        attachments = []
        document_title = source_message.DATA.DATA.DOCTITLE
        webhttp = source_message.DATA.DATA.WEBHTTP
        
        try:
            # 1. 构建HTML正文附件
            html_attachment = self.build_html_attachment(source_message.DATA.DATA.DOCPUBURL, document_title)
            if html_attachment:
                attachments.append(html_attachment)
            
            # 2. 从HTML内容中提取附件
            if source_message.DATA.DATA.DOCHTMLCON:
                html_attachments = self._extract_html_attachments(source_message.DATA.DATA.DOCHTMLCON)
                attachments.extend(html_attachments)
            
            # 3. 处理JSON格式附件字段
            json_fields = [
                ('DOCUMENT_RELATED_VIDEO', source_message.DATA.DATA.DOCUMENT_RELATED_VIDEO),
                ('DOCUMENT_CONTENT_VIDEO', source_message.DATA.DATA.DOCUMENT_CONTENT_VIDEO),
                ('DOCUMENT_RELATED_PIC', source_message.DATA.DATA.DOCUMENT_RELATED_PIC)
            ]
            
            for field_name, field_value in json_fields:
                if field_value:
                    json_attachments = self._parse_json_attachments(field_value, field_name)
                    attachments.extend(json_attachments)
            
            # 4. 处理传统APPENDIX数组
            if source_message.DATA.APPENDIX:
                appendix_attachments = self._build_appendix_attachments(
                    source_message.DATA.APPENDIX, document_title, webhttp
                )
                attachments.extend(appendix_attachments)
            
            # 5. 处理Appdix字段（新增）
            if source_message.DATA.appdix:
                appdix_attachments = self._build_appdix_attachments(
                    source_message.DATA.appdix, document_title
                )
                attachments.extend(appdix_attachments)
            
            # 6. 处理attachments字段（新增）
            if source_message.DATA.attachments:
                new_attachments = self._build_new_attachments(
                    source_message.DATA.attachments, document_title
                )
                attachments.extend(new_attachments)
            
            # 按file字段去重，保留第一个出现的附件
            seen_files = set()
            unique_attachments = []
            for attachment in attachments:
                if attachment.file not in seen_files:
                    seen_files.add(attachment.file)
                    unique_attachments.append(attachment)
            
            # 按优先级排序
            unique_attachments.sort(key=lambda x: self.attachment_priority.get(x.type, 999))
            attachments = unique_attachments
            
            logger.info(f"Successfully built {len(attachments)} attachments")
            return attachments
            
        except Exception as e:
            raise DataTransformException(f"Failed to build attachments: {str(e)}", cause=e)
    
    def _extract_html_attachments(self, html_content: str) -> List[AttachmentData]:
        """
        从HTML内容中提取附件
        
        Args:
            html_content: HTML内容字符串
            
        Returns:
            附件数据列表
        """
        attachments = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取<a>标签的href属性
            for a_tag in soup.find_all('a', href=True):
                url = a_tag['href']
                if self._is_attachment_url(url):
                    attachment = self._create_attachment_from_url(url, 'link')
                    if attachment:
                        attachments.append(attachment)
            
            # 提取<iframe>标签的src属性
            for iframe_tag in soup.find_all('iframe', src=True):
                url = iframe_tag['src']
                attachment = self._create_attachment_from_url(url, 'iframe')
                if attachment:
                    attachments.append(attachment)
            
            # 提取<img>标签的src属性
            for img_tag in soup.find_all('img', src=True):
                url = img_tag['src']
                attachment = self._create_attachment_from_url(url, 'image')
                if attachment:
                    attachments.append(attachment)
                    
        except Exception as e:
            logger.warning(f"Failed to extract HTML attachments: {str(e)}")
        
        return attachments
    
    def _parse_json_attachments(self, json_content: str, field_type: str) -> List[AttachmentData]:
        """
        解析JSON格式附件
        
        Args:
            json_content: JSON格式内容
            field_type: 字段类型名称
            
        Returns:
            附件数据列表
        """
        attachments = []
        
        try:
            items = json.loads(json_content)
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and 'APPURL' in item:
                        url = item['APPURL']
                        desc = item.get('APPDESC', '')
                        
                        # 转换地址
                        absolute_url = self._build_absolute_url(url)
                        
                        attachment = AttachmentData(
                            name=desc or f"{field_type}附件",
                            ext=self._extract_file_extension(url),
                            file=absolute_url,
                            type=self._determine_attachment_type(url)
                        )
                        attachments.append(attachment)
                        
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse JSON attachments from {field_type}: {str(e)}")
        
        return attachments
    
    def _build_appdix_attachments(self, appdix_list: List[AppendixInfo], document_title: str) -> List[AttachmentData]:
        """
        构建Appdix附件
        
        Args:
            appdix_list: Appdix附件列表
            document_title: 文档标题
            
        Returns:
            附件数据列表
        """
        attachments = []
        
        for i, appendix in enumerate(appdix_list):
            try:
                url = appendix.APPFILE
                absolute_url = self._build_absolute_url(url)
                
                attachment = AttachmentData(
                    name=f"Appdix附件{i+1}",
                    ext=self._extract_file_extension(url),
                    file=absolute_url,
                    type=self._determine_attachment_type(url)
                )
                attachments.append(attachment)
                
            except Exception as e:
                logger.warning(f"Failed to build Appdix attachment {i}: {str(e)}")
        
        return attachments
    
    def _build_new_attachments(self, attachments_list: List[AttachmentItem], document_title: str) -> List[AttachmentData]:
        """
        构建新格式附件
        
        Args:
            attachments_list: 新格式附件列表
            document_title: 文档标题
            
        Returns:
            附件数据列表
        """
        attachments = []
        
        for i, attachment_item in enumerate(attachments_list):
            try:
                url = attachment_item.APPURL
                absolute_url = self._build_absolute_url(url)
                
                attachment = AttachmentData(
                    name=attachment_item.APPDESC or f"附件{i+1}",
                    ext=self._extract_file_extension(url),
                    file=absolute_url,
                    type=attachment_item.attachment_type
                )
                attachments.append(attachment)
                
            except Exception as e:
                logger.warning(f"Failed to build new attachment {i}: {str(e)}")
        
        return attachments
    
    def _convert_w_suffix_address(self, address: str) -> str:
        """
        转换W后缀图片地址
        
        Args:
            address: 原始地址
            
        Returns:
            转换后的地址
        """
        # 检查是否是W后一串数字后缀名是图片的地址
        pattern = r'W\d+\.(jpg|jpeg|png|gif|bmp|webp)$'
        if re.search(pattern, address, re.IGNORECASE):
            # 现阶段直接返回原地址
            return address
        return address
    
    def _build_absolute_url(self, relative_path: str) -> str:
        """
        构建绝对地址
        
        Args:
            relative_path: 相对路径
            
        Returns:
            绝对地址
        """
        if not relative_path:
            return ""
        
        if relative_path.startswith('http'):
            return relative_path
        
        # 处理W后缀图片地址
        converted_path = self._convert_w_suffix_address(relative_path)
        
        # 确保路径以/开头
        if not converted_path.startswith('/'):
            converted_path = '/' + converted_path
        
        return f"http://{self.domain}{converted_path}"
    
    def build_html_attachment(self, pub_url: str, document_title: str) -> AttachmentData:
        """
        构建HTML正文附件
        
        Args:
            pub_url: 发布URL
            document_title: 文档标题
            
        Returns:
            HTML附件数据
            
        Raises:
            ValidationException: URL验证失败
        """
        if not pub_url or not pub_url.strip():
            raise ValidationException("Publication URL cannot be empty")
        
        try:
            # 验证URL格式
            self._validate_url(pub_url)
            
            # 创建HTML附件
            attachment_name = f"{document_title}(正文)" if document_title else "正文"
            
            return AttachmentData(
                name=attachment_name,
                ext=".html",
                file=pub_url,
                type="正文"
            )
            
        except Exception as e:
            raise DataTransformException(f"Failed to build HTML attachment: {str(e)}", cause=e)
    
    def build_media_attachments(self, related_media: List[Dict[str, Any]], media_type: str) -> List[AttachmentData]:
        """
        构建媒体附件
        
        Args:
            related_media: 相关媒体信息列表
            media_type: 媒体类型 ('video', 'image', 'audio')
            
        Returns:
            媒体附件数据列表
        """
        if not related_media:
            return []
        
        attachments = []
        
        try:
            for media_info in related_media:
                try:
                    attachment = self._build_media_attachment(media_info, media_type)
                    if attachment:
                        attachments.append(attachment)
                except Exception as e:
                    logger.warning(f"Failed to build media attachment: {str(e)}")
                    continue
            
            return attachments
            
        except Exception as e:
            logger.warning(f"Failed to build media attachments: {str(e)}")
            return []
    
    def _build_single_attachment(self, appendix: AppendixInfo, document_title: str) -> Optional[AttachmentData]:
        """
        构建单个附件
        
        Args:
            appendix: 附件信息
            document_title: 文档标题
            
        Returns:
            附件数据对象或None
        """
        if not appendix.APPFILE or not appendix.APPFILE.strip():
            logger.warning("Empty APPFILE found, skipping attachment")
            return None
        
        try:
            # 获取附件类型
            attachment_type = self._get_attachment_type(appendix.APPFLAG, appendix.APPFILE)
            
            # 获取文件扩展名
            file_extension = self._get_file_extension(appendix.APPFILE, attachment_type)
            
            # 生成附件名称
            attachment_name = self._generate_attachment_name(appendix, document_title, attachment_type)
            
            # 验证文件URL
            file_url = self._normalize_file_url(appendix.APPFILE)
            
            return AttachmentData(
                name=attachment_name,
                ext=file_extension,
                file=file_url,
                type=attachment_type
            )
            
        except Exception as e:
            logger.warning(f"Failed to build attachment for {appendix.APPFILE}: {str(e)}")
            return None
    
    def _build_media_attachment(self, media_info: Dict[str, Any], media_type: str) -> Optional[AttachmentData]:
        """
        构建媒体附件
        
        Args:
            media_info: 媒体信息字典
            media_type: 媒体类型
            
        Returns:
            媒体附件数据对象或None
        """
        try:
            # 获取媒体URL
            media_url = media_info.get('APPURL') or media_info.get('url')
            if not media_url:
                logger.warning("No media URL found in media info")
                return None
            
            # 获取媒体描述
            media_desc = media_info.get('APPDESC') or media_info.get('description') or ""
            
            # 根据媒体类型确定附件类型
            attachment_type = self._map_media_type_to_attachment_type(media_type)
            
            # 获取文件扩展名
            file_extension = self._get_file_extension(media_url, attachment_type)
            
            # 生成附件名称
            attachment_name = media_desc if media_desc else f"{media_type}_{len(media_info)}"
            
            # 验证文件URL
            file_url = self._normalize_file_url(media_url)
            
            return AttachmentData(
                name=attachment_name,
                ext=file_extension,
                file=file_url,
                type=attachment_type
            )
            
        except Exception as e:
            logger.warning(f"Failed to build media attachment: {str(e)}")
            return None
    
    def _get_attachment_type(self, appflag: str, file_url: str) -> str:
        """
        根据APPFLAG和文件URL确定附件类型
        
        Args:
            appflag: 附件类型标识
            file_url: 文件URL
            
        Returns:
            附件类型字符串
        """
        # 首先根据APPFLAG确定类型
        attachment_type = self.attachment_type_mapping.get(appflag, '其他')
        
        # 如果是其他类型，尝试根据文件扩展名推断
        if attachment_type == '其他':
            attachment_type = self._infer_type_from_extension(file_url)
        
        return attachment_type
    
    def _infer_type_from_extension(self, file_url: str) -> str:
        """
        根据文件扩展名推断附件类型
        
        Args:
            file_url: 文件URL
            
        Returns:
            附件类型字符串
        """
        file_ext = self._extract_file_extension(file_url).lower()
        
        for attachment_type, extensions in self.extension_mapping.items():
            if file_ext in extensions:
                return attachment_type
        
        return '其他'
    
    def _get_file_extension(self, file_url: str, attachment_type: str) -> str:
        """
        获取文件扩展名
        
        Args:
            file_url: 文件URL
            attachment_type: 附件类型
            
        Returns:
            文件扩展名
        """
        # 尝试从URL中提取扩展名
        file_ext = self._extract_file_extension(file_url)
        
        # 如果没有扩展名，根据附件类型提供默认扩展名
        if not file_ext:
            default_extensions = {
                '图片': '.jpg',
                '视频': '.mp4',
                '音频': '.mp3',
                '文档': '.pdf',
                '正文': '.html',
                '其他': '.file'
            }
            file_ext = default_extensions.get(attachment_type, '.file')
        
        # 确保扩展名以点开头
        if not file_ext.startswith('.'):
            file_ext = f".{file_ext}"
        
        return file_ext.lower()
    
    def _extract_file_extension(self, file_url: str) -> str:
        """
        从文件URL中提取扩展名
        
        Args:
            file_url: 文件URL
            
        Returns:
            文件扩展名（不带点）
        """
        if not file_url:
            return ""
        
        # 移除查询参数
        if '?' in file_url:
            file_url = file_url.split('?')[0]
        
        # 获取文件名部分
        parsed_url = urlparse(file_url)
        filename = parsed_url.path.split('/')[-1]
        
        # 提取扩展名
        if '.' in filename:
            return filename.split('.')[-1].lower()
        
        return ""
    
    def _generate_attachment_name(self, appendix: AppendixInfo, document_title: str, attachment_type: str) -> str:
        """
        生成附件名称
        
        Args:
            appendix: 附件信息
            document_title: 文档标题
            attachment_type: 附件类型
            
        Returns:
            附件名称
        """
        # 如果附件是视频播放页，使用特定名称
        if appendix.APPFLAG == '140':
            return f"{document_title}_视频播放页"
        
        # 尝试从文件URL中提取文件名
        filename = self._extract_filename_from_url(appendix.APPFILE)
        
        if filename and filename != appendix.APPFILE:
            # 清理文件名
            filename = self._clean_filename(filename)
            return filename
        else:
            # 使用文档标题和附件类型生成名称
            base_name = document_title if document_title else "附件"
            return f"{base_name}_{attachment_type}"
    
    def _extract_filename_from_url(self, file_url: str) -> str:
        """
        从URL中提取文件名
        
        Args:
            file_url: 文件URL
            
        Returns:
            文件名
        """
        if not file_url:
            return ""
        
        try:
            # 移除查询参数
            if '?' in file_url:
                file_url = file_url.split('?')[0]
            
            # 解析URL
            parsed_url = urlparse(file_url)
            filename = parsed_url.path.split('/')[-1]
            
            # 移除扩展名
            if '.' in filename:
                filename = filename.split('.')[0]
            
            return filename
            
        except Exception:
            return ""
    
    def _clean_filename(self, filename: str) -> str:
        """
        清理文件名
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        if not filename:
            return ""
        
        # 移除特殊字符
        cleaned = re.sub(r'[^\w\s-]', '', filename)
        
        # 替换空格为下划线
        cleaned = re.sub(r'\s+', '_', cleaned)
        
        # 限制长度
        max_length = 100
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned.strip()
    
    def _normalize_file_url(self, file_url: str) -> str:
        """
        规范化文件URL
        
        Args:
            file_url: 原始文件URL
            
        Returns:
            规范化后的URL
            
        Raises:
            ValidationException: URL格式无效
        """
        if not file_url or not file_url.strip():
            raise ValidationException("File URL cannot be empty")
        
        file_url = file_url.strip()
        
        # 验证URL格式
        self._validate_url(file_url)
        
        # 如果是相对路径，尝试转换为绝对路径
        if file_url.startswith('/'):
            # 这里可以根据实际需求添加基础URL
            # 例如: base_url = "https://www.example.com"
            # file_url = f"{base_url}{file_url}"
            pass
        
        return file_url
    
    def _validate_url(self, url: str) -> None:
        """
        验证URL格式
        
        Args:
            url: URL字符串
            
        Raises:
            ValidationException: URL格式无效
        """
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                # 如果不是完整的URL，检查是否是相对路径
                if not (url.startswith('/') or url.startswith('./') or url.startswith('../')):
                    raise ValidationException(f"Invalid URL format: {url}")
        except Exception as e:
            raise ValidationException(f"Invalid URL format: {url}", cause=e)
    
    def _map_media_type_to_attachment_type(self, media_type: str) -> str:
        """
        将媒体类型映射到附件类型
        
        Args:
            media_type: 媒体类型
            
        Returns:
            附件类型
        """
        type_mapping = {
            'video': '视频',
            'image': '图片',
            'audio': '音频',
            'document': '文档'
        }
        
        return type_mapping.get(media_type.lower(), '其他')
    
    def filter_attachments(self, attachments: List[AttachmentData], 
                          max_count: int = 10, 
                          max_size: int = 50) -> List[AttachmentData]:
        """
        过滤附件列表
        
        Args:
            attachments: 原始附件列表
            max_count: 最大附件数量
            max_size: 最大附件大小（MB）
            
        Returns:
            过滤后的附件列表
        """
        if not attachments:
            return []
        
        # 按优先级排序
        filtered = sorted(attachments, key=lambda x: self.attachment_priority.get(x.type, 999))
        
        # 限制数量
        if len(filtered) > max_count:
            filtered = filtered[:max_count]
            logger.info(f"Limited attachments to {max_count} items")
        
        # 这里可以添加文件大小检查
        # 由于我们无法直接获取远程文件大小，这里只是预留接口
        
        return filtered
    
    def get_attachment_summary(self, attachments: List[AttachmentData]) -> Dict[str, Any]:
        """
        获取附件摘要信息
        
        Args:
            attachments: 附件列表
            
        Returns:
            附件摘要字典
        """
        if not attachments:
            return {
                'total_count': 0,
                'by_type': {},
                'types': []
            }
        
        # 按类型统计
        type_counts = {}
        for attachment in attachments:
            att_type = attachment.type
            type_counts[att_type] = type_counts.get(att_type, 0) + 1
        
        return {
            'total_count': len(attachments),
            'by_type': type_counts,
            'types': list(type_counts.keys())
        }
    
    def _is_attachment_url(self, url: str) -> bool:
        """
        判断URL是否为附件
        
        Args:
            url: URL字符串
            
        Returns:
            是否为附件
        """
        # 排除页面链接，只保留文件链接
        file_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                          '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
                          '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
                          '.mp3', '.wav', '.aac', '.flac', '.ogg', '.zip', '.rar'}
        
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in file_extensions)
    
    def _create_attachment_from_url(self, url: str, source_type: str) -> Optional[AttachmentData]:
        """
        从URL创建附件对象
        
        Args:
            url: URL字符串
            source_type: 来源类型
            
        Returns:
            附件数据对象或None
        """
        try:
            absolute_url = self._build_absolute_url(url)
            
            return AttachmentData(
                name=f"{source_type}附件",
                ext=self._extract_file_extension(url),
                file=absolute_url,
                type=self._determine_attachment_type(url)
            )
        except Exception as e:
            logger.warning(f"Failed to create attachment from URL {url}: {str(e)}")
            return None
    
    # Legacy method for backward compatibility
    def build_attachments_legacy(self, appendix_list: List[AppendixInfo], document_title: str) -> List[AttachmentData]:
        """
        构建附件列表 - 传统方法（保持向后兼容）
        
        Args:
            appendix_list: 附件信息列表
            document_title: 文档标题
            
        Returns:
            附件数据列表
        """
        if not appendix_list:
            logger.info("No attachments found in message")
            return []
        
        attachments = []
        
        try:
            for appendix in appendix_list:
                try:
                    attachment = self._build_single_attachment(appendix, document_title)
                    if attachment:
                        attachments.append(attachment)
                except Exception as e:
                    logger.warning(f"Failed to build attachment for {appendix.APPFILE}: {str(e)}")
                    continue
            
            # 按优先级排序
            attachments.sort(key=lambda x: self.attachment_priority.get(x.type, 999))
            
            logger.info(f"Successfully built {len(attachments)} attachments (legacy method)")
            return attachments
            
        except Exception as e:
            raise DataTransformException(f"Failed to build attachments: {str(e)}", cause=e)
    
    def _determine_attachment_type(self, url: str) -> str:
        """确定附件类型"""
        extension = self._extract_file_extension(url)
        
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
        video_exts = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}
        audio_exts = {'mp3', 'wav', 'aac', 'flac', 'ogg'}
        doc_exts = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}
        
        if extension in image_exts:
            return "图片"
        elif extension in video_exts:
            return "视频"
        elif extension in audio_exts:
            return "音频"
        elif extension in doc_exts:
            return "文档"
        else:
            return "其他"
    
    def _build_appendix_attachments(self, appendix_list: List[AppendixInfo], document_title: str, webhttp: str) -> List[AttachmentData]:
        """构建传统APPENDIX附件"""
        attachments = []
        
        for i, appendix in enumerate(appendix_list):
            try:
                url = appendix.APPFILE
                # 使用域名构建绝对地址，而不是使用webhttp
                absolute_url = self._build_absolute_url(url)
                
                attachment = AttachmentData(
                    name=f"附件{i+1}",
                    ext=self._extract_file_extension(url),
                    file=absolute_url,
                    type=self._get_attachment_type(appendix.APPFLAG, url)
                )
                attachments.append(attachment)
                
            except Exception as e:
                logger.warning(f"Failed to build appendix attachment {i}: {str(e)}")
        
        return attachments