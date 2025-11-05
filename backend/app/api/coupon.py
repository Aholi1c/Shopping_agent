"""
优惠券和促销API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..services.coupon_service import CouponService
from ..services.llm_service import LLMService
from ..services.rag_service import RAGService

router = APIRouter()

class CouponDiscoveryRequest(BaseModel):
    """优惠券发现请求"""
    user_id: str = Field(..., description="用户ID")
    product_ids: Optional[List[str]] = Field(None, description="商品ID列表")
    categories: Optional[List[str]] = Field(None, description="类别列表")
    brands: Optional[List[str]] = Field(None, description="品牌列表")

class CouponValidationRequest(BaseModel):
    """优惠券验证请求"""
    coupon_code: str = Field(..., description="优惠券代码")
    user_id: str = Field(..., description="用户ID")
    cart_items: List[Dict[str, Any]] = Field(..., description="购物车商品")

class CartItem(BaseModel):
    """购物车商品"""
    product_id: str
    product_name: str
    price: float
    quantity: int = 1
    category: Optional[str] = None
    brand: Optional[str] = None

class CouponStrategyRequest(BaseModel):
    """优惠券策略请求"""
    user_id: str = Field(..., description="用户ID")
    strategy_type: str = Field("all", description="策略类型: all, saving, timing, stacking")

@router.post("/discover", response_model=Dict[str, Any])
async def discover_coupons(
    request: CouponDiscoveryRequest,
    db: Session = Depends(get_db)
):
    """智能发现优惠券"""
    try:
        llm_service = LLMService()
        rag_service = RAGService(db)

        async with CouponService(db, llm_service, rag_service) as service:
            result = await service.discover_coupons(
                user_id=request.user_id,
                product_ids=request.product_ids,
                categories=request.categories,
                brands=request.brands
            )

            return {
                "success": True,
                "data": result
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate", response_model=Dict[str, Any])
async def validate_coupon(
    request: CouponValidationRequest,
    db: Session = Depends(get_db)
):
    """验证优惠券"""
    try:
        llm_service = LLMService()
        rag_service = RAGService(db)

        async with CouponService(db, llm_service, rag_service) as service:
            result = await service.validate_coupon(
                coupon_code=request.coupon_code,
                user_id=request.user_id,
                cart_items=request.cart_items
            )

            return {
                "success": True,
                "data": result
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies/{user_id}", response_model=Dict[str, Any])
async def get_coupon_strategies(
    user_id: str,
    strategy_type: str = Query("all", description="策略类型"),
    db: Session = Depends(get_db)
):
    """获取优惠券策略"""
    try:
        llm_service = LLMService()
        rag_service = RAGService(db)

        async with CouponService(db, llm_service, rag_service) as service:
            result = await service.get_coupon_strategies(
                user_id=user_id,
                strategy_type=strategy_type
            )

            return {
                "success": True,
                "data": result
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available", response_model=Dict[str, Any])
async def get_available_coupons(
    user_id: str,
    category: Optional[str] = Query(None, description="商品类别"),
    brand: Optional[str] = Query(None, description="品牌"),
    min_discount: Optional[float] = Query(None, ge=0, description="最小折扣"),
    platform: Optional[str] = Query(None, description="平台"),
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取可用优惠券列表"""
    try:
        from ..models.ecommerce_models import Coupon
        from datetime import datetime

        query = db.query(Coupon).filter(
            and_(
                Coupon.is_active == True,
                Coupon.end_date >= datetime.now()
            )
        )

        # 应用过滤条件
        if category:
            query = query.filter(Coupon.applicable_categories.contains([category]))

        if brand:
            query = query.filter(Coupon.applicable_brands.contains([brand]))

        if platform:
            query = query.filter(Coupon.platform == platform)

        coupons = query.order_by(Coupon.discount_value.desc()).limit(limit).all()

        # 转换为字典格式
        coupon_list = []
        for coupon in coupons:
            coupon_data = {
                "id": coupon.id,
                "platform": coupon.platform,
                "code": coupon.code,
                "title": coupon.title,
                "description": coupon.description,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "min_order_amount": coupon.min_order_amount,
                "max_discount": coupon.max_discount,
                "start_date": coupon.start_date.isoformat(),
                "end_date": coupon.end_date.isoformat(),
                "usage_limit": coupon.usage_limit,
                "remaining_count": coupon.remaining_count,
                "applicable_categories": coupon.applicable_categories or [],
                "applicable_brands": coupon.applicable_brands or []
            }

            # 检查是否符合最小折扣要求
            if min_discount:
                if coupon.discount_type == "fixed" and coupon.discount_value >= min_discount:
                    coupon_list.append(coupon_data)
                elif coupon.discount_type == "percentage" and coupon.discount_value >= min_discount:
                    coupon_list.append(coupon_data)
            else:
                coupon_list.append(coupon_data)

        return {
            "success": True,
            "data": {
                "coupons": coupon_list,
                "total": len(coupon_list),
                "filters": {
                    "category": category,
                    "brand": brand,
                    "platform": platform,
                    "min_discount": min_discount
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending", response_model=Dict[str, Any])
async def get_trending_coupons(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    limit: int = Query(10, ge=1, le=20, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取热门优惠券"""
    try:
        from ..models.ecommerce_models import Coupon
        from datetime import datetime, timedelta

        since_date = datetime.now() - timedelta(hours=hours)

        # 获取最近新增的优惠券
        new_coupons = db.query(Coupon).filter(
            Coupon.created_at >= since_date
        ).order_by(Coupon.created_at.desc()).limit(limit).all()

        # 获取即将过期的优惠券
        expiring_coupons = db.query(Coupon).filter(
            and_(
                Coupon.end_date >= datetime.now(),
                Coupon.end_date <= datetime.now() + timedelta(days=3)
            )
        ).order_by(Coupon.end_date.asc()).limit(limit).all()

        # 获取高价值优惠券
        high_value_coupons = db.query(Coupon).filter(
            and_(
                Coupon.is_active == True,
                Coupon.end_date >= datetime.now()
            )
        ).order_by(
            (Coupon.discount_value * 100 / Coupon.min_order_amount).desc()
        ).limit(limit).all()

        return {
            "success": True,
            "data": {
                "new_coupons": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "platform": c.platform,
                        "discount_value": c.discount_value,
                        "discount_type": c.discount_type,
                        "created_at": c.created_at.isoformat()
                    }
                    for c in new_coupons
                ],
                "expiring_coupons": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "platform": c.platform,
                        "discount_value": c.discount_value,
                        "discount_type": c.discount_type,
                        "end_date": c.end_date.isoformat(),
                        "hours_left": int((c.end_date - datetime.now()).total_seconds() / 3600)
                    }
                    for c in expiring_coupons
                ],
                "high_value_coupons": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "platform": c.platform,
                        "discount_value": c.discount_value,
                        "discount_type": c.discount_type,
                        "min_order_amount": c.min_order_amount,
                        "value_ratio": c.discount_value / max(c.min_order_amount, 1)
                    }
                    for c in high_value_coupons
                ]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/{user_id}", response_model=Dict[str, Any])
async def get_user_coupon_dashboard(
    user_id: str,
    days: int = Query(30, ge=7, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取用户优惠券仪表板"""
    try:
        from ..models.ecommerce_models import Coupon, CouponStrategy
        from datetime import datetime, timedelta

        since_date = datetime.now() - timedelta(days=days)

        # 统计用户策略
        strategies = db.query(CouponStrategy).filter(
            CouponStrategy.user_id == user_id
        ).all()

        # 计算统计数据
        total_strategies = len(strategies)
        active_strategies = len([s for s in strategies if s.is_active])
        total_savings = sum(s.expected_savings for s in strategies if s.expected_savings)
        avg_success_rate = sum(s.success_rate for s in strategies) / len(strategies) if strategies else 0

        # 策略类型分布
        strategy_types = {}
        for strategy in strategies:
            strategy_types[strategy.strategy_type] = strategy_types.get(strategy.strategy_type, 0) + 1

        return {
            "success": True,
            "data": {
                "statistics": {
                    "total_strategies": total_strategies,
                    "active_strategies": active_strategies,
                    "total_expected_savings": round(total_savings, 2),
                    "average_success_rate": round(avg_success_rate * 100, 1)
                },
                "strategy_distribution": strategy_types,
                "recent_activity": [
                    {
                        "strategy_name": s.strategy_name,
                        "strategy_type": s.strategy_type,
                        "success_rate": round(s.success_rate * 100, 1),
                        "usage_count": s.usage_count,
                        "last_updated": s.updated_at.isoformat()
                    }
                    for s in sorted(strategies, key=lambda x: x.updated_at, reverse=True)[:5]
                ]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-cart", response_model=Dict[str, Any])
async def optimize_cart_with_coupons(
    cart_items: List[CartItem],
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """优化购物车优惠券组合"""
    try:
        from ..models.ecommerce_models import Coupon
        from datetime import datetime
        import itertools

        # 获取所有可用优惠券
        available_coupons = db.query(Coupon).filter(
            and_(
                Coupon.is_active == True,
                Coupon.end_date >= datetime.now()
            )
        ).all()

        cart_total = sum(item.price * item.quantity for item in cart_items)

        # 找出所有适用的优惠券组合
        applicable_combinations = []

        # 单个优惠券
        for coupon in available_coupons:
            if cart_total >= coupon.min_order_amount:
                discount = self._calculate_coupon_discount(coupon, cart_total)
                applicable_combinations.append(([coupon], discount))

        # 两个优惠券组合（如果支持）
        for coupon1, coupon2 in itertools.combinations(available_coupons, 2):
            if cart_total >= max(coupon1.min_order_amount, coupon2.min_order_amount):
                discount1 = self._calculate_coupon_discount(coupon1, cart_total)
                discount2 = self._calculate_coupon_discount(coupon2, cart_total - discount1)
                total_discount = discount1 + discount2
                applicable_combinations.append(([coupon1, coupon2], total_discount))

        # 按折扣金额排序
        applicable_combinations.sort(key=lambda x: x[1], reverse=True)

        # 返回最佳组合
        best_combination = applicable_combinations[0] if applicable_combination else ([], 0)

        return {
            "success": True,
            "data": {
                "original_total": cart_total,
                "best_discount": best_combination[1],
                "final_total": cart_total - best_combination[1],
                "savings_percentage": round(best_combination[1] / cart_total * 100, 1),
                "recommended_coupons": [
                    {
                        "id": c.id,
                        "code": c.code,
                        "title": c.title,
                        "discount_type": c.discount_type,
                        "discount_value": c.discount_value
                    }
                    for c in best_combination[0]
                ],
                "total_combinations_found": len(applicable_combinations)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_coupon_discount(self, coupon, cart_total):
    """计算优惠券折扣金额"""
    if coupon.discount_type == "fixed":
        discount = coupon.discount_value
    else:  # percentage
        discount = cart_total * coupon.discount_value / 100

    # 应用最大折扣限制
    if coupon.max_discount:
        discount = min(discount, coupon.max_discount)

    return discount

@router.get("/categories", response_model=Dict[str, Any])
async def get_coupon_categories(db: Session = Depends(get_db)):
    """获取优惠券类别统计"""
    try:
        from ..models.ecommerce_models import Coupon
        from collections import defaultdict

        coupons = db.query(Coupon).filter(
            Coupon.is_active == True
        ).all()

        category_stats = defaultdict(int)
        platform_stats = defaultdict(int)

        for coupon in coupons:
            # 统计平台
            platform_stats[coupon.platform] += 1

            # 统计类别
            if coupon.applicable_categories:
                for category in coupon.applicable_categories:
                    category_stats[category] += 1

        return {
            "success": True,
            "data": {
                "platforms": dict(platform_stats),
                "categories": dict(category_stats),
                "total_coupons": len(coupons)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy/create", response_model=Dict[str, Any])
async def create_coupon_strategy(
    user_id: str,
    strategy_name: str,
    strategy_type: str,
    description: str,
    rules: Dict[str, Any],
    expected_savings: float,
    db: Session = Depends(get_db)
):
    """创建优惠券策略"""
    try:
        from ..models.ecommerce_models import CouponStrategy

        strategy = CouponStrategy(
            user_id=user_id,
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            description=description,
            rules=rules,
            expected_savings=expected_savings
        )

        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        return {
            "success": True,
            "data": {
                "strategy_id": strategy.id,
                "strategy_name": strategy.strategy_name,
                "created_at": strategy.created_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))