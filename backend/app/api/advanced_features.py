from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..core.database import get_db
from ..services.price_prediction_service import price_prediction_service
from ..services.risk_detection_service import risk_detection_service
from ..services.decision_tool_service import decision_tool_service

logger = logging.getLogger(__name__)
router = APIRouter()

# 价格预测和促销优化相关API
@router.get("/price-prediction/{product_id}")
async def get_price_prediction(
    product_id: int,
    prediction_days: int = 30,
    db: Session = Depends(get_db)
):
    """获取商品价格预测"""
    try:
        result = await price_prediction_service.predict_price_trend(product_id, prediction_days)
        return result
    except Exception as e:
        logger.error(f"Error getting price prediction: {e}")
        raise HTTPException(status_code=500, detail="价格预测失败")

@router.post("/price-prediction/optimize-timing")
async def optimize_purchase_timing(
    product_id: int,
    user_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db)
):
    """优化购买时机"""
    try:
        result = await price_prediction_service.optimize_purchase_timing(
            product_id, user_id, quantity
        )
        return result
    except Exception as e:
        logger.error(f"Error optimizing purchase timing: {e}")
        raise HTTPException(status_code=500, detail="购买时机优化失败")

@router.post("/price-alerts")
async def create_price_alert(
    user_id: int,
    product_id: int,
    alert_type: str,
    threshold_value: float,
    notification_method: str = "app",
    db: Session = Depends(get_db)
):
    """创建价格提醒"""
    try:
        result = await price_prediction_service.create_price_alert(
            user_id, product_id, alert_type, threshold_value, notification_method
        )
        return result
    except Exception as e:
        logger.error(f"Error creating price alert: {e}")
        raise HTTPException(status_code=500, detail="价格提醒创建失败")

@router.get("/price-alerts/check")
async def check_price_alerts(db: Session = Depends(get_db)):
    """检查价格提醒（管理员用）"""
    try:
        triggered_alerts = await price_prediction_service.check_price_alerts()
        return {"triggered_alerts": triggered_alerts}
    except Exception as e:
        logger.error(f"Error checking price alerts: {e}")
        raise HTTPException(status_code=500, detail="价格提醒检查失败")

@router.get("/promotion-calendar")
async def get_promotion_calendar(
    platform: Optional[str] = None,
    days_ahead: int = 90,
    db: Session = Depends(get_db)
):
    """获取促销日历"""
    try:
        from ..models.models import PromotionCalendar
        from datetime import timedelta

        query = db.query(PromotionCalendar).filter(
            PromotionCalendar.is_active == True,
            PromotionCalendar.start_date <= datetime.now() + timedelta(days=days_ahead)
        )

        if platform:
            query = query.filter(PromotionCalendar.platform == platform)

        promotions = query.order_by(PromotionCalendar.start_date).all()
        return {"promotions": promotions}
    except Exception as e:
        logger.error(f"Error getting promotion calendar: {e}")
        raise HTTPException(status_code=500, detail="促销日历获取失败")

# 商品风险识别相关API
@router.get("/risk-analysis/{product_id}")
async def analyze_product_risks(
    product_id: int,
    db: Session = Depends(get_db)
):
    """分析商品风险"""
    try:
        result = await risk_detection_service.analyze_product_risks(product_id)
        return result
    except Exception as e:
        logger.error(f"Error analyzing product risks: {e}")
        raise HTTPException(status_code=500, detail="商品风险分析失败")

@router.post("/risk-analysis/batch")
async def batch_risk_analysis(
    product_ids: List[int],
    db: Session = Depends(get_db)
):
    """批量风险分析"""
    try:
        result = await risk_detection_service.batch_risk_analysis(product_ids)
        return result
    except Exception as e:
        logger.error(f"Error in batch risk analysis: {e}")
        raise HTTPException(status_code=500, detail="批量风险分析失败")

@router.get("/risk-statistics")
async def get_risk_statistics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """获取风险统计"""
    try:
        result = await risk_detection_service.get_risk_statistics(days)
        return result
    except Exception as e:
        logger.error(f"Error getting risk statistics: {e}")
        raise HTTPException(status_code=500, detail="风险统计获取失败")

@router.post("/risk-keywords")
async def add_risk_keyword(
    keyword: str,
    risk_category: str,
    severity_score: float = 0.5,
    context_patterns: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """添加风险关键词"""
    try:
        from ..models.models import RiskKeywordLibrary

        risk_keyword = RiskKeywordLibrary(
            keyword=keyword,
            risk_category=risk_category,
            severity_score=severity_score,
            context_patterns=context_patterns or [],
            frequency_weight=1.0
        )
        db.add(risk_keyword)
        db.commit()
        db.refresh(risk_keyword)

        return {"message": "风险关键词添加成功", "keyword_id": risk_keyword.id}
    except Exception as e:
        logger.error(f"Error adding risk keyword: {e}")
        raise HTTPException(status_code=500, detail="风险关键词添加失败")

@router.get("/risk-keywords")
async def get_risk_keywords(
    risk_category: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取风险关键词库"""
    try:
        from ..models.models import RiskKeywordLibrary
        query = db.query(RiskKeywordLibrary)

        if risk_category:
            query = query.filter(RiskKeywordLibrary.risk_category == risk_category)

        keywords = query.order_by(desc(RiskKeywordLibrary.severity_score)).limit(limit).all()
        return {"risk_keywords": keywords}
    except Exception as e:
        logger.error(f"Error getting risk keywords: {e}")
        raise HTTPException(status_code=500, detail="风险关键词获取失败")

# 交互式决策工具相关API
@router.post("/decision/create-session")
async def create_decision_session(
    user_id: int,
    product_candidates: List[int],
    context: str = "general",
    db: Session = Depends(get_db)
):
    """创建决策会话"""
    try:
        result = await decision_tool_service.create_decision_session(
            user_id, product_candidates, context
        )
        return result
    except Exception as e:
        logger.error(f"Error creating decision session: {e}")
        raise HTTPException(status_code=500, detail="决策会话创建失败")

@router.post("/decision/update-weights")
async def update_decision_weights(
    user_id: int,
    session_id: str,
    new_weights: Dict[str, float],
    product_candidates: List[int],
    db: Session = Depends(get_db)
):
    """更新决策权重"""
    try:
        result = await decision_tool_service.update_weights_and_recommend(
            user_id, session_id, new_weights, product_candidates
        )
        return result
    except Exception as e:
        logger.error(f"Error updating decision weights: {e}")
        raise HTTPException(status_code=500, detail="决策权重更新失败")

@router.get("/decision/history/{user_id}")
async def get_decision_history(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取决策历史"""
    try:
        result = await decision_tool_service.get_decision_history(user_id, limit)
        return result
    except Exception as e:
        logger.error(f"Error getting decision history: {e}")
        raise HTTPException(status_code=500, detail="决策历史获取失败")

@router.get("/decision/dimensions")
async def get_decision_dimensions():
    """获取决策维度信息"""
    try:
        return {
            "dimensions": decision_tool_service.default_weights,
            "descriptions": decision_tool_service.dimension_descriptions
        }
    except Exception as e:
        logger.error(f"Error getting decision dimensions: {e}")
        raise HTTPException(status_code=500, detail="决策维度信息获取失败")

# 用户偏好管理API
@router.get("/user-weights/{user_id}")
async def get_user_decision_weights(
    user_id: int,
    context: str = "general",
    db: Session = Depends(get_db)
):
    """获取用户决策权重"""
    try:
        from ..models.models import UserDecisionWeights
        weights = db.query(UserDecisionWeights).filter(
            UserDecisionWeights.user_id == user_id,
            UserDecisionWeights.decision_context == context,
            UserDecisionWeights.is_active == True
        ).all()

        weight_dict = {}
        for weight in weights:
            weight_dict[weight.weight_dimension] = weight.weight_value

        return {
            "user_id": user_id,
            "context": context,
            "weights": weight_dict,
            "default_weights": decision_tool_service.default_weights
        }
    except Exception as e:
        logger.error(f"Error getting user weights: {e}")
        raise HTTPException(status_code=500, detail="用户权重获取失败")

# 综合分析API
@router.post("/comprehensive-analysis/{product_id}")
async def comprehensive_product_analysis(
    product_id: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """综合商品分析（价格预测 + 风险评估 + 推荐建议）"""
    try:
        # 并行执行多个分析
        import asyncio

        # 价格预测
        price_task = price_prediction_service.predict_price_trend(product_id, 30)

        # 风险分析
        risk_task = risk_detection_service.analyze_product_risks(product_id)

        # 等待所有任务完成
        price_result, risk_result = await asyncio.gather(price_task, risk_task)

        # 生成综合建议
        comprehensive_advice = await self._generate_comprehensive_advice(
            price_result, risk_result, user_id
        )

        return {
            "product_id": product_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "price_analysis": price_result,
            "risk_analysis": risk_result,
            "comprehensive_advice": comprehensive_advice,
            "overall_recommendation": comprehensive_advice.get("action", "neutral")
        }

    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail="综合分析失败")

async def _generate_comprehensive_advice(
    self,
    price_result: Dict[str, Any],
    risk_result: Dict[str, Any],
    user_id: Optional[int]
) -> Dict[str, Any]:
    """生成综合建议"""
    try:
        advice = {
            "action": "neutral",
            "confidence": 0.5,
            "reasons": [],
            "warnings": [],
            "recommendations": []
        }

        # 价格因素分析
        if "error" not in price_result:
            purchase_advice = price_result.get("purchase_advice", {})
            price_action = purchase_advice.get("action", "hold")

            if price_action == "buy_now":
                advice["reasons"].append("当前价格相对较低，建议考虑购买")
                advice["confidence"] += 0.2
            elif price_action == "wait":
                advice["reasons"].append("预计价格可能下降，建议等待")
                advice["warnings"].append("可能需要等待数天才能获得更好价格")

        # 风险因素分析
        if "error" not in risk_result:
            risk_level = risk_result.get("overall_risk_level", "low")

            if risk_level in ["high", "critical"]:
                advice["action"] = "avoid"
                advice["warnings"].extend(risk_result.get("mitigation_suggestions", []))
                advice["confidence"] = max(advice["confidence"], 0.8)
                advice["reasons"].append(f"商品风险等级较高({risk_level})，建议谨慎考虑")
            elif risk_level == "medium":
                advice["warnings"].append("商品存在一定风险，建议仔细查看风险详情")
                if advice["action"] == "buy_now":
                    advice["action"] = "cautious"

        # 综合建议
        if advice["action"] == "neutral":
            if advice["confidence"] > 0.6:
                advice["action"] = "consider"
                advice["recommendations"].append("商品总体状况良好，可以考虑购买")
            else:
                advice["recommendations"].append("建议收集更多信息后再做决定")

        # 个性化建议（如果有用户信息）
        if user_id:
            advice["recommendations"].append("建议根据您的个人偏好调整决策权重")

        return advice

    except Exception as e:
        logger.error(f"Error generating comprehensive advice: {e}")
        return {"action": "neutral", "reasons": ["无法生成综合建议"]}