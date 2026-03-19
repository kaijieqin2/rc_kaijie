"""
Mock数据库实现
使用内存字典模拟PostgreSQL数据库
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from threading import Lock
from copy import deepcopy


class MockDatabase:
    """Mock数据库 - 使用内存存储"""

    def __init__(self):
        self._notifications: Dict[str, Dict[str, Any]] = {}
        self._delivery_logs: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def create_notification(self, notification_data: Dict[str, Any]) -> str:
        """创建通知记录"""
        with self._lock:
            notification_id = str(uuid.uuid4())
            now = datetime.utcnow()

            notification = {
                "id": notification_id,
                "business_system": notification_data["business_system"],
                "event_type": notification_data["event_type"],
                "provider": notification_data["provider"],
                "target_url": notification_data.get("target_url", ""),
                "headers": notification_data.get("headers", {}),
                "body": notification_data.get("body", {}),
                "status": "pending",
                "retry_count": 0,
                "max_retry": notification_data.get("max_retry", 7),
                "next_retry_at": None,
                "created_at": now,
                "updated_at": now,
                "delivered_at": None,
                "error": None,
            }

            self._notifications[notification_id] = notification
            return notification_id

    def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """获取通知记录"""
        with self._lock:
            return deepcopy(self._notifications.get(notification_id))

    def update_notification(self, notification_id: str, updates: Dict[str, Any]) -> bool:
        """更新通知记录"""
        with self._lock:
            if notification_id not in self._notifications:
                return False

            notification = self._notifications[notification_id]
            notification.update(updates)
            notification["updated_at"] = datetime.utcnow()
            return True

    def list_notifications(
        self,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出通知记录"""
        with self._lock:
            results = []
            for notification in self._notifications.values():
                # 应用过滤器
                if status and notification["status"] != status:
                    continue
                if provider and notification["provider"] != provider:
                    continue
                results.append(deepcopy(notification))

            # 按创建时间倒序排序
            results.sort(key=lambda x: x["created_at"], reverse=True)

            # 分页
            return results[offset : offset + limit]

    def get_pending_retries(self, current_time: datetime) -> List[Dict[str, Any]]:
        """获取需要重试的通知"""
        with self._lock:
            results = []
            for notification in self._notifications.values():
                if (
                    notification["status"] == "pending"
                    and notification["next_retry_at"]
                    and notification["next_retry_at"] <= current_time
                ):
                    results.append(deepcopy(notification))
            return results

    def create_delivery_log(self, log_data: Dict[str, Any]) -> str:
        """创建投递日志"""
        with self._lock:
            log_id = str(uuid.uuid4())
            now = datetime.utcnow()

            log_entry = {
                "id": log_id,
                "notification_id": log_data["notification_id"],
                "attempt": log_data["attempt"],
                "status_code": log_data.get("status_code"),
                "response": log_data.get("response", ""),
                "error": log_data.get("error"),
                "duration_ms": log_data.get("duration_ms", 0),
                "created_at": now,
            }

            self._delivery_logs[log_id] = log_entry
            return log_id

    def get_delivery_logs(
        self, notification_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取通知的投递日志"""
        with self._lock:
            results = []
            for log in self._delivery_logs.values():
                if log["notification_id"] == notification_id:
                    results.append(deepcopy(log))

            # 按创建时间排序
            results.sort(key=lambda x: x["created_at"])
            return results[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = len(self._notifications)
            status_counts = {"pending": 0, "processing": 0, "success": 0, "failed": 0}
            provider_counts = {}

            for notification in self._notifications.values():
                status = notification["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

                provider = notification["provider"]
                if provider not in provider_counts:
                    provider_counts[provider] = {"total": 0, "success": 0, "failed": 0}
                provider_counts[provider]["total"] += 1
                if status == "success":
                    provider_counts[provider]["success"] += 1
                elif status == "failed":
                    provider_counts[provider]["failed"] += 1

            return {
                "total_notifications": total,
                "status_counts": status_counts,
                "provider_counts": provider_counts,
                "total_delivery_logs": len(self._delivery_logs),
            }

    def clear_all(self):
        """清空所有数据 (用于测试)"""
        with self._lock:
            self._notifications.clear()
            self._delivery_logs.clear()


# 全局数据库实例
db = MockDatabase()
