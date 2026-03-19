"""
Mock供应商API实现
模拟外部供应商HTTP API
"""
import random
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from config.settings import ProviderConfig
from observability.logger import logger


@dataclass
class MockHTTPResponse:
    """Mock HTTP响应"""
    status_code: int
    text: str
    json_data: Optional[Dict[str, Any]] = None
    elapsed_ms: float = 0

    def json(self) -> Dict[str, Any]:
        """返回JSON数据"""
        return self.json_data or {}


class MockProviderAPI:
    """Mock供应商API"""

    def __init__(self, provider_config: ProviderConfig):
        self.config = provider_config
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0

    def send_notification(self, headers: Dict[str, str], body: Dict[str, Any]) -> MockHTTPResponse:
        """发送通知 (Mock)"""
        self.request_count += 1

        # 模拟网络延迟
        delay = self.config.mock_response_delay
        if delay > 0:
            time.sleep(delay)

        # 根据配置的成功率决定是否成功
        success = random.random() < self.config.mock_success_rate

        elapsed_ms = delay * 1000

        if success:
            self.success_count += 1
            # 模拟成功响应
            return MockHTTPResponse(
                status_code=200,
                text='{"status": "ok", "message": "Notification received"}',
                json_data={"status": "ok", "message": "Notification received", "id": f"mock_{self.request_count}"},
                elapsed_ms=elapsed_ms,
            )
        else:
            self.failure_count += 1
            # 随机返回不同类型的错误
            error_type = random.choice(["server_error", "timeout", "bad_request"])

            if error_type == "server_error":
                return MockHTTPResponse(
                    status_code=500,
                    text='{"error": "Internal server error"}',
                    json_data={"error": "Internal server error"},
                    elapsed_ms=elapsed_ms,
                )
            elif error_type == "timeout":
                return MockHTTPResponse(
                    status_code=504,
                    text='{"error": "Gateway timeout"}',
                    json_data={"error": "Gateway timeout"},
                    elapsed_ms=self.config.timeout * 1000,
                )
            else:  # bad_request
                return MockHTTPResponse(
                    status_code=400,
                    text='{"error": "Bad request"}',
                    json_data={"error": "Bad request"},
                    elapsed_ms=elapsed_ms,
                )

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "provider": self.config.name,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / self.request_count if self.request_count > 0 else 0,
        }


class MockProviderManager:
    """Mock供应商管理器"""

    def __init__(self):
        self._providers: Dict[str, MockProviderAPI] = {}

    def get_provider(self, provider_config: ProviderConfig) -> MockProviderAPI:
        """获取或创建供应商API实例"""
        if provider_config.name not in self._providers:
            self._providers[provider_config.name] = MockProviderAPI(provider_config)
            logger.info(f"Created mock provider: {provider_config.name}")
        return self._providers[provider_config.name]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有供应商统计"""
        return {name: provider.get_stats() for name, provider in self._providers.items()}


# 全局供应商管理器
provider_manager = MockProviderManager()
