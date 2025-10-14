# 视觉模块
"""
视觉处理模块

导出：
- ImageDescriptor：图像描述与空间定位
- UIElementDetector：UI元素检测
- AccessibilityHelper：无障碍辅助能力（AltText/语音导航）
"""

from .image_descriptor import ImageDescriptor
from .ui_element_detector import UIElementDetector
from .accessibility_helper import AccessibilityHelper

__all__ = [
    "ImageDescriptor",
    "UIElementDetector",
    "AccessibilityHelper",
]
