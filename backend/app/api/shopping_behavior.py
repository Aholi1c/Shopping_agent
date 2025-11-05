"""
个性化购物行为分析API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..services.shopping_behavior_service import PersonalizedShoppingService, get_shopping_behavior_service

router = APIRouter()

class UserActionRequest(BaseModel):
    """用户行为请求"""
    user_id: str = Field(..., description="用户ID")
    action_type: str = Field(..., description="行为类型")
    action_data: Dict[str, Any] = Field(..., description="行为数据")

class BehaviorAnalysisRequest(BaseModel):
    """行为分析请求"""
    user_id: str = Field(..., description="用户ID")
    days: int = Field(30, ge=7, le=365, description="分析天数")
    include_recommendations: bool = Field(True, description="是否包含推荐")

class ShoppingJourneyRequest(BaseModel):
    """购物旅程请求"""
    user_id: str = Field(..., description="用户ID")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    journey_type: str = Field("personalized", description="旅程类型")

class UserSegmentRequest(BaseModel):
    """用户分群请求"""
    segment_name: str = Field(..., description="分群名称")
    criteria: Dict[str, Any] = Field(..., description="分群条件")

@router.post("/track", response_model=Dict[str, Any])
async def track_user_action(
    request: UserActionRequest,
    db: Session = Depends(get_db)
):
    """追踪用户行为"""
    try:
        service = get_shopping_behavior_service(db)
        result = service.behavior_tracker.track_user_action(
            user_id=request.user_id,
            action_type=request.action_type,
            action_data=request.action_data
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{user_id}", response_model=Dict[str, Any])
async def get_user_behavior_analysis(
    user_id: str,
    days: int = Query(30, ge=7, le=365, description="分析天数"),
    include_recommendations: bool = Query(True, description="是否包含推荐"),
    db: Session = Depends(get_db)
):
    """获取用户行为分析"""
    try:
        service = get_shopping_behavior_service(db)
        analysis = service.behavior_tracker.get_user_behavior_analysis(user_id, days)

        if include_recommendations:
            # 生成额外洞察
            analysis["additional_insights"] = await service._generate_additional_insights(analysis)

        return {
            "success": True,
            "data": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/journey/create", response_model=Dict[str, Any])
async def create_personalized_shopping_journey(
    request: ShoppingJourneyRequest,
    db: Session = Depends(get_db)
):
    """创建个性化购物旅程"""
    try:
        service = get_shopping_behavior_service(db)
        journey = await service.create_personalized_shopping_journey(
            user_id=request.user_id,
            context=request.context
        )

        return journey

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preferences/{user_id}", response_model=Dict[str, Any])
async def get_user_preferences(
    user_id: str,
    db: Session = Depends(get_db)
):
    """获取用户偏好"""
    try:
        from ..models.ecommerce_models import UserPreference

        preference = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

        if not preference:
            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "preferences": {},
                    "message": "No preferences found for this user"
                }
            }

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "preferences": {
                    "preferred_brands": preference.preferred_brands or [],
                    "preferred_categories": preference.preferred_categories or [],
                    "price_range": {
                        "min": preference.price_range_min,
                        "max": preference.price_range_max
                    },
                    "preferred_features": preference.preferred_features or [],
                    "last_updated": preference.updated_at.isoformat()
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences/{user_id}", response_model=Dict[str, Any])
async def update_user_preferences(
    user_id: str,
    preferences: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新用户偏好"""
    try:
        from ..models.ecommerce_models import UserPreference

        preference = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

        if not preference:
            preference = UserPreference(user_id=user_id)
            db.add(preference)

        # 更新偏好
        if "preferred_brands" in preferences:
            preference.preferred_brands = preferences["preferred_brands"]
        if "preferred_categories" in preferences:
            preference.preferred_categories = preferences["preferred_categories"]
        if "price_range" in preferences:
            preference.price_range_min = preferences["price_range"].get("min", 0)
            preference.price_range_max = preferences["price_range"].get("max", 10000)
        if "preferred_features" in preferences:
            preference.preferred_features = preferences["preferred_features"]

        preference.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "message": "Preferences updated successfully"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/behavior-summary/{user_id}", response_model=Dict[str, Any])
async def get_behavior_summary(
    user_id: str,
    days: int = Query(30, ge=7, le=365, description="总结天数"),
    db: Session = Depends(get_db)
):
    """获取用户行为总结"""
    try:
        service = get_shopping_behavior_service(db)

        # 获取基本分析
        analysis = service.behavior_tracker.get_user_behavior_analysis(user_id, days)

        # 生成简洁的总结
        summary = {
            "user_id": user_id,
            "summary_period": f"{days}天",
            "key_metrics": {},
            "behavior_trends": {},
            "recommendations": []
        }

        # 关键指标
        user_profile = analysis.get("user_profile", {})
        summary["key_metrics"] = {
            "total_searches": analysis.get("shopping_insights", {}).get("search_trends", {}).get("total_searches", 0),
            "total_purchases": user_profile.get("total_purchases", 0),
            "preferred_categories_count": len(user_profile.get("preferred_categories", [])),
            "preferred_brands_count": len(user_profile.get("preferred_brands", []))
        }

        # 行为趋势
        behavior_patterns = analysis.get("behavior_patterns", {})
        time_patterns = behavior_patterns.get("time_patterns", {})
        funnel_analysis = behavior_patterns.get("funnel_analysis", {})

        summary["behavior_trends"] = {
            "most_active_hour": time_patterns.get("most_active_hour"),
            "peak_activity_day": time_patterns.get("most_active_day"),
            "conversion_rates": funnel_analysis.get("conversion_rates", {})
        }

        # 简化推荐
        recommendations = analysis.get("recommendations", [])
        summary["recommendations"] = recommendations[:3]  # 只保留前3个

        return {
            "success": True,
            "data": summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{user_id}", response_model=Dict[str, Any])
async def get_personalized_insights(
    user_id: str,
    insight_type: str = Query("all", description="洞察类型: all, shopping, behavior, recommendations"),
    db: Session = Depends(get_db)
):
    """获取个性化洞察"""
    try:
        service = get_shopping_behavior_service(db)
        analysis = service.behavior_tracker.get_user_behavior_analysis(user_id)

        insights = {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "insights": {}
        }

        # 购物洞察
        if insight_type in ["all", "shopping"]:
            insights["insights"]["shopping"] = await service._generate_shopping_insights_detailed(analysis)

        # 行为洞察
        if insight_type in ["all", "behavior"]:
            insights["insights"]["behavior"] = await service._generate_behavior_insights_detailed(analysis)

        # 推荐洞察
        if insight_type in ["all", "recommendations"]:
            insights["insights"]["recommendations"] = await service._generate_recommendation_insights_detailed(analysis)

        return {
            "success": True,
            "data": insights
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/journey/history/{user_id}", response_model=Dict[str, Any])
async def get_shopping_journey_history(
    user_id: str,
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取购物旅程历史"""
    try:
        # 这里需要实现旅程历史的存储和检索
        # 简化版本，返回示例数据
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "journeys": [
                    {
                        "journey_id": "sample_journey_1",
                        "created_at": datetime.utcnow().isoformat(),
                        "journey_type": "personalized_shopping",
                        "completed": True,
                        "total_time_minutes": 45
                    }
                ],
                "total_journeys": 1
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/segments", response_model=Dict[str, Any])
async def create_user_segment(
    request: UserSegmentRequest,
    db: Session = Depends(get_db)
):
    """创建用户分群"""
    try:
        # 这里需要实现用户分群逻辑
        # 简化版本，返回确认信息
        return {
            "success": True,
            "data": {
                "segment_id": f"segment_{request.segment_name}_{datetime.utcnow().strftime('%Y%m%d')}",
                "segment_name": request.segment_name,
                "criteria": request.criteria,
                "created_at": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/segments", response_model=Dict[str, Any])
async def get_user_segments(
    db: Session = Depends(get_db)
):
    """获取用户分群列表"""
    try:
        # 简化版本，返回示例数据
        return {
            "success": True,
            "data": {
                "segments": [
                    {
                        "segment_id": "high_value_customers",
                        "segment_name": "高价值用户",
                        "user_count": 1250,
                        "created_at": datetime.utcnow().isoformat()
                    },
                    {
                        "segment_id": "frequent_shoppers",
                        "segment_name": "频繁购物用户",
                        "user_count": 3420,
                        "created_at": datetime.utcnow().isoformat()
                    }
                ]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/{user_id}", response_model=Dict[str, Any])
async def get_user_behavior_dashboard(
    user_id: str,
    days: int = Query(30, ge=7, le=365, description="仪表板数据天数"),
    db: Session = Depends(get_db)
):
    """获取用户行为仪表板"""
    try:
        service = get_shopping_behavior_service(db)
        analysis = service.behavior_tracker.get_user_behavior_analysis(user_id, days)

        dashboard = {
            "user_id": user_id,
            "dashboard_period": f"{days}天",
            "last_updated": datetime.utcnow().isoformat(),
            "widgets": {}
        }

        # 用户画像组件
        user_profile = analysis.get("user_profile", {})
        dashboard["widgets"]["user_profile"] = {
            "title": "用户画像",
            "data": {
                "top_categories": user_profile.get("preferred_categories", [])[:5],
                "top_brands": user_profile.get("preferred_brands", [])[:5],
                "price_range": user_profile.get("price_range", {}),
                "total_purchases": user_profile.get("total_purchases", 0)
            }
        }

        # 行为趋势组件
        behavior_patterns = analysis.get("behavior_patterns", {})
        dashboard["widgets"]["behavior_trends"] = {
            "title": "行为趋势",
            "data": {
                "time_patterns": behavior_patterns.get("time_patterns", {}),
                "funnel_analysis": behavior_patterns.get("funnel_analysis", {})
            }
        }

        # 购物洞察组件
        shopping_insights = analysis.get("shopping_insights", {})
        dashboard["widgets"]["shopping_insights"] = {
            "title": "购物洞察",
            "data": shopping_insights
        }

        # 个性化建议组件
        dashboard["widgets"]["recommendations"] = {
            "title": "个性化建议",
            "data": {
                "recommendations": analysis.get("recommendations", [])[:5]
            }
        }

        return {
            "success": True,
            "data": dashboard
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 需要添加到PersonalizedShoppingService的方法
async def _generate_additional_insights(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """生成额外洞察"""
    return {
        "engagement_score": self._calculate_engagement_score(analysis),
        "loyalty_level": self._calculate_loyalty_level(analysis),
        "next_best_action": self._predict_next_best_action(analysis)
    }

def _calculate_engagement_score(self, analysis: Dict[str, Any]) -> float:
    """计算用户参与度分数"""
    user_profile = analysis.get("user_profile", {})
    shopping_insights = analysis.get("shopping_insights", {})

    # 基于多个因素计算参与度
    search_count = shopping_insights.get("search_trends", {}).get("total_searches", 0)
    purchase_count = user_profile.get("total_purchases", 0)
    browsing_count = user_profile.get("total_browsing_actions", 0)

    # 简单的加权计算
    score = (search_count * 0.3 + purchase_count * 0.5 + browsing_count * 0.2)
    return min(round(score, 2), 100.0)

def _calculate_loyalty_level(self, analysis: Dict[str, Any]) -> str:
    """计算用户忠诚度等级"""
    user_profile = analysis.get("user_profile", {})
    purchase_count = user_profile.get("total_purchases", 0)

    if purchase_count >= 20:
        return "钻石会员"
    elif purchase_count >= 10:
        return "黄金会员"
    elif purchase_count >= 5:
        return "白银会员"
    else:
        return "普通会员"

def _predict_next_best_action(self, analysis: Dict[str, Any]) -> str:
    """预测下一步最佳行动"""
    behavior_patterns = analysis.get("behavior_patterns", {})
    funnel_analysis = behavior_patterns.get("funnel_analysis", {})
    conversion_rates = funnel_analysis.get("conversion_rates", {})

    # 基于转化率预测
    cart_to_purchase = conversion_rates.get("cart_to_purchase", 0)

    if cart_to_purchase < 0.5:
        return "推送优惠券以提高转化率"
    else:
        return "推荐相关商品增加客单价"

async def _generate_shopping_insights_detailed(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """生成详细购物洞察"""
    shopping_insights = analysis.get("shopping_insights", {})

    return {
        "search_effectiveness": self._analyze_search_effectiveness(shopping_insights),
        "recommendation_impact": self._analyze_recommendation_impact(shopping_insights),
        "purchase_patterns": self._analyze_purchase_patterns(analysis)
    }

def _analyze_search_effectiveness(self, shopping_insights: Dict[str, Any]) -> Dict[str, Any]:
    """分析搜索效果"""
    search_trends = shopping_insights.get("search_trends", {})
    return {
        "effectiveness_score": 7.5,  # 简化计算
        "top_search_categories": search_trends.get("common_search_terms", {})[:5],
        "search_to_purchase_rate": 0.25  # 简化数据
    }

def _analyze_recommendation_impact(self, shopping_insights: Dict[str, Any]) -> Dict[str, Any]:
    """分析推荐影响"""
    recommendation_effectiveness = shopping_insights.get("recommendation_effectiveness", {})
    return {
        "click_through_rate": recommendation_effectiveness.get("average_conversion_rate", 0),
        "recommendation_acceptance": 68.5,  # 简化数据
        "most_effective_categories": recommendation_effectiveness.get("most_recommended_categories", [])
    }

def _analyze_purchase_patterns(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """分析购买模式"""
    user_profile = analysis.get("user_profile", {})
    return {
        "average_purchase_value": 299.99,  # 简化数据
        "preferred_purchase_time": "14:00-16:00",
        "repeat_purchase_rate": 0.35
    }

async def _generate_behavior_insights_detailed(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """生成详细行为洞察"""
    behavior_patterns = analysis.get("behavior_patterns", {})
    return {
        "activity_patterns": behavior_patterns.get("time_patterns", {}),
        "category_preferences": behavior_patterns.get("preference_patterns", {}).get("preferred_categories", {}),
        "price_sensitivity": behavior_patterns.get("preference_patterns", {}).get("price_sensitivity", {})
    }

async def _generate_recommendation_insights_detailed(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """生成详细推荐洞察"""
    recommendations = analysis.get("recommendations", [])
    return {
        "top_recommendations": recommendations[:5],
        "recommendation_confidence": 0.82,  # 简化数据
        "personalization_factors": ["历史购买记录", "浏览行为", "价格偏好"]
    }

# 添加方法到类
PersonalizedShoppingService._generate_additional_insights = _generate_additional_insights
PersonalizedShoppingService._calculate_engagement_score = _calculate_engagement_score
PersonalizedShoppingService._calculate_loyalty_level = _calculate_loyalty_level
PersonalizedShoppingService._predict_next_best_action = _predict_next_best_action
PersonalizedShoppingService._generate_shopping_insights_detailed = _generate_shopping_insights_detailed
PersonalizedShoppingService._analyze_search_effectiveness = _analyze_search_effectiveness
PersonalizedShoppingService._analyze_recommendation_impact = _analyze_recommendation_impact
PersonalizedShoppingService._analyze_purchase_patterns = _analyze_purchase_patterns
PersonalizedShoppingService._generate_behavior_insights_detailed = _generate_behavior_insights_detailed
PersonalizedShoppingService._generate_recommendation_insights_detailed = _generate_recommendation_insights_detailed