# MCP服务集成快速开始指南

## ✅ 已完成的集成

您的agent已经成功集成了MCP (Model Context Protocol) 服务！现在您可以直接从MCP服务器获取数据，而无需上传本地文档。

## 📋 快速配置步骤

### 1. 配置环境变量

在 `backend/.env` 文件中添加以下配置：

```bash
# MCP服务配置
MCP_ENABLED=true
MCP_BASE_URL=https://api.mcpworld.com/v1
MCP_API_KEY=your_mcp_api_key_here
MCP_TIMEOUT=30
MCP_RESOURCE_FILTERS={"type": "document", "status": "active"}
MCP_CONTENT_FORMAT=text
MCP_MAX_ITEMS=100
```

**注意**: 请将 `MCP_BASE_URL` 和 `MCP_API_KEY` 替换为您的实际MCP服务配置。

### 2. 启动服务

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 3. 验证MCP连接

访问以下端点检查MCP服务状态：

```bash
# 检查MCP状态
curl http://localhost:8000/api/mcp/status

# 连接到MCP服务器
curl -X POST http://localhost:8000/api/mcp/connect

# 列出可用资源
curl http://localhost:8000/api/mcp/resources
```

## 🎯 主要功能

### 1. 自动集成到RAG系统

当MCP启用后，`EnhancedRAGService` 会自动使用MCP作为数据源：

- ✅ MCP数据源会自动初始化
- ✅ 搜索时会优先使用MCP数据
- ✅ 无需手动上传文档

### 2. MCP资源管理

- **列出资源**: `GET /api/mcp/resources`
- **获取资源**: `GET /api/mcp/resources/{resource_id}`
- **搜索资源**: `POST /api/mcp/resources/search`

### 3. 数据同步

```bash
# 同步MCP数据到知识库
curl -X POST http://localhost:8000/api/mcp/sync

# 带查询条件同步
curl -X POST http://localhost:8000/api/mcp/sync \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone"}'
```

### 4. 工具调用

```bash
# 列出可用工具
curl http://localhost:8000/api/mcp/tools

# 调用工具
curl -X POST http://localhost:8000/api/mcp/tools/{tool_name} \
  -H "Content-Type: application/json" \
  -d '{"arguments": {...}}'
```

## 📚 API端点

所有MCP相关的API端点都在 `/api/mcp` 路径下：

- `/api/mcp/status` - 获取MCP服务状态
- `/api/mcp/connect` - 连接到MCP服务器
- `/api/mcp/disconnect` - 断开连接
- `/api/mcp/resources` - 资源管理
- `/api/mcp/tools` - 工具管理
- `/api/mcp/sync` - 数据同步

完整API文档: http://localhost:8000/docs#tag/MCP

## 🔄 工作流程

### 传统方式（本地文档上传）
```
用户上传文档 → 文档处理 → 向量化 → 存储到本地知识库 → RAG搜索
```

### MCP方式（远程数据）
```
MCP服务器提供数据 → MCP客户端获取 → 自动向量化 → 存储到知识库 → RAG搜索
```

## 🎨 优势

1. **无需维护本地文档** - 数据直接从MCP服务器获取
2. **实时数据更新** - MCP服务器可以实时更新数据
3. **集中化管理** - 多个agent可以共享同一个MCP数据源
4. **灵活的过滤** - 可以通过过滤条件获取特定类型的数据
5. **工具集成** - 可以使用MCP提供的工具扩展功能

## ⚙️ 配置说明

### MCP_BASE_URL

MCP服务器的基础URL，例如：
- `https://api.mcpworld.com/v1`
- `http://localhost:8001/api`

### MCP_API_KEY

MCP服务的API密钥（如果需要认证）

### MCP_RESOURCE_FILTERS

JSON格式的资源过滤条件，例如：
```json
{
  "type": "document",
  "status": "active",
  "category": "product"
}
```

### MCP_CONTENT_FORMAT

内容格式，可选值：
- `text` - 纯文本
- `json` - JSON格式
- `markdown` - Markdown格式
- `html` - HTML格式

## 📖 更多信息

详细文档请参考: [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md)

## 🐛 故障排除

### 问题1: MCP连接失败

```bash
# 检查MCP状态
curl http://localhost:8000/api/mcp/status

# 查看日志
tail -f logs/app.log | grep MCP
```

### 问题2: 无法获取资源

```bash
# 测试MCP服务器连接
curl -H "Authorization: Bearer YOUR_API_KEY" https://your-mcp-server.com/api/health

# 检查资源列表
curl http://localhost:8000/api/mcp/resources
```

### 问题3: 数据同步失败

```bash
# 查看同步错误
curl -X POST http://localhost:8000/api/mcp/sync

# 检查MCP配置
grep MCP backend/.env
```

## ✅ 验证清单

- [ ] 在 `.env` 文件中配置了MCP相关配置
- [ ] MCP_ENABLED 设置为 true
- [ ] MCP_BASE_URL 配置正确
- [ ] MCP_API_KEY 已设置（如果需要）
- [ ] 服务启动后可以访问 `/api/mcp/status`
- [ ] MCP连接成功
- [ ] 可以列出MCP资源
- [ ] 可以搜索MCP资源
- [ ] 数据同步功能正常

---

**完成！** 您的agent现在已经可以通过MCP服务获取数据了！🎉

