from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.schemas import (
    AgentCreate, AgentResponse, TaskCreate, TaskResponse,
    AgentCollaborationCreate, AgentCollaborationResponse
)
from ..services.agent_service import AgentService, get_agent_service
from ..core.database import get_db

router = APIRouter()

@router.post("/agents", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db)
):
    """创建新的Agent"""
    try:
        agent_service = get_agent_service(db)
        return await agent_service.create_agent(agent_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents", response_model=List[AgentResponse])
async def get_agents(
    db: Session = Depends(get_db)
):
    """获取所有活跃的Agent"""
    try:
        agent_service = get_agent_service(db)
        return agent_service.get_active_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/tasks", response_model=TaskResponse)
async def create_agent_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    """创建Agent任务"""
    try:
        agent_service = get_agent_service(db)
        return await agent_service.create_task(task_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/tasks/{session_id}", response_model=List[TaskResponse])
async def get_agent_tasks(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取会话的任务列表"""
    try:
        agent_service = get_agent_service(db)
        return agent_service.get_agent_tasks(session_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/tasks/{task_id}")
async def get_task_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取任务状态"""
    try:
        from ..models.models import AgentTask
        task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": task.task_id,
            "status": task.status,
            "result": task.result,
            "error_message": task.error_message,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/collaborations", response_model=AgentCollaborationResponse)
async def create_agent_collaboration(
    collaboration_data: AgentCollaborationCreate,
    db: Session = Depends(get_db)
):
    """创建Agent协作"""
    try:
        agent_service = get_agent_service(db)
        return await agent_service.create_collaboration(collaboration_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/collaborations/{collaboration_id}")
async def get_collaboration_status(
    collaboration_id: int,
    db: Session = Depends(get_db)
):
    """获取协作状态"""
    try:
        from ..models.models import AgentCollaboration
        collaboration = db.query(AgentCollaboration).filter(
            AgentCollaboration.id == collaboration_id
        ).first()

        if not collaboration:
            raise HTTPException(status_code=404, detail="Collaboration not found")

        return {
            "id": collaboration.id,
            "session_id": collaboration.session_id,
            "collaboration_type": collaboration.collaboration_type,
            "participants": collaboration.participants,
            "status": collaboration.status,
            "result": collaboration.result,
            "created_at": collaboration.created_at,
            "completed_at": collaboration.completed_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/collaborations/session/{session_id}")
async def get_session_collaborations(
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取会话的协作列表"""
    try:
        from ..models.models import AgentCollaboration
        collaborations = db.query(AgentCollaboration).filter(
            AgentCollaboration.session_id == session_id
        ).order_by(AgentCollaboration.created_at.desc()).all()

        return [
            {
                "id": collab.id,
                "collaboration_type": collab.collaboration_type,
                "participants": collab.participants,
                "status": collab.status,
                "created_at": collab.created_at,
                "completed_at": collab.completed_at
            }
            for collab in collaborations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/execute")
async def execute_agent_task_direct(
    agent_id: int,
    task_data: dict,
    db: Session = Depends(get_db)
):
    """直接执行Agent任务（用于测试）"""
    try:
        agent_service = get_agent_service(db)
        result = await agent_service.execute_agent_task(agent_id, task_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))