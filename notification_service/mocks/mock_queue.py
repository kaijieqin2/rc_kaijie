"""
Mock消息队列实现
使用内存队列模拟RabbitMQ/Kafka
"""
import time
from collections import deque
from typing import Any, Optional, Dict, Callable
from threading import Lock, Thread
from dataclasses import dataclass
from observability.logger import logger


@dataclass
class Message:
    """队列消息"""
    id: str
    payload: Any
    enqueued_at: float
    retry_count: int = 0


class MockQueue:
    """Mock消息队列 - 使用内存队列"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._queue = deque()
        self._processing: Dict[str, Message] = {}
        self._lock = Lock()
        self._running = False
        self._worker_thread: Optional[Thread] = None
        self._handler: Optional[Callable] = None

    def enqueue(self, message_id: str, payload: Any) -> bool:
        """入队消息"""
        with self._lock:
            message = Message(
                id=message_id,
                payload=payload,
                enqueued_at=time.time(),
            )
            self._queue.append(message)
            logger.info(f"Message enqueued: {message_id}", extra={"queue": self.name})
            return True

    def dequeue(self, timeout: float = 1.0) -> Optional[Message]:
        """出队消息 (阻塞)"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._lock:
                if self._queue:
                    message = self._queue.popleft()
                    self._processing[message.id] = message
                    return message
            time.sleep(0.1)
        return None

    def ack(self, message_id: str) -> bool:
        """确认消息处理成功"""
        with self._lock:
            if message_id in self._processing:
                del self._processing[message_id]
                logger.debug(f"Message acknowledged: {message_id}")
                return True
            return False

    def nack(self, message_id: str, requeue: bool = True) -> bool:
        """拒绝消息 (可选重新入队)"""
        with self._lock:
            if message_id not in self._processing:
                return False

            message = self._processing[message_id]
            del self._processing[message_id]

            if requeue:
                message.retry_count += 1
                self._queue.append(message)
                logger.warning(
                    f"Message nacked and requeued: {message_id}, retry: {message.retry_count}"
                )
            else:
                logger.warning(f"Message nacked and dropped: {message_id}")

            return True

    def size(self) -> int:
        """获取队列大小"""
        with self._lock:
            return len(self._queue)

    def processing_count(self) -> int:
        """获取正在处理的消息数"""
        with self._lock:
            return len(self._processing)

    def register_handler(self, handler: Callable[[Message], bool]):
        """注册消息处理器"""
        self._handler = handler

    def start_worker(self):
        """启动worker线程处理消息"""
        if self._running:
            return

        if not self._handler:
            raise ValueError("No handler registered")

        self._running = True
        self._worker_thread = Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info(f"Queue worker started: {self.name}")

    def stop_worker(self):
        """停止worker线程"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
            logger.info(f"Queue worker stopped: {self.name}")

    def _worker_loop(self):
        """Worker循环"""
        while self._running:
            message = self.dequeue(timeout=0.5)
            if message:
                try:
                    success = self._handler(message)
                    if success:
                        self.ack(message.id)
                    else:
                        # 失败则重新入队
                        self.nack(message.id, requeue=True)
                except Exception as e:
                    logger.error(f"Handler error for message {message.id}: {e}")
                    self.nack(message.id, requeue=True)

    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        with self._lock:
            return {
                "name": self.name,
                "queue_size": len(self._queue),
                "processing_count": len(self._processing),
                "worker_running": self._running,
            }

    def clear_all(self):
        """清空队列"""
        with self._lock:
            self._queue.clear()
            self._processing.clear()


class MockQueueManager:
    """Mock队列管理器 - 管理多个队列"""

    def __init__(self):
        self._queues: Dict[str, MockQueue] = {}
        self._lock = Lock()

    def get_queue(self, name: str) -> MockQueue:
        """获取或创建队列"""
        with self._lock:
            if name not in self._queues:
                self._queues[name] = MockQueue(name)
            return self._queues[name]

    def list_queues(self) -> list[str]:
        """列出所有队列"""
        with self._lock:
            return list(self._queues.keys())

    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有队列统计"""
        with self._lock:
            return {name: queue.get_stats() for name, queue in self._queues.items()}


# 全局队列管理器
queue_manager = MockQueueManager()


# 获取默认队列
def get_default_queue() -> MockQueue:
    """获取默认通知队列"""
    return queue_manager.get_queue("notifications")
