"""
API routes - 路由处理
"""
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.schemas import (
    CreateNotificationRequest,
    CreateNotificationResponse,
    NotificationDetail,
    NotificationList,
    DeliveryLogList,
    Statistics,
    HealthResponse,
    ErrorResponse,
)
from core.notification import notification_service
from observability.logger import logger
from observability.metrics import metrics
from config.settings import settings

router = APIRouter()


@router.post(
    "/notifications",
    response_model=CreateNotificationResponse,
    status_code=201,
    summary="创建通知",
    description="提交一个新的通知请求，系统将异步投递到目标供应商"
)
async def create_notification(request: CreateNotificationRequest):
    """创建通知"""
    start_time = time.time()

    try:
        result = notification_service.create_notification(request.model_dump())
        duration = time.time() - start_time
        metrics.record_request(duration, success=True)

        return CreateNotificationResponse(**result)

    except ValueError as e:
        duration = time.time() - start_time
        metrics.record_request(duration, success=False)
        logger.error(f"Create notification failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        duration = time.time() - start_time
        metrics.record_request(duration, success=False)
        logger.error(f"Create notification error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationDetail,
    summary="获取通知详情",
    description="根据通知ID获取通知的详细信息"
)
async def get_notification(notification_id: str):
    """获取通知详情"""
    try:
        result = notification_service.get_notification(notification_id)
        return NotificationDetail(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Get notification error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/notifications",
    response_model=NotificationList,
    summary="列出通知",
    description="列出通知记录，支持按状态和供应商过滤"
)
async def list_notifications(
    status: Optional[str] = Query(None, description="按状态过滤: pending/processing/success/failed"),
    provider: Optional[str] = Query(None, description="按供应商过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """列出通知"""
    try:
        result = notification_service.list_notifications(status, provider, limit, offset)
        return NotificationList(**result)

    except Exception as e:
        logger.error(f"List notifications error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/notifications/{notification_id}/logs",
    response_model=DeliveryLogList,
    summary="获取投递日志",
    description="获取指定通知的所有投递尝试日志"
)
async def get_delivery_logs(notification_id: str):
    """获取投递日志"""
    try:
        result = notification_service.get_delivery_logs(notification_id)
        return DeliveryLogList(**result)

    except Exception as e:
        logger.error(f"Get delivery logs error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/stats",
    response_model=Statistics,
    summary="获取统计信息",
    description="获取系统整体统计信息，包括成功率、各供应商统计等"
)
async def get_statistics():
    """获取统计信息"""
    try:
        result = notification_service.get_statistics()
        return Statistics(**result)

    except Exception as e:
        logger.error(f"Get statistics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/metrics",
    summary="获取监控指标",
    description="获取详细的监控指标数据"
)
async def get_metrics():
    """获取监控指标"""
    try:
        return metrics.get_all_metrics()

    except Exception as e:
        logger.error(f"Get metrics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查服务健康状态"
)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        version=settings.version,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
