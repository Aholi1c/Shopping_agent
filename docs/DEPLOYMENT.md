# 🚀 部署指南 (Deployment Guide)

本文档提供智能购物助手 LLM Agent 的完整部署指南，涵盖开发环境、生产环境和容器化部署。

## 📋 目录

- [环境要求](#环境要求)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker容器化部署](#docker容器化部署)
- [云平台部署](#云平台部署)
- [监控和日志](#监控和日志)
- [安全配置](#安全配置)
- [性能优化](#性能优化)
- [故障排除](#故障排除)

## 🖥️ 环境要求

### 系统要求
- **操作系统**: Linux (Ubuntu 20.04+), macOS 10.15+, Windows 10+
- **Python**: 3.8+ (推荐 3.9+)
- **Node.js**: 16+ (推荐 18+)
- **内存**: 最少 4GB RAM (推荐 8GB+)
- **存储**: 最少 10GB 可用空间
- **网络**: 稳定的互联网连接

### 依赖服务
- **Redis**: 6.0+ (可选，用于缓存)
- **数据库**: SQLite (开发) / PostgreSQL/MySQL (生产)
- **反向代理**: Nginx (生产环境推荐)

## 🛠️ 开发环境部署

### 1. 克隆项目
```bash
git clone https://github.com/your-repo/llm-agent.git
cd llm-agent
```

### 2. 后端环境配置
```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置API密钥等参数
```

### 3. 前端环境配置
```bash
# 进入前端目录
cd ../frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置API地址等参数
```

### 4. 数据库初始化
```bash
# 回到后端目录
cd ../backend

# 运行数据库迁移
python -m alembic upgrade head

# 初始化基础数据
python scripts/init_data.py
```

### 5. 启动开发服务器
```bash
# 启动后端服务
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 启动前端服务 (新终端)
cd frontend
npm start
```

### 6. 验证部署
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8001
- API文档: http://localhost:8001/docs
- 健康检查: http://localhost:8001/health

## 🏭 生产环境部署

### 1. 服务器准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y python3-pip nodejs npm nginx postgresql redis-server

# 安装Python虚拟环境
sudo apt install -y python3-venv
```

### 2. 数据库配置 (PostgreSQL)
```bash
# 创建数据库和用户
sudo -u postgres createdb llm_agent
sudo -u postgres createuser llm_user

# 设置密码
sudo -u postgres psql
ALTER USER llm_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE llm_agent TO llm_user;
\q
```

### 3. 后端部署
```bash
# 创建应用目录
sudo mkdir -p /opt/llm-agent
sudo chown $USER:$USER /opt/llm-agent

# 复制代码
cp -r backend /opt/llm-agent/
cd /opt/llm-agent/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 配置环境变量
sudo nano /etc/environment
# 添加:
# DATABASE_URL=postgresql://llm_user:your_password@localhost/llm_agent
# SECRET_KEY=your_production_secret_key
# REDIS_URL=redis://localhost:6379/0
```

### 4. 前端构建
```bash
# 在开发机器上构建
cd frontend
npm run build

# 复制构建文件到服务器
scp -r build/* user@server:/opt/llm-agent/frontend/
```

### 5. 配置Gunicorn服务
```bash
# 创建服务文件
sudo nano /etc/systemd/system/llm-agent.service

[Unit]
Description=LLM Agent Backend Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/llm-agent/backend
Environment=PATH=/opt/llm-agent/backend/venv/bin
ExecStart=/opt/llm-agent/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
Restart=always

[Install]
WantedBy=multi-user.target

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable llm-agent
sudo systemctl start llm-agent
```

### 6. 配置Nginx
```bash
# 创建Nginx配置
sudo nano /etc/nginx/sites-available/llm-agent

server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /opt/llm-agent/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/llm-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. SSL证书配置 (Let's Encrypt)
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🐳 Docker容器化部署

### 1. 创建Dockerfile (后端)
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001"]
```

### 2. 创建Dockerfile (前端)
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产环境
FROM nginx:alpine

# 复制构建文件
COPY --from=build /app/build /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3. 创建docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://llm_user:your_password@db:5432/llm_agent
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your_production_secret_key
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=llm_agent
      - POSTGRES_USER=llm_user
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

### 4. 部署命令
```bash
# 构建和启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 更新服务
docker-compose pull
docker-compose up -d --force-recreate
```

## ☁️ 云平台部署

### AWS部署
```bash
# 使用ECS部署
aws ecs create-cluster --cluster-name llm-agent

# 构建并推送镜像到ECR
aws ecr create-repository --repository-name llm-agent
docker build -t llm-agent .
docker tag llm-agent:latest aws_account_id.dkr.ecr.region.amazonaws.com/llm-agent:latest
docker push aws_account_id.dkr.ecr.region.amazonaws.com/llm-agent:latest

# 部署到ECS
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster llm-agent --service-name llm-agent-service --task-definition llm-agent --desired-count 2
```

### 阿里云部署
```bash
# 使用容器服务部署
aliyun cs POST /clusters --header "Content-Type=application/json" --body "$(cat cluster.json)"

# 部署应用
aliyun cs POST /clusters/[cluster_id]/applications --header "Content-Type=application/json" --body "$(cat application.json)"
```

### 腾讯云部署
```bash
# 使用TKE部署
kubectl create namespace llm-agent
kubectl apply -f k8s/
```

## 📊 监控和日志

### 1. 应用监控
```bash
# 安装监控工具
pip install prometheus-client grafana

# 配置Prometheus
# 创建 prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'llm-agent'
    static_configs:
      - targets: ['localhost:8001']
```

### 2. 日志管理
```bash
# 配置日志轮转
sudo nano /etc/logrotate.d/llm-agent

/opt/llm-agent/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### 3. 性能监控
```python
# 在应用中添加监控端点
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

@app.get("/metrics")
def metrics():
    return generate_latest()
```

## 🔒 安全配置

### 1. 防火墙配置
```bash
# 配置UFW防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 安全加固
```bash
# 限制文件权限
sudo chmod 600 /opt/llm-agent/backend/.env
sudo chmod 600 /etc/nginx/ssl/*

# 配置fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. 数据库安全
```sql
-- 创建只读用户
CREATE USER readonly_user WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE llm_agent TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

## ⚡ 性能优化

### 1. 缓存配置
```python
# Redis缓存配置
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
}
```

### 2. 数据库优化
```sql
-- 添加索引
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_memories_user_id ON memories(user_id);

-- 查询优化
EXPLAIN ANALYZE SELECT * FROM conversations WHERE user_id = 1;
```

### 3. 前端优化
```javascript
// 配置CDN
const CDN_CONFIG = {
  baseURL: 'https://cdn.your-domain.com',
  version: '2.2.0'
};

// 启用gzip压缩
const compression = require('compression');
app.use(compression());
```

## 🛠️ 故障排除

### 常见问题
1. **服务启动失败**
   ```bash
   # 检查日志
   sudo journalctl -u llm-agent -f

   # 检查端口占用
   sudo netstat -tulpn | grep :8001

   # 检查配置
   sudo nginx -t
   ```

2. **数据库连接问题**
   ```bash
   # 检查数据库状态
   sudo systemctl status postgresql

   # 测试连接
   psql -h localhost -U llm_user -d llm_agent
   ```

3. **内存不足**
   ```bash
   # 检查内存使用
   free -h

   # 优化Gunicorn配置
   gunicorn app.main:app -w 2 --threads 4 --max-requests 1000 --max-requests-jitter 50
   ```

### 性能调优
```bash
# 监控系统资源
htop
iotop

# 分析日志
tail -f /opt/llm-agent/logs/app.log | grep ERROR

# 数据库查询分析
sudo -u postgres psql -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

## 🔄 升级和维护

### 版本升级
```bash
# 备份数据库
pg_dump llm_agent > backup_$(date +%Y%m%d).sql

# 更新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade
npm update

# 运行迁移
python -m alembic upgrade head

# 重启服务
sudo systemctl restart llm-agent
```

### 日常维护
```bash
# 清理日志
find /opt/llm-agent/logs -name "*.log" -mtime +30 -delete

# 数据库维护
sudo -u postgres vacuumdb --analyze --full llm_agent

# 系统更新
sudo apt update && sudo apt upgrade -y
```

---