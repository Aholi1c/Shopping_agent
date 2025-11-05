# MCP (Model Context Protocol) 集成指南

本文档说明如何配置和使用MCP服务来替代本地文档上传功能。

## 📋 概述

MCP (Model Context Protocol) 是一个协议，用于让AI应用连接到外部数据源和工具。通过集成MCP服务，您的agent可以直接从MCP服务器获取数据，而无需上传和维护本地文档。

## 🔧 配置步骤

### 1. 环境变量配置

在 `backend/.env` 文件中添加以下配置：

```bash
# MCP服务配置
MCP_ENABLED=true
MCP_BASE_URL=https://your-mcp-server.com/api
MCP_API_KEY=your_mcp_api_key_here
MCP_TIMEOUT=30
MCP_RESOURCE_FILTERS={"type": "document", "status": "active"}
MCP_CONTENT_FORMAT=text
MCP_MAX_ITEMS=100
```

### 2. 配置说明

- **MCP_ENABLED**: 是否启用MCP服务 (true/false)
- **MCP_BASE_URL**: MCP服务器的基础URL
- **MCP_API_KEY**: MCP服务的API密钥（如果需要认证）
- **MCP_TIMEOUT**: 请求超时时间（秒）
- **MCP_RESOURCE_FILTERS**: JSON格式的资源过滤条件
- **MCP_CONTENT_FORMAT**: 内容格式 (text, json, markdown等)
- **MCP_MAX_ITEMS**: 每次获取的最大数据项数量

### 3. 验证配置

启动服务后，可以通过以下API端点验证MCP连接：

```bash
# 检查MCP状态
curl http://localhost:8000/api/mcp/status

# 连接到MCP服务器
curl -X POST http://localhost:8000/api/mcp/connect

# 列出可用资源
curl http://localhost:8000/api/mcp/resources
```

## 🚀 使用方式

### 1. 自动集成到RAG系统

当MCP启用后，`EnhancedRAGService` 会自动使用MCP作为数据源：

```python
# 在enhanced_rag_service.py中，MCP数据源会被自动初始化
# 并且在搜索时会优先使用MCP数据
```

### 2. 手动同步MCP数据

```bash
# 同步MCP数据到知识库
curl -X POST http://localhost:8000/api/mcp/sync

# 带查询条件同步
curl -X POST http://localhost:8000/api/mcp/sync \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone"}'
```

### 3. 搜索MCP资源

```bash
# 搜索MCP资源
curl -X POST http://localhost:8000/api/mcp/resources/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "iPhone 15 Pro",
    "limit": 10,
    "filters": {"type": "product"}
  }'
```

### 4. 获取特定资源

```bash
# 获取资源详情
curl http://localhost:8000/api/mcp/resources/{resource_id}?format=text
```

## 📊 API端点

### MCP管理端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/mcp/status` | GET | 获取MCP服务状态 |
| `/api/mcp/connect` | POST | 连接到MCP服务器 |
| `/api/mcp/disconnect` | POST | 断开MCP服务器连接 |

### 资源端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/mcp/resources` | GET | 列出所有可用资源 |
| `/api/mcp/resources/{resource_id}` | GET | 获取指定资源 |
| `/api/mcp/resources/search` | POST | 搜索资源 |

### 工具端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/mcp/tools` | GET | 列出可用工具 |
| `/api/mcp/tools/{tool_name}` | POST | 调用工具 |

### 数据同步端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/mcp/sync` | POST | 同步MCP数据到知识库 |

## 🔄 工作流程

### 传统方式（本地上传）

```
用户上传文档 → 文档处理 → 向量化 → 存储到本地知识库 → RAG搜索
```

### MCP方式（远程数据）

```
MCP服务器提供数据 → MCP客户端获取 → 自动向量化 → 存储到知识库 → RAG搜索
```

## 🎯 优势

1. **无需维护本地文档**: 数据直接从MCP服务器获取
2. **实时数据更新**: MCP服务器可以实时更新数据
3. **集中化管理**: 多个agent可以共享同一个MCP数据源
4. **灵活的过滤**: 可以通过过滤条件获取特定类型的数据
5. **工具集成**: 可以使用MCP提供的工具扩展功能

## ⚠️ 注意事项

1. **网络连接**: 确保服务器可以访问MCP服务器URL
2. **API密钥**: 正确配置API密钥以确保认证成功
3. **超时设置**: 根据网络情况调整超时时间
4. **数据缓存**: 系统会自动缓存MCP数据以提高性能
5. **错误处理**: 如果MCP连接失败，系统会回退到本地数据源（如果配置了）

## 🔍 故障排除

### 问题1: MCP连接失败

```bash
# 检查MCP服务状态
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

## 📝 示例配置

### 完整的.env配置示例

```bash
# MCP配置
MCP_ENABLED=true
MCP_BASE_URL=https://api.mcpworld.com/v1
MCP_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
MCP_TIMEOUT=30
MCP_RESOURCE_FILTERS={"type": "document", "category": "product"}
MCP_CONTENT_FORMAT=text
MCP_MAX_ITEMS=100
```

### Python代码示例

```python
from app.services.mcp_service import MCPService, MCPDataSource

# 创建MCP服务客户端
async with MCPService(
    base_url="https://api.mcpworld.com/v1",
    api_key="your_api_key"
) as mcp_service:
    # 获取资源列表
    resources = await mcp_service.list_resources()
    
    # 搜索资源
    results = await mcp_service.search_resources("iPhone", limit=10)
    
    # 获取资源内容
    content = await mcp_service.get_resource_content("resource_id")
```

## 📚 相关文档

- [MCP官方文档](https://modelcontextprotocol.io/)
- [API文档](./API.md)
- [RAG系统指南](./ECOMMERCE_RAG_GUIDE.md)

---

**最后更新**: 2025-01-XX
**版本**: 2.1.0

