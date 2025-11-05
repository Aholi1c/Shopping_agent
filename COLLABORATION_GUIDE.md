# 👥 团队协作开发指南

## 📋 目录

1. [快速定位](#快速定位)
2. [浏览器扩展开发](#浏览器扩展开发)
3. [后端API开发](#后端api开发)
4. [前端React应用开发](#前端react应用开发)
5. [数据管理](#数据管理)
6. [配置管理](#配置管理)
7. [常见开发任务](#常见开发任务)

---

## 🎯 快速定位

### 我想修改...应该编辑哪个文件？

| 功能模块 | 需要修改的文件 | 文件路径 |
|---------|--------------|---------|
| **浏览器扩展UI设计** | 侧边栏样式 | `browser-extension/sidepanel.css` |
| | 侧边栏HTML结构 | `browser-extension/sidepanel.html` |
| | 侧边栏JavaScript逻辑 | `browser-extension/sidepanel.js` |
| | 弹出窗口UI | `browser-extension/popup.html`, `popup.css`, `popup.js` |
| | 内容脚本样式 | `browser-extension/content.css` |
| **更新产品数据** | 产品数据JSON文件 | `products_data.json` |
| | 上传产品数据脚本 | `upload_products.py` |
| | 产品管理API | `backend/app/api/product_management.py` |
| **聊天功能** | 聊天API端点 | `backend/app/api/chat.py` |
| | 对话业务逻辑 | `backend/app/services/conversation_service.py` |
| | LLM服务 | `backend/app/services/llm_service.py` |
| **商品分析** | 商品分析API | `backend/app/api/shopping.py` |
| | 价格分析逻辑 | `backend/app/services/price_service.py` |
| | 风险评估逻辑 | `backend/app/services/risk_detection_service.py` |
| **价格对比** | 价格对比API | `backend/app/api/shopping.py` (price-comparison端点) |
| | 价格服务 | `backend/app/services/price_service.py` |
| | 购物服务 | `backend/app/services/shopping_service.py` |
| **记忆系统** | 记忆API | `backend/app/api/memory.py` |
| | 记忆服务 | `backend/app/services/memory_service.py` |
| | 向量服务 | `backend/app/services/vector_service.py` |
| **RAG增强** | RAG API | `backend/app/api/rag.py`, `enhanced_rag.py` |
| | RAG服务 | `backend/app/services/rag_service.py`, `enhanced_rag_service.py` |
| **数据库模型** | 数据模型定义 | `backend/app/models/models.py` |
| | 电商模型 | `backend/app/models/ecommerce_models.py` |
| | 数据模式 | `backend/app/models/schemas.py` |
| **配置** | 应用配置 | `backend/app/core/config.py` |
| | 环境变量 | `backend/.env` (需要创建) |
| **前端React应用** | 主应用组件 | `frontend/src/App.tsx` |
| | 聊天界面 | `frontend/src/components/ChatInterface.tsx` |
| | 购物助手组件 | `frontend/src/components/ShoppingAssistant.tsx` |
| | API服务 | `frontend/src/services/` |

---

## 🔌 浏览器扩展开发

### 文件结构

```
browser-extension/
├── manifest.json          # 扩展配置文件
├── background.js          # 后台服务脚本
├── content.js            # 内容脚本（页面商品信息提取）
├── content.css           # 内容脚本样式
├── sidepanel.html        # 侧边栏HTML
├── sidepanel.css         # 侧边栏样式
├── sidepanel.js          # 侧边栏逻辑
├── popup.html            # 弹出窗口HTML
├── popup.css             # 弹出窗口样式
├── popup.js              # 弹出窗口逻辑
├── api.js                # API客户端（与后端通信）
└── icons/                # 图标文件
```

### 常见修改场景

#### 1. 修改侧边栏UI设计

**修改样式**：
- 文件：`browser-extension/sidepanel.css`
- 说明：修改侧边栏的样式、颜色、布局等

**修改HTML结构**：
- 文件：`browser-extension/sidepanel.html`
- 说明：修改侧边栏的HTML结构、添加/删除元素

**修改交互逻辑**：
- 文件：`browser-extension/sidepanel.js`
- 说明：修改按钮点击、数据展示、API调用等逻辑

**示例：修改侧边栏背景色**
```css
/* browser-extension/sidepanel.css */
.sidepanel-container {
  background: #your-color;  /* 修改这里 */
}
```

#### 2. 修改商品信息提取逻辑

**文件**：`browser-extension/content.js`

**功能**：
- 从购物网站页面提取商品信息（名称、价格、描述等）
- 支持京东、淘宝、拼多多、Amazon等平台

**修改场景**：
- 添加新的购物平台支持
- 修改商品信息提取的CSS选择器
- 添加新的商品字段提取

**示例：添加新平台支持**
```javascript
// browser-extension/content.js
function extractProductInfo() {
  // ... 现有代码 ...
  
  // 添加新平台
  if (platform === 'new-platform') {
    return extractNewPlatformProductInfo();
  }
}
```

#### 3. 修改API调用逻辑

**文件**：`browser-extension/api.js`

**功能**：
- 封装与后端API的通信
- 处理请求和响应

**修改场景**：
- 添加新的API调用方法
- 修改请求参数格式
- 添加错误处理

#### 4. 修改扩展配置

**文件**：`browser-extension/manifest.json`

**修改场景**：
- 添加新的权限
- 修改内容脚本匹配规则
- 更新版本号

---

## 🖥️ 后端API开发

### 文件结构

```
backend/app/
├── main.py                    # 主应用入口（路由注册）
├── core/
│   ├── config.py              # 配置管理
│   └── database.py            # 数据库连接
├── models/
│   ├── models.py              # 数据库模型
│   ├── schemas.py             # Pydantic模式
│   └── ecommerce_models.py   # 电商模型
├── api/                       # API路由
│   ├── chat.py                # 聊天API
│   ├── shopping.py            # 购物API（商品分析、价格对比）
│   ├── product_management.py  # 产品管理API
│   ├── memory.py              # 记忆API
│   ├── rag.py                 # RAG API
│   └── ...                    # 其他API
└── services/                  # 业务逻辑
    ├── conversation_service.py
    ├── price_service.py
    ├── shopping_service.py
    ├── llm_service.py
    └── ...                    # 其他服务
```

### 常见修改场景

#### 1. 添加新的API端点

**步骤**：
1. 在 `backend/app/api/` 下找到对应的API文件（如 `shopping.py`）
2. 添加新的路由函数
3. 在 `backend/app/main.py` 中注册路由（如果文件已注册，则跳过）

**示例：在shopping.py中添加新端点**
```python
# backend/app/api/shopping.py
@router.post("/new-endpoint")
async def new_endpoint(request: SomeRequest):
    # 实现逻辑
    pass
```

#### 2. 修改业务逻辑

**文件**：`backend/app/services/`

**功能模块对应**：
- 聊天逻辑 → `conversation_service.py`
- 价格分析 → `price_service.py`
- 风险评估 → `risk_detection_service.py`
- 商品搜索 → `shopping_service.py`
- LLM调用 → `llm_service.py`
- 记忆管理 → `memory_service.py`
- RAG检索 → `rag_service.py`

**示例：修改价格对比逻辑**
```python
# backend/app/services/price_service.py
async def compare_prices(self, query: str, platforms: List[PlatformType]):
    # 修改这里的逻辑
    pass
```

#### 3. 修改数据库模型

**文件**：`backend/app/models/models.py`

**步骤**：
1. 修改模型类定义
2. 运行数据库迁移（或重新创建数据库）

**示例：添加新字段**
```python
# backend/app/models/models.py
class Product(Base):
    # ... 现有字段 ...
    new_field = Column(String)  # 添加新字段
```

#### 4. 修改API请求/响应格式

**文件**：`backend/app/models/schemas.py`

**功能**：定义Pydantic模型，用于API请求和响应的数据验证

**示例：修改请求模型**
```python
# backend/app/models/schemas.py
class ChatRequest(BaseModel):
    message: str
    # 添加新字段
    new_field: Optional[str] = None
```

---

## ⚛️ 前端React应用开发

### 文件结构

```
frontend/src/
├── App.tsx                    # 主应用组件
├── components/                # React组件
│   ├── ChatInterface.tsx      # 聊天界面
│   ├── ShoppingAssistant.tsx # 购物助手
│   ├── EnhancedChatInterface.tsx
│   └── ...                    # 其他组件
├── services/                  # API服务
│   ├── api.ts                 # 通用API
│   ├── chatApi.ts             # 聊天API
│   └── shoppingApi.ts         # 购物API
├── types/                     # TypeScript类型
│   ├── index.ts
│   └── shopping.ts
└── styles/                    # 样式文件
    ├── custom.css
    └── shopping-responsive.css
```

### 常见修改场景

#### 1. 修改聊天界面

**文件**：`frontend/src/components/ChatInterface.tsx` 或 `EnhancedChatInterface.tsx`

**修改内容**：
- UI布局和样式
- 消息展示格式
- 输入框功能

#### 2. 修改购物助手组件

**文件**：`frontend/src/components/ShoppingAssistant.tsx`

**子组件**：
- `frontend/src/components/shopping/` 目录下的组件

#### 3. 修改API调用

**文件**：`frontend/src/services/`

- `chatApi.ts` - 聊天相关API
- `shoppingApi.ts` - 购物相关API
- `api.ts` - 通用API

---

## 📊 数据管理

### 1. 更新产品数据

#### 方法一：直接修改JSON文件

**文件**：`products_data.json`

**格式**：
```json
{
  "products": [
    {
      "platform": "jd",
      "product_id": "123456",
      "title": "商品名称",
      "price": 999.0,
      "product_url": "https://...",
      ...
    }
  ]
}
```

**步骤**：
1. 编辑 `products_data.json`
2. 运行上传脚本：`python3 upload_products.py products_data.json`

#### 方法二：通过API上传

**API端点**：`POST /api/product-management/products/upload`

**文件**：`backend/app/api/product_management.py`

**示例**：
```bash
curl -X POST "http://localhost:8000/api/product-management/products/upload" \
  -H "Content-Type: application/json" \
  -d @products_data.json
```

### 2. 修改数据模型

**文件**：`backend/app/models/models.py`

**产品模型**：`Product` 类

**修改后**：
1. 删除旧数据库：`rm backend/llm_agent.db`
2. 重启服务：服务会自动创建新表结构

### 3. 查看产品数据

**API端点**：`GET /api/product-management/products`

**文件**：`backend/app/api/product_management.py`

---

## ⚙️ 配置管理

### 1. 环境变量配置

**文件**：`backend/.env`（需要创建）

**主要配置项**：
```bash
# LLM提供商
LLM_PROVIDER=bigmodel

# BigModel API密钥
BIGMODEL_API_KEY=your_key_here
BIGMODEL_VLM_API_KEY=your_vlm_key_here

# 数据库
DATABASE_URL=sqlite:///./llm_agent.db

# 万邦API（可选）
ONEBOUND_API_KEY=your_key
ONEBOUND_API_SECRET=your_secret
```

### 2. 应用配置

**文件**：`backend/app/core/config.py`

**修改场景**：
- 修改默认模型
- 修改端口号
- 添加新的配置项

---

## 🛠️ 常见开发任务

### 任务1：修改插件化的UI设计

#### 场景：修改侧边栏颜色主题

**需要修改的文件**：
1. `browser-extension/sidepanel.css` - 修改CSS变量和样式
2. `browser-extension/sidepanel.html` - 如果需要添加新的HTML元素

**示例**：
```css
/* browser-extension/sidepanel.css */
.sidepanel-header {
  background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
}
```

#### 场景：添加新的功能标签页

**需要修改的文件**：
1. `browser-extension/sidepanel.html` - 添加新的标签按钮
2. `browser-extension/sidepanel.js` - 添加标签切换逻辑
3. `browser-extension/sidepanel.css` - 添加标签样式

**步骤**：
1. 在HTML中添加标签按钮
2. 在JavaScript中添加点击事件处理
3. 添加对应的内容区域

### 任务2：更新产品数据

#### 场景：添加新产品到数据库

**方法一：直接编辑JSON文件**
1. 打开 `products_data.json`
2. 在 `products` 数组中添加新产品
3. 运行：`python3 upload_products.py products_data.json`

**方法二：使用API**
```bash
curl -X POST "http://localhost:8000/api/product-management/products/upload" \
  -H "Content-Type: application/json" \
  -d @products_data.json
```

#### 场景：修改现有产品数据

**方法一：通过API更新**
```bash
curl -X PUT "http://localhost:8000/api/product-management/products/{id}" \
  -H "Content-Type: application/json" \
  -d '{"price": 999.0, ...}'
```

**方法二：修改JSON后重新上传**
1. 编辑 `products_data.json`
2. 重新上传（会更新现有产品）

### 任务3：添加新的购物平台支持

**需要修改的文件**：
1. `browser-extension/content.js` - 添加商品信息提取逻辑
2. `browser-extension/manifest.json` - 添加URL匹配规则
3. `backend/app/services/shopping_service.py` - 添加平台搜索逻辑（可选）

**步骤**：
1. 在 `content.js` 中添加新平台的提取函数
2. 在 `extractProductInfo()` 中添加平台判断
3. 在 `manifest.json` 的 `content_scripts.matches` 中添加新域名

### 任务4：修改价格对比算法

**需要修改的文件**：
- `backend/app/services/price_service.py`

**函数**：
- `compare_prices()` - 价格对比主函数
- `_normalize_product_name()` - 商品名称标准化

**示例**：
```python
# backend/app/services/price_service.py
async def compare_prices(self, query: str, platforms: List[PlatformType]):
    # 修改这里的对比逻辑
    # 例如：改变分组算法、价格计算方式等
    pass
```

### 任务5：修改商品分析逻辑

**需要修改的文件**：
- `backend/app/api/shopping.py` - `analyze_product` 端点
- `backend/app/services/price_service.py` - 价格分析
- `backend/app/services/risk_detection_service.py` - 风险评估

**示例**：
```python
# backend/app/services/risk_detection_service.py
async def analyze_product_risks_by_data(self, product_data: Dict):
    # 修改风险评估逻辑
    pass
```

### 任务6：添加新的API端点

**步骤**：
1. 在对应的API文件中添加路由函数（如 `backend/app/api/shopping.py`）
2. 如果API文件已注册，无需修改 `main.py`
3. 添加对应的服务函数（如 `backend/app/services/`）
4. 添加请求/响应模型（如 `backend/app/models/schemas.py`）

**示例**：
```python
# backend/app/api/shopping.py
@router.post("/new-feature")
async def new_feature(request: NewFeatureRequest, db: Session = Depends(get_db)):
    # 调用服务层
    result = await some_service.new_feature(request)
    return result
```

### 任务7：修改LLM提示词

**需要修改的文件**：
- `backend/app/services/conversation_service.py` - 聊天提示词
- `backend/app/api/shopping.py` - 商品分析提示词
- `backend/app/services/risk_detection_service.py` - 风险评估提示词

**示例**：
```python
# backend/app/services/conversation_service.py
system_prompt = """
你是一个智能购物助手...
# 修改这里的提示词
"""
```

---

## 📁 文件修改检查清单

### 修改前端文件后

- [ ] 检查浏览器控制台是否有错误
- [ ] 测试功能是否正常工作
- [ ] 检查样式是否正常显示

### 修改后端文件后

- [ ] 重启后端服务（如果使用 `--reload` 会自动重载）
- [ ] 测试API端点（访问 `http://localhost:8000/docs`）
- [ ] 检查日志是否有错误

### 修改数据库模型后

- [ ] 备份数据库（可选）
- [ ] 删除旧数据库：`rm backend/llm_agent.db`
- [ ] 重启服务（会自动创建新表）

### 修改浏览器扩展后

- [ ] 重新加载扩展（`chrome://extensions/` → 点击刷新按钮）
- [ ] 测试扩展功能
- [ ] 检查控制台是否有错误

---

## 🔍 调试技巧

### 1. 查看后端日志

后端服务运行时会输出日志，查看：
- 控制台输出
- `logs/` 目录下的日志文件

### 2. 查看浏览器扩展日志

打开浏览器开发者工具：
- 侧边栏：右键扩展图标 → "检查弹出内容"
- 内容脚本：在网页上按F12 → Console标签
- 后台脚本：访问 `chrome://extensions/` → 点击扩展的"检查视图 service worker"

### 3. 测试API端点

访问 `http://localhost:8000/docs` 使用Swagger UI测试API

### 4. 检查数据库

```bash
# 使用SQLite查看数据库
sqlite3 backend/llm_agent.db
.tables
SELECT * FROM products LIMIT 10;
```

---

## 🚀 提交代码前检查

- [ ] 代码可以正常运行
- [ ] 没有语法错误
- [ ] 没有引入新的依赖（如果引入了，更新 `requirements.txt`）
- [ ] 更新了相关文档（如果修改了功能）
- [ ] 测试了相关功能
- [ ] 检查了代码格式（如果有代码格式规范）

---

## 📞 获取帮助

如果遇到问题：

1. **查看文档**：
   - `COMPLETE_HOW_TO_USE.md` - 完整使用指南
   - `FEATURES_COMPLETE_GUIDE.md` - 功能完整指南
   - `TROUBLESHOOTING_SERVICE.md` - 故障排查

2. **查看API文档**：
   - 访问 `http://localhost:8000/docs`

3. **查看代码注释**：
   - 各文件都有详细的注释说明

---

## 🎯 快速参考

### 最常用的文件

| 任务 | 文件路径 |
|------|---------|
| 修改侧边栏UI | `browser-extension/sidepanel.css`, `sidepanel.js` |
| 更新产品数据 | `products_data.json` + `upload_products.py` |
| 添加API端点 | `backend/app/api/[对应模块].py` |
| 修改业务逻辑 | `backend/app/services/[对应服务].py` |
| 修改数据库模型 | `backend/app/models/models.py` |
| 修改配置 | `backend/app/core/config.py` |

---

**祝开发顺利！** 🚀

