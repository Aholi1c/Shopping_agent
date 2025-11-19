# -*- coding: utf-8 -*-
import time
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from ..core.config import settings  # 新增: 允许后续根据配置扩展逻辑
from ..models.models import Conversation, Message
from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    MemoryCreate,
    MessageCreate,
    RAGSearchRequest,
    ProductSearchRequest,
    PlatformType,
    UserRole,
    MessageType,
)
from ..services.llm_service import get_llm_service
from ..services.memory_service import MemoryService
from ..services.rag_service import get_rag_service
from ..services.shopping_service import ShoppingService
from ..services.media_service import MediaService

logger = logging.getLogger("uvicorn.error")


class ConversationService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = get_llm_service()
        self.memory_service = MemoryService(db)
        self.rag_service = get_rag_service(db)

    # ------------------------------
    # CRUD helpers for conversations/messages
    # ------------------------------
    def create_conversation(self, data: ConversationCreate, user_id: Optional[int] = None) -> Conversation:
        conversation = Conversation(
            title=data.title or "New Conversation",
            user_id=data.user_id if data.user_id is not None else user_id,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_user_conversations(self, user_id: Optional[int] = None, limit: int = 50) -> List[Conversation]:
        q = self.db.query(Conversation).order_by(Conversation.updated_at.desc())
        if user_id:
            q = q.filter(Conversation.user_id == user_id)
        return q.limit(limit).all()

    def delete_conversation(self, conversation_id: int) -> bool:
        conv = self.get_conversation(conversation_id)
        if not conv:
            return False
        # delete messages first
        self.db.query(Message).filter(Message.conversation_id == conversation_id).delete()
        self.db.delete(conv)
        self.db.commit()
        return True

    def add_message(self, data: MessageCreate) -> Message:
        msg = Message(
            conversation_id=data.conversation_id,
            role=(data.role.value if hasattr(data.role, "value") else str(data.role)),
            content=data.content,
            message_type=(data.message_type.value if hasattr(data.message_type, "value") else (data.message_type or "text")),
            media_url=data.media_url,
        )
        self.db.add(msg)
        # touch conversation updated_at
        conv = self.db.query(Conversation).filter(Conversation.id == data.conversation_id).first()
        if conv:
            # SQLAlchemy onupdate should handle, but force update
            conv.updated_at = conv.updated_at
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    # ------------------------------
    # Core chat processing
    # ------------------------------
    async def process_chat_message(self, chat_request: ChatRequest, user_id: Optional[int] = None) -> ChatResponse:
        start = time.perf_counter()

        # 1) Ensure conversation
        if not chat_request.conversation_id:
            conv = self.create_conversation(ConversationCreate(title=chat_request.message[:50] + "..."), user_id=user_id)
            chat_request.conversation_id = conv.id
        else:
            conv = self.get_conversation(chat_request.conversation_id)
            if not conv:
                conv = self.create_conversation(ConversationCreate(title=chat_request.message[:50] + "..."), user_id=user_id)
                chat_request.conversation_id = conv.id

        # 2) Persist user message
        self.add_message(
            MessageCreate(
                conversation_id=chat_request.conversation_id,
                role=UserRole.USER,
                content=chat_request.message,
                message_type=chat_request.message_type,
                media_url=chat_request.media_url,
            )
        )

        # 3) Build history
        messages = self.get_conversation_messages(chat_request.conversation_id)
        message_history = [{"role": m.role, "content": m.content} for m in messages]

        # 4) Memory context
        session_id = f"session_{chat_request.conversation_id}"
        if chat_request.use_memory:
            try:
                memory_context = await self.memory_service.get_relevant_context(
                    chat_request.message, session_id, user_id, chat_request.conversation_id
                )
            except Exception as e:
                logger.exception("chat.memory error: %s", e)
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

        # 5) RAG context (shopping queries)
        rag_context: List[Any] = []
        rag_start = time.perf_counter()
        is_shopping_query = self._is_shopping_related_query(chat_request.message)
        if is_shopping_query:
            try:
                rag_search = RAGSearchRequest(
                    query=chat_request.message,
                    knowledge_base_ids=[],
                    limit=5,
                    threshold=0.6,
                )
                rag_results = await self.rag_service.search_knowledge_base(rag_search)
                if rag_results:
                    rag_context = rag_results
            except Exception as e:
                logger.exception("chat.rag error: %s", e)
        rag_ms = (time.perf_counter() - rag_start) * 1000
        logger.info("chat.rag duration_ms=%.1f used=%s conv_id=%s", rag_ms, bool(rag_context), chat_request.conversation_id)

        # 6) Real-time Taobao products (via Onebound)
        products_context: List[Dict[str, Any]] = []
        if is_shopping_query:
            try:
                shopping_llm = get_llm_service()
                shopping_service = ShoppingService(
                    self.db,
                    shopping_llm,
                    self.memory_service,
                    MediaService(),
                )
                product_search = ProductSearchRequest(
                    query=chat_request.message,
                    platforms=[PlatformType.TAOBAO],
                    category=None,
                    price_min=None,
                    price_max=None,
                    sort_by="relevance",
                    page=1,
                    page_size=10,
                )
                search_result = await shopping_service.search_products(product_search, user_id=user_id)
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
                logger.exception("chat.shopping_products error: %s", e)

        # 7) Build enhanced history
        enhanced_message_history = self._build_enhanced_message_history(
            message_history, memory_context, rag_context, products_context
        )

        # 8) Call LLM
        model = chat_request.model
        # Allow BigModel fallback naming
        if model.startswith("gpt-"):
            # let LLM service map when provider is bigmodel
            pass
        llm_start = time.perf_counter()
        result = await self.llm_service.chat_completion(
            messages=enhanced_message_history,
            model=model,
            max_tokens=chat_request.max_tokens,
            temperature=chat_request.temperature,
            stream=False,
        )
        llm_ms = (time.perf_counter() - llm_start) * 1000

        assistant_text = result.get("content", "")
        # 9) Persist assistant message
        assistant = self.add_message(
            MessageCreate(
                conversation_id=chat_request.conversation_id,
                role=UserRole.ASSISTANT,
                content=assistant_text,
                message_type=MessageType.TEXT,
            )
        )

        # 10) Store memory if enabled
        if chat_request.use_memory:
            try:
                await self._store_conversation_in_memory(
                    chat_request.message,
                    assistant_text,
                    chat_request.conversation_id,
                    user_id=user_id,
                    session_id=session_id,
                )
            except Exception as e:
                logger.exception("chat.memory.store error: %s", e)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("service.chat.process duration_ms=%.1f conv_id=%s rag=%s products=%s llm_ms=%.1f", duration_ms, chat_request.conversation_id, bool(rag_context), bool(products_context), llm_ms)

        return ChatResponse(
            response=assistant_text,
            conversation_id=chat_request.conversation_id,
            message_id=getattr(assistant, "id", 0),
            model_used=result.get("model_used", model),
            tokens_used=result.get("tokens_used"),
        )

    # ------------------------------
    # Helpers
    # ------------------------------
    def _is_shopping_related_query(self, text: str) -> bool:
        if not text:
            return False
        t = text.lower()
        keywords = [
            "买", "购买", "优惠", "折扣", "便宜", "价格", "对比", "推荐", "手机", "电脑", "耳机", "相机",
            "taobao", "淘宝", "jd", "京东", "拼多多", "pdd", "比价", "购物", "配置", "性价比",
            "选", "评测", "测评", "参数",
        ]
        return any(k in text for k in keywords) or any(k in t for k in ["taobao", "jd", "pdd"])

    def _build_enhanced_message_history(
        self,
        message_history: List[Dict[str, str]],
        memory_context: Dict[str, Any],
        rag_context: List[Any] = None,
        products_context: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        rag_context = rag_context or []
        products_context = products_context or []

        system_prompt = (
            "You are a helpful shopping assistant. Use user memory, knowledge base facts, and real-time product data to answer.\n"
            "Rules:\n"
            "- If recommending products, summarize key specs and provide reasoning.\n"
            "- Prefer products that align with user preferences if known.\n"
            "- If prices are in CNY unless otherwise noted; mention currency if known.\n"
            "- If insufficient data, say so clearly and suggest next steps.\n\n"
        )

        # Add KB context
        if rag_context:
            system_prompt += "Knowledge Base Information (Shopping & Pricing Data):\n"
            for i, result in enumerate(rag_context, 1):
                try:
                    content = result.content  # Pydantic model
                except Exception:
                    content = result.get("content", "") if isinstance(result, dict) else str(result)
                system_prompt += f"[KB {i}]: {content}\n\n"

        # Add Taobao products context
        if products_context:
            system_prompt += "Real-time Taobao Product Information:\n"
            for i, p in enumerate(products_context, 1):
                system_prompt += (
                    f"[Product {i}] 标题: {p.get('title')}, "
                    f"价格: {p.get('price')}, 原价: {p.get('original_price')}, "
                    f"折扣: {p.get('discount_rate')}, 评分: {p.get('rating')}, "
                    f"评论数: {p.get('review_count')}, 销量: {p.get('sales_count')}, "
                    f"链接: {p.get('product_url')}\n"
                )
            system_prompt += "\n"

        # Add memory context
        if memory_context.get("relevant_memories"):
            system_prompt += "Relevant user memories/preferences:\n"
            for i, mem in enumerate(memory_context.get("relevant_memories", []), 1):
                try:
                    content = mem.content
                except Exception:
                    content = mem.get("content", "") if isinstance(mem, dict) else str(mem)
                system_prompt += f"[MEM {i}]: {content}\n"
            system_prompt += "\n"

        # Add working memory/session
        if memory_context.get("working_memory"):
            system_prompt += f"Working context: {memory_context.get('working_memory')}\n\n"

        enhanced = [{"role": "system", "content": system_prompt}]
        enhanced.extend(message_history)
        return enhanced

    async def _store_conversation_in_memory(
        self,
        user_text: str,
        assistant_text: str,
        conversation_id: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
    ):
        try:
            # store a brief summary of the exchange
            summary = f"User: {user_text}\nAssistant: {assistant_text[:1000]}"
            mem = MemoryCreate(
                content=summary,
                metadata={"source": "chat", "conversation_id": conversation_id, "session_id": session_id},
            )
            await self.memory_service.create_memory(mem)
        except Exception as e:
            logger.debug("store memory failed: %s", e)
