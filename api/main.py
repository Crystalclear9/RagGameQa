# 主API入口
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from api.routes import qa_routes, analytics_routes
from config.settings import settings

# 可选导入（如果模块不存在也不会报错）
try:
    from api.routes import multimodal_routes
    HAS_MULTIMODAL = True
except ImportError:
    HAS_MULTIMODAL = False
    multimodal_routes = None

try:
    from api.routes import health_routes
    HAS_HEALTH = True
except ImportError:
    HAS_HEALTH = False
    health_routes = None

# 配置日志
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Game QA System",
    description="基于RAG的游戏问答系统",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "服务器内部错误，请稍后重试",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )

# 注册核心路由
app.include_router(qa_routes.router, prefix="/api/v1/qa", tags=["问答"])
app.include_router(analytics_routes.router, prefix="/api/v1/analytics", tags=["分析"])

# 注册可选路由
if HAS_MULTIMODAL and multimodal_routes:
    app.include_router(multimodal_routes.router, prefix="/api/v1/multimodal", tags=["多模态"])
    logger.info("已加载多模态路由")

if HAS_HEALTH and health_routes:
    app.include_router(health_routes.router, prefix="/api/v1/health", tags=["健康"])
    logger.info("已加载健康管理路由")

@app.get("/")
async def root():
    return {
        "message": "RAG Game QA System API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": {
            "qa": True,
            "analytics": True,
            "multimodal": HAS_MULTIMODAL,
            "health": HAS_HEALTH
        }
    }

@app.get("/health")
async def health_check():
    """基础健康检查"""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT, log_level=settings.LOG_LEVEL)
