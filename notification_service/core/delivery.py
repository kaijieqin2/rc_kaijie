"""
核心 - 投递逻辑
处理HTTP通知投递
"""
import time
from typing import Dict, Any, Tuple
from datetime import datetime
from config.settings import settings
from mocks.mock_db import db
from mocks.mock_providers import provider_manager
from observability.logger import logger
from observability.metrics import metrics
from core.retry import RetryStrategy


class DeliveryService:
    """投递服务"""

    def __init__(self):
        self.retry_strategy = RetryStrategy()

    def deliver(self, notification_id: str) -> Tuple[bool, str]:
        """投递通知"""
        # 获取通知记录
        notification = db.get_notification(notification_id)
        if not notification:
            error_msg = f"Notification not found: {notification_id}"
            logger.error(error_msg)
            return False, error_msg

        # 更新状态为处理中
        db.update_notification(notification_id, {"status": "processing"})
        metrics.record_notification_processing()

        provider_name = notification["provider"]
        retry_count = notification["retry_count"]

        logger.info(
            f"Starting delivery for notification {notification_id}",
            extra={
                "notification_id": notification_id,
                "provider": provider_name,
                "retry_count": retry_count,
            },
        )

        try:
            # 获取供应商配置
            provider_config = settings.get_provider(provider_name)
        except ValueError as e:
            error_msg = str(e)
            logger.error(error_msg, extra={"notification_id": notification_id})
            self._handle_permanent_failure(notification_id, 0, error_msg)
            return False, error_msg

        # 执行投递
        start_time = time.time()
        try:
            # 使用Mock供应商API
            provider_api = provider_manager.get_provider(provider_config)

            # 准备请求
            headers = {**provider_config.headers, **notification.get("headers", {})}
            body = notification.get("body", {})

            # 发送请求
            response = provider_api.send_notification(headers, body)
            duration_ms = response.elapsed_ms

            # 记录投递日志
            self._create_delivery_log(
                notification_id=notification_id,
                attempt=retry_count + 1,
                status_code=response.status_code,
                response=response.text,
                duration_ms=duration_ms,
            )

            # 记录指标
            success = 200 <= response.status_code < 300
            metrics.record_delivery(
                provider=provider_name,
                duration=duration_ms,
                success=success,
                retry_count=retry_count,
            )

            # 处理响应
            if success:
                return self._handle_success(notification_id, response)
            else:
                return self._handle_failure(
                    notification_id, response.status_code, response.text, retry_count
                )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Delivery exception: {str(e)}"
            logger.error(
                error_msg,
                extra={"notification_id": notification_id, "provider": provider_name},
                exc_info=True,
            )

            # 记录投递日志
            self._create_delivery_log(
                notification_id=notification_id,
                attempt=retry_count + 1,
                status_code=0,
                error=error_msg,
                duration_ms=duration_ms,
            )

            # 异常视为临时错误，可重试
            return self._handle_failure(notification_id, 0, error_msg, retry_count)

    def _handle_success(self, notification_id: str, response: Any) -> Tuple[bool, str]:
        """处理投递成功"""
        now = datetime.utcnow()
        db.update_notification(
            notification_id,
            {"status": "success", "delivered_at": now, "error": None},
        )

        metrics.record_notification_completed(success=True)

        logger.info(
            f"Notification delivered successfully: {notification_id}",
            extra={"notification_id": notification_id, "status": "success"},
        )

        return True, "Delivered successfully"

    def _handle_failure(
        self, notification_id: str, status_code: int, error: str, retry_count: int
    ) -> Tuple[bool, str]:
        """处理投递失败"""
        # 判断是否应该重试
        should_retry = self.retry_strategy.should_retry(status_code, retry_count)
        is_permanent = self.retry_strategy.is_permanent_failure(status_code)

        if is_permanent or not should_retry:
            return self._handle_permanent_failure(notification_id, status_code, error)
        else:
            return self._handle_temporary_failure(notification_id, status_code, error, retry_count)

    def _handle_permanent_failure(
        self, notification_id: str, status_code: int, error: str
    ) -> Tuple[bool, str]:
        """处理永久失败"""
        db.update_notification(
            notification_id,
            {"status": "failed", "error": error},
        )

        metrics.record_notification_completed(success=False)

        logger.warning(
            f"Notification permanently failed: {notification_id}",
            extra={
                "notification_id": notification_id,
                "status": "failed",
                "status_code": status_code,
                "error": error,
            },
        )

        return False, f"Permanently failed: {error}"

    def _handle_temporary_failure(
        self, notification_id: str, status_code: int, error: str, retry_count: int
    ) -> Tuple[bool, str]:
        """处理临时失败，安排重试"""
        new_retry_count = retry_count + 1
        next_retry_at = self.retry_strategy.calculate_next_retry_time(new_retry_count)

        db.update_notification(
            notification_id,
            {
                "status": "pending",
                "retry_count": new_retry_count,
                "next_retry_at": next_retry_at,
                "error": error,
            },
        )

        # 将状态从processing改回pending
        metrics.record_notification_processing()  # 先减processing
        metrics.notifications_pending.inc()  # 再加pending

        logger.info(
            f"Notification scheduled for retry: {notification_id}",
            extra={
                "notification_id": notification_id,
                "retry_count": new_retry_count,
                "next_retry_at": next_retry_at.isoformat(),
                "status_code": status_code,
            },
        )

        return False, f"Temporary failure, will retry at {next_retry_at}"

    def _create_delivery_log(
        self,
        notification_id: str,
        attempt: int,
        status_code: int = None,
        response: str = None,
        error: str = None,
        duration_ms: float = 0,
    ):
        """创建投递日志"""
        log_data = {
            "notification_id": notification_id,
            "attempt": attempt,
            "status_code": status_code,
            "response": response,
            "error": error,
            "duration_ms": duration_ms,
        }
        db.create_delivery_log(log_data)


# 全局投递服务实例
delivery_service = DeliveryService()
