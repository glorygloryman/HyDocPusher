# 部署基础设施文档

## 1. 部署架构总览

HyDocPusher采用容器化部署方式，支持多种部署环境：

```
┌─────────────────────────────────────────────────────────────────┐
│                        部署架构                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   开发环境       │  │   测试环境       │  │   生产环境       │   │
│  │  Development    │  │     Testing     │  │   Production    │   │
│  │                 │  │                 │  │                 │   │
│  │ • 单节点部署     │  │ • 多节点集群     │  │ • 高可用集群     │   │
│  │ • 本地Pulsar    │  │ • 独立Pulsar    │  │ • 生产级Pulsar  │   │
│  │ • 简化配置      │  │ • 完整配置      │  │ • 完整监控       │   │
│  │ • 快速启动      │  │ • 压力测试      │  │ • 自动扩缩容     │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 开发环境部署

### 2.1 环境要求

**硬件要求**:
- CPU: 2核心
- 内存: 4GB
- 磁盘: 20GB
- 网络: 100Mbps

**软件要求**:
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9.6
- pip 21.0+
- Git 2.0+

### 2.2 快速启动

**1. 克隆项目**:
```bash
git clone <repository-url>
cd HyDocPusher
```

**2. 配置环境变量**:
```bash
# .env.dev
PULSAR_CLUSTER_URL=pulsar://localhost:6650
PULSAR_TOPIC=persistent://public/default/content-publish-dev
ARCHIVE_API_URL=http://localhost:8081/news/archive/receive
SPRING_PROFILES_ACTIVE=dev
```

**3. 启动服务**:
```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f hydocpusher
```

**4. 验证部署**:
```bash
# 健康检查
curl http://localhost:8080/health

# 发送测试消息
./scripts/send-test-message.sh
```

### 2.3 开发环境配置

**docker-compose.dev.yml**:
```yaml
version: '3.8'

services:
  hydocpusher:
    build: 
      context: .
      dockerfile: docker/Dockerfile.dev
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - PULSAR_CLUSTER_URL=pulsar://pulsar:6650
      - ARCHIVE_API_URL=http://mock-archive:8080/news/archive/receive
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ./src/main/java:/app/src/main/java
    depends_on:
      - pulsar
      - mock-archive
    networks:
      - hydocpusher-network

  pulsar:
    image: apachepulsar/pulsar:2.10.0
    ports:
      - "6650:6650"
      - "8080:8080"
    environment:
      - PULSAR_STANDALONE_USE_ZOOKEEPER=false
    volumes:
      - pulsar-data:/pulsar/data
    networks:
      - hydocpusher-network

  mock-archive:
    image: mockserver/mockserver:latest
    ports:
      - "8081:1080"
    environment:
      - MOCKSERVER_PROPERTY_FILE=/config/mockserver.properties
    volumes:
      - ./docker/mockserver:/config
    networks:
      - hydocpusher-network

volumes:
  pulsar-data:

networks:
  hydocpusher-network:
    driver: bridge
```

## 3. 测试环境部署

### 3.1 环境要求

**硬件要求**:
- CPU: 4核心
- 内存: 8GB
- 磁盘: 50GB
- 网络: 1Gbps

**软件要求**:
- Kubernetes 1.20+
- Helm 3.0+
- Prometheus 2.20+
- Grafana 7.0+

### 3.2 Kubernetes部署

**1. 创建命名空间**:
```bash
kubectl create namespace hydocpusher-test
kubectl config set-context --current --namespace=hydocpusher-test
```

**2. 部署配置**:
```bash
# 部署配置
kubectl apply -f k8s/test/configmap.yaml
kubectl apply -f k8s/test/secret.yaml
kubectl apply -f k8s/test/deployment.yaml
kubectl apply -f k8s/test/service.yaml
kubectl apply -f k8s/test/ingress.yaml
```

**3. 监控部署**:
```bash
# 部署Prometheus
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --set server.service.type=LoadBalancer

# 部署Grafana
helm install grafana grafana/grafana \
  --namespace monitoring \
  --set admin.password=admin123
```

### 3.3 测试环境配置

**configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hydocpusher-config
  namespace: hydocpusher-test
data:
  application.yml: |
    spring:
      profiles: test
      application:
        name: hydocpusher
    
    pulsar:
      cluster:
        url: pulsar://pulsar-test:6650
      topic: persistent://public/default/content-publish-test
      subscription: hydocpusher-test-subscription
      dead-letter-topic: persistent://public/default/hydocpusher-test-dlq
    
    archive:
      api:
        url: http://archive-test:8080/news/archive/receive
        timeout: 30000
      retry:
        max-attempts: 3
        delay: 60000
    
    logging:
      level:
        com.hydocpusher: DEBUG
      pattern:
        console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
```

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hydocpusher
  namespace: hydocpusher-test
spec:
  replicas: 2
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
        image: hydocpusher:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "test"
        envFrom:
        - configMapRef:
            name: hydocpusher-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
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

## 4. 生产环境部署

### 4.1 环境要求

**硬件要求**:
- CPU: 8核心+
- 内存: 16GB+
- 磁盘: 100GB SSD
- 网络: 10Gbps
- 高可用性要求

**软件要求**:
- Kubernetes 1.22+
- Istio 1.10+ (服务网格)
- Prometheus 2.30+
- Grafana 8.0+
- ELK Stack 7.0+

### 4.2 生产级部署架构

**高可用架构**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Gateway   │    │   Service Mesh  │
│                 │    │                 │    │                 │
│ • HAProxy/Nginx │    │ • Kong/Istio    │    │ • Istio Sidecar │
│ • SSL Termination│    │ • Rate Limiting │    │ • mTLS          │
│ • Health Checks │    │ • Authentication│    │ • Circuit Breaker│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HyDocPusher   │    │   Pulsar Cluster │    │   Archive System│
│                 │    │                 │    │                 │
│ • Multi-AZ      │    │ • Multi-AZ      │    │ • Multi-AZ      │
│ • Auto Scaling  │    │ • Replication   │    │ • Load Balancing│
│ • Health Monitor│    │ • Backup        │    │ • Health Monitor│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 4.3 生产环境部署

**1. 基础设施准备**:
```bash
# 创建生产命名空间
kubectl create namespace hydocpusher-prod
kubectl label namespace hydocpusher-prod istio-injection=enabled

# 部署网络策略
kubectl apply -f k8s/prod/network-policy.yaml

# 部署资源配额
kubectl apply -f k8s/prod/resource-quota.yaml
```

**2. 部署应用**:
```bash
# 使用Helm部署
helm upgrade --install hydocpusher ./helm/hydocpusher \
  --namespace hydocpusher-prod \
  --set image.tag=1.0.0 \
  --set replicaCount=3 \
  --set resources.requests.memory=1Gi \
  --set resources.requests.cpu=500m \
  --set resources.limits.memory=2Gi \
  --set resources.limits.cpu=1000m
```

**3. 部署监控**:
```bash
# 部署Prometheus Operator
helm install prometheus-operator prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# 部署Grafana仪表板
kubectl apply -f monitoring/grafana-dashboards/
```

### 4.4 生产环境配置

**Helm Chart**:
```yaml
# helm/hydocpusher/values.yaml
replicaCount: 3

image:
  repository: hydocpusher
  tag: 1.0.0
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: hydocpusher.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: hydocpusher-tls
      hosts:
        - hydocpusher.example.com

resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

config:
  spring:
    profiles: prod
  pulsar:
    cluster:
      url: pulsar://pulsar-prod:6650
    topic: persistent://public/default/content-publish-prod
  archive:
    api:
      url: http://archive-prod:8080/news/archive/receive
      timeout: 30000
```

## 5. 数据库部署

### 5.1 配置数据库

**PostgreSQL部署**:
```yaml
# k8s/prod/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: hydocpusher-prod
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: hydocpusher
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

### 5.2 Redis部署

**Redis缓存部署**:
```yaml
# k8s/prod/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: hydocpusher-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:6-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --appendonly yes
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
```

## 6. 监控部署

### 6.1 Prometheus部署

**Prometheus配置**:
```yaml
# monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
    - job_name: 'hydocpusher'
      static_configs:
      - targets: ['hydocpusher.hydocpusher-prod.svc.cluster.local:8080']
      metrics_path: '/actuator/prometheus'
      scrape_interval: 15s
    
    - job_name: 'pulsar'
      static_configs:
      - targets: ['pulsar-prod:8080']
      metrics_path: '/metrics'
      scrape_interval: 30s
    
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
```

### 6.2 Grafana仪表板

**Grafana配置**:
```json
{
  "dashboard": {
    "id": null,
    "title": "HyDocPusher监控",
    "tags": ["hydocpusher"],
    "panels": [
      {
        "id": 1,
        "title": "消息处理速率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(message_processed_count_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "错误率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(error_count_total[5m]) / rate(message_processed_count_total[5m])",
            "legendFormat": "错误率"
          }
        ]
      }
    ]
  }
}
```

## 7. 日志部署

### 7.1 ELK Stack部署

**Elasticsearch部署**:
```yaml
# logging/elasticsearch.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.10.0
        ports:
        - containerPort: 9200
        env:
        - name: discovery.type
          value: "single-node"
        volumeMounts:
        - name: elasticsearch-data
          mountPath: /usr/share/elasticsearch/data
```

**Logstash部署**:
```yaml
# logging/logstash.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logstash
  namespace: logging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: logstash
  template:
    metadata:
      labels:
        app: logstash
    spec:
      containers:
      - name: logstash
        image: docker.elastic.co/logstash/logstash:7.10.0
        ports:
        - containerPort: 5044
        volumeMounts:
        - name: logstash-config
          mountPath: /usr/share/logstash/pipeline
      volumes:
      - name: logstash-config
        configMap:
          name: logstash-config
```

## 8. 备份和恢复

### 8.1 备份策略

**配置备份**:
```bash
#!/bin/bash
# backup-config.sh
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/hydocpusher/$DATE"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份Kubernetes配置
kubectl get configmap,secret,deployment,service -n hydocpusher-prod -o yaml > $BACKUP_DIR/k8s-config.yaml

# 备份Helm配置
helm get values hydocpusher -n hydocpusher-prod > $BACKUP_DIR/helm-values.yaml

# 备份数据库
kubectl exec postgres-0 -n hydocpusher-prod -- pg_dump -U hydocpusher hydocpusher > $BACKUP_DIR/database.sql

# 压缩备份
tar -czf $BACKUP_DIR.tar.gz -C /backup/hydocpusher $DATE

# 上传到对象存储
aws s3 cp $BACKUP_DIR.tar.gz s3://backup-bucket/hydocpusher/

# 清理旧备份
find /backup/hydocpusher -name "*.tar.gz" -mtime +7 -delete
```

### 8.2 恢复策略

**恢复步骤**:
```bash
#!/bin/bash
# restore.sh
#!/bin/bash

BACKUP_FILE=$1
RESTORE_DIR="/restore/hydocpusher"

# 解压备份
tar -xzf $BACKUP_FILE -C $RESTORE_DIR

# 恢复Kubernetes配置
kubectl apply -f $RESTORE_DIR/k8s-config.yaml

# 恢复Helm配置
helm upgrade --install hydocpusher ./helm/hydocpusher \
  -n hydocpusher-prod \
  -f $RESTORE_DIR/helm-values.yaml

# 恢复数据库
kubectl cp $RESTORE_DIR/database.sql postgres-0:/tmp/database.sql -n hydocpusher-prod
kubectl exec postgres-0 -n hydocpusher-prod -- psql -U hydocpusher -d hydocpusher -f /tmp/database.sql
```

## 9. 灾难恢复

### 9.1 多区域部署

**跨区域部署**:
```yaml
# k8s/prod/multi-region.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: region-config
  namespace: hydocpusher-prod
data:
  region-a: "us-east-1"
  region-b: "us-west-2"
  failover-threshold: "3"
  health-check-interval: "30"
```

### 9.2 自动故障转移

**故障转移脚本**:
```bash
#!/bin/bash
# failover.sh
#!/bin/bash

PRIMARY_REGION="us-east-1"
SECONDARY_REGION="us-west-2"
HEALTH_CHECK_URL="http://hydocpusher.example.com/health"

# 检查主区域健康状态
response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_CHECK_URL)

if [ $response -ne 200 ]; then
    echo "Primary region unhealthy, initiating failover"
    
    # 切换流量到备用区域
    kubectl patch ingress hydocpusher -n hydocpusher-prod \
      --type='json' \
      -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "hydocpusher-secondary"}]'
    
    # 发送告警
    ./scripts/send-alert.sh "Failover initiated from $PRIMARY_REGION to $SECONDARY_REGION"
fi
```

## 10. 部署验证

### 10.1 部署检查清单

**部署验证检查项**:
- [ ] 所有Pod正常运行
- [ ] 服务可以正常访问
- [ ] 数据库连接正常
- [ ] 消息队列连接正常
- [ ] 监控指标正常
- [ ] 日志收集正常
- [ ] 健康检查通过
- [ ] 性能指标达标
- [ ] 备份策略有效

### 10.2 性能测试

**负载测试**:
```bash
# 使用JMeter进行负载测试
jmeter -n -t jmeter/load-test.jmx -l results/load-test-results.jtl

# 生成测试报告
jmeter -g results/load-test-results.jtl -o reports/load-test-report
```

这个部署基础设施文档提供了HyDocPusher在不同环境下的完整部署方案，包括开发、测试和生产环境的部署配置和最佳实践。