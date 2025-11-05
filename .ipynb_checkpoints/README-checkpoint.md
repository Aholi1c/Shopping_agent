# 🛍️ 智能购物助手 LLM Agent

一个功能齐全的增强多模态大语言模型代理应用，专注于智能购物助手功能，支持文本、图像、语音交互，并集成记忆系统、RAG增强和多Agent协作功能。

## 🚀 最新更新 (v2.3.0)

### 🎨 全新UI界面
- **现代化设计**: 基于Ant Design 5.0的专业级UI组件库
- **智能对话界面**: 重新设计的聊天界面，支持文件上传和语音录制
- **响应式布局**: 完美适配桌面端和移动端设备
- **渐变配色**: 精心设计的蓝紫色渐变主题
- **流畅动画**: 打字指示器、悬浮效果、过渡动画

### 🛒 增强功能
- **多模态输入**: 支持文本、图像、语音多种输入方式
- **实时状态显示**: 系统状态、API连接状态、知识库状态实时监控
- **快速操作**: 图片分析、语音输入、购物车、RAG搜索快捷按钮
- **高级功能面板**: 记忆系统、RAG增强、多智能体协作配置

## 功能特性

### 🎯 核心功能
- 🎯 **多模态支持**: 文本、图像、语音输入输出
- 💬 **实时对话**: HTTP API支持实时通信
- 🗣️ **语音交互**: 语音识别和语音合成
- 🖼️ **图像理解**: 图像分析和描述生成
- 💾 **会话管理**: 历史记录和上下文保持
- 🌐 **响应式界面**: 现代化Web前端

### 🚀 增强功能
- 🧠 **记忆系统**: 长期记忆、短期记忆和上下文管理
- 📚 **RAG增强**: 检索增强生成，基于知识库的智能问答
- 🤖 **多Agent协作**: 多个AI助手协同工作
- 🔍 **向量搜索**: 基于embedding的语义搜索
- 📄 **文档处理**: 支持PDF、DOCX、Markdown、HTML文件
- 🧩 **模块化架构**: 清晰的服务分离和扩展性
- 🌟 **双模型支持**: 支持OpenAI和BigModel GLM-4.5系列模型
- 🖼️ **视觉理解**: BigModel GLM-4.5V多模态图像分析

### 🛒 智能购物助手
- 📈 **智能价格预测**: 基于历史数据的时间序列分析，预测未来价格走势
- 🛡️ **商品风险识别**: 多维度风险检测，投诉分析和LLM内容理解
- 🎯 **交互式决策工具**: 实时权重调整，多目标优化推荐
- 🔄 **多平台支持**: 京东、淘宝、拼多多、小红书、抖音等
- 🖼️ **图像识别**: 拍照识商品，以图搜图功能
- 💰 **智能比价**: 跨平台价格对比，优惠计算
- 🎭 **场景化推荐**: 基于使用场景的个性化商品推荐

## 技术栈

### 后端
- **FastAPI**: 高性能Web框架
- **OpenAI API**: LLM推理服务
- **BigModel API**: 智谱清言GLM-4.5模型服务
- **SQLite**: 主数据存储
- **FAISS**: 向量数据库
- **Redis**: 缓存和会话管理
- **Sentence Transformers**: 文本嵌入
- **Langchain**: RAG框架
- **WebSocket**: 实时通信
- **Pillow**: 图像处理
- **SpeechRecognition**: 语音识别
- **Unstructured**: 文档处理
- **Celery**: 异步任务处理
- **ZhipuAI**: BigModel官方Python客户端

### 前端
- **React**: 现代JavaScript框架
- **TypeScript**: 类型安全
- **Ant Design**: 企业级UI组件库 (v5.0)
- **Recharts**: 数据可视化图表库
- **Axios**: HTTP客户端
- **HTML5**: 语音和图像API
- **CSS-in-JS**: 内联样式实现

## 项目结构

```
llm-agent/
├── backend/                 # 后端FastAPI服务
│   ├── app/
│   │   ├── main.py         # 主应用入口
│   │   ├── models/         # 数据模型
│   │   │   ├── models.py   # 数据库模型
│   │   │   └── schemas.py  # Pydantic模式
│   │   ├── api/            # API路由
│   │   │   ├── chat.py     # 聊天相关API
│   │   │   ├── memory.py   # 记忆系统API
│   │   │   ├── rag.py      # RAG系统API
│   │   │   └── agents.py   # 多Agent系统API
│   │   ├── services/       # 业务逻辑
│   │   │   ├── llm_service.py      # LLM服务
│   │   │   ├── memory_service.py   # 记忆管理服务
│   │   │   ├── rag_service.py       # RAG服务
│   │   │   ├── agent_service.py    # 多Agent服务
│   │   │   ├── vector_service.py   # 向量搜索服务
│   │   │   └── media_service.py     # 媒体处理服务
│   │   └── core/           # 核心配置
│   ├── requirements.txt    # Python依赖
│   └── .env.example       # 环境变量示例
├── frontend/               # React前端应用
│   ├── src/
│   │   ├── components/    # React组件
│   │   │   ├── EnhancedChatInterface.tsx  # 增强聊天界面
│   │   │   ├── ShoppingAssistant.tsx      # 购物助手
│   │   │   ├── FeaturePanel.tsx           # 功能面板
│   │   │   ├── layout/                    # 布局组件
│   │   │   │   └── MainLayout.tsx         # 主布局
│   │   │   └── shopping/                  # 购物相关组件
│   │   │       ├── PricePrediction.tsx   # 价格预测
│   │   │       ├── RiskAnalysis.tsx      # 风险分析
│   │   │       └── DecisionTool.tsx      # 决策工具
│   │   ├── services/      # API和WebSocket服务
│   │   ├── types/         # TypeScript类型定义
│   │   └── App.tsx        # 主应用组件
│   ├── package.json       # Node.js依赖
│   └── public/           # 静态资源
├── vector_store/          # 向量数据库存储
└── docs/                # 文档
    ├── STARTUP.md       # 快速启动指南
    ├── CONTRIBUTING.md  # 贡献指南
    └── README.md        # 项目说明
```

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- Redis (可选，用于缓存)

### 选择模型提供商

系统支持两种模型提供商：

#### 选项1: OpenAI
```bash
# 在 .env 文件中设置
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
```

#### 选项2: BigModel GLM-4.5
```bash
# 在 .env 文件中设置
LLM_PROVIDER=bigmodel
BIGMODEL_API_KEY=your_bigmodel_text_api_key
BIGMODEL_VLM_API_KEY=your_bigmodel_vision_api_key
```

### 后端启动
```bash
cd backend
pip install -r requirements.txt
# 启动Redis (可选)
redis-server --daemonize yes
# 启动后端服务
python -m uvicorn app.main:app --reload
```

### 前端启动
```bash
cd frontend
npm install
npm start
```

## 🚀 快速启动指南

### 方式一：手动启动

#### 1. 环境准备
```bash
# 检查Python版本 (需要3.8+)
python --version

# 检查Node.js版本 (需要16+)
node --version

# 安装Python依赖
cd backend
pip install -r requirements.txt

# 安装Node.js依赖
cd ../frontend
npm install
```

#### 2. 配置环境变量
```bash
# 后端配置
cd backend
cp .env.example .env
# 编辑 .env 文件，设置API密钥

# 前端配置
cd ../frontend
# 创建 .env 文件
echo "REACT_APP_API_URL=http://localhost:8000" > .env
```

#### 3. 启动服务
```bash
# 启动后端服务 (端口8000)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# 启动前端服务 (端口3000)
cd ../frontend
npm start
```

#### 4. 验证服务
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 🛠️ 常见问题解决

#### 端口冲突
如果端口被占用，可以：

```bash
# 查找占用端口的进程
lsof -i :3000  # 前端端口
lsof -i :8000  # 后端端口

# 终止进程
kill -9 <PID>
```

#### API密钥配置
确保在 `backend/.env` 文件中正确设置：

```bash
# OpenAI配置
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key

# 或 BigModel配置
LLM_PROVIDER=bigmodel
BIGMODEL_API_KEY=your_bigmodel_api_key
```

#### 依赖安装问题
```bash
# 清除缓存重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install

cd ../backend
pip install --upgrade pip
pip install -r requirements.txt
```

## 配置

### 后端配置
复制 `backend/.env.example` 为 `backend/.env`：

#### OpenAI 配置
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_PROVIDER=openai
```

#### BigModel 配置
```
BIGMODEL_API_KEY=your_bigmodel_text_api_key
BIGMODEL_VLM_API_KEY=your_bigmodel_vision_api_key
LLM_PROVIDER=bigmodel
```

#### 通用配置
```
DATABASE_URL=sqlite:///./llm_agent.db
SECRET_KEY=your_secret_key_here
REDIS_URL=redis://localhost:6379/0
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./vector_store
```

### 前端配置
在 `frontend` 目录创建 `.env` 文件：
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## 访问应用

- 🛍️ **前端界面**: http://localhost:3000
- 📚 **后端API文档**: http://localhost:8000/docs
- ❤️ **后端健康检查**: http://localhost:8000/health

## 🎨 界面展示

### 主要功能区域
1. **顶部导航栏**: Logo、搜索框、快捷操作、购物车、用户菜单
2. **左侧推荐区**: 智能商品推荐、热门搜索标签
3. **主对话区**: 多模态聊天界面、商品卡片展示
4. **底部信息栏**: 系统状态、帮助链接、版权信息

### 多模态交互
- 📝 **文本对话**: 自然语言购物咨询
- 🖼️ **图片上传**: 商品拍照识别和以图搜图
- 🎤 **语音输入**: 语音转文字对话
- 📊 **实时反馈**: 打字指示器和响应动画

## 增强功能使用

### 🧠 记忆系统
- 自动管理长期和短期记忆
- 基于重要性的记忆评分
- 上下文相关的记忆检索

### 📚 RAG增强
- 支持多种文档格式 (PDF, DOCX, Markdown, HTML)
- 智能文档分块和向量化
- 基于知识库的智能问答

### 🤖 多Agent协作
- 顺序、并行、层级协作模式
- 专业化Agent (研究员、分析师、作家、协调员)
- 任务分配和结果整合

### 🛒 智能购物助手功能
- **价格预测系统**: 使用线性回归、移动平均、季节性分析等多种算法
- **风险评估引擎**: 基于关键词库和机器学习的风险识别
- **决策优化工具**: 多目标权重调整和自然语言解释
- **多平台数据集成**: 统一的商品信息采集和标准化处理

## 许可证

MIT License