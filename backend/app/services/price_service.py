import asyncio
import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging
import numpy as np

from ..models.models import (
    Product, PriceHistory, Coupon, CouponProduct, CouponStrategy,
    UserPreference, PurchaseHistory, SearchHistory
)
from ..models.schemas import (
    BestDealRequest, BestDealResponse, CouponResponse,
    ProductResponse, PlatformType, DiscountType
)
from ..core.config import settings
from .llm_service import LLMService
from .shopping_service import ShoppingService

logger = logging.getLogger(__name__)

class PriceService:
    def __init__(self, db: Session, llm_service: LLMService, shopping_service: ShoppingService):
        self.db = db
        self.llm_service = llm_service
        self.shopping_service = shopping_service

    async def compare_prices(self, query: str, platforms: List[PlatformType] = None) -> Dict:
        """多平台价格对比 - 优先从数据库获取数据"""
        if platforms is None:
            platforms = [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD]

        # 首先尝试从数据库直接搜索（这是最快的，使用用户上传的products_data.json数据）
        try:
            from ..models.schemas import ProductSearchRequest
            from sqlalchemy import or_, func
            from ..models.models import Product
            
            # 构建数据库查询
            db_query = self.db.query(Product)
            
            # 平台过滤 - 处理PlatformType枚举
            platform_names = []
            for p in platforms:
                if hasattr(p, 'value'):
                    platform_names.append(p.value)
                elif isinstance(p, str):
                    platform_names.append(p)
                else:
                    platform_names.append(str(p))
            
            # 确保平台名称格式正确（小写）
            platform_names = [p.lower() for p in platform_names]
            logger.info(f"查询平台: {platform_names}")
            
            db_query = db_query.filter(Product.platform.in_(platform_names))
            
            # 商品名称模糊匹配 - 使用更灵活的匹配策略
            if query:
                # 清理查询关键词
                query_clean = query.strip()
                # 支持部分匹配（包含关系）
                db_query = db_query.filter(
                    or_(
                        Product.title.contains(query_clean),
                        Product.description.contains(query_clean),
                        Product.title.like(f"%{query_clean}%"),  # 更宽松的匹配
                        Product.description.like(f"%{query_clean}%")
                    )
                )
                logger.info(f"搜索关键词: {query_clean}")
            
            # 按价格排序，限制结果数量
            db_products = db_query.order_by(Product.price.asc()).limit(20).all()
            
            if db_products and len(db_products) > 0:
                logger.info(f"从数据库找到 {len(db_products)} 个商品用于价格对比")
                # 直接使用数据库结果
                products = []
                for product in db_products:
                    # 获取商品URL（如果有）
                    product_url = None
                    if hasattr(product, 'product_url') and product.product_url:
                        product_url = product.product_url
                    elif hasattr(product, 'url') and product.url:
                        product_url = product.url
                    
                    products.append({
                        "title": product.title,
                        "price": float(product.price) if product.price else 0,
                        "platform": product.platform,
                        "product_id": product.product_id,
                        "product_url": product_url,
                        "currency": "CNY",  # 数据库中的价格都是人民币
                        "original_price": float(product.original_price) if hasattr(product, 'original_price') and product.original_price else None,
                        "image_url": product.image_url if hasattr(product, 'image_url') and product.image_url else None
                    })
                
                # 如果数据库有结果，直接使用（不要求至少3个，只要有结果就可以）
                if len(products) > 0:
                    # 按商品名称分组对比价格
                    comparison = {}
                    for product in products:
                        if not isinstance(product, dict):
                            continue
                            
                        title = product.get("title", "")
                        price = product.get("price", 0)
                        platform = product.get("platform", "")
                        
                        if not title or price <= 0:
                            continue
                        
                        product_key = self._normalize_product_name(title)
                        if product_key not in comparison:
                            comparison[product_key] = []
                        comparison[product_key].append({
                            "title": title,
                            "price": price,
                            "platform": platform,
                            "product_id": product.get("product_id", "")
                        })
                    
                    # 分析每个商品组的价格差异（即使只有一个商品也返回）
                    analysis = {}
                    for product_key, product_list in comparison.items():
                        prices = [p["price"] for p in product_list if p.get("price", 0) > 0]
                        if prices:
                            min_price = min(prices)
                            max_price = max(prices) if len(prices) > 1 else min_price
                            price_diff = max_price - min_price if len(prices) > 1 else 0
                            
                            # 找到最低价格的平台
                            best_platform = ""
                            best_product = None
                            for p in product_list:
                                if p.get("price") == min_price:
                                    best_platform = p.get("platform", "")
                                    best_product = p
                                    break
                            
                            # 构建平台价格映射
                            platform_prices = {}
                            for p in product_list:
                                platform = p.get("platform", "")
                                price = p.get("price", 0)
                                if platform and price > 0:
                                    platform_prices[platform] = {
                                        "price": price,
                                        "title": p.get("title", ""),
                                        "product_id": p.get("product_id", ""),
                                        "product_url": p.get("product_url", "")
                                    }
                            
                            # 即使只有一个商品，也添加到分析结果中
                            analysis[product_key] = {
                                "min_price": min_price,
                                "max_price": max_price,
                                "price_diff": price_diff,
                                "price_diff_percent": (price_diff / max_price * 100) if max_price > 0 and len(prices) > 1 else 0,
                                "best_platform": best_platform,
                                "best_product": best_product,
                                "platforms": list(platform_prices.keys()),
                                "platform_prices": platform_prices,  # 按平台组织的价格信息
                                "products": product_list,
                                "product_count": len(product_list),
                                "has_multiple_platforms": len(product_list) > 1  # 标记是否有多个平台
                            }
                        else:
                            # 即使没有价格，也保留商品信息
                            analysis[product_key] = {
                                "products": product_list,
                                "product_count": len(product_list),
                                "platforms": [p.get("platform", "") for p in product_list if p.get("platform")]
                            }
                    
                    # 即使只有一个商品组，也返回结果
                    if analysis:
                        return {
                            "query": query,
                            "comparison": analysis,
                            "total_products": len(products),
                            "search_time": 0,
                            "data_source": "database",
                            "message": f"Found {len(products)} products from database, {len(analysis)} product groups"
                        }
                    else:
                        # 如果分组后没有结果，直接返回所有商品（不分组）
                        logger.warning(f"商品分组后没有结果，返回原始商品列表")
                        # 按平台组织价格
                        platform_prices = {}
                        for product in products:
                            platform = product.get("platform", "")
                            if platform:
                                if platform not in platform_prices:
                                    platform_prices[platform] = []
                                platform_prices[platform].append({
                                    "title": product.get("title", ""),
                                    "price": product.get("price", 0),
                                    "product_id": product.get("product_id", "")
                                })
                        
                        return {
                            "query": query,
                            "comparison": {
                                "all_products": {
                                    "platform_prices": platform_prices,
                                    "products": products,
                                    "total_count": len(products)
                                }
                            },
                            "total_products": len(products),
                            "search_time": 0,
                            "data_source": "database",
                            "message": f"Found {len(products)} products from database"
                        }
        except Exception as e:
            logger.warning(f"数据库价格对比失败: {e}")
            # 不再回退到API，直接返回空结果
            return {
                "query": query,
                "comparison": {},
                "total_products": 0,
                "search_time": 0,
                "data_source": "database",
                "message": "Database query failed. Please ensure product data has been uploaded to the database. Price comparison only uses database data and does not call external APIs."
            }

        # 如果数据库没有结果，直接返回空结果，不再调用API
        logger.info("No matching products found in database. Price comparison only uses database data")
        return {
            "query": query,
            "comparison": {},
            "total_products": 0,
            "search_time": 0,
            "data_source": "database",
            "message": "No matching products found. Price comparison only uses database data (from products_data.json). Please ensure product data has been uploaded to the database. To add new products, use the product management API to upload data."
        }

    async def track_price_changes(self, product_id: int, days: int = 30) -> Dict:
        """追踪价格变化"""
        since_date = datetime.now() - timedelta(days=days)

        # 获取价格历史
        price_history = self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.product_id == product_id,
                PriceHistory.timestamp >= since_date
            )
        ).order_by(PriceHistory.timestamp.asc()).all()

        if not price_history:
            return {"error": "No price history found"}

        # 计算价格变化趋势
        prices = [p.price for p in price_history]
        timestamps = [p.timestamp for p in price_history]

        # 计算统计指标
        current_price = prices[-1]
        start_price = prices[0]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        # 计算变化趋势
        price_change = current_price - start_price
        price_change_percent = (price_change / start_price) * 100 if start_price > 0 else 0

        # 简单的趋势分析
        if len(prices) >= 3:
            # 计算移动平均
            ma_3 = sum(prices[-3:]) / 3
            trend = "上升" if current_price > ma_3 else "下降" if current_price < ma_3 else "稳定"
        else:
            trend = "数据不足"

        # 预测未来价格（简单线性回归）
        prediction = self._simple_price_prediction(timestamps, prices)

        return {
            "product_id": product_id,
            "current_price": current_price,
            "start_price": start_price,
            "min_price": min_price,
            "max_price": max_price,
            "average_price": avg_price,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "trend": trend,
            "prediction": prediction,
            "history": [
                {
                    "date": p.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "price": p.price,
                    "original_price": p.original_price
                }
                for p in price_history
            ]
        }

    def _simple_price_prediction(self, timestamps: List[datetime], prices: List[float]) -> Dict:
        """简单的价格预测"""
        try:
            if len(prices) < 2:
                return {"error": "Insufficient data for prediction"}

            # 将时间戳转换为数值
            time_values = [(t - timestamps[0]).total_seconds() / 3600 for t in timestamps]  # 转换为小时

            # 简单线性回归
            n = len(time_values)
            sum_x = sum(time_values)
            sum_y = sum(prices)
            sum_xy = sum(x * y for x, y in zip(time_values, prices))
            sum_x2 = sum(x * x for x in time_values)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n

            # 预测未来7天
            future_time = time_values[-1] + 24 * 7  # 7天后
            predicted_price = slope * future_time + intercept

            # 计算置信度（基于R²）
            mean_y = sum_y / n
            ss_tot = sum((y - mean_y) ** 2 for y in prices)
            ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(time_values, prices))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {
                "predicted_price": predicted_price,
                "confidence": min(max(r_squared, 0), 1),  # 限制在0-1之间
                "trend_direction": "上升" if slope > 0 else "下降" if slope < 0 else "稳定",
                "days_predicted": 7
            }

        except Exception as e:
            logger.error(f"Error in price prediction: {e}")
            return {"error": "Prediction failed"}

    async def get_best_deal(self, request: BestDealRequest) -> BestDealResponse:
        """获取最佳优惠方案"""
        try:
            # 获取商品信息
            product = self.db.query(Product).filter(Product.id == request.product_id).first()
            if not product:
                raise ValueError("Product not found")

            # 获取适用优惠券
            available_coupons = await self._get_available_coupons(product, request.user_id)

            # 计算最优优惠券组合
            best_combination = await self._find_best_coupon_combination(
                product, available_coupons, request.quantity
            )

            # 生成购买建议
            if best_combination:
                final_price = best_combination["final_price"]
                total_discount = best_combination["total_discount"]
                strategy_description = best_combination["description"]
                recommended_coupons = best_combination["coupons"]
            else:
                final_price = product.price * request.quantity if product.price else 0
                total_discount = 0
                strategy_description = "无可用优惠券，建议直接购买"
                recommended_coupons = []

            original_price = (product.original_price or product.price or 0) * request.quantity
            savings_amount = original_price - final_price

            # 保存策略到数据库（如果有用户ID）
            if request.user_id and best_combination:
                await self._save_coupon_strategy(request.user_id, product.id, best_combination)

            return BestDealResponse(
                product_id=product.id,
                best_price=final_price,
                original_price=original_price,
                total_discount=total_discount,
                recommended_coupons=recommended_coupons,
                savings_amount=savings_amount,
                final_price=final_price,
                strategy_description=strategy_description
            )

        except Exception as e:
            logger.error(f"Error getting best deal: {e}")
            return BestDealResponse(
                product_id=request.product_id,
                best_price=0,
                original_price=0,
                total_discount=0,
                recommended_coupons=[],
                savings_amount=0,
                final_price=0,
                strategy_description="计算优惠方案失败"
            )

    async def _get_available_coupons(self, product: Product, user_id: Optional[int] = None) -> List[Coupon]:
        """获取可用优惠券"""
        try:
            current_time = datetime.now()

            # 基础查询：有效且未过期的优惠券
            query = self.db.query(Coupon).filter(
                and_(
                    Coupon.platform == product.platform,
                    or_(Coupon.end_date.is_(None), Coupon.end_date > current_time),
                    or_(Coupon.usage_limit.is_(None), Coupon.usage_count < Coupon.usage_limit)
                )
            )

            # 检查是否适用于特定商品
            applicable_coupons = []
            for coupon in query.all():
                # 检查金额门槛
                if coupon.min_purchase_amount and product.price and product.price < coupon.min_purchase_amount:
                    continue

                # 检查商品适用性
                coupon_products = self.db.query(CouponProduct).filter(
                    CouponProduct.coupon_id == coupon.id
                ).all()

                # 如果没有指定适用商品，则适用所有商品
                if not coupon_products:
                    applicable_coupons.append(coupon)
                else:
                    # 检查是否适用于当前商品
                    product_ids = [cp.product_id for cp in coupon_products]
                    if product.id in product_ids:
                        applicable_coupons.append(coupon)

            return applicable_coupons

        except Exception as e:
            logger.error(f"Error getting available coupons: {e}")
            return []

    async def _find_best_coupon_combination(self, product: Product, coupons: List[Coupon], quantity: int = 1) -> Optional[Dict]:
        """寻找最佳优惠券组合"""
        try:
            if not coupons:
                return None

            base_price = (product.price or 0) * quantity
            best_total = base_price
            best_combination = []
            best_description = "不使用优惠券"

            # 简化策略：尝试单个优惠券和常见组合
            combinations_to_try = []

            # 单个优惠券
            for coupon in coupons:
                combinations_to_try.append([coupon])

            # 两两组合（如果平台支持）
            if len(coupons) >= 2:
                for i in range(len(coupons)):
                    for j in range(i + 1, len(coupons)):
                        # 检查是否可以叠加使用
                        if self._can_combine_coupons(coupons[i], coupons[j]):
                            combinations_to_try.append([coupons[i], coupons[j]])

            # 评估每种组合
            for combination in combinations_to_try:
                total_price, description = self._calculate_combination_price(
                    base_price, combination
                )

                if total_price < best_total:
                    best_total = total_price
                    best_combination = combination
                    best_description = description

            if best_combination:
                return {
                    "final_price": best_total,
                    "total_discount": base_price - best_total,
                    "coupons": [CouponResponse.from_orm(c) for c in best_combination],
                    "description": best_description
                }

            return None

        except Exception as e:
            logger.error(f"Error finding best coupon combination: {e}")
            return None

    def _can_combine_coupons(self, coupon1: Coupon, coupon2: Coupon) -> bool:
        """检查两个优惠券是否可以叠加使用"""
        # 简化规则：不同类型的优惠券可以叠加
        # 实际项目中需要根据各平台的具体规则来实现
        return coupon1.discount_type != coupon2.discount_type

    def _calculate_combination_price(self, base_price: float, coupons: List[Coupon]) -> Tuple[float, str]:
        """计算优惠券组合后的价格"""
        current_price = base_price
        description_parts = []

        # 按优惠券类型排序应用（先固定金额，后百分比）
        sorted_coupons = sorted(coupons, key=lambda c: (
            0 if c.discount_type == DiscountType.FIXED else 1
        ))

        for coupon in sorted_coupons:
            original_price = current_price
            if coupon.discount_type == DiscountType.FIXED:
                current_price = max(0, current_price - coupon.discount_value)
                discount_amount = original_price - current_price
                description_parts.append(f"满减券减¥{coupon.discount_value}")
            elif coupon.discount_type == DiscountType.PERCENTAGE:
                discount_amount = current_price * (coupon.discount_value / 100)
                current_price = max(0, current_price - discount_amount)
                description_parts.append(f"折扣券{coupon.discount_value}% off")
            elif coupon.discount_type == DiscountType.CASHBACK:
                # 返现是在购买后返还，不影响支付价格
                description_parts.append(f"返现券¥{coupon.discount_value}")

        description = " + ".join(description_parts) if description_parts else "无优惠"
        return current_price, description

    async def _save_coupon_strategy(self, user_id: int, product_id: int, strategy: Dict):
        """保存优惠券策略"""
        try:
            coupon_strategy = CouponStrategy(
                user_id=user_id,
                product_id=product_id,
                strategy_data={
                    "coupons": [c.id for c in strategy["coupons"]],
                    "final_price": strategy["final_price"],
                    "total_discount": strategy["total_discount"]
                },
                max_discount=strategy["total_discount"]
            )
            self.db.add(coupon_strategy)
            self.db.commit()

        except Exception as e:
            logger.error(f"Error saving coupon strategy: {e}")

    async def create_coupon(self, coupon_data: Dict) -> CouponResponse:
        """创建优惠券"""
        try:
            coupon = Coupon(
                platform=coupon_data["platform"],
                coupon_id=coupon_data["coupon_id"],
                title=coupon_data["title"],
                description=coupon_data.get("description"),
                discount_type=coupon_data["discount_type"],
                discount_value=coupon_data["discount_value"],
                min_purchase_amount=coupon_data.get("min_purchase_amount"),
                start_date=coupon_data.get("start_date"),
                end_date=coupon_data.get("end_date"),
                usage_limit=coupon_data.get("usage_limit"),
                terms=coupon_data.get("terms")
            )
            self.db.add(coupon)
            self.db.commit()
            self.db.refresh(coupon)

            return CouponResponse.from_orm(coupon)

        except Exception as e:
            logger.error(f"Error creating coupon: {e}")
            raise

    async def get_user_coupon_statistics(self, user_id: int) -> Dict:
        """获取用户优惠券统计"""
        try:
            # 获取用户使用的优惠券策略
            strategies = self.db.query(CouponStrategy).filter(
                CouponStrategy.user_id == user_id
            ).all()

            total_savings = sum(s.max_discount for s in strategies)
            total_strategies = len(strategies)

            # 按平台统计
            platform_stats = {}
            for strategy in strategies:
                product = self.db.query(Product).filter(Product.id == strategy.product_id).first()
                if product:
                    platform = product.platform
                    if platform not in platform_stats:
                        platform_stats[platform] = {"count": 0, "savings": 0}
                    platform_stats[platform]["count"] += 1
                    platform_stats[platform]["savings"] += strategy.max_discount

            # 最常用的优惠类型
            if strategies:
                all_coupons = []
                for strategy in strategies:
                    coupon_ids = strategy.strategy_data.get("coupons", [])
                    coupons = self.db.query(Coupon).filter(Coupon.id.in_(coupon_ids)).all()
                    all_coupons.extend(coupons)

                discount_types = {}
                for coupon in all_coupons:
                    discount_type = coupon.discount_type
                    if discount_type not in discount_types:
                        discount_types[discount_type] = 0
                    discount_types[discount_type] += 1

                most_used_type = max(discount_types.items(), key=lambda x: x[1])[0] if discount_types else None
            else:
                most_used_type = None

            return {
                "user_id": user_id,
                "total_strategies": total_strategies,
                "total_savings": total_savings,
                "average_savings_per_strategy": total_savings / total_strategies if total_strategies > 0 else 0,
                "platform_statistics": platform_stats,
                "most_used_discount_type": most_used_type,
                "recent_strategies": [
                    {
                        "product_id": s.product_id,
                        "savings": s.max_discount,
                        "created_at": s.created_at.isoformat()
                    }
                    for s in strategies[-5:]  # 最近5个策略
                ]
            }

        except Exception as e:
            logger.error(f"Error getting user coupon statistics: {e}")
            return {}

    async def get_price_alerts(self, user_id: int, threshold_percent: float = 10.0) -> List[Dict]:
        """获取价格提醒"""
        try:
            # 获取用户关注的商品（基于搜索历史）
            search_history = self.db.query(func.max(SearchHistory.search_query)).filter(
                SearchHistory.user_id == user_id
            ).group_by(SearchHistory.search_query).all()

            alerts = []
            for (query,) in search_history:
                # 搜索相关商品
                search_request = {
                    "query": query,
                    "platforms": [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD],
                    "page": 1,
                    "page_size": 5
                }

                try:
                    results = await self.shopping_service.search_products(search_request)

                    for product in results["products"]:
                        # 检查是否有历史价格数据
                        price_history = self.db.query(PriceHistory).filter(
                            PriceHistory.product_id == product.id
                        ).order_by(PriceHistory.timestamp.desc()).first()

                        if price_history and product.price:
                            price_change = ((product.price - price_history.price) / price_history.price) * 100

                            if abs(price_change) >= threshold_percent:
                                alerts.append({
                                    "product": ProductResponse.from_orm(product),
                                    "previous_price": price_history.price,
                                    "current_price": product.price,
                                    "price_change_percent": price_change,
                                    "alert_type": "price_drop" if price_change < 0 else "price_increase",
                                    "query": query
                                })

                except Exception as e:
                    logger.error(f"Error checking price alerts for query {query}: {e}")
                    continue

            # 按价格变化幅度排序
            alerts.sort(key=lambda x: abs(x["price_change_percent"]), reverse=True)

            return alerts[:10]  # 返回前10个提醒

        except Exception as e:
            logger.error(f"Error getting price alerts: {e}")
            return []

    def _normalize_product_name(self, title: str) -> str:
        """标准化商品名称 - 用于商品分组"""
        if not title:
            return ""
        
        import re
        # 移除常见的修饰词和品牌词（中文和英文）
        stop_words = {
            "官方", "正品", "旗舰店", "专卖店", "特价", "优惠", "包邮", "新品", "热卖",
            "国行", "全国联保", "正品保证", "官方正品",
            "official", "genuine", "original", "authentic", "new", "hot", "sale",
            "京东", "淘宝", "天猫", "拼多多", "jd", "taobao", "tmall", "pdd"
        }
        
        # 统一转换为小写，便于比较
        title_lower = title.lower()
        
        # 提取关键词（支持中英文）
        # 中文字符（排除停用词）
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', title)
        # 英文单词（统一小写）
        english_words = re.findall(r'[a-zA-Z]+', title_lower)
        # 数字规格（如256GB, 512GB等）
        numbers = re.findall(r'\d+\s*[GBMBkm]+', title_lower, re.I)
        
        words = []
        # 添加中文词（排除停用词）
        for word in chinese_words:
            # 排除停用词和过短的词
            if word not in stop_words and len(word) > 1:
                # 排除颜色等可变信息（但保留型号关键信息）
                if word not in ["深空黑色", "原色钛金属", "原色钛", "银色", "铜色", "星宇橙", "汐月蓝", "玄夜黑", "冰羽白"]:
                    words.append(word)
        
        # 添加英文词（统一小写，排除停用词）
        has_apple = False
        has_iphone = False
        for word in english_words:
            if word not in stop_words and len(word) > 2:
                # 统一品牌名称（apple -> apple, iphone -> iphone）
                if word == "apple":
                    has_apple = True
                elif word == "iphone":
                    has_iphone = True
                else:
                    words.append(word)
        
        # 如果有iphone，统一添加apple iphone（即使标题中没有apple）
        if has_iphone:
            words.append("apple")
            words.append("iphone")
        elif has_apple:
            words.append("apple")
        
        # 添加数字规格（统一格式）
        for num in numbers:
            # 统一格式：移除空格，转为小写
            num_clean = num.replace(" ", "").lower()
            words.append(num_clean)
        
        # 如果提取的关键词太少，使用原始标题的关键部分
        if len(words) < 2:
            # 简单分词（按空格或常见分隔符）
            simple_words = re.split(r'[\s\-\|]+', title_lower)
            words.extend([w for w in simple_words[:3] if w and len(w) > 1 and w not in stop_words])
        
        # 排序并去重，确保相同商品名称生成相同的key
        words_unique = []
        seen = set()
        for w in words:
            if w not in seen:
                words_unique.append(w)
                seen.add(w)
        
        # 返回排序后的关键词组合（最多5个）
        words_unique_sorted = sorted(words_unique[:5])
        key = " ".join(words_unique_sorted) if words_unique_sorted else title_lower[:30]
        return key.strip()