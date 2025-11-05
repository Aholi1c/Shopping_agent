"""
社交商务API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..services.social_commerce_service import SocialCommerceService, get_social_commerce_service

router = APIRouter()

class SocialShareRequest(BaseModel):
    """社交分享请求"""
    user_id: str = Field(..., description="用户ID")
    product_id: str = Field(..., description="商品ID")
    platform: str = Field(..., description="社交平台")
    content: str = Field(..., description="分享内容")

class CampaignConfig(BaseModel):
    """活动配置"""
    platforms: List[str] = Field(..., description="目标平台")
    campaign_type: str = Field(..., description="活动类型")
    target_audience: str = Field(..., description="目标受众")
    budget: Optional[float] = Field(None, description="预算")
    duration: int = Field(7, ge=1, le=30, description="活动持续时间(天)")

class RecommendationRequest(BaseModel):
    """推荐请求"""
    user_id: str = Field(..., description="用户ID")
    product_id: str = Field(..., description="商品ID")
    include_social_content: bool = Field(True, description="是否包含社交内容")
    recommendation_type: str = Field("personalized", description="推荐类型")

class CampaignCreateRequest(BaseModel):
    """创建活动请求"""
    product_id: str = Field(..., description="商品ID")
    config: CampaignConfig = Field(..., description="活动配置")

@router.get("/trending", response_model=Dict[str, Any])
async def get_trending_social_products(
    category: Optional[str] = Query(None, description="商品类别"),
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取社交平台热门商品"""
    try:
        service = get_social_commerce_service(db)
        trending_products = await service.get_trending_social_products(category, limit)

        return {
            "success": True,
            "data": {
                "trending_products": trending_products,
                "total_results": len(trending_products),
                "filters": {
                    "category": category,
                    "limit": limit,
                    "days": days
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations/generate", response_model=Dict[str, Any])
async def generate_social_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """生成社交推荐内容"""
    try:
        service = get_social_commerce_service(db)
        recommendation = await service.generate_social_recommendations(
            request.user_id, request.product_id
        )

        return recommendation

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/create", response_model=Dict[str, Any])
async def create_social_campaign(
    request: CampaignCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建社交分享活动"""
    try:
        service = get_social_commerce_service(db)
        campaign = await service.create_social_sharing_campaign(request.product_id, request.config.dict())

        return campaign

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/share", response_model=Dict[str, Any])
async def share_product_to_social(
    request: SocialShareRequest,
    db: Session = Depends(get_db)
):
    """分享商品到社交平台"""
    try:
        service = get_social_commerce_service(db)
        share_result = await service.share_product_to_social(
            request.user_id, request.product_id, request.platform, request.content
        )

        return share_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=Dict[str, Any])
async def get_social_commerce_analytics(
    product_id: Optional[str] = Query(None, description="商品ID"),
    days: int = Query(30, ge=7, le=365, description="分析天数"),
    platform: Optional[str] = Query(None, description="平台过滤"),
    db: Session = Depends(get_db)
):
    """获取社交商务分析"""
    try:
        service = get_social_commerce_service(db)
        analytics = await service.get_social_commerce_analytics(product_id, days)

        # 应用平台过滤
        if platform:
            platform_analytics = analytics.get("data", {}).get("platform_analytics", {})
            if platform in platform_analytics:
                analytics["data"]["platform_analytics"] = {platform: platform_analytics[platform]}
            else:
                analytics["data"]["platform_analytics"] = {}

        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms", response_model=Dict[str, Any])
async def get_supported_platforms(db: Session = Depends(get_db)):
    """获取支持的社交平台"""
    try:
        service = get_social_commerce_service(db)

        platforms = {}
        for platform_name, platform in service.platforms.items():
            platforms[platform_name] = {
                "name": platform.platform_name,
                "is_active": platform.is_active,
                "supported_features": [
                    "trending_products",
                    "user_reviews",
                    "influencer_content",
                    "product_sharing"
                ]
            }

        return {
            "success": True,
            "data": {
                "platforms": platforms,
                "total_platforms": len(platforms),
                "active_platforms": len([p for p in platforms.values() if p["is_active"]])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content/performance", response_model=Dict[str, Any])
async def get_content_performance(
    user_id: Optional[str] = Query(None, description="用户ID"),
    days: int = Query(30, ge=7, le=365, description="分析天数"),
    db: Session = Depends(get_db)
):
    """获取内容性能分析"""
    try:
        service = get_social_commerce_service(db)

        # 获取性能数据
        performance_data = await service._get_content_performance(days)

        # 如果指定了用户ID，添加用户特定数据
        if user_id:
            user_performance = await service._get_user_content_performance(user_id, days)
            performance_data["user_performance"] = user_performance

        return {
            "success": True,
            "data": performance_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment-analysis", response_model=Dict[str, Any])
async def get_sentiment_analysis(
    product_id: Optional[str] = Query(None, description="商品ID"),
    category: Optional[str] = Query(None, description="商品类别"),
    days: int = Query(30, ge=7, le=365, description="分析天数"),
    db: Session = Depends(get_db)
):
    """获取情感分析"""
    try:
        service = get_social_commerce_service(db)
        sentiment_analysis = await service._get_sentiment_analysis(days)

        # 如果指定了商品或类别，获取特定分析
        if product_id or category:
            specific_analysis = await service._get_specific_sentiment_analysis(
                product_id, category, days
            )
            sentiment_analysis["specific_analysis"] = specific_analysis

        return {
            "success": True,
            "data": sentiment_analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending-topics", response_model=Dict[str, Any])
async def get_trending_topics(
    category: Optional[str] = Query(None, description="商品类别"),
    limit: int = Query(10, ge=1, le=20, description="返回数量"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取热门话题"""
    try:
        service = get_social_commerce_service(db)
        trending_topics = await service._get_trending_topics(days)

        # 应用类别过滤
        if category:
            trending_topics = [
                topic for topic in trending_topics
                if category.lower() in topic["topic"].lower()
            ]

        return {
            "success": True,
            "data": {
                "trending_topics": trending_topics[:limit],
                "total_topics": len(trending_topics),
                "filters": {
                    "category": category,
                    "limit": limit,
                    "days": days
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/influencers", response_model=Dict[str, Any])
async def get_influencer_content(
    category: Optional[str] = Query(None, description="商品类别"),
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    min_followers: int = Query(10000, ge=1000, description="最小粉丝数"),
    db: Session = Depends(get_db)
):
    """获取网红内容"""
    try:
        service = get_social_commerce_service(db)
        influencer_content = []

        # 从各平台获取网红内容
        for platform_name, platform in service.platforms.items():
            if platform.is_active:
                content = await platform.fetch_influencer_content(category)
                influencer_content.extend(content)

        # 过滤和排序
        filtered_content = [
            content for content in influencer_content
            if content.get("followers", 0) >= min_followers
        ]

        # 按粉丝数排序
        filtered_content.sort(key=lambda x: x.get("followers", 0), reverse=True)

        return {
            "success": True,
            "data": {
                "influencer_content": filtered_content[:limit],
                "total_results": len(filtered_content),
                "filters": {
                    "category": category,
                    "limit": limit,
                    "min_followers": min_followers
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/social-activity", response_model=Dict[str, Any])
async def get_user_social_activity(
    user_id: str,
    days: int = Query(30, ge=7, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取用户社交活动"""
    try:
        service = get_social_commerce_service(db)

        # 获取用户社交分享记录
        user_activity = await service._get_user_social_activity(user_id, days)

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "activity_period": f"{days}天",
                "social_activity": user_activity,
                "summary": await service._summarize_user_activity(user_activity)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign_details(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """获取活动详情"""
    try:
        # 这里需要实现活动详情查询
        # 简化版本，返回示例数据
        return {
            "success": True,
            "data": {
                "campaign_id": campaign_id,
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "performance": {
                    "total_shares": 150,
                    "total_engagement": 5000,
                    "conversion_rate": 0.12
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns", response_model=Dict[str, Any])
async def list_campaigns(
    user_id: Optional[str] = Query(None, description="用户ID"),
    status: str = Query("active", description="活动状态"),
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """列出活动"""
    try:
        # 简化版本，返回示例数据
        return {
            "success": True,
            "data": {
                "campaigns": [
                    {
                        "campaign_id": "campaign_001",
                        "product_id": "product_001",
                        "status": "active",
                        "created_at": datetime.utcnow().isoformat(),
                        "platforms": ["weibo", "xiaohongshu"],
                        "performance": {
                            "shares": 120,
                            "engagement": 3500
                        }
                    }
                ],
                "total_campaigns": 1,
                "filters": {
                    "user_id": user_id,
                    "status": status,
                    "limit": limit
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/activate", response_model=Dict[str, Any])
async def activate_campaign(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """激活活动"""
    try:
        # 简化版本，返回确认信息
        return {
            "success": True,
            "data": {
                "campaign_id": campaign_id,
                "status": "activated",
                "activated_at": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/pause", response_model=Dict[str, Any])
async def pause_campaign(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """暂停活动"""
    try:
        # 简化版本，返回确认信息
        return {
            "success": True,
            "data": {
                "campaign_id": campaign_id,
                "status": "paused",
                "paused_at": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def check_social_commerce_health(db: Session = Depends(get_db)):
    """检查社交商务服务健康状态"""
    try:
        service = get_social_commerce_service(db)

        # 检查各平台状态
        platform_status = {}
        for platform_name, platform in service.platforms.items():
            platform_status[platform_name] = {
                "name": platform.platform_name,
                "is_active": platform.is_active,
                "has_credentials": bool(platform.api_key)
            }

        return {
            "success": True,
            "data": {
                "status": "healthy",
                "platforms": platform_status,
                "total_platforms": len(service.platforms),
                "active_platforms": len([p for p in service.platforms.values() if p.is_active]),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# 添加缺失的方法到SocialCommerceService
async def _get_user_content_performance(self, user_id: str, days: int) -> Dict[str, Any]:
    """获取用户内容性能"""
    try:
        # 简化版本，返回示例数据
        return {
            "user_id": user_id,
            "total_shares": 15,
            "average_engagement": 85,
            "top_performing_platform": "xiaohongshu",
            "best_posting_time": "14:00"
        }
    except Exception as e:
        logger.error(f"Error getting user content performance: {e}")
        return {}

async def _get_specific_sentiment_analysis(self, product_id: str, category: str, days: int) -> Dict[str, Any]:
    """获取特定商品或类别的情感分析"""
    try:
        # 简化版本，返回示例数据
        return {
            "target": f"product_{product_id}" if product_id else f"category_{category}",
            "sentiment_score": 0.75,
            "positive_mentions": 120,
            "negative_mentions": 15,
            "neutral_mentions": 25
        }
    except Exception as e:
        logger.error(f"Error getting specific sentiment analysis: {e}")
        return {}

async def _get_user_social_activity(self, user_id: str, days: int) -> List[Dict[str, Any]]:
    """获取用户社交活动"""
    try:
        # 简化版本，返回示例数据
        return [
            {
                "activity_id": f"activity_{user_id}_001",
                "platform": "xiaohongshu",
                "action": "share",
                "product_id": "product_001",
                "engagement": {"likes": 25, "comments": 5},
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    except Exception as e:
        logger.error(f"Error getting user social activity: {e}")
        return []

async def _summarize_user_activity(self, activity: List[Dict[str, Any]]) -> Dict[str, Any]:
    """总结用户活动"""
    try:
        if not activity:
            return {"message": "No recent activity"}

        total_shares = len(activity)
        total_engagement = sum(
            act.get("engagement", {}).get("likes", 0) +
            act.get("engagement", {}).get("comments", 0)
            for act in activity
        )

        return {
            "total_activities": total_shares,
            "total_engagement": total_engagement,
            "average_engagement": round(total_engagement / total_shares, 2) if total_shares > 0 else 0,
            "most_active_platform": max(
                set(act["platform"] for act in activity),
                key=lambda x: sum(1 for act in activity if act["platform"] == x)
            )
        }
    except Exception as e:
        logger.error(f"Error summarizing user activity: {e}")
        return {"error": str(e)}

# 添加导入
import logging
logger = logging.getLogger(__name__)
from hashlib import sha256

def hash(text: str) -> str:
    """简单哈希函数"""
    return sha256(text.encode()).hexdigest()[:16]

# 添加方法到类
SocialCommerceService._get_user_content_performance = _get_user_content_performance
SocialCommerceService._get_specific_sentiment_analysis = _get_specific_sentiment_analysis
SocialCommerceService._get_user_social_activity = _get_user_social_activity
SocialCommerceService._summarize_user_activity = _summarize_user_activity