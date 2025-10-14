# 交互协调模块
"""
多模态交互协调模块

导出多模态编排与UI渲染相关组件：
- MultimodalCoordinator：处理语音/视觉/触觉协同
- UserInterface：将多模态结果渲染为UI数据
"""

from .multimodal_coordinator import MultimodalCoordinator
from .user_interface import UserInterface

__all__ = [
    "MultimodalCoordinator",
    "UserInterface",
]
