#!/usr/bin/env python3
"""
场景化推荐服务
基于用户场景理解提供个性化推荐
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import numpy as np
from collections import defaultdict

from ..models.models import (
    User, Product, ScenarioTag, UserScenario, ProductScenarioMapping,
    ScenarioKnowledge, UserBehavior, UserPreferenceModel, PreferenceFeedback,
    PotentialNeed, UserPreference, SearchHistory
)
from ..core.database import get_db
from .shopping_service import ShoppingService
from .image_service import ImageService
from .price_service import PriceService


class ScenarioRecommendationService:
    """场景化推荐服务"""

    def __init__(self, db=None, llm_service=None, memory_service=None, media_service=None):
        # Initialize services only if dependencies are provided
        if all([db, llm_service, memory_service, media_service]):
            self.shopping_service = ShoppingService(db, llm_service, memory_service, media_service)
            self.image_service = ImageService(db, llm_service, self.shopping_service)
            self.price_service = PriceService(db, llm_service, self.shopping_service)
        else:
            self.shopping_service = None
            self.image_service = None
            self.price_service = None

        # 场景关键词映射
        self.scenario_keywords = {
            'time': {
                'morning': ['早晨', '早上', '清晨', '晨练', '早餐'],
                'afternoon': ['下午', '午后', '午餐', '午休'],
                'evening': ['晚上', '夜晚', '晚餐', '睡前'],
                'weekend': ['周末', '休息日', '假期', '放假'],
                'holiday': ['节日', '假期', '旅游', '出行'],
                'season': {
                    'spring': ['春天', '春季', '春游', '踏青'],
                    'summer': ['夏天', '夏季', '避暑', '游泳'],
                    'autumn': ['秋天', '秋季', '秋游', '登山'],
                    'winter': ['冬天', '冬季', '保暖', '滑雪']
                }
            },
            'location': {
                'home': ['家里', '居家', '室内', '家用'],
                'office': ['办公室', '公司', '工作', '职场'],
                'outdoor': ['户外', '野外', '露营', '徒步'],
                'travel': ['旅行', '出差', '酒店', '机场'],
                'school': ['学校', '校园', '学习', '考试'],
                'gym': ['健身房', '运动', '健身', '锻炼']
            },
            'user_role': {
                'student': ['学生', '同学', '校园', '学习'],
                'office_worker': ['上班族', '白领', '职场', '工作'],
                'parent': ['父母', '家长', '孩子', '家庭'],
                'elderly': ['老人', '长辈', '老年', '退休'],
                'athlete': ['运动员', '健身', '运动', '锻炼']
            },
            'purpose': {
                'gift': ['礼物', '送礼', '礼品', '赠品'],
                'daily_use': ['日常', '家用', '常用', '生活'],
                'emergency': ['应急', '备用', '紧急', '突发'],
                'entertainment': ['娱乐', '休闲', '游戏', '影音'],
                'health': ['健康', '保健', '医疗', '养生'],
                'efficiency': ['效率', '办公', '生产力', '便捷']
            },
            'constraints': {
                'budget': ['预算', '便宜', '经济', '性价比'],
                'quality': ['质量', '品质', '耐用', '高端'],
                'portability': ['便携', '轻便', '小巧', '随身'],
                'ease_of_use': ['简单', '易用', '方便', '便捷'],
                'eco_friendly': ['环保', '节能', '可持续', '绿色']
            }
        }

    async def parse_scenario_from_input(self, user_input: str, user_id: int) -> Dict[str, Any]:
        """
        解析用户输入中的场景关键词

        Args:
            user_input: 用户输入文本
            user_id: 用户ID

        Returns:
            场景解析结果
        """
        try:
            # 使用LLM解析场景
            llm_prompt = f"""
            请分析以下用户输入，提取场景相关的信息：

            用户输入：{user_input}

            请提取以下信息并以JSON格式返回：
            {{
                "scenario_keywords": {{
                    "time": ["时间相关关键词"],
                    "location": ["地点相关关键词"],
                    "user_role": ["用户角色相关关键词"],
                    "purpose": ["使用目的相关关键词"],
                    "constraints": ["约束条件相关关键词"]
                }},
                "scenario_intent": "场景意图描述",
                "priority_constraints": ["优先约束条件"],
                "implicit_needs": ["隐含需求"]
            }}
            """

            # 调用LLM（这里使用mock，实际应该调用真实的LLM API）
            llm_result = await self._call_llm_for_scenario_parsing(llm_prompt)

            # 解析LLM结果
            scenario_data = json.loads(llm_result)

            # 构建场景标签
            scenario_tags = await self._build_scenario_tags(scenario_data)

            # 保存用户场景
            user_scenario = await self._save_user_scenario(user_id, scenario_data, scenario_tags)

            return {
                "scenario_id": user_scenario.id,
                "parsed_scenario": scenario_data,
                "scenario_tags": scenario_tags,
                "confidence": self._calculate_scenario_confidence(scenario_data)
            }

        except Exception as e:
            print(f"场景解析失败: {e}")
            return {"error": str(e)}

    async def _call_llm_for_scenario_parsing(self, prompt: str) -> str:
        """调用LLM进行场景解析"""
        # 这里应该调用真实的LLM API
        # 为了演示，返回一个模拟结果
        return json.dumps({
            "scenario_keywords": {
                "time": ["早晨", "日常"],
                "location": ["家里", "居家"],
                "user_role": ["父母", "家长"],
                "purpose": ["日常使用", "简单操作"],
                "constraints": ["易用", "性价比"]
            },
            "scenario_intent": "为父母选择一款操作简单的日常使用产品",
            "priority_constraints": ["操作简单", "性价比高"],
            "implicit_needs": ["大字体", "音量适中", "功能实用"]
        }, ensure_ascii=False)

    async def _build_scenario_tags(self, scenario_data: Dict[str, Any]) -> List[str]:
        """构建场景标签"""
        tags = []

        # 基于关键词生成标签
        for category, keywords in scenario_data['scenario_keywords'].items():
            for keyword in keywords:
                tag = f"{category}:{keyword}"
                tags.append(tag)

        # 基于意图生成标签
        intent = scenario_data.get('scenario_intent', '')
        if '父母' in intent and '简单' in intent:
            tags.append('special_group:elderly_friendly')

        # 基于约束生成标签
        constraints = scenario_data.get('priority_constraints', [])
        if '易用' in constraints:
            tags.append('usability:easy')
        if '性价比' in constraints:
            tags.append('price:value_for_money')

        return list(set(tags))  # 去重

    async def _save_user_scenario(self, user_id: int, scenario_data: Dict[str, Any], tags: List[str]) -> UserScenario:
        """保存用户场景"""
        db = next(get_db())

        try:
            # 创建用户场景记录
            user_scenario = UserScenario(
                user_id=user_id,
                scenario_intent=scenario_data.get('scenario_intent', ''),
                scenario_keywords=json.dumps(scenario_data['scenario_keywords'], ensure_ascii=False),
                priority_constraints=json.dumps(scenario_data.get('priority_constraints', []), ensure_ascii=False),
                implicit_needs=json.dumps(scenario_data.get('implicit_needs', []), ensure_ascii=False),
                confidence_score=self._calculate_scenario_confidence(scenario_data)
            )

            db.add(user_scenario)
            db.commit()
            db.refresh(user_scenario)

            # 保存场景标签
            for tag_name in tags:
                # 查找或创建标签
                tag = db.query(ScenarioTag).filter(ScenarioTag.tag_name == tag_name).first()
                if not tag:
                    tag = ScenarioTag(
                        tag_name=tag_name,
                        tag_category=tag_name.split(':')[0] if ':' in tag_name else 'general',
                        description=f"Auto-generated tag for {tag_name}"
                    )
                    db.add(tag)
                    db.commit()
                    db.refresh(tag)

                # 更新标签使用统计
                tag.usage_count = (tag.usage_count or 0) + 1
                tag.last_used = datetime.now()

            db.commit()
            return user_scenario

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def _calculate_scenario_confidence(self, scenario_data: Dict[str, Any]) -> float:
        """计算场景解析置信度"""
        score = 0.0

        # 基于关键词数量
        keyword_count = sum(len(keywords) for keywords in scenario_data['scenario_keywords'].values())
        score += min(keyword_count * 0.1, 0.3)

        # 基于意图清晰度
        intent = scenario_data.get('scenario_intent', '')
        if len(intent) > 10:
            score += 0.2

        # 基于约束条件
        constraints = scenario_data.get('priority_constraints', [])
        if constraints:
            score += 0.2

        # 基于隐含需求
        implicit_needs = scenario_data.get('implicit_needs', [])
        if implicit_needs:
            score += 0.3

        return min(score, 1.0)

    async def get_scenario_based_recommendations(
        self,
        user_id: int,
        scenario_id: int,
        query: str = "",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        基于场景获取推荐商品

        Args:
            user_id: 用户ID
            scenario_id: 场景ID
            query: 搜索查询
            limit: 推荐数量限制

        Returns:
            推荐商品列表
        """
        db = next(get_db())

        try:
            # 获取场景信息
            scenario = db.query(UserScenario).filter(UserScenario.id == scenario_id).first()
            if not scenario:
                return []

            # 获取场景标签
            scenario_tags = self._extract_tags_from_scenario(scenario)

            # 基于场景匹配商品
            product_scores = await self._score_products_by_scenario(db, scenario, scenario_tags, user_id)

            # 排序并返回推荐
            top_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:limit]

            # 获取商品详细信息
            recommendations = []
            for product_id, score in top_products:
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    recommendations.append({
                        "product": product,
                        "score": score,
                        "scenario_match": await self._get_scenario_match_details(db, product, scenario_tags),
                        "reason": await self._generate_recommendation_reason(product, scenario, score)
                    })

            return recommendations

        except Exception as e:
            print(f"场景推荐失败: {e}")
            return []
        finally:
            db.close()

    def _extract_tags_from_scenario(self, scenario: UserScenario) -> List[str]:
        """从场景中提取标签"""
        tags = []

        # 从关键词中提取标签
        keywords = json.loads(scenario.scenario_keywords)
        for category, keyword_list in keywords.items():
            for keyword in keyword_list:
                tags.append(f"{category}:{keyword}")

        # 从约束条件中提取标签
        constraints = json.loads(scenario.priority_constraints)
        for constraint in constraints:
            if '简单' in constraint:
                tags.append('usability:easy')
            elif '便宜' in constraint or '经济' in constraint:
                tags.append('price:budget')
            elif '质量' in constraint or '品质' in constraint:
                tags.append('quality:high')

        return tags

    async def _score_products_by_scenario(
        self,
        db: Session,
        scenario: UserScenario,
        scenario_tags: List[str],
        user_id: int
    ) -> Dict[int, float]:
        """基于场景对商品评分"""
        product_scores = defaultdict(float)

        # 获取所有商品
        products = db.query(Product).all()

        for product in products:
            score = 0.0

            # 1. 场景标签匹配
            scenario_mappings = db.query(ProductScenarioMapping).filter(
                ProductScenarioMapping.product_id == product.id
            ).all()

            for mapping in scenario_mappings:
                if mapping.scenario_tag in scenario_tags:
                    score += mapping.match_score * 0.4

            # 2. 用户历史偏好
            user_prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).all()
            for pref in user_prefs:
                if pref.preference_key in product.title or pref.preference_key in product.description:
                    score += pref.weight * 0.3

            # 3. 价格适配性
            constraints = json.loads(scenario.priority_constraints)
            if any(word in constraints for word in ['便宜', '经济', '性价比']):
                if product.price < 1000:  # 假设1000以下是经济型
                    score += 0.2

            # 4. 品质适配性
            if any(word in constraints for word in ['质量', '品质']):
                if product.rating and product.rating >= 4.5:
                    score += 0.2

            product_scores[product.id] = score

        return product_scores

    async def _get_scenario_match_details(
        self,
        db: Session,
        product: Product,
        scenario_tags: List[str]
    ) -> Dict[str, Any]:
        """获取商品与场景的匹配详情"""
        match_details = {
            "matched_tags": [],
            "match_score": 0.0,
            "strengths": [],
            "weaknesses": []
        }

        # 查找匹配的场景标签
        mappings = db.query(ProductScenarioMapping).filter(
            ProductScenarioMapping.product_id == product.id
        ).all()

        for mapping in mappings:
            if mapping.scenario_tag in scenario_tags:
                match_details["matched_tags"].append(mapping.scenario_tag)
                match_details["match_score"] += mapping.match_score

                if mapping.match_score > 0.7:
                    match_details["strengths"].append(mapping.scenario_tag)
                elif mapping.match_score < 0.3:
                    match_details["weaknesses"].append(mapping.scenario_tag)

        return match_details

    async def _generate_recommendation_reason(
        self,
        product: Product,
        scenario: UserScenario,
        score: float
    ) -> str:
        """生成推荐理由"""
        reasons = []

        # 基于评分生成理由
        if score > 0.8:
            reasons.append("高度匹配您的场景需求")
        elif score > 0.6:
            reasons.append("比较符合您的使用场景")

        # 基于商品特性
        if product.rating and product.rating >= 4.5:
            reasons.append(f"用户评分高({product.rating}/5)")

        if product.original_price and product.price < product.original_price:
            discount = (product.original_price - product.price) / product.original_price * 100
            reasons.append(f"当前优惠{discount:.1f}%")

        # 基于场景约束
        constraints = json.loads(scenario.priority_constraints)
        if '简单' in constraints and '简单' in product.description:
            reasons.append("操作简单，适合日常使用")

        return "；".join(reasons) if reasons else "基于场景分析推荐"

    async def enrich_scenario_with_knowledge(self, scenario_id: int) -> Dict[str, Any]:
        """
        使用RAG系统补充场景相关知识

        Args:
            scenario_id: 场景ID

        Returns:
            补充的知识信息
        """
        db = next(get_db())

        try:
            # 获取场景信息
            scenario = db.query(UserScenario).filter(UserScenario.id == scenario_id).first()
            if not scenario:
                return {}

            # 构建知识查询
            scenario_intent = scenario.scenario_intent
            keywords = json.loads(scenario.scenario_keywords)

            # 查询相关知识点
            knowledge_list = db.query(ScenarioKnowledge).filter(
                or_(
                    *[ScenarioKnowledge.scenario_type.contains(keyword)
                      for category in keywords.values()
                      for keyword in category]
                )
            ).all()

            # 组织知识信息
            enriched_knowledge = {
                "scenario_id": scenario_id,
                "knowledge_points": [],
                "recommendation_tips": [],
                "consideration_factors": []
            }

            for knowledge in knowledge_list:
                enriched_knowledge["knowledge_points"].append({
                    "type": knowledge.scenario_type,
                    "title": knowledge.knowledge_title,
                    "content": knowledge.knowledge_content,
                    "source": knowledge.source_type,
                    "confidence": knowledge.confidence_score
                })

                # 提取建议和考虑因素
                if knowledge.knowledge_content:
                    content = knowledge.knowledge_content
                    if "建议" in content or "推荐" in content:
                        enriched_knowledge["recommendation_tips"].append(content)
                    if "注意" in content or "考虑" in content:
                        enriched_knowledge["consideration_factors"].append(content)

            return enriched_knowledge

        except Exception as e:
            print(f"知识补充失败: {e}")
            return {}
        finally:
            db.close()

    async def track_user_behavior(
        self,
        user_id: int,
        behavior_type: str,
        behavior_data: Dict[str, Any]
    ) -> bool:
        """
        记录用户行为

        Args:
            user_id: 用户ID
            behavior_type: 行为类型
            behavior_data: 行为数据

        Returns:
            是否成功
        """
        db = next(get_db())

        try:
            # 创建行为记录
            behavior = UserBehavior(
                user_id=user_id,
                behavior_type=behavior_type,
                behavior_data=json.dumps(behavior_data, ensure_ascii=False),
                timestamp=datetime.now()
            )

            db.add(behavior)
            db.commit()

            # 触发偏好学习
            await self._update_user_preferences_from_behavior(db, user_id, behavior)

            return True

        except Exception as e:
            print(f"行为记录失败: {e}")
            return False
        finally:
            db.close()

    async def _update_user_preferences_from_behavior(
        self,
        db: Session,
        user_id: int,
        behavior: UserBehavior
    ):
        """基于行为更新用户偏好"""
        try:
            behavior_data = json.loads(behavior.behavior_data)

            # 根据行为类型更新偏好
            if behavior.behavior_type == 'view_product':
                # 查看商品：增加品类偏好
                category = behavior_data.get('category')
                if category:
                    await self._update_preference_weight(db, user_id, 'category', category, 0.05)

            elif behavior.behavior_type == 'search':
                # 搜索行为：增加关键词偏好
                query = behavior_data.get('query', '')
                keywords = self._extract_keywords(query)
                for keyword in keywords:
                    await self._update_preference_weight(db, user_id, 'keyword', keyword, 0.08)

            elif behavior.behavior_type == 'add_to_favorites':
                # 收藏行为：大幅增加偏好
                category = behavior_data.get('category')
                if category:
                    await self._update_preference_weight(db, user_id, 'category', category, 0.15)

            elif behavior.behavior_type == 'purchase':
                # 购买行为：最强的偏好信号
                brand = behavior_data.get('brand')
                if brand:
                    await self._update_preference_weight(db, user_id, 'brand', brand, 0.25)

        except Exception as e:
            print(f"偏好更新失败: {e}")

    def _extract_keywords(self, query: str) -> List[str]:
        """提取搜索关键词"""
        # 简单的关键词提取
        keywords = []
        words = re.findall(r'[\w]+', query)

        # 过滤掉常见词
        stop_words = {'的', '了', '是', '在', '有', '和', '与', '或', '但', '如果', '因为', '所以'}
        for word in words:
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)

        return keywords

    async def _update_preference_weight(
        self,
        db: Session,
        user_id: int,
        pref_type: str,
        pref_key: str,
        weight_increase: float
    ):
        """更新偏好权重"""
        # 查找或创建偏好
        preference = db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_type == pref_type,
            UserPreference.preference_key == pref_key
        ).first()

        if preference:
            # 更新现有偏好
            old_weight = preference.weight
            preference.weight = min(old_weight + weight_increase, 1.0)

            # 记录反馈
            feedback = PreferenceFeedback(
                user_id=user_id,
                preference_type=pref_type,
                preference_key=pref_key,
                old_weight=old_weight,
                new_weight=preference.weight,
                feedback_type='behavior_based',
                feedback_data=json.dumps({
                    "behavior_type": "auto_update",
                    "weight_change": weight_increase
                }, ensure_ascii=False)
            )
            db.add(feedback)
        else:
            # 创建新偏好
            preference = UserPreference(
                user_id=user_id,
                preference_type=pref_type,
                preference_key=pref_key,
                preference_value=pref_key,
                weight=min(weight_increase, 1.0)
            )
            db.add(preference)

        db.commit()

    async def discover_potential_needs(self, user_id: int) -> List[Dict[str, Any]]:
        """
        发现用户潜在需求

        Args:
            user_id: 用户ID

        Returns:
            潜在需求列表
        """
        db = next(get_db())

        try:
            # 分析用户行为模式
            behaviors = db.query(UserBehavior).filter(
                UserBehavior.user_id == user_id,
                UserBehavior.timestamp >= datetime.now() - timedelta(days=30)
            ).all()

            # 分析购买历史
            purchase_behaviors = [b for b in behaviors if b.behavior_type == 'purchase']

            potential_needs = []

            # 基于购买历史发现相关需求
            for purchase in purchase_behaviors:
                purchase_data = json.loads(purchase.behavior_data)
                category = purchase_data.get('category')

                if category:
                    # 发现相关品类的潜在需求
                    related_needs = self._find_related_needs(category)
                    for need in related_needs:
                        # 检查是否已经存在
                        existing = db.query(PotentialNeed).filter(
                            PotentialNeed.user_id == user_id,
                            PotentialNeed.need_type == need['type'],
                            PotentialNeed.need_content == need['content']
                        ).first()

                        if not existing:
                            potential_need = PotentialNeed(
                                user_id=user_id,
                                need_type=need['type'],
                                need_content=need['content'],
                                confidence_score=need['confidence'],
                                source_behavior_id=purchase.id,
                                need_metadata=json.dumps({
                                    "related_category": category,
                                    "discovery_method": "purchase_pattern"
                                }, ensure_ascii=False)
                            )
                            db.add(potential_need)
                            potential_needs.append(potential_need)

            db.commit()

            # 格式化返回结果
            return [
                {
                    "id": need.id,
                    "type": need.need_type,
                    "content": need.need_content,
                    "confidence": need.confidence_score,
                    "metadata": json.loads(need.need_metadata)
                }
                for need in potential_needs
            ]

        except Exception as e:
            print(f"潜在需求发现失败: {e}")
            return []
        finally:
            db.close()

    def _find_related_needs(self, category: str) -> List[Dict[str, Any]]:
        """基于品类发现相关需求"""
        # 简单的规则-based相关需求发现
        related_needs_map = {
            '咖啡机': [
                {'type': 'consumable', 'content': '咖啡豆/咖啡粉', 'confidence': 0.8},
                {'type': 'accessory', 'content': '咖啡杯', 'confidence': 0.6},
                {'type': 'maintenance', 'content': '清洁剂', 'confidence': 0.5}
            ],
            '手机': [
                {'type': 'accessory', 'content': '手机壳', 'confidence': 0.9},
                {'type': 'accessory', 'content': '充电器', 'confidence': 0.8},
                {'type': 'consumable', 'content': '贴膜', 'confidence': 0.7}
            ],
            '打印机': [
                {'type': 'consumable', 'content': '墨盒/墨粉', 'confidence': 0.9},
                {'type': 'consumable', 'content': '打印纸', 'confidence': 0.8}
            ]
        }

        return related_needs_map.get(category, [])

    async def generate_user_insight_report(self, user_id: int) -> Dict[str, Any]:
        """
        生成用户洞察报告

        Args:
            user_id: 用户ID

        Returns:
            用户洞察报告
        """
        db = next(get_db())

        try:
            # 收集用户数据
            behaviors = db.query(UserBehavior).filter(
                UserBehavior.user_id == user_id,
                UserBehavior.timestamp >= datetime.now() - timedelta(days=30)
            ).all()

            preferences = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).all()

            scenarios = db.query(UserScenario).filter(
                UserScenario.user_id == user_id,
                UserScenario.created_at >= datetime.now() - timedelta(days=30)
            ).all()

            # 生成洞察
            report = {
                "user_id": user_id,
                "report_period": "30天",
                "generated_at": datetime.now().isoformat(),
                "behavior_analysis": await self._analyze_behavior_patterns(behaviors),
                "preference_analysis": await self._analyze_preferences(preferences),
                "scenario_analysis": await self._analyze_scenario_patterns(scenarios),
                "recommendations": await self._generate_user_recommendations(user_id, behaviors, preferences)
            }

            # 保存报告
            insight_report = UserInsightReport(
                user_id=user_id,
                report_data=json.dumps(report, ensure_ascii=False),
                report_period_days=30
            )
            db.add(insight_report)
            db.commit()

            return report

        except Exception as e:
            print(f"洞察报告生成失败: {e}")
            return {}
        finally:
            db.close()

    async def _analyze_behavior_patterns(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """分析用户行为模式"""
        behavior_stats = defaultdict(int)
        category_stats = defaultdict(int)
        time_stats = defaultdict(int)

        for behavior in behaviors:
            behavior_stats[behavior.behavior_type] += 1

            try:
                behavior_data = json.loads(behavior.behavior_data)
                category = behavior_data.get('category')
                if category:
                    category_stats[category] += 1

                # 分析时间模式
                hour = behavior.timestamp.hour
                if 6 <= hour < 12:
                    time_stats['morning'] += 1
                elif 12 <= hour < 18:
                    time_stats['afternoon'] += 1
                elif 18 <= hour < 24:
                    time_stats['evening'] += 1
                else:
                    time_stats['night'] += 1

            except:
                continue

        return {
            "behavior_frequency": dict(behavior_stats),
            "preferred_categories": dict(category_stats),
            "active_time_periods": dict(time_stats),
            "total_behaviors": len(behaviors)
        }

    async def _analyze_preferences(self, preferences: List[UserPreference]) -> Dict[str, Any]:
        """分析用户偏好"""
        pref_by_type = defaultdict(list)

        for pref in preferences:
            pref_by_type[pref.preference_type].append({
                "key": pref.preference_key,
                "weight": pref.weight,
                "value": pref.preference_value
            })

        # 计算偏好强度分布
        weight_distribution = {"high": 0, "medium": 0, "low": 0}
        for pref in preferences:
            if pref.weight >= 0.7:
                weight_distribution["high"] += 1
            elif pref.weight >= 0.4:
                weight_distribution["medium"] += 1
            else:
                weight_distribution["low"] += 1

        return {
            "preferences_by_type": dict(pref_by_type),
            "weight_distribution": weight_distribution,
            "total_preferences": len(preferences)
        }

    async def _analyze_scenario_patterns(self, scenarios: List[UserScenario]) -> Dict[str, Any]:
        """分析用户场景模式"""
        if not scenarios:
            return {"total_scenarios": 0}

        intent_keywords = []
        constraint_stats = defaultdict(int)

        for scenario in scenarios:
            intent_keywords.extend(scenario.scenario_intent.split())

            try:
                constraints = json.loads(scenario.priority_constraints)
                for constraint in constraints:
                    constraint_stats[constraint] += 1
            except:
                continue

        return {
            "total_scenarios": len(scenarios),
            "common_constraints": dict(constraint_stats),
            "avg_confidence": sum(s.confidence_score for s in scenarios) / len(scenarios)
        }

    async def _generate_user_recommendations(
        self,
        user_id: int,
        behaviors: List[UserBehavior],
        preferences: List[UserPreference]
    ) -> List[str]:
        """为用户生成建议"""
        recommendations = []

        # 基于行为频率的建议
        if len(behaviors) < 10:
            recommendations.append("建议增加使用频率，让系统更好地了解您的偏好")

        # 基于偏好分布的建议
        high_prefs = [p for p in preferences if p.weight >= 0.7]
        if len(high_prefs) < 3:
            favorites = [p.preference_key for p in high_prefs]
            recommendations.append(f"建议标记更多喜欢的商品，当前偏好：{', '.join(favorites)}")

        # 基于购买行为的建议
        purchase_count = len([b for b in behaviors if b.behavior_type == 'purchase'])
        if purchase_count == 0:
            recommendations.append("建议完成首次购买，系统将能为您提供更精准的推荐")

        return recommendations


# 创建服务实例
scenario_service = ScenarioRecommendationService()