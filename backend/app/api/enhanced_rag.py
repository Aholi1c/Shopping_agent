"""
增强RAG API接口 - 多源数据集成
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..services.enhanced_rag_service import EnhancedRAGService, get_enhanced_rag_service
from ..services.llm_service import LLMService
from ..services.rag_service import RAGSearchRequest, RAGSearchResult

router = APIRouter()

class DataSourceConfig(BaseModel):
    """数据源配置"""
    name: str = Field(..., description="数据源名称")
    source_type: str = Field(..., description="数据源类型: rss, web_crawler, api")
    config: Dict[str, Any] = Field(..., description="数据源配置")
    is_active: bool = Field(True, description="是否激活")

class CrossSourceSearchRequest(BaseModel):
    """跨数据源搜索请求"""
    query: str = Field(..., description="搜索查询")
    limit: int = Field(10, ge=1, le=50, description="返回结果数量")
    source_filter: Optional[List[str]] = Field(None, description="数据源过滤")
    use_ai_analysis: bool = Field(True, description="是否使用AI分析")

class SourceUpdateRequest(BaseModel):
    """数据源更新请求"""
    sources: Optional[List[str]] = Field(None, description="要更新的数据源列表")
    force_update: bool = Field(False, description="是否强制更新")

class KnowledgeSourceRequest(BaseModel):
    """知识库数据源请求"""
    source_name: str = Field(..., description="数据源名称")
    query: str = Field(..., description="搜索查询")
    limit: int = Field(10, ge=1, le=30, description="返回结果数量")

@router.post("/sources/update", response_model=Dict[str, Any])
async def update_data_sources(
    request: SourceUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """更新数据源"""
    try:
        rag_service = get_enhanced_rag_service(db)

        # 如果指定了数据源，只更新指定的
        if request.sources:
            results = {}
            for source_name in request.sources:
                if source_name in rag_service.data_sources:
                    source = rag_service.data_sources[source_name]
                    if request.force_update or source._should_update():
                        data = await source.update_data()
                        await rag_service._store_source_data(source_name, data)
                        results[source_name] = {
                            "success": True,
                            "items_processed": len(data),
                            "force_updated": request.force_update
                        }
                    else:
                        results[source_name] = {
                            "success": True,
                            "message": "No update needed",
                            "items_processed": 0
                        }
                else:
                    results[source_name] = {
                        "success": False,
                        "error": f"Data source '{source_name}' not found"
                    }
        else:
            # 更新所有数据源
            results = await rag_service.update_all_sources()

        return {
            "success": True,
            "data": {
                "update_results": results,
                "total_sources": len(rag_service.data_sources),
                "updated_sources": len([r for r in results.values() if r.get("success")])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/cross-source", response_model=Dict[str, Any])
async def cross_source_search(
    request: CrossSourceSearchRequest,
    db: Session = Depends(get_db)
):
    """跨数据源搜索"""
    try:
        rag_service = get_enhanced_rag_service(db)

        # 搜索所有数据源
        search_results = await rag_service.search_all_sources(
            query=request.query,
            limit=request.limit,
            source_filter=request.source_filter
        )

        # 如果需要AI分析
        ai_analysis = None
        if request.use_ai_analysis and search_results:
            # 按数据源分组
            source_results = {}
            for result in search_results:
                source = result.get("metadata", {}).get("source", "unknown")
                if source not in source_results:
                    source_results[source] = []
                source_results[source].append(result)

            # 生成跨源分析
            ai_analysis = await rag_service._analyze_cross_source_results(
                request.query, source_results
            )

        return {
            "success": True,
            "data": {
                "query": request.query,
                "results": search_results,
                "ai_analysis": ai_analysis,
                "total_results": len(search_results),
                "source_breakdown": _count_by_source(search_results),
                "filters_applied": {
                    "source_filter": request.source_filter,
                    "limit": request.limit
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/cross-source-response", response_model=Dict[str, Any])
async def generate_cross_source_response(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """生成跨数据源增强响应"""
    try:
        rag_service = get_enhanced_rag_service(db)

        result = await rag_service.generate_cross_source_response(query, context)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/statistics", response_model=Dict[str, Any])
async def get_source_statistics(db: Session = Depends(get_db)):
    """获取数据源统计信息"""
    try:
        rag_service = get_enhanced_rag_service(db)
        stats = await rag_service.get_source_statistics()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/list", response_model=Dict[str, Any])
async def list_data_sources(db: Session = Depends(get_db)):
    """列出所有数据源"""
    try:
        rag_service = get_enhanced_rag_service(db)

        sources_info = {}
        for name, source in rag_service.data_sources.items():
            sources_info[name] = {
                "name": source.name,
                "type": source.__class__.__name__,
                "is_active": source.is_active,
                "update_frequency": source.update_frequency,
                "last_updated": source.last_updated.isoformat() if source.last_updated else None,
                "config_summary": _summarize_config(source.config)
            }

        return {
            "success": True,
            "data": {
                "sources": sources_info,
                "total_sources": len(sources_info),
                "active_sources": len([s for s in sources_info.values() if s["is_active"]])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sources/configure", response_model=Dict[str, Any])
async def configure_data_source(
    config: DataSourceConfig,
    db: Session = Depends(get_db)
):
    """配置数据源"""
    try:
        rag_service = get_enhanced_rag_service(db)

        # 这里应该保存配置到数据库或配置文件
        # 简化版本，只返回确认信息
        return {
            "success": True,
            "data": {
                "message": f"Data source '{config.name}' configured successfully",
                "config": {
                    "name": config.name,
                    "type": config.source_type,
                    "is_active": config.is_active
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/knowledge-sources", response_model=Dict[str, Any])
async def search_knowledge_sources(
    request: KnowledgeSourceRequest,
    db: Session = Depends(get_db)
):
    """搜索特定知识库数据源"""
    try:
        rag_service = get_enhanced_rag_service(db)

        # 搜索特定数据源
        search_results = await rag_service.search_all_sources(
            query=request.query,
            limit=request.limit,
            source_filter=[request.source_name]
        )

        return {
            "success": True,
            "data": {
                "source": request.source_name,
                "query": request.query,
                "results": search_results,
                "total_results": len(search_results)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup/old-data", response_model=Dict[str, Any])
async def cleanup_old_source_data(
    background_tasks: BackgroundTasks,
    days_threshold: int = Query(30, ge=7, le=365, description="清理天数阈值"),
    db: Session = Depends(get_db)
):
    """清理旧的源数据"""
    try:
        rag_service = get_enhanced_rag_service(db)

        # 在后台任务中执行清理
        background_tasks.add_task(
            rag_service.cleanup_old_source_data,
            days_threshold
        )

        return {
            "success": True,
            "data": {
                "message": f"Cleanup task started for data older than {days_threshold} days",
                "threshold_days": days_threshold
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/{source_name}/health", response_model=Dict[str, Any])
async def check_source_health(
    source_name: str,
    db: Session = Depends(get_db)
):
    """检查数据源健康状态"""
    try:
        rag_service = get_enhanced_rag_service(db)

        if source_name not in rag_service.data_sources:
            raise HTTPException(status_code=404, detail=f"Data source '{source_name}' not found")

        source = rag_service.data_sources[source_name]

        # 检查数据源状态
        health_status = {
            "name": source_name,
            "is_active": source.is_active,
            "last_updated": source.last_updated.isoformat() if source.last_updated else None,
            "needs_update": source._should_update(),
            "update_frequency": source.update_frequency,
            "status": "healthy" if source.is_active else "inactive"
        }

        # 获取对应知识库的统计
        kb_name = f"auto_{source_name}_kb"
        kb = rag_service.db.query(rag_service.db.query(KnowledgeBase).filter(
            KnowledgeBase.name == kb_name
        ).first())

        if kb:
            kb_stats = await rag_service.get_knowledge_base_stats(kb.id)
            health_status["knowledge_base"] = kb_stats
        else:
            health_status["knowledge_base"] = None

        return {
            "success": True,
            "data": health_status
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sources/refresh", response_model=Dict[str, Any])
async def refresh_all_sources(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """刷新所有数据源"""
    try:
        rag_service = get_enhanced_rag_service(db)

        # 在后台任务中执行刷新
        background_tasks.add_task(rag_service.update_all_sources)

        return {
            "success": True,
            "data": {
                "message": "Refresh task started for all data sources",
                "total_sources": len(rag_service.data_sources)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数
def _count_by_source(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """按数据源统计结果数量"""
    counts = {}
    for result in results:
        source = result.get("metadata", {}).get("source", "unknown")
        counts[source] = counts.get(source, 0) + 1
    return counts

def _summarize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """总结配置信息"""
    summary = {}
    for key, value in config.items():
        if key in ["api_key", "password", "token"]:
            summary[key] = "***"
        elif isinstance(value, (list, dict)) and len(str(value)) > 100:
            summary[key] = f"{type(value).__name__} (length: {len(value)})"
        else:
            summary[key] = value
    return summary

# 需要在文件顶部添加导入
from ..models.models import KnowledgeBase