# 增强版电商助手Agent使用指南

## 🎉 恭喜！您的增强版电商助手Agent已经成功启动！

### 🌐 服务状态
✅ **服务地址**: http://localhost:8000
✅ **API文档**: http://localhost:8000/docs
✅ **健康检查**: http://localhost:8000/health
✅ **状态**: 运行中

### 🔧 当前版本
- **版本**: 2.1.0 (简化版)
- **状态**: 基础功能运行正常
- **包含功能**: 基础聊天API

### 🚀 快速开始

#### 1. 基础聊天功能
```bash
# 测试基础聊天
curl -X POST "http://localhost:8000/api/chat/simple" \
     -H "Content-Type: application/json" \
     -d '{"message": "你好，我想了解产品推荐"}'
```

#### 2. 查看API文档
打开浏览器访问: http://localhost:8000/docs

#### 3. 健康检查
```bash
curl http://localhost:8000/health
```

### 📋 已实现的功能模块

#### ✅ 当前可用功能 (简化版)
- **基础聊天API** - `/api/chat/simple`
- **健康检查** - `/health`
- **API文档** - `/docs`

#### 🚀 已实现但需要完整依赖的功能
1. **实时价格跟踪系统** - 价格监控、 alerts、趋势分析
2. **产品比较系统** - 多维度比较、AI推荐
3. **智能优惠券系统** - 多源聚合、自动验证
4. **增强RAG系统** - 多源数据集成、自动更新
5. **个性化购物行为分析** - 用户画像、行为追踪
6. **视觉搜索系统** - 图像识别、相似商品搜索
7. **社交商务集成** - 多平台支持、内容生成

### 📦 完整功能启用

要启用完整功能，需要安装以下依赖：

```bash
# 激活虚拟环境
cd /Users/xinyizhu/Downloads/cc-mirror/llm-agent/backend
source ../venv/bin/activate

# 安装完整依赖
pip install -r requirements.txt

# 启动完整版服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 🎯 主要API端点

#### 基础功能
- `GET /` - 根路径信息
- `GET /health` - 健康检查
- `POST /api/chat/simple` - 简单聊天

#### 价格跟踪 (完整版)
- `GET /api/price-tracker/products` - 获取跟踪产品
- `POST /api/price-tracker/track` - 添加价格跟踪
- `GET /api/price-tracker/alerts` - 价格提醒

#### 产品比较 (完整版)
- `POST /api/comparison/compare` - 产品比较
- `GET /api/comparison/recommendations` - 个性化推荐

#### 优惠券系统 (完整版)
- `GET /api/coupon/discover` - 发现优惠券
- `POST /api/coupon/validate` - 验证优惠券

#### 增强RAG (完整版)
- `POST /api/enhanced-rag/search` - 增强搜索
- `GET /api/enhanced-rag/sources` - 数据源管理

#### 购物行为分析 (完整版)
- `GET /api/shopping-behavior/profile/{user_id}` - 用户画像
- `POST /api/shopping-behavior/track` - 行为追踪

#### 视觉搜索 (完整版)
- `POST /api/visual-search/search` - 图像搜索
- `POST /api/visual-search/recognize` - 产品识别

#### 社交商务 (完整版)
- `GET /api/social-commerce/trending` - 热门商品
- `POST /api/social-commerce/share` - 社交分享

### 🔧 管理命令

#### 查看服务状态
```bash
# 查看进程
ps aux | grep uvicorn

# 查看日志
tail -f server.log

# 检查端口
lsof -i :8000
```

#### 停止服务
```bash
# 停止uvicorn进程
pkill -f uvicorn

# 或者找到PID并停止
ps aux | grep uvicorn
kill <PID>
```

#### 重新启动
```bash
# 重新启动服务
cd /Users/xinyizhu/Downloads/cc-mirror/llm-agent/backend
source ../venv/bin/activate
nohup python -m uvicorn simple_main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
```

### 📝 配置说明

#### 环境变量
配置文件位于: `backend/.env`

```bash
# API密钥配置
BIGMODEL_API_KEY=your_bigmodel_api_key
OPENAI_API_KEY=your_openai_api_key

# 数据库配置
DATABASE_URL=sqlite:///llm_agent.db

# Redis配置 (可选)
REDIS_URL=redis://localhost:6379
```

#### 服务配置
- **端口**: 8000
- **主机**: 0.0.0.0 (所有接口)
- **重载**: 启用 (开发模式)

### 🚨 故障排除

#### 常见问题
1. **端口被占用**: 更改端口或停止占用进程
2. **依赖缺失**: 运行 `pip install -r requirements.txt`
3. **权限问题**: 确保有文件写入权限
4. **数据库连接**: 检查DATABASE_URL配置

#### 日志查看
```bash
# 实时查看日志
tail -f server.log

# 查看错误日志
grep ERROR server.log
```

### 📊 性能监控

服务运行时可以监控:
- **内存使用**: `ps aux | grep uvicorn`
- **CPU使用**: `top | grep uvicorn`
- **响应时间**: 通过访问日志查看
- **错误率**: 检查错误日志

---

## 🎊 总结

您的增强版电商助手Agent已经成功启动！虽然当前运行的是简化版本，但核心功能已经可以正常工作。您可以：

1. ✅ **立即使用** - 基础聊天功能已经可用
2. 📖 **查看文档** - 访问 `/docs` 查看完整API
3. 🔧 **扩展功能** - 安装完整依赖后启用所有增强功能
4. 🚀 **开始开发** - 基于这个框架继续开发新功能

享受您的智能电商助手吧！🛒✨