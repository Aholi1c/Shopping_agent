# 📋 LLM Agent 配置检查清单

本文档提供了配置llm-agent项目的完整检查清单，确保所有必要的配置项都已正确设置。

## 🔑 必需配置项

### 1. 模型API密钥

#### ☐ 选择模型提供商
- [ ] **OpenAI** (推荐)
  - [ ] 获取API密钥: https://platform.openai.com/api-keys
  - [ ] 设置 `OPENAI_API_KEY` 环境变量
  - [ ] 确认账户余额充足

- [ ] **BigModel GLM-4.5** (推荐中文支持)
  - [ ] 获取API密钥: https://open.bigmodel.cn/
  - [ ] 设置 `BIGMODEL_API_KEY` 环境变量
  - [ ] 设置 `BIGMODEL_VLM_API_KEY` 环境变量 (用于图像)

- [ ] **DeepSeek** (经济选择)
  - [ ] 获取API密钥: https://platform.deepseek.com/
  - [ ] 设置 `DEEPSEEK_API_KEY` 环境变量

- [ ] **Moonshot** (Kimi模型)
  - [ ] 获取API密钥: https://platform.moonshot.cn/
  - [ ] 设置 `MOONSHOT_API_KEY` 环境变量

### 2. 后端环境配置

#### ☐ 基础配置
- [ ] 复制 `backend/.env.example` 为 `backend/.env`
- [ ] 设置 `SECRET_KEY` (生产环境必须修改)
- [ ] 配置 `DEBUG=false` (生产环境)
- [ ] 设置 `HOST=0.0.0.0`
- [ ] 设置 `PORT=8000`

#### ☐ 数据库配置
- [ ] **SQLite** (开发环境，默认)
  - [ ] 确认 `DATABASE_URL=sqlite:///./llm_agent.db`
  - [ ] 检查写权限

- [ ] **PostgreSQL** (生产环境推荐)
  - [ ] 安装PostgreSQL服务
  - [ ] 创建数据库 `llm_agent`
  - [ ] 创建用户 `llm_user`
  - [ ] 设置 `DATABASE_URL=postgresql://llm_user:password@localhost/llm_agent`

#### ☐ 可选服务配置
- [ ] **Redis** (缓存，推荐)
  - [ ] 安装Redis服务
  - [ ] 启动Redis: `redis-server --daemonize yes`
  - [ ] 设置 `REDIS_URL=redis://localhost:6379/0`

### 3. 前端环境配置

#### ☐ 基础配置
- [ ] 复制 `frontend/.env.example` 为 `frontend/.env.local`
- [ ] 设置 `REACT_APP_API_URL=http://localhost:8000`
- [ ] 设置 `REACT_APP_WS_URL=ws://localhost:8000`
- [ ] 设置 `REACT_APP_ENVIRONMENT=development`

## 📁 目录结构准备

### ☐ 后端目录
- [ ] 创建 `logs/` 目录 (日志文件)
- [ ] 创建 `uploads/` 目录 (文件上传)
- [ ] 创建 `vector_store/` 目录 (向量数据库)
  - [ ] `vector_store/faiss/`
  - [ ] `vector_store/chroma/`

### ☐ 数据目录
- [ ] 创建 `data/` 目录
- [ ] 创建 `data/documents/` (文档上传)
- [ ] 创建 `data/knowledge_base/` (知识库)
- [ ] 创建 `data/price_history/` (价格历史)
- [ ] 创建 `data/risk_keywords/` (风险关键词)

## 🚀 安装和启动检查

### ☐ 依赖安装
- [ ] Python 3.8+ 已安装
- [ ] Node.js 16+ 已安装
- [ ] 后端依赖: `cd backend && pip install -r requirements.txt`
- [ ] 前端依赖: `cd frontend && npm install`

### ☐ 数据库初始化
- [ ] 运行数据库迁移: `cd backend && python -c "from app.core.database import engine; from app.models.models import Base; Base.metadata.create_all(bind=engine)"`
- [ ] 确认数据库文件创建成功

### ☐ 服务启动
- [ ] 启动Redis (可选): `redis-server --daemonize yes`
- [ ] 启动后端: `cd backend && python -m uvicorn app.main:app --reload`
- [ ] 启动前端: `cd frontend && npm start`

## ✅ 功能验证

### ☐ 基础功能测试
- [ ] 访问 http://localhost:3000
- [ ] 检查前端界面加载正常
- [ ] 访问 http://localhost:8000/docs
- [ ] 检查API文档加载正常
- [ ] 测试健康检查: `curl http://localhost:8000/health`

### ☐ 对话功能测试
- [ ] 在前端发送文本消息
- [ ] 验证AI回复正常
- [ ] 检查WebSocket连接状态
- [ ] 测试对话历史保存

### ☐ 多模态功能测试
- [ ] 测试图片上传功能
- [ ] 验证图像识别正常工作
- [ ] 测试语音输入 (如果支持)

### ☐ 购物助手功能测试
- [ ] 进入购物助手界面
- [ ] 测试商品搜索功能
- [ ] 验证价格预测功能
- [ ] 测试风险分析功能
- [ ] 测试决策工具功能

## 🔧 可选高级配置

### ☐ 性能优化
- [ ] 配置Redis缓存
- [ ] 优化数据库索引
- [ ] 设置日志级别
- [ ] 配置监控和告警

### ☐ 安全配置
- [ ] 启用HTTPS
- [ ] 配置CORS
- [ ] 设置API密钥验证
- [ ] 配置防火墙规则

### ☐ 生产环境配置
- [ ] 使用PostgreSQL
- [ ] 配置Nginx反向代理
- [ ] 设置进程管理 (PM2)
- [ ] 配置SSL证书

## 🐛 常见问题检查

### ☐ API密钥问题
- [ ] 确认API密钥格式正确
- [ ] 检查API密钥权限
- [ ] 验证账户余额
- [ ] 测试网络连接

### ☐ 数据库连接问题
- [ ] 确认数据库服务运行
- [ ] 检查连接字符串
- [ ] 验证用户权限
- [ ] 检查防火墙设置

### ☐ 依赖安装问题
- [ ] 使用虚拟环境
- [ ] 升级pip到最新版本
- [ ] 清理pip缓存
- [ ] 重新安装依赖

## 📝 配置文件示例

### backend/.env
```env
# 模型配置 (选择一个)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# 数据库配置
DATABASE_URL=sqlite:///./llm_agent.db

# 应用配置
SECRET_KEY=your-super-secret-key
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 可选配置
REDIS_URL=redis://localhost:6379/0
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./vector_store
```

### frontend/.env.local
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## 📞 需要帮助？

如果配置过程中遇到问题：

1. **查看日志文件**
   - 后端日志: `logs/app.log`
   - 控制台输出: 后端启动时的终端输出

2. **检查文档**
   - [配置指南](SETUP.md)
   - [更新日志](CHANGELOG.md)
   - [前端文档](frontend/README.md)

3. **获取支持**
   - GitHub Issues: 提交问题报告
   - 技术社区: 搜索类似问题
   - 邮件支持: 联系技术团队

## ✨ 完成配置后的下一步

1. **探索功能**: 尝试各种AI功能
2. **上传文档**: 添加知识库内容
3. **自定义配置**: 根据需要调整配置
4. **部署上线**: 配置生产环境

---

*配置完成时间: ________*
*配置人员: ___________*
*联系方式: ___________*