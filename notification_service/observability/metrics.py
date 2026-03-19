"""
可观测性 - 指标模块
收集和统计系统指标
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List
from threading import Lock
from collections import defaultdict


@dataclass
class Counter:
    """计数器"""
    value: int = 0
    _lock: Lock = field(default_factory=Lock)

    def inc(self, delta: int = 1):
        """增加计数"""
        with self._lock:
            self.value += delta

    def get(self) -> int:
        """获取当前值"""
        with self._lock:
            return self.value


@dataclass
class Gauge:
    """仪表盘 - 可增可减的值"""
    value: float = 0.0
    _lock: Lock = field(default_factory=Lock)

    def set(self, value: float):
        """设置值"""
        with self._lock:
            self.value = value

    def inc(self, delta: float = 1.0):
        """增加"""
        with self._lock:
            self.value += delta

    def dec(self, delta: float = 1.0):
        """减少"""
        with self._lock:
            self.value -= delta

    def get(self) -> float:
        """获取当前值"""
        with self._lock:
            return self.value


@dataclass
class Histogram:
    """直方图 - 记录数值分布"""
    values: List[float] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock)

    def observe(self, value: float):
        """记录一个观测值"""
        with self._lock:
            self.values.append(value)
            # 保持最近1000个值
            if len(self.values) > 1000:
                self.values = self.values[-1000:]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            if not self.values:
                return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}

            sorted_values = sorted(self.values)
            count = len(sorted_values)
            total = sum(sorted_values)

            return {
                "count": count,
                "sum": total,
                "avg": total / count,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "p50": sorted_values[int(count * 0.5)],
                "p95": sorted_values[int(count * 0.95)] if count > 20 else sorted_values[-1],
                "p99": sorted_values[int(count * 0.99)] if count > 100 else sorted_values[-1],
            }


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        # 请求指标
        self.requests_total = Counter()
        self.requests_success = Counter()
        self.requests_failed = Counter()
        self.request_duration = Histogram()

        # 通知指标
        self.notifications_created = Counter()
        self.notifications_pending = Gauge()
        self.notifications_processing = Gauge()
        self.notifications_success = Counter()
        self.notifications_failed = Counter()

        # 投递指标
        self.delivery_attempts = Counter()
        self.delivery_success = Counter()
        self.delivery_failed = Counter()
        self.delivery_duration = Histogram()
        self.delivery_retry_count = Histogram()

        # 按供应商统计
        self.provider_success: Dict[str, Counter] = defaultdict(Counter)
        self.provider_failed: Dict[str, Counter] = defaultdict(Counter)
        self.provider_duration: Dict[str, Histogram] = defaultdict(Histogram)

        # 队列指标
        self.queue_size = Gauge()
        self.queue_enqueued = Counter()
        self.queue_dequeued = Counter()

    def record_request(self, duration: float, success: bool = True):
        """记录API请求"""
        self.requests_total.inc()
        self.request_duration.observe(duration)
        if success:
            self.requests_success.inc()
        else:
            self.requests_failed.inc()

    def record_notification_created(self):
        """记录通知创建"""
        self.notifications_created.inc()
        self.notifications_pending.inc()

    def record_notification_processing(self):
        """记录通知开始处理"""
        self.notifications_pending.dec()
        self.notifications_processing.inc()

    def record_notification_completed(self, success: bool):
        """记录通知完成"""
        self.notifications_processing.dec()
        if success:
            self.notifications_success.inc()
        else:
            self.notifications_failed.inc()

    def record_delivery(self, provider: str, duration: float, success: bool, retry_count: int = 0):
        """记录投递"""
        self.delivery_attempts.inc()
        self.delivery_duration.observe(duration)
        self.delivery_retry_count.observe(retry_count)

        self.provider_duration[provider].observe(duration)

        if success:
            self.delivery_success.inc()
            self.provider_success[provider].inc()
        else:
            self.delivery_failed.inc()
            self.provider_failed[provider].inc()

    def get_all_metrics(self) -> Dict:
        """获取所有指标"""
        metrics = {
            "requests": {
                "total": self.requests_total.get(),
                "success": self.requests_success.get(),
                "failed": self.requests_failed.get(),
                "duration": self.request_duration.get_stats(),
            },
            "notifications": {
                "created": self.notifications_created.get(),
                "pending": self.notifications_pending.get(),
                "processing": self.notifications_processing.get(),
                "success": self.notifications_success.get(),
                "failed": self.notifications_failed.get(),
            },
            "delivery": {
                "attempts": self.delivery_attempts.get(),
                "success": self.delivery_success.get(),
                "failed": self.delivery_failed.get(),
                "duration": self.delivery_duration.get_stats(),
                "retry_count": self.delivery_retry_count.get_stats(),
            },
            "queue": {
                "size": self.queue_size.get(),
                "enqueued": self.queue_enqueued.get(),
                "dequeued": self.queue_dequeued.get(),
            },
            "providers": {}
        }

        # 添加各供应商指标
        for provider in set(list(self.provider_success.keys()) + list(self.provider_failed.keys())):
            metrics["providers"][provider] = {
                "success": self.provider_success[provider].get(),
                "failed": self.provider_failed[provider].get(),
                "duration": self.provider_duration[provider].get_stats(),
            }

        return metrics


# 全局指标收集器
metrics = MetricsCollector()
