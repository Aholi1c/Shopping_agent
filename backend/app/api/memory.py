from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.schemas import (
    MemoryCreate, MemoryResponse, MemorySearchRequest, WorkingMemoryUpdate
)
from ..services.memory_service import MemoryService, get_memory_service
from ..core.database import get_db

router = APIRouter()

@router.post("/memories", response_model=MemoryResponse)
async def create_memory(
    memory_data: MemoryCreate,
    db: Session = Depends(get_db)
):
    """创建新的记忆"""
    try:
        memory_service = get_memory_service(db)
        return await memory_service.create_memory(memory_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories/search", response_model=List[MemoryResponse])
async def search_memories(
    query: str,
    memory_type: Optional[str] = None,
    limit: int = 10,
    threshold: float = 0.7,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """搜索记忆"""
    try:
        memory_service = get_memory_service(db)
        search_request = MemorySearchRequest(
            query=query,
            memory_type=memory_type,
            limit=limit,
            threshold=threshold,
            user_id=user_id
        )
        return memory_service.search_memories(search_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/working-memory/{session_id}")
async def get_working_memory(
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取工作记忆"""
    try:
        memory_service = get_memory_service(db)
        working_memory = memory_service.get_working_memory(session_id)
        return working_memory or {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/working-memory/{session_id}")
async def update_working_memory(
    session_id: str,
    update_data: WorkingMemoryUpdate,
    db: Session = Depends(get_db)
):
    """更新工作记忆"""
    try:
        memory_service = get_memory_service(db)
        return await memory_service.update_working_memory(update_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/working-memory/{session_id}")
async def clear_working_memory(
    session_id: str,
    db: Session = Depends(get_db)
):
    """清除工作记忆"""
    try:
        memory_service = get_memory_service(db)
        memory_service.clear_working_memory(session_id)
        return {"message": "Working memory cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memories/consolidate")
async def consolidate_memories(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """整合记忆（工作记忆到长期记忆）"""
    try:
        memory_service = get_memory_service(db)
        await memory_service.consolidate_memories(user_id)
        return {"message": "Memory consolidation completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories/context/{session_id}")
async def get_relevant_context(
    session_id: str,
    query: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取相关的上下文信息"""
    try:
        memory_service = get_memory_service(db)
        context = await memory_service.get_relevant_context(query, session_id, user_id)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))