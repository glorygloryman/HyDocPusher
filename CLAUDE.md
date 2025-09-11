# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 1. 项目概览

- **愿景：**
当前，业务系统在内容发布成功后，需要按照档案管理规范，将发布的内容元数据及原文附件信息归档至第三方电子档案管理系统。为实现此流程的自动化、解耦和高可靠性，避免手动归档或批处理带来的延迟和错漏，我们计划开发一个数据同步服务，实时处理内容发布数据并完成归档。

**HyDocPusher** (内容发布数据归档同步服务) 开发目标：
  * **自动化归档**：自动消费内容发布系统的消息，无需人工干预。
  * **数据标准化**：将源系统数据结构转换为符合电子档案管理系统要求的标准结构。
  * **系统解耦**：通过消息队列作为中间件，降低内容发布系统与档案系统的直接耦合。
  * **可靠同步**：确保数据能够被准确、可靠地推送至目标系统，并具备错误记录能力。

- **当前阶段：**
初始开发阶段 - 已有完整的文档和配置，但尚未实现源代码。

- **核心架构：**
项目统一采用 **Python 3.9.6 (精确版本要求) + FastAPI** 技术栈，所有开发工作需严格基于此组合展开，不允许擅自引入其他核心框架。

服务遵循**三阶段异步管道**架构：
```
Pulsar Message Consumption → Data Transformation → HTTP Archive Push
```

- **开发策略：**
开发环境：必须基于虚拟环境开发，支持 venv（Python 内置）或 conda（第三方工具），禁止直接使用本机全局 Python 环境，避免依赖遗漏或版本冲突。

示例（venv 创建命令）：
```bash
python3.9 -m venv venv  # 创建虚拟环境
source venv/bin/activate  # Linux/Mac 激活
# 或 venv\Scripts\activate  # Windows 激活
```

## 2. 项目结构

**⚠️ 重要：AI 智能体在执行任何任务前，必须先阅读[项目结构文档](/docs/ai-context/project-structure.md)，了解完整的技术栈、文件树和项目组织方式。**

HyDocPusher 遵循模块化异步架构模式。完整的技术栈和文件树结构，请参见 <mcfile name="project-structure.md" path="/docs/ai-context/project-structure.md"></mcfile>。

### 核心组件架构（待实现）

```
hydocpusher/
├── __init__.py
├── main.py                 # 应用程序入口点
├── config/
│   ├── __init__.py
│   ├── settings.py         # Pydantic 设置
│   └── models.py           # 配置模型
├── consumer/
│   ├── __init__.py
│   ├── pulsar_consumer.py  # PulsarConsumer: 处理 Pulsar 连接和消息订阅
│   ├── message_handler.py  # MessageHandler: 处理传入消息和验证
│   └── dead_letter_queue.py # DeadLetterQueue: 管理失败消息处理
├── transformer/
│   ├── __init__.py
│   ├── data_transformer.py # DataTransformer: 转换源 JSON 为档案系统格式
│   ├── field_mapper.py     # FieldMapper: 处理字段映射和转换规则
│   └── attachment_builder.py # AttachmentBuilder: 从各种源构建附件数组
├── client/
│   ├── __init__.py
│   ├── archive_client.py   # ArchiveClient: 处理与档案系统的 HTTP 通信
│   ├── retry_handler.py    # RetryHandler: 实现指数退避重试逻辑
│   └── circuit_breaker.py  # CircuitBreaker: 防止级联故障
├── models/
│   ├── __init__.py
│   ├── message_models.py   # 消息的 Pydantic 模型
│   └── archive_models.py   # 档案 API 的 Pydantic 模型
├── exceptions/
│   ├── __init__.py
│   └── custom_exceptions.py
├── utils/
│   ├── __init__.py
│   ├── logging_config.py
│   └── helpers.py
└── services/
    ├── __init__.py
    └── monitoring.py       # 指标和健康检查
```

## 3. 编码规范与 AI 指令

### 通用指令
- 你最重要的工作是管理自己的上下文。在规划变更前，务必先阅读相关文件。
- 更新文档时，保持更新简洁明了，防止内容冗余。
- 编写代码遵循 KISS、YAGNI 和 DRY 原则。
- 有疑问时遵循经过验证的最佳实践。
- 未经用户批准不要提交到 git。
- 不要运行任何服务器，而是告诉用户运行服务器进行测试。
- 优先考虑行业标准库/框架，而不是自定义实现。
- 永远不要模拟任何东西。永远不要使用占位符。永远不要省略代码。
- 相关时应用 SOLID 原则。使用现代框架特性而不是重新发明解决方案。
- 对想法的好坏要坦率诚实。
- 让副作用明确且最小化。
- 设计数据库模式要便于演进（避免破坏性变更）。

### 文件组织与模块化
- 默认创建多个小而专注的文件，而不是大而单一的文件
- 每个文件应该有单一职责和明确目的
- 尽可能保持文件在 350 行以内 - 通过提取工具、常量、类型或逻辑组件到单独模块来拆分大文件
- 分离关注点：工具、常量、类型、组件和业务逻辑到不同文件
- 优先组合而非继承 - 只在真正的 'is-a' 关系中使用继承，在 'has-a' 或行为混合时优先组合
- 遵循现有项目结构和约定 - 将文件放在适当目录。必要时创建新目录并移动文件。
- 使用定义明确的子目录保持组织和可扩展性
- 用清晰的文件夹层次和一致的命名约定构建项目
- 正确导入/导出 - 为可重用性和可维护性而设计

### 类型提示（必需）
- **始终**为函数参数和返回值使用类型提示
- 对复杂类型使用 `from typing import`
- 优先使用 `Optional[T]` 而不是 `Union[T, None]`
- 对数据结构使用 Pydantic 模型
- 启用严格的 mypy 检查
- 在启动时验证配置
- 使用字段别名进行 JSON 映射

```python
# 良好示例
from typing import Optional, List, Dict, Tuple
from pydantic import BaseModel, Field

class MessageSchema(BaseModel):
    doc_id: str = Field(alias="DOCID")
    title: str = Field(alias="DOCTITLE")
    content: Optional[str] = Field(default=None, alias="DOCCONTENT")

async def process_message(
    message_data: MessageSchema,
    session_id: str,
    retry_count: Optional[int] = None
) -> Tuple[bool, Dict[str, Any]]:
    """处理来自 Pulsar 的消息。
    
    Args:
        message_data: 验证过的消息数据
        session_id: 会话标识符
        retry_count: 重试次数（可选）
    
    Returns:
        处理结果元组（成功标志，响应数据）
    
    Raises:
        ValidationError: 如果消息数据无效
        ProcessingError: 如果处理失败
    """
    pass
```

### 命名约定
- **类**：PascalCase（例如 `PulsarConsumer`、`DataTransformer`）
- **函数/方法**：snake_case（例如 `process_message`、`transform_data`）
- **常量**：UPPER_SNAKE_CASE（例如 `MAX_RETRY_COUNT`、`DEFAULT_TIMEOUT`）
- **私有方法**：前导下划线（例如 `_validate_input`、`_build_attachment`）
- **Pydantic 模型**：PascalCase 带 `Schema` 后缀（例如 `MessageSchema`、`ArchiveRequestSchema`）

### 文档要求
- 每个模块需要文档字符串
- 每个公共函数需要文档字符串
- 使用 Google 风格的文档字符串
- 在文档字符串中包含类型信息

```python
def transform_message_data(source_data: Dict[str, Any], mapping_rules: Dict[str, str]) -> Dict[str, Any]:
    """将源消息数据转换为档案系统格式。

    Args:
        source_data: 来自 Pulsar 的原始消息数据
        mapping_rules: 字段映射规则配置

    Returns:
        转换后的档案系统格式数据

    Raises:
        ValidationError: 如果源数据格式无效
        MappingError: 如果字段映射失败
    """
    pass
```

### 异步编程模式
- 对所有 I/O 操作使用 `async/await`
- 利用 `asyncio` 进行并发处理
- 使用 `httpx` 进行异步 HTTP 请求
- 使用 try/except 块实现适当的错误处理

### 安全优先
- 永远不要信任外部输入 - 在边界处验证一切
- 将秘钥保存在环境变量中，永远不要在代码中
- 记录安全事件（登录尝试、认证失败、速率限制、权限拒绝），但永远不要记录敏感数据（消息内容、令牌、个人信息）
- 在 API 网关级别认证用户 - 永远不要信任客户端令牌
- 在存储或处理前清理所有用户输入
- 使用 HTTPS 进行所有外部通信
- 定期使用 `safety` 进行依赖安全扫描

### 错误处理策略
1. **消息处理**：记录错误，继续处理下一条消息
2. **数据转换**：验证必需字段，为可选字段提供默认值
3. **HTTP 操作**：实现指数退避重试逻辑
4. **系统错误**：优雅降级，全面记录

- 使用具体异常而不是泛型异常
- 始终记录带上下文的错误
- 提供有用的错误消息
- 安全地失败 - 错误不应该暴露系统内部

### 可观测系统与日志标准
- 每个请求都需要关联 ID 用于调试
- 为机器而不是人类构建日志 - 使用 JSON 格式，带一致字段（时间戳、级别、关联 ID、事件、上下文）用于自动化分析
- 使跨服务边界的调试成为可能
- 使用 `structlog` 进行结构化日志记录
- 在适当级别记录（DEBUG、INFO、WARNING、ERROR）
- 在日志消息中包含上下文信息

### 状态管理
- 每个状态片段有一个真相来源
- 让状态变更明确且可追踪
- 为多服务消息处理而设计 - 使用会话 ID 进行状态协调，避免在服务器内存中存储消息数据
- 保持处理历史轻量（元数据，不是完整消息）

### API 设计原则
- 带一致 URL 模式的 RESTful 设计
- 正确使用 HTTP 状态码
- 从第一天就版本化 API（/v1/、/v2/）
- 为列表端点支持分页
- 使用一致的 JSON 响应格式：
  - 成功：`{ "data": {...}, "error": null }`
  - 错误：`{ "data": null, "error": {"message": "...", "code": "..."} }`

## 4. 数据流架构

### 输入消息格式（来自 Pulsar）
```json
{
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
			"DEFAULTRELDOCS": "{\"DATA\":[],\"COUNT\":0}",
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
			"DOCTITLE": "裸眼3D看云能",
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
```

### 输出格式（档案系统）
```json
{
  "AppId": "NEWS",
  "AppToken": "TmV3cytJbnRlcmZhY2U=",
  "CompanyName": "云南省能源投资集团有限公司",
  "ArchiveType": "17",
  "ArchiveData": {
    "did": "84085",
    "wzmc": "测试推送",
    "dn": "www.cnyeig.com",
    "classfyname": "新闻头条",
    "classfy": "XWTT",
    "title": "裸眼3D看云能",
    "author": "集团党群部",
    "docdate": "2025-04-09",
    "year": "2025",
    "retentionperiod": 30,
    "fillingdepartment": "云南省能源投资集团有限公司~云南能投信息产业开发有限公司~",
    "bly": "dev",
    "attachment": [
      {
        "name": "裸眼3D看云能(正文)",
        "ext": "html",
        "file": "https://www.cnyeig.com/csts/test_2240/202508/t20250829_64941.html",
        "type": "正文"
      }
    ]
  }
}
```

## 5. 配置管理

### 配置文件
- `config/application.yaml` - 主应用程序配置
- `config/classification-rules.yaml` - 频道到类别映射
- `.env` - 环境变量和秘钥

### 关键配置区域
```yaml
# Pulsar 连接
pulsar:
  cluster:
    url: "pulsar://localhost:6650"
  topic: "persistent://public/default/content-publish"
  subscription: "hydocpusher-subscription"

# 档案系统集成
archive:
  api:
    url: "http://archive-system:8080/news/archive/receive"
    timeout: 30000
    auth:
      type: "bearer"
      token: "${ARCHIVE_API_TOKEN}"

# 业务配置
business:
  domain: "example.com"
  retention_period: 30
  company_name: "云南省能源投资集团有限公司"
```

## 6. 多智能体工作流与上下文注入

### 子智能体的自动上下文注入
当使用 Task 工具生成子智能体时，核心项目上下文（CLAUDE.md、project-structure.md、docs-overview.md）会通过 subagent-context-injector hook 自动注入到它们的提示中。这确保所有子智能体都能立即访问基本项目文档，无需在每个 Task 提示中手动指定。

## 7. 开发命令

### 环境设置
```bash
# 创建并激活虚拟环境
python3.9 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 开发服务器
```bash
# 启动开发服务器
python -m hydocpusher.main

# 或使用 uvicorn（用于 FastAPI）
uvicorn hydocpusher.main:app --reload --host 0.0.0.0 --port 8080
```

### 测试
```bash
# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov=hydocpusher --cov-report=html

# 运行特定测试类别
pytest -m unit      # 仅单元测试
pytest -m integration  # 仅集成测试
```

### 代码质量
```bash
# 格式化代码
black hydocpusher/ tests/

# 排序导入
isort hydocpusher/ tests/

# 代码检查
flake8 hydocpusher/ tests/

# 类型检查
mypy hydocpusher/

# 安全扫描
bandit -r hydocpusher/

# 依赖安全检查
safety check
```

## 8. 性能要求

- **吞吐量**：≥100 消息/秒
- **延迟**：≤500ms 端到端
- **错误率**：≤1%
- **可用性**：≥99.9%
- **资源使用**：CPU ≤70%，内存 ≤80%

## 9. 监控和可观测性

### 健康检查
- `GET /health` - 基本健康状态
- `GET /health/liveness` - Kubernetes 存活探针
- `GET /health/readiness` - Kubernetes 就绪探针
- `GET /metrics` - Prometheus 指标

### 关键指标
- 消息处理速率和延迟
- HTTP 请求成功/失败率
- 系统资源利用率
- 死信队列大小

## 10. 任务完成后协议

完成任何编码任务后，遵循此检查清单：

### 1. 类型安全与质量检查
根据修改内容运行适当命令：
- **Python 项目**：运行 mypy 类型检查
- **其他语言**：运行适当的代码检查/类型检查工具

### 2. 验证
- 确保所有类型检查通过后再认为任务完成
- 如果发现类型错误，在标记任务完成前修复它们

### 3. 测试策略

#### 测试结构
```
tests/
├── unit/                    # 单元测试
│   ├── test_consumer.py
│   ├── test_transformer.py
│   └── test_client.py
├── integration/             # 集成测试
│   ├── test_pulsar_integration.py
│   └── test_archive_integration.py
├── fixtures/               # 测试夹具和模拟
└── conftest.py             # 测试配置
```

#### 测试模式
- 使用 `pytest-asyncio` 进行异步测试支持
- 模拟外部依赖（Pulsar、档案 API）
- 使用 `pytest-httpx` 进行 HTTP 客户端测试
- 为数据转换实现基于属性的测试

## 重要指令提醒

按要求做；不多不少。
除非绝对必要以实现目标，否则永远不要创建文件。
始终优先编辑现有文件而不是创建新文件。
除非用户明确要求，否则永远不要主动创建文档文件（*.md）或 README 文件。只有在用户明确要求时才创建文档文件。

## 常见开发模式

### 创建新组件
1. 为数据结构定义 Pydantic 模型
2. 为 I/O 操作实现异步方法
3. 添加全面的类型提示
4. 包含适当的错误处理
5. 为所有功能编写单元测试

### 添加新依赖
1. 将确切版本添加到 requirements.txt 或 requirements-dev.txt
2. 如需要更新 pyproject.toml
3. 使用 `safety` 运行安全检查
4. 在开发环境中测试

### 配置更改
1. 更新 Pydantic 设置模型
2. 修改配置文件
3. 更新文档
4. 测试配置验证