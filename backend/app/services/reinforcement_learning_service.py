#!/usr/bin/env python3
"""
强化学习偏好优化服务
基于用户行为反馈动态调整推荐策略
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import random
from collections import defaultdict

from ..models.models import (
    User, Product, UserPreferenceModel, PreferenceFeedback,
    UserBehavior, UserPreference, UserScenario
)
from ..core.database import get_db


class ReinforcementLearningService:
    """强化学习偏好优化服务"""

    def __init__(self):
        # 学习参数
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.2
        self.min_exploration_rate = 0.01
        self.exploration_decay = 0.995

        # 奖励函数权重
        self.reward_weights = {
            'click': 0.1,
            'view': 0.05,
            'favorite': 0.2,
            'add_to_cart': 0.3,
            'purchase': 0.5,
            'negative_feedback': -0.3,
            'positive_feedback': 0.2
        }

        # 状态-动作对定义
        self.action_space = [
            'increase_weight',
            'decrease_weight',
            'maintain_weight',
            'explore_new',
            'focus_on_similar'
        ]

        self.state_space = {
            'user_satisfaction': ['low', 'medium', 'high'],
            'behavior_frequency': ['low', 'medium', 'high'],
            'preference_diversity': ['low', 'medium', 'high'],
            'recommendation_accuracy': ['low', 'medium', 'high']
        }

    async def update_preference_model(
        self,
        user_id: int,
        feedback_data: Dict[str, Any]
    ) -> bool:
        """
        更新用户偏好模型

        Args:
            user_id: 用户ID
            feedback_data: 反馈数据

        Returns:
            是否成功
        """
        db = next(get_db())

        try:
            # 计算奖励
            reward = self._calculate_reward(feedback_data)

            # 获取当前状态
            current_state = await self._get_current_state(db, user_id)

            # 选择动作
            action = self._select_action(current_state)

            # 执行动作并更新模型
            await self._execute_action(db, user_id, action, feedback_data)

            # 更新Q值
            await self._update_q_value(db, user_id, current_state, action, reward)

            # 记录反馈
            await self._record_feedback(db, user_id, feedback_data, reward, action)

            # 衰减探索率
            self._decay_exploration_rate()

            return True

        except Exception as e:
            print(f"偏好模型更新失败: {e}")
            return False
        finally:
            db.close()

    def _calculate_reward(self, feedback_data: Dict[str, Any]) -> float:
        """计算奖励值"""
        reward = 0.0

        # 基于行为类型的奖励
        behavior_type = feedback_data.get('behavior_type', '')
        if behavior_type in self.reward_weights:
            reward += self.reward_weights[behavior_type]

        # 基于停留时间的奖励
        duration = feedback_data.get('duration', 0)
        if duration > 30:  # 停留超过30秒
            reward += 0.1

        # 基于转换率的奖励
        conversion_rate = feedback_data.get('conversion_rate', 0)
        reward += conversion_rate * 0.2

        # 基于用户评分的奖励
        user_rating = feedback_data.get('user_rating', 0)
        if user_rating > 0:
            reward += (user_rating - 3) * 0.1  # 5分制，3分是中性

        # 基于价格敏感度的奖励
        price_action = feedback_data.get('price_action', '')
        if price_action == 'within_budget':
            reward += 0.15
        elif price_action == 'over_budget_no_purchase':
            reward -= 0.1

        return np.clip(reward, -1.0, 1.0)  # 限制在[-1, 1]范围内

    async def _get_current_state(self, db: Session, user_id: int) -> str:
        """获取当前状态"""
        # 分析用户满意度
        recent_behaviors = db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.timestamp >= datetime.now() - timedelta(days=7)
        ).all()

        if not recent_behaviors:
            return 'low_frequency_low_satisfaction_low_diversity_low_accuracy'

        # 计算满意度
        positive_behaviors = len([b for b in recent_behaviors
                                if b.behavior_type in ['favorite', 'purchase', 'positive_feedback']])
        total_behaviors = len(recent_behaviors)
        satisfaction = positive_behaviors / total_behaviors if total_behaviors > 0 else 0

        if satisfaction > 0.6:
            satisfaction_level = 'high'
        elif satisfaction > 0.3:
            satisfaction_level = 'medium'
        else:
            satisfaction_level = 'low'

        # 计算行为频率
        if total_behaviors > 20:
            frequency_level = 'high'
        elif total_behaviors > 10:
            frequency_level = 'medium'
        else:
            frequency_level = 'low'

        # 计算偏好多样性
        user_preferences = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()

        preference_types = set(p.preference_type for p in user_preferences)
        diversity = len(preference_types)

        if diversity > 5:
            diversity_level = 'high'
        elif diversity > 3:
            diversity_level = 'medium'
        else:
            diversity_level = 'low'

        # 计算推荐准确度（基于反馈）
        feedbacks = db.query(PreferenceFeedback).filter(
            PreferenceFeedback.user_id == user_id,
            PreferenceFeedback.created_at >= datetime.now() - timedelta(days=7)
        ).all()

        if feedbacks:
            accuracy = sum(f.new_weight > f.old_weight for f in feedbacks) / len(feedbacks)
        else:
            accuracy = 0.5

        if accuracy > 0.7:
            accuracy_level = 'high'
        elif accuracy > 0.5:
            accuracy_level = 'medium'
        else:
            accuracy_level = 'low'

        return f"{satisfaction_level}_satisfaction_{frequency_level}_frequency_{diversity_level}_diversity_{accuracy_level}_accuracy"

    def _select_action(self, state: str) -> str:
        """选择动作（ε-贪婪策略）"""
        if random.random() < self.exploration_rate:
            # 探索：随机选择动作
            return random.choice(self.action_space)
        else:
            # 利用：选择Q值最高的动作
            # 这里简化处理，实际应该查询Q表
            return 'increase_weight'  # 默认动作

    async def _execute_action(
        self,
        db: Session,
        user_id: int,
        action: str,
        feedback_data: Dict[str, Any]
    ):
        """执行动作"""
        if action == 'increase_weight':
            await self._increase_preference_weights(db, user_id, feedback_data)
        elif action == 'decrease_weight':
            await self._decrease_preference_weights(db, user_id, feedback_data)
        elif action == 'maintain_weight':
            await self._maintain_preference_weights(db, user_id)
        elif action == 'explore_new':
            await self._explore_new_preferences(db, user_id)
        elif action == 'focus_on_similar':
            await self._focus_on_similar_preferences(db, user_id, feedback_data)

    async def _increase_preference_weights(
        self,
        db: Session,
        user_id: int,
        feedback_data: Dict[str, Any]
    ):
        """增加偏好权重"""
        # 获取相关的偏好
        category = feedback_data.get('category')
        brand = feedback_data.get('brand')
        keywords = feedback_data.get('keywords', [])

        if category:
            await self._update_single_preference(db, user_id, 'category', category, 0.1)

        if brand:
            await self._update_single_preference(db, user_id, 'brand', brand, 0.1)

        for keyword in keywords:
            await self._update_single_preference(db, user_id, 'keyword', keyword, 0.05)

    async def _decrease_preference_weights(
        self,
        db: Session,
        user_id: int,
        feedback_data: Dict[str, Any]
    ):
        """减少偏好权重"""
        # 获取相关的偏好
        category = feedback_data.get('category')
        brand = feedback_data.get('brand')

        if category:
            await self._update_single_preference(db, user_id, 'category', category, -0.1)

        if brand:
            await self._update_single_preference(db, user_id, 'brand', brand, -0.1)

    async def _maintain_preference_weights(
        self,
        db: Session,
        user_id: int
    ):
        """保持偏好权重"""
        # 轻微调整所有偏好，增加稳定性
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()

        for pref in preferences:
            # 向0.5靠拢，避免极值
            if pref.weight > 0.5:
                pref.weight -= 0.02
            else:
                pref.weight += 0.02

        db.commit()

    async def _explore_new_preferences(
        self,
        db: Session,
        user_id: int
    ):
        """探索新偏好"""
        # 分析用户最近的搜索行为
        recent_searches = db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.behavior_type == 'search',
            UserBehavior.timestamp >= datetime.now() - timedelta(days=3)
        ).all()

        for search in recent_searches:
            try:
                search_data = json.loads(search.behavior_data)
                query = search_data.get('query', '')

                # 提取新关键词
                keywords = self._extract_keywords(query)
                for keyword in keywords:
                    # 检查是否已经是偏好
                    existing = db.query(UserPreference).filter(
                        UserPreference.user_id == user_id,
                        UserPreference.preference_key == keyword
                    ).first()

                    if not existing:
                        # 创建新偏好，低权重
                        new_pref = UserPreference(
                            user_id=user_id,
                            preference_type='keyword',
                            preference_key=keyword,
                            preference_value=keyword,
                            weight=0.3
                        )
                        db.add(new_pref)

            except:
                continue

        db.commit()

    async def _focus_on_similar_preferences(
        self,
        db: Session,
        user_id: int,
        feedback_data: Dict[str, Any]
    ):
        """聚焦相似偏好"""
        # 获取当前高权重偏好的相似项
        high_weight_prefs = db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.weight >= 0.7
        ).all()

        for pref in high_weight_prefs:
            # 基于当前偏好发现相似偏好
            similar_items = await self._find_similar_preferences(pref.preference_key)

            for similar_item in similar_items:
                # 检查是否已存在
                existing = db.query(UserPreference).filter(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_key == similar_item
                ).first()

                if not existing:
                    # 创建相似偏好
                    new_pref = UserPreference(
                        user_id=user_id,
                        preference_type=pref.preference_type,
                        preference_key=similar_item,
                        preference_value=similar_item,
                        weight=pref.weight * 0.8  # 略低于原偏好
                    )
                    db.add(new_pref)

        db.commit()

    async def _update_single_preference(
        self,
        db: Session,
        user_id: int,
        pref_type: str,
        pref_key: str,
        weight_change: float
    ):
        """更新单个偏好"""
        preference = db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_type == pref_type,
            UserPreference.preference_key == pref_key
        ).first()

        if preference:
            old_weight = preference.weight
            preference.weight = np.clip(old_weight + weight_change, 0.0, 1.0)

            # 记录反馈
            feedback = PreferenceFeedback(
                user_id=user_id,
                preference_type=pref_type,
                preference_key=pref_key,
                old_weight=old_weight,
                new_weight=preference.weight,
                feedback_type='rl_optimization',
                feedback_data=json.dumps({
                    "action": "weight_update",
                    "weight_change": weight_change,
                    "reason": "reinforcement_learning"
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
                weight=np.clip(weight_change, 0.0, 1.0)
            )
            db.add(preference)

        db.commit()

    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        import re
        keywords = []
        words = re.findall(r'[\w]+', query)

        # 过滤常见词
        stop_words = {'的', '了', '是', '在', '有', '和', '与', '或', '但', '如果', '因为', '所以'}
        for word in words:
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)

        return keywords

    async def _find_similar_preferences(self, preference_key: str) -> List[str]:
        """发现相似偏好"""
        # 简单的相似性发现
        similarity_map = {
            '手机': ['智能手机', '移动电话', '通讯设备'],
            '电脑': ['笔记本', '台式机', '平板电脑'],
            '运动': ['健身', '锻炼', '户外'],
            '美食': ['食物', '餐厅', '烹饪'],
            '旅游': ['旅行', '出行', '度假'],
            '音乐': ['歌曲', '音频', '音响'],
            '摄影': ['拍照', '相机', '镜头'],
            '读书': ['阅读', '书籍', '学习']
        }

        return similarity_map.get(preference_key, [])

    async def _update_q_value(
        self,
        db: Session,
        user_id: int,
        state: str,
        action: str,
        reward: float
    ):
        """更新Q值"""
        # 获取或创建Q表
        q_table = db.query(UserPreferenceModel).filter(
            UserPreferenceModel.user_id == user_id,
            UserPreferenceModel.preference_dimension == 'q_table'
        ).first()

        if not q_table:
            q_table = UserPreferenceModel(
                user_id=user_id,
                preference_dimension='q_table',
                current_weight=0.5,
                learning_rate=self.learning_rate,
                confidence=0.5,
                model_metadata=json.dumps({}, ensure_ascii=False)
            )
            db.add(q_table)
            db.commit()
            db.refresh(q_table)

        # 获取当前Q表数据
        try:
            q_data = json.loads(q_table.model_metadata or '{}')
        except:
            q_data = {}

        # 初始化状态-动作对
        if state not in q_data:
            q_data[state] = {action: 0.0 for action in self.action_space}

        # Q-learning更新
        old_q = q_data[state][action]
        max_next_q = max(q_data[state].values())  # 简化处理
        new_q = old_q + self.learning_rate * (reward + self.discount_factor * max_next_q - old_q)

        q_data[state][action] = new_q

        # 更新模型
        q_table.model_metadata = json.dumps(q_data, ensure_ascii=False)
        q_table.current_weight = np.mean([max(state_values.values()) for state_values in q_data.values()])
        q_table.confidence = min(q_table.confidence + 0.01, 1.0)

        db.commit()

    async def _record_feedback(
        self,
        db: Session,
        user_id: int,
        feedback_data: Dict[str, Any],
        reward: float,
        action: str
    ):
        """记录反馈"""
        feedback = PreferenceFeedback(
            user_id=user_id,
            preference_type='reinforcement_learning',
            preference_key=action,
            old_weight=0.0,
            new_weight=reward,
            feedback_type='rl_training',
            feedback_data=json.dumps({
                "reward": reward,
                "action": action,
                "original_feedback": feedback_data,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False)
        )
        db.add(feedback)
        db.commit()

    def _decay_exploration_rate(self):
        """衰减探索率"""
        self.exploration_rate = max(
            self.exploration_rate * self.exploration_decay,
            self.min_exploration_rate
        )

    async def get_optimization_report(self, user_id: int) -> Dict[str, Any]:
        """
        获取优化报告

        Args:
            user_id: 用户ID

        Returns:
            优化报告
        """
        db = next(get_db())

        try:
            # 获取用户模型
            models = db.query(UserPreferenceModel).filter(
                UserPreferenceModel.user_id == user_id
            ).all()

            # 获取最近的反馈
            recent_feedbacks = db.query(PreferenceFeedback).filter(
                PreferenceFeedback.user_id == user_id,
                PreferenceFeedback.created_at >= datetime.now() - timedelta(days=7)
            ).all()

            # 分析学习效果
            report = {
                "user_id": user_id,
                "report_period": "7天",
                "generated_at": datetime.now().isoformat(),
                "learning_parameters": {
                    "learning_rate": self.learning_rate,
                    "exploration_rate": self.exploration_rate,
                    "discount_factor": self.discount_factor
                },
                "model_performance": await self._analyze_model_performance(models),
                "recent_improvements": await self._analyze_recent_improvements(recent_feedbacks),
                "recommendation_accuracy": await self._calculate_recommendation_accuracy(db, user_id),
                "optimization_suggestions": await self._generate_optimization_suggestions(db, user_id)
            }

            return report

        except Exception as e:
            print(f"优化报告生成失败: {e}")
            return {}
        finally:
            db.close()

    async def _analyze_model_performance(self, models: List[UserPreferenceModel]) -> Dict[str, Any]:
        """分析模型性能"""
        if not models:
            return {"total_models": 0}

        performance = {
            "total_models": len(models),
            "average_confidence": np.mean([m.confidence for m in models]),
            "high_confidence_models": len([m for m in models if m.confidence > 0.8]),
            "learning_progress": {}
        }

        # 分析学习进度
        for model in models:
            if model.model_metadata:
                try:
                    q_data = json.loads(model.model_metadata)
                    total_states = len(q_data)
                    avg_q_value = np.mean([max(state.values()) for state in q_data.values()])

                    performance["learning_progress"][model.preference_dimension] = {
                        "states_learned": total_states,
                        "average_q_value": avg_q_value
                    }
                except:
                    continue

        return performance

    async def _analyze_recent_improvements(self, feedbacks: List[PreferenceFeedback]) -> Dict[str, Any]:
        """分析近期改进"""
        if not feedbacks:
            return {"total_feedbacks": 0}

        positive_changes = [f for f in feedbacks if f.new_weight > f.old_weight]
        negative_changes = [f for f in feedbacks if f.new_weight < f.old_weight]

        return {
            "total_feedbacks": len(feedbacks),
            "positive_changes": len(positive_changes),
            "negative_changes": len(negative_changes),
            "improvement_rate": len(positive_changes) / len(feedbacks) if feedbacks else 0,
            "average_improvement": np.mean([f.new_weight - f.old_weight for f in positive_changes]) if positive_changes else 0
        }

    async def _calculate_recommendation_accuracy(self, db: Session, user_id: int) -> Dict[str, Any]:
        """计算推荐准确度"""
        # 获取推荐相关的行为
        recommendation_behaviors = db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.behavior_type.in_(['click_recommendation', 'view_recommendation']),
            UserBehavior.timestamp >= datetime.now() - timedelta(days=7)
        ).all()

        if not recommendation_behaviors:
            return {"accuracy": 0.0, "total_recommendations": 0}

        # 计算转化率
        conversions = 0
        for behavior in recommendation_behaviors:
            try:
                behavior_data = json.loads(behavior.behavior_data)
                if behavior_data.get('converted', False):
                    conversions += 1
            except:
                continue

        accuracy = conversions / len(recommendation_behaviors) if recommendation_behaviors else 0

        return {
            "accuracy": accuracy,
            "total_recommendations": len(recommendation_behaviors),
            "conversions": conversions
        }

    async def _generate_optimization_suggestions(self, db: Session, user_id: int) -> List[str]:
        """生成优化建议"""
        suggestions = []

        # 分析用户行为频率
        recent_behaviors = db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.timestamp >= datetime.now() - timedelta(days=7)
        ).all()

        if len(recent_behaviors) < 5:
            suggestions.append("建议增加使用频率，提供更多学习数据")

        # 分析偏好多样性
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()

        pref_types = set(p.preference_type for p in preferences)
        if len(pref_types) < 3:
            suggestions.append("建议探索更多类型的偏好，增加推荐多样性")

        # 分析反馈质量
        recent_feedbacks = db.query(PreferenceFeedback).filter(
            PreferenceFeedback.user_id == user_id,
            PreferenceFeedback.created_at >= datetime.now() - timedelta(days=7)
        ).all()

        if len(recent_feedbacks) < 3:
            suggestions.append("建议提供更多反馈，帮助系统学习您的偏好")

        # 分析探索率
        if self.exploration_rate > 0.3:
            suggestions.append("系统正在积极探索新偏好，推荐可能更多样化")

        return suggestions


# 创建服务实例
rl_service = ReinforcementLearningService()