import logging
import sys
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from api.routes import analytics_routes, project_routes, qa_routes, runtime_routes
from config.database import create_tables, database_status
from config.runtime_config import load_persisted_runtime_config
from config.settings import settings
from utils.security import redact_sensitive_text

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

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Game QA System",
    description="基于 RAG 的游戏类问答智能体",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

frontend_dir = root_dir / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ALLOW_ORIGINS if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def secure_request_middleware(request: Request, call_next):
    request_id = uuid4().hex[:12]
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "microphone=(), camera=(), geolocation=()"

    if request.url.path == "/app" or request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"

    logger.info(
        "[%s] %s %s - status=%s - time=%.3fs",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "")
    if exc.status_code >= 500:
        logger.warning(
            "[%s] HTTPException %s on %s: %s",
            request_id,
            exc.status_code,
            request.url.path,
            redact_sensitive_text(exc.detail),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": "服务器内部处理失败，请稍后重试。",
                "request_id": request_id,
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "")
    logger.error(
        "[%s] Global exception on %s: %s",
        request_id,
        request.url.path,
        redact_sensitive_text(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "服务器内部错误，请稍后重试。",
            "request_id": request_id,
        },
    )


@app.on_event("startup")
async def startup_event():
    create_tables()
    loaded_secure_runtime = load_persisted_runtime_config()
    logger.info("Database initialized: %s", database_status())
    logger.info("Secure runtime config loaded: %s", loaded_secure_runtime)


app.include_router(qa_routes.router, prefix="/api/v1/qa", tags=["问答"])
app.include_router(analytics_routes.router, prefix="/api/v1/analytics", tags=["分析"])
app.include_router(project_routes.router, prefix="/api/v1/project", tags=["项目展示"])
app.include_router(runtime_routes.router, prefix="/api/v1/runtime", tags=["运行时配置"])

if HAS_MULTIMODAL and multimodal_routes:
    app.include_router(multimodal_routes.router, prefix="/api/v1/multimodal", tags=["多模态"])
    logger.info("Loaded multimodal routes")

if HAS_HEALTH and health_routes:
    app.include_router(health_routes.router, prefix="/api/v1/health", tags=["健康"])
    logger.info("Loaded health routes")

if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="frontend-assets")

    @app.get("/app", include_in_schema=False)
    async def web_app():
        return FileResponse(frontend_dir / "index.html", media_type="text/html; charset=utf-8")


@app.get("/")
async def root():
    db_info = database_status()
    return {
        "message": "RAG Game QA System API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "web_ui": "/app" if frontend_dir.exists() else None,
        "features": {
            "qa": True,
            "analytics": True,
            "project_showcase": True,
            "runtime_config": True,
            "multimodal": HAS_MULTIMODAL,
            "health": HAS_HEALTH,
            "web_frontend": frontend_dir.exists(),
        },
        "database": db_info,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT, log_level=settings.LOG_LEVEL)
