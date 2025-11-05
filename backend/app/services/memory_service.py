from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from ..models.models import Memory, WorkingMemory, User
from ..models.schemas import MemoryCreate, MemoryResponse, WorkingMemoryUpdate, MemorySearchRequest
from ..services.vector_service import vector_service
from ..services.llm_service import get_llm_service
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    # 下载NLTK数据（第一次运行时）
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except:
            pass
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠️  nltk未安装，某些文本处理功能将不可用。请运行: pip install nltk")
    sent_tokenize = None
    stopwords = None
from collections import Counter
import asyncio

if NLTK_AVAILABLE:
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except:
            pass

class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        if NLTK_AVAILABLE and stopwords:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                self.stop_words = set()
        else:
            self.stop_words = set()

    async def create_memory(self, memory_data: MemoryCreate) -> MemoryResponse:
        """创建新的记忆"""
        try:
            # 提取关键词和重要性分数
            keywords, importance_score = self._extract_keywords_and_importance(memory_data.content)

            # 创建记忆记录
            memory = Memory(
                content=memory_data.content,
                memory_type=memory_data.memory_type,
                importance_score=importance_score,
                user_id=memory_data.user_id,
                metadata=memory_data.metadata or {},
                tags=memory_data.tags or keywords
            )

            self.db.add(memory)
            self.db.commit()
            self.db.refresh(memory)

            # 添加到向量索引
            await asyncio.to_thread(
                vector_service.add_memory_embedding,
                memory.id, memory.content, self.db
            )

            return MemoryResponse.from_orm(memory)

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create memory: {e}")

    def search_memories(self, search_request: MemorySearchRequest) -> List[MemoryResponse]:
        """搜索记忆"""
        try:
            # 使用向量搜索
            similar_memories = vector_service.search_similar_memories(
                query=search_request.query,
                limit=search_request.limit * 2,  # 获取更多结果以便过滤
                threshold=search_request.threshold,
                user_id=search_request.user_id,
                memory_type=search_request.memory_type,
                db=self.db
            )

            # 转换为MemoryResponse
            results = []
            from ..models.models import Memory
            
            for mem_data in similar_memories:
                # 从数据库获取完整的记忆信息（包括tags和access_count）
                memory = self.db.query(Memory).filter(Memory.id == mem_data["id"]).first()
                if not memory:
                    continue
                
                memory_response = MemoryResponse(
                    id=mem_data["id"],
                    content=mem_data["content"],
                    memory_type=mem_data["memory_type"],
                    importance_score=mem_data["importance_score"],
                    access_count=getattr(memory, "access_count", 0),
                    last_accessed=getattr(memory, "last_accessed", memory.created_at),
                    created_at=datetime.fromisoformat(mem_data["created_at"]) if isinstance(mem_data["created_at"], str) else mem_data["created_at"],
                    metadata=mem_data.get("metadata", {}),
                    tags=memory.tags or []
                )
                results.append(memory_response)
                
                # 限制返回数量
                if len(results) >= search_request.limit:
                    break

            return results

        except Exception as e:
            print(f"Error searching memories: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_working_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取工作记忆"""
        try:
            working_memory = self.db.query(WorkingMemory).filter(
                WorkingMemory.session_id == session_id,
                WorkingMemory.is_active == True
            ).first()

            if working_memory:
                # 检查是否过期
                if working_memory.expires_at and working_memory.expires_at < datetime.utcnow():
                    working_memory.is_active = False
                    self.db.commit()
                    return None

                return {
                    "context_data": working_memory.context_data or {},
                    "short_term_memory": working_memory.short_term_memory or {},
                    "expires_at": working_memory.expires_at
                }

            return None

        except Exception as e:
            print(f"Error getting working memory: {e}")
            return None

    async def update_working_memory(self, update_data: WorkingMemoryUpdate) -> Dict[str, Any]:
        """更新工作记忆"""
        try:
            working_memory = self.db.query(WorkingMemory).filter(
                WorkingMemory.session_id == update_data.session_id
            ).first()

            if not working_memory:
                # 创建新的工作记忆
                expires_at = None
                if update_data.expires_in:
                    expires_at = datetime.utcnow() + timedelta(seconds=update_data.expires_in)

                working_memory = WorkingMemory(
                    session_id=update_data.session_id,
                    context_data=update_data.context_data or {},
                    short_term_memory=update_data.short_term_memory or {},
                    expires_at=expires_at
                )
                self.db.add(working_memory)
            else:
                # 更新现有工作记忆
                if update_data.context_data is not None:
                    current_context = working_memory.context_data or {}
                    current_context.update(update_data.context_data)
                    working_memory.context_data = current_context

                if update_data.short_term_memory is not None:
                    current_memory = working_memory.short_term_memory or {}
                    current_memory.update(update_data.short_term_memory)
                    working_memory.short_term_memory = current_memory

                if update_data.expires_in:
                    working_memory.expires_at = datetime.utcnow() + timedelta(seconds=update_data.expires_in)

                working_memory.is_active = True

            self.db.commit()
            self.db.refresh(working_memory)

            return {
                "context_data": working_memory.context_data or {},
                "short_term_memory": working_memory.short_term_memory or {},
                "expires_at": working_memory.expires_at
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update working memory: {e}")

    def clear_working_memory(self, session_id: str):
        """清除工作记忆"""
        try:
            working_memory = self.db.query(WorkingMemory).filter(
                WorkingMemory.session_id == session_id
            ).first()

            if working_memory:
                working_memory.is_active = False
                self.db.commit()

        except Exception as e:
            print(f"Error clearing working memory: {e}")

    async def consolidate_memories(self, user_id: Optional[int] = None):
        """整合记忆，将工作记忆转移到长期记忆"""
        try:
            # 获取所有活跃的工作记忆
            working_memories = self.db.query(WorkingMemory).filter(
                WorkingMemory.is_active == True
            ).all()

            for wm in working_memories:
                if user_id and wm.context_data and wm.context_data.get("user_id") != user_id:
                    continue

                # 将重要的工作记忆转为长期记忆
                if wm.short_term_memory:
                    for key, value in wm.short_term_memory.items():
                        if self._is_important_memory(key, value):
                            memory_content = f"Context: {wm.context_data}\nKey Information: {key} - {value}"

                            memory_data = MemoryCreate(
                                content=memory_content,
                                memory_type="episodic",
                                importance_score=0.7,
                                metadata={"source": "working_memory", "session_id": wm.session_id}
                            )

                            await self.create_memory(memory_data)

                # 清除工作记忆
                wm.is_active = False

            self.db.commit()

        except Exception as e:
            print(f"Error consolidating memories: {e}")

    async def extract_and_store_conversation_memory(self, conversation_id: int, user_id: Optional[int] = None):
        """从对话中提取并存储重要信息到记忆"""
        try:
            from ..models.models import Message

            # 获取对话的所有消息
            messages = self.db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).all()

            if not messages:
                return

            # 使用LLM提取重要信息
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}" for msg in messages
            ])

            extraction_prompt = f"""
            Analyze the following conversation and extract important information that should be remembered.
            Focus on:
            - User preferences and interests
            - Important facts mentioned
            - Decisions made
            - Action items
            - Personal information shared

            Conversation:
            {conversation_text}

            Return a JSON object with extracted memories in the format:
            {{
                "memories": [
                    {{
                        "content": "specific fact or information",
                        "importance": 0.8,
                        "tags": ["preference", "fact"],
                        "type": "semantic"
                    }}
                ]
            }}
            """

            llm_service = get_llm_service()
            response = await llm_service.chat_completion([
                {"role": "system", "content": "You are a memory extraction expert. Extract important information from conversations."},
                {"role": "user", "content": extraction_prompt}
            ])

            try:
                # 解析LLM响应
                import json
                result = json.loads(response["content"])

                for mem_data in result.get("memories", []):
                    memory_create = MemoryCreate(
                        content=mem_data["content"],
                        memory_type=mem_data.get("type", "semantic"),
                        importance_score=mem_data.get("importance", 0.5),
                        tags=mem_data.get("tags", []),
                        user_id=user_id,
                        metadata={"source": "conversation", "conversation_id": conversation_id}
                    )

                    await self.create_memory(memory_create)

            except json.JSONDecodeError:
                print("Failed to parse memory extraction response")

        except Exception as e:
            print(f"Error extracting conversation memory: {e}")

    def _extract_keywords_and_importance(self, text: str) -> Tuple[List[str], float]:
        """提取关键词和重要性分数"""
        try:
            # 简单的关键词提取
            words = re.findall(r'\b\w+\b', text.lower())
            words = [w for w in words if w not in self.stop_words and len(w) > 2]

            word_freq = Counter(words)
            keywords = [word for word, freq in word_freq.most_common(5)]

            # 计算重要性分数（基于长度、关键词密度等）
            importance_score = min(1.0, len(keywords) / 10.0)
            if any(keyword in text.lower() for keyword in ["important", "remember", "note", "key"]):
                importance_score += 0.2
            if "?" in text or "!" in text:
                importance_score += 0.1

            return keywords, min(1.0, importance_score)

        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return [], 0.5

    def _is_important_memory(self, key: str, value: Any) -> bool:
        """判断是否为重要记忆"""
        important_keywords = [
            "preference", "important", "remember", "key", "decision",
            "goal", "objective", "plan", "strategy", "personal"
        ]

        text = f"{key} {str(value)}".lower()
        return any(keyword in text for keyword in important_keywords)

    async def get_relevant_context(self, query: str, session_id: str, user_id: Optional[int] = None, conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """获取相关的上下文信息"""
        try:
            # 优先搜索偏好相关的记忆
            preference_query = query + " 偏好 喜欢 不喜欢 预算 品牌 颜色 尺码"
            
            # 首先搜索偏好记忆（更高重要性）
            preference_memories = self.search_memories(MemorySearchRequest(
                query=preference_query,
                limit=10,
                threshold=0.7,  # 提高阈值，只获取相关度高的记忆
                user_id=user_id,
                memory_type="semantic"  # 偏好记忆通常是语义记忆
            ))
            
            # 然后搜索一般记忆
            general_memories = self.search_memories(MemorySearchRequest(
                query=query,
                limit=5,
                threshold=0.75,  # 更高的阈值
                user_id=user_id
            ))
            
            # 合并结果，优先显示偏好记忆和同一对话的记忆
            all_memories = []
            memory_ids = set()
            
            # 1. 优先添加同一对话的记忆
            if conversation_id:
                from ..models.models import Memory
                from sqlalchemy import func
                
                # 查询同一对话的记忆（metadata中包含conversation_id）
                all_conversation_memories = self.db.query(Memory).filter(
                    (Memory.user_id == user_id) if user_id else True
                ).all()
                
                conversation_memories = []
                for mem in all_conversation_memories:
                    if mem.metadata and isinstance(mem.metadata, dict):
                        if mem.metadata.get("conversation_id") == conversation_id:
                            conversation_memories.append(mem)
                
                # 按创建时间排序
                conversation_memories.sort(key=lambda x: x.created_at, reverse=True)
                
                for mem in conversation_memories[:10]:
                    if mem.id not in memory_ids:
                        all_memories.append({
                            "content": mem.content,
                            "type": mem.memory_type,
                            "importance": mem.importance_score,
                            "source": "same_conversation"
                        })
                        memory_ids.add(mem.id)
            
            # 2. 添加偏好记忆（按重要性排序）
            for mem in preference_memories:
                if mem.id not in memory_ids:
                    # 检查是否有偏好标签
                    has_preference_tag = "preference" in (mem.tags or [])
                    if has_preference_tag or mem.memory_type == "semantic":
                        all_memories.append({
                            "content": mem.content,
                            "type": mem.memory_type,
                            "importance": mem.importance_score,
                            "source": "preference_memory"
                        })
                        memory_ids.add(mem.id)
            
            # 3. 添加一般记忆
            for mem in general_memories:
                if mem.id not in memory_ids:
                    all_memories.append({
                        "content": mem.content,
                        "type": mem.memory_type,
                        "importance": mem.importance_score,
                        "source": "general_memory"
                    })
                    memory_ids.add(mem.id)
            
            # 按重要性排序，限制数量
            all_memories.sort(key=lambda x: x["importance"], reverse=True)
            relevant_memories = all_memories[:10]  # 最多返回10条

            # 获取工作记忆
            working_memory = self.get_working_memory(session_id)

            # 构建上下文
            context = {
                "relevant_memories": relevant_memories,
                "working_memory": working_memory or {},
                "session_context": {
                    "session_id": session_id,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            return context

        except Exception as e:
            print(f"Error getting relevant context: {e}")
            import traceback
            traceback.print_exc()
            return {
                "relevant_memories": [],
                "working_memory": {},
                "session_context": {
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    async def update_memory_access(self, memory_id: int):
        """更新记忆访问记录"""
        try:
            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()
                self.db.commit()

        except Exception as e:
            print(f"Error updating memory access: {e}")

# 全局记忆服务实例（需要通过依赖注入使用）
def get_memory_service(db: Session) -> MemoryService:
    return MemoryService(db)