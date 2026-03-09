# API路由模块
"""
API路由模块

包含所有API端点的路由定义。
"""

# 核心路由（必需）
from . import qa_routes
from . import analytics_routes
from . import project_routes
from . import runtime_routes

# 可选路由（可能不存在）
try:
    from . import health_routes
except ImportError:
    health_routes = None

try:
    from . import multimodal_routes
except ImportError:
    multimodal_routes = None

__all__ = [
    "qa_routes",
    "analytics_routes",
    "project_routes",
    "runtime_routes",
    "health_routes",
    "multimodal_routes"
]
