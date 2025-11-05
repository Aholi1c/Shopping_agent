"""
实时价格跟踪和提醒服务
"""

import asyncio
import aiohttp
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging
try:
    from celery import Celery
    from celery.schedules import crontab
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None
    crontab = None
    print("⚠️  celery未安装，价格跟踪的定时任务功能将不可用。请运行: pip install celery")

from ..models.ecommerce_models import (
    Product, PriceHistory, PriceAlert, UserPreference
)
from ..core.config import settings
from .llm_service import LLMService

logger = logging.getLogger(__name__)

# Celery配置
if CELERY_AVAILABLE and Celery:
    celery_app = Celery('price_tracker')
    celery_app.conf.update(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        timezone='Asia/Shanghai',
        enable_utc=True,
    )
else:
    celery_app = None

class PriceTrackerService:
    def __init__(self, db: Session, llm_service: LLMService):
        self.db = db
        self.llm_service = llm_service
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def track_product_prices(self, product_ids: List[str] = None) -> Dict:
        """跟踪指定商品的价格变化"""
        if not product_ids:
            # 获取所有活跃的价格提醒商品
            active_alerts = self.db.query(PriceAlert).filter(
                PriceAlert.is_active == True
            ).all()
            product_ids = list(set([alert.product_id for alert in active_alerts]))

        if not product_ids:
            return {"tracked": 0, "updated": 0, "alerts_triggered": 0}

        tracked_count = 0
        updated_count = 0
        alerts_triggered = 0

        for product_id in product_ids:
            try:
                result = await self._track_single_product(product_id)
                tracked_count += 1
                if result['price_updated']:
                    updated_count += 1
                if result['alerts_triggered']:
                    alerts_triggered += len(result['alerts_triggered'])
            except Exception as e:
                logger.error(f"Error tracking product {product_id}: {e}")

        return {
            "tracked": tracked_count,
            "updated": updated_count,
            "alerts_triggered": alerts_triggered,
            "timestamp": datetime.now().isoformat()
        }

    async def _track_single_product(self, product_id: str) -> Dict:
        """跟踪单个商品价格"""
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            return {"price_updated": False, "alerts_triggered": []}

        # 获取当前价格（这里可以实现真实的API调用）
        current_price = await self._fetch_current_price(product)

        if not current_price:
            return {"price_updated": False, "alerts_triggered": []}

        # 检查价格是否有变化
        last_price = self.db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(PriceHistory.date.desc()).first()

        price_changed = not last_price or abs(last_price.price - current_price) > 0.01

        if price_changed:
            # 记录新的价格历史
            price_history = PriceHistory(
                product_id=product_id,
                price=current_price,
                platform=product.platform,
                date=datetime.now(),
                is_stock_available=True,
                monthly_sales=last_price.monthly_sales if last_price else 0
            )
            self.db.add(price_history)

            # 更新商品价格
            product.price = current_price
            product.discount_rate = (product.original_price - current_price) / product.original_price if product.original_price else 0
            product.updated_at = datetime.now()

            self.db.commit()

            # 检查是否触发价格提醒
            triggered_alerts = await self._check_price_alerts(product_id, current_price)

            return {
                "price_updated": True,
                "old_price": last_price.price if last_price else None,
                "new_price": current_price,
                "alerts_triggered": triggered_alerts
            }

        return {"price_updated": False, "alerts_triggered": []}

    async def _fetch_current_price(self, product: Product) -> Optional[float]:
        """获取商品当前价格（模拟实现）"""
        # 这里可以实现真实的电商平台API调用
        # 目前使用模拟数据

        # 模拟价格波动
        import random
        base_price = product.original_price or product.price
        variation = random.uniform(-0.05, 0.05)  # ±5%的波动
        new_price = base_price * (1 + variation)

        # 模拟API延迟
        await asyncio.sleep(0.1)

        return round(new_price, 2)

    async def _check_price_alerts(self, product_id: str, current_price: float) -> List[Dict]:
        """检查价格提醒"""
        alerts = self.db.query(PriceAlert).filter(
            and_(
                PriceAlert.product_id == product_id,
                PriceAlert.is_active == True,
                PriceAlert.is_triggered == False
            )
        ).all()

        triggered_alerts = []

        for alert in alerts:
            should_trigger = False
            reason = ""

            if alert.alert_type == "below_target" and current_price <= alert.target_price:
                should_trigger = True
                reason = f"价格已降至 ¥{current_price:.2f}，低于目标价 ¥{alert.target_price:.2f}"

            elif alert.alert_type == "percentage_drop" and alert.threshold_percentage:
                # 计算价格降幅
                original_price = alert.current_price or current_price * 1.2  # 如果没有记录原价，估算一个
                drop_percentage = (original_price - current_price) / original_price * 100

                if drop_percentage >= alert.threshold_percentage:
                    should_trigger = True
                    reason = f"价格已下降 {drop_percentage:.1f}%，当前价 ¥{current_price:.2f}"

            if should_trigger:
                # 发送提醒
                await self._send_price_alert(alert, current_price, reason)

                # 更新提醒状态
                alert.is_triggered = True
                alert.triggered_at = datetime.now()
                alert.current_price = current_price
                self.db.commit()

                triggered_alerts.append({
                    "alert_id": alert.id,
                    "user_id": alert.user_id,
                    "reason": reason,
                    "current_price": current_price
                })

        return triggered_alerts

    async def _send_price_alert(self, alert: PriceAlert, current_price: float, reason: str):
        """发送价格提醒"""
        try:
            product = self.db.query(Product).filter(Product.product_id == alert.product_id).first()
            if not product:
                return

            # 获取用户偏好
            user_pref = self.db.query(UserPreference).filter(
                UserPreference.user_id == alert.user_id
            ).first()

            notification_method = alert.notification_method
            if user_pref and user_pref.meta_data:
                notification_method = user_pref.meta_data.get('preferred_notification_method', notification_method)

            # 生成提醒内容
            alert_content = await self._generate_alert_content(product, current_price, reason)

            # 根据用户偏好发送提醒
            if notification_method == "email":
                await self._send_email_alert(alert, product, alert_content)
            elif notification_method == "sms":
                await self._send_sms_alert(alert, alert_content)
            else:  # app
                await self._send_app_alert(alert, alert_content)

            logger.info(f"Price alert sent for product {alert.product_id} to user {alert.user_id}")

        except Exception as e:
            logger.error(f"Error sending price alert: {e}")

    async def _generate_alert_content(self, product: Product, current_price: float, reason: str) -> Dict:
        """生成提醒内容"""
        # 使用LLM生成个性化的提醒内容
        prompt = f"""
        为以下商品价格变化生成一个吸引人的提醒消息：

        商品名称: {product.name}
        品牌: {product.brand}
        原价: ¥{product.original_price:.2f}
        现价: ¥{current_price:.2f}
        平台: {product.platform}
        变化原因: {reason}

        请生成包含以下内容的提醒：
        1. 引人注目的标题
        2. 简洁的产品描述
        3. 价格变化信息
        4. 购买建议
        5. 行动号召

        返回JSON格式：
        {{
            "title": "...",
            "description": "...",
            "price_info": "...",
            "recommendation": "...",
            "cta": "立即查看"
        }}
        """

        try:
            response = await self.llm_service.generate_response(prompt)
            content_data = json.loads(response)
        except:
            # 默认内容
            content_data = {
                "title": f"🔥 {product.name} 价格提醒",
                "description": f"{product.brand} {product.name} 价格有变！",
                "price_info": f"原价: ¥{product.original_price:.2f} → 现价: ¥{current_price:.2f}",
                "recommendation": reason,
                "cta": "立即查看"
            }

        return {
            **content_data,
            "product_id": product.product_id,
            "product_url": product.product_url,
            "image_url": product.image_url,
            "timestamp": datetime.now().isoformat()
        }

    async def _send_email_alert(self, alert: PriceAlert, product: Product, content: Dict):
        """发送邮件提醒"""
        # 这里需要配置邮件服务器
        # 目前模拟实现
        logger.info(f"Email alert would be sent to {alert.user_id} for {product.name}")

    async def _send_sms_alert(self, alert: PriceAlert, content: Dict):
        """发送短信提醒"""
        # 这里需要配置短信服务
        # 目前模拟实现
        logger.info(f"SMS alert would be sent to {alert.user_id}")

    async def _send_app_alert(self, alert: PriceAlert, content: Dict):
        """发送应用内提醒"""
        # 这里可以通过WebSocket或推送服务发送
        # 目前模拟实现
        logger.info(f"App alert would be sent to {alert.user_id}")

    async def create_price_alert(self, user_id: str, product_id: str, target_price: float,
                               alert_type: str = "below_target",
                               threshold_percentage: float = None,
                               notification_method: str = "app") -> Dict:
        """创建价格提醒"""
        # 检查商品是否存在
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise ValueError("商品不存在")

        # 检查是否已有活跃提醒
        existing_alert = self.db.query(PriceAlert).filter(
            and_(
                PriceAlert.user_id == user_id,
                PriceAlert.product_id == product_id,
                PriceAlert.is_active == True
            )
        ).first()

        if existing_alert:
            # 更新现有提醒
            existing_alert.target_price = target_price
            existing_alert.alert_type = alert_type
            existing_alert.threshold_percentage = threshold_percentage
            existing_alert.notification_method = notification_method
            existing_alert.updated_at = datetime.now()
            self.db.commit()
            return {"success": True, "alert_id": existing_alert.id, "action": "updated"}

        # 创建新提醒
        alert = PriceAlert(
            user_id=user_id,
            product_id=product_id,
            target_price=target_price,
            current_price=product.price,
            alert_type=alert_type,
            threshold_percentage=threshold_percentage,
            notification_method=notification_method
        )
        self.db.add(alert)
        self.db.commit()

        return {"success": True, "alert_id": alert.id, "action": "created"}

    async def get_user_alerts(self, user_id: str, include_triggered: bool = False) -> List[Dict]:
        """获取用户的价格提醒"""
        query = self.db.query(PriceAlert).filter(PriceAlert.user_id == user_id)

        if not include_triggered:
            query = query.filter(PriceAlert.is_triggered == False)

        alerts = query.order_by(PriceAlert.created_at.desc()).all()

        result = []
        for alert in alerts:
            product = self.db.query(Product).filter(Product.product_id == alert.product_id).first()
            result.append({
                "alert_id": alert.id,
                "product_id": alert.product_id,
                "product_name": product.name if product else "未知商品",
                "target_price": alert.target_price,
                "current_price": alert.current_price,
                "alert_type": alert.alert_type,
                "threshold_percentage": alert.threshold_percentage,
                "is_active": alert.is_active,
                "is_triggered": alert.is_triggered,
                "created_at": alert.created_at.isoformat(),
                "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None
            })

        return result

    async def delete_alert(self, alert_id: int, user_id: str) -> bool:
        """删除价格提醒"""
        alert = self.db.query(PriceAlert).filter(
            and_(
                PriceAlert.id == alert_id,
                PriceAlert.user_id == user_id
            )
        ).first()

        if not alert:
            return False

        self.db.delete(alert)
        self.db.commit()
        return True

    async def get_price_analysis(self, product_id: str, days: int = 30) -> Dict:
        """获取价格分析报告"""
        since_date = datetime.now() - timedelta(days=days)

        price_history = self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.product_id == product_id,
                PriceHistory.date >= since_date
            )
        ).order_by(PriceHistory.date.asc()).all()

        if not price_history:
            return {"error": "无价格历史数据"}

        prices = [p.price for p in price_history]
        dates = [p.date for p in price_history]

        # 计算统计数据
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        current_price = prices[-1]

        # 计算价格趋势
        if len(prices) >= 7:
            recent_prices = prices[-7:]
            price_trend = "上涨" if recent_prices[-1] > recent_prices[0] else "下跌"
            trend_magnitude = abs(recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
        else:
            price_trend = "稳定"
            trend_magnitude = 0

        # 价格波动性
        price_volatility = (max_price - min_price) / avg_price * 100

        # 最佳购买时机分析
        buy_recommendation = self._analyze_buy_timing(current_price, avg_price, min_price, max_price)

        return {
            "product_id": product_id,
            "analysis_period": f"{days}天",
            "statistics": {
                "min_price": min_price,
                "max_price": max_price,
                "avg_price": avg_price,
                "current_price": current_price,
                "volatility": price_volatility
            },
            "trend": {
                "direction": price_trend,
                "magnitude": trend_magnitude,
                "change_percent": ((current_price - prices[0]) / prices[0] * 100) if len(prices) > 1 else 0
            },
            "recommendation": buy_recommendation,
            "price_history": [
                {
                    "date": p.date.isoformat(),
                    "price": p.price,
                    "platform": p.platform
                }
                for p in price_history[-10:]  # 最近10条记录
            ]
        }

    def _analyze_buy_timing(self, current_price: float, avg_price: float, min_price: float, max_price: float) -> Dict:
        """分析购买时机"""
        score = 0
        reasons = []

        # 价格相对于平均水平
        if current_price <= avg_price * 0.9:
            score += 40
            reasons.append("价格低于历史平均水平的10%")
        elif current_price <= avg_price * 0.95:
            score += 20
            reasons.append("价格低于历史平均水平")
        elif current_price >= avg_price * 1.05:
            score -= 20
            reasons.append("价格高于历史平均水平")

        # 价格接近历史最低
        if current_price <= min_price * 1.05:
            score += 30
            reasons.append("价格接近历史最低价")

        # 价格接近历史最高
        if current_price >= max_price * 0.95:
            score -= 30
            reasons.append("价格接近历史最高价")

        # 确定建议等级
        if score >= 70:
            level = "强烈推荐"
            urgency = "高"
        elif score >= 40:
            level = "推荐"
            urgency = "中"
        elif score >= 0:
            level = "可以考虑"
            urgency = "低"
        else:
            level = "建议等待"
            urgency = "无"

        return {
            "score": max(0, min(100, score)),
            "level": level,
            "urgency": urgency,
            "reasons": reasons
        }

# Celery任务定义
if CELERY_AVAILABLE and celery_app:
    @celery_app.task
    def scheduled_price_tracking():
        """定时价格跟踪任务"""
        from ..core.database import SessionLocal
        from .llm_service import LLMService

        db = SessionLocal()
        llm_service = LLMService()

        try:
            tracker = PriceTrackerService(db, llm_service)
            result = asyncio.run(tracker.track_product_prices())
            logger.info(f"Scheduled price tracking completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in scheduled price tracking: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    # 配置定时任务
    celery_app.conf.beat_schedule = {
        'price-tracking-every-6-hours': {
            'task': 'backend.services.price_tracker_service.scheduled_price_tracking',
            'schedule': crontab(minute=0, hour='*/6'),  # 每6小时执行一次
        },
        'price-tracking-daily': {
            'task': 'backend.services.price_tracker_service.scheduled_price_tracking',
            'schedule': crontab(minute=0, hour=9),  # 每天9点执行
        },
    }
else:
    def scheduled_price_tracking():
        """定时价格跟踪任务（未启用celery）"""
        logger.warning("Celery未安装，定时任务不可用")
        return {"error": "Celery未安装"}