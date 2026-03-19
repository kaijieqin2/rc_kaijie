"""
Mock缓存实现
使用内存字典模拟Redis缓存
"""
import time
from typing import Any, Optional, Dict
from threading import Lock


class MockCache:
    """Mock缓存 - 使用内存存储"""

    def __init__(self):
        self._data: Dict[str, tuple[Any, Optional[float]]] = {}  # key -> (value, expire_time)
        self._lock = Lock()

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        with self._lock:
            expire_time = time.time() + ttl if ttl else None
            self._data[key] = (value, expire_time)
            return True

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._data:
                return None

            value, expire_time = self._data[key]

            # 检查是否过期
            if expire_time and time.time() > expire_time:
                del self._data[key]
                return None

            return value

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        return self.get(key) is not None

    def incr(self, key: str, delta: int = 1) -> int:
        """增加计数"""
        with self._lock:
            current_value = self.get(key) or 0
            new_value = int(current_value) + delta
            self.set(key, new_value)
            return new_value

    def decr(self, key: str, delta: int = 1) -> int:
        """减少计数"""
        return self.incr(key, -delta)

    def clear_all(self):
        """清空所有缓存"""
        with self._lock:
            self._data.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            # 清理过期key
            current_time = time.time()
            expired_keys = [
                key
                for key, (_, expire_time) in self._data.items()
                if expire_time and current_time > expire_time
            ]
            for key in expired_keys:
                del self._data[key]

            return {
                "total_keys": len(self._data),
                "expired_keys_cleaned": len(expired_keys),
            }


# 全局缓存实例
cache = MockCache()
