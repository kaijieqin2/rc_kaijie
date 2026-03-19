"""
可观测性 - 日志模块
提供结构化日志功能
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from config.settings import settings


class JSONFormatter(logging.Formatter):
    """JSON格式日志formatter"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "notification_id"):
            log_data["notification_id"] = record.notification_id
        if hasattr(record, "provider"):
            log_data["provider"] = record.provider
        if hasattr(record, "status"):
            log_data["status"] = record.status

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str = None) -> logging.Logger:
    """设置日志记录器"""
    logger_name = name or settings.app_name
    logger = logging.getLogger(logger_name)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # 创建控制台handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))

    # 设置格式
    if settings.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# 全局logger实例
logger = setup_logger()


def log_with_context(level: str, message: str, **kwargs):
    """带上下文的日志记录"""
    log_func = getattr(logger, level.lower())
    log_func(message, extra=kwargs)
