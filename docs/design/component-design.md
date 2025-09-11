# 组件设计文档

## 1. 组件概览

HyDocPusher采用模块化设计，包含以下核心组件：

### 1.1 核心组件架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   消息消费模块   │    │   数据转换模块   │    │   HTTP客户端模块  │
│  Message Consumer│───▶│ Data Transformer│───▶│ Archive Client  │
│                 │    │                 │    │                 │
│ • PulsarConsumer│    │ • FieldMapper   │    │ • ArchiveClient │
│ • MessageHandler│    │ • AttachmentBuilder│ │ • RetryHandler  │
│ • DeadLetterQueue│    │                 │    │ • HttpClient    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   配置管理模块   │    │   数据模型模块   │    │   异常处理模块   │
│  Config Manager │    │  Data Models    │    │ Exception Handler│
│                 │    │                 │    │                 │
│ • AppConfig     │    │ • SourceMessage │    │ • DataTransform │
│ • PulsarConfig  │    │ • ArchiveRequest│    │ • ArchiveClient │
│ • ArchiveConfig │    │ • ArchiveResponse│    │ • MessageConsumer│
│ • Classification│    │ • Attachment     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 2. 消息消费模块设计

### 2.1 PulsarConsumer 组件

**职责**: 负责连接Pulsar集群，订阅Topic，接收消息

**核心方法**:
```python
class PulsarConsumer:
    def __init__(self, config: PulsarConfig):
        self.client = None
        self.consumer = None
        self.config = config
        self.message_handler = None
    
    async def start(self):                           # 启动消费者
        pass
    
    async def stop(self):                            # 停止消费者
        pass
    
    def set_message_handler(self, handler):          # 设置消息处理器
        self.message_handler = handler
    
    async def setup_consumer(self):                  # 设置消费者配置
        pass
    
    async def handle_message(self, message: str):   # 处理接收到的消息
        pass
```

**配置项**:
- `pulsar.cluster.url`: Pulsar集群地址
- `pulsar.topic`: 订阅的Topic
- `pulsar.subscription`: 订阅名称
- `pulsar.dead-letter-topic`: 死信队列Topic

**异常处理**:
- 连接失败时自动重试
- 消息解析失败时发送到死信队列
- 网络异常时记录日志并继续运行

### 2.2 MessageHandler 组件

**职责**: 处理接收到的消息，协调数据转换和推送流程

**核心方法**:
```python
class MessageHandler:
    def __init__(self, transformer: DataTransformer, 
                 archive_client: ArchiveClient,
                 dlq: DeadLetterQueue):
        self.transformer = transformer
        self.archive_client = archive_client
        self.dlq = dlq
    
    async def handle(self, raw_message: str):      # 处理消息主入口
        pass
    
    def parse_message(self, raw_message: str) -> SourceMessage:  # 解析消息
        pass
    
    def transform_data(self, source: SourceMessage) -> ArchiveRequest:  # 转换数据
        pass
    
    async def send_to_archive(self, request: ArchiveRequest):  # 发送到档案系统
        pass
    
    def handle_error(self, error: Exception, message_id: str):  # 错误处理
        pass
```

**处理流程**:
1. 解析原始JSON消息
2. 验证消息格式完整性
3. 调用数据转换器
4. 调用档案系统客户端
5. 处理成功/失败结果

### 2.3 DeadLetterQueue 组件

**职责**: 处理失败的消息，支持后续手动补偿

**核心方法**:
```python
class DeadLetterQueue:
    def __init__(self, config: PulsarConfig):
        self.dlq_producer = None
        self.config = config
    
    async def send_to_dlq(self, message: str, error: Exception):  # 发送到死信队列
        pass
    
    async def get_failed_messages(self) -> List[DlqMessage]:  # 获取失败消息
        pass
    
    async def retry_message(self, message_id: str) -> bool:   # 重试特定消息
        pass
    
    async def setup_dlq_producer(self):                     # 设置死信队列生产者
        pass
```

## 3. 数据转换模块设计

### 3.1 DataTransformer 组件

**职责**: 协调整个数据转换过程，管理转换规则

**核心方法**:
```python
class DataTransformer:
    def __init__(self, field_mapper: FieldMapper,
                 attachment_builder: AttachmentBuilder,
                 classification_config: ClassificationConfig):
        self.field_mapper = field_mapper
        self.attachment_builder = attachment_builder
        self.classification_config = classification_config
    
    def transform(self, source: SourceMessage) -> ArchiveRequest:  # 主转换方法
        pass
    
    def build_archive_data(self, source: SourceMessage) -> ArchiveData:  # 构建ArchiveData
        pass
    
    def map_classification(self, channel_id: str) -> str:   # 映射分类
        pass
    
    def validate_required_fields(self, source: SourceMessage):  # 验证必填字段
        pass
```

**转换规则**:
- 顶层字段直接从配置读取
- ArchiveData字段根据映射规则转换
- 附件数组动态构建
- 分类字段根据配置映射

### 3.2 FieldMapper 组件

**职责**: 处理字段映射逻辑，支持复杂的字段转换

**核心方法**:
```java
public class FieldMapper {
    private AppConfig appConfig;
    
    public ArchiveRequest mapFields(SourceMessage source); // 字段映射主方法
    private String mapDid(SourceMessage source);           // 映射did字段
    private String mapTitle(SourceMessage source);         // 映射title字段
    private String mapDocDate(SourceMessage source);       // 映射docdate字段
    private String mapYear(SourceMessage source);           // 映射year字段
    private String mapDepartment(SourceMessage source);    // 映射部门字段
}
```

**字段映射表**:

| 目标字段 | 源字段路径 | 转换规则 |
|---------|-----------|----------|
| did | DATA.DATA.RECID | 直接映射 |
| wzmc | DATA.DATA.SITENAME | 直接映射 |
| title | DATA.DATA.DOCTITLE | 直接映射 |
| author | DATA.DATA.TXY | 直接映射 |
| docdate | DATA.DATA.DOCRELTIME | 格式化为YYYY-MM-DD |
| year | DATA.DATA.DOCRELTIME | 提取年份部分 |
| fillingdepartment | DATA.CHNLDOC.CRDEPT | 直接映射 |
| bly | DATA.DATA.CRUSER | 直接映射 |

### 3.3 AttachmentBuilder 组件

**职责**: 构建附件数组，处理多种附件字段和地址转换

**核心方法**:
```python
class AttachmentBuilder:
    def __init__(self, domain_config: str = "www.cnyeig.com"):
        self.domain_config = domain_config
    
    def build_attachments(self, source_message: SourceMessage) -> List[AttachmentData]:  # 构建附件列表
        pass
    
    def _extract_html_attachments(self, html_content: str) -> List[str]:  # 从HTML中提取附件地址
        pass
    
    def _parse_json_attachments(self, json_content: str) -> List[Dict]:  # 解析JSON格式附件
        pass
    
    def _convert_w_suffix_address(self, address: str) -> str:  # 转换W后缀图片地址
        pass
    
    def _build_absolute_url(self, relative_path: str) -> str:  # 构建绝对地址
        pass
    
    def _extract_file_extension(self, url: str) -> str:  # 提取文件扩展名
        pass
    
    def _determine_attachment_type(self, url: str) -> str:  # 确定附件类型
        pass
```

**附件处理规则**:
- **域名配置**: 默认使用 www.cnyeig.com，可配置
- **支持字段**: DOCHTMLCON, DOCUMENT_RELATED_VIDEO, DOCUMENT_CONTENT_VIDEO, DOCUMENT_RELATED_PIC, Appdix
- **HTML解析**: 从DOCHTMLCON中提取 <a>, <iframe>, <img> 标签的地址
- **JSON解析**: 解析JSON结构 [{"APPDESC":"描述","APPURL":"地址","APPENDIXID":ID}]
- **地址转换**: W后缀图片地址特殊处理，其他地址前缀域名
- **绝对地址**: /a/b/c/aaa.mp4 → http://www.cnyeig.com/a/b/c/aaa.mp4

## 4. HTTP客户端模块设计

### 4.1 ArchiveClient 组件

**职责**: 与档案系统API交互，处理HTTP请求和响应

**核心方法**:
```java
public class ArchiveClient {
    private HttpClient httpClient;
    private RetryHandler retryHandler;
    private ArchiveConfig config;
    
    public ArchiveResponse sendArchiveRequest(ArchiveRequest request); // 发送归档请求
    private HttpResponse executeHttpRequest(ArchiveRequest request);   // 执行HTTP请求
    private ArchiveResponse parseResponse(HttpResponse response);      // 解析响应
    private boolean isSuccessResponse(ArchiveResponse response);      // 判断是否成功
}
```

**API接口规范**:
- **URL**: `http://10.20.162.1:8080/news/archive/receive`
- **Method**: POST
- **Content-Type**: application/json
- **Timeout**: 30秒
- **重试**: 失败后重试3次，间隔1分钟

### 4.2 RetryHandler 组件

**职责**: 实现重试逻辑，处理网络异常和服务器错误

**核心方法**:
```java
public class RetryHandler {
    private int maxAttempts;
    private long delay;
    
    public <T> T executeWithRetry(Callable<T> callable);      // 带重试的执行
    private boolean shouldRetry(Exception e);                  // 判断是否需要重试
    private void waitForNextAttempt(int attempt);             // 等待下次重试
    private void logRetryAttempt(Exception e, int attempt);    // 记录重试日志
}
```

**重试策略**:
- 网络超时：重试
- 5xx服务器错误：重试
- 4xx客户端错误：不重试
- 最多重试3次
- 重试间隔：1分钟

### 4.3 HttpClient 组件

**职责**: 封装HTTP操作，提供统一的HTTP客户端接口

**核心方法**:
```java
public class HttpClient {
    private OkHttpClient client;
    
    public HttpResponse post(String url, String body);         // POST请求
    public HttpResponse get(String url);                       // GET请求
    private void setupClient();                                // 设置客户端
    private Headers buildHeaders();                            // 构建请求头
    private String serializeRequest(Object request);          // 序列化请求
}
```

## 5. 配置管理模块设计

### 5.1 AppConfig 组件

**职责**: 管理应用主配置，提供配置访问接口

**核心方法**:
```python
@dataclass
class AppConfig:
    app_id: str
    app_token: str
    company_name: str
    archive_type: str
    domain: str = "www.cnyeig.com"  # 新增域名配置
    retention_period: int = 30
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """从环境变量加载配置"""
        return cls(
            app_id=os.getenv('ARCHIVE_APP_ID'),
            app_token=os.getenv('ARCHIVE_APP_TOKEN'),
            company_name=os.getenv('ARCHIVE_COMPANY_NAME'),
            archive_type=os.getenv('ARCHIVE_TYPE'),
            domain=os.getenv('DOMAIN', 'www.cnyeig.com'),
            retention_period=int(os.getenv('RETENTION_PERIOD', '30'))
        )
```

**新增配置项**:
- `domain`: 系统域名配置，用于构建附件绝对地址，默认为 www.cnyeig.com
```

### 5.2 ClassificationConfig 组件

**职责**: 管理分类映射规则，提供分类查询功能

**核心方法**:
```java
@ConfigurationProperties(prefix = "classification")
public class ClassificationConfig {
    private List<ClassificationRule> rules;
    
    public ClassificationRule findRule(String channelId);     // 查找分类规则
    public ClassificationRule getDefaultRule();                // 获取默认规则
    public String mapClassfyName(String channelId);            // 映射分类名称
    public String mapClassfy(String channelId);                // 映射分类代码
}

public class ClassificationRule {
    private String channelId;
    private String classfyname;
    private String classfy;
}
```

## 6. 数据模型设计

### 6.1 SourceMessage 模型

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Appendix(BaseModel):
    appfile: str = Field(..., alias="APPFILE")

class AttachmentItem(BaseModel):
    """JSON格式附件项模型"""
    appdesc: str = Field(..., alias="APPDESC")
    appurl: str = Field(..., alias="APPURL")
    appendixid: int = Field(..., alias="APPENDIXID")

class ChannelDoc(BaseModel):
    crdept: str = Field(..., alias="CRDEPT")

class DataData(BaseModel):
    recid: str = Field(..., alias="RECID")
    sitename: str = Field(..., alias="SITENAME")
    doctitle: str = Field(..., alias="DOCTITLE")
    txy: str = Field(..., alias="TXY")
    docreltime: str = Field(..., alias="DOCRELTIME")
    docpuburl: str = Field(..., alias="DOCPUBURL")
    cruser: str = Field(..., alias="CRUSER")
    webhttp: str = Field(..., alias="WEBHTTP")
    # 新增附件相关字段
    dochtmlcon: Optional[str] = Field(None, alias="DOCHTMLCON")  # HTML内容
    document_related_video: Optional[str] = Field(None, alias="DOCUMENT_RELATED_VIDEO")  # 相关视频JSON
    document_content_video: Optional[str] = Field(None, alias="DOCUMENT_CONTENT_VIDEO")  # 内容视频JSON
    document_related_pic: Optional[str] = Field(None, alias="DOCUMENT_RELATED_PIC")  # 相关图片JSON

class DataContainer(BaseModel):
    data: DataData = Field(..., alias="DATA")
    chnldoc: ChannelDoc = Field(..., alias="CHNLDOC")
    appendix: List[Appendix] = Field([], alias="APPENDIX")  # 原有附件字段
    appdix: Optional[List[Appendix]] = Field([], alias="Appdix")  # 新增Appdix字段

class SourceMessage(BaseModel):
    data: DataContainer = Field(..., alias="DATA")
    
    class Config:
        populate_by_name = True
```

### 6.2 ArchiveRequest 模型

```python
class Attachment(BaseModel):
    name: str
    ext: str
    file: str
    type: str

class ArchiveData(BaseModel):
    did: str
    wzmc: str
    dn: str
    classfyname: str
    classfy: str
    title: str
    author: str
    docdate: str
    year: str
    retentionperiod: int
    fillingdepartment: str
    bly: str
    attachment: List[Attachment]

class ArchiveRequest(BaseModel):
    app_id: str = Field(..., alias="AppId")
    app_token: str = Field(..., alias="AppToken")
    company_name: str = Field(..., alias="CompanyName")
    archive_type: str = Field(..., alias="ArchiveType")
    archive_data: ArchiveData = Field(..., alias="ArchiveData")
    
    class Config:
        populate_by_name = True
```

## 7. 异常处理设计

### 7.1 异常体系
```
Exception
├── DataTransformException
│   ├── MessageParseException
│   ├── FieldMappingException
│   └── ValidationException
├── ArchiveClientException
│   ├── NetworkException
│   ├── ApiException
│   └── TimeoutException
└── MessageConsumerException
    ├── ConnectionException
    └── SubscriptionException
```

**Python异常类定义**:
```python
class DataTransformException(Exception):
    """数据转换异常基类"""
    pass

class MessageParseException(DataTransformException):
    """消息解析异常"""
    pass

class FieldMappingException(DataTransformException):
    """字段映射异常"""
    pass

class ValidationException(DataTransformException):
    """数据验证异常"""
    pass

class ArchiveClientException(Exception):
    """档案系统客户端异常基类"""
    pass

class NetworkException(ArchiveClientException):
    """网络异常"""
    pass

class ApiException(ArchiveClientException):
    """API异常"""
    pass

class TimeoutException(ArchiveClientException):
    """超时异常"""
    pass

class MessageConsumerException(Exception):
    """消息消费者异常基类"""
    pass

class ConnectionException(MessageConsumerException):
    """连接异常"""
    pass

class SubscriptionException(MessageConsumerException):
    """订阅异常"""
    pass
```

### 7.2 异常处理策略
- **消息解析失败**: 记录错误日志，发送到死信队列
- **字段映射失败**: 抛出DataTransformException，终止处理
- **HTTP调用失败**: 根据重试策略处理，最终失败发送到死信队列
- **配置错误**: 启动时验证，失败时终止应用

## 8. 组件交互流程

### 8.1 消息处理流程
1. **PulsarConsumer** 接收消息
2. **MessageHandler** 解析消息
3. **DataTransformer** 转换数据
4. **ArchiveClient** 发送HTTP请求
5. **DeadLetterQueue** 处理失败消息

### 8.2 数据转换流程
1. **FieldMapper** 映射基础字段
2. **AttachmentBuilder** 构建附件数组
3. **ClassificationConfig** 映射分类字段
4. **DataTransformer** 组装最终请求

### 8.3 错误处理流程
1. 各组件捕获特定异常
2. 记录详细错误日志
3. 根据异常类型决定重试或终止
4. 失败消息发送到死信队列