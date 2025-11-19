from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
# Form已暂时移除，因为python-multipart安装有问题
# from fastapi import Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime
import time
import logging
import json

from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    ConversationCreate,
    FileUploadResponse,
    EnhancedChatRequest,
    EnhancedChatResponse,
    MessageCreate,
    RAGSearchRequest,
    ProductSearchRequest, PlatformType,
)
from ..services.conversation_service import ConversationService
from ..services.media_service import media_service, MediaService
from ..services.memory_service import MemoryService, get_memory_service
from ..services.rag_service import RAGService, get_rag_service
from ..services.llm_service import LLMService, get_llm_service
from ..services.shopping_service import ShoppingService
from ..core.database import get_db
from ..core.config import settings
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse


router = APIRouter()
# 使用 uvicorn 的 error logger，保证在控制台能看到 INFO 日志
logger = logging.getLogger("uvicorn.error")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    处理聊天消息
    """
    start = time.perf_counter()
    conversation_service = ConversationService(db)
    try:
        response = await conversation_service.process_chat_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "api.chat.chat duration_ms=%.1f conv_id=%s",
            duration_ms,
            getattr(request, "conversation_id", None),
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    SSE 实时聊天（仅返回 assistant 文本流），前端用 EventSource 或 fetch+ReadableStream 读取。
    路由不返回标准JSON，而是 text/event-stream。
    """
    start = time.perf_counter()
    conversation_service = ConversationService(db)
    llm_service = get_llm_service()

    if llm_service is None:
        raise HTTPException(status_code=500, detail="LLM服务未初始化，请检查API密钥配置")

    # 1) 准备对话（创建/获取）并写入用户消息
    created_new = False
    if not request.conversation_id:
        conversation = conversation_service.create_conversation(
            ConversationCreate(title=request.message[:50] + "..."),
            user_id=None,
        )
        request.conversation_id = conversation.id
        created_new = True
    else:
        conversation = conversation_service.get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    conversation_service.add_message(
        MessageCreate(
            conversation_id=request.conversation_id,
            role="user",
            content=request.message,
            message_type=request.message_type,
            media_url=request.media_url,
        )
    )

    # 2) 构建消息历史
    messages = conversation_service.get_conversation_messages(request.conversation_id)
    message_history = [{"role": msg.role, "content": msg.content} for msg in messages]

    # 3) 记忆与 RAG 上下文
    session_id = f"session_{request.conversation_id}"

    # 3.1 记忆
    if request.use_memory:
        try:
            memory_context = await conversation_service.memory_service.get_relevant_context(
                request.message, session_id, None, request.conversation_id
            )
        except Exception as e:
            logger.exception("chat.stream.memory error: %s", e)
            memory_context = {
                "relevant_memories": [],
                "working_memory": {},
                "session_context": {"session_id": session_id},
            }
    else:
        memory_context = {
            "relevant_memories": [],
            "working_memory": {},
            "session_context": {"session_id": session_id},
        }

    # 3.2 RAG（购物相关时启用）
    rag_context = []
    is_shopping_query = conversation_service._is_shopping_related_query(request.message)
    try:
        if is_shopping_query:
            rag_search = RAGSearchRequest(
                query=request.message, knowledge_base_ids=[], limit=5, threshold=0.6
            )
            rag_results = await conversation_service.rag_service.search_knowledge_base(rag_search)
            if rag_results:
                rag_context = rag_results
    except Exception as e:
        logger.exception("chat.stream.rag error: %s", e)

    # 3.3 淘宝商品上下文（实时商品数据）
    products_context = []
    if is_shopping_query:
        try:
            shopping_service = ShoppingService(
                db,
                llm_service,
                MemoryService(db),
                MediaService(),
            )
            product_search = ProductSearchRequest(
                query=request.message,
                platforms=[PlatformType.TAOBAO],
                category=None,
                price_min=None,
                price_max=None,
                sort_by="relevance",
                page=1,
                page_size=10,
            )
            search_result = await shopping_service.search_products(
                product_search, user_id=None
            )
            raw_products = search_result.get("products", [])
            for p in raw_products[:5]:
                if hasattr(p, "dict"):
                    data = p.dict()
                elif isinstance(p, dict):
                    data = p
                else:
                    data = getattr(p, "__dict__", {}) or {}
                products_context.append(
                    {
                        "title": data.get("title"),
                        "price": data.get("price"),
                        "original_price": data.get("original_price"),
                        "discount_rate": data.get("discount_rate"),
                        "rating": data.get("rating"),
                        "review_count": data.get("review_count"),
                        "sales_count": data.get("sales_count"),
                        "product_url": data.get("product_url"),
                    }
                )
        except Exception as e:
            logger.exception("chat.stream.shopping_products error: %s", e)

    # 4) 构造增强消息历史
    enhanced_message_history = conversation_service._build_enhanced_message_history(
        message_history, memory_context, rag_context, products_context
    )

    # 5) SSE 事件生成器
    async def event_generator():
        accumulated = []
        assistant_message_id = None
        try:
            # 先告知前端会话ID，便于首发时前端同步会话状态
            meta_payload = {"conversation_id": request.conversation_id}
            yield f"event: meta\ndata: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"

            # 模型名称兼容 BigModel
            model = request.model
            if model.startswith("gpt-") and settings.llm_provider == "bigmodel":
                model = settings.text_model or "glm-4-0520"

            async for delta in llm_service.stream_chat(
                messages=enhanced_message_history,
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            ):
                accumulated.append(delta)
                yield f"data: {delta}\n\n"
        except Exception as e:
            # 错误事件
            err = str(e).replace("\n", " ")
            yield f"event: error\ndata: {err}\n\n"
            logger.exception("chat.stream error: %s", e)
        finally:
            # 流结束时：持久化 assistant 消息，并发 done 事件
            try:
                full_text = "".join(accumulated)
                if full_text:
                    msg = conversation_service.add_message(
                        MessageCreate(
                            conversation_id=request.conversation_id,
                            role="assistant",
                            content=full_text,
                            message_type="text",
                        )
                    )
                    assistant_message_id = getattr(msg, "id", None)
                    if request.use_memory:
                        await conversation_service._store_conversation_in_memory(
                            request.message,
                            full_text,
                            request.conversation_id,
                            user_id=None,
                            session_id=session_id,
                        )
            except Exception as persist_err:
                logger.exception("chat.stream persist error: %s", persist_err)
            # 结束标记（JSON），附带会话与消息ID，便于前端刷新
            done_payload = {
                "status": "done",
                "conversation_id": request.conversation_id,
                "message_id": assistant_message_id,
            }
            yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Nginx 反向代理时禁用缓冲
    }

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


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
    获取对话中的所有消息
    """
    conversation_service = ConversationService(db)
    messages = conversation_service.get_conversation_messages(conversation_id)
    return messages


# 其余与上传、媒体等相关的路由维持不变，可按需要从原文件补充
