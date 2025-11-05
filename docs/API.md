# 📚 API 文档

本文档提供智能购物助手 LLM Agent 的完整 API 接口说明。

## 🌐 访问信息

- **API 基础URL**: `http://localhost:8001`
- **API 文档**: `http://localhost:8001/docs`
- **OpenAPI Schema**: `http://localhost:8001/openapi.json`

## 🔐 认证方式

系统支持多种认证方式：

### Bearer Token (推荐)
```http
Authorization: Bearer {your_token}
```

### API Key (备用)
```http
X-API-Key: {your_api_key}
```

## 📊 通用响应格式

所有 API 响应都遵循统一格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "error": null,
  "timestamp": "2024-09-25T10:00:00Z"
}
```

## 🗨️ 聊天接口

### 发送消息
```http
POST /api/chat/chat
Content-Type: application/json

{
  "message": "我想买一部手机",
  "conversation_id": 123,
  "message_type": "text",
  "model": "glm-4-0520",
  "use_memory": true,
  "use_rag": false
}
```

### 增强聊天 (支持多模态)
```http
POST /api/chat/enhanced
Content-Type: application/json

{
  "message": "帮我分析这个商品",
  "conversation_id": 123,
  "message_type": "text",
  "media_url": "https://example.com/image.jpg",
  "model": "glm-4v",
  "use_memory": true,
  "use_rag": true,
  "knowledge_base_ids": [1, 2],
  "agent_collaboration": true,
  "collaboration_type": "sequential",
  "agents": [1, 2, 3]
}
```

### 上传文件聊天
```http
POST /api/chat/chat/upload
Content-Type: multipart/form-data

file: {binary_file_data}
conversation_id: 123
message_type: "image"
```

### 获取对话历史
```http
GET /api/chat/conversations?user_id=1&limit=50
```

### 获取对话详情
```http
GET /api/chat/conversations/{conversation_id}
```

### 获取对话消息
```http
GET /api/chat/conversations/{conversation_id}/messages
```

## 🧠 记忆系统接口

### 创建记忆
```http
POST /api/memory/memories
Content-Type: application/json

{
  "content": "用户喜欢苹果产品",
  "memory_type": "semantic",
  "importance_score": 0.8,
  "tags": ["preference", "apple"],
  "metadata": {
    "source": "conversation",
    "confidence": 0.9
  }
}
```

### 搜索记忆
```http
GET /api/memory/memories/search?query=苹果产品&limit=10&score_threshold=0.5
```

### 获取工作记忆
```http
GET /api/memory/working-memory/{session_id}
```

### 更新工作记忆
```http
PUT /api/memory/working-memory/{session_id}
Content-Type: application/json

{
  "context_data": {
    "current_topic": "手机购买",
    "user_preferences": ["iOS", "大屏幕"]
  },
  "short_term_memory": {
    "mentioned_brands": ["Apple", "Samsung"]
  }
}
```

### 整合记忆
```http
POST /api/memory/memories/consolidate?user_id=1
```

## 📚 RAG 系统接口

### 创建知识库
```http
POST /api/rag/knowledge-bases
Content-Type: application/json

{
  "name": "手机产品知识库",
  "description": "包含各种手机产品的详细信息",
  "user_id": 1
}
```

### 获取知识库列表
```http
GET /api/rag/knowledge-bases?user_id=1
```

### 上传文档到知识库
```http
POST /api/rag/knowledge-bases/{kb_id}/upload
Content-Type: multipart/form-data

file: {binary_file_data}
chunk_size: 1000
overlap: 200
```

### 搜索知识库
```http
POST /api/rag/knowledge-bases/search
Content-Type: application/json

{
  "query": "iPhone 15 Pro Max",
  "knowledge_base_ids": [1, 2],
  "top_k": 5,
  "score_threshold": 0.7
}
```

### 生成 RAG 响应
```http
POST /api/rag/knowledge-bases/generate-response
Content-Type: multipart/form-data

query: "iPhone 15 Pro Max的特点"
knowledge_base_ids: 1,2
temperature: 0.7
```

### 获取知识库统计
```http
GET /api/rag/knowledge-bases/{kb_id}/stats
```

## 🤖 多 Agent 系统接口

### 获取活跃 Agent 列表
```http
GET /api/agents
```

### 创建 Agent 任务
```http
POST /api/agents/tasks
Content-Type: application/json

{
  "task_type": "product_analysis",
  "task_data": {
    "product_name": "iPhone 15 Pro Max",
    "analysis_type": "price_comparison"
  },
  "session_id": "session_123"
}
```

### 获取会话任务
```http
GET /api/agents/tasks/{session_id}?limit=20
```

### 获取任务状态
```http
GET /api/agents/tasks/{task_id}
```

### 创建 Agent 协作
```http
POST /api/agents/collaborations
Content-Type: application/json

{
  "collaboration_type": "sequential",
  "participants": [1, 2, 3],
  "workflow": {
    "steps": [
      {"agent_id": 1, "role": "researcher"},
      {"agent_id": 2, "role": "analyst"},
      {"agent_id": 3, "role": "writer"}
    ]
  },
  "session_id": "session_123"
}
```

### 获取协作状态
```http
GET /api/agents/collaborations/{collab_id}
```

### 获取会话协作列表
```http
GET /api/agents/collaborations/session/{session_id}
```

## 🛒 购物助手接口

### 商品搜索
```http
GET /api/shopping/search?query=iPhone+15&platforms=jd,taobao&min_price=5000&max_price=15000
```

### 价格预测
```http
POST /api/shopping/price-prediction
Content-Type: application/json

{
  "product_id": "iphone_15_pro_max",
  "platform": "jd",
  "current_price": 9999,
  "prediction_days": 30,
  "historical_data": [
    {"date": "2024-08-01", "price": 10999},
    {"date": "2024-08-15", "price": 10499}
  ]
}
```

### 风险分析
```http
POST /api/shopping/risk-analysis
Content-Type: application/json

{
  "product_info": {
    "title": "iPhone 15 Pro Max",
    "price": 9999,
    "seller": "Apple官方旗舰店",
    "platform": "jd"
  },
  "analysis_type": "comprehensive"
}
```

### 决策支持
```http
POST /api/shopping/decision-support
Content-Type: application/json

{
  "products": [
    {
      "id": "product_1",
      "name": "iPhone 15 Pro Max",
      "price": 9999,
      "features": {"storage": "256GB", "color": "深空黑"}
    },
    {
      "id": "product_2",
      "name": "Samsung Galaxy S24 Ultra",
      "price": 8999,
      "features": {"storage": "256GB", "color": "钛灰"}
    }
  ],
  "user_preferences": {
    "budget": 10000,
    "priority_features": ["camera", "battery", "performance"],
    "weights": {"price": 0.3, "quality": 0.4, "brand": 0.3}
  }
}
```

## 🎵 媒体处理接口

### 语音转文字
```http
POST /api/media/transcribe
Content-Type: application/json

{
  "audio_url": "https://example.com/audio.wav",
  "language": "zh-CN"
}
```

### 上传音频转文字
```http
POST /api/media/transcribe/upload
Content-Type: multipart/form-data

file: {binary_audio_data}
language: zh-CN
```

### 文字转语音
```http
POST /api/media/speech
Content-Type: application/json

{
  "text": "欢迎使用智能购物助手",
  "voice": "female",
  "rate": 1.0,
  "pitch": 1.0
}
```

### 图像分析
```http
POST /api/media/analyze-image
Content-Type: application/json

{
  "image_url": "https://example.com/product.jpg",
  "prompt": "请分析这个商品的特点和价格区间"
}
```

### 上传图像分析
```http
POST /api/media/analyze-image/upload
Content-Type: multipart/form-data

file: {binary_image_data}
prompt: 请分析这个商品的特点和价格区间
```

## 📈 WebSocket 实时通信

### 连接地址
```
ws://localhost:8001/ws/chat
```

### 消息格式
```json
{
  "type": "message",
  "data": {
    "message": "你好",
    "conversation_id": 123,
    "user_id": 1
  },
  "timestamp": "2024-09-25T10:00:00Z"
}
```

### 消息类型
- `message`: 用户消息
- `typing`: 正在输入状态
- `response`: AI 响应（流式）
- `error`: 错误消息
- `status`: 连接状态

## 🔄 文件上传

### 支持的文件格式
- **图片**: JPG, PNG, GIF, WebP (最大 10MB)
- **音频**: WAV, MP3, M4A (最大 20MB)
- **文档**: PDF, DOCX, TXT, MD (最大 50MB)

### 上传接口
```http
POST /api/upload
Content-Type: multipart/form-data

file: {binary_file_data}
type: image|audio|document
```

## ⚡ 系统监控

### 健康检查
```http
GET /health
```

### 系统状态
```http
GET /api/system/status
```

### 性能指标
```http
GET /api/system/metrics
```

## 📝 错误代码

| 代码 | 含义 | 说明 |
|------|------|------|
| 200 | 成功 | 请求成功处理 |
| 400 | 错误请求 | 请求参数错误 |
| 401 | 未授权 | 缺少或无效的认证 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 未找到 | 资源不存在 |
| 422 | 验证失败 | 数据验证错误 |
| 429 | 请求过多 | 超出速率限制 |
| 500 | 服务器错误 | 内部服务器错误 |
| 503 | 服务不可用 | 服务暂时不可用 |

## 🚀 请求示例

### cURL 示例
```bash
# 发送聊天消息
curl -X POST "http://localhost:8001/api/chat/enhanced" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "message": "我想买一部手机，预算10000元左右",
    "use_memory": true,
    "use_rag": true
  }'

# 上传图片分析
curl -X POST "http://localhost:8001/api/media/analyze-image/upload" \
  -H "Authorization: Bearer your_token" \
  -F "file=@/path/to/image.jpg" \
  -F "prompt=请分析这个手机的价格和特点"
```

### Python 示例
```python
import requests

# 设置 API 基础 URL
BASE_URL = "http://localhost:8001"
headers = {"Authorization": "Bearer your_token"}

# 发送聊天消息
response = requests.post(
    f"{BASE_URL}/api/chat/enhanced",
    headers=headers,
    json={
        "message": "我想买一部手机",
        "use_memory": True,
        "use_rag": True
    }
)
print(response.json())

# 获取对话历史
response = requests.get(
    f"{BASE_URL}/api/chat/conversations?user_id=1",
    headers=headers
)
print(response.json())
```

### JavaScript 示例
```javascript
// 设置 API 基础 URL
const BASE_URL = 'http://localhost:8001';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your_token'
};

// 发送聊天消息
async function sendMessage(message) {
  const response = await fetch(`${BASE_URL}/api/chat/enhanced`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      use_memory: true,
      use_rag: true
    })
  });
  return await response.json();
}

// 使用 WebSocket 连接
const ws = new WebSocket('ws://localhost:8001/ws/chat');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
};
```

## 🔧 开发工具

### Postman Collection
导入以下配置到 Postman：
```json
{
  "info": {
    "name": "智能购物助手 API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "聊天接口",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{token}}"}
        ],
        "url": {
          "raw": "{{base_url}}/api/chat/enhanced"
        }
      }
    }
  ]
}
```

### 环境变量
```json
{
  "base_url": "http://localhost:8001",
  "token": "your_api_token"
}
```

---