# 环境要求 - Python 版本：3.9.6

# HyDocPusher (内容发布数据归档同步服务)

## 📋 项目概览

HyDocPusher是一个基于Python 3.9.6开发的数据同步服务，用于自动化地将内容发布系统的数据归档到第三方电子档案管理系统。

## 🚀 快速开始

### 环境要求

**Python 版本：3.9.6** (精确版本要求)

**系统要求**:
- 操作系统: Linux/MacOS/Windows
- 内存: 最低4GB，推荐8GB
- 磁盘: 最低20GB可用空间
- 网络: 稳定的互联网连接

**依赖软件**:
- Python 3.9.6 (必须精确版本)
- pip 21.0+
- Docker 20.10+ (容器化部署)
- Docker Compose 2.0+ (开发环境)

### 安装步骤

#### 1. 环境准备

**验证Python版本**:
```bash
# 检查Python版本
python --version
# 或
python3 --version

# 必须显示: Python 3.9.6
```

**创建虚拟环境**:
```bash
# 创建虚拟环境
python3.9 -m venv venv

# 激活虚拟环境
# Linux/MacOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# 验证虚拟环境
which python  # 应该显示虚拟环境路径
```

#### 2. 项目安装

**克隆项目**:
```bash
git clone <repository-url>
cd HyDocPusher
```

**安装依赖**:
```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

#### 3. 配置文件

**复制配置模板**:
```bash
# 复制配置文件
cp config/application.yaml.example config/application.yaml
cp config/classification-rules.yaml.example config/classification-rules.yaml

# 编辑配置文件
vim config/application.yaml
```

**环境变量配置**:
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

#### 4. 数据库初始化

**运行数据库迁移**:
```bash
# 如果使用数据库
python -m alembic upgrade head
```

#### 5. 启动服务

**开发环境启动**:
```bash
# 启动开发服务器
python -m hydocpusher.main

# 或使用uvicorn
uvicorn hydocpusher.main:app --reload --host 0.0.0.0 --port 8080
```

**Docker环境启动**:
```bash
# 构建镜像
docker build -t hydocpusher:latest .

# 启动服务
docker-compose up -d
```

### 验证安装

**健康检查**:
```bash
# 检查服务状态
curl http://localhost:8080/health

# 预期响应
{
  "status": "UP",
  "timestamp": "2024-01-01T12:00:00Z",
  "components": {
    "pulsar": "UP",
    "archive": "UP"
  }
}
```

**测试消息处理**:
```bash
# 发送测试消息
python scripts/send-test-message.py
```

## 📁 项目结构

```
HyDocPusher/
├── hydocpusher/                 # 主要代码
│   ├── __init__.py
│   ├── main.py                  # 应用入口
│   ├── config/                  # 配置模块
│   ├── consumer/               # 消息消费
│   ├── transformer/            # 数据转换
│   ├── client/                 # HTTP客户端
│   ├── models/                 # 数据模型
│   ├── exceptions/             # 异常处理
│   ├── utils/                  # 工具类
│   └── services/               # 业务服务
├── tests/                      # 测试代码
├── config/                     # 配置文件
├── scripts/                    # 脚本文件
├── requirements.txt            # 生产依赖
├── requirements-dev.txt        # 开发依赖
├── Dockerfile                  # Docker配置
├── docker-compose.yml          # Docker编排
├── .env                        # 环境变量
├── .gitignore                  # Git忽略
├── pyproject.toml             # 项目配置
└── README.md                   # 项目说明
```

## 🛠️ 开发指南

### 代码规范

**格式化代码**:
```bash
# 格式化代码
black hydocpusher/ tests/

# 检查代码风格
flake8 hydocpusher/ tests/

# 类型检查
mypy hydocpusher/
```

**运行测试**:
```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=hydocpusher --cov-report=html

# 运行特定测试
pytest tests/test_consumer/
```

### 依赖管理

**添加新依赖**:
```bash
# 添加生产依赖
pip install package-name==1.0.0
pip freeze > requirements.txt

# 添加开发依赖
pip install package-name==1.0.0
pip freeze > requirements-dev.txt
```

**依赖版本规则**:
- 必须指定精确版本号 (如 `requests==2.31.0`)
- 禁止使用版本区间 (如 `requests>=2.30.0`)
- 禁止使用模糊版本 (如 `requests~=2.30.0`)

### 日志和调试

**查看日志**:
```bash
# 查看应用日志
tail -f logs/application.log

# 查看错误日志
tail -f logs/error.log

# Docker环境
docker-compose logs -f hydocpusher
```

**调试模式**:
```bash
# 启用调试模式
export LOG_LEVEL=DEBUG
python -m hydocpusher.main
```

## 🔧 配置说明

### 主要配置文件

- `config/application.yaml` - 应用主配置
- `config/classification-rules.yaml` - 分类映射规则
- `config/logging.yaml` - 日志配置
- `.env` - 环境变量

### 关键配置项

```yaml
# Pulsar配置
pulsar:
  cluster:
    url: "pulsar://localhost:6650"
  topic: "persistent://public/default/content-publish"

# 档案系统配置
archive:
  api:
    url: "http://archive-system:8080/news/archive/receive"
    timeout: 30000
```

## 📊 监控和运维

### 健康检查

- `GET /health` - 基础健康检查
- `GET /health/liveness` - 存活探针
- `GET /health/readiness` - 就绪探针
- `GET /metrics` - 性能指标

### 日志管理

- 结构化日志格式
- 按天轮转
- 支持`DEBUG`, `INFO`, `WARNING`, `ERROR`级别

### 性能监控

- 消息处理速度和延迟
- 系统资源使用率
- HTTP调用成功率
- 错误率统计

## 🚨 故障排除

### 常见问题

1. **Python版本不匹配**
   ```bash
   # 确保使用Python 3.9.6
   python3.9 --version
   ```

2. **依赖安装失败**
   ```bash
   # 清理pip缓存
   pip cache purge
   
   # 重新安装
   pip install -r requirements.txt
   ```

3. **Pulsar连接失败**
   ```bash
   # 检查Pulsar服务状态
   docker-compose ps pulsar
   
   # 检查网络连接
   telnet localhost 6650
   ```

### 调试技巧

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG

# 检查配置
python -c "from hydocpusher.config import app_config; print(app_config.dict())"

# 测试数据库连接
python scripts/test-database-connection.py
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目维护者: [姓名] <邮箱>
- 技术支持: [邮箱]
- 问题反馈: [Issues地址]

---

**重要提示**: 本项目必须使用 Python 3.9.6 版本，其他版本可能导致兼容性问题。