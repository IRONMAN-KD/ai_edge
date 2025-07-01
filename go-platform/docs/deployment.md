# Go Platform 部署指南

本文档详细介绍了如何在不同环境中部署 Go Platform。

## 目录

- [系统要求](#系统要求)
- [环境准备](#环境准备)
- [本地开发部署](#本地开发部署)
- [Docker 部署](#docker-部署)
- [生产环境部署](#生产环境部署)
- [云平台部署](#云平台部署)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [故障排除](#故障排除)

## 系统要求

### 最低要求

- **CPU**: 2 核心
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows (10+)

### 推荐配置

- **CPU**: 4+ 核心
- **内存**: 8GB+ RAM
- **存储**: 100GB+ SSD
- **网络**: 稳定的互联网连接

### 软件依赖

- **Go**: 1.21+
- **数据库**: MySQL 8.0+ / PostgreSQL 13+ / SQLite 3.35+
- **缓存**: Redis 6.0+ (可选)
- **反向代理**: Nginx 1.18+ / Apache 2.4+ (生产环境)
- **容器**: Docker 20.10+ / Docker Compose 2.0+ (可选)

## 环境准备

### 1. 安装 Go

```bash
# Ubuntu/Debian
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# macOS (使用 Homebrew)
brew install go

# 验证安装
go version
```

### 2. 安装数据库

#### MySQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation

# macOS
brew install mysql
brew services start mysql

# 创建数据库和用户
mysql -u root -p
CREATE DATABASE go_platform;
CREATE USER 'go_platform'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON go_platform.* TO 'go_platform'@'localhost';
FLUSH PRIVILEGES;
```

#### PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew install postgresql
brew services start postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE go_platform;
CREATE USER go_platform WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE go_platform TO go_platform;
```

### 3. 安装 Redis (可选)

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS
brew install redis
brew services start redis

# 验证安装
redis-cli ping
```

## 本地开发部署

### 1. 克隆项目

```bash
git clone https://github.com/your-org/go-platform.git
cd go-platform
```

### 2. 安装依赖

```bash
go mod download
```

### 3. 配置环境

```bash
# 复制配置文件
cp config/config.example.yaml config/config.yaml

# 编辑配置文件
vim config/config.yaml
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
make db-migrate

# 创建默认管理员用户
make db-seed
```

### 5. 启动应用

```bash
# 开发模式（热重载）
make dev

# 或者直接运行
go run cmd/server/main.go
```

### 6. 验证部署

```bash
# 健康检查
curl http://localhost:8080/health

# 登录测试
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## Docker 部署

### 1. 单容器部署

```bash
# 构建镜像
docker build -t go-platform .

# 运行容器
docker run -d \
  --name go-platform \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  go-platform
```

### 2. Docker Compose 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

### 3. 自定义 Docker Compose

创建 `docker-compose.override.yml` 文件来自定义配置：

```yaml
version: '3.8'

services:
  app:
    environment:
      - DB_HOST=your-external-db
      - DB_PASSWORD=your-password
    ports:
      - "80:8080"
  
  mysql:
    environment:
      - MYSQL_ROOT_PASSWORD=your-root-password
    volumes:
      - /your/data/path:/var/lib/mysql
```

## 生产环境部署

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y curl wget git unzip

# 创建应用用户
sudo useradd -m -s /bin/bash go-platform
sudo usermod -aG sudo go-platform
```

### 2. 应用部署

```bash
# 切换到应用用户
sudo su - go-platform

# 创建应用目录
mkdir -p /home/go-platform/app
cd /home/go-platform/app

# 下载应用
wget https://github.com/your-org/go-platform/releases/latest/download/go-platform-linux-amd64.tar.gz
tar -xzf go-platform-linux-amd64.tar.gz

# 设置权限
chmod +x go-platform
```

### 3. 配置文件

```bash
# 创建配置目录
mkdir -p config logs data

# 复制生产配置
cp config.example.yaml config/config.yaml
vim config/config.yaml
```

生产环境配置示例：

```yaml
server:
  port: 8080
  mode: release
  enable_https: true
  cert_file: "/etc/ssl/certs/go-platform.crt"
  key_file: "/etc/ssl/private/go-platform.key"

database:
  driver: mysql
  host: localhost
  port: 3306
  username: go_platform
  password: "your-secure-password"
  database: go_platform
  max_open_conns: 100
  max_idle_conns: 10

jwt:
  secret: "your-super-secure-jwt-secret-key"
  access_token_expire: 3600
  refresh_token_expire: 604800

logger:
  level: info
  format: json
  output: file
  file_path: "/home/go-platform/app/logs/app.log"

security:
  password_hash_cost: 12
  max_login_attempts: 5
  enable_csrf: true
  enable_csp: true
```

### 4. 系统服务

创建 systemd 服务文件：

```bash
sudo vim /etc/systemd/system/go-platform.service
```

```ini
[Unit]
Description=Go Platform API Server
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=go-platform
Group=go-platform
WorkingDirectory=/home/go-platform/app
ExecStart=/home/go-platform/app/go-platform
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=go-platform
KillMode=mixed
KillSignal=SIGTERM

# 环境变量
Environment=GIN_MODE=release
Environment=CONFIG_PATH=/home/go-platform/app/config/config.yaml

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/go-platform/app/logs /home/go-platform/app/data

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start go-platform

# 设置开机自启
sudo systemctl enable go-platform

# 查看服务状态
sudo systemctl status go-platform

# 查看日志
sudo journalctl -u go-platform -f
```

### 5. Nginx 反向代理

安装 Nginx：

```bash
sudo apt install nginx
```

创建站点配置：

```bash
sudo vim /etc/nginx/sites-available/go-platform
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 配置
    ssl_certificate /etc/ssl/certs/go-platform.crt;
    ssl_certificate_key /etc/ssl/private/go-platform.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 日志
    access_log /var/log/nginx/go-platform.access.log;
    error_log /var/log/nginx/go-platform.error.log;
    
    # 限制请求大小
    client_max_body_size 10M;
    
    # 代理到应用
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # 静态文件
    location /static/ {
        alias /home/go-platform/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        access_log off;
    }
}
```

启用站点：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/go-platform /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 6. SSL 证书

使用 Let's Encrypt：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

## 云平台部署

### AWS 部署

#### 1. EC2 实例

```bash
# 创建 EC2 实例
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1d0 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx
```

#### 2. RDS 数据库

```bash
# 创建 RDS 实例
aws rds create-db-instance \
  --db-instance-identifier go-platform-db \
  --db-instance-class db.t3.micro \
  --engine mysql \
  --master-username admin \
  --master-user-password your-password \
  --allocated-storage 20
```

#### 3. 负载均衡器

```bash
# 创建应用负载均衡器
aws elbv2 create-load-balancer \
  --name go-platform-alb \
  --subnets subnet-xxxxxxxxx subnet-yyyyyyyyy \
  --security-groups sg-xxxxxxxxx
```

### Docker Swarm 部署

```bash
# 初始化 Swarm
docker swarm init

# 部署堆栈
docker stack deploy -c docker-compose.yml go-platform

# 查看服务
docker service ls

# 扩展服务
docker service scale go-platform_app=3
```

### Kubernetes 部署

创建 Kubernetes 配置文件：

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: go-platform

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: go-platform-config
  namespace: go-platform
data:
  config.yaml: |
    server:
      port: 8080
      mode: release
    database:
      driver: mysql
      host: mysql-service
      port: 3306
      username: go_platform
      database: go_platform

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: go-platform-secret
  namespace: go-platform
type: Opaque
data:
  db-password: eW91ci1wYXNzd29yZA==  # base64 encoded
  jwt-secret: eW91ci1qd3Qtc2VjcmV0  # base64 encoded

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-platform
  namespace: go-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: go-platform
  template:
    metadata:
      labels:
        app: go-platform
    spec:
      containers:
      - name: go-platform
        image: go-platform:latest
        ports:
        - containerPort: 8080
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: go-platform-secret
              key: db-password
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: go-platform-secret
              key: jwt-secret
        volumeMounts:
        - name: config
          mountPath: /app/config
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: go-platform-config

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: go-platform-service
  namespace: go-platform
spec:
  selector:
    app: go-platform
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: go-platform-ingress
  namespace: go-platform
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: go-platform-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: go-platform-service
            port:
              number: 80
```

部署到 Kubernetes：

```bash
# 应用配置
kubectl apply -f k8s/

# 查看部署状态
kubectl get pods -n go-platform
kubectl get services -n go-platform
kubectl get ingress -n go-platform

# 查看日志
kubectl logs -f deployment/go-platform -n go-platform
```

## 监控和日志

### 1. 应用日志

应用内置了结构化日志记录，支持多种日志级别和输出格式：

```yaml
# config.yaml
logging:
  level: info
  format: json
  output: file
  file_path: logs/app.log
  max_size: 100
  max_backups: 10
  max_age: 30
```

### 2. 健康检查

应用提供内置的健康检查端点：

```bash
# 检查应用健康状态
curl http://localhost:8080/health

# 检查就绪状态
curl http://localhost:8080/ready

# 获取应用指标
curl http://localhost:8080/metrics
```

### 3. 日志聚合

使用 ELK Stack：

```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
  
  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

## 备份和恢复

### 1. 数据库备份

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mysql"
DB_NAME="go_platform"
DB_USER="go_platform"
DB_PASS="your_password"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -u$DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/backup_$DATE.sql

# 删除 7 天前的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

### 2. 应用备份

```bash
#!/bin/bash
# app-backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/app"
APP_DIR="/home/go-platform/app"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份配置和数据
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
  -C $APP_DIR \
  config/ data/ logs/

echo "App backup completed: app_backup_$DATE.tar.gz"
```

### 3. 自动备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份数据库
0 2 * * * /home/go-platform/scripts/backup.sh

# 每周日凌晨 3 点备份应用
0 3 * * 0 /home/go-platform/scripts/app-backup.sh
```

## 故障排除

### 常见问题

#### 1. 应用无法启动

```bash
# 检查配置文件
go run cmd/server/main.go --config-check

# 检查端口占用
sudo netstat -tlnp | grep :8080

# 检查日志
sudo journalctl -u go-platform -n 50
```

#### 2. 数据库连接失败

```bash
# 测试数据库连接
mysql -h localhost -u go_platform -p go_platform

# 检查数据库服务
sudo systemctl status mysql

# 查看数据库日志
sudo tail -f /var/log/mysql/error.log
```

#### 3. 内存使用过高

```bash
# 查看内存使用
free -h
top -p $(pgrep go-platform)

# 生成内存分析
curl http://localhost:8080/debug/pprof/heap > heap.prof
go tool pprof heap.prof
```

#### 4. 性能问题

```bash
# CPU 分析
curl http://localhost:8080/debug/pprof/profile?seconds=30 > cpu.prof
go tool pprof cpu.prof

# 查看慢查询
mysql -u root -p -e "SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;"
```

### 日志分析

```bash
# 查看错误日志
grep "ERROR" /home/go-platform/app/logs/app.log | tail -20

# 统计 API 响应时间
awk '/"method":"GET"/ {print $0}' /home/go-platform/app/logs/app.log | \
  jq -r '.duration' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count "ms"}'

# 查看最频繁的错误
grep "ERROR" /home/go-platform/app/logs/app.log | \
  awk -F'"error":"' '{print $2}' | \
  awk -F'"' '{print $1}' | \
  sort | uniq -c | sort -nr | head -10
```

### 性能优化

#### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_models_type ON models(type);
CREATE INDEX idx_models_provider ON models(provider);

-- 分析查询性能
EXPLAIN SELECT * FROM users WHERE username = 'admin';
```

#### 2. 应用优化

```yaml
# config.yaml
database:
  max_open_conns: 100
  max_idle_conns: 10
  conn_max_lifetime: 3600

redis:
  pool_size: 20
  min_idle_conns: 5

rate_limit:
  requests_per_second: 1000
  burst: 2000
```

#### 3. 系统优化

```bash
# 调整文件描述符限制
echo "go-platform soft nofile 65536" >> /etc/security/limits.conf
echo "go-platform hard nofile 65536" >> /etc/security/limits.conf

# 调整内核参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

## 安全最佳实践

### 1. 系统安全

```bash
# 禁用 root 登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# 配置防火墙
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 安装 fail2ban
sudo apt install fail2ban
```

### 2. 应用安全

```yaml
# config.yaml
security:
  password_min_length: 12
  password_require_special: true
  max_login_attempts: 3
  login_lockout_duration: 1800
  enable_csrf: true
  enable_csp: true

jwt:
  secret: "use-a-very-long-and-random-secret-key"
  access_token_expire: 900  # 15 minutes
```

### 3. 数据库安全

```sql
-- 删除测试数据库
DROP DATABASE IF EXISTS test;

-- 删除匿名用户
DELETE FROM mysql.user WHERE User='';

-- 禁止远程 root 登录
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

FLUSH PRIVILEGES;
```

---

本部署指南涵盖了从开发环境到生产环境的完整部署流程。根据实际需求选择合适的部署方式，并定期更新和维护系统以确保安全性和稳定性。