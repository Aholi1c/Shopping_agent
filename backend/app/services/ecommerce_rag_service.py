"""
电商领域 RAG 集成服务

说明：
- 知识库已通过 scripts/import_phone_guide.py 预先构建，名称为「手机导购知识库」
- 这里不再负责构建知识库，只做：
  1. 从手机导购知识库中做 RAG 检索
  2. 通过 ShoppingService 只访问淘宝（Onebound）商品数据
  3. 调用 LLM 生成结合行业知识 + 实时商品数据的推荐说明
"""

from typing import Any, Dict, List, Optional
import json
import logging

from sqlalchemy.orm import Session

from ..models.schemas import RAGSearchRequest, ProductSearchRequest, PlatformType
from ..models.models import KnowledgeBase
from .rag_service import RAGService
from .shopping_service import ShoppingService
from .fallback_data_service import fallback_data_service
from .llm_service import get_llm_service, LLMService
from .memory_service import MemoryService
from .media_service import MediaService
from .onebound_api_client import onebound_api_client

logger = logging.getLogger(__name__)

PHONE_KB_NAME = "手机导购知识库"


class EcommerceRAGService:
    """
    电商 RAG 服务：
    - 使用手机导购知识库（RAG）提供选购知识
    - 使用淘宝商品数据（Onebound）提供实时候选商品
    - 使用 LLM 综合输出分析与推荐
    """

    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService(db)
        self.llm_service: Optional[LLMService] = get_llm_service()
        self.shopping_service = ShoppingService(
            db,
            self.llm_service or LLMService(),
            MemoryService(db),
            MediaService(),
        )

    async def _get_phone_kb_id(self) -> Optional[int]:
        """获取手机导购知识库的 ID（如果不存在则返回 None）。"""
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.name == PHONE_KB_NAME)
            .first()
        )
        return kb.id if kb else None

    async def _analyze_ecommerce_intent_for_onebound(
            self,
            query: str,
            budget: Optional[float] = None,
            preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        只给电商 RAG 推荐用的意图解析：
        - 不影响 ShoppingService 里的通用意图函数
        - 输出结构专门用于构造万邦搜索关键词
        """
        prefs = preferences or {}
        prompt = f"""                                                                                                                                                                                                                             
     你是手机/3C 导购意图分析助手，请**只输出 JSON，不要任何解释性文字**。                                                                                                                                                                             

     用户需求: {query}                                                                                                                                                                                                                                 
     预算: {budget if budget is not None else "未说明"}                                                                                                                                                                                                
     偏好: {json.dumps(prefs, ensure_ascii=False)}                                                                                                                                                                                                     

     请严格用下面这个 JSON 结构回答（字段可以为空，但结构不能变）：                                                                                                                                                                                    
     {{                                                                                                                                                                                                                                                
       "category": "手机/平板/笔记本 等，尽量具体",                                                                                                                                                                                                    
       "brands": ["小米", "Redmi"],                                                                                                                                                                                                                    
       "negative_brands": [],                                                                                                                                                                                                                          
       "core_features": ["游戏", "拍照", "续航"],                                                                                                                                                                                                      
       "price_range": {{"min": null, "max": null}},                                                                                                                                                                                                    
       "raw_keywords": "适合用来作为电商搜索 q 的关键词串，例如：5G 游戏 手机 拍照 续航"                                                                                                                                                               
     }}                                                                                                                                                                                                                                                
     """

        try:
            raw = await self.llm_service.generate_response(prompt)

            # 保险一点：只截取最外层 { ... } 部分
            if not raw:
                return {}
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                raw = raw[start: end + 1]

            data = json.loads(raw)
            if not isinstance(data, dict):
                return {}
            return data
        except Exception:
            # 解析失败就返回空，让后续用简单规则兜底
            return {}

    async def _search_taobao_for_recommendation(
            self,
            query: str,
            limit: int = 40,
    ) -> List[Dict[str, Any]]:
        """
        专门给电商 RAG 推荐用的淘宝搜索接口：
        - 只调万邦淘宝搜索
        - 不做意图解析，不走通用 ShoppingService
        - 出错或无结果时自动走 fallback_data_service
        """
        try:
            result = await onebound_api_client.search_products(
                query=query,
                platform="taobao",
                page=1,
                page_size=limit,
            )

            # 万邦封装后正常返回结构：{"products": [...], "total": ...}
            if isinstance(result, dict) and result.get("products"):
                return result["products"]

        except Exception:
            # 这里不用再往外抛，直接走兜底
            pass

            # 万邦查不到 / 出错时，走本地备用数据源
        fallback_products = fallback_data_service.get_fallback_products(
            query,
            count=limit,
        )
        return fallback_products or []

    async def recommend_with_taobao(self, request: Any) -> Dict[str, Any]:
        """
        核心工作流（电商 RAG + 淘宝实时数据）：
        1）从手机导购知识库中检索相关知识（RAG）
        2）用专用意图解析生成适合万邦的搜索关键词
        3）仅使用万邦淘宝搜索候选商品（查不到时走 fallback）
        4）使用 LLM 结合行业知识与商品数据生成推荐文案
        """
        # 1. RAG 检索行业知识
        kb_id = await self._get_phone_kb_id()
        rag_results: List[Any] = []
        if kb_id is not None:
            rag_request = RAGSearchRequest(
                query=request.query,
                knowledge_base_ids=[kb_id],
                limit=8,
                threshold=0.6,
            )
            rag_results = await self.rag_service.search_knowledge_base(rag_request)

        knowledge_snippets: List[Dict[str, Any]] = []
        for r in rag_results:
            content = getattr(r, "content", None)
            metadata = getattr(r, "metadata", {}) if hasattr(r, "metadata") else {}
            score = getattr(r, "score", None)
            knowledge_snippets.append(
                {
                    "content": content,
                    "metadata": metadata,
                    "score": score,
                }
            )

            # 2. 专用意图解析 + 关键词构造
        text = str(getattr(request, "query", "") or "")
        text_lower = text.lower()
        prefs: Dict[str, Any] = getattr(request, "preferences", None) or {}
        budget = getattr(request, "budget", None)

        intent = await self._analyze_ecommerce_intent_for_onebound(
            text,
            budget=budget,
            preferences=prefs,
        )

        # 品牌来源：preferences.preferred_brands + 用户描述 + 意图解析结果
        brands: List[str] = []

        # 2.1 从 preferences.preferred_brands 获取
        pref_brands = prefs.get("preferred_brands")
        if isinstance(pref_brands, list):
            for b in pref_brands:
                if not b:
                    continue
                brands.append(str(b).strip())

                # 2.2 从自然语言中粗略匹配常见品牌
        common_brand_patterns = [
            "小米", "红米", "Xiaomi", "Redmi",
            "OPPO", "vivo", "华为", "荣耀",
            "一加", "realme", "iQOO",
            "苹果", "Apple", "iPhone",
            "三星", "Samsung",
        ]
        for pat in common_brand_patterns:
            if pat.lower() in text_lower:
                brands.append(pat)

                # 2.3 从意图解析结果中补充品牌
        intent_brands = intent.get("brands") or []
        if isinstance(intent_brands, list):
            for b in intent_brands:
                if not b:
                    continue
                brands.append(str(b).strip())

                # 去重保持顺序
        seen = set()
        brand_list: List[str] = []
        for b in brands:
            if b not in seen:
                seen.add(b)
                brand_list.append(b)

                # 基础品类 & 使用场景/特征
        category = "手机" if "手机" in text else ""
        if not category:
            category = str(intent.get("category") or "").strip() or ""

        core_features: List[str] = intent.get("core_features") or []
        if not isinstance(core_features, list):
            core_features = []

        want_game = ("游戏" in text) or ("game" in text_lower) or ("游戏" in core_features)
        want_camera = ("拍照" in text) or ("camera" in text_lower) or ("自拍" in core_features)

        raw_keywords: str = str(intent.get("raw_keywords") or "").strip()

        # 3. 调用万邦获取候选商品（不通过 ShoppingService）
        all_products: List[Any] = []

        async def _search_with_query_base(q_base: str) -> List[Any]:
            # 用 q_base + raw_keywords 合成最终检索词
            parts: List[str] = []
            if q_base:
                parts.append(q_base)
            if raw_keywords:
                parts.append(raw_keywords)
            final_q = " ".join(dict.fromkeys(" ".join(parts).split())) or q_base

            logger.info(
                "[Onebound 推荐链路] q_base=%s | raw_keywords=%s | final_q=%s",
                q_base,
                raw_keywords,
                final_q,
            )

            return await self._search_taobao_for_recommendation(
                final_q,
                limit=getattr(request, "limit", 10) * 2,
            )

        if brand_list:
            # 按品牌拆分调用万邦：q_base = "品类 品牌 用途/特征"
            for brand in brand_list:
                parts: List[str] = []
                if category:
                    parts.append(category)
                parts.append(brand)
                if want_game:
                    parts.append("游戏")
                if want_camera:
                    parts.append("拍照")
                for feat in core_features:
                    parts.append(str(feat))

                q_base = " ".join(dict.fromkeys([p for p in parts if p]))
                all_products.extend(await _search_with_query_base(q_base))
        else:
            # 没识别出品牌时，用“品类 + 用途 + 核心特征”做召回
            parts: List[str] = []
            if category:
                parts.append(category)
            if want_game:
                parts.append("游戏")
            if want_camera:
                parts.append("拍照")
            for feat in core_features:
                parts.append(str(feat))

            q_base = " ".join(dict.fromkeys([p for p in parts if p])) or text
            all_products.extend(await _search_with_query_base(q_base))

            # 4. 本地按预算过滤，不把预算直接塞进搜索词
        raw_products: List[Any] = all_products
        if budget is not None:
            try:
                budget_val = float(budget)
                low = budget_val * 0.5
                high = budget_val * 1.2

                filtered: List[Any] = []
                for p in raw_products:
                    if hasattr(p, "price"):
                        price = p.price
                    elif isinstance(p, dict):
                        price = p.get("price")
                    else:
                        price = getattr(p, "price", None)

                    if price is None:
                        filtered.append(p)
                        continue

                    try:
                        pr = float(price)
                    except (TypeError, ValueError):
                        filtered.append(p)
                        continue

                    if low <= pr <= high:
                        filtered.append(p)

                raw_products = filtered
            except (TypeError, ValueError):
                # budget 无法解析时，忽略预算过滤
                pass

        if not raw_products:
            # 再保险一层：如果还是没有数据，再次 fallback
            fallback_products = fallback_data_service.get_fallback_products(
                request.query,
                count=getattr(request, "limit", 10) * 2,
            )
            raw_products = fallback_products or []

            # 5. 整理给 LLM 的商品列表
        products_for_llm: List[Dict[str, Any]] = []
        limit = getattr(request, "limit", 10)
        for p in raw_products[: limit]:
            if hasattr(p, "dict"):
                data = p.dict()
            elif isinstance(p, dict):
                data = p
            else:
                data = getattr(p, "__dict__", {}) or {}

            products_for_llm.append(
                {
                    "title": data.get("title"),
                    "price": data.get("price"),
                    "original_price": data.get("original_price"),
                    "discount_rate": data.get("discount_rate"),
                    "product_url": data.get("product_url"),
                    "image_url": data.get("image_url"),
                    "platform": str(data.get("platform")),
                    "rating": data.get("rating"),
                    "review_count": data.get("review_count"),
                    "sales_count": data.get("sales_count"),
                }
            )

            # 6. 构造给 LLM 的 Prompt 并生成推荐文案
        knowledge_text = ""
        if knowledge_snippets:
            parts = []
            for i, s in enumerate(knowledge_snippets, start=1):
                if not s.get("content"):
                    continue
                parts.append(f"[KB{i}] {s['content']}")
            knowledge_text = "\n\n".join(parts)

        prompt = f"""                                                                                                                                                                                                                             
     你是一个专业电商导购助手，目前只能访问淘宝商品数据。                                                                                                                                                                                              
     用户需求：{request.query}                                                                                                                                                                                                                         
     预算：{request.budget or "未特别说明"}                                                                                                                                                                                                            
     其他偏好：{json.dumps(prefs, ensure_ascii=False)}                                                                                                                                                                                                 

     下面是从「{PHONE_KB_NAME}」中检索到的内容（选购指南、经验、注意事项等）：                                                                                                                                                                         
     {knowledge_text or "（未检索到相关行业知识）"}                                                                                                                                                                                                    

     下面是从淘宝搜索到的候选商品列表（字段：title, price, original_price, discount_rate, rating, review_count, sales_count, product_url）：                                                                                                           
     {json.dumps(products_for_llm, ensure_ascii=False)}                                                                                                                                                                                                

     请你：                                                                                                                                                                                                                                            
     1. 先用行业知识概括一下选购该类商品时应注意的关键点；                                                                                                                                                                                             
     2. 在候选商品中选出 3 个最推荐的，并说明推荐理由（结合价格、评价、销量、折扣等）；                                                                                                                                                                
     3. 指出不太推荐的典型坑点或需要避免的情况；                                                                                                                                                                                                       
     4. 明确给出最终推荐列表（用编号列出：商品名 + 淘宝链接）。                                                                                                                                                                                        
     请用英文回答。                                                                                                                                                                                                                                    
     """

        if not self.llm_service:
            return {
                "recommendation_text": "LLM 服务未初始化，暂时无法生成自然语言推荐，请先检查 LLM 配置。",
                "products": products_for_llm,
                "knowledge_snippets": knowledge_snippets,
            }

        llm_response = await self.llm_service.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "你是一个严谨且懂行业知识的电商导购助手。",
                },
                {"role": "user", "content": prompt},
            ],
            model="gpt-4.1-mini",
        )

        return {
            "recommendation_text": llm_response.get("content"),
            "products": products_for_llm,
            "knowledge_snippets": knowledge_snippets,
        }


def get_ecommerce_rag_service(db: Session) -> EcommerceRAGService:
    """FastAPI 依赖注入入口，只负责拉通已有知识库与淘宝接口。"""
    return EcommerceRAGService(db)
