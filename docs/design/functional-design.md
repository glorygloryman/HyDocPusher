# 功能设计文档

## 1. 功能模块总览

基于PRD需求，HyDocPusher包含以下核心功能模块：

```
┌─────────────────────────────────────────────────────────────┐
│                     HyDocPusher 功能架构                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   消息消费功能   │  │   数据转换功能   │  │   数据推送功能   │ │
│  │                 │  │                 │  │                 │ │
│  │ • Pulsar连接    │  │ • 字段映射      │  │ • HTTP调用      │ │
│  │ • Topic订阅     │  │ • 分类映射      │  │ • 重试机制      │ │
│  │ • 消息解析      │  │ • 附件构建      │  │ • 响应处理      │ │
│  │ • 错误处理      │  │ • 数据验证      │  │ • 死信队列      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   配置管理功能   │  │   日志记录功能   │  │   监控运维功能   │ │
│  │                 │  │                 │  │                 │ │
│  │ • 应用配置      │  │ • 结构化日志    │  │ • 健康检查      │ │
│  │ • 分类规则      │  │ • 错误日志      │  │ • 性能指标      │ │
│  │ • 环境配置      │  │ • 审计日志      │  │ • 告警机制      │ │
│  │ • 配置验证      │  │ • 日志轮转      │  │ • 运维接口      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 2. 消息消费功能设计

### 2.1 Pulsar连接管理

**功能描述**: 建立和维护与Pulsar集群的连接

**技术实现**:
```python
import asyncio
from pulsar import Client
from typing import Optional

class PulsarConnectionManager:
    def __init__(self, config: 'PulsarConfig'):
        self.config = config
        self.client: Optional[Client] = None
    
    async def initialize(self):
        """初始化Pulsar客户端连接"""
        self.client = Client(
            service_url=self.config.cluster_url,
            connection_timeout_ms=30000,
            operation_timeout_ms=30000
        )
    
    async def create_consumer(self):
        """创建Pulsar消费者"""
        if not self.client:
            await self.initialize()
        
        return self.client.subscribe(
            topic=self.config.topic,
            subscription_name=self.config.subscription,
            subscription_type='Shared',
            ack_timeout_ms=30000,
            dead_letter_policy={
                'max_redeliver_count': 3,
                'dead_letter_topic': self.config.dead_letter_topic
            }
        )
    
    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()
```

**配置参数**:
- `pulsar.cluster.url`: Pulsar集群地址
- `pulsar.topic`: 订阅的Topic
- `pulsar.subscription`: 订阅名称
- `pulsar.connection-timeout`: 连接超时时间
- `pulsar.ack-timeout`: 消息确认超时时间

### 2.2 消息订阅和接收

**功能描述**: 订阅指定Topic，接收内容发布消息

**技术实现**:
```java
@Service
public class MessageConsumer {
    private Consumer<String> consumer;
    private final MessageHandler messageHandler;
    
    @Async
    public void startConsuming() {
        while (true) {
            try {
                Message<String> message = consumer.receive();
                String messageId = message.getMessageId().toString();
                
                log.info("Received message: {}", messageId);
                
                // 处理消息
                messageHandler.handle(message.getValue());
                
                // 确认消息
                consumer.acknowledge(message);
                
            } catch (PulsarClientException e) {
                log.error("Error receiving message", e);
                // 等待后重试
                Thread.sleep(5000);
            }
        }
    }
}
```

**消息处理流程**:
1. 接收消息
2. 记录消息ID日志
3. 调用消息处理器
4. 处理成功后确认消息
5. 处理失败时进行重试

### 2.3 消息解析和验证

**功能描述**: 解析JSON格式消息，验证数据完整性

**技术实现**:
```python
import json
from typing import Dict, Any
from pydantic import ValidationError

class MessageParser:
    def __init__(self):
        pass
    
    def parse(self, raw_message: str) -> SourceMessage:
        """解析原始JSON消息"""
        try:
            message_data = json.loads(raw_message)
            message = SourceMessage(**message_data)
            self.validate_message(message)
            return message
        except json.JSONDecodeError as e:
            raise MessageParseException(f"Failed to parse message JSON: {e}")
        except ValidationError as e:
            raise MessageParseException(f"Message validation failed: {e}")
    
    def validate_message(self, message: SourceMessage):
        """验证消息数据完整性"""
        if not message.data:
            raise ValidationException("DATA field is required")
        
        if not message.data.data:
            raise ValidationException("DATA.DATA field is required")
        
        # 验证必填字段
        data = message.data.data
        self.validate_required_field(data.recid, "RECID")
        self.validate_required_field(data.sitename, "SITENAME")
        self.validate_required_field(data.doctitle, "DOCTITLE")
        self.validate_required_field(data.docreltime, "DOCRELTIME")
    
    def validate_required_field(self, value: str, field_name: str):
        """验证必填字段"""
        if not value or not value.strip():
            raise ValidationException(f"{field_name} is required")
```

## 3. 数据转换功能设计

### 3.1 ArchiveRequest构建功能

**功能描述**: 将SourceMessage转换为ArchiveRequest格式，支持新的附件处理逻辑

**技术实现**:
```python
from typing import Dict, Any, List
import logging
from datetime import datetime

class ArchiveRequestBuilderService:
    def __init__(self, attachment_builder: AttachmentBuilderService, 
                 classification_service: ClassificationService,
                 app_config: AppConfig):
        self.attachment_builder = attachment_builder
        self.classification_service = classification_service
        self.app_config = app_config
        self.logger = logging.getLogger(__name__)
    
    def build_archive_request(self, source_message: SourceMessage) -> ArchiveRequest:
        """构建档案请求对象"""
        try:
            request = ArchiveRequest()
            data = source_message.data.data
            
            # 设置基本信息
            request.company_name = self.app_config.company_name
            request.archive_type = self.app_config.archive_type
            request.title = data.doctitle
            request.content = data.doccontent
            request.create_time = self._format_date(data.docdate)
            request.author = data.docauthor
            
            # 设置分类
            classification = self.classification_service.get_classification(data)
            request.classification = classification
            
            # 构建附件（支持新的附件字段）
            attachments = self.attachment_builder.build_attachments(source_message)
            request.attachments = attachments
            
            # 设置元数据
            metadata = self._build_metadata(source_message)
            request.metadata = metadata
            
            self.logger.info(f"成功构建ArchiveRequest，标题: {request.title}，附件数量: {len(attachments)}")
            return request
            
        except Exception as e:
            self.logger.error(f"构建ArchiveRequest失败: {e}")
            raise ArchiveRequestBuildException(f"构建档案请求失败: {e}")
    
    def _build_metadata(self, source_message: SourceMessage) -> Dict[str, Any]:
        """构建元数据"""
        metadata = {}
        data = source_message.data.data
        
        # 基础元数据
        metadata['sourceSystem'] = 'HyDocPusher'
        metadata['docId'] = data.docid
        metadata['docType'] = data.doctype
        metadata['docStatus'] = data.docstatus
        metadata['publishUrl'] = data.docpuburl
        metadata['webHttp'] = data.webhttp
        
        # 新增附件相关元数据
        if data.dochtmlcon:
            metadata['hasHtmlContent'] = True
            metadata['htmlContentLength'] = len(data.dochtmlcon)
        
        # 记录各种附件字段的存在情况
        attachment_fields = {
            'hasDocumentRelatedVideo': bool(data.document_related_video),
            'hasDocumentContentVideo': bool(data.document_content_video),
            'hasDocumentRelatedPic': bool(data.document_related_pic),
            'hasAppdix': bool(source_message.data.appdix),
            'hasAppendix': bool(source_message.data.appendix)
        }
        metadata.update(attachment_fields)
        
        # 处理时间戳
        metadata['processTime'] = datetime.now().isoformat()
        metadata['domain'] = self.app_config.domain
        
        return metadata
    
    def _format_date(self, date_str: str) -> str:
        """格式化日期字符串"""
        if not date_str:
            return datetime.now().isoformat()
        
        try:
            # 尝试解析常见的日期格式
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            return parsed_date.isoformat()
        except Exception:
            # 如果解析失败，返回当前时间
            self.logger.warning(f"日期格式解析失败: {date_str}，使用当前时间")
            return datetime.now().isoformat()

class ArchiveRequestBuildException(Exception):
    """档案请求构建异常"""
    pass
```

### 3.2 字段映射功能

**功能描述**: 将源数据字段映射到目标档案系统字段

**技术实现**:
```java
@Service
public class FieldMapperService {
    private final AppConfig appConfig;
    
    public ArchiveRequest mapFields(SourceMessage source) {
        ArchiveRequest request = new ArchiveRequest();
        DataData data = source.getDATA().getDATA();
        
        // 设置顶层字段
        request.setAppId(appConfig.getAppId());
        request.setAppToken(appConfig.getAppToken());
        request.setCompanyName(appConfig.getCompanyName());
        request.setArchiveType(appConfig.getArchiveType());
        
        // 构建ArchiveData
        ArchiveRequest.ArchiveData archiveData = new ArchiveRequest.ArchiveData();
        archiveData.setDid(data.getRECID());
        archiveData.setWzmc(data.getSITENAME());
        archiveData.setDn(appConfig.getDomain());
        archiveData.setTitle(data.getDOCTITLE());
        archiveData.setAuthor(data.getTXY());
        archiveData.setDocDate(formatDate(data.getDOCRELTIME()));
        archiveData.setYear(extractYear(data.getDOCRELTIME()));
        archiveData.setRetentionperiod(appConfig.getRetentionPeriod());
        archiveData.setFillingdepartment(source.getDATA().getCHNLDOC().getCRDEPT());
        archiveData.setBly(data.getCRUSER());
        
        request.setArchiveData(archiveData);
        return request;
    }
    
    private String formatDate(String docRelTime) {
        // 解析日期并格式化为YYYY-MM-DD
        try {
            LocalDateTime dateTime = LocalDateTime.parse(docRelTime, 
                DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
            return dateTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        } catch (Exception e) {
            log.warn("Failed to parse date: {}", docRelTime);
            return docRelTime.substring(0, 10); // 简单处理
        }
    }
    
    private String extractYear(String docRelTime) {
        return docRelTime.substring(0, 4);
    }
}
```

### 3.3 分类映射功能

**功能描述**: 根据频道ID映射分类名称和代码

**技术实现**:
```java
@Service
public class ClassificationMapper {
    private final ClassificationConfig classificationConfig;
    
    public void mapClassification(ArchiveRequest.ArchiveData archiveData, String channelId) {
        ClassificationRule rule = classificationConfig.findRule(channelId);
        
        if (rule == null) {
            rule = classificationConfig.getDefaultRule();
            log.warn("No classification rule found for channel: {}, using default", channelId);
        }
        
        archiveData.setClassfyname(rule.getClassfyname());
        archiveData.setClassfy(rule.getClassfy());
        
        log.info("Mapped classification for channel {}: {} -> {}", 
            channelId, rule.getClassfyname(), rule.getClassfy());
    }
}
```

### 3.4 附件构建功能

**功能描述**: 构建附件数组，支持多种附件字段和地址转换

**技术实现**:
```python
import re
import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup

class AttachmentBuilderService:
    def __init__(self, app_config: AppConfig):
        self.app_config = app_config
        self.domain = app_config.domain
    
    def build_attachments(self, source_message: SourceMessage) -> List[AttachmentData]:
        """构建附件列表"""
        attachments = []
        data = source_message.data.data
        
        # 处理HTML内容附件
        if data.dochtmlcon:
            html_attachments = self._extract_html_attachments(data.dochtmlcon)
            attachments.extend(html_attachments)
        
        # 处理JSON格式附件字段
        json_fields = [
            ('DOCUMENT_RELATED_VIDEO', data.document_related_video),
            ('DOCUMENT_CONTENT_VIDEO', data.document_content_video),
            ('DOCUMENT_RELATED_PIC', data.document_related_pic)
        ]
        
        for field_name, field_value in json_fields:
            if field_value:
                json_attachments = self._parse_json_attachments(field_value, field_name)
                attachments.extend(json_attachments)
        
        # 处理Appdix字段
        if source_message.data.appdix:
            appdix_attachments = self._build_appdix_attachments(source_message.data.appdix)
            attachments.extend(appdix_attachments)
        
        # 处理原有APPENDIX字段（保持兼容性）
        if source_message.data.appendix:
            appendix_attachments = self._build_appendix_attachments(source_message.data.appendix, data.webhttp)
            attachments.extend(appendix_attachments)
        
        return attachments
    
    def _extract_html_attachments(self, html_content: str) -> List[AttachmentData]:
        """从HTML内容中提取附件"""
        attachments = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取<a>标签的href属性
        for a_tag in soup.find_all('a', href=True):
            url = a_tag['href']
            if self._is_attachment_url(url):
                attachment = self._create_attachment_from_url(url, 'link')
                attachments.append(attachment)
        
        # 提取<iframe>标签的src属性
        for iframe_tag in soup.find_all('iframe', src=True):
            url = iframe_tag['src']
            attachment = self._create_attachment_from_url(url, 'iframe')
            attachments.append(attachment)
        
        # 提取<img>标签的src属性
        for img_tag in soup.find_all('img', src=True):
            url = img_tag['src']
            attachment = self._create_attachment_from_url(url, 'image')
            attachments.append(attachment)
        
        return attachments
    
    def _parse_json_attachments(self, json_content: str, field_type: str) -> List[AttachmentData]:
        """解析JSON格式附件"""
        attachments = []
        try:
            items = json.loads(json_content)
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
            # 记录错误但不中断处理
            pass
        
        return attachments
    
    def _build_appdix_attachments(self, appdix_list: List[Appendix]) -> List[AttachmentData]:
        """构建Appdix附件"""
        attachments = []
        for i, appendix in enumerate(appdix_list):
            url = appendix.appfile
            absolute_url = self._build_absolute_url(url)
            
            attachment = AttachmentData(
                name=f"Appdix附件{i+1}",
                ext=self._extract_file_extension(url),
                file=absolute_url,
                type=self._determine_attachment_type(url)
            )
            attachments.append(attachment)
        
        return attachments
    
    def _build_appendix_attachments(self, appendix_list: List[Appendix], webhttp: str) -> List[AttachmentData]:
        """构建原有APPENDIX附件（保持兼容性）"""
        attachments = []
        for i, appendix in enumerate(appendix_list):
            url = appendix.appfile
            # 原有逻辑：WEBHTTP + APPFILE
            full_url = webhttp + url if not url.startswith('http') else url
            
            attachment = AttachmentData(
                name=f"附件{i+1}",
                ext=self._extract_file_extension(url),
                file=full_url,
                type=self._determine_attachment_type(url)
            )
            attachments.append(attachment)
        
        return attachments
    
    def _convert_w_suffix_address(self, address: str) -> str:
        """转换W后缀图片地址"""
        # 检查是否是W后一串数字后缀名是图片的地址
        pattern = r'W\d+\.(jpg|jpeg|png|gif|bmp|webp)$'
        if re.search(pattern, address, re.IGNORECASE):
            # 现阶段直接返回原地址
            return address
        return address
    
    def _build_absolute_url(self, relative_path: str) -> str:
        """构建绝对地址"""
        if relative_path.startswith('http'):
            return relative_path
        
        # 处理W后缀图片地址
        converted_path = self._convert_w_suffix_address(relative_path)
        
        # 确保路径以/开头
        if not converted_path.startswith('/'):
            converted_path = '/' + converted_path
        
        return f"http://{self.domain}{converted_path}"
    
    def _extract_file_extension(self, url: str) -> str:
        """提取文件扩展名"""
        if not url:
            return ""
        
        # 移除查询参数
        url = url.split('?')[0]
        last_dot_index = url.rfind('.')
        
        if last_dot_index == -1:
            return ""
        
        return url[last_dot_index + 1:].lower()
    
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
            return "附件"
    
    def _is_attachment_url(self, url: str) -> bool:
        """判断URL是否为附件"""
        # 排除页面链接，只保留文件链接
        file_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                          '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
                          '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
                          '.mp3', '.wav', '.aac', '.flac', '.ogg', '.zip', '.rar'}
        
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in file_extensions)
    
    def _create_attachment_from_url(self, url: str, source_type: str) -> AttachmentData:
        """从URL创建附件对象"""
        absolute_url = self._build_absolute_url(url)
        
        return AttachmentData(
            name=f"{source_type}附件",
            ext=self._extract_file_extension(url),
            file=absolute_url,
            type=self._determine_attachment_type(url)
        )
```
```

## 4. 数据推送功能设计

### 4.1 HTTP客户端功能

**功能描述**: 向档案系统发送HTTP POST请求

**技术实现**:
```java
@Service
public class ArchiveClientService {
    private final HttpClient httpClient;
    private final ArchiveConfig archiveConfig;
    
    public ArchiveResponse sendArchiveRequest(ArchiveRequest request) {
        try {
            String jsonRequest = objectMapper.writeValueAsString(request);
            HttpRequest httpRequest = HttpRequest.newBuilder()
                .uri(URI.create(archiveConfig.getApiUrl()))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofMillis(archiveConfig.getTimeout()))
                .POST(HttpRequest.BodyPublishers.ofString(jsonRequest))
                .build();
            
            HttpResponse<String> response = httpClient.send(httpRequest, 
                HttpResponse.BodyHandlers.ofString());
            
            return parseResponse(response);
            
        } catch (Exception e) {
            throw new ArchiveClientException("Failed to send archive request", e);
        }
    }
    
    private ArchiveResponse parseResponse(HttpResponse<String> response) {
        ArchiveResponse archiveResponse = objectMapper.readValue(response.body(), 
            ArchiveResponse.class);
        
        if (response.statusCode() != 200) {
            throw new ArchiveClientException(
                String.format("API returned status %d: %s", 
                    response.statusCode(), response.body()));
        }
        
        return archiveResponse;
    }
}
```

### 4.2 重试机制功能

**功能描述**: 实现失败请求的自动重试逻辑

**技术实现**:
```java
@Service
public class RetryService {
    private final ArchiveConfig archiveConfig;
    
    public ArchiveResponse sendWithRetry(Supplier<ArchiveResponse> requestSupplier) {
        int maxAttempts = archiveConfig.getRetry().getMaxAttempts();
        long delay = archiveConfig.getRetry().getDelay();
        
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                ArchiveResponse response = requestSupplier.get();
                log.info("Archive request succeeded on attempt {}", attempt);
                return response;
                
            } catch (Exception e) {
                if (attempt == maxAttempts) {
                    log.error("Archive request failed after {} attempts", maxAttempts, e);
                    throw new ArchiveClientException("Request failed after " + maxAttempts + " attempts", e);
                }
                
                log.warn("Archive request failed on attempt {}, retrying in {}ms", attempt, delay, e);
                Thread.sleep(delay);
            }
        }
        
        throw new ArchiveClientException("Unexpected error in retry logic");
    }
}
```

### 4.3 响应处理功能

**功能描述**: 处理档案系统的响应结果

**技术实现**:
```java
@Service
public class ResponseHandler {
    public void handleResponse(ArchiveResponse response, String messageId) {
        if (response.getSTATUS() == 0) {
            // 成功响应
            log.info("Archive request succeeded for message {}, dataId: {}", 
                messageId, response.getDATAID());
            
        } else {
            // 失败响应
            log.error("Archive request failed for message {}, status: {}, description: {}", 
                messageId, response.getSTATUS(), response.getDESC());
            
            throw new ArchiveClientException(
                String.format("Archive API returned error: status=%d, description=%s", 
                    response.getSTATUS(), response.getDESC()));
        }
    }
}
```

## 5. 配置管理功能设计

### 5.1 配置加载功能

**功能描述**: 加载和管理应用配置，支持域名配置

**技术实现**:
```java
@Configuration
@EnableConfigurationProperties
public class AppConfigLoader {
    
    @Bean
    @ConfigurationProperties(prefix = "pulsar")
    public PulsarConfig pulsarConfig() {
        return new PulsarConfig();
    }
    
    @Bean
    @ConfigurationProperties(prefix = "archive")
    public ArchiveConfig archiveConfig() {
        return new ArchiveConfig();
    }
    
    @Bean
    @ConfigurationProperties(prefix = "classification")
    public ClassificationConfig classificationConfig() {
        return new ClassificationConfig();
    }
    
    @Bean
    @ConfigurationProperties(prefix = "app")
    public AppConfig appConfig() {
        return new AppConfig();
    }
}```

### 5.2 配置验证功能

**功能描述**: 启动时验证配置的完整性和有效性，包括域名配置验证

**技术实现**:
```java
@Service
public class ConfigValidator {
    private final PulsarConfig pulsarConfig;
    private final ArchiveConfig archiveConfig;
    private final ClassificationConfig classificationConfig;
    private final AppConfig appConfig;
    
    @PostConstruct
    public void validateConfig() {
        validatePulsarConfig();
        validateArchiveConfig();
        validateClassificationConfig();
        validateAppConfig();
    }
    
    private void validatePulsarConfig() {
        if (StringUtils.isEmpty(pulsarConfig.getClusterUrl())) {
            throw new ConfigException("Pulsar cluster URL is required");
        }
        
        if (StringUtils.isEmpty(pulsarConfig.getTopic())) {
            throw new ConfigException("Pulsar topic is required");
        }
        
        if (StringUtils.isEmpty(pulsarConfig.getSubscription())) {
            throw new ConfigException("Pulsar subscription is required");
        }
    }
    
    private void validateArchiveConfig() {
        if (StringUtils.isEmpty(archiveConfig.getApiUrl())) {
            throw new ConfigException("Archive API URL is required");
        }
        
        if (StringUtils.isEmpty(archiveConfig.getAppId())) {
            throw new ConfigException("Archive AppId is required");
        }
        
        if (StringUtils.isEmpty(archiveConfig.getAppToken())) {
            throw new ConfigException("Archive AppToken is required");
        }
        
        if (archiveConfig.getTimeout() <= 0) {
            throw new ConfigException("Archive timeout must be greater than 0");
        }
    }
    
    private void validateClassificationConfig() {
        if (classificationConfig.getRules() == null || 
            classificationConfig.getRules().isEmpty()) {
            throw new ConfigException("Classification rules are required");
        }
        
        // 验证是否有默认规则
        boolean hasDefault = classificationConfig.getRules().stream()
            .anyMatch(rule -> "default".equals(rule.getChannelId()));
        
        if (!hasDefault) {
            throw new ConfigException("Default classification rule is required");
        }
    }
    
    private void validateAppConfig() {
        if (StringUtils.isEmpty(appConfig.getDomain())) {
            throw new ConfigException("Application domain is required");
        }
        
        if (!isValidDomain(appConfig.getDomain())) {
            throw new ConfigException("Invalid domain format: " + appConfig.getDomain());
        }
        
        if (StringUtils.isEmpty(appConfig.getCompanyName())) {
            throw new ConfigException("Company name is required");
        }
        
        if (StringUtils.isEmpty(appConfig.getArchiveType())) {
            throw new ConfigException("Archive type is required");
        }
    }
    
    private boolean isValidDomain(String domain) {
        // 简单的域名格式验证
        String domainPattern = "^[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?(\\.[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?)*$";
        return domain.matches(domainPattern);
    }
}```

## 6. 日志记录功能设计

### 6.1 结构化日志功能

**功能描述**: 记录结构化的日志信息，便于分析和监控

**技术实现**:
```java
@Service
public class StructuredLogger {
    private static final Logger logger = LoggerFactory.getLogger(StructuredLogger.class);
    
    public void logMessageReceived(String messageId, String topic) {
        Map<String, Object> logData = new HashMap<>();
        logData.put("event", "message_received");
        logData.put("message_id", messageId);
        logData.put("topic", topic);
        logData.put("timestamp", Instant.now());
        
        logger.info("{}", objectMapper.writeValueAsString(logData));
    }
    
    public void logMessageProcessed(String messageId, long processingTime) {
        Map<String, Object> logData = new HashMap<>();
        logData.put("event", "message_processed");
        logData.put("message_id", messageId);
        logData.put("processing_time_ms", processingTime);
        logData.put("timestamp", Instant.now());
        
        logger.info("{}", objectMapper.writeValueAsString(logData));
    }
    
    public void logError(String messageId, String errorType, String errorMessage) {
        Map<String, Object> logData = new HashMap<>();
        logData.put("event", "error");
        logData.put("message_id", messageId);
        logData.put("error_type", errorType);
        logData.put("error_message", errorMessage);
        logData.put("timestamp", Instant.now());
        
        logger.error("{}", objectMapper.writeValueAsString(logData));
    }
}
```

### 6.2 审计日志功能

**功能描述**: 记录关键操作的审计日志

**技术实现**:
```java
@Service
public class AuditLogger {
    private static final Logger auditLogger = LoggerFactory.getLogger("AUDIT");
    
    public void logArchiveRequest(String messageId, ArchiveRequest request) {
        Map<String, Object> auditData = new HashMap<>();
        auditData.put("event", "archive_request");
        auditData.put("message_id", messageId);
        auditData.put("app_id", request.getAppId());
        auditData.put("archive_type", request.getArchiveType());
        auditData.put("document_id", request.getArchiveData().getDid());
        auditData.put("timestamp", Instant.now());
        
        auditLogger.info("{}", objectMapper.writeValueAsString(auditData));
    }
    
    public void logArchiveResponse(String messageId, ArchiveResponse response) {
        Map<String, Object> auditData = new HashMap<>();
        auditData.put("event", "archive_response");
        auditData.put("message_id", messageId);
        auditData.put("status", response.getSTATUS());
        auditData.put("data_id", response.getDATAID());
        auditData.put("timestamp", Instant.now());
        
        auditLogger.info("{}", objectMapper.writeValueAsString(auditData));
    }
}
```

## 7. 监控运维功能设计

### 7.1 健康检查功能

**功能描述**: 提供应用健康状态检查接口

**技术实现**:
```java
@RestController
@RequestMapping("/health")
public class HealthController {
    
    @GetMapping
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("timestamp", Instant.now());
        health.put("version", getAppVersion());
        
        // 检查各个组件状态
        health.put("pulsar", checkPulsarConnection());
        health.put("archive", checkArchiveConnection());
        
        return ResponseEntity.ok(health);
    }
    
    private Map<String, Object> checkPulsarConnection() {
        Map<String, Object> status = new HashMap<>();
        try {
            // 检查Pulsar连接状态
            status.put("status", "UP");
            status.put("connected", true);
        } catch (Exception e) {
            status.put("status", "DOWN");
            status.put("error", e.getMessage());
        }
        return status;
    }
    
    private Map<String, Object> checkArchiveConnection() {
        Map<String, Object> status = new HashMap<>();
        try {
            // 检查档案系统连接状态
            status.put("status", "UP");
            status.put("connected", true);
        } catch (Exception e) {
            status.put("status", "DOWN");
            status.put("error", e.getMessage());
        }
        return status;
    }
}
```

### 7.2 性能监控功能

**功能描述**: 监控应用性能指标

**技术实现**:
```java
@Service
public class PerformanceMonitor {
    private final MeterRegistry meterRegistry;
    
    @EventListener
    public void handleMessageReceived(MessageReceivedEvent event) {
        Timer.Sample sample = Timer.start(meterRegistry);
        event.setTimerSample(sample);
    }
    
    @EventListener
    public void handleMessageProcessed(MessageProcessedEvent event) {
        Timer.Sample sample = event.getTimerSample();
        sample.stop(meterRegistry.timer("message.processing.time"));
        
        // 记录计数器
        meterRegistry.counter("message.processed.count").increment();
    }
    
    @EventListener
    public void handleError(ErrorEvent event) {
        meterRegistry.counter("error.count", 
            "type", event.getErrorType()).increment();
    }
}
```

## 8. 功能模块交互流程

### 8.1 完整处理流程
1. **启动阶段**: 配置验证 → 连接建立 → 服务初始化
2. **运行阶段**: 消息接收 → 数据转换 → HTTP推送 → 结果处理
3. **错误处理**: 异常捕获 → 日志记录 → 重试/死信队列

### 8.2 关键业务流程
1. **消息处理流程**: PulsarConsumer → MessageHandler → DataTransformer → ArchiveClient
2. **错误处理流程**: Exception → ErrorHandler → RetryHandler → DeadLetterQueue
3. **监控流程**: Event → PerformanceMonitor → Metrics → Alert

### 8.3 性能优化点
1. **连接池**: 复用HTTP连接，提高性能
2. **异步处理**: 使用异步消息处理，提高吞吐量
3. **批量处理**: 支持批量消息处理，减少网络开销
4. **缓存**: 缓存分类映射规则，减少配置读取