"""
FastAPI主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings, load_settings_from_env
from api.routes import router
from observability.logger import logger
from workers.delivery_worker import start_delivery_worker, stop_delivery_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")

    # 启动投递worker
    start_delivery_worker()
    logger.info("Delivery worker started")

    yield

    # 关闭时
    logger.info("Shutting down...")
    stop_delivery_worker()
    logger.info("Delivery worker stopped")


# 创建FastAPI应用
app = FastAPI(
    title="HTTP通知投递服务",
    description="接收业务系统提交的外部HTTP通知请求，并可靠地投递到目标地址",
    version=settings.version,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix=settings.api_prefix, tags=["notifications"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn

    # 加载环境变量配置
    load_settings_from_env()

    # 启动服务
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
