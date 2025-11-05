"""
MCP服务API端点
用于管理和使用MCP (Model Context Protocol) 服务
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from ..core.database import get_db
from ..core.config import settings
from ..services.mcp_service import MCPService, MCPDataSource
from ..models.schemas import MCPResourceResponse, MCPSearchRequest, MCPSearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局MCP服务实例
_mcp_service: Optional[MCPService] = None
_mcp_data_source: Optional[MCPDataSource] = None


def get_mcp_service() -> Optional[MCPService]:
    """获取MCP服务实例"""
    global _mcp_service
    
    if not settings.mcp_enabled:
        return None
    
    if _mcp_service is None and settings.mcp_base_url:
        _mcp_service = MCPService(
            base_url=settings.mcp_base_url,
            api_key=settings.mcp_api_key,
            timeout=settings.mcp_timeout
        )
    
    return _mcp_service


async def get_mcp_data_source() -> Optional[MCPDataSource]:
    """获取MCP数据源实例"""
    global _mcp_data_source
    
    mcp_service = get_mcp_service()
    if not mcp_service:
        return None
    
    if _mcp_data_source is None:
        import json
        resource_filters = {}
        if settings.mcp_resource_filters:
            try:
                resource_filters = json.loads(settings.mcp_resource_filters)
            except:
                pass
        
        config = {
            "name": "mcp",
            "resource_filters": resource_filters,
            "content_format": settings.mcp_content_format,
            "max_items": settings.mcp_max_items,
            "update_frequency": "hourly"
        }
        _mcp_data_source = MCPDataSource(mcp_service, config)
    
    return _mcp_data_source


@router.get("/status")
async def get_mcp_status():
    """获取MCP服务状态"""
    try:
        mcp_service = get_mcp_service()
        if not mcp_service:
            return {
                "enabled": False,
                "connected": False,
                "message": "MCP服务未启用或未配置"
            }
        
        if not mcp_service.is_connected():
            await mcp_service.connect()
        
        health = await mcp_service.health_check()
        
        return {
            "enabled": settings.mcp_enabled,
            "connected": mcp_service.is_connected(),
            "base_url": settings.mcp_base_url,
            "health": health
        }
    except Exception as e:
        logger.error(f"获取MCP状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect")
async def connect_mcp():
    """连接到MCP服务器"""
    try:
        mcp_service = get_mcp_service()
        if not mcp_service:
            raise HTTPException(status_code=400, detail="MCP服务未配置")
        
        await mcp_service.connect()
        
        return {
            "message": "已成功连接到MCP服务器",
            "connected": mcp_service.is_connected()
        }
    except Exception as e:
        logger.error(f"连接MCP服务器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect_mcp():
    """断开MCP服务器连接"""
    try:
        global _mcp_service, _mcp_data_source
        
        if _mcp_service:
            await _mcp_service.disconnect()
            _mcp_service = None
            _mcp_data_source = None
        
        return {"message": "已断开MCP服务器连接"}
    except Exception as e:
        logger.error(f"断开MCP连接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources", response_model=List[MCPResourceResponse])
async def list_resources(
    limit: int = Query(100, description="返回结果数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """列出可用的MCP资源"""
    try:
        mcp_service = get_mcp_service()
        if not mcp_service or not mcp_service.is_connected():
            raise HTTPException(status_code=400, detail="MCP服务未连接")
        
        resources = await mcp_service.list_resources()
        
        # 应用分页
        paginated_resources = resources[offset:offset + limit]
        
        return [
            MCPResourceResponse(
                id=res.get("id") or res.get("resource_id", ""),
                name=res.get("name") or res.get("title", ""),
                type=res.get("type") or res.get("mimeType", ""),
                description=res.get("description", ""),
                uri=res.get("uri") or res.get("url", ""),
                metadata=res.get("metadata", {})
            )
            for res in paginated_resources
        ]
    except Exception as e:
        logger.error(f"获取MCP资源列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/{resource_id}")
async def get_resource(
    resource_id: str,
    format: str = Query("text", description="内容格式")
):
    """获取指定资源"""
    try:
        mcp_service = get_mcp_service()
        if not mcp_service or not mcp_service.is_connected():
            raise HTTPException(status_code=400, detail="MCP服务未连接")
        
        resource = await mcp_service.get_resource(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        
        content = await mcp_service.get_resource_content(resource_id, format=format)
        
        return {
            "resource": resource,
            "content": content,
            "format": format
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取MCP资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resources/search", response_model=MCPSearchResponse)
async def search_resources(
    request: MCPSearchRequest
):
    """搜索MCP资源"""
    try:
        mcp_service = get_mcp_service()
        if not mcp_service or not mcp_service.is_connected():
            raise HTTPException(status_code=400, detail="MCP服务未连接")
        
        results = await mcp_service.search_resources(
            query=request.query,
            limit=request.limit,
            filters=request.filters
        )
        
        return MCPSearchResponse(
            query=request.query,
            results=results,
            count=len(results)
        )
    except Exception as e:
        logger.error(f"搜索MCP资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools():
    """列出可用的MCP工具"""
    try:
        mcp_service = get_mcp_service()
        if not mcp_service or not mcp_service.is_connected():
            raise HTTPException(status_code=400, detail="MCP服务未连接")
        
        tools = await mcp_service.list_tools()
        
        return {
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        logger.error(f"获取MCP工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_name}")
async def call_tool(
    tool_name: str,
    arguments: Dict[str, Any]
):
    """调用MCP工具"""
    try:
        mcp_service = get_mcp_service()
        if not mcp_service or not mcp_service.is_connected():
            raise HTTPException(status_code=400, detail="MCP服务未连接")
        
        result = await mcp_service.call_tool(tool_name, arguments)
        
        if result is None:
            raise HTTPException(status_code=500, detail="工具调用失败")
        
        return {
            "tool_name": tool_name,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"调用MCP工具失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_mcp_data(
    query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """同步MCP数据到知识库"""
    try:
        mcp_data_source = await get_mcp_data_source()
        if not mcp_data_source:
            raise HTTPException(status_code=400, detail="MCP数据源未配置")
        
        # 从MCP获取数据
        data_items = await mcp_data_source.fetch_data(query)
        
        # 这里可以集成到enhanced_rag_service来存储数据
        # 暂时返回获取的数据项
        return {
            "message": "MCP数据同步成功",
            "items_count": len(data_items),
            "items": data_items[:10]  # 只返回前10个作为示例
        }
    except Exception as e:
        logger.error(f"同步MCP数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

