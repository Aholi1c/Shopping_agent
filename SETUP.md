# 🚀 LLM Agent 智能购物助手配置指南

本文档提供了llm-agent项目的完整配置指南，包括API密钥配置、数据集准备、环境设置等必要步骤。

## 📋 目录

1. [环境要求](#环境要求)
2. [API密钥配置](#api密钥配置)
3. [数据集准备](#数据集准备)
4. [环境变量设置](#环境变量设置)
5. [数据库配置](#数据库配置)
6. [服务启动](#服务启动)
7. [验证配置](#验证配置)
8. [常见问题](#常见问题)

## 🖥️ 环境要求

### 系统要求
- **操作系统**: Linux (Ubuntu 20.04+) / macOS 10.15+ / Windows 10+
- **Python**: 3.8+
- **Node.js**: 16+
- **内存**: 最低4GB，推荐8GB+
- **存储**: 最低20GB可用空间

### 软件依赖
- Redis (可选，用于缓存)
- PostgreSQL (可选，生产环境推荐)
- Docker (可选，用于容器化部署)

## 🔑 API密钥配置

### 1. 模型服务商选择

系统支持多种模型提供商，需要至少配置一个：

#### 选项A: OpenAI
```bash
# 访问 https://platform.openai.com/api-keys 获取API密钥
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_PROVIDER=openai
```

#### 选项B: BigModel (智谱AI)
```bash
# 访问 https://open.bigmodel.cn/ 获取API密钥
BIGMODEL_API_KEY=your-bigmodel-text-api-key
BIGMODEL_VLM_API_KEY=your-bigmodel-vision-api-key
LLM_PROVIDER=bigmodel
```

#### 选项C: DeepSeek
```bash
# 访问 https://platform.deepseek.com/ 获取API密钥
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
LLM_PROVIDER=deepseek
```

#### 选项D: Moonshot (月之暗面)
```bash
# 访问 https://platform.moonshot.cn/ 获取API密钥
MOONSHOT_API_KEY=sk-your-moonshot-api-key-here
LLM_PROVIDER=moonshot
```

### 2. 其他API服务 (可选)

#### Anthropic API (用于Claude模型)
```bash
# 如果需要使用Claude模型
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

#### Azure OpenAI (可选)
```bash
# 如果使用Azure OpenAI服务
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_API_VERSION=2024-02-15-preview
```

## 📊 数据集准备

### 1. 向量数据库初始化

系统会自动创建向量数据库，但可以提供初始数据：

#### 创建向量存储目录
```bash
# 在项目根目录创建
mkdir -p vector_store/faiss
mkdir -p vector_store/chroma
mkdir -p data/documents
mkdir -p data/knowledge_base
```

#### 可选：上传初始知识库文件
```bash
# 支持的文件格式：PDF, DOCX, Markdown, HTML, TXT
data/knowledge_base/
├── 产品手册.pdf
├── 技术文档.docx
├── 使用指南.md
└── 常见问题.html
```

### 2. 购物助手数据准备

#### 价格历史数据 (可选)
如果已有价格历史数据，可以上传到：
```bash
data/price_history/
├── 电子产品/
│   ├── 手机/
│   └── 电脑/
├── 服装/
└── 家居/
```

#### 风险关键词库
系统会自动初始化基础关键词库，您可以扩展：
```bash
data/risk_keywords/
├── quality_keywords.json      # 质量相关关键词
├── logistics_keywords.json   # 物流相关关键词
├── service_keywords.json      # 售后服务关键词
└── fraud_keywords.json        # 欺诈相关关键词
```

## ⚙️ 环境变量设置

### 1. 后端配置文件

复制并编辑配置文件：
```bash
cd backend
cp .env.example .env
```

#### 完整的 `.env` 配置示例：

```env
# === 模型提供商配置 (选择一个) ===
# OpenAI配置
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1

# BigModel配置
# LLM_PROVIDER=bigmodel
# BIGMODEL_API_KEY=your-bigmodel-key
# BIGMODEL_VLM_API_KEY=your-bigmodel-vision-key

# === 数据库配置 ===
# SQLite (开发环境)
DATABASE_URL=sqlite:///./llm_agent.db

# PostgreSQL (生产环境)
# DATABASE_URL=postgresql://username:password@localhost/llm_agent

# Redis配置 (可选)
REDIS_URL=redis://localhost:6379/0

# === 应用配置 ===
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=true
HOST=0.0.0.0
PORT=8000

# === 文件存储配置 ===
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760  # 10MB

# === 向量数据库配置 ===
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./vector_store
VECTOR_DB_TYPE=faiss

# === RAG配置 ===
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5

# === 购物助手配置 ===
ENABLE_SHOPPING_ASSISTANT=true
PRICE_PREDICTION_DAYS=30
RISK_ANALYSIS_THRESHOLD=0.7

# === 日志配置 ===
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### 2. 前端配置文件

```bash
cd frontend
cp .env.example .env.local
```

#### `.env.local` 配置示例：
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## 🗄️ 数据库配置

### 1. SQLite (默认，开发环境)

系统会自动创建SQLite数据库，无需额外配置。

### 2. PostgreSQL (生产环境推荐)

#### 安装PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# 启动服务
sudo systemctl start postgresql
```

#### 创建数据库
```bash
# 切换到postgres用户
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE llm_agent;
CREATE USER llm_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE llm_agent TO llm_user;
\q
```

#### 更新环境变量
```env
DATABASE_URL=postgresql://llm_user:your_password@localhost/llm_agent
```

### 3. 数据库初始化

```bash
cd backend
# 创建所有表
python -c "from app.core.database import engine; from app.models.models import Base; Base.metadata.create_all(bind=engine)"

# 可选：运行数据迁移
python scripts/migrate.py
```

## 🚀 服务启动

### 1. 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动Redis (可选)
redis-server --daemonize yes

# 启动后端服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

### 3. Docker启动 (可选)

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

## ✅ 验证配置

### 1. 后端健康检查

```bash
# 检查API服务状态
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

### 2. 前端访问

打开浏览器访问：http://localhost:3000

### 3. 功能测试

#### 测试基本对话功能
1. 在前端界面输入消息
2. 验证AI回复是否正常
3. 检查WebSocket连接状态

#### 测试购物助手功能
1. 进入购物助手标签页
2. 测试商品搜索功能
3. 验证价格预测功能
4. 测试风险分析功能

#### 测试多模态功能
1. 上传测试图片
2. 验证图像识别功能
3. 测试语音输入（如果支持）

## 🐛 常见问题

### 1. API密钥相关

#### 问题：OpenAI API调用失败
```bash
# 错误信息：AuthenticationError
# 解决方案：
1. 检查OPENAI_API_KEY是否正确
2. 验证API密钥是否有效
3. 确认账户余额充足
4. 检查网络连接
```

#### 问题：BigModel API调用失败
```bash
# 解决方案：
1. 确认BIGMODEL_API_KEY格式正确
2. 检查API密钥权限
3. 验证模型选择是否正确
```

### 2. 数据库相关

#### 问题：数据库连接失败
```bash
# 解决方案：
1. 检查数据库服务是否启动
2. 验证连接字符串格式
3. 确认用户权限设置
4. 检查防火墙设置
```

#### 问题：向量数据库初始化失败
```bash
# 解决方案：
1. 检查vector_store目录权限
2. 确认磁盘空间充足
3. 重新安装依赖：pip install -r requirements.txt
```

### 3. 依赖相关

#### 问题：Python包安装失败
```bash
# 解决方案：
1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

2. 升级pip
pip install --upgrade pip

3. 清理缓存
pip cache purge

4. 重新安装
pip install -r requirements.txt
```

#### 问题：Node.js依赖安装失败
```bash
# 解决方案：
1. 清理node_modules
rm -rf node_modules package-lock.json

2. 重新安装
npm install

3. 使用淘宝镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### 4. 性能优化

#### 问题：响应速度慢
```bash
# 解决方案：
1. 启用Redis缓存
2. 优化数据库索引
3. 使用更快的embedding模型
4. 增加服务器内存
```

#### 问题：内存占用高
```bash
# 解决方案：
1. 限制向量数据库大小
2. 定期清理旧数据
3. 使用分片处理
4. 优化模型参数
```

## 🔧 高级配置

### 1. 自定义模型配置

```env
# 使用自定义embedding模型
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 自定义LLM模型
CUSTOM_LLM_MODEL=gpt-4-turbo-preview
CUSTOM_LLM_TEMPERATURE=0.7
CUSTOM_LLM_MAX_TOKENS=2000
```

### 2. 安全配置

```env
# 启用API密钥验证
API_KEY_REQUIRED=true

# 设置CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# 启用HTTPS
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### 3. 监控配置

```env
# 启用性能监控
ENABLE_MONITORING=true

# 日志级别
LOG_LEVEL=DEBUG

# 错误追踪
SENTRY_DSN=your-sentry-dsn
```

---
