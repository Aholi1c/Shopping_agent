"""
数据源管理器 - 负责数据源的调度、监控和管理
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from celery import Celery
from celery.schedules import crontab
from ..core.config import settings
from ..services.enhanced_rag_service import EnhancedRAGService
from ..models.models import DataSourceConfig as DataSourceModel

logger = logging.getLogger(__name__)

# 创建Celery实例
celery_app = Celery(
    'data_source_manager',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

class DataSourceManager:
    """数据源管理器"""

    def __init__(self, db: Session):
        self.db = db
        self.rag_service = EnhancedRAGService(db)
        self.is_running = False
        self.update_tasks = {}

    async def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            return

        self.is_running = True
        logger.info("Data source scheduler started")

        # 为每个数据源创建调度任务
        for source_name, source in self.rag_service.data_sources.items():
            if source.is_active:
                await self._schedule_source_updates(source_name, source)

    async def stop_scheduler(self):
        """停止调度器"""
        self.is_running = False
        logger.info("Data source scheduler stopped")

        # 取消所有调度任务
        for task in self.update_tasks.values():
            task.cancel()

        self.update_tasks.clear()

    async def _schedule_source_updates(self, source_name: str, source):
        """为数据源调度更新任务"""
        schedule_interval = self._get_schedule_interval(source.update_frequency)

        async def update_task():
            while self.is_running:
                try:
                    await asyncio.sleep(schedule_interval)

                    if not self.is_running:
                        break

                    # 检查是否需要更新
                    if source._should_update():
                        logger.info(f"Starting scheduled update for {source_name}")
                        await self._update_source_with_retry(source_name, source)
                        logger.info(f"Completed scheduled update for {source_name}")

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in scheduled update for {source_name}: {e}")

        # 创建并启动任务
        task = asyncio.create_task(update_task())
        self.update_tasks[source_name] = task

    def _get_schedule_interval(self, frequency: str) -> int:
        """获取调度间隔（秒）"""
        intervals = {
            "hourly": 3600,      # 1小时
            "daily": 86400,      # 24小时
            "weekly": 604800,    # 7天
            "monthly": 2592000   # 30天
        }
        return intervals.get(frequency, 86400)  # 默认每天

    async def _update_source_with_retry(self, source_name: str, source, max_retries: int = 3):
        """带重试的数据源更新"""
        for attempt in range(max_retries):
            try:
                data = await source.update_data()

                if data:
                    await self.rag_service._store_source_data(source_name, data)
                    logger.info(f"Successfully updated {source_name} with {len(data)} items")
                    return True
                else:
                    logger.info(f"No new data for {source_name}")
                    return True

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {source_name}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(60 * (attempt + 1))  # 指数退避
                else:
                    logger.error(f"All retries failed for {source_name}")
                    return False

    async def update_source_now(self, source_name: str) -> Dict[str, Any]:
        """立即更新指定数据源"""
        if source_name not in self.rag_service.data_sources:
            return {
                "success": False,
                "error": f"Data source '{source_name}' not found"
            }

        source = self.rag_service.data_sources[source_name]
        if not source.is_active:
            return {
                "success": False,
                "error": f"Data source '{source_name}' is not active"
            }

        try:
            data = await source.update_data()
            if data:
                await self.rag_service._store_source_data(source_name, data)
                return {
                    "success": True,
                    "items_processed": len(data),
                    "message": f"Successfully updated {source_name}"
                }
            else:
                return {
                    "success": True,
                    "items_processed": 0,
                    "message": f"No new data available for {source_name}"
                }

        except Exception as e:
            logger.error(f"Error updating {source_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_source_status(self) -> Dict[str, Any]:
        """获取所有数据源状态"""
        status = {
            "scheduler_running": self.is_running,
            "total_sources": len(self.rag_service.data_sources),
            "active_sources": 0,
            "sources": {}
        }

        for source_name, source in self.rag_service.data_sources.items():
            is_active = source.is_active
            needs_update = source._should_update()
            last_updated = source.last_updated.isoformat() if source.last_updated else None

            source_status = {
                "name": source_name,
                "is_active": is_active,
                "needs_update": needs_update,
                "last_updated": last_updated,
                "update_frequency": source.update_frequency,
                "scheduled": source_name in self.update_tasks,
                "status": "healthy" if is_active else "inactive"
            }

            status["sources"][source_name] = source_status
            if is_active:
                status["active_sources"] += 1

        return status

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        healthy_sources = 0
        total_sources = len(self.rag_service.data_sources)

        for source_name, source in self.rag_service.data_sources.items():
            if source.is_active:
                # 简单的健康检查：检查最近是否成功更新过
                if source.last_updated:
                    time_since_update = datetime.utcnow() - source.last_updated
                    if time_since_update <= timedelta(days=7):  # 7内有更新认为健康
                        healthy_sources += 1

        health_score = (healthy_sources / total_sources * 100) if total_sources > 0 else 0

        return {
            "healthy": health_score >= 80,  # 80%以上数据源健康认为整体健康
            "health_score": round(health_score, 1),
            "healthy_sources": healthy_sources,
            "total_sources": total_sources,
            "scheduler_running": self.is_running
        }

    async def cleanup_old_data(self, days_threshold: int = 30):
        """清理旧数据"""
        try:
            await self.rag_service.cleanup_old_source_data(days_threshold)
            logger.info(f"Cleaned up data older than {days_threshold} days")
            return {
                "success": True,
                "message": f"Cleanup completed for data older than {days_threshold} days"
            }
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Celery任务定义
@celery_app.task
def update_data_source_task(source_name: str):
    """Celery任务：更新数据源"""
    try:
        from ..core.database import SessionLocal
        from .data_source_manager import DataSourceManager

        db = SessionLocal()
        manager = DataSourceManager(db)

        result = asyncio.run(manager.update_source_now(source_name))

        db.close()
        return result

    except Exception as e:
        logger.error(f"Error in Celery task for {source_name}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@celery_app.task
def cleanup_old_data_task(days_threshold: int = 30):
    """Celery任务：清理旧数据"""
    try:
        from ..core.database import SessionLocal
        from .data_source_manager import DataSourceManager

        db = SessionLocal()
        manager = DataSourceManager(db)

        result = asyncio.run(manager.cleanup_old_data(days_threshold))

        db.close()
        return result

    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@celery_app.task
def health_check_task():
    """Celery任务：健康检查"""
    try:
        from ..core.database import SessionLocal
        from .data_source_manager import DataSourceManager

        db = SessionLocal()
        manager = DataSourceManager(db)

        result = asyncio.run(manager.health_check())

        db.close()
        return result

    except Exception as e:
        logger.error(f"Error in health check task: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }

# 配置定期任务
celery_app.conf.beat_schedule = {
    'update-rss-sources': {
        'task': 'app.services.data_source_manager.update_data_source_task',
        'schedule': crontab(minute=0, hour='*/6'),  # 每6小时
        'args': ('rss',)
    },
    'cleanup-old-data': {
        'task': 'app.services.data_source_manager.cleanup_old_data_task',
        'schedule': crontab(minute=0, hour=2),  # 每天凌晨2点
        'args': (30,)
    },
    'health-check': {
        'task': 'app.services.data_source_manager.health_check_task',
        'schedule': crontab(minute=0, hour='*/1'),  # 每小时
    },
}

# 全局数据源管理器实例
data_source_manager = None

def get_data_source_manager(db: Session) -> DataSourceManager:
    """获取数据源管理器实例"""
    global data_source_manager
    if data_source_manager is None:
        data_source_manager = DataSourceManager(db)
    return data_source_manager