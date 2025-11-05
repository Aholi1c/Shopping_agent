"""
智能优惠券和促销发现服务
"""

import asyncio
import aiohttp
import json
import hashlib
import re
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from ..models.ecommerce_models import (
    Product, Coupon, CouponProduct, CouponStrategy, UserPreference
)
from ..services.llm_service import LLMService
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)

class CouponService:
    def __init__(self, db: Session, llm_service: LLMService, rag_service: RAGService):
        self.db = db
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def discover_coupons(self, user_id: str, product_ids: List[str] = None,
                              categories: List[str] = None, brands: List[str] = None) -> Dict:
        """智能发现优惠券和促销信息"""
        discovery_result = {
            "user_id": user_id,
            "discovery_time": datetime.now().isoformat(),
            "total_coupons": 0,
            "applicable_coupons": [],
            "potential_savings": 0.0,
            "best_deals": [],
            "recommendations": []
        }

        # 获取用户偏好
        user_preferences = await self._get_user_coupon_preferences(user_id)

        # 构建搜索条件
        search_criteria = await self._build_search_criteria(
            product_ids, categories, brands, user_preferences
        )

        # 搜索优惠券
        coupons = await self._search_coupons(search_criteria)

        # 分析优惠券适用性
        applicable_coupons = await self._analyze_coupon_applicability(coupons, search_criteria)

        # 计算潜在节省
        total_savings = sum(c['estimated_savings'] for c in applicable_coupons)

        # 生成最佳推荐
        best_deals = await self._generate_best_deals(applicable_coupons, search_criteria)

        # 生成个性化推荐
        recommendations = await self._generate_coupon_recommendations(
            applicable_coupons, user_preferences, search_criteria
        )

        discovery_result.update({
            "total_coupons": len(coupons),
            "applicable_coupons": applicable_coupons,
            "potential_savings": total_savings,
            "best_deals": best_deals,
            "recommendations": recommendations
        })

        # 记录发现历史
        await self._record_discovery_history(user_id, discovery_result)

        return discovery_result

    async def _get_user_coupon_preferences(self, user_id: str) -> Dict:
        """获取用户优惠券偏好"""
        preferences = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

        if not preferences:
            return {
                "preferred_brands": [],
                "preferred_categories": [],
                "price_sensitivity": "medium",
                "coupon_usage_frequency": "occasional"
            }

        return {
            "preferred_brands": preferences.preferred_brands or [],
            "preferred_categories": preferences.preferred_categories or [],
            "price_range": {
                "min": preferences.price_range_min,
                "max": preferences.price_range_max
            },
            "coupon_usage_patterns": preferences.meta_data.get('coupon_patterns', {}) if preferences.meta_data else {}
        }

    async def _build_search_criteria(self, product_ids: List[str], categories: List[str],
                                   brands: List[str], user_preferences: Dict) -> Dict:
        """构建搜索条件"""
        criteria = {
            "product_ids": product_ids or [],
            "categories": categories or user_preferences.get("preferred_brands", []),
            "brands": brands or user_preferences.get("preferred_brands", []),
            "price_range": user_preferences.get("price_range", {}),
            "usage_patterns": user_preferences.get("coupon_usage_patterns", {})
        }

        # 扩展搜索范围
        if criteria["categories"]:
            # 搜索相关类别
            related_categories = await self._get_related_categories(criteria["categories"])
            criteria["expanded_categories"] = related_categories

        return criteria

    async def _get_related_categories(self, categories: List[str]) -> List[str]:
        """获取相关类别"""
        # 使用RAG搜索相关类别
        related = []
        for category in categories:
            try:
                results = await self.rag_service.search_knowledge(
                    f"{category} 相关类别", k=5
                )
                for result in results:
                    content = result['content']
                    # 简单的类别提取
                    category_matches = re.findall(r'类别[：:]\s*([^\n,]+)', content)
                    related.extend(category_matches)
            except:
                pass

        return list(set(related))

    async def _search_coupons(self, criteria: Dict) -> List[Dict]:
        """搜索优惠券"""
        coupons = []

        # 1. 数据库中的优惠券
        db_coupons = await self._search_database_coupons(criteria)
        coupons.extend(db_coupons)

        # 2. 网络优惠券抓取（模拟）
        web_coupons = await self._scrape_web_coupons(criteria)
        coupons.extend(web_coupons)

        # 3. AI生成的优惠券策略
        ai_coupons = await self._generate_ai_coupons(criteria)
        coupons.extend(ai_coupons)

        # 去重
        unique_coupons = await self._deduplicate_coupons(coupons)

        return unique_coupons

    async def _search_database_coupons(self, criteria: Dict) -> List[Dict]:
        """搜索数据库中的优惠券"""
        query = self.db.query(Coupon).filter(
            and_(
                Coupon.is_active == True,
                Coupon.end_date >= datetime.now()
            )
        )

        # 应用过滤条件
        if criteria.get("categories"):
            query = query.filter(Coupon.applicable_categories.overlap(criteria["categories"]))

        if criteria.get("brands"):
            query = query.filter(Coupon.applicable_brands.overlap(criteria["brands"]))

        if criteria.get("price_range"):
            min_price = criteria["price_range"].get("min")
            max_price = criteria["price_range"].get("max")
            if min_price:
                query = query.filter(Coupon.min_order_amount >= min_price)
            if max_price:
                query = query.filter(Coupon.max_order_amount <= max_price)

        db_coupons = query.order_by(Coupon.discount_value.desc()).limit(20).all()

        return [self._coupon_to_dict(coupon) for coupon in db_coupons]

    async def _scrape_web_coupons(self, criteria: Dict) -> List[Dict]:
        """抓取网络优惠券（模拟实现）"""
        # 这里可以实现真实的优惠券抓取逻辑
        # 目前返回模拟数据

        web_coupons = []
        platforms = ["京东", "淘宝", "拼多多", "苏宁"]

        for platform in platforms:
            # 模拟抓取延迟
            await asyncio.sleep(0.1)

            # 生成模拟优惠券
            coupon = {
                "id": f"web_{platform}_{hash(str(criteria)) % 1000}",
                "platform": platform,
                "code": f"{platform.upper()}_{hash(str(criteria)) % 10000}",
                "title": f"{platform}专属优惠券",
                "description": f"适用于{criteria.get('categories', ['全品类'])}商品",
                "discount_type": "percentage",
                "discount_value": 5.0 + (hash(platform) % 10),  # 5-15%折扣
                "min_order_amount": 99.0,
                "max_discount": 50.0,
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "usage_limit": 1000,
                "remaining_count": 500,
                "applicable_categories": criteria.get("categories", []),
                "applicable_brands": criteria.get("brands", []),
                "source": "web_scraping",
                "priority": 2
            }
            web_coupons.append(coupon)

        return web_coupons

    async def _generate_ai_coupons(self, criteria: Dict) -> List[Dict]:
        """生成AI优惠券策略"""
        # 基于用户行为和购买历史生成个性化优惠券
        ai_coupons = []

        prompt = f"""
        基于以下用户搜索条件，生成个性化的优惠券策略：

        搜索条件: {json.dumps(criteria, ensure_ascii=False)}

        请生成3个优惠券策略，每个策略包含：
        1. 优惠类型（固定金额或百分比）
        2. 优惠力度
        3. 使用条件
        4. 适用范围
        5. 有效期

        返回JSON格式数组。
        """

        try:
            response = await self.llm_service.generate_response(prompt)
            ai_strategies = json.loads(response)

            for i, strategy in enumerate(ai_strategies):
                coupon = {
                    "id": f"ai_generated_{i}",
                    "platform": "AI推荐",
                    "code": f"AI_SAVE_{i}",
                    "title": strategy.get("title", f"AI智能优惠券{i+1}"),
                    "description": strategy.get("description", "基于您的购物习惯生成的专属优惠"),
                    "discount_type": strategy.get("discount_type", "percentage"),
                    "discount_value": strategy.get("discount_value", 10.0),
                    "min_order_amount": strategy.get("min_order_amount", 99.0),
                    "max_discount": strategy.get("max_discount", 100.0),
                    "start_date": datetime.now().isoformat(),
                    "end_date": (datetime.now() + timedelta(days=3)).isoformat(),
                    "usage_limit": 1,
                    "remaining_count": 1,
                    "applicable_categories": criteria.get("categories", []),
                    "applicable_brands": criteria.get("brands", []),
                    "source": "ai_generated",
                    "priority": 1,
                    "personalization_score": 0.9
                }
                ai_coupons.append(coupon)

        except Exception as e:
            logger.error(f"Error generating AI coupons: {e}")

        return ai_coupons

    def _coupon_to_dict(self, coupon: Coupon) -> Dict:
        """转换优惠券为字典"""
        return {
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
            "applicable_brands": coupon.applicable_brands or [],
            "source": "database",
            "priority": 3
        }

    async def _deduplicate_coupons(self, coupons: List[Dict]) -> List[Dict]:
        """去重优惠券"""
        seen = set()
        unique_coupons = []

        for coupon in coupons:
            # 创建唯一标识
            signature = f"{coupon['platform']}_{coupon['discount_value']}_{coupon['min_order_amount']}"
            if signature not in seen:
                seen.add(signature)
                unique_coupons.append(coupon)

        return unique_coupons

    async def _analyze_coupon_applicability(self, coupons: List[Dict], criteria: Dict) -> List[Dict]:
        """分析优惠券适用性"""
        applicable = []

        for coupon in coupons:
            # 计算适用性分数
            applicability_score = await self._calculate_applicability_score(coupon, criteria)

            # 估算节省金额
            estimated_savings = await self._estimate_savings(coupon, criteria)

            if applicability_score > 0.3:  # 适用性阈值
                coupon_copy = coupon.copy()
                coupon_copy.update({
                    "applicability_score": applicability_score,
                    "estimated_savings": estimated_savings,
                    "matching_categories": self._get_matching_categories(coupon, criteria),
                    "matching_brands": self._get_matching_brands(coupon, criteria)
                })
                applicable.append(coupon_copy)

        # 按适用性分数排序
        applicable.sort(key=lambda x: x['applicability_score'], reverse=True)

        return applicable

    async def _calculate_applicability_score(self, coupon: Dict, criteria: Dict) -> float:
        """计算适用性分数"""
        score = 0.0

        # 类别匹配
        if criteria.get("categories") and coupon.get("applicable_categories"):
            matching_categories = set(criteria["categories"]) & set(coupon["applicable_categories"])
            if matching_categories:
                score += 0.4

        # 品牌匹配
        if criteria.get("brands") and coupon.get("applicable_brands"):
            matching_brands = set(criteria["brands"]) & set(coupon["applicable_brands"])
            if matching_brands:
                score += 0.3

        # 价格范围匹配
        if criteria.get("price_range"):
            min_price = criteria["price_range"].get("min")
            max_price = criteria["price_range"].get("max")
            coupon_min = coupon.get("min_order_amount", 0)

            if min_price and coupon_min <= min_price * 1.5:
                score += 0.2
            elif max_price and coupon_min <= max_price:
                score += 0.2

        # 时间紧迫性
        end_date = datetime.fromisoformat(coupon["end_date"])
        days_left = (end_date - datetime.now()).days
        if days_left <= 3:
            score += 0.1

        # 来源优先级
        source_priority = {
            "ai_generated": 1.0,
            "database": 0.8,
            "web_scraping": 0.6
        }
        score *= source_priority.get(coupon.get("source", "web_scraping"), 0.6)

        return min(1.0, score)

    async def _estimate_savings(self, coupon: Dict, criteria: Dict) -> float:
        """估算节省金额"""
        # 基于搜索条件估算平均订单金额
        estimated_order_amount = self._estimate_average_order_amount(criteria)

        if coupon["discount_type"] == "fixed":
            return min(coupon["discount_value"], coupon.get("max_discount", float('inf')))
        else:  # percentage
            discount_amount = estimated_order_amount * coupon["discount_value"] / 100
            return min(discount_amount, coupon.get("max_discount", float('inf')))

    def _estimate_average_order_amount(self, criteria: Dict) -> float:
        """估算平均订单金额"""
        if criteria.get("price_range"):
            price_range = criteria["price_range"]
            return (price_range.get("min", 0) + price_range.get("max", 1000)) / 2
        else:
            return 500.0  # 默认估算

    def _get_matching_categories(self, coupon: Dict, criteria: Dict) -> List[str]:
        """获取匹配的类别"""
        if not criteria.get("categories") or not coupon.get("applicable_categories"):
            return []

        return list(set(criteria["categories"]) & set(coupon["applicable_categories"]))

    def _get_matching_brands(self, coupon: Dict, criteria: Dict) -> List[str]:
        """获取匹配的品牌"""
        if not criteria.get("brands") or not coupon.get("applicable_brands"):
            return []

        return list(set(criteria["brands"]) & set(coupon["applicable_brands"]))

    async def _generate_best_deals(self, coupons: List[Dict], criteria: Dict) -> List[Dict]:
        """生成最佳推荐"""
        best_deals = []

        # 按性价比排序
        for coupon in coupons[:5]:  # 前5个最适用的
            value_score = coupon["estimated_savings"] / max(coupon.get("min_order_amount", 1), 1)

            deal = {
                "coupon": coupon,
                "value_score": value_score,
                "reasoning": await self._generate_deal_reasoning(coupon, criteria),
                "usage_scenario": await self._suggest_usage_scenario(coupon)
            }
            best_deals.append(deal)

        # 按价值分数排序
        best_deals.sort(key=lambda x: x['value_score'], reverse=True)

        return best_deals

    async def _generate_deal_reasoning(self, coupon: Dict, criteria: Dict) -> str:
        """生成推荐理由"""
        reasons = []

        if coupon["estimated_savings"] > 50:
            reasons.append(f"可节省¥{coupon['estimated_savings']:.2f}，优惠力度大")

        if coupon["applicability_score"] > 0.8:
            reasons.append("高度匹配您的需求")

        days_left = (datetime.fromisoformat(coupon["end_date"]) - datetime.now()).days
        if days_left <= 3:
            reasons.append("即将过期，建议尽快使用")

        if coupon.get("personalization_score", 0) > 0.8:
            reasons.append("AI为您量身定制的专属优惠")

        return "；".join(reasons) if reasons else "推荐使用此优惠券"

    async def _suggest_usage_scenario(self, coupon: Dict) -> str:
        """建议使用场景"""
        min_amount = coupon.get("min_order_amount", 0)

        if min_amount >= 500:
            return "适合大额购物时使用"
        elif min_amount >= 200:
            return "适合中等金额购物使用"
        else:
            return "适合小额购物凑单使用"

    async def _generate_coupon_recommendations(self, coupons: List[Dict], preferences: Dict,
                                             criteria: Dict) -> List[Dict]:
        """生成优惠券推荐"""
        recommendations = []

        # 1. 即时可用推荐
        immediate_coupons = [c for c in coupons if c.get("applicability_score", 0) > 0.7]
        if immediate_coupons:
            recommendations.append({
                "type": "immediate",
                "title": "立即可用优惠券",
                "coupons": immediate_coupons[:3],
                "priority": 1
            })

        # 2. 高价值推荐
        high_value_coupons = sorted(coupons, key=lambda x: x.get("estimated_savings", 0), reverse=True)[:3]
        if high_value_coupons:
            recommendations.append({
                "type": "high_value",
                "title": "高价值优惠券",
                "coupons": high_value_coupons,
                "priority": 2
            })

        # 3. 紧急使用推荐
        urgent_coupons = [c for c in coupons if (datetime.fromisoformat(c["end_date"]) - datetime.now()).days <= 3]
        if urgent_coupons:
            recommendations.append({
                "type": "urgent",
                "title": "即将过期优惠券",
                "coupons": urgent_coupons,
                "priority": 3
            })

        # 4. 个性化推荐
        personalized_coupons = [c for c in coupons if c.get("personalization_score", 0) > 0.8]
        if personalized_coupons:
            recommendations.append({
                "type": "personalized",
                "title": "为您专属推荐",
                "coupons": personalized_coupons,
                "priority": 4
            })

        return recommendations

    async def _record_discovery_history(self, user_id: str, discovery_result: Dict):
        """记录发现历史"""
        # 这里可以实现历史记录功能
        logger.info(f"Recorded coupon discovery for user {user_id}: {len(discovery_result['applicable_coupons'])} coupons found")

    async def get_coupon_strategies(self, user_id: str, strategy_type: str = "all") -> Dict:
        """获取优惠券策略"""
        strategies = {
            "user_id": user_id,
            "strategies": [],
            "recommendations": []
        }

        # 获取用户行为模式
        user_patterns = await self._analyze_user_coupon_patterns(user_id)

        # 生成策略建议
        if strategy_type in ["all", "saving"]:
            saving_strategy = await self._generate_saving_strategy(user_patterns)
            strategies["strategies"].append(saving_strategy)

        if strategy_type in ["all", "timing"]:
            timing_strategy = await self._generate_timing_strategy(user_patterns)
            strategies["strategies"].append(timing_strategy)

        if strategy_type in ["all", "stacking"]:
            stacking_strategy = await self._generate_stacking_strategy(user_patterns)
            strategies["strategies"].append(stacking_strategy)

        return strategies

    async def _analyze_user_coupon_patterns(self, user_id: str) -> Dict:
        """分析用户优惠券使用模式"""
        # 这里可以实现用户行为分析
        return {
            "usage_frequency": "medium",
            "preferred_discount_type": "percentage",
            "average_savings": 25.0,
            "favorite_categories": ["电子产品", "服装"],
            "coupon_usage_efficiency": 0.75
        }

    async def _generate_saving_strategy(self, patterns: Dict) -> Dict:
        """生成省钱策略"""
        return {
            "type": "saving",
            "title": "最大化省钱策略",
            "description": "结合多种优惠券和促销活动，实现最大化的省钱效果",
            "tips": [
                "优先使用高折扣率的优惠券",
                "关注平台大促活动",
                "合理搭配使用优惠券"
            ],
            "expected_savings": "15-30%"
        }

    async def _generate_timing_strategy(self, patterns: Dict) -> Dict:
        """生成使用时机策略"""
        return {
            "type": "timing",
            "title": "最佳使用时机策略",
            "description": "在合适的时机使用优惠券，获得最大价值",
            "tips": [
                "关注商品价格波动",
                "在促销期间使用",
                "设置价格提醒"
            ],
            "expected_savings": "10-20%"
        }

    async def _generate_stacking_strategy(self, patterns: Dict) -> Dict:
        """生成叠加使用策略"""
        return {
            "type": "stacking",
            "title": "优惠券叠加策略",
            "description": "合理叠加使用多种优惠券和优惠",
            "tips": [
                "了解平台叠加规则",
                "先使用大额优惠券",
                "配合平台优惠活动"
            ],
            "expected_savings": "20-40%"
        }

    async def validate_coupon(self, coupon_code: str, user_id: str,
                             cart_items: List[Dict]) -> Dict:
        """验证优惠券可用性"""
        validation_result = {
            "is_valid": False,
            "message": "",
            "discount_amount": 0.0,
            "final_price": 0.0
        }

        # 查找优惠券
        coupon = self.db.query(Coupon).filter(
            and_(
                Coupon.code == coupon_code,
                Coupon.is_active == True,
                Coupon.end_date >= datetime.now()
            )
        ).first()

        if not coupon:
            validation_result["message"] = "优惠券不存在或已过期"
            return validation_result

        # 计算购物车总额
        cart_total = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_items)

        # 检查最低消费要求
        if cart_total < coupon.min_order_amount:
            validation_result["message"] = f"未达到最低消费金额¥{coupon.min_order_amount}"
            return validation_result

        # 检查使用限制
        if coupon.remaining_count <= 0:
            validation_result["message"] = "优惠券已用完"
            return validation_result

        # 计算折扣金额
        if coupon.discount_type == "fixed":
            discount_amount = coupon.discount_value
        else:
            discount_amount = cart_total * coupon.discount_value / 100

        # 应用最大折扣限制
        if coupon.max_discount:
            discount_amount = min(discount_amount, coupon.max_discount)

        validation_result.update({
            "is_valid": True,
            "message": "优惠券可用",
            "discount_amount": discount_amount,
            "final_price": cart_total - discount_amount
        })

        return validation_result