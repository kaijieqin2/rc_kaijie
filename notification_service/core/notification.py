"""
核心 - 通知管理
"""
import uuid
from typing import Dict, Any
from datetime import datetime
from config.settings import settings
from mocks.mock_db import db
from mocks.mock_queue import get_default_queue
from observability.logger import logger
from observability.metrics import metrics


class NotificationService:
    """通知服务"""

    def __init__(self):
        self.queue = get_default_queue()

    def create_notification(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建通知"""
        # 验证必需字段
        required_fields = ["business_system", "event_type", "provider", "data"]
        for field in required_fields:
            if field not in request_data:
                raise ValueError(f"Missing required field: {field}")

        provider_name = request_data["provider"]

        # 验证供应商配置
        try:
            provider_config = settings.get_provider(provider_name)
        except ValueError as e:
            raise ValueError(f"Invalid provider: {provider_name}")

        # 构建通知数据
        notification_data = {
            "business_system": request_data["business_system"],
            "event_type": request_data["event_type"],
            "provider": provider_name,
            "target_url": provider_config.url,
            "headers": provider_config.headers.copy(),
            "body": request_data["data"],
            "max_retry": settings.retry.max_retry,
        }

        # 创建数据库记录
        notification_id = db.create_notification(notification_data)

        # 记录指标
        metrics.record_notification_created()

        # 将任务放入队列
        self.queue.enqueue(notification_id, {"notification_id": notification_id})
        metrics.queue_enqueued.inc()
        metrics.queue_size.inc()

        logger.info(
            f"Notification created: {notification_id}",
            extra={
                "notification_id": notification_id,
                "provider": provider_name,
                "event_type": request_data["event_type"],
            },
        )

        return {
            "notification_id": notification_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

    def get_notification(self, notification_id: str) -> Dict[str, Any]:
        """获取通知详情"""
        notification = db.get_notification(notification_id)
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        # 转换datetime为字符串
        result = {**notification}
        for key in ["created_at", "updated_at", "delivered_at", "next_retry_at"]:
            if result.get(key):
                result[key] = result[key].isoformat() + "Z"

        return result

    def list_notifications(
        self, status: str = None, provider: str = None, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """列出通知"""
        notifications = db.list_notifications(status, provider, limit, offset)

        # 转换datetime为字符串
        for notification in notifications:
            for key in ["created_at", "updated_at", "delivered_at", "next_retry_at"]:
                if notification.get(key):
                    notification[key] = notification[key].isoformat() + "Z"

        return {"notifications": notifications, "count": len(notifications)}

    def get_delivery_logs(self, notification_id: str) -> Dict[str, Any]:
        """获取投递日志"""
        logs = db.get_delivery_logs(notification_id)

        # 转换datetime为字符串
        for log in logs:
            if log.get("created_at"):
                log["created_at"] = log["created_at"].isoformat() + "Z"

        return {"logs": logs, "count": len(logs)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        # 从数据库获取统计
        db_stats = db.get_statistics()

        # 计算成功率
        success_count = db_stats["status_counts"].get("success", 0)
        failed_count = db_stats["status_counts"].get("failed", 0)
        total_completed = success_count + failed_count

        success_rate = success_count / total_completed if total_completed > 0 else 0

        # 添加队列统计
        queue_stats = self.queue.get_stats()

        return {
            "total_notifications": db_stats["total_notifications"],
            "status_counts": db_stats["status_counts"],
            "success_rate": round(success_rate, 4),
            "provider_counts": db_stats["provider_counts"],
            "queue": queue_stats,
        }


# 全局通知服务实例
notification_service = NotificationService()
