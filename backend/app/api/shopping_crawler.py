"""
实时购物爬虫API接口
结合RAG知识库和实时爬虫的智能购物助手
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..services.shopping_crawler_service import ShoppingCrawlerService

router = APIRouter()

class ShoppingQueryRequest(BaseModel):
    """购物查询请求"""
    query: str = Field(..., description="用户查询内容")
    force_real_time: bool = Field(False, description="强制使用实时数据")
    platforms: Optional[List[str]] = Field(None, description="指定查询平台")

class CrawlerTestRequest(BaseModel):
    """爬虫测试请求"""
    platform: str = Field(..., description="测试平台：jd/taobao/pdd")
    product_name: str = Field(..., description="测试商品名称")

class IntentAnalysisResponse(BaseModel):
    """意图分析响应"""
    needs_real_time: bool
    product_name: str
    info_types: List[str]
    target_platforms: List[str]
    confidence: float

class PlatformPriceResponse(BaseModel):
    """平台价格响应"""
    platform: str
    current_price: float
    original_price: float
    discount: str
    in_stock: bool
    promotion_info: Dict[str, Any]
    product_url: str
    timestamp: str

@router.post("/query", response_model=Dict[str, Any])
async def shopping_crawler_query(
    request: ShoppingQueryRequest,
    db: Session = Depends(get_db)
):
    """智能购物查询 - 结合RAG和实时爬虫"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            result = await crawler_service.generate_integrated_response(request.query)

            return {
                "success": True,
                "data": result,
                "metadata": {
                    "query": request.query,
                    "force_real_time": request.force_real_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-intent", response_model=Dict[str, Any])
async def analyze_query_intent(
    request: ShoppingQueryRequest,
    db: Session = Depends(get_db)
):
    """分析查询意图"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            intent = await crawler_service.analyze_query_intent(request.query)

            return {
                "success": True,
                "data": intent,
                "metadata": {
                    "query": request.query,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl-real-time", response_model=Dict[str, Any])
async def crawl_real_time_data(
    request: ShoppingQueryRequest,
    db: Session = Depends(get_db)
):
    """实时爬取数据"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            # 分析意图获取参数
            intent = await crawler_service.analyze_query_intent(request.query)

            if not intent.get("needs_real_time", False):
                return {
                    "success": True,
                    "data": {
                        "message": "此查询不需要实时数据",
                        "intent": intent
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }

            # 爬取实时数据
            real_time_data = await crawler_service.crawl_real_time_data(
                product_name=intent.get("product_name", request.query),
                platforms=request.platforms or intent.get("target_platforms", ["jd", "taobao"]),
                info_types=intent.get("info_types", ["price"])
            )

            return {
                "success": True,
                "data": {
                    "intent": intent,
                    "real_time_data": real_time_data
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-crawler", response_model=Dict[str, Any])
async def test_crawler(
    request: CrawlerTestRequest,
    db: Session = Depends(get_db)
):
    """测试爬虫功能"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            # 爬取指定平台数据
            results = await crawler_service.crawl_real_time_data(
                product_name=request.product_name,
                platforms=[request.platform],
                info_types=["price", "stock", "promotion"]
            )

            return {
                "success": True,
                "data": {
                    "platform": request.platform,
                    "product_name": request.product_name,
                    "results": results,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rag-search", response_model=Dict[str, Any])
async def rag_search(
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(10, description="返回结果数量"),
    db: Session = Depends(get_db)
):
    """RAG知识库搜索"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            rag_data = await crawler_service.search_rag_knowledge(query)

            return {
                "success": True,
                "data": rag_data,
                "metadata": {
                    "query": query,
                    "limit": limit,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare-prices", response_model=Dict[str, Any])
async def compare_prices(
    product_name: str = Query(..., description="商品名称"),
    platforms: Optional[str] = Query(None, description="平台列表，逗号分隔"),
    db: Session = Depends(get_db)
):
    """多平台价格比较"""
    try:
        target_platforms = platforms.split(",") if platforms else ["jd", "taobao", "pdd"]

        async with ShoppingCrawlerService(db) as crawler_service:
            real_time_data = await crawler_service.crawl_real_time_data(
                product_name=product_name,
                platforms=target_platforms,
                info_types=["price", "stock", "promotion"]
            )

            # 分析和比较价格
            price_comparison = await crawler_service._generate_response_with_ai(
                f"请帮我比较{product_name}在各个平台的价格",
                {
                    "needs_real_time": True,
                    "product_name": product_name,
                    "info_types": ["price"],
                    "target_platforms": target_platforms,
                    "confidence": 0.9
                },
                {"rag_results": []},
                real_time_data
            )

            return {
                "success": True,
                "data": {
                    "product_name": product_name,
                    "platforms": target_platforms,
                    "real_time_data": real_time_data,
                    "price_analysis": price_comparison,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/product-timeline", response_model=Dict[str, Any])
async def get_product_timeline(
    product_name: str = Query(..., description="商品名称"),
    db: Session = Depends(get_db)
):
    """获取产品时间线信息"""
    try:
        async with ShoppingCrawlerService(db) as crawler_service:
            # 从RAG获取历史数据
            rag_data = await crawler_service.search_rag_knowledge(product_name)

            # 获取实时价格
            intent = {
                "needs_real_time": True,
                "product_name": product_name,
                "info_types": ["price"],
                "target_platforms": ["jd", "taobao"],
                "confidence": 0.9
            }

            real_time_data = await crawler_service.crawl_real_time_data(
                product_name=product_name,
                platforms=["jd", "taobao"],
                info_types=["price"]
            )

            # 生成时间线分析
            timeline_analysis = await crawler_service._generate_response_with_ai(
                f"请分析{product_name}的价格历史和购买时机",
                intent,
                rag_data,
                real_time_data
            )

            return {
                "success": True,
                "data": {
                    "product_name": product_name,
                    "historical_data": rag_data.get("price_history", []),
                    "current_prices": real_time_data,
                    "timeline_analysis": timeline_analysis,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def check_crawler_health(db: Session = Depends(get_db)):
    """检查爬虫服务健康状态"""
    try:
        # 测试各平台连接
        platforms_status = {}
        test_platforms = ["jd", "taobao", "pdd"]

        async with ShoppingCrawlerService(db) as crawler_service:
            for platform in test_platforms:
                try:
                    # 简单测试连接
                    site_config = crawler_service.shopping_sites.get(platform)
                    if site_config:
                        platforms_status[platform] = {
                            "name": site_config["name"],
                            "status": "configured",
                            "base_url": site_config["base_url"]
                        }
                    else:
                        platforms_status[platform] = {
                            "status": "not_configured"
                        }
                except Exception as e:
                    platforms_status[platform] = {
                        "status": "error",
                        "error": str(e)
                    }

        return {
            "success": True,
            "data": {
                "service_status": "healthy",
                "platforms": platforms_status,
                "supported_platforms": len(test_platforms),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/statistics", response_model=Dict[str, Any])
async def get_crawler_statistics(db: Session = Depends(get_db)):
    """获取爬虫使用统计"""
    try:
        # 这里可以添加数据库查询来获取使用统计
        # 目前返回示例数据
        return {
            "success": True,
            "data": {
                "total_queries": 0,
                "real_time_queries": 0,
                "rag_queries": 0,
                "platform_usage": {
                    "jd": 0,
                    "taobao": 0,
                    "pdd": 0
                },
                "success_rate": 0.0,
                "average_response_time": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))