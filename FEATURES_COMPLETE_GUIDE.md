# 🛍️ 智能购物助手 LLM Agent - 完整功能指南

## 📋 目录

1. [项目概述](#项目概述)
2. [核心功能模块](#核心功能模块)
3. [购物助手功能](#购物助手功能)
4. [技术实现架构](#技术实现架构)
5. [数据流程](#数据流程)
6. [API端点详解](#api端点详解)

---

## 项目概述

**智能购物助手 LLM Agent** 是一个基于大语言模型的智能购物辅助系统，支持多模态交互（文本、图像、语音），集成记忆系统、RAG增强和多Agent协作功能，专注于帮助用户做出更明智的购物决策。

### 主要特性

- 🎯 **多模态交互**：支持文本、图像、语音输入
- 🧠 **智能记忆系统**：长期、短期、上下文记忆管理
- 📚 **RAG增强**：基于知识库的智能问答
- 🤖 **多Agent协作**：多个AI助手协同工作
- 🛒 **购物助手功能**：价格分析、风险评估、商品推荐
- 🌐 **多平台支持**：京东、淘宝、拼多多、Amazon等
- 🔌 **浏览器扩展**：无缝集成到购物网站

---

## 核心功能模块

### 1. 💬 聊天对话系统

#### 功能描述
提供智能对话能力，支持用户与AI助手进行自然语言交互，回答购物相关问题，提供商品推荐和购买建议。

#### 实现位置
- **API路由**: `backend/app/api/chat.py`
- **服务层**: `backend/app/services/conversation_service.py`
- **LLM服务**: `backend/app/services/llm_service.py`
- **前端**: `browser-extension/sidepanel.js` (聊天视图)

#### 主要功能
1. **基础聊天** (`POST /api/chat/chat`)
   - 文本对话
   - 支持多种LLM模型（OpenAI、BigModel GLM-4）
   - 对话历史管理
   - 上下文保持

2. **增强聊天** (`POST /api/chat/enhanced`)
   - 集成记忆系统
   - RAG增强（基于知识库）
   - 多Agent协作
   - 自定义参数（temperature、max_tokens等）

3. **对话管理**
   - 创建新对话
   - 获取对话列表
   - 查看对话历史
   - 删除对话

#### 技术实现
- **LLM集成**：支持OpenAI API和BigModel API
- **对话上下文**：使用SQLAlchemy存储对话历史
- **消息处理**：异步处理，支持流式响应
- **错误处理**：完善的异常处理和重试机制

#### 使用示例
```javascript
// 浏览器扩展中
const response = await window.apiClient.sendChatMessage({
  message: "给我推荐一款7000元左右的iPhone手机",
  use_memory: true,
  use_rag: false,
  model: "glm-4-0520"
});
```

---

### 2. 🧠 记忆系统

#### 功能描述
智能记忆管理系统，能够记住用户的偏好、历史对话和重要信息，在后续对话中自动调用相关记忆，提供个性化的服务。

#### 实现位置
- **API路由**: `backend/app/api/memory.py`
- **服务层**: `backend/app/services/memory_service.py`
- **向量服务**: `backend/app/services/vector_service.py`

#### 主要功能
1. **记忆类型**
   - **长期记忆（Episodic）**：事件和经历记忆
   - **语义记忆（Semantic）**：事实和知识记忆
   - **工作记忆（Working）**：当前对话上下文
   - **情境记忆（Contextual）**：特定场景的记忆

2. **记忆操作**
   - 创建记忆
   - 搜索记忆（基于语义相似度）
   - 更新记忆重要性
   - 合并相似记忆
   - 删除过期记忆

3. **用户偏好提取**
   - 自动从对话中提取用户偏好
   - 存储为语义记忆
   - 在推荐时优先使用

#### 技术实现
- **向量存储**：使用FAISS进行向量索引
- **Embedding模型**：sentence-transformers (all-MiniLM-L6-v2)
- **相似度搜索**：余弦相似度计算
- **重要性评分**：基于使用频率和用户反馈

#### 数据流程
```
用户对话 → 提取关键信息 → 生成Embedding → 存储到FAISS → 
后续对话 → 语义搜索 → 检索相关记忆 → 增强上下文 → LLM生成回答
```

---

### 3. 📚 RAG增强系统

#### 功能描述
检索增强生成（Retrieval-Augmented Generation），通过知识库检索相关信息来增强LLM的回答质量，支持文档上传、处理和智能检索。

#### 实现位置
- **API路由**: `backend/app/api/rag.py`, `backend/app/api/enhanced_rag.py`
- **服务层**: `backend/app/services/rag_service.py`, `backend/app/services/enhanced_rag_service.py`

#### 主要功能
1. **知识库管理**
   - 创建知识库
   - 上传文档（PDF、DOCX、Markdown、HTML）
   - 文档分块和向量化
   - 知识库查询

2. **文档处理**
   - 自动文档解析
   - 文本分块（chunk_size=1000, overlap=200）
   - 向量化存储
   - 元数据提取

3. **智能检索**
   - 语义搜索
   - 关键词匹配
   - 混合检索（语义+关键词）
   - Top-K结果返回

#### 技术实现
- **文档解析**：PyPDF2、python-docx、beautifulsoup4
- **向量化**：sentence-transformers
- **存储**：FAISS向量数据库
- **检索**：语义相似度 + TF-IDF

---

### 4. 🤖 多Agent协作系统

#### 功能描述
多个专业化AI Agent协同工作，每个Agent负责不同的任务，通过协作完成复杂的购物决策任务。

#### 实现位置
- **API路由**: `backend/app/api/agents.py`
- **服务层**: `backend/app/services/agent_service.py`

#### Agent类型
1. **研究员Agent**：收集商品信息和市场数据
2. **分析师Agent**：分析价格、质量和风险
3. **作家Agent**：生成推荐报告和购买建议
4. **协调员Agent**：协调其他Agent的工作

#### 协作模式
- **顺序协作**：Agent按顺序执行任务
- **并行协作**：多个Agent同时工作
- **层级协作**：主Agent协调子Agent

---

### 5. 🖼️ 多模态支持

#### 功能描述
支持文本、图像、语音多种输入方式，提供多模态交互能力。

#### 实现位置
- **API路由**: `backend/app/api/media.py`
- **服务层**: `backend/app/services/media_service.py`

#### 主要功能
1. **图像处理**
   - 图像上传和存储
   - 图像分析（使用GLM-4V）
   - 图像描述生成
   - 商品识别

2. **语音处理**
   - 语音转文字（SpeechRecognition）
   - 文字转语音（pyttsx3）
   - 语音对话

3. **视频处理**（计划中）
   - 视频分析
   - 关键帧提取

---

## 购物助手功能

### 1. 📊 商品分析功能

#### 功能描述
对商品进行综合分析，包括价格分析、风险评估、购买建议等，帮助用户做出明智的购买决策。

#### 实现位置
- **API路由**: `backend/app/api/shopping.py` (`POST /api/shopping/product-analysis`)
- **服务层**: 
  - `backend/app/services/price_service.py` (价格分析)
  - `backend/app/services/risk_detection_service.py` (风险评估)
  - `backend/app/services/conversation_service.py` (LLM综合分析)
- **前端**: `browser-extension/sidepanel.js` (分析视图)

#### 功能特点
1. **价格分析**
   - 当前价格评估
   - 多平台价格对比
   - 历史价格趋势
   - 价格合理性判断

2. **风险评估**
   - 关键词风险检测
   - LLM深度分析
   - 风险等级评估（低/中/高/严重）
   - 风险规避建议

3. **综合分析**
   - 商品概述和特点
   - 价格合理性分析
   - 多平台价格对比
   - 风险评估和建议
   - 购买建议（立即购买/等待降价/谨慎考虑）

#### 技术实现
```python
# 分析流程
1. 提取商品信息（名称、价格、平台、描述等）
2. 价格分析：调用PriceService.compare_prices()
3. 风险评估：调用RiskDetectionService.analyze_product_risks_by_data()
4. LLM综合分析：调用LLM生成综合分析报告
5. 返回结果：包含价格分析、风险评估、购买建议
```

#### 货币识别
- 自动识别商品价格货币（CNY、HKD、USD等）
- 在分析报告中明确标注货币类型
- 提醒用户注意汇率转换

---

### 2. 💰 价格对比功能

#### 功能描述
在多平台（京东、淘宝、拼多多）之间进行价格对比，帮助用户找到最优惠的价格。

#### 实现位置
- **API路由**: `backend/app/api/shopping.py` (`POST /api/shopping/price-comparison`)
- **服务层**: `backend/app/services/price_service.py`
- **前端**: `browser-extension/sidepanel.js` (比价视图)

#### 功能特点
1. **多平台搜索**
   - 优先从数据库获取（静态数据库）
   - 回退到Onebound API（如果配置）
   - 支持Web爬虫（可选）

2. **智能分组**
   - 商品名称标准化
   - 自动识别相同商品
   - 按平台组织价格

3. **价格分析**
   - 最低价/最高价
   - 价格差异
   - 节省百分比
   - 最佳平台推荐

#### 技术实现
- **数据库优先策略**：优先使用用户上传的静态数据库
- **商品名称标准化**：排除颜色、修饰词等可变信息，统一品牌名称
- **模糊匹配**：支持部分匹配和关键词搜索
- **平台价格映射**：按平台组织价格信息

#### 数据流程
```
用户输入商品名称 → 数据库查询（优先） → 商品分组 → 
价格对比分析 → 返回对比结果（最低价、最高价、价格差、最佳平台）
```

---

### 3. 📈 价格追踪功能

#### 功能描述
设置商品价格提醒，当价格达到目标值时自动通知用户。

#### 实现位置
- **API路由**: `backend/app/api/price_tracker.py`
- **服务层**: `backend/app/services/price_tracker_service.py`
- **前端**: `browser-extension/sidepanel.js` (追踪视图)

#### 功能特点
1. **价格监控**
   - 目标价格设置
   - 自动价格检查（Celery定时任务）
   - 价格变化通知

2. **价格历史**
   - 价格历史记录
   - 价格趋势图表
   - 价格预测

3. **提醒管理**
   - 创建提醒
   - 查看提醒列表
   - 删除提醒

#### 技术实现
- **Celery异步任务**：定时检查价格变化
- **价格历史存储**：SQLAlchemy存储价格记录
- **通知系统**：支持邮件、浏览器通知等

---

### 4. 🛡️ 风险评估功能

#### 功能描述
识别商品潜在风险（假货、质量问题、虚假宣传等），帮助用户避免购买风险商品。

#### 实现位置
- **API路由**: `backend/app/api/advanced_features.py`
- **服务层**: `backend/app/services/risk_detection_service.py`

#### 功能特点
1. **风险检测方法**
   - **关键词检测**：基于风险关键词库
   - **价格异常检测**：价格过低可能存在风险
   - **LLM深度分析**：使用LLM理解商品描述和评论

2. **风险类别**
   - 质量问题
   - 物流问题
   - 服务问题
   - 价格问题
   - 真伪问题

3. **风险等级**
   - 低风险
   - 中风险
   - 高风险
   - 严重风险

#### 技术实现
- **关键词库**：预定义风险关键词
- **LLM分析**：使用GLM-4分析商品描述和评论
- **风险评分**：综合多因素计算风险等级

---

### 5. 📦 商品管理功能

#### 功能描述
管理商品数据，支持上传、查询、更新、删除商品信息。

#### 实现位置
- **API路由**: `backend/app/api/product_management.py`
- **数据库模型**: `backend/app/models/models.py` (Product模型)

#### 主要功能
1. **数据上传**
   - JSON格式上传
   - CSV格式上传（计划中）
   - 批量导入

2. **数据管理**
   - 查询商品列表
   - 获取商品详情
   - 更新商品信息
   - 删除商品

3. **统计信息**
   - 商品总数
   - 平台分布
   - 分类统计

#### 使用示例
```bash
# 上传商品数据
python3 upload_products.py products_data.json

# 查询商品
curl "http://localhost:8000/api/product-management/products?platform=jd&limit=10"
```

---

### 6. 🔍 视觉搜索功能

#### 功能描述
以图搜图，通过上传商品图片找到相似商品或识别商品信息。

#### 实现位置
- **API路由**: `backend/app/api/visual_search.py`
- **服务层**: `backend/app/services/visual_search_service.py`

#### 功能特点
- 图像特征提取
- 相似商品搜索
- 商品识别
- 价格对比

---

### 7. 🎁 优惠券管理功能

#### 功能描述
管理优惠券信息，计算最优购买方案。

#### 实现位置
- **API路由**: `backend/app/api/coupon.py`
- **服务层**: `backend/app/services/coupon_service.py`

---

### 8. 📱 商品对比功能

#### 功能描述
对比多个商品的详细规格和价格，帮助用户选择最适合的商品。

#### 实现位置
- **API路由**: `backend/app/api/product_comparison.py`
- **服务层**: `backend/app/services/product_comparison_service.py`

---

## 技术实现架构

### 后端架构

#### 1. 框架和技术栈
- **Web框架**: FastAPI
- **数据库**: SQLite（主数据库）+ FAISS（向量数据库）
- **ORM**: SQLAlchemy
- **异步处理**: asyncio + Celery（可选）
- **向量搜索**: FAISS + sentence-transformers

#### 2. 服务层架构
```
API层 (FastAPI路由)
    ↓
服务层 (业务逻辑)
    ├── LLM服务 (llm_service.py)
    ├── 对话服务 (conversation_service.py)
    ├── 记忆服务 (memory_service.py)
    ├── RAG服务 (rag_service.py)
    ├── 价格服务 (price_service.py)
    ├── 风险检测服务 (risk_detection_service.py)
    └── 购物服务 (shopping_service.py)
    ↓
数据层 (SQLAlchemy + FAISS)
```

#### 3. 数据模型
- **User**: 用户信息
- **Conversation**: 对话记录
- **Message**: 消息记录
- **Memory**: 记忆存储
- **Product**: 商品信息
- **PriceHistory**: 价格历史
- **UserPreference**: 用户偏好

### 前端架构

#### 浏览器扩展
- **Manifest V3**: Chrome扩展标准
- **Content Script**: 页面商品信息提取
- **Background Script**: 后台服务和消息传递
- **Sidepanel**: 主界面（聊天、分析、比价、追踪）
- **Popup**: 快捷操作面板

#### 数据流
```
购物网站页面 → Content Script提取商品信息 → 
Background Script处理 → Sidepanel显示 → 
用户操作 → API调用 → 后端处理 → 返回结果 → 前端展示
```

---

## 数据流程

### 1. 商品分析流程

```
用户在购物网站浏览商品
    ↓
Content Script提取商品信息（名称、价格、描述、参数等）
    ↓
用户点击"y分析商品"
    ↓
Sidepanel发送分析请求到后端
    ↓
后端API接收请求
    ├── 价格分析：调用PriceService.compare_prices()
    │   └── 查询数据库 → 商品分组 → 价格对比
    ├── 风险评估：调用RiskDetectionService.analyze_product_risks_by_data()
    │   └── 关键词检测 → LLM分析 → 风险评分
    └── LLM综合分析：调用LLM生成分析报告
        └── 整合价格和风险信息 → 生成综合分析
    ↓
返回分析结果
    ↓
Sidepanel展示结果（价格分析、风险评估、购买建议）
```

### 2. 价格对比流程

```
用户输入商品名称
    ↓
Sidepanel发送比价请求
    ↓
后端PriceService.compare_prices()
    ├── 优先查询数据库（静态数据库）
    │   ├── 平台过滤（jd、taobao、pdd）
    │   ├── 商品名称模糊匹配
    │   └── 商品分组（标准化商品名称）
    ├── 如果数据库结果不足，回退到Onebound API
    └── 价格分析
        ├── 计算最低价/最高价
        ├── 计算价格差异
        └── 推荐最佳平台
    ↓
返回价格对比结果
    ↓
Sidepanel展示对比结果（各平台价格、价格差、最佳平台）
```

### 3. 聊天对话流程

```
用户发送消息
    ↓
Sidepanel发送聊天请求
    ↓
后端ConversationService.process_chat_message()
    ├── 提取用户偏好（如果启用记忆）
    ├── 检索相关记忆（如果启用记忆）
    ├── 检索知识库（如果启用RAG）
    └── 构建增强上下文
        ├── 系统提示（包含用户偏好）
        ├── 相关记忆
        ├── RAG检索结果
        └── 对话历史
    ↓
调用LLM生成回答
    ↓
存储对话和记忆
    ↓
返回回答
    ↓
Sidepanel展示回答
```

---

## API端点详解

### 聊天相关 (`/api/chat`)

| 端点 | 方法 | 功能 | 实现位置 |
|------|------|------|----------|
| `/chat` | POST | 基础聊天 | `chat.py` |
| `/enhanced` | POST | 增强聊天（记忆+RAG） | `chat.py` |
| `/conversations` | GET | 获取对话列表 | `chat.py` |
| `/conversations/{id}` | GET | 获取对话详情 | `chat.py` |
| `/conversations/{id}/messages` | GET | 获取对话消息 | `chat.py` |

### 记忆相关 (`/api/memory`)

| 端点 | 方法 | 功能 | 实现位置 |
|------|------|------|----------|
| `/memories` | POST | 创建记忆 | `memory.py` |
| `/memories/search` | POST | 搜索记忆 | `memory.py` |
| `/memories/{id}` | GET | 获取记忆详情 | `memory.py` |
| `/memories/{id}` | DELETE | 删除记忆 | `memory.py` |

### RAG相关 (`/api/rag`, `/api/enhanced-rag`)

| 端点 | 方法 | 功能 | 实现位置 |
|------|------|------|----------|
| `/knowledge-bases` | POST | 创建知识库 | `rag.py` |
| `/knowledge-bases/{id}/documents` | POST | 上传文档 | `rag.py` |
| `/knowledge-bases/{id}/search` | POST | 搜索知识库 | `rag.py` |
| `/search` | POST | 增强RAG搜索 | `enhanced_rag.py` |

### 购物相关 (`/api/shopping`)

| 端点 | 方法 | 功能 | 实现位置 |
|------|------|------|----------|
| `/product-analysis` | POST | 商品综合分析 | `shopping.py` |
| `/price-comparison` | POST | 多平台价格对比 | `shopping.py` |
| `/search` | POST | 商品搜索 | `shopping.py` |
| `/products/{id}` | GET | 获取商品详情 | `shopping.py` |
| `/compare` | POST | 商品对比 | `shopping.py` |

### 商品管理 (`/api/product-management`)

| 端点 | 方法 | 功能 | 实现位置 |
|------|------|------|----------|
| `/products/upload` | POST | 上传商品数据（JSON） | `product_management.py` |
| `/products` | GET | 查询商品列表 | `product_management.py` |
| `/products/{id}` | GET | 获取商品详情 | `product_management.py` |
| `/products/{id}` | PUT | 更新商品信息 | `product_management.py` |
| `/products/{id}` | DELETE | 删除商品 | `product_management.py` |
| `/products/stats` | GET | 获取统计信息 | `product_management.py` |

### 价格追踪 (`/api/price-tracker`)

| 端点 | 方法 | 功能 | 实现位置 |
|------|------|------|----------|
| `/track` | POST | 创建价格追踪 | `price_tracker.py` |
| `/alerts` | GET | 获取价格提醒 | `price_tracker.py` |
| `/history/{product_id}` | GET | 获取价格历史 | `price_tracker.py` |

### 其他功能

- **视觉搜索** (`/api/visual-search`): 图像识别和搜索
- **优惠券** (`/api/coupon`): 优惠券管理
- **商品对比** (`/api/comparison`): 多商品对比
- **社交商务** (`/api/social-commerce`): 社交平台集成
- **购物行为** (`/api/shopping-behavior`): 用户行为分析

---

## 数据存储

### SQLite数据库
- **主数据库**: `backend/llm_agent.db`
- **存储内容**: 用户、对话、消息、商品、价格历史等
- **ORM**: SQLAlchemy

### FAISS向量数据库
- **存储位置**: `backend/vector_store/`
- **存储内容**: 记忆向量、文档向量
- **用途**: 语义搜索和相似度匹配

### 静态商品数据库
- **数据来源**: 用户上传的JSON文件（`products_data.json`）
- **存储**: SQLite数据库的Product表
- **用途**: 价格对比、商品分析

---

## 配置说明

### LLM提供商配置
- **OpenAI**: 支持GPT-3.5、GPT-4等模型
- **BigModel**: 支持GLM-4-0520、GLM-4V等模型
- **Azure OpenAI**: 支持Azure部署的OpenAI模型

### 第三方API配置
- **Onebound API**: 万邦API，用于商品数据获取
- **平台API**: 京东、淘宝、拼多多API（可选）

### 可选依赖
系统支持可选依赖，即使某些库未安装，核心功能仍可运行：
- `faiss-cpu`: 向量搜索（可选）
- `sentence-transformers`: 文本嵌入（可选）
- `celery`: 异步任务（可选）
- `feedparser`: RSS订阅（可选）
- `PIL`: 图像处理（可选）

---

## 浏览器扩展功能

### 主要功能
1. **商品信息提取**: 自动从购物网站提取商品信息
2. **聊天助手**: 在侧边栏与AI助手对话
3. **商品分析**: 综合分析当前浏览的商品
4. **价格对比**: 搜索并对比多平台价格
5. **价格追踪**: 设置价格提醒

### 支持的网站
- 京东 (jd.com)
- 淘宝 (taobao.com)
- 天猫 (tmall.com)
- 拼多多 (pdd.com)
- Amazon (amazon.com, amazon.com.hk等)

### 扩展组件
- **Content Script**: 提取商品信息
- **Background Script**: 处理消息和API调用
- **Sidepanel**: 主界面（聊天、分析、比价、追踪）
- **Popup**: 快捷操作

---

## 总结

本系统是一个功能完整的智能购物助手，集成了：
- ✅ 多模态交互（文本、图像、语音）
- ✅ 智能记忆系统
- ✅ RAG增强
- ✅ 多Agent协作
- ✅ 商品分析和价格对比
- ✅ 风险评估和购买建议
- ✅ 浏览器扩展集成
- ✅ 静态数据库支持

所有功能都经过实际测试和优化，可以立即使用。

