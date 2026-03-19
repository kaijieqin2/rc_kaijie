"""
投递Worker
处理队列中的投递任务
"""
from mocks.mock_queue import get_default_queue, Message
from core.delivery import delivery_service
from observability.logger import logger
from observability.metrics import metrics


def handle_delivery_message(message: Message) -> bool:
    """处理投递消息"""
    try:
        notification_id = message.payload.get("notification_id")
        if not notification_id:
            logger.error("Invalid message: missing notification_id")
            return False

        logger.info(f"Processing delivery for notification: {notification_id}")

        # 执行投递
        success, error_msg = delivery_service.deliver(notification_id)

        # 更新队列指标
        metrics.queue_dequeued.inc()
        metrics.queue_size.dec()

        if success:
            logger.info(f"Delivery successful: {notification_id}")
        else:
            logger.warning(f"Delivery failed: {notification_id}, reason: {error_msg}")

        return success

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return False


_worker_started = False


def start_delivery_worker():
    """启动投递worker"""
    global _worker_started
    if _worker_started:
        return

    queue = get_default_queue()
    queue.register_handler(handle_delivery_message)
    queue.start_worker()

    _worker_started = True
    logger.info("Delivery worker started")


def stop_delivery_worker():
    """停止投递worker"""
    global _worker_started
    if not _worker_started:
        return

    queue = get_default_queue()
    queue.stop_worker()

    _worker_started = False
    logger.info("Delivery worker stopped")
