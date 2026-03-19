"""
配置管理模块
支持从环境变量和配置文件加载配置
"""
import os
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class RetryConfig:
    """重试配置"""
    max_retry: int = 7
    initial_delay: int = 1  # 秒
    max_delay: int = 64  # 秒
    timeout: int = 30  # 秒

    def get_retry_delay(self, retry_count: int) -> int:
        """计算指数退避延迟"""
        delay = self.initial_delay * (2 ** retry_count)
        return min(delay, self.max_delay)


@dataclass
class ProviderConfig:
    """供应商配置"""
    name: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    auth_type: str = "none"  # none, bearer, basic, api_key
    auth_token: str = ""
    timeout: int = 30

    # Mock配置 - 控制Mock行为
    mock_enabled: bool = True
    mock_success_rate: float = 0.8  # 80%成功率
    mock_response_delay: float = 0.1  # 100ms延迟


@dataclass
class SystemConfig:
    """系统配置"""
    # 应用配置
    app_name: str = "notification-service"
    version: str = "1.0.0"
    environment: str = "development"

    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # 数据库配置 (Mock)
    db_type: str = "mock"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "notifications"

    # 缓存配置 (Mock)
    cache_type: str = "mock"
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_ttl: int = 3600  # 1小时

    # 队列配置 (Mock)
    queue_type: str = "mock"
    queue_host: str = "localhost"
    queue_port: int = 5672
    queue_name: str = "notifications"

    # 重试配置
    retry: RetryConfig = field(default_factory=RetryConfig)

    # 供应商配置
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    # 监控配置
    enable_metrics: bool = True
    metrics_port: int = 9090

    def __post_init__(self):
        """初始化后加载供应商配置"""
        if not self.providers:
            self.providers = self._load_default_providers()

    def _load_default_providers(self) -> Dict[str, ProviderConfig]:
        """加载默认供应商配置"""
        return {
            "ad_provider_a": ProviderConfig(
                name="ad_provider_a",
                url="https://api.adprovider-a.com/webhook",
                headers={"Content-Type": "application/json"},
                auth_type="bearer",
                auth_token="mock_token_ad_a",
                mock_success_rate=0.9
            ),
            "ad_provider_b": ProviderConfig(
                name="ad_provider_b",
                url="https://api.adprovider-b.com/notify",
                headers={"Content-Type": "application/json", "X-API-Key": "mock_key_b"},
                auth_type="api_key",
                mock_success_rate=0.85
            ),
            "crm_system": ProviderConfig(
                name="crm_system",
                url="https://crm.example.com/api/contacts/update",
                headers={"Content-Type": "application/json"},
                auth_type="bearer",
                auth_token="mock_token_crm",
                mock_success_rate=0.95
            ),
            "inventory_system": ProviderConfig(
                name="inventory_system",
                url="https://inventory.example.com/api/stock/update",
                headers={"Content-Type": "application/json"},
                auth_type="basic",
                auth_token="mock_basic_auth",
                mock_success_rate=0.92
            )
        }

    def get_provider(self, provider_name: str) -> ProviderConfig:
        """获取供应商配置"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self.providers[provider_name]


# 全局配置实例
settings = SystemConfig()


def load_settings_from_env():
    """从环境变量加载配置"""
    global settings

    # 从环境变量覆盖配置
    settings.environment = os.getenv("ENVIRONMENT", settings.environment)
    settings.api_host = os.getenv("API_HOST", settings.api_host)
    settings.api_port = int(os.getenv("API_PORT", settings.api_port))
    settings.log_level = os.getenv("LOG_LEVEL", settings.log_level)

    return settings
