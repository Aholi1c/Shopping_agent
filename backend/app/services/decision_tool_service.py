#!/usr/bin/env python3
"""
交互式决策工具服务
提供多目标优化和个性化推荐解释
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging
from collections import defaultdict

from ..models.models import (
    Product, UserDecisionWeights, DecisionRecommendation,
    RecommendationExplanation, UserPreference, User, ProductRisk
)
from ..core.database import get_db
from .llm_service import LLMService
from .price_prediction_service import price_prediction_service
from .risk_detection_service import risk_detection_service

logger = logging.getLogger(__name__)


class DecisionToolService:
    """交互式决策工具服务"""

    def __init__(self):
        self.llm_service = None

        # 默认权重配置
        self.default_weights = {
            "price": 0.25,
            "quality": 0.20,
            "brand": 0.15,
            "functionality": 0.15,
            "appearance": 0.10,
            "logistics": 0.10,
            "service": 0.05
        }

        # 维度描述
        self.dimension_descriptions = {
            "price": "价格因素，包括商品价格、折扣力度、性价比",
            "quality": "质量因素，包括材质、工艺、耐用性",
            "brand": "品牌因素，包括品牌知名度、信誉度",
            "functionality": "功能性，包括功能完整性、实用性",
            "appearance": "外观因素，包括设计、颜色、尺寸",
            "logistics": "物流因素，包括配送速度、运费",
            "service": "服务因素，包括售后服务、客服质量"
        }

    async def create_decision_session(
        self,
        user_id: int,
        product_candidates: List[int],
        context: str = "general"
    ) -> Dict[str, Any]:
        """
        创建决策会话

        Args:
            user_id: 用户ID
            product_candidates: 候选商品ID列表
            context: 决策上下文

        Returns:
            决策会话信息
        """
        db = next(get_db())

        try:
            # 初始化LLM服务
            if not self.llm_service:
                self.llm_service = LLMService()

            # 验证商品存在
            products = db.query(Product).filter(
                Product.id.in_(product_candidates)
            ).all()

            if len(products) != len(product_candidates):
                return {"error": "部分商品不存在"}

            # 获取用户历史权重
            user_weights = await self._get_user_decision_weights(db, user_id, context)

            # 生成会话ID
            session_id = f"decision_{user_id}_{int(datetime.now().timestamp())}"

            # 分析候选商品
            candidate_analysis = await self._analyze_candidates(db, products)

            # 初始推荐结果
            initial_recommendation = await self._generate_recommendation(
                db, user_id, products, user_weights, session_id
            )

            return {
                "session_id": session_id,
                "user_id": user_id,
                "context": context,
                "candidate_count": len(products),
                "product_candidates": candidate_analysis,
                "current_weights": user_weights,
                "initial_recommendation": initial_recommendation,
                "dimension_descriptions": self.dimension_descriptions,
                "suggested_adjustments": await self._suggest_weight_adjustments(db, user_id, context)
            }

        except Exception as e:
            logger.error(f"决策会话创建失败: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def update_weights_and_recommend(
        self,
        user_id: int,
        session_id: str,
        new_weights: Dict[str, float],
        product_candidates: List[int]
    ) -> Dict[str, Any]:
        """
        更新权重并重新推荐

        Args:
            user_id: 用户ID
            session_id: 会话ID
            new_weights: 新的权重配置
            product_candidates: 候选商品ID列表

        Returns:
            更新后的推荐结果
        """
        db = next(get_db())

        try:
            # 验证权重有效性
            if not self._validate_weights(new_weights):
                return {"error": "权重配置无效"}

            # 保存用户权重调整
            await self._save_user_weights(db, user_id, new_weights, session_id)

            # 获取商品信息
            products = db.query(Product).filter(
                Product.id.in_(product_candidates)
            ).all()

            # 生成新的推荐
            new_recommendation = await self._generate_recommendation(
                db, user_id, products, new_weights, session_id
            )

            # 生成权重变化解释
            weight_change_explanation = await self._explain_weight_changes(
                db, user_id, new_weights, session_id
            )

            return {
                "session_id": session_id,
                "updated_weights": new_weights,
                "new_recommendation": new_recommendation,
                "weight_change_explanation": weight_change_explanation,
                "optimization_insights": await self._generate_optimization_insights(new_recommendation)
            }

        except Exception as e:
            logger.error(f"权重更新失败: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def _get_user_decision_weights(
        self,
        db: Session,
        user_id: int,
        context: str
    ) -> Dict[str, float]:
        """获取用户决策权重"""
        try:
            # 查询用户历史权重
            user_weight_records = db.query(UserDecisionWeights).filter(
                UserDecisionWeights.user_id == user_id,
                UserDecisionWeights.decision_context == context,
                UserDecisionWeights.is_active == True
            ).all()

            if user_weight_records:
                weights = {}
                for record in user_weight_records:
                    weights[record.weight_dimension] = record.weight_value
                return weights
            else:
                # 查询用户偏好作为权重参考
                user_preferences = db.query(UserPreference).filter(
                    UserPreference.user_id == user_id
                ).all()

                weights = self.default_weights.copy()

                # 根据用户偏好调整权重
                for pref in user_preferences:
                    if pref.preference_type == "price_sensitivity":
                        weights["price"] = min(0.5, weights["price"] + pref.weight * 0.2)
                    elif pref.preference_type == "quality_focus":
                        weights["quality"] = min(0.5, weights["quality"] + pref.weight * 0.2)
                    elif pref.preference_type == "brand_loyalty":
                        weights["brand"] = min(0.4, weights["brand"] + pref.weight * 0.2)

                return self._normalize_weights(weights)

        except Exception as e:
            logger.error(f"获取用户权重失败: {e}")
            return self.default_weights.copy()

    def _validate_weights(self, weights: Dict[str, float]) -> bool:
        """验证权重配置"""
        if not weights:
            return False

        # 检查权重范围
        for value in weights.values():
            if not (0 <= value <= 1):
                return False

        # 检查总和（应该接近1.0）
        total_weight = sum(weights.values())
        return abs(total_weight - 1.0) < 0.1

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """标准化权重"""
        total = sum(weights.values())
        if total == 0:
            return self.default_weights.copy()

        return {k: v / total for k, v in weights.items()}

    async def _analyze_candidates(self, db: Session, products: List[Product]) -> List[Dict[str, Any]]:
        """分析候选商品"""
        try:
            candidates = []

            for product in products:
                # 获取商品风险信息
                risks = db.query(ProductRisk).filter(
                    ProductRisk.product_id == product.id
                ).all()

                risk_score = 0
                if risks:
                    risk_score = max([self._risk_level_to_score(r.risk_level) for r in risks])

                candidate = {
                    "product_id": product.id,
                    "title": product.title,
                    "price": product.price,
                    "original_price": product.original_price,
                    "rating": product.rating or 0,
                    "review_count": product.review_count or 0,
                    "sales_count": product.sales_count or 0,
                    "platform": product.platform,
                    "category": product.category,
                    "brand": product.brand,
                    "risk_score": risk_score,
                    "dimensions": await self._calculate_product_dimensions(db, product)
                }

                candidates.append(candidate)

            return candidates

        except Exception as e:
            logger.error(f"候选商品分析失败: {e}")
            return []

    async def _calculate_product_dimensions(self, db: Session, product: Product) -> Dict[str, float]:
        """计算商品各维度分数"""
        try:
            dimensions = {}

            # 价格维度 (0-1分，价格越低分数越高)
            price_score = self._calculate_price_score(product)
            dimensions["price"] = price_score

            # 质量维度 (基于评分)
            dimensions["quality"] = (product.rating or 3.0) / 5.0

            # 品牌维度 (基于品牌知名度和评分)
            dimensions["brand"] = await self._calculate_brand_score(db, product)

            # 功能维度 (基于商品描述和评价)
            dimensions["functionality"] = await self._calculate_functionality_score(db, product)

            # 外观维度 (基于评价关键词)
            dimensions["appearance"] = await self._calculate_appearance_score(db, product)

            # 物流维度 (基于平台和配送信息)
            dimensions["logistics"] = self._calculate_logistics_score(product.platform)

            # 服务维度 (基于售后服务信息)
            dimensions["service"] = self._calculate_service_score(product.platform)

            return dimensions

        except Exception as e:
            logger.error(f"商品维度计算失败: {e}")
            return {dim: 0.5 for dim in self.default_weights.keys()}

    def _calculate_price_score(self, product: Product) -> float:
        """计算价格分数"""
        try:
            if product.original_price and product.original_price > 0:
                discount_ratio = 1 - (product.price / product.original_price)
                return min(1.0, 0.5 + discount_ratio)
            else:
                # 基于品类估算价格竞争力
                return 0.5  # 默认中等分数
        except:
            return 0.5

    async def _calculate_brand_score(self, db: Session, product: Product) -> float:
        """计算品牌分数"""
        try:
            if not product.brand:
                return 0.3

            # 查询同品牌其他商品的平均评分
            brand_products = db.query(Product).filter(
                Product.brand == product.brand,
                Product.id != product.id
            ).all()

            if brand_products:
                avg_rating = np.mean([p.rating or 3.0 for p in brand_products])
                return min(1.0, avg_rating / 5.0)
            else:
                return 0.6  # 未知品牌给予中等分数

        except:
            return 0.5

    async def _calculate_functionality_score(self, db: Session, product: Product) -> float:
        """计算功能分数"""
        try:
            # 基于评价中的功能性关键词
            from backend.app.models.models import ProductReview
            reviews = db.query(ProductReview).filter(
                ProductReview.product_id == product.id
            ).limit(20).all()

            functionality_keywords = ["功能", "好用", "实用", "方便", "操作", "性能"]
            positive_count = 0

            for review in reviews:
                review_text = review.review_content.lower()
                if any(keyword in review_text for keyword in functionality_keywords):
                    positive_count += 1

            if reviews:
                return min(1.0, 0.3 + positive_count / len(reviews))
            else:
                return 0.6

        except:
            return 0.5

    async def _calculate_appearance_score(self, db: Session, product: Product) -> float:
        """计算外观分数"""
        try:
            # 基于评价中的外观关键词
            from backend.app.models.models import ProductReview
            reviews = db.query(ProductReview).filter(
                ProductReview.product_id == product.id
            ).limit(20).all()

            appearance_keywords = ["好看", "漂亮", "外观", "设计", "颜色", "尺寸"]
            positive_count = 0

            for review in reviews:
                review_text = review.review_content.lower()
                if any(keyword in review_text for keyword in appearance_keywords):
                    positive_count += 1

            if reviews:
                return min(1.0, 0.3 + positive_count / len(reviews))
            else:
                return 0.6

        except:
            return 0.5

    def _calculate_logistics_score(self, platform: str) -> float:
        """计算物流分数"""
        # 基于平台的物流服务水平
        platform_scores = {
            "jd": 0.9,      # 京东物流
            "taobao": 0.7,  # 淘宝
            "pdd": 0.6,     # 拼多多
            "xiaohongshu": 0.6,
            "douyin": 0.6
        }
        return platform_scores.get(platform, 0.6)

    def _calculate_service_score(self, platform: str) -> float:
        """计算服务分数"""
        # 基于平台的售后服务水平
        platform_scores = {
            "jd": 0.9,
            "taobao": 0.8,
            "pdd": 0.7,
            "xiaohongshu": 0.6,
            "douyin": 0.6
        }
        return platform_scores.get(platform, 0.6)

    def _risk_level_to_score(self, risk_level: str) -> float:
        """将风险等级转换为分数"""
        mapping = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.6,
            "critical": 1.0
        }
        return mapping.get(risk_level, 0.0)

    async def _generate_recommendation(
        self,
        db: Session,
        user_id: int,
        products: List[Product],
        weights: Dict[str, float],
        session_id: str
    ) -> Dict[str, Any]:
        """生成推荐结果"""
        try:
            # 计算加权分数
            product_scores = []

            for product in products:
                dimensions = await self._calculate_product_dimensions(db, product)

                # 计算加权总分
                total_score = 0
                dimension_scores = {}

                for dimension, weight in weights.items():
                    dimension_score = dimensions.get(dimension, 0.5)
                    weighted_score = dimension_score * weight
                    dimension_scores[dimension] = {
                        "raw_score": dimension_score,
                        "weight": weight,
                        "weighted_score": weighted_score
                    }
                    total_score += weighted_score

                # 考虑风险因素
                risks = db.query(ProductRisk).filter(
                    ProductRisk.product_id == product.id
                ).all()

                risk_penalty = 0
                if risks:
                    max_risk_score = max([self._risk_level_to_score(r.risk_level) for r in risks])
                    risk_penalty = max_risk_score * 0.2  # 风险惩罚最多20%

                final_score = total_score * (1 - risk_penalty)

                product_scores.append({
                    "product": product,
                    "total_score": final_score,
                    "dimension_scores": dimension_scores,
                    "risk_penalty": risk_penalty,
                    "risks": risks
                })

            # 排序
            product_scores.sort(key=lambda x: x["total_score"], reverse=True)

            # 生成排名和解释
            ranked_products = []
            for rank, score_data in enumerate(product_scores, 1):
                product = score_data["product"]
                ranked_products.append({
                    "rank": rank,
                    "product_id": product.id,
                    "title": product.title,
                    "price": product.price,
                    "total_score": score_data["total_score"],
                    "dimension_scores": score_data["dimension_scores"],
                    "risk_penalty": score_data["risk_penalty"],
                    "risks": len(score_data["risks"])
                })

            # 生成商品对比解释
            comparisons = await self._generate_product_comparisons(
                db, ranked_products[:3], weights
            )

            # 保存推荐结果
            await self._save_recommendation_result(
                db, user_id, session_id, ranked_products, weights
            )

            return {
                "ranked_products": ranked_products,
                "top_recommendation": ranked_products[0] if ranked_products else None,
                "comparisons": comparisons,
                "weight_configuration": weights,
                "optimization_method": "weighted_scoring"
            }

        except Exception as e:
            logger.error(f"推荐生成失败: {e}")
            return {"error": str(e)}

    async def _generate_product_comparisons(
        self,
        db: Session,
        top_products: List[Dict[str, Any]],
        weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """生成商品对比解释"""
        try:
            comparisons = []

            for i in range(len(top_products) - 1):
                product_a = top_products[i]
                product_b = top_products[i + 1]

                comparison = {
                    "product_a": {
                        "id": product_a["product_id"],
                        "title": product_a["title"],
                        "score": product_a["total_score"]
                    },
                    "product_b": {
                        "id": product_b["product_id"],
                        "title": product_b["title"],
                        "score": product_b["total_score"]
                    },
                    "score_difference": product_a["total_score"] - product_b["total_score"],
                    "dimension_comparisons": []
                }

                # 对比各个维度
                for dimension, weight in weights.items():
                    a_score = product_a["dimension_scores"][dimension]["raw_score"]
                    b_score = product_b["dimension_scores"][dimension]["raw_score"]

                    if abs(a_score - b_score) > 0.1:  # 差异显著
                        comparison["dimension_comparisons"].append({
                            "dimension": dimension,
                            "product_a_score": a_score,
                            "product_b_score": b_score,
                            "difference": a_score - b_score,
                            "advantage": "product_a" if a_score > b_score else "product_b",
                            "weight": weight
                        })

                comparisons.append(comparison)

            return comparisons

        except Exception as e:
            logger.error(f"商品对比生成失败: {e}")
            return []

    async def _save_recommendation_result(
        self,
        db: Session,
        user_id: int,
        session_id: str,
        ranked_products: List[Dict[str, Any]],
        weights: Dict[str, float]
    ):
        """保存推荐结果"""
        try:
            recommendation = DecisionRecommendation(
                user_id=user_id,
                session_id=session_id,
                product_candidates=[p["product_id"] for p in ranked_products],
                user_weights=weights,
                recommendation_results={
                    "ranked_products": ranked_products,
                    "generated_at": datetime.now().isoformat()
                },
                optimization_algorithm="weighted_multi_objective",
                confidence_score=0.8
            )

            db.add(recommendation)
            db.commit()
            db.refresh(recommendation)

            # 生成详细解释
            await self._generate_detailed_explanations(db, recommendation, ranked_products, weights)

        except Exception as e:
            logger.error(f"推荐结果保存失败: {e}")
            db.rollback()

    async def _generate_detailed_explanations(
        self,
        db: Session,
        recommendation: DecisionRecommendation,
        ranked_products: List[Dict[str, Any]],
        weights: Dict[str, float]
    ):
        """生成详细解释"""
        try:
            # 初始化LLM服务
            if not self.llm_service:
                self.llm_service = LLMService()

            # 为前两个商品生成详细对比解释
            if len(ranked_products) >= 2:
                product_a = ranked_products[0]
                product_b = ranked_products[1]

                # 构建解释提示
                explanation_prompt = f"""
                请为以下两个商品生成对比解释：

                商品A：{product_a['title']}
                评分：{product_a['total_score']:.3f}
                价格：¥{product_a['price']}

                商品B：{product_b['title']}
                评分：{product_b['total_score']:.3f}
                价格：¥{product_b['price']}

                用户权重配置：
                {chr(10).join([f"- {dim}: {weight}" for dim, weight in weights.items()])}

                主要差异维度：
                {chr(10).join([
                    f"- {dim}: A({product_a['dimension_scores'][dim]['raw_score']:.2f}) vs B({product_b['dimension_scores'][dim]['raw_score']:.2f})"
                    for dim in weights.keys()
                    if abs(product_a['dimension_scores'][dim]['raw_score'] - product_b['dimension_scores'][dim]['raw_score']) > 0.1
                ])}

                请生成自然语言解释，说明为什么商品A比商品B更适合当前用户：
                """

                # 调用LLM生成解释
                llm_explanation = await self.llm_service.generate_text(explanation_prompt)

                # 保存解释
                explanation = RecommendationExplanation(
                    recommendation_id=recommendation.id,
                    product_a_id=product_a["product_id"],
                    product_b_id=product_b["product_id"],
                    comparison_dimension="overall",
                    advantage_reason="基于用户权重的综合评分更高",
                    quantitive_difference=product_a["total_score"] - product_b["total_score"],
                    confidence_score=0.8,
                    natural_language_explanation=llm_explanation
                )

                db.add(explanation)
                db.commit()

        except Exception as e:
            logger.error(f"详细解释生成失败: {e}")

    async def _save_user_weights(
        self,
        db: Session,
        user_id: int,
        weights: Dict[str, float],
        session_id: str
    ):
        """保存用户权重"""
        try:
            # 清理旧的同上下文权重
            context = session_id.split("_")[-1]  # 从session_id提取context
            db.query(UserDecisionWeights).filter(
                UserDecisionWeights.user_id == user_id,
                UserDecisionWeights.decision_context == context
            ).update({"is_active": False})

            # 保存新权重
            for dimension, weight in weights.items():
                user_weight = UserDecisionWeights(
                    user_id=user_id,
                    decision_context=context,
                    weight_dimension=dimension,
                    weight_value=weight,
                    priority_level=list(weights.keys()).index(dimension) + 1
                )
                db.add(user_weight)

            db.commit()

        except Exception as e:
            logger.error(f"用户权重保存失败: {e}")
            db.rollback()

    async def _explain_weight_changes(
        self,
        db: Session,
        user_id: int,
        new_weights: Dict[str, float],
        session_id: str
    ) -> List[str]:
        """解释权重变化影响"""
        try:
            # 获取之前的权重
            context = session_id.split("_")[-1]
            old_weights = await self._get_user_decision_weights(db, user_id, context)

            explanations = []

            # 分析主要变化的维度
            changes = []
            for dimension in new_weights.keys():
                old_weight = old_weights.get(dimension, self.default_weights.get(dimension, 0))
                new_weight = new_weights[dimension]
                change = new_weight - old_weight

                if abs(change) > 0.05:  # 变化超过5%
                    changes.append({
                        "dimension": dimension,
                        "old_weight": old_weight,
                        "new_weight": new_weight,
                        "change": change
                    })

            # 按变化幅度排序
            changes.sort(key=lambda x: abs(x["change"]), reverse=True)

            # 生成解释
            for change in changes[:3]:  # 最多解释3个主要变化
                dimension = change["dimension"]
                change_amount = change["change"]
                direction = "增加" if change_amount > 0 else "减少"

                explanation = f"{self.dimension_descriptions[dimension]}的权重{direction}了{abs(change_amount):.1%}"
                explanations.append(explanation)

            return explanations

        except Exception as e:
            logger.error(f"权重变化解释失败: {e}")
            return []

    async def _suggest_weight_adjustments(
        self,
        db: Session,
        user_id: int,
        context: str
    ) -> List[Dict[str, Any]]:
        """建议权重调整"""
        try:
            suggestions = []

            # 基于用户历史行为建议
            user_preferences = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).all()

            for pref in user_preferences:
                if pref.preference_type == "price_sensitivity" and pref.weight > 0.7:
                    suggestions.append({
                        "dimension": "price",
                        "current_weight": 0.25,
                        "suggested_weight": 0.35,
                        "reason": "根据您的购买历史，您对价格比较敏感"
                    })
                elif pref.preference_type == "quality_focus" and pref.weight > 0.7:
                    suggestions.append({
                        "dimension": "quality",
                        "current_weight": 0.20,
                        "suggested_weight": 0.30,
                        "reason": "您过去比较重视商品质量"
                    })

            # 基于决策上下文建议
            if context == "gift":
                suggestions.append({
                    "dimension": "appearance",
                    "current_weight": 0.10,
                    "suggested_weight": 0.20,
                    "reason": "送礼时外观因素更重要"
                })
            elif context == "daily_use":
                suggestions.append({
                    "dimension": "functionality",
                    "current_weight": 0.15,
                    "suggested_weight": 0.25,
                    "reason": "日常使用建议更注重实用性"
                })

            return suggestions[:3]  # 返回前3个建议

        except Exception as e:
            logger.error(f"权重调整建议失败: {e}")
            return []

    async def _generate_optimization_insights(self, recommendation: Dict[str, Any]) -> List[str]:
        """生成优化洞察"""
        try:
            insights = []

            ranked_products = recommendation.get("ranked_products", [])
            if not ranked_products:
                return insights

            # 分析分数分布
            scores = [p["total_score"] for p in ranked_products]
            score_std = np.std(scores)
            score_range = max(scores) - min(scores)

            if score_std < 0.05:
                insights.append("各商品综合评分相近，建议重点考虑您最关注的维度")
            elif score_range > 0.3:
                insights.append("商品间差异明显，推荐结果相对可靠")

            # 分析价格敏感性
            top_product = ranked_products[0]
            if top_product["dimension_scores"]["price"]["raw_score"] > 0.8:
                insights.append("推荐商品具有很好的价格优势")

            # 分析风险影响
            if top_product["risk_penalty"] > 0.1:
                insights.append("推荐商品存在一定风险，建议仔细查看风险详情")

            return insights

        except Exception as e:
            logger.error(f"优化洞察生成失败: {e}")
            return []

    async def get_decision_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取决策历史"""
        db = next(get_db())

        try:
            decisions = db.query(DecisionRecommendation).filter(
                DecisionRecommendation.user_id == user_id
            ).order_by(desc(DecisionRecommendation.created_at)).limit(limit).all()

            decision_history = []

            for decision in decisions:
                try:
                    results = json.loads(decision.recommendation_results)
                    top_product = results.get("ranked_products", [{}])[0]

                    decision_history.append({
                        "session_id": decision.session_id,
                        "created_at": decision.created_at.isoformat(),
                        "product_count": len(decision.product_candidates),
                        "top_recommendation": top_product.get("title", ""),
                        "confidence": decision.confidence_score,
                        "user_feedback": decision.user_feedback
                    })
                except:
                    continue

            return {
                "total_decisions": len(decision_history),
                "decision_history": decision_history
            }

        except Exception as e:
            logger.error(f"决策历史获取失败: {e}")
            return {"error": str(e)}
        finally:
            db.close()


# 创建服务实例
decision_tool_service = DecisionToolService()