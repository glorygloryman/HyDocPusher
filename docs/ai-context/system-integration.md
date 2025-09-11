# 系统集成文档

## 1. 集成架构总览

HyDocPusher作为数据同步中间件，需要与多个外部系统进行集成：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   内容发布系统   │    │   HyDocPusher    │    │   电子档案系统   │
│Content Publishing│    │                 │    │ Archive System  │
│                 │    │                 │    │                 │
│ • 内容发布接口   │◄──►│ • 消息消费      │◄──►│ • 归档接收接口   │
│ • 消息生成      │    │ • 数据转换      │    │ • 状态返回      │
│ • 格式标准化    │    │ • HTTP推送      │    │ • 错误处理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Pulsar集群    │    │   监控告警系统   │    │   运维管理平台   │
│   Pulsar Cluster│    │ Monitoring      │    │ Operations      │
│                 │    │                 │    │                 │
│ • 消息队列      │    │ • 性能监控      │    │ • 部署管理      │
│ • Topic管理     │    │ • 错误告警      │    │ • 配置管理      │
│ • 死信队列      │    │ • 日志聚合      │    │ • 健康检查      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 2. Pulsar消息队列集成

### 2.1 连接配置

**Pulsar集群连接**:
```yaml
pulsar:
  cluster:
    url: "pulsar://pulsar-cluster:6650"  # 生产环境地址
    admin-url: "http://pulsar-cluster:8080"  # 管理接口地址
    connection-timeout: 30000  # 连接超时时间(ms)
    operation-timeout: 30000  # 操作超时时间(ms)
    
  topic: "persistent://public/default/content-publish"
  subscription: "hydocpusher-subscription"
  subscription-type: "Shared"  # 共享订阅模式
  
  dead-letter:
    topic: "persistent://public/default/hydocpusher-dlq"
    max-redeliver-count: 3  # 最大重试次数
    
  # 认证配置（如果需要）
  auth:
    plugin: "org.apache.pulsar.client.impl.auth.AuthenticationToken"
    token: "your-auth-token"
```

### 2.2 消息格式约定

**输入消息格式**:
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

### 2.3 集成测试

**连接测试**:
```bash
# 测试Pulsar连接
./scripts/test-pulsar-connection.sh

# 发送测试消息
./scripts/send-test-message.sh

# 查看消息消费状态
./scripts/check-consumer-status.sh
```

## 3. 电子档案系统集成

### 3.1 API接口规范

**归档接收接口**:
- **URL**: `http://archive-system:8080/news/archive/receive`
- **Method**: POST
- **Content-Type**: application/json
- **Authentication**: Bearer Token
- **Timeout**: 30秒

**请求头**:
```http
POST /news/archive/receive HTTP/1.1
Host: archive-system:8080
Content-Type: application/json
Authorization: Bearer your-api-token
```

**请求体格式**:
```json
{
  "AppId": "NEWS",
  "AppToken": "TmV3cytJbnRlcmZhY2U=",
  "CompanyName": "云南省能源投资集团有限公司",
  "ArchiveType": "17",
  "ArchiveData": {
    "did": "DOC001",
    "wzmc": "新闻网站",
    "dn": "example.com",
    "classfyname": "新闻头条",
    "classfy": "XWTT",
    "title": "重要新闻标题",
    "author": "张三",
    "docdate": "2024-01-01",
    "year": "2024",
    "retentionperiod": 30,
    "fillingdepartment": "新闻部",
    "bly": "admin",
    "attachment": [
      {
        "name": "重要新闻标题(正文)",
        "ext": "html",
        "file": "http://example.com/news/001.html",
        "type": "正文"
      },
      {
        "name": "附件1_图片",
        "ext": "jpg",
        "file": "http://example.com/images/news001.jpg",
        "type": "图片"
      }
    ]
  }
}
```

**响应格式**:
```json
{
  "STATUS": 0,
  "DESC": "成功",
  "DATAID": "ARCHIVE001",
  "TIMESTAMP": "2024-01-01T12:00:01Z"
}
```

### 3.2 错误码定义

| 状态码 | 描述 | 处理方式 |
|-------|------|----------|
| 0 | 成功 | 记录成功日志 |
| 1001 | 参数错误 | 检查请求格式 |
| 1002 | 认证失败 | 检查认证信息 |
| 1003 | 数据重复 | 记录警告，继续处理 |
| 2001 | 系统错误 | 重试处理 |
| 2002 | 服务不可用 | 重试处理 |

### 3.3 集成配置

**档案系统配置**:
```yaml
archive:
  api:
    url: "http://archive-system:8080/news/archive/receive"
    timeout: 30000
    connect-timeout: 10000
    read-timeout: 20000
    auth:
      type: "bearer"
      token: "your-archive-api-token"
    
  retry:
    max-attempts: 3
    delay: 60000
    backoff-multiplier: 2.0
    
  circuit-breaker:
    enabled: true
    failure-rate-threshold: 50
    wait-duration-in-open-state: 30000
    permitted-number-of-calls-in-half-open-state: 5
```

## 4. 监控系统集成

### 4.1 Prometheus监控

**应用指标**:
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 监控配置
    metrics_enabled: bool = True
    metrics_port: int = 8080
    metrics_path: str = "/metrics"
    
    # 应用配置
    app_name: str = "hydocpusher"
    environment: str = "development"
    
    # Prometheus配置
    prometheus_enabled: bool = True
    prometheus_path: str = "/metrics"
    
    class Config:
        env_file = ".env"
        env_prefix = ""

settings = Settings()
```

**应用启动配置**:
```python
# main.py
from fastapi import FastAPI
from prometheus_client import make_asgi_app, REGISTRY
from prometheus_client.core import CollectorRegistry
import uvicorn
from config import settings
from metrics_collector import MetricsCollector

app = FastAPI(title=settings.app_name)

# 创建自定义注册表
registry = CollectorRegistry()
metrics_collector = MetricsCollector(registry)

# 添加Prometheus指标端点
metrics_app = make_asgi_app(registry=registry)
app.mount(settings.prometheus_path, metrics_app)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.metrics_port,
        reload=settings.environment == "development"
    )
```

**关键指标**:
```python
# metrics_collector.py
import asyncio
import time
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client.registry import CollectorRegistry

class MetricsCollector:
    def __init__(self, registry: CollectorRegistry):
        self.registry = registry
        
        # 消息处理指标
        self.message_received_counter = Counter(
            'message_received_total', 
            'Total messages received', 
            registry=registry
        )
        self.message_processed_counter = Counter(
            'message_processed_total', 
            'Total messages processed', 
            registry=registry
        )
        self.message_failed_counter = Counter(
            'message_failed_total', 
            'Total messages failed', 
            registry=registry
        )
        self.message_processing_timer = Histogram(
            'message_processing_time_seconds', 
            'Time spent processing messages', 
            registry=registry
        )
        
        # HTTP调用指标
        self.http_request_counter = Counter(
            'http_requests_total', 
            'Total HTTP requests', 
            ['method', 'endpoint'],
            registry=registry
        )
        self.http_request_timer = Histogram(
            'http_request_time_seconds', 
            'Time spent on HTTP requests', 
            ['method', 'endpoint'],
            registry=registry
        )
        self.http_error_counter = Counter(
            'http_errors_total', 
            'Total HTTP errors', 
            ['method', 'endpoint', 'status_code'],
            registry=registry
        )
        
        # 处理时间记录
        self._processing_start_times = {}
    
    async def handle_message_received(self, message_id: str):
        """处理消息接收事件"""
        self.message_received_counter.inc()
        self._processing_start_times[message_id] = time.time()
    
    async def handle_message_processed(self, message_id: str):
        """处理消息处理完成事件"""
        self.message_processed_counter.inc()
        if message_id in self._processing_start_times:
            processing_time = time.time() - self._processing_start_times[message_id]
            self.message_processing_timer.observe(processing_time)
            del self._processing_start_times[message_id]
    
    async def handle_message_failed(self, message_id: str, error_type: str):
        """处理消息失败事件"""
        self.message_failed_counter.inc()
        if message_id in self._processing_start_times:
            del self._processing_start_times[message_id]
```

### 4.2 日志聚合

**Logstash配置**:
```ruby
# logstash.conf
input {
  tcp {
    port => 5000
    codec => json_lines
  }
}

filter {
  if [app_name] == "hydocpusher" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp}%{SPACE}%{WORD:level}%{SPACE}%{GREEDYDATA:log_message}" }
    }
    
    date {
      match => [ "timestamp", "yyyy-MM-dd HH:mm:ss,SSS" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "hydocpusher-%{+YYYY.MM.dd}"
  }
}
```

### 4.3 告警规则

**Prometheus告警规则**:
```yaml
# alert-rules.yml
groups:
  - name: hydocpusher
    rules:
      - alert: HighMessageProcessingTime
        expr: histogram_quantile(0.95, rate(message_processing_time_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High message processing time"
          description: "95th percentile processing time is above 1 second"
      
      - alert: HighErrorRate
        expr: rate(error_count_total[5m]) / rate(message_processed_count_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate"
          description: "Error rate is above 10%"
      
      - alert: DeadLetterQueueGrowing
        expr: pulsar_subscription_backlog{subscription="hydocpusher-dlq"} > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Dead letter queue is growing"
          description: "DLQ backlog is above 100 messages"
```

## 5. 部署集成

### 5.1 Docker Compose集成

**开发环境**:
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  hydocpusher:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - PULSAR_CLUSTER_URL=pulsar://pulsar:6650
      - ARCHIVE_API_URL=http://archive-system:8080/news/archive/receive
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - pulsar
      - archive-system
    
  pulsar:
    image: apachepulsar/pulsar:latest
    ports:
      - "6650:6650"
      - "8080:8080"
    environment:
      - PULSAR_STANDALONE_USE_ZOOKEEPER=false
    
  archive-system:
    image: archive-system:latest
    ports:
      - "8081:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
  
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 5.2 Kubernetes部署

**Kubernetes配置**:
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hydocpusher
  labels:
    app: hydocpusher
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hydocpusher
  template:
    metadata:
      labels:
        app: hydocpusher
    spec:
      containers:
      - name: hydocpusher
        image: hydocpusher:latest
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "prod"
        - name: PULSAR_CLUSTER_URL
          valueFrom:
            configMapKeyRef:
              name: hydocpusher-config
              key: pulsar-cluster-url
        - name: ARCHIVE_API_URL
          valueFrom:
            configMapKeyRef:
              name: hydocpusher-config
              key: archive-api-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 5.3 CI/CD集成

**Jenkins Pipeline**:
```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        DOCKER_IMAGE = 'hydocpusher'
        KUBE_NAMESPACE = 'production'
        PYTHON_VERSION = '3.9.6'
    }
    
    stages {
        stage('Build') {
            steps {
                sh '''
                    python${PYTHON_VERSION} -m venv venv
                    source venv/bin/activate
                    pip install -r requirements.txt
                    pip install -r requirements-dev.txt
                    python -m black hydocpusher/
                    python -m flake8 hydocpusher/
                    python -m mypy hydocpusher/
                '''
            }
        }
        
        stage('Test') {
            steps {
                sh '''
                    source venv/bin/activate
                    python -m pytest tests/ -v --cov=hydocpusher --cov-report=xml
                    python -m pytest integration-tests/ -v
                '''
                junit 'test-results.xml'
                publishCoverage adapters: [coberturaAdapter('coverage.xml')],
                    sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    def appVersion = getVersion()
                    sh "docker build -t ${DOCKER_IMAGE}:${appVersion} ."
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-credentials') {
                        docker.image("${DOCKER_IMAGE}:${appVersion}").push()
                    }
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                sh '''
                    source venv/bin/activate
                    pip install bandit safety
                    bandit -r hydocpusher/ -f json -o bandit-report.json
                    safety check --json --output safety-report.json
                '''
                archiveArtifacts artifacts: '*-report.json'
            }
        }
        
        stage('Deploy to Staging') {
            steps {
                sh '''
                    kubectl apply -f k8s/staging/
                    kubectl rollout status deployment/hydocpusher -n staging
                '''
            }
        }
        
        stage('Integration Test') {
            steps {
                sh '''
                    source venv/bin/activate
                    python scripts/run-integration-tests.py
                '''
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    kubectl apply -f k8s/production/
                    kubectl rollout status deployment/hydocpusher -n production
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
            emailext (
                subject: 'Pipeline Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}',
                body: '''
                    Pipeline failed for ${env.JOB_NAME} - ${env.BUILD_NUMBER}
                    
                    Build URL: ${env.BUILD_URL}
                    Console Output: ${env.BUILD_URL}console
                ''',
                to: '${env.CHANGE_AUTHOR_EMAIL}, dev-team@company.com'
            )
        }
    }
}
```

## 6. 安全集成

### 6.1 网络安全

**防火墙配置**:
```bash
# iptables配置
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
iptables -A INPUT -p tcp --dport 6650 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 6650 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -j DROP
```

### 6.2 认证授权

**API认证**:
```python
# security.py
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic_settings import BaseSettings
import os

class SecuritySettings(BaseSettings):
    # Pulsar认证配置
    pulsar_auth_token: Optional[str] = None
    pulsar_auth_plugin: Optional[str] = None
    
    # 档案系统认证配置
    archive_api_token: Optional[str] = None
    archive_auth_type: str = "bearer"
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_prefix = ""

security_settings = SecuritySettings()

# HTTP Bearer认证
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.pulsar_token = security_settings.pulsar_auth_token
        self.archive_token = security_settings.archive_api_token
    
    def get_pulsar_auth_params(self) -> dict:
        """获取Pulsar认证参数"""
        if not self.pulsar_token:
            return {}
        
        return {
            "auth_plugin": "org.apache.pulsar.client.impl.auth.AuthenticationToken",
            "auth_params": {
                "token": self.pulsar_token
            }
        }
    
    def get_archive_auth_headers(self) -> dict:
        """获取档案系统认证头"""
        if not self.archive_token:
            return {}
        
        return {
            "Authorization": f"Bearer {self.archive_token}"
        }
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials) -> bool:
        """验证JWT令牌"""
        try:
            # 这里实现JWT验证逻辑
            # 在实际应用中，应该使用像PyJWT这样的库
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

# 创建认证服务实例
auth_service = AuthService()
```

### 6.3 数据加密

**敏感数据加密**:
```python
# encryption_service.py
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

class EncryptionService:
    def __init__(self, encryption_key: str = None):
        self.logger = logging.getLogger(__name__)
        self.encryption_key = encryption_key or os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError("Encryption key must be provided")
        
        # 生成Fernet密钥
        self.fernet_key = self._generate_fernet_key()
        self.fernet = Fernet(self.fernet_key)
    
    def _generate_fernet_key(self) -> bytes:
        """从加密密钥生成Fernet密钥"""
        # 使用PBKDF2派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'salt_',  # 在生产环境中应该使用随机salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        try:
            if not data:
                return ""
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            if not encrypted_data:
                return ""
            # 解码base64并解密
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def is_encrypted(self, data: str) -> bool:
        """检查数据是否已加密"""
        try:
            if not data:
                return False
            # 尝试解密，如果成功则认为是加密的
            self.decrypt(data)
            return True
        except Exception:
            return False
```

## 7. 集成测试

### 7.1 端到端测试

**测试场景**:
1. **消息流程测试**: 验证完整的消息处理流程
2. **错误处理测试**: 验证各种错误情况的处理
3. **性能测试**: 验证系统性能指标
4. **集成测试**: 验证与外部系统的集成

### 7.2 性能测试

**JMeter测试脚本**:
```xml
<!-- jmeter-test-plan.jmx -->
<TestPlan>
  <ThreadGroup>
    <stringProp name="ThreadGroup.num_threads">100</stringProp>
    <stringProp name="ThreadGroup.ramp_time">60</stringProp>
    <stringProp name="ThreadGroup.duration">300</stringProp>
    
    <HTTPSampler>
      <stringProp name="HTTPSampler.domain">localhost</stringProp>
      <stringProp name="HTTPSampler.port">8080</stringProp>
      <stringProp name="HTTPSampler.path">/api/messages</stringProp>
      <stringProp name="HTTPSampler.method">POST</stringProp>
    </HTTPSampler>
  </ThreadGroup>
</TestPlan>
```

## 8. 运维集成

### 8.1 配置管理

**配置中心集成**:
```python
# config_manager.py
import asyncio
import aiohttp
import yaml
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
import logging

class ConfigManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_cache: Dict[str, Any] = {}
        self.last_updated: Optional[float] = None
        self.refresh_interval: int = 300  # 5分钟刷新一次
    
    async def load_config_from_server(self, config_server_url: str, app_name: str, profile: str) -> Dict[str, Any]:
        """从配置服务器加载配置"""
        try:
            url = f"{config_server_url}/{app_name}-{profile}.yml"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        config_data = await response.text()
                        return yaml.safe_load(config_data)
                    else:
                        self.logger.error(f"Failed to load config: {response.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"Error loading config from server: {e}")
            return {}
    
    async def get_config(self, config_server_url: str, app_name: str, profile: str, force_refresh: bool = False) -> Dict[str, Any]:
        """获取配置，支持缓存"""
        current_time = asyncio.get_event_loop().time()
        
        # 检查是否需要刷新
        if (force_refresh or 
            self.last_updated is None or 
            current_time - self.last_updated > self.refresh_interval):
            
            new_config = await self.load_config_from_server(config_server_url, app_name, profile)
            if new_config:
                self.config_cache = new_config
                self.last_updated = current_time
                self.logger.info("Configuration refreshed from server")
        
        return self.config_cache
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config_cache
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

# 全局配置管理器实例
config_manager = ConfigManager()

class AppConfig(BaseSettings):
    # 配置服务器设置
    config_server_url: str = "http://config-server:8888"
    app_name: str = "hydocpusher"
    profile: str = "development"
    
    # Consul服务发现设置
    consul_host: str = "consul-server"
    consul_port: int = 8500
    service_name: str = "hydocpusher"
    health_check_path: str = "/health"
    health_check_interval: int = 10
    
    class Config:
        env_file = ".env"
        env_prefix = ""

settings = AppConfig()
```

### 8.2 备份恢复

**数据备份策略**:
```bash
#!/bin/bash
# backup-config.sh
#!/bin/bash

# 备份配置文件
tar -czf config-backup-$(date +%Y%m%d).tar.gz /app/config/

# 备份日志文件
tar -czf logs-backup-$(date +%Y%m%d).tar.gz /app/logs/

# 上传到对象存储
aws s3 cp config-backup-$(date +%Y%m%d).tar.gz s3://backup-bucket/config/
aws s3 cp logs-backup-$(date +%Y%m%d).tar.gz s3://backup-bucket/logs/
```

这个系统集成文档提供了HyDocPusher与外部系统集成的完整指南，包括Pulsar消息队列、电子档案系统、监控系统、部署平台等的集成方案。