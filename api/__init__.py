# API接口模块
"""
API接口模块

提供FastAPI应用的路由聚合与导出，包含：
- 问答路由（核心）
- 分析路由（核心）
- 多模态路由（可选）
- 健康路由（可选）
"""

# 导入核心路由
from .routes import qa_routes, analytics_routes

# 可选导入其他路由
try:
    from .routes import multimodal_routes
except ImportError:
    multimodal_routes = None

try:
    from .routes import health_routes
except ImportError:
    health_routes = None

__all__ = [
    "qa_routes",
    "analytics_routes",
    "multimodal_routes",
    "health_routes",
]
