"""
核心 - 重试策略
"""
from datetime import datetime, timedelta
from config.settings import settings


class RetryStrategy:
    """重试策略"""

    @staticmethod
    def should_retry(status_code: int, retry_count: int) -> bool:
        """判断是否应该重试"""
        # 超过最大重试次数
        if retry_count >= settings.retry.max_retry:
            return False

        # 4xx错误 (客户端错误) - 不重试
        if 400 <= status_code < 500 and status_code != 408 and status_code != 429:
            return False

        # 5xx错误, 408超时, 429限流, 或连接错误 - 应重试
        if status_code >= 500 or status_code in [408, 429, 0]:
            return True

        # 2xx成功 - 不需要重试
        if 200 <= status_code < 300:
            return False

        # 其他情况默认不重试
        return False

    @staticmethod
    def calculate_next_retry_time(retry_count: int) -> datetime:
        """计算下次重试时间 (指数退避)"""
        delay_seconds = settings.retry.get_retry_delay(retry_count)
        return datetime.utcnow() + timedelta(seconds=delay_seconds)

    @staticmethod
    def is_permanent_failure(status_code: int) -> bool:
        """判断是否是永久失败"""
        # 4xx错误 (除了408, 429) 认为是永久失败
        return 400 <= status_code < 500 and status_code not in [408, 429]
