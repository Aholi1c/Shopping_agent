#!/usr/bin/env python3
"""
价格预测和促销优化服务
分析历史价格数据，预测价格走势，优化购买时机
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    LinearRegression = None
    StandardScaler = None
    print("⚠️  scikit-learn未安装，价格预测功能将不可用。请运行: pip install scikit-learn")
import warnings
warnings.filterwarnings('ignore')

from ..models.models import (
    Product, PriceHistory, PricePrediction, PromotionCalendar,
    PriceAlert, User, Coupon
)
from ..core.database import get_db
from .price_service import PriceService

logger = logging.getLogger(__name__)


class PricePredictionService:
    """价格预测和促销优化服务"""

    def __init__(self):
        self.price_service = PriceService(None, None, None)

        # 促销日历模板
        self.promotion_templates = {
            "618": {
                "start_month": 6,
                "start_day": 1,
                "end_month": 6,
                "end_day": 18,
                "typical_discount": 0.15,
                "platform_coverage": ["jd", "taobao", "pdd"]
            },
            "双11": {
                "start_month": 11,
                "start_day": 1,
                "end_month": 11,
                "end_day": 11,
                "typical_discount": 0.25,
                "platform_coverage": ["jd", "taobao", "pdd", "xiaohongshu"]
            },
            "双12": {
                "start_month": 12,
                "start_day": 1,
                "end_month": 12,
                "end_day": 12,
                "typical_discount": 0.20,
                "platform_coverage": ["jd", "taobao", "pdd"]
            },
            "春节": {
                "start_month": 1,
                "start_day": 15,
                "end_month": 2,
                "end_day": 15,
                "typical_discount": 0.10,
                "platform_coverage": ["jd", "taobao", "pdd"]
            }
        }

    async def predict_price_trend(
        self,
        product_id: int,
        prediction_days: int = 30
    ) -> Dict[str, Any]:
        """
        预测商品价格趋势

        Args:
            product_id: 商品ID
            prediction_days: 预测天数

        Returns:
            价格预测结果
        """
        db = next(get_db())

        try:
            # 获取商品信息
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"error": "商品不存在"}

            # 获取历史价格数据
            price_history = db.query(PriceHistory).filter(
                PriceHistory.product_id == product_id,
                PriceHistory.record_date >= datetime.now() - timedelta(days=90)
            ).order_by(PriceHistory.record_date).all()

            if len(price_history) < 7:
                return {"error": "历史价格数据不足，无法预测"}

            # 准备时间序列数据
            df = self._prepare_time_series_data(price_history)

            # 多种预测模型
            predictions = {}
            models_used = []

            # 1. 线性回归预测
            lr_pred, lr_confidence = self._linear_regression_prediction(df, prediction_days)
            if lr_pred is not None:
                predictions['linear_regression'] = {
                    'predictions': lr_pred,
                    'confidence': lr_confidence
                }
                models_used.append('linear_regression')

            # 2. 移动平均预测
            ma_pred, ma_confidence = self._moving_average_prediction(df, prediction_days)
            if ma_pred is not None:
                predictions['moving_average'] = {
                    'predictions': ma_pred,
                    'confidence': ma_confidence
                }
                models_used.append('moving_average')

            # 3. 季节性预测
            seasonal_pred, seasonal_confidence = self._seasonal_prediction(df, prediction_days, product.platform)
            if seasonal_pred is not None:
                predictions['seasonal'] = {
                    'predictions': seasonal_pred,
                    'confidence': seasonal_confidence
                }
                models_used.append('seasonal')

            # 集成预测结果
            if predictions:
                final_prediction = self._ensemble_predictions(predictions)
                purchase_advice = self._generate_purchase_advice(final_prediction, product)

                # 保存预测结果
                await self._save_prediction_results(db, product_id, final_prediction, models_used)

                return {
                    "product_id": product_id,
                    "current_price": product.price,
                    "prediction_days": prediction_days,
                    "final_prediction": final_prediction,
                    "models_used": models_used,
                    "purchase_advice": purchase_advice,
                    "confidence_score": final_prediction.get('confidence', 0.5),
                    "next_promotion": await self._get_next_promotion_info(db, product.platform)
                }
            else:
                return {"error": "预测失败"}

        except Exception as e:
            logger.error(f"价格预测失败: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    def _prepare_time_series_data(self, price_history: List[PriceHistory]) -> pd.DataFrame:
        """准备时间序列数据"""
        data = []
        for record in price_history:
            data.append({
                'date': record.record_date,
                'price': record.price,
                'day_of_week': record.record_date.weekday(),
                'day_of_month': record.record_date.day,
                'month': record.record_date.month,
                'is_weekend': record.record_date.weekday() in [5, 6]
            })

        df = pd.DataFrame(data)
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        return df

    def _linear_regression_prediction(
        self,
        df: pd.DataFrame,
        prediction_days: int
    ) -> Tuple[Optional[List[float]], float]:
        """线性回归预测"""
        try:
            X = df[['days_since_start', 'day_of_week', 'is_weekend']]
            y = df['price']

            # 标准化特征
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # 训练模型
            model = LinearRegression()
            model.fit(X_scaled, y)

            # 预测未来
            last_day = df['days_since_start'].max()
            future_days = []
            for i in range(1, prediction_days + 1):
                future_date = df['date'].max() + timedelta(days=i)
                future_days.append([
                    last_day + i,
                    future_date.weekday(),
                    future_date.weekday() in [5, 6]
                ])

            future_days_scaled = scaler.transform(future_days)
            predictions = model.predict(future_days_scaled)

            # 计算置信度（基于R²）
            r2_score = model.score(X_scaled, y)
            confidence = max(0.1, min(0.9, r2_score))

            return predictions.tolist(), confidence

        except Exception as e:
            logger.error(f"线性回归预测失败: {e}")
            return None, 0.0

    def _moving_average_prediction(
        self,
        df: pd.DataFrame,
        prediction_days: int
    ) -> Tuple[Optional[List[float]], float]:
        """移动平均预测"""
        try:
            # 计算多个移动平均
            ma_7 = df['price'].rolling(window=7, min_periods=1).mean()
            ma_14 = df['price'].rolling(window=14, min_periods=1).mean()
            ma_30 = df['price'].rolling(window=30, min_periods=1).mean()

            # 预测未来价格（简单延续趋势）
            last_ma_7 = ma_7.iloc[-1]
            last_ma_14 = ma_14.iloc[-1]
            last_ma_30 = ma_30.iloc[-1]

            # 计算趋势
            recent_trend = df['price'].tail(7).mean() - df['price'].tail(14).mean()

            predictions = []
            for i in range(prediction_days):
                # 加权平均不同周期的移动平均
                pred = (last_ma_7 * 0.5 + last_ma_14 * 0.3 + last_ma_30 * 0.2) + (recent_trend * 0.1 * i)
                predictions.append(pred)

            # 计算置信度（基于价格稳定性）
            price_volatility = df['price'].std() / df['price'].mean()
            confidence = max(0.1, min(0.8, 1.0 - price_volatility))

            return predictions, confidence

        except Exception as e:
            logger.error(f"移动平均预测失败: {e}")
            return None, 0.0

    def _seasonal_prediction(
        self,
        df: pd.DataFrame,
        prediction_days: int,
        platform: str
    ) -> Tuple[Optional[List[float]], float]:
        """季节性预测（考虑促销周期）"""
        try:
            current_date = df['date'].max()
            predictions = []

            for i in range(prediction_days):
                future_date = current_date + timedelta(days=i)
                base_price = df['price'].mean()

                # 检查是否接近促销期
                seasonal_factor = 1.0
                for promo_name, promo_info in self.promotion_templates.items():
                    if (promo_info['start_month'] == future_date.month and
                        future_date.day >= promo_info['start_day'] and
                        future_date.day <= promo_info['end_day'] and
                        platform in promo_info['platform_coverage']):

                        seasonal_factor = 1.0 - promo_info['typical_discount']
                        break

                # 添加随机波动
                random_factor = 1.0 + np.random.normal(0, 0.02)
                predicted_price = base_price * seasonal_factor * random_factor
                predictions.append(predicted_price)

            # 季节性预测的置信度较高
            confidence = 0.7

            return predictions, confidence

        except Exception as e:
            logger.error(f"季节性预测失败: {e}")
            return None, 0.0

    def _ensemble_predictions(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """集成多个模型的预测结果"""
        try:
            all_predictions = []
            weights = []

            for model_name, model_result in predictions.items():
                pred_list = model_result['predictions']
                confidence = model_result['confidence']

                all_predictions.append(pred_list)
                weights.append(confidence)

            # 归一化权重
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]

            # 加权平均
            num_days = len(all_predictions[0])
            final_predictions = []

            for day in range(num_days):
                day_predictions = [pred[day] for pred in all_predictions]
                weighted_avg = sum(pred * weight for pred, weight in zip(day_predictions, weights))
                final_predictions.append(weighted_avg)

            # 计算置信区间
            prediction_std = np.std([pred[day] for pred in all_predictions for day in range(num_days)])
            confidence_lower = [p - prediction_std for p in final_predictions]
            confidence_upper = [p + prediction_std for p in final_predictions]

            return {
                'predictions': final_predictions,
                'confidence_lower': confidence_lower,
                'confidence_upper': confidence_upper,
                'confidence': np.mean(weights)
            }

        except Exception as e:
            logger.error(f"预测集成失败: {e}")
            return {}

    def _generate_purchase_advice(
        self,
        prediction: Dict[str, Any],
        product: Product
    ) -> Dict[str, Any]:
        """生成购买建议"""
        try:
            current_price = product.price
            predictions = prediction['predictions']
            confidence_lower = prediction['confidence_lower']
            confidence_upper = prediction['confidence_upper']

            # 分析价格趋势
            min_future_price = min(confidence_lower[:7])  # 未来7天最低价
            max_future_price = max(confidence_upper[:7])  # 未来7天最高价

            advice = {
                "action": "hold",  # wait, buy_now, set_alert
                "reason": "",
                "confidence": prediction['confidence'],
                "expected_savings": 0.0,
                "time_frame": "",
                "risk_level": "low"
            }

            # 判断购买时机
            if min_future_price < current_price * 0.95:  # 未来7天可能降价5%以上
                advice["action"] = "wait"
                advice["reason"] = f"预计未来7天内价格可能降至¥{min_future_price:.2f}，建议等待"
                advice["expected_savings"] = current_price - min_future_price
                advice["time_frame"] = "7天内"
                advice["risk_level"] = "medium"
            elif max_future_price > current_price * 1.05:  # 未来7天可能涨价
                advice["action"] = "buy_now"
                advice["reason"] = f"预计未来7天内价格可能涨至¥{max_future_price:.2f}，建议立即购买"
                advice["expected_savings"] = max_future_price - current_price
                advice["time_frame"] = "立即"
                advice["risk_level"] = "low"
            else:  # 价格相对稳定
                price_change_percent = abs(predictions[0] - current_price) / current_price
                if price_change_percent < 0.02:  # 价格变化小于2%
                    advice["action"] = "buy_now"
                    advice["reason"] = "价格相对稳定，可以按需购买"
                    advice["risk_level"] = "low"
                else:
                    advice["action"] = "set_alert"
                    advice["reason"] = f"价格可能有{price_change_percent*100:.1f}%的波动，建议设置价格提醒"
                    advice["risk_level"] = "medium"

            return advice

        except Exception as e:
            logger.error(f"购买建议生成失败: {e}")
            return {"action": "hold", "reason": "无法生成建议"}

    async def _save_prediction_results(
        self,
        db: Session,
        product_id: int,
        prediction: Dict[str, Any],
        models_used: List[str]
    ):
        """保存预测结果"""
        try:
            # 清理旧预测
            db.query(PricePrediction).filter(
                PricePrediction.product_id == product_id,
                PricePrediction.created_at < datetime.now() - timedelta(days=1)
            ).delete()

            # 保存新预测
            for i, (pred_price, lower, upper) in enumerate(zip(
                prediction['predictions'],
                prediction['confidence_lower'],
                prediction['confidence_upper']
            )):
                prediction_date = datetime.now() + timedelta(days=i+1)

                price_pred = PricePrediction(
                    product_id=product_id,
                    prediction_date=prediction_date,
                    predicted_price=pred_price,
                    confidence_lower=lower,
                    confidence_upper=upper,
                    prediction_model="ensemble",
                    features_used=json.dumps({"models_used": models_used}),
                    accuracy_score=prediction['confidence']
                )
                db.add(price_pred)

            db.commit()

        except Exception as e:
            logger.error(f"预测结果保存失败: {e}")
            db.rollback()

    async def _get_next_promotion_info(self, db: Session, platform: str) -> Optional[Dict[str, Any]]:
        """获取下一个促销信息"""
        try:
            current_date = datetime.now()

            # 查找即将到来的促销
            next_promo = db.query(PromotionCalendar).filter(
                PromotionCalendar.platform == platform,
                PromotionCalendar.start_date > current_date,
                PromotionCalendar.is_active == True
            ).order_by(PromotionCalendar.start_date).first()

            if next_promo:
                days_until = (next_promo.start_date - current_date).days
                return {
                    "name": next_promo.promotion_name,
                    "start_date": next_promo.start_date.strftime("%Y-%m-%d"),
                    "days_until": days_until,
                    "typical_discount": next_promo.maximum_discount,
                    "minimum_threshold": next_promo.minimum_threshold
                }

            # 检查模板促销
            for promo_name, promo_info in self.promotion_templates.items():
                if platform in promo_info['platform_coverage']:
                    promo_start = datetime(
                        current_date.year,
                        promo_info['start_month'],
                        promo_info['start_day']
                    )

                    # 如果今年的促销已过，计算明年的
                    if promo_start < current_date:
                        promo_start = datetime(
                            current_date.year + 1,
                            promo_info['start_month'],
                            promo_info['start_day']
                        )

                    days_until = (promo_start - current_date).days
                    if 0 < days_until <= 60:  # 只显示60天内的促销
                        return {
                            "name": promo_name,
                            "start_date": promo_start.strftime("%Y-%m-%d"),
                            "days_until": days_until,
                            "typical_discount": promo_info['typical_discount'],
                            "minimum_threshold": 0
                        }

            return None

        except Exception as e:
            logger.error(f"获取促销信息失败: {e}")
            return None

    async def optimize_purchase_timing(
        self,
        product_id: int,
        user_id: int,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        优化购买时机

        Args:
            product_id: 商品ID
            user_id: 用户ID
            quantity: 购买数量

        Returns:
            优化建议
        """
        db = next(get_db())

        try:
            # 获取价格预测
            prediction_result = await self.predict_price_trend(product_id, 30)
            if "error" in prediction_result:
                return prediction_result

            # 获取用户优惠券
            user_coupons = db.query(Coupon).filter(
                Coupon.platform == prediction_result.get('platform', 'jd'),
                func.datetime(Coupon.end_date) > datetime.now()
            ).all()

            # 分析凑单机会
            bundle_analysis = await self._analyze_bundle_opportunity(db, product_id, user_id, user_coupons)

            # 生成综合建议
            comprehensive_advice = await self._generate_comprehensive_advice(
                prediction_result, bundle_analysis, user_coupons, quantity
            )

            return {
                "product_id": product_id,
                "user_id": user_id,
                "quantity": quantity,
                "price_prediction": prediction_result,
                "bundle_analysis": bundle_analysis,
                "comprehensive_advice": comprehensive_advice,
                "optimal_action": comprehensive_advice.get('action', 'wait'),
                "expected_savings": comprehensive_advice.get('total_savings', 0),
                "confidence": comprehensive_advice.get('confidence', 0.5)
            }

        except Exception as e:
            logger.error(f"购买时机优化失败: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def _analyze_bundle_opportunity(
        self,
        db: Session,
        product_id: int,
        user_id: int,
        user_coupons: List[Coupon]
    ) -> Dict[str, Any]:
        """分析凑单机会"""
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"error": "商品不存在"}

            bundle_opportunities = []

            for coupon in user_coupons:
                if coupon.min_purchase_amount and product.price < coupon.min_purchase_amount:
                    # 计算凑单需求
                    needed_amount = coupon.min_purchase_amount - product.price
                    discount_value = 0

                    if coupon.discount_type == 'fixed':
                        discount_value = coupon.discount_value
                    elif coupon.discount_type == 'percentage':
                        discount_value = product.price * coupon.discount_value / 100

                    if discount_value > 0:
                        bundle_opportunities.append({
                            "coupon_id": coupon.id,
                            "coupon_title": coupon.title,
                            "needed_amount": needed_amount,
                            "discount_value": discount_value,
                            "suggestion": f"建议凑单¥{needed_amount:.2f}可使用此优惠券，节省¥{discount_value:.2f}"
                        })

            return {
                "has_bundle_opportunity": len(bundle_opportunities) > 0,
                "bundle_opportunities": bundle_opportunities,
                "best_opportunity": max(bundle_opportunities, key=lambda x: x['discount_value']) if bundle_opportunities else None
            }

        except Exception as e:
            logger.error(f"凑单分析失败: {e}")
            return {"error": str(e)}

    async def _generate_comprehensive_advice(
        self,
        prediction_result: Dict[str, Any],
        bundle_analysis: Dict[str, Any],
        user_coupons: List[Coupon],
        quantity: int
    ) -> Dict[str, Any]:
        """生成综合购买建议"""
        try:
            purchase_advice = prediction_result.get('purchase_advice', {})
            current_price = prediction_result.get('current_price', 0)
            next_promotion = prediction_result.get('next_promotion')

            total_savings = 0
            reasons = []
            action = purchase_advice.get('action', 'hold')
            confidence = purchase_advice.get('confidence', 0.5)

            # 考虑优惠券影响
            if user_coupons and action != 'wait':
                best_coupon = max(user_coupons, key=lambda c: (
                    c.discount_value if c.discount_type == 'fixed'
                    else current_price * c.discount_value / 100
                ), default=None)

                if best_coupon:
                    if best_coupon.discount_type == 'fixed':
                        coupon_savings = best_coupon.discount_value
                    else:
                        coupon_savings = current_price * best_coupon.discount_value / 100

                    if best_coupon.min_purchase_amount and current_price >= best_coupon.min_purchase_amount:
                        total_savings += coupon_savings
                        reasons.append(f"使用优惠券[{best_coupon.title}]可节省¥{coupon_savings:.2f}")

            # 考虑凑单机会
            if bundle_analysis.get('best_opportunity'):
                best_bundle = bundle_analysis['best_opportunity']
                if action == 'buy_now':
                    reasons.append(best_bundle['suggestion'])
                    total_savings += best_bundle['discount_value']

            # 考虑促销影响
            if next_promotion and action == 'wait':
                days_until = next_promotion.get('days_until', 0)
                if days_until <= 7:
                    expected_savings = current_price * next_promotion.get('typical_discount', 0.1)
                    total_savings += expected_savings
                    reasons.append(f"{days_until}天后{next_promotion['name']}促销，预计节省¥{expected_savings:.2f}")

            # 调整购买建议
            if total_savings > current_price * 0.1:  # 如果能节省超过10%
                if action == 'buy_now':
                    action = 'bundle_buy'
                elif action == 'wait':
                    reasons.append(f"总计可节省¥{total_savings:.2f}，建议等待")

            return {
                "action": action,
                "reasons": reasons,
                "total_savings": total_savings,
                "confidence": confidence,
                "price_comparison": {
                    "current_price": current_price,
                    "expected_final_price": current_price - total_savings,
                    "savings_percentage": (total_savings / current_price * 100) if current_price > 0 else 0
                },
                "timing_suggestion": self._generate_timing_suggestion(action, next_promotion)
            }

        except Exception as e:
            logger.error(f"综合建议生成失败: {e}")
            return {"action": "hold", "reasons": ["无法生成建议"]}

    def _generate_timing_suggestion(self, action: str, next_promotion: Optional[Dict]) -> str:
        """生成时间建议"""
        if action == 'buy_now':
            return "建议立即购买"
        elif action == 'bundle_buy':
            return "建议凑单后立即购买"
        elif action == 'wait' and next_promotion:
            return f"建议等待{next_promotion['days_until']}天后的{next_promotion['name']}促销"
        elif action == 'set_alert':
            return "建议设置价格提醒"
        else:
            return "建议继续观望"

    async def create_price_alert(
        self,
        user_id: int,
        product_id: int,
        alert_type: str,
        threshold_value: float,
        notification_method: str = "app"
    ) -> Dict[str, Any]:
        """
        创建价格提醒

        Args:
            user_id: 用户ID
            product_id: 商品ID
            alert_type: 提醒类型
            threshold_value: 阈值
            notification_method: 通知方式

        Returns:
            创建结果
        """
        db = next(get_db())

        try:
            # 验证商品存在
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"error": "商品不存在"}

            # 计算目标价格
            target_price = product.price
            if alert_type == "below":
                target_price = threshold_value
            elif alert_type == "percentage_drop":
                target_price = product.price * (1 - threshold_value / 100)
            elif alert_type == "above":
                target_price = threshold_value

            # 创建价格提醒
            price_alert = PriceAlert(
                user_id=user_id,
                product_id=product_id,
                target_price=target_price,
                alert_type=alert_type,
                threshold_value=threshold_value,
                notification_method=notification_method
            )

            db.add(price_alert)
            db.commit()
            db.refresh(price_alert)

            return {
                "success": True,
                "alert_id": price_alert.id,
                "message": f"价格提醒创建成功，当价格{self._get_alert_description(alert_type, threshold_value)}时将通知您"
            }

        except Exception as e:
            logger.error(f"价格提醒创建失败: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    def _get_alert_description(self, alert_type: str, threshold_value: float) -> str:
        """获取提醒描述"""
        if alert_type == "below":
            return f"低于¥{threshold_value}"
        elif alert_type == "above":
            return f"高于¥{threshold_value}"
        elif alert_type == "percentage_drop":
            return f"下降{threshold_value}%"
        else:
            return "达到设定条件"

    async def check_price_alerts(self) -> List[Dict[str, Any]]:
        """检查价格提醒"""
        db = next(get_db())

        try:
            # 获取活跃的价格提醒
            active_alerts = db.query(PriceAlert).filter(
                PriceAlert.is_active == True,
                PriceAlert.is_triggered == False
            ).all()

            triggered_alerts = []

            for alert in active_alerts:
                product = db.query(Product).filter(Product.id == alert.product_id).first()
                if not product:
                    continue

                should_trigger = False

                if alert.alert_type == "below" and product.price <= alert.target_price:
                    should_trigger = True
                elif alert.alert_type == "above" and product.price >= alert.target_price:
                    should_trigger = True
                elif alert.alert_type == "percentage_drop":
                    # 需要查询历史价格计算跌幅
                    latest_price = db.query(PriceHistory).filter(
                        PriceHistory.product_id == alert.product_id
                    ).order_by(desc(PriceHistory.record_date)).first()

                    if latest_price:
                        drop_percentage = (latest_price.price - product.price) / latest_price.price * 100
                        if drop_percentage >= alert.threshold_value:
                            should_trigger = True

                if should_trigger:
                    alert.is_triggered = True
                    alert.triggered_at = datetime.now()

                    triggered_alerts.append({
                        "alert_id": alert.id,
                        "user_id": alert.user_id,
                        "product_id": alert.product_id,
                        "product_title": product.title,
                        "current_price": product.price,
                        "target_price": alert.target_price,
                        "alert_type": alert.alert_type,
                        "notification_method": alert.notification_method
                    })

            if triggered_alerts:
                db.commit()

            return triggered_alerts

        except Exception as e:
            logger.error(f"价格提醒检查失败: {e}")
            return []
        finally:
            db.close()


# 创建服务实例
price_prediction_service = PricePredictionService()