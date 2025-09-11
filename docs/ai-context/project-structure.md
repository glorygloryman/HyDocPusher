# 项目结构文档

## 1. 项目概览

**项目名称**: HyDocPusher (内容发布数据归档同步服务)  
**项目类型**: Python 应用程序  
**开发语言**: Python 3.9.6  
**依赖管理**: requirements.txt  
**部署方式**: Docker 容器化  

## 2. 目录结构

```
HyDocPusher/
├── hydocpusher/
│   ├── __init__.py                              # 包初始化文件
│   ├── main.py                                   # 主程序入口
│   ├── config/                                   # 配置管理
│   │   ├── __init__.py
│   │   ├── app_config.py                         # 应用配置
│   │   ├── pulsar_config.py                      # Pulsar配置
│   │   ├── archive_config.py                    # 档案系统配置
│   │   └── classification_config.py              # 分类映射配置
│   ├── consumer/                                 # 消息消费者
│   │   ├── __init__.py
│   │   ├── pulsar_consumer.py                    # Pulsar消费者
│   │   ├── message_handler.py                    # 消息处理器
│   │   └── dead_letter_queue.py                  # 死信队列
│   ├── transformer/                              # 数据转换器
│   │   ├── __init__.py
│   │   ├── data_transformer.py                   # 数据转换主类
│   │   ├── field_mapper.py                       # 字段映射器
│   │   └── attachment_builder.py                 # 附件构建器
│   ├── client/                                   # HTTP客户端
│   │   ├── __init__.py
│   │   ├── archive_client.py                     # 档案系统客户端
│   │   ├── retry_handler.py                      # 重试处理器
│   │   └── http_client.py                        # HTTP客户端工具
│   ├── models/                                   # 数据模型
│   │   ├── __init__.py
│   │   ├── source_message.py                     # 源消息模型
│   │   ├── archive_request.py                    # 档案请求模型
│   │   ├── archive_response.py                  # 档案响应模型
│   │   └── attachment.py                         # 附件模型
│   ├── exceptions/                               # 异常处理
│   │   ├── __init__.py
│   │   ├── data_transform_exception.py
│   │   ├── archive_client_exception.py
│   │   └── message_consumer_exception.py
│   ├── utils/                                    # 工具类
│   │   ├── __init__.py
│   │   ├── date_utils.py                         # 日期工具
│   │   ├── json_utils.py                         # JSON工具
│   │   ├── url_utils.py                          # URL工具
│   │   └── log_utils.py                          # 日志工具
│   └── services/                                 # 服务层
│       ├── __init__.py
│       ├── archive_service.py                    # 档案服务
│       └── health_check_service.py               # 健康检查服务
├── tests/                                        # 测试文件
│   ├── __init__.py
│   ├── test_consumer/
│   ├── test_transformer/
│   ├── test_client/
│   └── test_services/
├── config/                                       # 配置文件
│   ├── application.yaml                          # 主配置文件
│   ├── classification-rules.yaml                 # 分类映射规则
│   └── logging.yaml                              # 日志配置
├── requirements.txt                              # Python依赖文件
├── setup.py                                      # 安装脚本
├── pyproject.toml                                # 项目配置
├── Dockerfile                                    # Docker镜像配置
├── docker-compose.yml                            # Docker编排配置
├── .env                                          # 环境变量
├── .gitignore                                    # Git忽略文件
├── README.md                                     # 项目说明
├── CLAUDE.md                                     # Claude Code上下文
└── PRD-md                                        # 产品需求文档
├── docs/
│   ├── ai-context/                                  # AI上下文文档
│   │   ├── project-structure.md                     # 项目结构文档
│   │   ├── system-integration.md                    # 系统集成文档
│   │   ├── deployment-infrastructure.md             # 部署基础设施
│   │   ├── docs-overview.md                         # 文档概览
│   │   └── handoff.md                               # 项目交接文档
│   ├── design/                                      # 设计文档
│   │   ├── architecture-design.md                   # 架构设计
│   │   ├── data-flow-design.md                     # 数据流设计
│   │   ├── api-design.md                            # API设计
│   │   └── database-design.md                      # 数据库设计
│   └── specs/                                       # 规格文档
│       ├── functional-specs.md                      # 功能规格
│       ├── technical-specs.md                      # 技术规格
│       └── performance-specs.md                    # 性能规格
├── docker/
│   ├── Dockerfile                                   # Docker镜像配置
│   └── docker-compose.yml                          # Docker编排配置
├── scripts/
│   ├── build.sh                                     # 构建脚本
│   ├── deploy.sh                                    # 部署脚本
│   └── health-check.sh                              # 健康检查脚本
├── config/
│   ├── application.yml                              # 生产环境配置
│   ├── classification-rules.yml                     # 生产环境分类规则
│   └── logback.xml                                  # 生产环境日志配置
├── pom.xml                                          # Maven项目配置
├── README.md                                        # 项目说明
├── CLAUDE.md                                        # Claude Code上下文
└── PRD-md                                           # 产品需求文档
```

## 3. 核心组件说明

### 3.1 配置管理模块 (config/)
- **AppConfig**: 应用主配置类，管理所有配置项
- **PulsarConfig**: Pulsar连接配置，包括集群地址、Topic等
- **ArchiveConfig**: 档案系统配置，包括API地址、认证信息等
- **ClassificationConfig**: 分类映射配置，管理栏目分类规则

### 3.2 消息消费模块 (consumer/)
- **PulsarConsumer**: Pulsar消息消费者，负责连接和消息接收
- **MessageHandler**: 消息处理器，处理接收到的消息
- **DeadLetterQueue**: 死信队列，处理失败消息

### 3.3 数据转换模块 (transformer/)
- **DataTransformer**: 数据转换主类，协调整个转换过程
- **FieldMapper**: 字段映射器，处理字段映射逻辑
- **AttachmentBuilder**: 附件构建器，构建附件数组

### 3.4 HTTP客户端模块 (client/)
- **ArchiveClient**: 档案系统客户端，负责API调用
- **RetryHandler**: 重试处理器，实现重试逻辑
- **HttpClient**: HTTP客户端工具，封装HTTP操作

### 3.5 数据模型 (model/)
- **SourceMessage**: 源消息数据模型
- **ArchiveRequest**: 档案请求数据模型
- **ArchiveResponse**: 档案响应数据模型
- **Attachment**: 附件数据模型

## 4. 技术栈详情

### 4.1 核心技术
- **Python 3.9.6**: 基础开发语言
- **pip + requirements.txt**: 依赖管理
- **Apache Pulsar**: 消息队列中间件
- **FastAPI**: Web框架（用于健康检查和管理接口）
- **Pydantic**: 数据验证和序列化
- **httpx**: HTTP客户端
- **structlog**: 结构化日志框架

### 4.2 开发和测试
- **pytest**: 单元测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-mock**: Mock测试框架
- **pytest-cov**: 代码覆盖率工具
- **black**: 代码格式化
- **flake8**: 代码质量检查

### 4.3 部署和运维
- **Docker**: 容器化部署
- **Docker Compose**: 本地开发环境
- **Prometheus**: 监控指标（可选）
- **Grafana**: 监控面板（可选）
- **uvicorn**: ASGI服务器

## 5. 配置文件说明

### 5.1 application.yml
```yaml
server:
  port: 8080

pulsar:
  cluster:
    url: "pulsar://localhost:6650"
  topic: "persistent://public/default/content-publish"
  subscription: "hydocpusher-subscription"
  dead-letter-topic: "persistent://public/default/hydocpusher-dlq"

archive:
  api:
    url: "http://10.20.162.1:8080/news/archive/receive"
    timeout: 30000
    retry:
      max-attempts: 3
      delay: 60000
  app:
    id: "NEWS"
    token: "TmV3cytJbnRlcmZhY2U="
    company-name: "云南省能源投资集团有限公司"
    type: "17"
    domain: "example.com"
    retention-period: 30

logging:
  level:
    com.hydocpusher: INFO
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
```

### 5.2 classification-rules.yml
```yaml
classification_rules:
  - channel_id: "2240"
    classfyname: "新闻头条"
    classfy: "XWTT"
  - channel_id: "2241"
    classfyname: "集团要闻"
    classfy: "JTYW"
  - default:
      classfyname: "其他"
      classfy: "QT"
```

## 6. 构建和部署

### 6.1 本地开发
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest

# 启动应用
python -m hydocpusher.main

# 代码格式化
black hydocpusher/
flake8 hydocpusher/
```

### 6.2 生产部署
```bash
# 构建Docker镜像
docker build -t hydocpusher:latest .

# 运行容器
docker run -d --name hydocpusher \
  -v /path/to/config:/app/config \
  -p 8080:8080 \
  hydocpusher:latest

# 使用docker-compose
docker-compose up -d
```

## 7. 监控和运维

### 7.1 健康检查
- 应用提供 `/health` 端点用于健康检查
- 监控消息消费和处理状态
- 监控HTTP调用成功率和响应时间

### 7.2 日志管理
- 使用结构化日志格式
- 按天轮转日志文件
- 保留30天日志历史

### 7.3 性能监控
- 监控消息处理速度和延迟
- 监控系统资源使用情况
- 设置告警阈值