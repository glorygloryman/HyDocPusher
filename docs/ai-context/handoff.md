# 项目交接文档

## 1. 交接概览

**项目名称**: HyDocPusher (内容发布数据归档同步服务)  
**项目版本**: 1.0.0  
**交接日期**: 2024-01-01  
**交接人员**: 开发团队 → 运维团队  

## 2. 项目状态

### 2.1 当前状态

- **开发状态**: ✅ 开发完成，待部署
- **测试状态**: ✅ 单元测试通过，集成测试完成
- **文档状态**: ✅ 文档完整，已更新
- **部署状态**: ⏳ 待生产部署
- **监控状态**: ⏳ 监控系统待配置

### 2.2 已完成功能

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 消息消费功能 | ✅ 完成 | Pulsar消息接收和处理 |
| 数据转换功能 | ✅ 完成 | 字段映射和分类转换 |
| HTTP推送功能 | ✅ 完成 | 档案系统API调用 |
| 重试机制 | ✅ 完成 | 失败重试和死信队列 |
| 配置管理 | ✅ 完成 | 外部配置文件管理 |
| 日志记录 | ✅ 完成 | 结构化日志记录 |
| 健康检查 | ✅ 完成 | 应用健康状态监控 |
| 性能监控 | ✅ 完成 | 关键性能指标收集 |

### 2.3 已知问题

| 问题描述 | 优先级 | 影响范围 | 解决方案 |
|---------|--------|----------|----------|
| 大附件处理性能 | 中 | 附件处理速度 | 后续优化 |
| 内存使用优化 | 低 | 长期运行稳定性 | 监控观察 |
| 配置热更新 | 低 | 运维便利性 | 后续版本实现 |

## 3. 系统架构

### 3.1 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   内容发布系统   │    │   HyDocPusher    │    │   电子档案系统   │
│                 │    │                 │    │                 │
│ • 消息生成      │───▶│ • 消息消费      │───▶│ • 归档接收      │
│ • 格式标准化    │    │ • 数据转换      │    │ • 状态返回      │
│                 │    │ • HTTP推送      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3.2 核心组件

| 组件名称 | 功能描述 | 技术实现 |
|---------|----------|----------|
| PulsarConsumer | Pulsar消息消费者 | Apache Pulsar Client |
| DataTransformer | 数据转换器 | 自定义映射引擎 |
| ArchiveClient | 档案系统客户端 | OkHttp + Spring RestTemplate |
| RetryHandler | 重试处理器 | 自定义重试策略 |
| DeadLetterQueue | 死信队列 | Pulsar DLQ机制 |
| ConfigManager | 配置管理器 | Spring Configuration |

## 4. 部署信息

### 4.1 部署环境

| 环境名称 | 地址 | 用途 | 状态 |
|---------|------|------|------|
| 开发环境 | dev.example.com | 开发和测试 | ✅ 运行中 |
| 测试环境 | test.example.com | 集成测试 | ✅ 运行中 |
| 生产环境 | prod.example.com | 生产运行 | ⏳ 待部署 |

### 4.2 部署配置

**Docker镜像**:
- 镜像名称: `hydocpusher:1.0.0`
- 镜像大小: ~200MB
- 基础镜像: `openjdk:11-jre-slim`

**资源要求**:
- CPU: 500m - 1000m
- 内存: 1Gi - 2Gi
- 存储: 10Gi (日志)
- 网络: 1Gbps

### 4.3 部署脚本

```bash
# 部署脚本位置
./scripts/deploy.sh

# 使用方法
./scripts/deploy.sh [environment]

# 示例
./scripts/deploy.sh prod
```

## 5. 配置管理

### 5.1 配置文件

| 配置文件 | 路径 | 用途 |
|---------|------|------|
| application.yml | /app/config/ | 主配置文件 |
| classification-rules.yml | /app/config/ | 分类映射规则 |
| logback.xml | /app/config/ | 日志配置 |

### 5.2 关键配置项

**Pulsar配置**:
```yaml
pulsar:
  cluster:
    url: "pulsar://pulsar-cluster:6650"
  topic: "persistent://public/default/content-publish"
  subscription: "hydocpusher-subscription"
```

**档案系统配置**:
```yaml
archive:
  api:
    url: "http://archive-system:8080/news/archive/receive"
    timeout: 30000
  app:
    id: "NEWS"
    token: "TmV3cytJbnRlcmZhY2U="
```

### 5.3 环境变量

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| SPRING_PROFILES_ACTIVE | dev | 运行环境 |
| PULSAR_CLUSTER_URL | - | Pulsar集群地址 |
| ARCHIVE_API_URL | - | 档案系统API地址 |
| LOG_LEVEL | INFO | 日志级别 |

## 6. 监控和告警

### 6.1 监控指标

| 指标类型 | 指标名称 | 告警阈值 |
|---------|----------|----------|
| 消息处理 | message_processed_count | - |
| 错误率 | error_rate | >10% |
| 处理延迟 | processing_time | >1000ms |
| 系统资源 | memory_usage | >80% |
| HTTP调用 | http_request_duration | >5000ms |

### 6.2 健康检查

**健康检查端点**:
- `GET /health` - 应用健康状态
- `GET /health/liveness` - 存活探针
- `GET /health/readiness` - 就绪探针

**预期响应**:
```json
{
  "status": "UP",
  "timestamp": "2024-01-01T12:00:00Z",
  "components": {
    "pulsar": "UP",
    "archive": "UP",
    "database": "UP"
  }
}
```

### 6.3 告警配置

**告警级别**:
- **CRITICAL**: 系统不可用，立即处理
- **WARNING**: 性能下降，24小时内处理
- **INFO**: 信息通知，无需立即处理

**告警渠道**:
- 邮件通知
- 短信通知
- 企业微信群
- PagerDuty

## 7. 运维操作

### 7.1 日常操作

**启动服务**:
```bash
# 启动服务
docker-compose up -d hydocpusher

# 查看状态
docker-compose ps hydocpusher

# 查看日志
docker-compose logs -f hydocpusher
```

**停止服务**:
```bash
# 停止服务
docker-compose stop hydocpusher

# 重启服务
docker-compose restart hydocpusher
```

### 7.2 配置更新

**更新配置**:
```bash
# 1. 更新配置文件
vim config/application.yml

# 2. 重启服务
docker-compose restart hydocpusher

# 3. 验证配置
curl http://localhost:8080/health
```

**更新分类规则**:
```bash
# 1. 更新分类规则
vim config/classification-rules.yml

# 2. 重启服务
docker-compose restart hydocpusher

# 3. 验证规则
./scripts/test-classification.sh
```

### 7.3 版本升级

**升级流程**:
```bash
# 1. 拉取新版本镜像
docker pull hydocpusher:1.0.1

# 2. 更新docker-compose.yml
vim docker-compose.yml

# 3. 停止旧版本
docker-compose stop hydocpusher

# 4. 启动新版本
docker-compose up -d hydocpusher

# 5. 验证升级
curl http://localhost:8080/health
```

## 8. 故障排除

### 8.1 常见问题

**消息消费失败**:
```bash
# 检查Pulsar连接
curl http://localhost:8080/health | jq '.components.pulsar'

# 查看消费状态
docker-compose exec pulsar bin/pulsar-admin topics stats persistent://public/default/content-publish

# 检查死信队列
docker-compose exec pulsar bin/pulsar-admin topics stats persistent://public/default/hydocpusher-dlq
```

**HTTP调用失败**:
```bash
# 检查档案系统连接
curl http://localhost:8080/health | jq '.components.archive'

# 查看HTTP调用日志
docker-compose logs hydocpusher | grep "ArchiveClient"

# 测试API连接
curl -X POST http://archive-system:8080/news/archive/receive -H "Content-Type: application/json" -d '{"test": true}'
```

**性能问题**:
```bash
# 查看资源使用情况
docker stats hydocpusher

# 查看性能指标
curl http://localhost:8080/actuator/metrics

# 分析线程状态
docker-compose exec hydocpusher jstack <pid>
```

### 8.2 日志分析

**日志位置**:
- 应用日志: `/app/logs/application.log`
- 错误日志: `/app/logs/error.log`
- 访问日志: `/app/logs/access.log`

**日志查询**:
```bash
# 查看错误日志
tail -f /app/logs/error.log

# 搜索特定消息
grep "message_id" /app/logs/application.log

# 统计错误数量
grep "ERROR" /app/logs/application.log | wc -l
```

### 8.3 数据恢复

**死信队列处理**:
```bash
# 查看死信队列消息
docker-compose exec pulsar bin/pulsar-client consume persistent://public/default/hydocpusher-dlq -s

# 重新处理死信消息
./scripts/retry-dlq-messages.sh

# 清理死信队列
docker-compose exec pulsar bin/pulsar-admin topics clear-backlog persistent://public/default/hydocpusher-dlq
```

## 9. 安全配置

### 9.1 访问控制

**网络访问控制**:
- 只允许特定IP访问管理端口
- 使用防火墙限制外部访问
- 启用HTTPS/TLS加密

**认证配置**:
```yaml
security:
  oauth2:
    resource:
      jwt:
        key-uri: http://auth-server/oauth/token_key
```

### 9.2 数据安全

**敏感数据保护**:
- 使用环境变量存储敏感信息
- 配置文件加密存储
- 定期轮换访问令牌

**审计日志**:
```bash
# 查看审计日志
tail -f /app/logs/audit.log

# 分析访问模式
grep "archive_request" /app/logs/audit.log | awk '{print $1}' | sort | uniq -c
```

## 10. 联系方式

### 10.1 技术支持

**开发团队**:
- 技术负责人: [姓名] <邮箱>
- 后端开发: [姓名] <邮箱>
- DevOps工程师: [姓名] <邮箱>

**运维团队**:
- 运维负责人: [姓名] <邮箱>
- 系统管理员: [姓名] <邮箱>

### 10.2 紧急联系

**严重故障**:
- 值班电话: [电话号码]
- 企业微信: [群组]
- PagerDuty: [调度规则]

### 10.3 文档和资源

**项目资源**:
- 代码仓库: [Git地址]
- 文档地址: [文档地址]
- 监控地址: [监控地址]
- 日志系统: [日志地址]

## 11. 附录

### 11.1 检查清单

**日常运维检查**:
- [ ] 服务运行状态正常
- [ ] 消息消费无积压
- [ ] 错误率在正常范围
- [ ] 资源使用率正常
- [ ] 备份任务执行成功

**发布检查**:
- [ ] 代码编译成功
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 性能测试通过
- [ ] 安全扫描通过
- [ ] 文档更新完成

### 11.2 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service]

# 进入容器
docker-compose exec [service] bash

# 重启服务
docker-compose restart [service]

# 查看资源使用
docker stats [container]

# 备份数据
./scripts/backup.sh

# 恢复数据
./scripts/restore.sh [backup-file]
```

### 11.3 性能基准

**性能指标**:
- 消息处理速度: ≥100条/秒
- 端到端延迟: ≤500ms
- CPU使用率: ≤70%
- 内存使用率: ≤80%
- 错误率: ≤1%

**容量规划**:
- 单实例处理能力: 100条/秒
- 集群处理能力: 1000条/秒
- 存储需求: 10GB/月
- 网络带宽: 100Mbps

---

本项目交接文档提供了HyDocPusher项目的完整交接信息，确保运维团队能够顺利接管和维护系统。