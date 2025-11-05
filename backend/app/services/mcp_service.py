"""
MCP (Model Context Protocol) 服务集成
用于连接到MCP服务器并获取数据，替代本地文档上传
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class MCPService:
    """MCP服务客户端"""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        """
        初始化MCP服务客户端

        Args:
            base_url: MCP服务器的基础URL
            api_key: API密钥（如果需要认证）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.disconnect()

    async def connect(self):
        """连接到MCP服务器"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self._get_headers()
            )
            # 测试连接
            health = await self.health_check()
            if health.get("status") == "healthy":
                self._connected = True
                logger.info(f"成功连接到MCP服务器: {self.base_url}")
            else:
                logger.warning(f"MCP服务器健康检查失败: {health}")
        except Exception as e:
            logger.error(f"连接MCP服务器失败: {e}")
            self._connected = False
            raise

    async def disconnect(self):
        """断开MCP服务器连接"""
        if self.session:
            await self.session.close()
            self.session = None
            self._connected = False
            logger.info("已断开MCP服务器连接")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def health_check(self) -> Dict[str, Any]:
        """检查MCP服务器健康状态"""
        try:
            url = urljoin(self.base_url, "/health")
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"MCP健康检查失败: {e}")
            return {"status": "error", "error": str(e)}

    async def list_resources(self) -> List[Dict[str, Any]]:
        """列出可用的资源"""
        try:
            url = urljoin(self.base_url, "/resources")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("resources", [])
                else:
                    logger.error(f"获取资源列表失败: HTTP {response.status}")
                    return []
        except Exception as e:
            logger.error(f"获取MCP资源列表失败: {e}")
            return []

    async def get_resource(self, resource_id: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        获取指定资源

        Args:
            resource_id: 资源ID
            params: 可选的查询参数

        Returns:
            资源数据，如果失败返回None
        """
        try:
            url = urljoin(self.base_url, f"/resources/{resource_id}")
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"获取资源失败: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"获取MCP资源失败: {e}")
            return None

    async def search_resources(self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索资源

        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            filters: 可选的过滤条件

        Returns:
            搜索结果列表
        """
        try:
            url = urljoin(self.base_url, "/resources/search")
            payload = {
                "query": query,
                "limit": limit
            }
            if filters:
                payload["filters"] = filters

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"搜索资源失败: HTTP {response.status}")
                    return []
        except Exception as e:
            logger.error(f"MCP资源搜索失败: {e}")
            return []

    async def get_resource_content(self, resource_id: str, format: str = "text") -> Optional[str]:
        """
        获取资源内容

        Args:
            resource_id: 资源ID
            format: 内容格式 (text, json, markdown等)

        Returns:
            资源内容字符串
        """
        try:
            url = urljoin(self.base_url, f"/resources/{resource_id}/content")
            params = {"format": format}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("content", "")
                else:
                    logger.error(f"获取资源内容失败: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"获取MCP资源内容失败: {e}")
            return None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用的工具"""
        try:
            url = urljoin(self.base_url, "/tools")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("tools", [])
                else:
                    logger.error(f"获取工具列表失败: HTTP {response.status}")
                    return []
        except Exception as e:
            logger.error(f"获取MCP工具列表失败: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        调用工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        try:
            url = urljoin(self.base_url, f"/tools/{tool_name}")
            async with self.session.post(url, json={"arguments": arguments}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"调用工具失败: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"调用MCP工具失败: {e}")
            return None

    async def stream_resource(self, resource_id: str, chunk_size: int = 1024):
        """流式获取资源内容"""
        try:
            url = urljoin(self.base_url, f"/resources/{resource_id}/stream")
            async with self.session.get(url) as response:
                if response.status == 200:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        yield chunk
                else:
                    logger.error(f"流式获取资源失败: HTTP {response.status}")
        except Exception as e:
            logger.error(f"流式获取MCP资源失败: {e}")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self.session is not None


class MCPDataSource:
    """MCP数据源适配器，用于集成到RAG系统"""

    def __init__(self, mcp_service: MCPService, config: Dict[str, Any]):
        """
        初始化MCP数据源

        Args:
            mcp_service: MCP服务客户端实例
            config: 数据源配置
        """
        self.mcp_service = mcp_service
        self.config = config
        self.name = config.get("name", "mcp")
        self.resource_filters = config.get("resource_filters", {})
        self.update_frequency = config.get("update_frequency", "hourly")
        self.last_updated: Optional[datetime] = None

    async def fetch_data(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从MCP服务器获取数据

        Args:
            query: 可选的搜索查询

        Returns:
            数据项列表
        """
        data_items = []

        try:
            if query:
                # 使用搜索功能
                resources = await self.mcp_service.search_resources(
                    query=query,
                    limit=self.config.get("max_items", 100),
                    filters=self.resource_filters
                )
            else:
                # 获取所有可用资源
                resources = await self.mcp_service.list_resources()

            # 处理每个资源
            for resource in resources:
                resource_id = resource.get("id") or resource.get("resource_id")
                if not resource_id:
                    continue

                # 获取资源内容
                content = await self.mcp_service.get_resource_content(
                    resource_id,
                    format=self.config.get("content_format", "text")
                )

                if content:
                    data_item = {
                        "id": resource_id,
                        "title": resource.get("name") or resource.get("title") or resource_id,
                        "content": content,
                        "source": "mcp",
                        "source_url": resource.get("uri") or resource.get("url"),
                        "metadata": {
                            "resource_type": resource.get("type") or resource.get("mimeType"),
                            "description": resource.get("description"),
                            "created_at": resource.get("createdAt"),
                            "updated_at": resource.get("updatedAt"),
                            "tags": resource.get("tags", [])
                        },
                        "hash": self._generate_hash(resource_id + content)
                    }
                    data_items.append(data_item)

            self.last_updated = datetime.utcnow()
            logger.info(f"从MCP获取了 {len(data_items)} 个数据项")

        except Exception as e:
            logger.error(f"从MCP获取数据失败: {e}")
            raise

        return data_items

    def _generate_hash(self, text: str) -> str:
        """生成数据哈希"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索MCP资源

        Args:
            query: 搜索查询
            limit: 结果数量限制

        Returns:
            搜索结果列表
        """
        resources = await self.mcp_service.search_resources(
            query=query,
            limit=limit,
            filters=self.resource_filters
        )

        results = []
        for resource in resources:
            resource_id = resource.get("id") or resource.get("resource_id")
            content = await self.mcp_service.get_resource_content(resource_id)
            
            if content:
                results.append({
                    "id": resource_id,
                    "title": resource.get("name") or resource_id,
                    "content": content,
                    "score": resource.get("score", 1.0),
                    "source": "mcp",
                    "metadata": resource
                })

        return results

