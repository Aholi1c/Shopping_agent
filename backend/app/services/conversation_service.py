import logging

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ..models.models import Conversation, Message, User
from ..models.schemas import ConversationCreate, MessageCreate, ChatRequest, ChatResponse, MemoryCreate, RAGSearchRequest
from ..services.llm_service import get_llm_service
from ..services.memory_service import MemoryService
from ..services.rag_service import get_rag_service
from ..services.shopping_service import ShoppingService
from ..services.media_service import MediaService

logger = logging.getLogger("uvicorn.error")

from ..services.rag_service import RAGService, get_rag_service
from ..core.config import settings
from datetime import datetime
import uuid
import json

class ConversationService:
    def __init__(self, db: Session):
        self.db = db
        self.memory_service = MemoryService(db)
        self.rag_service = get_rag_service(db)

    def create_conversation(self, conversation_data: ConversationCreate, user_id: Optional[int] = None) -> Conversation:
        """
        创建新对话
        """
        conversation = Conversation(
            title=conversation_data.title,
            user_id=user_id
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        获取对话详情
        """
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_user_conversations(self, user_id: Optional[int] = None, limit: int = 50) -> List[Conversation]:
        """
        获取用户的对话列表
        """
        query = self.db.query(Conversation)
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        return query.order_by(Conversation.updated_at.desc()).limit(limit).all()

    def add_message(self, message_data: MessageCreate) -> Message:
        """
        添加消息到对话
        """
        message = Message(
            conversation_id=message_data.conversation_id,
            role=message_data.role,
            content=message_data.content,
            message_type=message_data.message_type,
            media_url=message_data.media_url
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        # 更新对话的更新时间
        conversation = self.get_conversation(message_data.conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
            self.db.commit()

        return message

    def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        """
        获取对话的所有消息
        """
        return self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

    async def process_chat_message(self, chat_request: ChatRequest, user_id: Optional[int] = None) -> ChatResponse:
        """
        处理聊天消息并返回AI回复，集成记忆功能
        """
        # 创建或获取对话
        if not chat_request.conversation_id:
            conversation = self.create_conversation(
                ConversationCreate(title=chat_request.message[:50] + "..."),
                user_id
            )
            chat_request.conversation_id = conversation.id
        else:
            conversation = self.get_conversation(chat_request.conversation_id)
            if not conversation:
                raise ValueError("Conversation not found")

        # 添加用户消息
        user_message = self.add_message(MessageCreate(
            conversation_id=chat_request.conversation_id,
            role="user",
            content=chat_request.message,
            message_type=chat_request.message_type,
            media_url=chat_request.media_url
        ))

        # 构建消息历史
        messages = self.get_conversation_messages(chat_request.conversation_id)
        message_history = [{"role": msg.role, "content": msg.content} for msg in messages]

        # 获取记忆上下文（如果启用记忆功能）
        # 🔍 使用混合检索系统（向量搜索 + 关键词匹配）
        session_id = f"session_{chat_request.conversation_id}"
        memory_context = {}
        if chat_request.use_memory:
            # 获取相关记忆上下文（使用混合检索 + 所有历史记忆）
            # 系统会自动检测查询中的实体（品牌、价格、尺寸等），并智能调整搜索策略
            memory_context = await self.memory_service.get_relevant_context(
                chat_request.message,
                session_id,
                user_id,
                chat_request.conversation_id
            )
        else:
            # 即使不使用记忆，也要初始化一个空的工作记忆，用于保持对话上下文
            memory_context = {
                "relevant_memories": [],
                "working_memory": {},
                "session_context": {
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

        # 获取RAG上下文（自动检测购物相关查询）
        rag_context = []
        if self._is_shopping_related_query(chat_request.message):
            try:
                rag_search = RAGSearchRequest(
                    query=chat_request.message,
                    knowledge_base_ids=[1],  # 使用购物知识库
                    limit=5,
                    threshold=0.6
                )
                rag_results = await self.rag_service.search_knowledge_base(rag_search)
                if rag_results:
                    rag_context = rag_results
            except Exception as e:
                print(f"RAG search error: {e}")

        # 构建包含记忆和RAG的增强消息历史
        enhanced_message_history = self._build_enhanced_message_history(message_history, memory_context, rag_context)

        # 处理多模态消息
        llm_service = get_llm_service()
        if llm_service is None:
            raise Exception("LLM服务未初始化，请检查API密钥配置")
        
        if chat_request.message_type == "image" and chat_request.media_url:
            # 图像分析
            analysis_result = await llm_service.analyze_image(
                chat_request.media_url,
                "Analyze this image and respond to the user's question: " + chat_request.message
            )
            response_content = analysis_result["analysis"]
        elif chat_request.message_type == "audio" and chat_request.media_url:
            # 音频转录
            transcription_result = await llm_service.transcribe_audio(chat_request.media_url)
            response_content = f"Transcribed: {transcription_result['text']}"
        else:
            # 文本对话（使用增强的上下文）
            llm_service = get_llm_service()
            if llm_service is None:
                raise Exception("LLM服务未初始化，请检查API密钥配置")
            
            # 如果模型名称是OpenAI格式，但配置的是BigModel，使用默认模型
            model = chat_request.model
            if model.startswith("gpt-") and settings.llm_provider == "bigmodel":
                # 使用配置的默认模型
                model = settings.text_model or "glm-4-0520"
            
            llm_response = await llm_service.chat_completion(
                messages=enhanced_message_history,
                model=model,
                max_tokens=chat_request.max_tokens,
                temperature=chat_request.temperature
            )
            response_content = llm_response["content"]

        # 添加AI回复消息
        ai_message = self.add_message(MessageCreate(
            conversation_id=chat_request.conversation_id,
            role="assistant",
            content=response_content,
            message_type="text"
        ))

        # 存储到记忆系统（如果启用记忆功能）
        recommended_products = None
        if chat_request.use_memory:
            # ⭐ 获取推荐的商品列表
            recommended_products = await self._store_conversation_in_memory(
                chat_request.message, response_content, chat_request.conversation_id, user_id, session_id
            )

        # 更新工作记忆（如果启用记忆功能）
        if chat_request.use_memory:
            from ..models.schemas import WorkingMemoryUpdate

            # ⭐ 构建 context_data，包含当前讨论的商品
            context_data = {
                "last_query": chat_request.message,
                "last_response": response_content
            }

            # ⭐ 如果提取到了推荐的商品，将其添加到显式上下文中
            if recommended_products and len(recommended_products) > 0:
                context_data["current_products"] = recommended_products
                print(f"\n{'='*80}")
                print(f"💡 已将 {len(recommended_products)} 个推荐商品存入 WorkingMemory")
                print(f"{'='*80}")
                for i, product in enumerate(recommended_products, 1):
                    print(f"  [{i}] {product.get('name', 'N/A')} - {product.get('brand', 'N/A')}")
                print(f"{'='*80}\n")

            working_memory_update = WorkingMemoryUpdate(
                session_id=session_id,
                context_data=context_data,
                short_term_memory={"conversation_topic": conversation.title},
                expires_in=3600  # 1小时
            )
            await self.memory_service.update_working_memory(working_memory_update)

        return ChatResponse(
            response=response_content,
            conversation_id=chat_request.conversation_id,
            message_id=ai_message.id,
            model_used=chat_request.model,
            tokens_used=llm_response.get("tokens_used") if "tokens_used" in llm_response else None
        )

    def delete_conversation(self, conversation_id: int) -> bool:
        """
        删除对话
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            # 删除相关消息
            self.db.query(Message).filter(Message.conversation_id == conversation_id).delete()
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False

    def update_conversation_title(self, conversation_id: int, title: str) -> Optional[Conversation]:
        """
        更新对话标题
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(conversation)
        return conversation

    def _build_enhanced_message_history(
        self,
        message_history: List[Dict],
        memory_context: Dict,
        rag_context: List = None,
        products_context: List[Dict] | None = None,
    ) -> List[Dict]:
        """
        构建包含记忆、RAG 和实时商品上下文的增强消息历史
        """
        enhanced_history = []

        # 添加系统提示（允许上下文中包含多语言，但最终给用户的自然语言回复必须为英文）
        system_prompt = """You are an AI shopping assistant with memory and knowledge base capabilities. You have access to previous conversations, important information about the user, and a comprehensive shopping database.

Language & output rules:
1. Your final replies that the user sees must be in clear, natural English only.
2. You may freely read and reason over any language (including Chinese) that appears in the context below.
3. Product names, brand names, and other proper nouns may remain in their original language, but you should explain them in English.
4. If the user writes in Chinese or any other language, first understand their intent, then answer entirely in English (except for unavoidable proper nouns).

Shopping & personalization instructions:
5. Always remember and actively use user preferences mentioned in previous conversations.
6. If the user mentioned preferences before (brands, price range, features, colors, sizes, etc.), remember and apply them in your recommendations.
7. When the user asks about their preferences or asks you to remember something, acknowledge it and store it in your memory.
8. Use the memory context below to provide personalized and consistent responses.
9. Use the knowledge base information to provide accurate pricing and product information.
10. Refer to previous interactions when relevant.
11. Provide specific price ranges and comparisons when available.
12. Be conversational and natural while using all available context.

"""

        # ⭐ 添加当前讨论的商品上下文（显式状态，处理代词引用）
        if memory_context.get("working_memory", {}).get("context_data", {}).get("current_products"):
            current_products = memory_context["working_memory"]["context_data"]["current_products"]
            system_prompt += f"""
⭐ CURRENT CONTEXT - Products Being Discussed (当前正在讨论的商品):
{'='*60}
When the user says "that one", "it", "the previous one", "那个", "它", "之前的", they are referring to these products:

"""
            for i, product in enumerate(current_products, 1):
                system_prompt += f"""
[Product {i}]: {product.get('name', 'N/A')}
  - Brand: {product.get('brand', 'N/A')}
  - Key Features: {', '.join(product.get('key_features', []))}
  - Price: {product.get('price_info', 'N/A')}
"""
            system_prompt += f"{'='*60}\n\n"

        # 添加知识库上下文
        if rag_context:
            system_prompt += "Knowledge Base Information (Shopping & Pricing Data):\n"
            for i, result in enumerate(rag_context, 1):
                system_prompt += f"[KB {i}]: {result.content}\n\n"

        # 添加实时商品候选上下文（如有）
        if products_context:
            system_prompt += "Real-time E-commerce Candidates (From live search):\n"
            for i, product in enumerate(products_context, 1):
                system_prompt += (
                    f"[Live Product {i}]: {product.get('title')}\n"
                    f"  - Price: {product.get('price')} (Original: {product.get('original_price')})\n"
                    f"  - Rating: {product.get('rating')} | Reviews: {product.get('review_count')} | Sales: {product.get('sales_count')}\n"
                    f"  - URL: {product.get('product_url')}\n\n"
                )

        # 添加记忆上下文
        if memory_context.get("relevant_memories"):
            system_prompt += "Memory Context (Previous Conversations & User Preferences):\n"
            # 优先显示偏好记忆
            preference_memories = [m for m in memory_context["relevant_memories"] if m.get("source") == "preference_memory" or "preference" in (m.get("content", "").lower())]
            other_memories = [m for m in memory_context["relevant_memories"] if m not in preference_memories]
            
            # 先显示偏好记忆
            if preference_memories:
                system_prompt += "\n--- User Preferences (IMPORTANT - Use these in recommendations): ---\n"
                for i, memory in enumerate(preference_memories[:5], 1):
                    system_prompt += f"[Preference {i}]: {memory['content']} (Type: {memory['type']}, Importance: {memory['importance']})\n"
            
            # 再显示其他记忆
            if other_memories:
                system_prompt += "\n--- Other Context: ---\n"
                for i, memory in enumerate(other_memories[:5], 1):
                    system_prompt += f"[Memory {i}]: {memory['content']} (Type: {memory['type']}, Importance: {memory['importance']})\n"
            
            system_prompt += "\n"

        # 添加工作记忆
        if memory_context.get("working_memory", {}).get("context_data"):
            system_prompt += f"\nWorking Memory Context: {json.dumps(memory_context['working_memory']['context_data'], ensure_ascii=False)}\n"

        system_prompt += "\nNow, respond to the user's message considering all the context above. If they ask about prices or product comparisons, use the knowledge base information to provide specific details."

        # 打印发送给LLM的上下文
        print(f"\n{'='*80}")
        print(f"💬 构建发送给 LLM 的上下文")
        print(f"{'='*80}")
        if memory_context.get("relevant_memories"):
            print(f"包含 {len(memory_context['relevant_memories'])} 条记忆")
            print(f"  - 偏好记忆: {len(preference_memories)}")
            print(f"  - 其他记忆: {len(other_memories)}")
        if rag_context:
            print(f"包含 {len(rag_context)} 条知识库信息")
        if products_context:
            print(f"包含 {len(products_context)} 个实时商品候选（用于价格与商品推荐）")
        # ⭐ 打印当前讨论的商品信息
        if memory_context.get("working_memory", {}).get("context_data", {}).get("current_products"):
            current_products = memory_context["working_memory"]["context_data"]["current_products"]
            print(f"⭐ 包含 {len(current_products)} 个当前讨论的商品（用于代词引用）")
            for i, product in enumerate(current_products[:3], 1):
                print(f"  [{i}] {product.get('name', 'N/A')}")
        print(f"\n系统提示长度: {len(system_prompt)} 字符")
        print(f"{'='*80}\n")

        enhanced_history.append({"role": "system", "content": system_prompt})

        # 添加原始消息历史
        enhanced_history.extend(message_history)

        return enhanced_history

    async def _store_conversation_in_memory(self, user_message: str, assistant_response: str, conversation_id: int, user_id: Optional[int], session_id: str):
        """
        将对话内容存储到记忆系统，并自动提取用户偏好
        """
        try:
            # 检测是否包含用户偏好信息
            preference_keywords = [
                "喜欢", "偏好", "偏好", "想要", "希望", "需要", "要求",
                "不喜欢", "讨厌", "避免", "不想要",
                "预算", "价格", "价位", "多少钱", "花费",
                "品牌", "牌子", "型号", "款式", "颜色", "尺码",
                "总是", "经常", "通常", "一般"
            ]
            
            is_preference_related = any(keyword in user_message for keyword in preference_keywords)
            
            # 存储用户消息（如果包含偏好信息，提高重要性）
            user_memory = MemoryCreate(
                content=user_message,
                memory_type="semantic" if is_preference_related else "episodic",
                importance_score=0.9 if is_preference_related else 0.6,  # 提高偏好相关消息的重要性
                user_id=user_id,
                metadata={
                    "source": "user_input",
                    "conversation_id": conversation_id,
                    "is_preference": is_preference_related
                },
                tags=["preference", "user_preference"] if is_preference_related else []
            )
            await self.memory_service.create_memory(user_memory)

            # 智能提取助手推荐的商品（仅当真正推荐了商品时才保存）
            # ⭐ 获取推荐的商品列表，用于更新 WorkingMemory
            recommended_products = await self._extract_and_store_recommendations(
                assistant_response,
                conversation_id,
                user_id
            )

            # 如果包含偏好信息，创建一个专门的偏好记忆
            if is_preference_related:
                try:
                    print(f"\n{'='*80}")
                    print(f"🎯 检测到偏好相关信息，开始提取...")
                    print(f"{'='*80}")
                    print(f"用户消息: {user_message}")
                    print(f"{'-'*80}")

                    # 使用LLM提取偏好信息
                    llm_service = get_llm_service()
                    if llm_service:
                        preference_prompt = f"""
从以下用户消息中提取用户的购物偏好信息，包括：
- 品牌偏好（喜欢的品牌或不喜欢哪些品牌）
- 价格偏好（预算范围、价位要求）
- 商品特性偏好（颜色、尺寸、款式等）
- 其他特殊要求

用户消息：{user_message}

请以JSON格式返回提取的偏好信息：
{{
    "preferences": {{
        "brands": ["喜欢的品牌1", "不喜欢的品牌2"],
        "price_range": {{"min": 0, "max": 1000}},
        "features": ["特性1", "特性2"],
        "other": "其他偏好描述"
    }}
}}

只返回JSON，不要其他文字。
"""

                        llm_response = await llm_service.chat_completion([
                            {"role": "system", "content": "你是偏好提取专家，从对话中提取用户的购物偏好。"},
                            {"role": "user", "content": preference_prompt}
                        ], max_tokens=500, temperature=0.3)

                        print(f"LLM 返回: {llm_response.get('content', '')[:200]}...")

                        # 尝试解析偏好信息
                        import json
                        import re
                        response_text = llm_response.get("content", "")
                        # 提取JSON部分
                        json_match = re.search(r'\{[\s\S]*\}', response_text)
                        if json_match:
                            preference_data = json.loads(json_match.group())
                            preference_summary = json.dumps(preference_data, ensure_ascii=False)

                            print(f"\n✅ 成功提取偏好信息:")
                            print(f"   品牌: {preference_data.get('preferences', {}).get('brands', [])}")
                            print(f"   价格区间: {preference_data.get('preferences', {}).get('price_range', {})}")
                            print(f"   特性: {preference_data.get('preferences', {}).get('features', [])}")
                            print(f"   其他: {preference_data.get('preferences', {}).get('other', 'N/A')}")
                            print(f"{'='*80}\n")

                            # 创建偏好记忆
                            preference_memory = MemoryCreate(
                                content=f"用户偏好：{preference_summary}",
                                memory_type="semantic",
                                importance_score=0.9,
                                user_id=user_id,
                                metadata={
                                    "source": "preference_extraction",
                                    "conversation_id": conversation_id,
                                    "preference_data": preference_data
                                },
                                tags=["preference", "user_preference", "shopping_preference"]
                            )
                            await self.memory_service.create_memory(preference_memory)
                        else:
                            print(f"⚠️  无法从LLM响应中提取JSON")
                            print(f"{'='*80}\n")
                except Exception as e:
                    print(f"\n❌ 偏好提取错误: {e}")
                    print(f"{'='*80}\n")
                    # 即使提取失败，也继续存储对话记忆

            # ⭐ 返回推荐的商品列表（用于更新 WorkingMemory）
            return recommended_products

        except Exception as e:
            print(f"Error storing conversation in memory: {e}")
            return None

    async def _extract_and_store_recommendations(self, assistant_response: str, conversation_id: int, user_id: Optional[int]):
        """
        从AI回复中智能提取推荐的商品信息（仅保存核心信息，避免冗余）
        只在真正推荐了商品时才保存记忆
        """
        try:
            # 检测是否包含推荐相关的关键词
            recommendation_keywords = [
                "推荐", "建议", "可以看看", "可以考虑", "为您找到", "为您推荐",
                "这款", "那款", "以下", "下面是", "介绍", "这个产品"
            ]

            has_recommendation = any(keyword in assistant_response for keyword in recommendation_keywords)

            # 如果没有推荐内容，就不保存
            if not has_recommendation:
                print(f"\n💭 AI回复不包含商品推荐，跳过记忆存储")
                return

            print(f"\n{'='*80}")
            print(f"🛍️  检测到AI推荐，开始提取商品信息...")
            print(f"{'='*80}")
            print(f"AI回复（前150字）: {assistant_response[:150]}...")
            print(f"{'-'*80}")

            # 使用LLM提取推荐的商品信息
            llm_service = get_llm_service()
            if not llm_service:
                print(f"⚠️  LLM服务不可用，跳过推荐提取")
                return

            extraction_prompt = f"""
从以下AI助手的回复中提取推荐的商品信息。只提取核心信息，避免冗余描述。

AI回复：{assistant_response}

请以JSON格式返回提取的信息：
{{
    "has_recommendation": true/false,  // 是否真的推荐了具体商品
    "products": [
        {{
            "name": "商品名称（简短，例如：阿迪达斯UltraBoost白色）",
            "brand": "品牌",
            "key_features": ["关键特点1", "关键特点2"],  // 最多3个
            "price_info": "价格信息（如有）"
        }}
    ],
    "recommendation_reason": "推荐理由的简要总结（一句话）"
}}

要求：
1. 如果没有推荐具体商品（只是一般性对话），设置has_recommendation为false
2. 商品名称要简洁明了，不要长句子
3. 只提取关键特点，不要冗长描述
4. 只返回JSON，不要其他文字

只返回JSON，不要任何额外文字。
"""

            llm_response = await llm_service.chat_completion([
                {"role": "system", "content": "你是商品推荐信息提取专家。只提取核心信息，保持简洁。"},
                {"role": "user", "content": extraction_prompt}
            ], max_tokens=500, temperature=0.3)

            response_text = llm_response.get("content", "")
            print(f"LLM提取结果: {response_text[:200]}...")

            # 提取JSON部分
            import json
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)

            if json_match:
                recommendation_data = json.loads(json_match.group())

                # 检查是否真的有推荐
                if not recommendation_data.get("has_recommendation", False):
                    print(f"✓ 确认无具体商品推荐，跳过保存")
                    print(f"{'='*80}\n")
                    return

                products = recommendation_data.get("products", [])
                if not products:
                    print(f"✓ 未提取到商品信息，跳过保存")
                    print(f"{'='*80}\n")
                    return

                # 构建简洁的记忆内容
                product_names = [p.get("name", "") for p in products]
                recommendation_summary = f"已推荐商品: {', '.join(product_names)}"

                if recommendation_data.get("recommendation_reason"):
                    recommendation_summary += f" | 原因: {recommendation_data['recommendation_reason']}"

                print(f"\n✅ 成功提取推荐信息:")
                print(f"   推荐商品: {product_names}")
                print(f"   原因: {recommendation_data.get('recommendation_reason', 'N/A')}")
                for i, product in enumerate(products[:3], 1):  # 最多显示3个
                    print(f"   [{i}] {product.get('name')} - {product.get('brand', 'N/A')}")
                    if product.get('key_features'):
                        print(f"       特点: {', '.join(product['key_features'][:3])}")
                print(f"{'='*80}\n")

                # 创建简洁的推荐记忆（重要性较低，避免干扰用户偏好）
                recommendation_memory = MemoryCreate(
                    content=recommendation_summary,
                    memory_type="episodic",
                    importance_score=0.4,  # 较低的重要性，避免干扰用户偏好搜索
                    user_id=user_id,
                    metadata={
                        "source": "ai_recommendation",
                        "conversation_id": conversation_id,
                        "products": products,
                        "recommendation_data": recommendation_data
                    },
                    tags=["recommendation", "ai_suggestion"] + [p.get("brand", "") for p in products if p.get("brand")]
                )
                await self.memory_service.create_memory(recommendation_memory)

                print(f"✅ 推荐记忆已保存 (简洁模式)\n")

                # ⭐ 将推荐的商品存储到 WorkingMemory 中（显式上下文状态）
                return products  # 返回商品列表，用于更新 WorkingMemory
            else:
                print(f"⚠️  无法从LLM响应中提取JSON，跳过保存")
                print(f"{'='*80}\n")

        except Exception as e:
            print(f"\n❌ 推荐提取错误: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
            # 提取失败不影响主流程

        return None  # 如果没有提取到商品，返回 None

    def _is_shopping_related_query(self, query: str) -> bool:
        """
        检测是否为购物相关查询
        """
        shopping_keywords = [
            "价格", "多少钱", "多少钱", "价钱", "费用", "花费", "预算",
            "对比", "比较", "哪个好", "推荐", "评价", "性价比",
            "购买", "买", "购买", "下单", "优惠", "促销", "折扣",
            "运动鞋", "跑鞋", "篮球鞋", "休闲鞋", "靴子", "凉鞋",
            "耐克", "nike", "阿迪达斯", "adidas", "匡威", "converse",
            "万斯", "vans", "新百伦", "new balance", "亚瑟士", "asics",
            "牌子", "品牌", "型号", "款式", "颜色", "尺码", "尺寸"
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in shopping_keywords)
