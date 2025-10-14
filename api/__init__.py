# API接口模块
"""
API接口模块

提供FastAPI应用的路由聚合与导出，包含：
- 问答路由
- 多模态路由（语音/图像/触觉）
- 分析路由（反馈分析、热力图等）
- 健康路由
"""

from .routes import qa_routes, multimodal_routes, analytics_routes, health_routes

__all__ = [
    "qa_routes",
    "multimodal_routes",
    "analytics_routes",
    "health_routes",
]
