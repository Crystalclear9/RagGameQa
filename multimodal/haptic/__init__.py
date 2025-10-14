# 触觉模块
"""
触觉交互模块

包含：
- 震动编码器（将语义反馈映射为震动模式）
- 反馈映射器（游戏动作→触觉反馈）
- 自适应控制器（兼容Xbox Adaptive Controller等设备）
"""

from .vibration_encoder import VibrationEncoder
from .feedback_mapper import FeedbackMapper
from .adaptive_controller import AdaptiveController

__all__ = [
    "VibrationEncoder",
    "FeedbackMapper",
    "AdaptiveController",
]
