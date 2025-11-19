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
            keywords, auto_importance_score = self._extract_keywords_and_importance(memory_data.content)

            # 使用传入的importance_score，如果没有提供则使用自动计算的
            final_importance_score = memory_data.importance_score if memory_data.importance_score > 0 else auto_importance_score

            print(f"\n{'='*80}")
            print(f"📝 创建新记忆")
            print(f"{'='*80}")
            print(f"内容: {memory_data.content[:100]}{'...' if len(memory_data.content) > 100 else ''}")
            print(f"类型: {memory_data.memory_type}")
            print(f"传入重要性: {memory_data.importance_score}")
            print(f"自动计算重要性: {auto_importance_score:.2f}")
            print(f"最终重要性: {final_importance_score:.2f}")
            print(f"提取的关键词: {keywords}")
            print(f"标签: {memory_data.tags or keywords}")
            print(f"元数据: {memory_data.metadata}")
            print(f"{'='*80}\n")

            # 创建记忆记录
            memory = Memory(
                content=memory_data.content,
                memory_type=memory_data.memory_type,
                importance_score=final_importance_score,
                user_id=memory_data.user_id,
                meta_data=memory_data.metadata or {},
                tags=memory_data.tags or keywords
            )

            self.db.add(memory)
            self.db.commit()
            self.db.refresh(memory)

            print(f"✅ 记忆已保存 - ID: {memory.id}\n")

            # 添加到向量索引
            await asyncio.to_thread(
                vector_service.add_memory_embedding,
                memory.id, memory.content, self.db
            )
            
            # 手动构造响应，因为 ORM 字段是 meta_data 但 Pydantic 期望 metadata
            return MemoryResponse(
                id=memory.id,
                content=memory.content,
                memory_type=memory.memory_type,
                importance_score=memory.importance_score,
                access_count=memory.access_count,
                last_accessed=memory.last_accessed,
                created_at=memory.created_at,
                metadata=memory.meta_data or {},
                tags=memory.tags or []
            )

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create memory: {e}")

    def search_memories(self, search_request: MemorySearchRequest) -> List[MemoryResponse]:
        """
        混合搜索记忆（向量搜索 + 关键词匹配）
        """
        try:
            print(f"\n{'='*80}")
            print(f"🔍 混合搜索记忆 (Hybrid Search)")
            print(f"{'='*80}")
            print(f"查询: {search_request.query[:80]}{'...' if len(search_request.query) > 80 else ''}")
            print(f"类型过滤: {search_request.memory_type or '全部'}")
            print(f"用户ID: {search_request.user_id or '全部'}")
            print(f"限制数量: {search_request.limit}")
            print(f"相似度阈值: {search_request.threshold}")
            print(f"{'-'*80}")
            
            # 步骤1: 从查询中提取实体和关键词
            query_entities = self._extract_shopping_entities(search_request.query)
            
            # 打印提取的实体
            has_entities = any(len(v) > 0 for v in query_entities.values())
            if has_entities:
                print(f"\n📋 提取的查询实体:")
                for entity_type, entity_list in query_entities.items():
                    if entity_list:
                        print(f"   {entity_type}: {entity_list[:5]}")  # 只显示前5个
            else:
                print(f"\n📋 未提取到明确实体，使用纯向量搜索")
            
            # 步骤2: 使用向量搜索获取候选集
            similar_memories = vector_service.search_similar_memories(
                query=search_request.query,
                limit=search_request.limit * 3,  # 获取更多结果用于关键词重排序
                threshold=max(0.3, search_request.threshold - 0.2),  # 降低阈值以获取更多候选
                user_id=search_request.user_id,
                memory_type=search_request.memory_type,
                db=self.db
            )

            print(f"\n🔢 向量搜索返回: {len(similar_memories)} 条候选结果")
            
            # 步骤3: 对每条记忆计算关键词匹配分数，并重新排序
            from ..models.models import Memory
            scored_memories = []
            
            for mem_data in similar_memories:
                # 从数据库获取完整的记忆信息
                memory = self.db.query(Memory).filter(Memory.id == mem_data["id"]).first()
                if not memory:
                    continue
                
                # 计算关键词匹配分数
                keyword_score = 0.0
                if has_entities:
                    keyword_score = self._calculate_keyword_match_score(
                        mem_data["content"], 
                        query_entities
                    )
                
                # 获取向量相似度分数
                vector_score = mem_data.get("score", 0.0)
                
                # 计算混合分数
                # 如果有明确实体，关键词匹配权重更高；否则主要依赖向量搜索
                if has_entities:
                    # 有实体：60% 关键词 + 40% 向量
                    hybrid_score = 0.6 * keyword_score + 0.4 * vector_score
                    # 如果关键词完全不匹配，大幅降低分数
                    if keyword_score < 0.1:
                        hybrid_score *= 0.3
                else:
                    # 无实体：100% 向量
                    hybrid_score = vector_score
                
                # 考虑记忆的重要性
                importance_boost = mem_data["importance_score"] * 0.1
                final_score = hybrid_score + importance_boost
                
                scored_memories.append({
                    "memory": memory,
                    "mem_data": mem_data,
                    "vector_score": vector_score,
                    "keyword_score": keyword_score,
                    "hybrid_score": hybrid_score,
                    "final_score": final_score
                })
            
            # 步骤4: 按混合分数重新排序
            scored_memories.sort(key=lambda x: x["final_score"], reverse=True)
            
            # 步骤5: 转换为MemoryResponse
            results = []
            for i, scored_mem in enumerate(scored_memories[:search_request.limit], 1):
                memory = scored_mem["memory"]
                mem_data = scored_mem["mem_data"]
                
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
                
                # 打印每条搜索结果（显示混合分数）
                if i <= 5:  # 只打印前5条
                    print(f"\n  [{i}] ID:{mem_data['id']}")
                    print(f"      向量:{scored_mem['vector_score']:.3f} | 关键词:{scored_mem['keyword_score']:.3f} | 混合:{scored_mem['hybrid_score']:.3f} | 最终:{scored_mem['final_score']:.3f}")
                    print(f"      类型:{mem_data['memory_type']} | 重要性:{mem_data['importance_score']:.2f} | 标签:{memory.tags}")
                    print(f"      内容:{mem_data['content'][:80]}{'...' if len(mem_data['content']) > 80 else ''}")

            if len(scored_memories) > 5:
                print(f"\n  ... 还有 {len(scored_memories) - 5} 条结果未显示")
            
            print(f"\n✅ 混合搜索完成，最终返回 {len(results)} 条记忆")
            print(f"{'='*80}\n")

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

    def _extract_shopping_entities(self, text: str) -> Dict[str, List[str]]:
        """
        提取购物相关的实体词（通用版本，适用于所有商品类型）
        返回: {
            "brands": [...],
            "price_numbers": [...],
            "sizes": [...],
            "colors": [...],
            "materials": [...],
            "features": [...],
            "key_nouns": [...]
        }
        """
        entities = {
            "brands": [],
            "price_numbers": [],
            "sizes": [],
            "colors": [],
            "materials": [],
            "features": [],
            "key_nouns": []
        }
        
        text_lower = text.lower()
        
        # 1. 提取价格相关数字（通用）
        price_patterns = [
            r'(\d+\.?\d*)\s*元',
            r'(\d+\.?\d*)\s*块',
            r'(\d+\.?\d*)\s*rmb',
            r'(\d+\.?\d*)\s*¥',
            r'\$\s*(\d+\.?\d*)',
            r'预算.*?(\d+)',
            r'(\d{3,})',  # 3位以上数字，可能是价格
        ]
        for pattern in price_patterns:
            matches = re.findall(pattern, text_lower)
            entities["price_numbers"].extend(matches)
        
        # 2. 提取尺寸/尺码（通用）
        size_patterns = [
            r'(\d+\.?\d*)\s*码',
            r'(\d+\.?\d*)\s*号',
            r'([xs]{1,3}l{0,3})\s*码',  # XS, S, M, L, XL, XXL, XXXL
            r'尺寸.*?(\d+)',
            r'(\d+)\s*[cm毫米mm]',  # 尺寸单位
        ]
        for pattern in size_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            entities["sizes"].extend(matches)
        
        # 3. 提取颜色（通用，中英文）
        common_colors = [
            "黑色", "白色", "红色", "蓝色", "绿色", "黄色", "紫色", "粉色", "橙色", "灰色", "棕色", "褐色",
            "black", "white", "red", "blue", "green", "yellow", "purple", "pink", "orange", "gray", "grey", "brown",
            "银色", "金色", "米色", "卡其", "navy", "beige", "khaki"
        ]
        for color in common_colors:
            if color in text_lower:
                entities["colors"].append(color)
        
        # 4. 提取材质（通用）
        common_materials = [
            "皮革", "真皮", "pu", "帆布", "网面", "棉", "涤纶", "尼龙", "羊毛", "丝绸",
            "leather", "canvas", "cotton", "polyester", "nylon", "wool", "silk",
            "金属", "塑料", "木质", "玻璃", "陶瓷", "不锈钢",
            "metal", "plastic", "wood", "glass", "ceramic", "stainless"
        ]
        for material in common_materials:
            if material in text_lower:
                entities["materials"].append(material)
        
        # 5. 提取品牌词（通用，包含常见品牌）
        # 这里使用通用品牌识别策略：大写开头的连续词、知名品牌
        common_brands = [
            # 运动品牌
            "nike", "耐克", "adidas", "阿迪达斯", "阿迪", "puma", "彪马", "new balance", "nb", "新百伦",
            "asics", "亚瑟士", "converse", "匡威", "vans", "万斯", "reebok", "锐步", "under armour", "ua",
            # 时尚品牌
            "gucci", "古驰", "lv", "louis vuitton", "prada", "普拉达", "chanel", "香奈儿", "dior", "迪奥",
            "hermes", "爱马仕", "burberry", "巴宝莉", "coach", "蔻驰",
            # 电子品牌
            "apple", "苹果", "samsung", "三星", "huawei", "华为", "xiaomi", "小米", "oppo", "vivo",
            "sony", "索尼", "dell", "戴尔", "lenovo", "联想", "hp", "惠普", "asus", "华硕",
            # 家居品牌
            "ikea", "宜家", "muji", "无印良品", "zara home", "h&m home",
            # 美妆品牌
            "loreal", "欧莱雅", "estee lauder", "雅诗兰黛", "lancome", "兰蔻", "dior", "chanel",
            # 食品品牌
            "nestle", "雀巢", "coca cola", "可口可乐", "pepsi", "百事", "starbucks", "星巴克"
        ]
        for brand in common_brands:
            if brand in text_lower:
                entities["brands"].append(brand)
        
        # 6. 提取重要特征词（通用购物特征）
        feature_keywords = [
            "轻便", "舒适", "透气", "防水", "耐磨", "防滑", "减震", "支撑",
            "lightweight", "comfortable", "breathable", "waterproof", "durable", "non-slip",
            "智能", "高端", "入门", "专业", "性价比", "经典", "时尚", "简约", "复古",
            "smart", "premium", "entry-level", "professional", "classic", "fashionable", "minimalist", "vintage",
            "无线", "有线", "蓝牙", "wifi", "4g", "5g",
            "wireless", "wired", "bluetooth"
        ]
        for feature in feature_keywords:
            if feature in text_lower:
                entities["features"].append(feature)
        
        # 7. 提取关键名词（使用分词，过滤停用词）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        words = [w for w in words if len(w) > 1 and w.lower() not in self.stop_words]
        
        # 使用词频统计提取关键词
        word_freq = Counter([w.lower() for w in words])
        entities["key_nouns"] = [word for word, freq in word_freq.most_common(10) if freq > 0]
        
        return entities

    def _calculate_keyword_match_score(self, text: str, entities: Dict[str, List[str]]) -> float:
        """
        计算文本与实体的关键词匹配度
        返回 0.0-1.0 的分数
        """
        text_lower = text.lower()
        total_matches = 0
        total_entities = 0
        
        # 权重配置（不同类型的实体有不同的重要性）
        weights = {
            "brands": 3.0,          # 品牌最重要
            "price_numbers": 2.5,   # 价格数字很重要
            "sizes": 2.5,           # 尺寸很重要
            "colors": 2.0,          # 颜色重要
            "materials": 1.5,       # 材质较重要
            "features": 1.5,        # 特征较重要
            "key_nouns": 1.0        # 关键词基础权重
        }
        
        for entity_type, entity_list in entities.items():
            if not entity_list:
                continue
            
            weight = weights.get(entity_type, 1.0)
            
            for entity in entity_list:
                if not entity:
                    continue
                    
                entity_lower = str(entity).lower()
                total_entities += weight
                
                # 检查是否匹配
                if entity_lower in text_lower:
                    total_matches += weight
                # 模糊匹配（针对数字，允许一定范围）
                elif entity_type == "price_numbers":
                    try:
                        entity_num = float(entity)
                        # 在文本中查找相近的数字
                        numbers_in_text = re.findall(r'\d+\.?\d*', text_lower)
                        for num_str in numbers_in_text:
                            text_num = float(num_str)
                            # 允许10%的误差
                            if abs(text_num - entity_num) / max(entity_num, 1) < 0.1:
                                total_matches += weight * 0.8  # 模糊匹配得分略低
                                break
                    except:
                        pass
        
        if total_entities == 0:
            return 0.0  # 如果没有提取到任何实体，返回0（说明查询过于泛化）
        
        return min(1.0, total_matches / total_entities)

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
        """
        获取相关的上下文信息（使用混合检索 + 所有历史记忆）
        
        Args:
            query: 查询文本
            session_id: 会话ID
            user_id: 用户ID
            conversation_id: 对话ID（用于优先显示同一对话的记忆）
        """
        try:
            # 提取查询中的实体，用于判断搜索策略
            query_entities = self._extract_shopping_entities(query)
            has_specific_entities = any(len(v) > 0 for k, v in query_entities.items() if k in ["brands", "price_numbers", "sizes", "colors"])
            
            print(f"\n{'='*80}")
            print(f"🔍 开始检索相关记忆")
            print(f"{'='*80}")
            print(f"Query: {query[:60]}...")
            if has_specific_entities:
                print(f"✓ 检测到明确实体，将使用混合检索（向量+关键词）")
                for k, v in query_entities.items():
                    if v and k in ["brands", "price_numbers", "sizes", "colors"]:
                        print(f"   - {k}: {v[:3]}")
            else:
                print(f"✓ 未检测到明确实体，使用纯向量检索")
            print(f"{'-'*80}\n")
            
            # 首先搜索偏好记忆（使用混合检索 + 标签过滤）

            preference_memories = self.search_memories(MemorySearchRequest(
                query=query,  # 使用原始查询
                limit=15,
                threshold=0.45 if has_specific_entities else 0.5,
                user_id=user_id,
                memory_type="semantic"  # 偏好记忆通常是语义记忆
            ))
            
            # 过滤出真正的偏好记忆（有 'preference' 标签的）
            preference_memories = [
                mem for mem in preference_memories 
                if 'preference' in (mem.tags or []) or 'user_preference' in (mem.tags or [])
            ]
            
            # 然后搜索一般记忆（使用混合检索）
            general_memories = self.search_memories(MemorySearchRequest(
                query=query,
                limit=10,
                threshold=0.50 if has_specific_entities else 0.55,
                user_id=user_id
            ))
            
            # 合并结果，优先显示偏好记忆和同一对话的记忆
            all_memories = []
            memory_ids = set()
            
            # 1. 优先添加同一对话的记忆
            if conversation_id:
                from ..models.models import Memory
                
                # 查询同一对话的记忆（metadata中包含conversation_id）
                all_conversation_memories = self.db.query(Memory).filter(
                    (Memory.user_id == user_id) if user_id else True
                ).all()
                
                conversation_memories = []
                for mem in all_conversation_memories:
                    if mem.meta_data and isinstance(mem.meta_data, dict):
                        if mem.meta_data.get("conversation_id") == conversation_id:
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
            
            print(f"📚 混合检索结果：{len(preference_memories)} 条偏好记忆，{len(general_memories)} 条一般记忆")
            
            # 按重要性排序，限制数量
            all_memories.sort(key=lambda x: x["importance"], reverse=True)
            relevant_memories = all_memories[:15]  # 增加到15条，提供更多上下文

            # 打印调试信息
            print(f"\n{'='*60}")
            print(f"🧠 最终记忆检索结果")
            print(f"{'='*60}")
            print(f"📊 总共检索到 {len(relevant_memories)} 条相关记忆:")
            for i, mem in enumerate(relevant_memories[:5], 1):  # 显示前5条
                print(f"\n[{i}] {mem['source']} (重要性: {mem['importance']:.2f}, 类型: {mem['type']})")
                print(f"   内容: {mem['content'][:100]}...")
            if len(relevant_memories) > 5:
                print(f"\n   ... 还有 {len(relevant_memories) - 5} 条记忆未显示")
            print(f"{'='*60}\n")

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