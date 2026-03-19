"""
API schemas - 请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# 请求模型
class CreateNotificationRequest(BaseModel):
    """创建通知请求"""
    business_system: str = Field(..., description="业务系统名称")
    event_type: str = Field(..., description="事件类型")
    provider: str = Field(..., description="供应商名称")
    data: Dict[str, Any] = Field(..., description="通知数据")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "business_system": "user-service",
                    "event_type": "user_registered",
                    "provider": "ad_provider_a",
                    "data": {
                        "user_id": "12345",
                        "email": "user@example.com",
                        "registration_time": "2024-01-01T00:00:00Z"
                    }
                }
            ]
        }
    }


# 响应模型
class CreateNotificationResponse(BaseModel):
    """创建通知响应"""
    notification_id: str
    status: str
    created_at: str


class NotificationDetail(BaseModel):
    """通知详情"""
    id: str
    business_system: str
    event_type: str
    provider: str
    target_url: str
    headers: Dict[str, str]
    body: Dict[str, Any]
    status: str
    retry_count: int
    max_retry: int
    next_retry_at: Optional[str] = None
    created_at: str
    updated_at: str
    delivered_at: Optional[str] = None
    error: Optional[str] = None


class NotificationList(BaseModel):
    """通知列表"""
    notifications: List[NotificationDetail]
    count: int


class DeliveryLog(BaseModel):
    """投递日志"""
    id: str
    notification_id: str
    attempt: int
    status_code: Optional[int]
    response: Optional[str]
    error: Optional[str]
    duration_ms: float
    created_at: str


class DeliveryLogList(BaseModel):
    """投递日志列表"""
    logs: List[DeliveryLog]
    count: int


class Statistics(BaseModel):
    """统计信息"""
    total_notifications: int
    status_counts: Dict[str, int]
    success_rate: float
    provider_counts: Dict[str, Dict[str, int]]
    queue: Dict[str, Any]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
