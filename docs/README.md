# HyDocPusher 工程文档

## 📋 项目概览

HyDocPusher (内容发布数据归档同步服务) 是一个基于Java J2SE开发的数据同步服务，用于自动化地将内容发布系统的数据归档到第三方电子档案管理系统。

## 📁 文档结构

```
docs/
├── ai-context/                    # AI上下文文档
│   ├── project-structure.md       # 项目结构文档
│   ├── system-integration.md      # 系统集成文档
│   ├── deployment-infrastructure.md # 部署基础设施文档
│   ├── docs-overview.md           # 文档概览
│   └── handoff.md                 # 项目交接文档
├── design/                        # 设计文档
│   ├── component-design.md        # 组件设计文档
│   └── functional-design.md       # 功能设计文档
└── specs/                         # 规格文档 (待创建)
    ├── functional-specs.md        # 功能规格文档
    ├── technical-specs.md         # 技术规格文档
    └── performance-specs.md       # 性能规格文档
```

## 🎯 核心功能

### 1. 消息消费功能
- 连接Pulsar消息队列集群
- 订阅指定Topic消费消息
- 支持JSON格式消息解析
- 健壮的错误处理机制
- 异步消息处理

### 2. 数据转换功能
- 字段映射和转换
- 分类规则配置化映射
- 附件数组动态构建
- 数据验证和格式化
- Pydantic模型验证

### 3. 数据推送功能
- HTTP POST请求发送
- 重试机制和死信队列
- 响应处理和状态记录
- 错误恢复和补偿
- 异步HTTP客户端

### 4. 配置管理功能
- 外部配置文件管理
- 分类规则配置
- 环境配置支持
- 配置验证机制
- Pydantic Settings集成

## 🏗️ 技术架构

### 技术栈
- **语言**: Python 3.9.6
- **依赖管理**: pip + requirements.txt
- **Web框架**: FastAPI
- **数据验证**: Pydantic
- **消息队列**: Apache Pulsar
- **HTTP客户端**: httpx
- **日志框架**: structlog
- **部署方式**: Docker
- **监控**: Prometheus + Grafana

### 核心组件
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   消息消费模块   │    │   数据转换模块   │    │   HTTP客户端模块  │
│                 │    │                 │    │                 │
│ • PulsarConsumer│    │ • DataTransformer│    │ • ArchiveClient │
│ • MessageHandler│    │ • FieldMapper   │    │ • RetryHandler  │
│ • DeadLetterQueue│    │ • AttachmentBuilder│ │ • HttpClient    │
│ • Async Processing│  • Pydantic Models │  • Async HTTP     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 文档使用指南

### 新开发者入门
1. 阅读 [PRD-md](../PRD-md) 了解项目需求
2. 查看 [project-structure.md](./ai-context/project-structure.md) 理解项目架构
3. 参考 [functional-design.md](./design/functional-design.md) 了解功能设计
4. 查看 [component-design.md](./design/component-design.md) 进行开发实现

### 部署和运维
1. 参考 [deployment-infrastructure.md](./ai-context/deployment-infrastructure.md) 进行部署
2. 查看 [system-integration.md](./ai-context/system-integration.md) 了解系统集成
3. 使用 [handoff.md](./ai-context/handoff.md) 进行运维操作

### 测试和验收
1. 查看 [functional-specs.md](./specs/functional-specs.md) 了解功能规格
2. 参考 [technical-specs.md](./specs/technical-specs.md) 了解技术要求
3. 查看 [performance-specs.md](./specs/performance-specs.md) 了解性能标准

## 🚀 快速开始

### 环境要求
- **Python 版本：3.9.6** (必须精确版本)
- pip 21.0+
- Docker 20.10+
- Docker Compose 2.0+

### 本地开发
```bash
# 克隆项目
git clone <repository-url>
cd HyDocPusher

# 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发环境
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f hydocpusher
```

### 构建和测试
```bash
# 运行测试
pytest

# 代码格式化
black hydocpusher/
flake8 hydocpusher/

# 类型检查
mypy hydocpusher/

# 启动应用
python -m hydocpusher.main

# 或使用uvicorn
uvicorn hydocpusher.main:app --reload --host 0.0.0.0 --port 8080
```

## 📊 性能指标

- **处理能力**: ≥100条/秒
- **端到端延迟**: ≤500ms
- **错误率**: ≤1%
- **可用性**: ≥99.9%
- **资源使用**: CPU ≤70%, 内存 ≤80%

## 🔧 配置说明

### 主要配置文件
- `application.yml` - 主配置文件
- `classification-rules.yml` - 分类映射规则
- `logback.xml` - 日志配置

### 关键配置项
```yaml
pulsar:
  cluster:
    url: "pulsar://localhost:6650"
  topic: "persistent://public/default/content-publish"

archive:
  api:
    url: "http://archive-system:8080/news/archive/receive"
    timeout: 30000
```

## 📈 监控和告警

### 监控指标
- 消息处理速度和数量
- 错误率和失败原因
- 系统资源使用情况
- HTTP调用性能

### 健康检查
- `GET /health` - 应用健康状态
- `GET /actuator/health` - 详细健康信息
- `GET /actuator/metrics` - 性能指标

## 🛠️ 运维操作

### 日常操作
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f hydocpusher

# 重启服务
docker-compose restart hydocpusher
```

### 故障排除
- 检查Pulsar连接状态
- 查看死信队列消息
- 分析HTTP调用失败原因
- 监控系统资源使用

## 📞 技术支持

如有问题或需要帮助，请联系：
- 技术负责人: [姓名] <邮箱>
- 开发团队: [邮箱]
- 运维团队: [邮箱]

## 📄 相关文档

- [产品需求文档](../PRD-md)
- [Claude Code上下文](../CLAUDE.md)
- [变更日志](../claude-init/CHANGELOG.md)
- [开源协议](../claude-init/LICENSE)

---

**注意**: 本文档基于Claude Code中文开发套件生成，遵循项目文档规范和最佳实践。