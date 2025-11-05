# 📖 智能购物助手 LLM Agent - 完整使用指南

## 📋 目录

1. [系统要求](#系统要求)
2. [环境准备](#环境准备)
3. [配置说明](#配置说明)
4. [启动服务](#启动服务)
5. [浏览器扩展安装](#浏览器扩展安装)
6. [使用指南](#使用指南)
7. [常见问题](#常见问题)
8. [故障排查](#故障排查)

---

## 系统要求

### 基础要求
- **操作系统**: macOS、Linux 或 Windows
- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本（仅前端需要）
- **浏览器**: Chrome/Edge 88+ 或 Firefox 109+（用于浏览器扩展）

### 推荐配置
- **内存**: 4GB 或更多
- **存储**: 至少 2GB 可用空间
- **网络**: 稳定的互联网连接（用于API调用）

---

## 环境准备

### 1. 克隆或下载项目

```bash
# 如果项目已存在，进入项目目录
cd /path/to/llm-agent
```

### 2. 创建Python虚拟环境

```bash
# 在项目根目录创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. 安装Python依赖

```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

**注意**: 某些依赖是可选的，如果安装失败，核心功能仍可运行：
- `faiss-cpu`: 向量搜索（可选，但推荐安装）
- `sentence-transformers`: 文本嵌入（可选，但推荐安装）
- `celery`: 异步任务（可选）
- `feedparser`: RSS订阅（可选）
- `PIL`: 图像处理（可选）

### 4. 安装前端依赖（可选，如果使用React前端）

```bash
cd frontend
npm install
```

---

## 配置说明

### 1. 创建环境变量文件

在 `backend` 目录下创建 `.env` 文件：

```bash
cd backend
cp .env.example .env  # 如果存在示例文件
# 或者直接创建新文件
touch .env
```

### 2. 配置LLM提供商

系统支持多种LLM提供商，您需要选择其中一个进行配置。

#### 选项1: BigModel (GLM-4) - 推荐

这是默认配置，适合中文场景。

```bash
# .env 文件内容
LLM_PROVIDER=bigmodel
BIGMODEL_API_KEY=your_bigmodel_api_key_here
BIGMODEL_VLM_API_KEY=your_bigmodel_vlm_api_key_here  # 可选，用于图像分析
BIGMODEL_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

**获取API密钥**:
1. 访问 [BigModel开放平台](https://open.bigmodel.cn/)
2. 注册账号并创建应用
3. 获取API密钥

#### 选项2: OpenAI

```bash
# .env 文件内容
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

#### 选项3: Azure OpenAI

```bash
# .env 文件内容
LLM_PROVIDER=azure
AZURE_ENDPOINT=https://your-resource.openai.azure.com
AZURE_API_KEY=your_azure_api_key_here
AZURE_DEPLOYMENT=your_deployment_name
AZURE_API_VERSION=2025-01-01-preview
```

### 3. 配置数据库

默认使用SQLite，无需额外配置：

```bash
# .env 文件内容（默认值，通常不需要修改）
DATABASE_URL=sqlite:///./llm_agent.db
```

### 4. 配置向量数据库（可选）

如果安装了 `faiss-cpu`，可以使用向量搜索：

```bash
# .env 文件内容
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=./vector_store
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 5. 配置第三方API（可选）

#### Onebound API (万邦API) - 用于商品数据获取

```bash
# .env 文件内容
ONEBOUND_API_KEY=your_onebound_api_key
ONEBOUND_API_SECRET=your_onebound_api_secret
ONEBOUND_API_BASE_URL=https://api-gw.onebound.cn
```

**注意**: 如果不配置Onebound API，系统会使用静态数据库（需要上传商品数据）。

#### 平台API（可选）

```bash
# .env 文件内容
JD_API_KEY=your_jd_api_key
JD_API_SECRET=your_jd_api_secret
TAOBAO_API_KEY=your_taobao_api_key
TAOBAO_API_SECRET=your_taobao_api_secret
PDD_API_KEY=your_pdd_api_key
PDD_API_SECRET=your_pdd_api_secret
```

### 6. 其他配置

```bash
# .env 文件内容
# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=True

# 安全配置
SECRET_KEY=your-secret-key-change-this-in-production

# 文件上传配置
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760  # 10MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

---

## 启动服务

### 方式一：手动启动（开发环境）

#### 1. 启动后端服务

```bash
# 进入后端目录
cd backend

# 激活虚拟环境（如果还没有激活）
source ../venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 启动服务
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**参数说明**:
- `--host 0.0.0.0`: 监听所有网络接口
- `--port 8000`: 服务端口
- `--reload`: 开发模式，代码修改自动重载

#### 2. 验证服务启动

打开浏览器访问：
- **欢迎页面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 方式二：使用Python启动脚本（推荐）

```bash
# 直接运行Python启动脚本（跨平台支持）
python3 start_agent.py
```

**或者使用bash脚本（仅限macOS/Linux）**：
```bash
chmod +x start_backend.sh
./start_backend.sh
```

### 方式三：后台运行（生产环境）

```bash
# 使用nohup在后台运行
cd backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &

# 查看日志
tail -f ../logs/backend.log

# 停止服务
pkill -f "uvicorn app.main:app"
```

---

## 浏览器扩展安装

### 1. 准备扩展文件

扩展文件位于 `browser-extension/` 目录。

### 2. 加载扩展（Chrome/Edge）

1. 打开Chrome浏览器
2. 访问 `chrome://extensions/`
3. 开启"开发者模式"（右上角开关）
4. 点击"加载已解压的扩展程序"
5. 选择 `browser-extension/` 目录
6. 扩展安装完成

### 3. 加载扩展（Firefox）

1. 打开Firefox浏览器
2. 访问 `about:debugging`
3. 点击"此 Firefox"
4. 点击"临时载入附加组件"
5. 选择 `browser-extension/manifest.json`
6. 扩展安装完成

### 4. 验证扩展安装

1. 访问任意购物网站（如京东、淘宝）
2. 点击浏览器工具栏的扩展图标
3. 应该能看到扩展的侧边栏或弹出窗口

---

## 使用指南

### 1. 基础聊天功能

#### 通过浏览器扩展
1. 打开任意网页
2. 点击扩展图标，打开侧边栏
3. 在聊天界面输入问题
4. 点击发送或按Enter键
5. 等待AI回答

#### 通过API
```bash
curl -X POST "http://localhost:8000/api/chat/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "给我推荐一款7000元左右的iPhone手机",
    "use_memory": true,
    "use_rag": false,
    "model": "glm-4-0520"
  }'
```

### 2. 商品分析功能

#### 使用步骤
1. 访问购物网站（京东、淘宝、拼多多、Amazon等）
2. 打开商品详情页
3. 点击扩展图标，打开侧边栏
4. 切换到"分析"标签
5. 点击"分析商品"按钮
6. 等待分析完成，查看结果

#### 分析内容
- **商品概述**: 基于商品描述和参数的综合概述
- **价格分析**: 当前价格评估和多平台价格对比
- **风险评估**: 风险等级和风险详情
- **购买建议**: 立即购买/等待降价/谨慎考虑
- **注意事项**: 特别提醒（如货币类型、汇率转换）

### 3. 价格对比功能

#### 使用步骤
1. 打开浏览器扩展侧边栏
2. 切换到"比价"标签
3. 输入商品名称（如"iPhone 15 Pro"）
4. 点击"搜索"按钮
5. 查看价格对比结果

#### 对比结果
- **各平台价格**: 显示jd、taobao、pdd等平台的价格
- **最低价/最高价**: 价格范围
- **价格差异**: 价格差和节省百分比
- **最佳平台**: 推荐最优惠的平台
- **商品链接**: 可以直接点击查看商品

### 4. 价格追踪功能

#### 使用步骤
1. 打开浏览器扩展侧边栏
2. 切换到"追踪"标签
3. 输入目标价格
4. 点击"开始追踪"
5. 系统会在价格达到目标时提醒

### 5. 上传商品数据（静态数据库）

#### 准备数据文件
创建 `products_data.json` 文件，格式如下：

```json
{
  "products": [
    {
      "platform": "jd",
      "product_id": "100012043978",
      "title": "Apple iPhone 15 Pro 256GB 原色钛金属",
      "price": 7999.0,
      "original_price": 8999.0,
      "discount_rate": 11.1,
      "category": "手机",
      "brand": "Apple",
      "description": "商品描述...",
      "image_url": "https://example.com/image.jpg",
      "product_url": "https://item.jd.com/100012043978.html",
      "rating": 4.8,
      "review_count": 1250,
      "sales_count": 5000,
      "stock_status": "有货",
      "specs": {
        "存储容量": "256GB",
        "屏幕尺寸": "6.1英寸"
      }
    }
  ]
}
```

#### 上传数据
```bash
# 使用提供的上传脚本
python3 upload_products.py products_data.json

# 或使用curl
curl -X POST "http://localhost:8000/api/product-management/products/upload" \
  -H "Content-Type: application/json" \
  -d @products_data.json
```

### 6. 查看API文档

访问 http://localhost:8000/docs 查看完整的API文档，包括：
- 所有可用的API端点
- 请求和响应格式
- 直接在浏览器中测试API

---

## 常见问题

### Q1: 服务启动失败

**可能原因**:
- 端口被占用
- 依赖未安装
- 环境变量配置错误

**解决方法**:
```bash
# 检查端口占用
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 终止占用进程
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# 检查依赖
pip list | grep fastapi
pip list | grep uvicorn

# 重新安装依赖
pip install -r requirements.txt
```

### Q2: LLM API调用失败

**可能原因**:
- API密钥未配置或错误
- 网络连接问题
- API配额用尽

**解决方法**:
```bash
# 检查环境变量
cat backend/.env | grep API_KEY

# 测试API连接
curl -X POST "http://localhost:8000/api/chat/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "测试"}'
```

### Q3: 浏览器扩展无法加载

**可能原因**:
- 扩展文件损坏
- 浏览器版本过低
- 权限配置错误

**解决方法**:
1. 检查浏览器版本（Chrome 88+）
2. 重新加载扩展
3. 检查 `manifest.json` 文件
4. 查看浏览器控制台错误信息

### Q4: 价格对比找不到商品

**可能原因**:
- 数据库中没有数据
- 商品名称匹配失败
- 平台名称不匹配

**解决方法**:
```bash
# 检查数据库中的商品数量
python3 -c "
from app.core.database import SessionLocal
from app.models.models import Product
db = SessionLocal()
count = db.query(Product).count()
print(f'数据库中的商品数量: {count}')
db.close()
"

# 重新上传数据
python3 upload_products.py products_data.json

# 使用更具体的关键词（如"iPhone"而不是完整标题）
```

### Q5: 记忆功能不工作

**可能原因**:
- FAISS未安装
- 向量数据库未初始化
- 记忆服务未启用

**解决方法**:
```bash
# 安装FAISS
pip install faiss-cpu

# 安装sentence-transformers
pip install sentence-transformers

# 重启服务
```

---

## 故障排查

### 1. 检查服务状态

```bash
# 检查后端服务是否运行
curl http://localhost:8000/health

# 检查端口监听
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### 2. 查看日志

```bash
# 查看后端日志
tail -f logs/backend.log

# 或在启动时查看控制台输出
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 检查数据库

```bash
# 检查数据库文件
ls -lh backend/llm_agent.db

# 使用SQLite查看数据库内容
sqlite3 backend/llm_agent.db
.tables
SELECT COUNT(*) FROM products;
```

### 4. 检查环境变量

```bash
# 查看环境变量
cd backend
cat .env

# 或在Python中测试
python3 -c "
from app.core.config import settings
print(f'LLM Provider: {settings.llm_provider}')
print(f'BigModel API Key: {settings.bigmodel_api_key[:10] if settings.bigmodel_api_key else \"Not Set\"}...')
"
```

### 5. 测试API端点

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试聊天功能
curl -X POST "http://localhost:8000/api/chat/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 测试价格对比
curl -X POST "http://localhost:8000/api/shopping/price-comparison" \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone", "platforms": ["jd", "taobao", "pdd"]}'
```

---

## 高级配置

### 1. 使用Redis缓存（可选）

```bash
# 安装Redis
# macOS: brew install redis
# Linux: sudo apt-get install redis-server

# 启动Redis
redis-server

# 配置环境变量
REDIS_URL=redis://localhost:6379/0
```

### 2. 使用Celery异步任务（可选）

```bash
# 安装Celery
pip install celery

# 启动Celery Worker
celery -A app.services.price_tracker_service worker --loglevel=info

# 启动Celery Beat（定时任务）
celery -A app.services.price_tracker_service beat --loglevel=info
```

### 3. 配置HTTPS（生产环境）

```bash
# 使用Nginx反向代理
# 配置SSL证书
# 修改FastAPI配置支持HTTPS
```

---

## 数据管理

### 1. 备份数据库

```bash
# 备份SQLite数据库
cp backend/llm_agent.db backend/llm_agent.db.backup

# 备份向量数据库
cp -r backend/vector_store backend/vector_store.backup
```

### 2. 清理数据

```bash
# 删除所有对话
python3 -c "
from app.core.database import SessionLocal
from app.models.models import Conversation
db = SessionLocal()
db.query(Conversation).delete()
db.commit()
db.close()
print('已删除所有对话')
"
```

### 3. 导出数据

```bash
# 导出商品数据
python3 -c "
import json
from app.core.database import SessionLocal
from app.models.models import Product
db = SessionLocal()
products = db.query(Product).all()
data = {'products': [{'platform': p.platform, 'title': p.title, 'price': p.price} for p in products]}
with open('exported_products.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
db.close()
print('数据已导出到 exported_products.json')
"
```

---

## 生产环境部署

### 1. 使用Docker（推荐）

```bash
# 构建镜像
docker build -t llm-agent-backend -f backend/Dockerfile .

# 运行容器
docker run -d -p 8000:8000 \
  -v $(pwd)/backend:/app \
  -e BIGMODEL_API_KEY=your_key \
  llm-agent-backend
```

### 2. 使用systemd（Linux）

创建服务文件 `/etc/systemd/system/llm-agent.service`:

```ini
[Unit]
Description=LLM Agent Backend Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/llm-agent/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl enable llm-agent
sudo systemctl start llm-agent
sudo systemctl status llm-agent
```

---

## 快速参考

### 常用命令

```bash
# 启动后端服务
cd backend && source ../venv/bin/activate && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 上传商品数据
python3 upload_products.py products_data.json

# 查看服务日志
tail -f logs/backend.log

# 检查服务健康
curl http://localhost:8000/health

# 测试聊天功能
curl -X POST "http://localhost:8000/api/chat/chat" -H "Content-Type: application/json" -d '{"message": "你好"}'
```

### 重要URL

- **欢迎页面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **前端界面**: http://localhost:3000 (如果启动前端)

---

## 获取帮助

如果遇到问题：

1. **查看日志**: 检查 `logs/` 目录下的日志文件
2. **查看文档**: 阅读项目中的其他文档文件
3. **查看API文档**: 访问 http://localhost:8000/docs
4. **检查配置**: 确认 `.env` 文件配置正确
5. **测试连接**: 使用curl测试各个API端点

---

## 总结

本指南涵盖了：
- ✅ 环境准备和依赖安装
- ✅ 配置文件设置
- ✅ 服务启动方法
- ✅ 浏览器扩展安装
- ✅ 功能使用说明
- ✅ 常见问题解决
- ✅ 故障排查方法

按照本指南操作，您应该能够成功启动和使用智能购物助手LLM Agent！

