# 🚀 智能购物助手启动指南

本文档详细介绍了如何启动和运行智能购物助手 LLM Agent。

## 📋 目录

- [环境要求](#环境要求)
- [快速启动](#快速启动)
- [详细配置](#详细配置)
- [启动步骤](#启动步骤)
- [验证部署](#验证部署)
- [常见问题](#常见问题)
- [高级配置](#高级配置)

## 🔧 环境要求

### 必需软件
- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本
- **npm**: 8.0 或更高版本

### 推荐软件
- **Redis**: 用于缓存和会话管理 (可选)
- **Git**: 用于代码管理

### 检查环境
```bash
# 检查 Python 版本
python --version
# 或者
python3 --version

# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version
```

## 🚀 快速启动

### 方式一：使用自动启动脚本 (推荐)

我们提供了便捷的启动脚本，支持多种模型提供商：

```bash
# 1. 进入项目目录
cd /path/to/llm-agent

# 2. 赋予脚本执行权限
chmod +x cc_bigmodel.sh

# 3. 运行启动脚本
./cc_bigmodel.sh
```

脚本会自动：
- 检查和安装 Node.js
- 安装项目依赖
- 配置环境变量
- 启动前后端服务

### 方式二：手动启动

## 📝 详细配置

### 1. 获取 API 密钥

#### OpenAI 配置
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册并登录账户
3. 进入 API Keys 页面
4. 创建新的 API 密钥

#### BigModel 配置
1. 访问 [BigModel Platform](https://open.bigmodel.cn/)
2. 注册并登录账户
3. 进入 API 密钥管理
4. 创建 API 密钥

### 2. 配置后端环境

```bash
# 进入后端目录
cd backend

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
nano .env
```

在 `.env` 文件中设置：

```bash
# OpenAI 配置示例
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 或 BigModel 配置示例
LLM_PROVIDER=bigmodel
BIGMODEL_API_KEY=your-bigmodel-api-key

# 通用配置
DATABASE_URL=sqlite:///./llm_agent.db
SECRET_KEY=your-secret-key-here
REDIS_URL=redis://localhost:6379/0
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./vector_store
```

### 3. 配置前端环境

```bash
# 进入前端目录
cd frontend

# 创建环境变量文件
echo "REACT_APP_API_URL=http://localhost:8000" > .env
echo "REACT_APP_LLM_PROVIDER=bigmodel" >> .env
```

## 🛠️ 启动步骤

### 步骤 1：安装依赖

```bash
# 安装 Python 依赖
cd backend
pip install -r requirements.txt

# 安装 Node.js 依赖
cd ../frontend
npm install
```

### 步骤 2：启动后端服务

```bash
# 进入后端目录
cd backend

# 启动 FastAPI 服务器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或者使用后台运行：

```bash
# 后台运行
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

### 步骤 3：启动前端服务

```bash
# 进入前端目录
cd frontend

# 启动 React 开发服务器
npm start
```

### 步骤 4：验证服务

#### 检查后端服务
```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 查看 API 文档
open http://localhost:8000/docs
```

#### 检查前端服务
```bash
# 访问前端界面
open http://localhost:3000
```

## ✅ 验证部署

### 1. 服务状态检查

#### 后端服务
```bash
# 检查端口是否在监听
lsof -i :8000

# 测试健康检查端点
curl http://localhost:8000/health
```

期望响应：
```json
{
  "status": "healthy",
  "timestamp": "2024-09-26T10:00:00Z",
  "version": "2.3.0"
}
```

#### 前端服务
```bash
# 检查端口是否在监听
lsof -i :3000

# 测试前端响应
curl -I http://localhost:3000
```

### 2. 功能测试

#### 基础对话测试
1. 打开浏览器访问 http://localhost:3000
2. 在聊天界面输入测试消息："你好"
3. 验证 AI 是否正常回复

#### 文件上传测试
1. 点击上传按钮
2. 选择一张测试图片
3. 验证图片是否正常上传和识别

#### 高级功能测试
1. 点击"高级设置"按钮
2. 启用记忆系统或 RAG 功能
3. 验证功能是否正常工作

## 🛠️ 常见问题

### 端口冲突问题

#### 问题症状
```
Error: listen EADDRINUSE :::3000
Error: listen EADDRINUSE :::8000
```

#### 解决方案
```bash
# 查找占用端口的进程
lsof -i :3000  # 前端端口
lsof -i :8000  # 后端端口

# 终止占用进程
kill -9 <PID>

# 或者更改端口
# 后端端口更改
cd backend
python -m uvicorn app.main:app --reload --port 8001

# 前端端口更改
cd frontend
echo "PORT=3001" >> .env
npm start
```

### 依赖安装问题

#### Python 依赖问题
```bash
# 清除 pip 缓存
pip cache purge

# 升级 pip
pip install --upgrade pip

# 重新安装依赖
cd backend
pip install -r requirements.txt --force-reinstall
```

#### Node.js 依赖问题
```bash
# 清除 npm 缓存
npm cache clean --force

# 删除 node_modules 和 package-lock.json
cd frontend
rm -rf node_modules package-lock.json

# 重新安装依赖
npm install
```

### API 密钥问题

#### 问题症状
```
API key is invalid or expired
Authentication failed
```

#### 解决方案
1. 检查 `.env` 文件中的 API 密钥是否正确
2. 验证 API 密钥是否有效
3. 确保网络连接正常
4. 检查 API 密钥权限设置

### 权限问题

#### 脚本执行权限
```bash
# 赋予执行权限
chmod +x cc_bigmodel.sh
chmod +x cc_deepseek.sh
chmod +x cc_moonshot.sh
chmod +x cc_siliconflow.sh
chmod +x cc_modelscope.sh
```

#### 文件权限
```bash
# 修复文件权限
chmod 755 -R backend/
chmod 755 -R frontend/
chmod 644 backend/.env
chmod 644 frontend/.env
```

### 环境变量问题

#### 检查环境变量
```bash
# 查看当前环境变量
env

# 检查特定环境变量
echo $LLM_PROVIDER
echo $OPENAI_API_KEY
echo $BIGMODEL_API_KEY
```

#### 重新加载环境变量
```bash
# 重新加载 shell 配置
source ~/.bashrc
# 或者
source ~/.zshrc

# 重新启动服务
```

## 🔧 高级配置

### Redis 配置 (可选)

#### 安装 Redis
```bash
# macOS (使用 Homebrew)
brew install redis

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server

# 启动 Redis
redis-server --daemonize yes
```

#### 配置 Redis
在 `backend/.env` 文件中添加：
```bash
REDIS_URL=redis://localhost:6379/0
```

### 数据库配置

#### SQLite 配置
```bash
# 数据库文件路径
DATABASE_URL=sqlite:///./llm_agent.db
```

#### PostgreSQL 配置 (可选)
```bash
# 安装 PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb llm_agent

# 配置连接
DATABASE_URL=postgresql://username:password@localhost/llm_agent
```

### 向量数据库配置

#### FAISS 配置
```bash
# 向量数据库路径
VECTOR_DB_PATH=./vector_store

# 嵌入模型
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 日志配置

#### 后端日志
```bash
# 启动时指定日志级别
python -m uvicorn app.main:app --reload --log-level info

# 输出日志到文件
python -m uvicorn app.main:app --reload > backend.log 2>&1 &
```

#### 前端日志
```bash
# 查看构建日志
npm start --verbose

# 查看错误日志
npm start 2>&1 | tee frontend.log
```

## 📊 性能优化

### 后端优化
```bash
# 启用多进程
python -m uvicorn app.main:app --reload --workers 4

# 调整超时时间
python -m uvicorn app.main:app --reload --timeout 60
```

### 前端优化
```bash
# 启用压缩
npm run build
serve -s build -l 3000

# 启用缓存
npm start -- --cache
```

## 🔒 安全配置

### 环境变量安全
```bash
# 设置文件权限
chmod 600 backend/.env
chmod 600 frontend/.env

# 添加到 .gitignore
echo ".env" >> .gitignore
```

### API 安全
```bash
# 启用 HTTPS
python -m uvicorn app.main:app --reload --ssl-keyfile key.pem --ssl-certfile cert.pem

# 设置访问控制
export ALLOWED_HOSTS=localhost,127.0.0.1
```
