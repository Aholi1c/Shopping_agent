# 🚀 快速启动指南

## 后端服务启动

### 方式一：使用Python启动脚本（推荐）

```bash
cd /path/to/llm-agent
python3 start_agent.py
```

**或者使用bash脚本（仅限macOS/Linux）**：
```bash
chmod +x start_backend.sh
./start_backend.sh
```

### 方式二：手动启动

```bash
# 1. 进入项目目录
cd /Users/xinyizhu/Downloads/claude-mirror/cc-mirror/llm-agent

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖（如果还未安装）
pip install -r backend/requirements.txt

# 4. 创建必要目录
mkdir -p backend/uploads/images backend/uploads/documents backend/vector_store logs

# 5. 初始化数据库
cd backend
python -c "
from app.core.database import engine
from app.models.models import Base
from app.models.ecommerce_models import Base as EcommerceBase
Base.metadata.create_all(bind=engine)
EcommerceBase.metadata.create_all(bind=engine)
print('✅ 数据库初始化完成')
"

# 6. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方式三：使用原有的启动脚本

```bash
cd /Users/xinyizhu/Downloads/claude-mirror/cc-mirror/llm-agent
chmod +x start_agent.sh
./start_agent.sh
```

## ✅ 验证服务是否启动成功

服务启动后，您应该能看到类似以下的输出：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 测试服务

在浏览器中访问：

1. **健康检查**: http://localhost:8000/health
   - 应该返回: `{"status": "healthy", "service": "LLM Agent API"}`

2. **API文档**: http://localhost:8000/docs
   - 应该看到 Swagger UI 文档界面

3. **根路径**: http://localhost:8000/
   - 应该返回 API 基本信息

### 使用curl测试

```bash
# 健康检查
curl http://localhost:8000/health

# 根路径
curl http://localhost:8000/

# 聊天接口
curl -X POST http://localhost:8000/api/chat/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

## 🔧 常见问题

### 问题1: ModuleNotFoundError

如果遇到模块未找到的错误：

```bash
# 激活虚拟环境
source venv/bin/activate

# 重新安装依赖
pip install -r backend/requirements.txt
```

### 问题2: 端口被占用

如果8000端口被占用：

```bash
# 查找占用端口的进程
lsof -i :8000

# 停止进程
kill -9 <PID>

# 或者修改端口
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 问题3: faiss导入失败

如果遇到faiss导入问题：

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 安装faiss
pip install faiss-cpu

# 如果还有问题，尝试
pip install faiss-cpu --force-reinstall
```

### 问题4: 数据库错误

如果遇到数据库相关错误：

```bash
# 删除旧数据库（注意：会丢失数据）
rm backend/llm_agent.db

# 重新初始化
cd backend
python -c "
from app.core.database import engine
from app.models.models import Base
from app.models.ecommerce_models import Base as EcommerceBase
Base.metadata.create_all(bind=engine)
EcommerceBase.metadata.create_all(bind=engine)
"
```

## 📝 配置说明

### .env 文件配置

确保 `backend/.env` 文件存在并配置了必要的API密钥：

```bash
# LLM配置（至少配置一个）
LLM_PROVIDER=bigmodel  # 或 openai, azure
BIGMODEL_API_KEY=your_api_key_here

# 或使用OpenAI
# OPENAI_API_KEY=your_openai_api_key

# 数据库配置
DATABASE_URL=sqlite:///./llm_agent.db

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 🎯 下一步

服务启动成功后，您可以：

1. **测试API**: 访问 http://localhost:8000/docs 查看API文档
2. **启动前端**: 如果需要，可以启动前端服务
3. **安装浏览器插件**: 安装 `browser-extension` 目录中的插件
4. **测试功能**: 使用各种API端点测试功能

---

**提示**: 如果遇到问题，请查看终端的错误信息，或查看 `logs/` 目录中的日志文件。

