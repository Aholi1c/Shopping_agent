#!/usr/bin/env python3
"""
商品风险识别服务
自动识别商品潜在风险，提供规避建议
"""

import json
import re
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from ..models.models import (
    Product, ProductRisk, RiskKeywordLibrary, ComplaintRecord,
    ProductReview, User
)
from ..core.database import get_db
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class RiskDetectionService:
    """商品风险识别服务"""

    def __init__(self, db: Optional[Session] = None, llm_service: Optional[LLMService] = None):
        self.db = db
        self.llm_service = llm_service

        # 风险关键词库初始化
        self.risk_keywords = {
            "fake_product": {
                "keywords": ["翻新", "二手", "仿冒", "假货", "高仿", "A货", "山寨", "水货"],
                "patterns": [r"翻新.*机", r"二手.*新品", r"仿.*正品"],
                "severity": 0.9
            },
            "quality_issue": {
                "keywords": ["质量差", "易坏", "故障", "问题", "缺陷", "瑕疵", "不耐用"],
                "patterns": [r"用.*就坏", r"质量.*不行", r"经常.*故障"],
                "severity": 0.7
            },
            "misleading_advertising": {
                "keywords": ["虚假宣传", "夸大", "不符", "欺骗", "误导", "名不副实"],
                "patterns": [r"宣传.*但.*", r"实际.*与.*不符", r"图片.*与实物"],
                "severity": 0.6
            },
            "service_problem": {
                "keywords": ["售后差", "客服差", "推诿", "不退换", "不理睬", "态度差"],
                "patterns": [r"售后.*差", r"客服.*不理", r"不给.*退换"],
                "severity": 0.5
            },
            "safety_risk": {
                "keywords": ["安全隐患", "危险", "爆炸", "漏电", "过热", "有害物质"],
                "patterns": [r".*危险", r".*爆炸", r"漏电.*风险"],
                "severity": 1.0
            }
        }

        # 材质风险关键词
        self.material_risks = {
            "纯棉": ["起球", "缩水", "褪色", "起皱", "不透气"],
            "真皮": ["人造革", "PU皮", "假皮", "塑料味", "开裂"],
            "实木": ["板材", "贴皮", "密度板", "胶合板", "甲醛"],
            "不锈钢": ["生锈", "掉漆", "薄", "轻", "磁性"],
            "陶瓷": ["塑料", "树脂", "易碎", "裂痕", "不平整"]
        }

    async def analyze_product_risks(self, product_id: int) -> Dict[str, Any]:
        """
        分析商品风险

        Args:
            product_id: 商品ID

        Returns:
            风险分析结果
        """
        db = next(get_db())

        try:
            # 获取商品信息
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"error": "商品不存在"}

            # 初始化LLM服务
            if not self.llm_service:
                self.llm_service = LLMService()

            # 多维度风险分析
            risk_analyses = []

            # 1. 投诉分析
            complaint_risks = await self._analyze_complaints(db, product_id)
            if complaint_risks:
                risk_analyses.extend(complaint_risks)

            # 2. 评价分析
            review_risks = await self._analyze_reviews(db, product_id)
            if review_risks:
                risk_analyses.extend(review_risks)

            # 3. 商品描述风险分析
            description_risks = await self._analyze_product_description(db, product)
            if description_risks:
                risk_analyses.extend(description_risks)

            # 4. LLM深度分析
            llm_risks = await self._llm_risk_analysis(db, product)
            if llm_risks:
                risk_analyses.extend(llm_risks)

            # 综合风险评估
            overall_risk = self._calculate_overall_risk(risk_analyses)

            # 生成风险报告
            risk_report = {
                "product_id": product_id,
                "product_title": product.title,
                "overall_risk_level": overall_risk["risk_level"],
                "overall_confidence": overall_risk["confidence"],
                "risk_count": len(risk_analyses),
                "risk_categories": list(set([risk["risk_type"] for risk in risk_analyses])),
                "detailed_risks": risk_analyses,
                "mitigation_suggestions": await self._generate_mitigation_suggestions(risk_analyses),
                "alternative_recommendations": await self._recommend_alternatives(db, product, risk_analyses),
                "analysis_timestamp": datetime.now().isoformat()
            }

            # 保存风险分析结果
            await self._save_risk_analysis(db, product_id, risk_report)

            return risk_report

        except Exception as e:
            logger.error(f"商品风险分析失败: {e}")
            return {"error": str(e)}
        finally:
            if db:
                db.close()

    async def analyze_product_risks_by_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于商品数据（非数据库商品）进行风险分析
        
        Args:
            product_data: 商品数据字典，包含 name, price, platform 等
            
        Returns:
            风险分析结果
        """
        try:
            # 初始化LLM服务（如果未初始化）
            if not self.llm_service:
                from .llm_service import get_llm_service
                self.llm_service = get_llm_service()
            
            product_name = product_data.get('name', '')
            product_price = product_data.get('price', 0)
            product_platform = product_data.get('platform', '')
            
            # 基础风险检测
            risk_analyses = []
            
            # 1. 商品名称风险检测
            description_risks = self._analyze_text_for_risks(product_name)
            if description_risks:
                risk_analyses.extend(description_risks)
            
            # 2. 价格异常检测
            price_risks = self._analyze_price_anomaly(product_price, product_name)
            if price_risks:
                risk_analyses.append(price_risks)
            
            # 3. LLM风险分析
            if self.llm_service:
                llm_risks = await self._llm_analyze_product_data(product_data)
                if llm_risks:
                    risk_analyses.extend(llm_risks)
            
            # 综合风险评估
            overall_risk = self._calculate_overall_risk(risk_analyses)
            
            return {
                "product_name": product_name,
                "overall_risk_level": overall_risk["risk_level"],
                "overall_confidence": overall_risk["confidence"],
                "risk_count": len(risk_analyses),
                "detailed_risks": risk_analyses,
                "mitigation_suggestions": await self._generate_mitigation_suggestions(risk_analyses),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"商品数据风险分析失败: {e}")
            return {
                "error": str(e),
                "overall_risk_level": "unknown",
                "risk_count": 0
            }

    def _analyze_text_for_risks(self, text: str) -> List[Dict[str, Any]]:
        """分析文本中的风险关键词"""
        risks = []
        if not text:
            return risks
            
        text_lower = text.lower()
        
        for risk_type, risk_config in self.risk_keywords.items():
            # 检查关键词
            for keyword in risk_config["keywords"]:
                if keyword in text_lower:
                    risks.append({
                        "risk_type": risk_type,
                        "severity": risk_config["severity"],
                        "evidence": f"商品名称包含风险关键词：{keyword}",
                        "confidence": 0.6
                    })
                    break
            
            # 检查正则模式
            for pattern in risk_config["patterns"]:
                if re.search(pattern, text_lower):
                    risks.append({
                        "risk_type": risk_type,
                        "severity": risk_config["severity"],
                        "evidence": f"商品名称匹配风险模式：{pattern}",
                        "confidence": 0.7
                    })
                    break
        
        return risks

    def _analyze_price_anomaly(self, price: float, product_name: str) -> Optional[Dict[str, Any]]:
        """分析价格异常"""
        if price <= 0:
            return {
                "risk_type": "price_anomaly",
                "severity": 0.5,
                "evidence": "商品价格为0或负数，可能存在异常",
                "confidence": 0.8
            }
        
        # 可以根据商品名称判断价格是否过低
        # 这里简化处理，可以后续扩展
        return None

    async def _llm_analyze_product_data(self, product_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用LLM分析商品数据"""
        try:
            if not self.llm_service:
                return []
                
            product_name = product_data.get('name', '')
            product_price = product_data.get('price', 0)
            product_platform = product_data.get('platform', '')
            
            analysis_prompt = f"""
            请分析以下商品可能存在的风险：
            
            商品名称：{product_name}
            价格：¥{product_price}
            平台：{product_platform}
            
            请识别：
            1. 是否存在虚假宣传风险
            2. 价格是否异常（过高或过低）
            3. 商品名称是否包含可疑词汇
            4. 是否需要特别关注的事项
            
            请用JSON格式返回风险分析结果，格式：
            {{
                "risks": [
                    {{
                        "risk_type": "风险类型",
                        "severity": 0.5-1.0,
                        "evidence": "风险证据",
                        "confidence": 0.0-1.0
                    }}
                ]
            }}
            """
            
            response = await self.llm_service.chat_completion([
                {"role": "system", "content": "你是一个专业的商品风险分析专家，擅长识别购物中的潜在风险。"},
                {"role": "user", "content": analysis_prompt}
            ])
            
            content = response.get("content", "")
            
            # 尝试解析JSON
            try:
                import json
                # 提取JSON部分
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                    return result.get("risks", [])
            except:
                # 如果无法解析JSON，返回基于文本的风险
                if "风险" in content or "问题" in content or "可疑" in content:
                    return [{
                        "risk_type": "general_risk",
                        "severity": 0.6,
                        "evidence": "LLM分析发现潜在风险",
                        "confidence": 0.7
                    }]
            
            return []
            
        except Exception as e:
            logger.error(f"LLM风险分析失败: {e}")
            return []

    async def _analyze_complaints(self, db: Session, product_id: int) -> List[Dict[str, Any]]:
        """分析投诉记录"""
        try:
            complaints = db.query(ComplaintRecord).filter(
                ComplaintRecord.product_id == product_id
            ).all()

            if not complaints:
                return []

            risks = []

            # 按投诉类型统计
            complaint_stats = {}
            for complaint in complaints:
                complaint_type = complaint.complaint_type
                if complaint_type not in complaint_stats:
                    complaint_stats[complaint_type] = {
                        "count": 0,
                        "total_severity": 0,
                        "verified_count": 0
                    }

                complaint_stats[complaint_type]["count"] += 1
                complaint_stats[complaint_type]["total_severity"] += self._severity_to_score(complaint.severity_level)
                if complaint.verified:
                    complaint_stats[complaint_type]["verified_count"] += 1

            # 生成风险评估
            for complaint_type, stats in complaint_stats.items():
                avg_severity = stats["total_severity"] / stats["count"]
                verified_ratio = stats["verified_count"] / stats["count"]

                if stats["count"] >= 3 or avg_severity >= 0.7:  # 至少3条投诉或平均严重程度高
                    risk_level = self._score_to_risk_level(avg_severity * verified_ratio)

                    risks.append({
                        "risk_type": complaint_type,
                        "risk_level": risk_level,
                        "confidence": min(0.9, 0.3 + stats["count"] * 0.1 + verified_ratio * 0.3),
                        "evidence": {
                            "complaint_count": stats["count"],
                            "verified_complaints": stats["verified_count"],
                            "average_severity": avg_severity
                        },
                        "description": f"该商品有{stats['count']}条{complaint_type}相关投诉，其中{stats['verified_count']}条已核实",
                        "detection_method": "complaint_analysis"
                    })

            return risks

        except Exception as e:
            logger.error(f"投诉分析失败: {e}")
            return []

    async def _analyze_reviews(self, db: Session, product_id: int) -> List[Dict[str, Any]]:
        """分析用户评价"""
        try:
            reviews = db.query(ProductReview).filter(
                ProductReview.product_id == product_id
            ).all()

            if not reviews:
                return []

            risks = []
            review_texts = [review.review_content for review in reviews]

            # 关键词风险检测
            keyword_risks = self._detect_keyword_risks(review_texts)
            risks.extend(keyword_risks)

            # 情感分析
            negative_reviews = [r for r in reviews if r.sentiment_score and r.sentiment_score < 0.3]
            if len(negative_reviews) > len(reviews) * 0.2:  # 负面评价超过20%
                risks.append({
                    "risk_type": "negative_sentiment",
                    "risk_level": "medium",
                    "confidence": min(0.8, len(negative_reviews) / len(reviews)),
                    "evidence": {
                        "negative_review_count": len(negative_reviews),
                        "total_review_count": len(reviews),
                        "negative_ratio": len(negative_reviews) / len(reviews)
                    },
                    "description": f"负面评价比例较高({len(negative_reviews)/len(reviews)*100:.1f}%)",
                    "detection_method": "sentiment_analysis"
                })

            return risks

        except Exception as e:
            logger.error(f"评价分析失败: {e}")
            return []

    async def _analyze_product_description(self, db: Session, product: Product) -> List[Dict[str, Any]]:
        """分析商品描述风险"""
        try:
            risks = []
            description = product.description or ""
            title = product.title or ""

            # 材质矛盾检测
            material_risks = self._detect_material_inconsistencies(description, title)
            risks.extend(material_risks)

            # 价格异常检测
            price_risks = self._detect_price_anomalies(product)
            if price_risks:
                risks.extend(price_risks)

            # 销量异常检测
            if product.sales_count and product.sales_count > 10000:
                review_count = db.query(ProductReview).filter(
                    ProductReview.product_id == product.id
                ).count()

                if review_count < product.sales_count * 0.01:  # 评价率低于1%
                    risks.append({
                        "risk_type": "suspicious_sales",
                        "risk_level": "medium",
                        "confidence": 0.7,
                        "evidence": {
                            "sales_count": product.sales_count,
                            "review_count": review_count,
                            "review_ratio": review_count / product.sales_count if product.sales_count > 0 else 0
                        },
                        "description": f"销量很高但评价数量较少，可能存在刷单嫌疑",
                        "detection_method": "sales_analysis"
                    })

            return risks

        except Exception as e:
            logger.error(f"商品描述分析失败: {e}")
            return []

    async def _llm_risk_analysis(self, db: Session, product: Product) -> List[Dict[str, Any]]:
        """LLM深度风险分析"""
        try:
            if not self.llm_service:
                return []

            # 获取商品相关信息
            reviews = db.query(ProductReview).filter(
                ProductReview.product_id == product.id
            ).limit(50).all()

            complaints = db.query(ComplaintRecord).filter(
                ComplaintRecord.product_id == product.id
            ).limit(20).all()

            # 构建分析提示
            analysis_prompt = f"""
            请分析以下商品信息，识别潜在风险：

            商品标题：{product.title}
            商品描述：{product.description}
            当前价格：{product.price}
            平台：{product.platform}

            最近用户评价（前5条）：
            {chr(10).join([f"- {review.review_content[:100]}..." for review in reviews[:5]])}

            最近投诉记录（前3条）：
            {chr(10).join([f"- {complaint.complaint_content[:100]}..." for complaint in complaints[:3]])}

            请分析以下维度的风险：
            1. 虚假宣传或夸大其词
            2. 质量问题隐患
            3. 价格异常
            4. 售后服务风险
            5. 安全隐患

            请以JSON格式返回分析结果：
            {{
                "risks": [
                    {{
                        "risk_type": "风险类型",
                        "risk_level": "low/medium/high/critical",
                        "confidence": 0.0-1.0,
                        "description": "风险描述",
                        "evidence": ["证据1", "证据2"]
                    }}
                ]
            }}
            """

            # 调用LLM分析
            llm_response = await self.llm_service.generate_text(analysis_prompt)

            # 解析LLM结果
            try:
                result = json.loads(llm_response)
                llm_risks = []

                for risk in result.get("risks", []):
                    llm_risks.append({
                        "risk_type": risk["risk_type"],
                        "risk_level": risk["risk_level"],
                        "confidence": risk["confidence"],
                        "description": risk["description"],
                        "evidence": {"llm_analysis": risk.get("evidence", [])},
                        "detection_method": "llm_analysis"
                    })

                return llm_risks

            except json.JSONDecodeError:
                logger.error("LLM风险分析结果解析失败")
                return []

        except Exception as e:
            logger.error(f"LLM风险分析失败: {e}")
            return []

    def _detect_keyword_risks(self, texts: List[str]) -> List[Dict[str, Any]]:
        """关键词风险检测"""
        risks = []
        combined_text = " ".join(texts).lower()

        for risk_category, config in self.risk_keywords.items():
            matches = []
            for keyword in config["keywords"]:
                if keyword in combined_text:
                    matches.append(keyword)

            for pattern in config["patterns"]:
                pattern_matches = re.findall(pattern, combined_text)
                matches.extend(pattern_matches)

            if matches:
                confidence = min(0.9, 0.3 + len(matches) * 0.1)
                risk_level = self._score_to_risk_level(config["severity"] * confidence)

                risks.append({
                    "risk_type": risk_category,
                    "risk_level": risk_level,
                    "confidence": confidence,
                    "evidence": {
                        "matched_keywords": matches,
                        "match_count": len(matches)
                    },
                    "description": f"检测到{len(matches)}个风险关键词：{', '.join(matches[:3])}",
                    "detection_method": "keyword_analysis"
                })

        return risks

    def _detect_material_inconsistencies(self, description: str, title: str) -> List[Dict[str, Any]]:
        """材质矛盾检测"""
        risks = []
        full_text = (description + " " + title).lower()

        for claimed_material, risk_indicators in self.material_risks.items():
            if claimed_material in full_text:
                # 检查是否有矛盾描述
                found_indicators = []
                for indicator in risk_indicators:
                    if indicator in full_text:
                        found_indicators.append(indicator)

                if found_indicators:
                    risks.append({
                        "risk_type": "material_inconsistency",
                        "risk_level": "medium",
                        "confidence": 0.8,
                        "evidence": {
                            "claimed_material": claimed_material,
                            "found_indicators": found_indicators
                        },
                        "description": f"宣传为{claimed_material}但描述中包含：{', '.join(found_indicators)}",
                        "detection_method": "material_analysis"
                    })

        return risks

    def _detect_price_anomalies(self, product: Product) -> List[Dict[str, Any]]:
        """价格异常检测"""
        risks = []

        # 检查价格是否异常低
        if product.original_price and product.price < product.original_price * 0.3:
            risks.append({
                "risk_type": "price_too_low",
                "risk_level": "medium",
                "confidence": 0.7,
                "evidence": {
                    "current_price": product.price,
                    "original_price": product.original_price,
                    "discount_ratio": 1 - product.price / product.original_price
                },
                "description": f"当前价格相比原价折扣过大({(1-product.price/product.original_price)*100:.1f}%)，可能存在质量问题",
                "detection_method": "price_analysis"
            })

        # 检查价格是否异常高
        if product.category and product.price > 10000:  # 假设10000元以上为高价商品
            # 这里可以添加品类特定的价格检查逻辑
            pass

        return risks

    def _calculate_overall_risk(self, risk_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算整体风险等级"""
        if not risk_analyses:
            return {"risk_level": "low", "confidence": 0.9}

        # 风险等级映射（基于severity或risk_level）
        risk_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}

        # 计算加权风险分数
        total_score = 0
        total_weight = 0

        for risk in risk_analyses:
            # 支持两种格式：有risk_level字段，或通过severity计算
            if "risk_level" in risk:
                risk_score = risk_scores.get(risk["risk_level"], 1)
            elif "severity" in risk:
                # 将severity (0-1) 转换为风险等级分数
                severity = risk.get("severity", 0)
                if severity >= 0.9:
                    risk_score = 4  # critical
                elif severity >= 0.7:
                    risk_score = 3  # high
                elif severity >= 0.5:
                    risk_score = 2  # medium
                else:
                    risk_score = 1  # low
            else:
                risk_score = 1  # 默认低风险
            
            confidence = risk.get("confidence", 0.5)
            weight = risk_score * confidence

            total_score += weight
            total_weight += confidence

        if total_weight > 0:
            avg_score = total_score / total_weight
        else:
            avg_score = 1

        # 确定整体风险等级
        if avg_score >= 3.5:
            overall_risk = "critical"
        elif avg_score >= 2.5:
            overall_risk = "high"
        elif avg_score >= 1.5:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        # 计算整体置信度
        overall_confidence = min(0.95, len(risk_analyses) * 0.1 + 0.5)

        # 计算风险分布（支持两种格式）
        risk_distribution = {}
        for level in ["low", "medium", "high", "critical"]:
            count = 0
            for r in risk_analyses:
                if r.get("risk_level") == level:
                    count += 1
                elif "severity" in r:
                    severity = r.get("severity", 0)
                    if level == "critical" and severity >= 0.9:
                        count += 1
                    elif level == "high" and 0.7 <= severity < 0.9:
                        count += 1
                    elif level == "medium" and 0.5 <= severity < 0.7:
                        count += 1
                    elif level == "low" and severity < 0.5:
                        count += 1
            risk_distribution[level] = count
        
        return {
            "risk_level": overall_risk,
            "confidence": overall_confidence,
            "risk_score": avg_score,
            "risk_distribution": risk_distribution
        }

    async def _generate_mitigation_suggestions(self, risk_analyses: List[Dict[str, Any]]) -> List[str]:
        """生成风险规避建议"""
        suggestions = []

        for risk in risk_analyses:
            risk_type = risk.get("risk_type", "general_risk")
            # 支持两种格式：risk_level或通过severity计算
            if "risk_level" in risk:
                risk_level = risk["risk_level"]
            elif "severity" in risk:
                severity = risk.get("severity", 0)
                if severity >= 0.9:
                    risk_level = "critical"
                elif severity >= 0.7:
                    risk_level = "high"
                elif severity >= 0.5:
                    risk_level = "medium"
                else:
                    risk_level = "low"
            else:
                risk_level = "low"  # 默认低风险

            if risk_type == "fake_product":
                suggestions.append("建议购买时仔细检查商品包装和防伪标识")
                suggestions.append("选择官方认证店铺或品牌直营店")
            elif risk_type == "quality_issue":
                suggestions.append("关注其他用户的最新评价，特别是关于耐用性的反馈")
                suggestions.append("了解退换货政策和保修期限")
            elif risk_type == "misleading_advertising":
                suggestions.append("仔细阅读商品详情和规格参数")
                suggestions.append("查看实物图片和用户晒单")
            elif risk_type == "service_problem":
                suggestions.append("确认售后服务响应时间和处理流程")
                suggestions.append("保存购买凭证和沟通记录")
            elif risk_type == "safety_risk":
                suggestions.append("检查产品安全认证和检测报告")
                suggestions.append("谨慎购买，建议选择有安全保障的品牌")
            elif risk_type == "material_inconsistency":
                suggestions.append("向客服确认材质成分和规格")
                suggestions.append("查看专业评测和材质分析")

        if risk_analyses:
            suggestions.append("建议货比三家，综合对比不同平台的评价和价格")
            suggestions.append("考虑选择支持7天无理由退换的商品")

        # 去重
        suggestions = list(set(suggestions))
        return suggestions[:5]  # 返回前5个建议

    async def _recommend_alternatives(
        self,
        db: Session,
        product: Product,
        risk_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """推荐替代商品"""
        try:
            if not risk_analyses:  # 如果没有风险，不需要替代品
                return []

            # 查找同类商品中风险较低的商品
            alternatives = db.query(Product).filter(
                Product.category == product.category,
                Product.platform == product.platform,
                Product.id != product.id,
                Product.rating >= 4.0,  # 评分较高
                Product.price >= product.price * 0.8,  # 价格相近
                Product.price <= product.price * 1.2
            ).limit(5).all()

            alternative_recommendations = []

            for alt_product in alternatives:
                # 检查替代品的风险
                alt_risks = db.query(ProductRisk).filter(
                    ProductRisk.product_id == alt_product.id,
                    ProductRisk.risk_level.in_(["high", "critical"])
                ).count()

                if alt_risks == 0:  # 替代品没有高风险
                    alternative_recommendations.append({
                        "product_id": alt_product.id,
                        "title": alt_product.title,
                        "price": alt_product.price,
                        "rating": alt_product.rating,
                        "platform": alt_product.platform,
                        "advantage": "同类商品中风险较低，评分较高",
                        "price_comparison": f"{'高' if alt_product.price > product.price else '低'}于原价{abs(alt_product.price - product.price):.2f}元"
                    })

            return alternative_recommendations[:3]

        except Exception as e:
            logger.error(f"替代品推荐失败: {e}")
            return []

    async def _save_risk_analysis(self, db: Session, product_id: int, risk_report: Dict[str, Any]):
        """保存风险分析结果"""
        try:
            # 清理旧的风险记录
            db.query(ProductRisk).filter(
                ProductRisk.product_id == product_id,
                ProductRisk.created_at < datetime.now() - timedelta(days=7)
            ).delete()

            # 保存新的风险记录
            for risk in risk_report.get("detailed_risks", []):
                product_risk = ProductRisk(
                    product_id=product_id,
                    risk_type=risk["risk_type"],
                    risk_level=risk["risk_level"],
                    risk_description=risk["description"],
                    evidence_sources=risk.get("evidence", {}),
                    detection_method=risk.get("detection_method", "unknown"),
                    confidence_score=risk.get("confidence", 0.5),
                    mitigation_suggestions=risk_report.get("mitigation_suggestions", [])
                )
                db.add(product_risk)

            db.commit()

        except Exception as e:
            logger.error(f"风险分析保存失败: {e}")
            db.rollback()

    def _severity_to_score(self, severity_level: str) -> float:
        """将严重程度转换为分数"""
        mapping = {
            "low": 0.25,
            "medium": 0.5,
            "high": 0.75,
            "critical": 1.0
        }
        return mapping.get(severity_level, 0.5)

    def _score_to_risk_level(self, score: float) -> str:
        """将分数转换为风险等级"""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"

    async def batch_risk_analysis(self, product_ids: List[int]) -> Dict[str, Any]:
        """批量风险分析"""
        try:
            results = {}
            for product_id in product_ids:
                result = await self.analyze_product_risks(product_id)
                results[product_id] = result

            # 汇总统计
            total_products = len(results)
            high_risk_products = len([
                r for r in results.values()
                if isinstance(r, dict) and r.get("overall_risk_level") in ["high", "critical"]
            ])

            summary = {
                "total_analyzed": total_products,
                "high_risk_count": high_risk_products,
                "high_risk_ratio": high_risk_products / total_products if total_products > 0 else 0,
                "risk_distribution": {
                    level: len([
                        r for r in results.values()
                        if isinstance(r, dict) and r.get("overall_risk_level") == level
                    ])
                    for level in ["low", "medium", "high", "critical"]
                }
            }

            return {
                "summary": summary,
                "detailed_results": results
            }

        except Exception as e:
            logger.error(f"批量风险分析失败: {e}")
            return {"error": str(e)}

    async def get_risk_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取风险统计信息"""
        db = next(get_db())

        try:
            start_date = datetime.now() - timedelta(days=days)

            # 风险类型分布
            risk_types = db.query(
                ProductRisk.risk_type,
                func.count(ProductRisk.id).label('count')
            ).filter(
                ProductRisk.created_at >= start_date
            ).group_by(ProductRisk.risk_type).all()

            # 风险等级分布
            risk_levels = db.query(
                ProductRisk.risk_level,
                func.count(ProductRisk.id).label('count')
            ).filter(
                ProductRisk.created_at >= start_date
            ).group_by(ProductRisk.risk_level).all()

            # 检测方法分布
            detection_methods = db.query(
                ProductRisk.detection_method,
                func.count(ProductRisk.id).label('count')
            ).filter(
                ProductRisk.created_at >= start_date
            ).group_by(ProductRisk.detection_method).all()

            # 高风险商品
            high_risk_products = db.query(
                ProductRisk.product_id,
                func.count(ProductRisk.id).label('risk_count')
            ).filter(
                ProductRisk.created_at >= start_date,
                ProductRisk.risk_level.in_(["high", "critical"])
            ).group_by(ProductRisk.product_id).having(
                func.count(ProductRisk.id) >= 2
            ).all()

            return {
                "analysis_period_days": days,
                "total_risk_records": sum([count for _, count in risk_types]),
                "risk_type_distribution": {rtype: count for rtype, count in risk_types},
                "risk_level_distribution": {level: count for level, count in risk_levels},
                "detection_method_distribution": {method: count for method, count in detection_methods},
                "high_risk_products": [
                    {"product_id": pid, "risk_count": count}
                    for pid, count in high_risk_products
                ]
            }

        except Exception as e:
            logger.error(f"风险统计获取失败: {e}")
            return {"error": str(e)}
        finally:
            db.close()


# 创建服务实例
risk_detection_service = RiskDetectionService()