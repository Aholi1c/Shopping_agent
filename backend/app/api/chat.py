from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
# Form已暂时移除，因为python-multipart安装有问题
# from fastapi import Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime

from ..models.schemas import (
    ChatRequest, ChatResponse, ConversationResponse,
    MessageResponse, ConversationCreate, FileUploadResponse,
    EnhancedChatRequest, EnhancedChatResponse
)
from ..services.conversation_service import ConversationService
from ..services.media_service import media_service
from ..services.memory_service import MemoryService, get_memory_service
from ..services.rag_service import RAGService, get_rag_service
from ..services.llm_service import LLMService, get_llm_service
from ..core.database import get_db
from ..core.config import settings
from fastapi.responses import FileResponse
import time

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    处理聊天消息
    """
    conversation_service = ConversationService(db)
    try:
        response = await conversation_service.process_chat_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 暂时注释掉文件上传路由，因为FastAPI需要python-multipart来处理File参数
# 当python-multipart正确安装后，可以取消注释
# @router.post("/chat/upload", response_model=ChatResponse)
# async def chat_with_upload(
#     request: ChatRequest,
#     file: Optional[UploadFile] = File(None),
#     db: Session = Depends(get_db)
# ):
#     """
#     处理带文件上传的聊天消息（使用JSON body替代Form）
#     """
#     try:
#         file_path = None
#         if file:
#             # 保存文件
#             file_path = await media_service.save_upload_file(file, "chat")
# 
#             # 确定文件类型
#             file_type = "image" if file.content_type and file.content_type.startswith("image/") else "audio"
# 
#             # 处理文件
#             if file_type == "image":
#                 processed_path, _ = await media_service.process_image(file_path)
#                 request.media_url = processed_path
#                 request.message_type = file_type
#         else:
#             file_type = request.message_type or "text"
# 
#         conversation_service = ConversationService(db)
#         response = await conversation_service.process_chat_message(request)
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    user_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取对话列表
    """
    conversation_service = ConversationService(db)
    conversations = conversation_service.get_user_conversations(user_id, limit)
    return conversations

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    获取对话详情
    """
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db)
):
    """
    创建新对话
    """
    conversation_service = ConversationService(db)
    conversation = conversation_service.create_conversation(conversation_data)
    return conversation

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    删除对话
    """
    conversation_service = ConversationService(db)
    success = conversation_service.delete_conversation(conversation_id)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted successfully"}

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    获取对话的消息历史
    """
    conversation_service = ConversationService(db)
    messages = conversation_service.get_conversation_messages(conversation_id)
    return messages

# 暂时注释掉File上传路由，因为FastAPI需要python-multipart来处理File参数
# @router.post("/upload", response_model=FileUploadResponse)
# async def upload_file(
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
    """
    上传文件
    """
    try:
        # 验证文件类型
        allowed_types = ['jpg', 'jpeg', 'png', 'gif', 'mp3', 'wav', 'mp4', 'mov']
        if not media_service.validate_file_type(file.filename, allowed_types):
            raise HTTPException(status_code=400, detail="File type not allowed")

        # 验证文件大小
        file_size = 0
        if hasattr(file, 'size'):
            file_size = file.size
        if not media_service.validate_file_size(file_size):
            raise HTTPException(status_code=400, detail="File too large")

        # 保存文件
        file_path = await media_service.save_upload_file(file)
        file_info = media_service.get_file_info(file_path)

        return FileUploadResponse(
            id=1,  # 这里应该保存到数据库并返回真实ID
            filename=os.path.basename(file_path),
            original_name=file.filename,
            file_type=file_info.get('extension', ''),
            file_size=file_info.get('size', 0),
            file_url=file_path,
            uploaded_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{filename}")
async def get_file(filename: str):
    """
    获取文件
    """
    file_path = os.path.join(settings.upload_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)

@router.post("/chat/enhanced", response_model=EnhancedChatResponse)
async def enhanced_chat(
    request: EnhancedChatRequest,
    db: Session = Depends(get_db)
):
    """
    增强的聊天接口，支持记忆、RAG、多Agent协作
    """
    start_time = time.time()

    try:
        # 初始化服务
        memory_service = get_memory_service(db)
        rag_service = get_rag_service(db)
        llm_service = get_llm_service(db)
        conversation_service = ConversationService(db)

        # 获取或创建对话
        if not request.conversation_id:
            conversation = conversation_service.create_conversation(
                type('', (), {"title": request.message[:50] + "..."})(),
                None
            )
            request.conversation_id = conversation.id

        # 构建增强的上下文
        context_parts = []
        memory_used = False
        rag_results = []
        agent_collaboration_result = None

        # 1. 记忆检索
        if request.use_memory:
            memory_context = await memory_service.get_relevant_context(
                request.message, f"session_{request.conversation_id}"
            )
            if memory_context.get("relevant_memories"):
                context_parts.append("Memory Context:")
                for mem in memory_context["relevant_memories"]:
                    context_parts.append(f"- {mem['content']} (Type: {mem['type']}, Importance: {mem['importance']})")
                memory_used = True

        # 2. RAG检索
        if request.use_rag and request.knowledge_base_ids:
            from ..models.schemas import RAGSearchRequest
            rag_search = RAGSearchRequest(
                query=request.message,
                knowledge_base_ids=request.knowledge_base_ids,
                limit=5,
                threshold=0.7
            )
            rag_results = await rag_service.search_knowledge_base(rag_search)
            if rag_results:
                context_parts.append("Knowledge Base Context:")
                for i, result in enumerate(rag_results, 1):
                    context_parts.append(f"[{i}] {result.content}")

        # 3. 多Agent协作
        if request.agent_collaboration and request.agents:
            from ..models.schemas import AgentCollaborationCreate, CollaborationType
            from ..services.agent_service import AgentService, get_agent_service

            agent_service = get_agent_service(db)
            collab_request = AgentCollaborationCreate(
                session_id=f"session_{request.conversation_id}",
                collaboration_type=request.collaboration_type or CollaborationType.SEQUENTIAL,
                participants=request.agents,
                workflow={
                    "main_task": {
                        "query": request.message,
                        "context": "\n".join(context_parts) if context_parts else ""
                    }
                },
                task_data={"query": request.message}
            )

            collab_result = await agent_service.create_collaboration(collab_request)
            agent_collaboration_result = {
                "collaboration_id": collab_result.id,
                "type": collab_result.collaboration_type,
                "participants": collab_result.participants,
                "status": collab_result.status
            }

        # 4. 构建最终提示
        enhanced_prompt = request.message
        if context_parts:
            enhanced_prompt = f"""
Context Information:
{chr(10).join(context_parts)}

User Question: {request.message}

Please provide a comprehensive response considering all the context provided above.
"""

        # 5. 调用LLM
        llm_response = await llm_service.chat_completion([
            {"role": "system", "content": "You are an AI assistant with access to memory, knowledge bases, and multi-agent collaboration. Use all available context to provide the best possible response."},
            {"role": "user", "content": enhanced_prompt}
        ], model=request.model, max_tokens=request.max_tokens, temperature=request.temperature)

        # 6. 存储到记忆系统
        if request.use_memory:
            from ..models.schemas import MemoryCreate
            user_memory = MemoryCreate(
                content=request.message,
                memory_type="episodic",
                importance_score=0.6,
                metadata={"source": "user_input", "conversation_id": request.conversation_id}
            )
            await memory_service.create_memory(user_memory)

            assistant_memory = MemoryCreate(
                content=llm_response["content"],
                memory_type="episodic",
                importance_score=0.8,
                metadata={"source": "assistant_response", "conversation_id": request.conversation_id}
            )
            await memory_service.create_memory(assistant_memory)

        # 7. 更新工作记忆
        await memory_service.update_working_memory(
            type('', (), {
                "session_id": f"session_{request.conversation_id}",
                "context_data": {"last_query": request.message, "last_response": llm_response["content"]},
                "expires_in": 3600  # 1小时
            })()
        )

        processing_time = time.time() - start_time

        return EnhancedChatResponse(
            response=llm_response["content"],
            conversation_id=request.conversation_id,
            message_id=0,  # 实际应该从数据库获取
            model_used=request.model,
            tokens_used=llm_response.get("tokens_used"),
            memory_used=memory_used,
            rag_results=rag_results,
            agent_collaboration=agent_collaboration_result,
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/extract-memory")
async def extract_conversation_memory(
    conversation_id: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    从对话中提取重要信息到记忆系统
    """
    try:
        memory_service = get_memory_service(db)
        await memory_service.extract_and_store_conversation_memory(conversation_id, user_id)
        return {"message": "Memory extraction completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))