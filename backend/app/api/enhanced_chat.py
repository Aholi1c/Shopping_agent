"""
增强聊天API - 集成RAG和实时爬虫
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..services.shopping_crawler_service import ShoppingCrawlerService
from ..services.llm_service import LLMService

router = APIRouter()

class EnhancedChatRequest(BaseModel):
    """增强聊天请求"""
    message: str = Field(..., description="用户消息")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    enable_rag: bool = Field(True, description="启用RAG搜索")
    enable_crawler: bool = Field(True, description="启用实时爬虫")
    force_crawler: bool = Field(False, description="强制使用爬虫")

class ChatResponse(BaseModel):
    """聊天响应"""
    response: str
    sources: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]

class ChatSession(BaseModel):
    """聊天会话"""
    session_id: str
    user_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    last_updated: str

@router.post("/chat", response_model=Dict[str, Any])
async def enhanced_chat(
    request: EnhancedChatRequest,
    db: Session = Depends(get_db)
):
    """增强聊天 - 集成RAG和实时爬虫"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            # 生成整合响应
            result = await crawler_service.generate_integrated_response(request.message)

            # 提取响应内容
            response_content = result.get("response", "")

            # 构建源引用信息
            sources = []

            # 添加RAG源
            rag_data = result.get("rag_data", {})
            if rag_data.get("rag_results"):
                for i, rag_result in enumerate(rag_data["rag_results"][:3]):
                    sources.append({
                        "type": "rag",
                        "source": rag_result.get("metadata", {}).get("source", "unknown"),
                        "content": rag_result.get("content", "")[:100] + "...",
                        "score": rag_result.get("score", 0.0)
                    })

            # 添加实时数据源
            real_time_data = result.get("real_time_data", {})
            for platform, platform_data in real_time_data.items():
                if platform_data.get("product_info"):
                    sources.append({
                        "type": "crawler",
                        "source": platform,
                        "content": f"{platform}实时价格: {platform_data['product_info'].get('name', '')}",
                        "timestamp": platform_data.get("price", {}).get("timestamp", "")
                    })

            # 计算置信度
            confidence = result.get("intent", {}).get("confidence", 0.5)
            if sources:
                confidence = min(confidence + 0.2, 1.0)  # 有数据源时增加置信度

            return {
                "success": True,
                "data": {
                    "response": response_content,
                    "sources": sources,
                    "confidence": confidence,
                    "intent": result.get("intent", {}),
                    "query_analysis": {
                        "needs_real_time": result.get("intent", {}).get("needs_real_time", False),
                        "rag_results_count": len(rag_data.get("rag_results", [])),
                        "real_time_platforms": list(real_time_data.keys())
                    }
                },
                "metadata": {
                    "message": request.message,
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "enable_rag": request.enable_rag,
                    "enable_crawler": request.enable_crawler,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/product-advice", response_model=Dict[str, Any])
async def get_product_advice(
    request: EnhancedChatRequest,
    db: Session = Depends(get_db)
):
    """获取产品购买建议"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            # 分析查询意图
            intent = await crawler_service.analyze_query_intent(request.message)

            # 从RAG获取深度信息
            rag_data = await crawler_service.search_rag_knowledge(request.message)

            # 如果需要实时数据，进行爬虫
            real_time_data = {}
            if intent.get("needs_real_time", False):
                product_name = intent.get("product_name", request.message)
                platforms = intent.get("target_platforms", ["jd", "taobao"])
                info_types = intent.get("info_types", ["price"])

                real_time_data = await crawler_service.crawl_real_time_data(
                    product_name, platforms, info_types
                )

            # 生成购买建议
            advice_prompt = f"""
            作为专业的购物顾问，请基于以下信息为用户提供详细的购买建议：

            用户问题：{request.message}

            意图分析：{intent}

            历史数据和市场分析：
            - 商品信息：{rag_data.get('product_info', {})}
            - 价格历史：{rag_data.get('price_history', [])}
            - 专家建议：{rag_data.get('recommendations', [])}

            实时市场数据：
            {real_time_data}

            请提供：
            1. 产品优缺点分析
            2. 当前市场价格分析
            3. 购买时机建议（现在买 vs 等待）
            4. 预算规划建议
            5. 具体的购买渠道推荐
            6. 风险提醒和注意事项

            请用专业、客观的语气回答，重点突出实用建议。
            """

            llm_service = LLMService()
            advice_response = await llm_service.chat_completion([
                {"role": "user", "content": advice_prompt}
            ])

            return {
                "success": True,
                "data": {
                    "advice": advice_response.get("content", ""),
                    "intent": intent,
                    "historical_data": {
                        "product_info": rag_data.get("product_info", {}),
                        "price_history": rag_data.get("price_history", []),
                        "recommendations": rag_data.get("recommendations", [])
                    },
                    "real_time_data": real_time_data,
                    "confidence": intent.get("confidence", 0.5)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/price-comparison", response_model=Dict[str, Any])
async def price_comparison_chat(
    request: EnhancedChatRequest,
    db: Session = Depends(get_db)
):
    """价格比较聊天"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            # 分析查询意图
            intent = await crawler_service.analyze_query_intent(request.message)

            # 强制进行实时价格比较
            product_name = intent.get("product_name", request.message)
            platforms = ["jd", "taobao", "pdd"]  # 比较所有平台

            real_time_data = await crawler_service.crawl_real_time_data(
                product_name, platforms, ["price", "stock", "promotion"]
            )

            # 生成价格比较分析
            comparison_prompt = f"""
            请为用户提供详细的价格比较分析：

            用户需求：{request.message}

            各平台实时价格数据：
            {real_time_data}

            请提供：
            1. 各平台价格对比表
            2. 最优购买推荐
            3. 价格差异分析
            4. 促销活动对比
            5. 购买建议和注意事项

            请用清晰的格式展示，方便用户做出购买决策。
            """

            llm_service = LLMService()
            comparison_response = await llm_service.chat_completion([
                {"role": "user", "content": comparison_prompt}
            ])

            return {
                "success": True,
                "data": {
                    "comparison": comparison_response.get("content", ""),
                    "price_data": real_time_data,
                    "lowest_price": await self._find_lowest_price(real_time_data),
                    "available_platforms": await self._find_available_platforms(real_time_data)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timing-analysis", response_model=Dict[str, Any])
async def timing_analysis_chat(
    request: EnhancedChatRequest,
    db: Session = Depends(get_db)
):
    """购买时机分析"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            # 分析查询意图
            intent = await crawler_service.analyze_query_intent(request.message)

            # 获取历史数据
            rag_data = await crawler_service.search_rag_knowledge(request.message)

            # 获取实时数据
            product_name = intent.get("product_name", request.message)
            real_time_data = await crawler_service.crawl_real_time_data(
                product_name, ["jd", "taobao"], ["price"]
            )

            # 生成时机分析
            timing_prompt = f"""
            请为用户提供购买时机分析：

            用户问题：{request.message}
            用户预算：5000元（从问题中推断）

            历史数据：
            - 价格历史：{rag_data.get('price_history', [])}
            - 市场分析：{rag_data.get('recommendations', [])}

            当前价格：
            {real_time_data}

            请分析：
            1. 当前价格是否合理
            2. 历史价格趋势分析
            3. 未来价格预测（基于历史规律）
            4. 最佳购买时机建议
            5. 等待成本收益分析
            6. 风险评估

            请基于数据和逻辑给出客观分析。
            """

            llm_service = LLMService()
            timing_response = await llm_service.chat_completion([
                {"role": "user", "content": timing_prompt}
            ])

            return {
                "success": True,
                "data": {
                    "timing_analysis": timing_response.get("content", ""),
                    "historical_trends": rag_data.get("price_history", []),
                    "current_prices": real_time_data,
                    "recommendation": await self._generate_timing_recommendation(
                        rag_data, real_time_data, 5000
                    )
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _find_lowest_price(self, real_time_data: Dict) -> Dict[str, Any]:
    """找到最低价格"""
    lowest_price = float('inf')
    lowest_platform = ""

    for platform, data in real_time_data.items():
        if data.get("price") and data["price"].get("current_price", 0) < lowest_price:
            lowest_price = data["price"]["current_price"]
            lowest_platform = platform

    return {
        "platform": lowest_platform,
        "price": lowest_price
    }

async def _find_available_platforms(self, real_time_data: Dict) -> List[str]:
    """找到有货的平台"""
    available = []

    for platform, data in real_time_data.items():
        if data.get("stock", {}).get("in_stock", False):
            available.append(platform)

    return available

async def _generate_timing_recommendation(self, rag_data: Dict, real_time_data: Dict, budget: float) -> str:
    """生成时机推荐"""
    # 简单的逻辑：根据预算和当前价格给出建议
    current_prices = []
    for platform_data in real_time_data.values():
        if platform_data.get("price") and platform_data["price"].get("current_price"):
            current_prices.append(platform_data["price"]["current_price"])

    if not current_prices:
        return "无法获取当前价格信息"

    avg_price = sum(current_prices) / len(current_prices)

    if avg_price <= budget * 0.8:
        return "建议现在购买，价格较为优惠"
    elif avg_price <= budget:
        return "可以考虑购买，但建议等待可能的促销"
    else:
        return "建议等待降价或考虑其他选择"

@router.get("/health", response_model=Dict[str, Any])
async def enhanced_chat_health(db: Session = Depends(get_db)):
    """检查增强聊天服务健康状态"""
    try:
        # 测试基础功能
        async with ShoppingCrawlerService(db) as crawler_service:
            # 测试意图分析
            test_intent = await crawler_service.analyze_query_intent("iPhone 15 Pro多少钱")

            return {
                "success": True,
                "data": {
                    "service_status": "healthy",
                    "intent_analysis_working": test_intent.get("confidence", 0) > 0,
                    "supported_platforms": ["jd", "taobao", "pdd"],
                    "features": [
                        "RAG知识库搜索",
                        "实时价格爬取",
                        "购买建议生成",
                        "价格比较分析",
                        "购买时机分析"
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }