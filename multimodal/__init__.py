# 多模态交互模块
"""
多模态交互模块

实现语音、视觉、触觉等多模态交互功能。
支持无障碍交互和智能适配。
"""

from .speech.asr_service import ASRService
from .speech.tts_service import TTSService
from .speech.dialect_recognizer import DialectRecognizer
from .visual.image_descriptor import ImageDescriptor
from .visual.ui_element_detector import UIElementDetector
from .haptic.vibration_encoder import VibrationEncoder
from .haptic.feedback_mapper import FeedbackMapper
from .interaction.multimodal_coordinator import MultimodalCoordinator

__all__ = [
    # 语音模块
    "ASRService",
    "TTSService", 
    "DialectRecognizer",
    
    # 视觉模块
    "ImageDescriptor",
    "UIElementDetector",
    
    # 触觉模块
    "VibrationEncoder",
    "FeedbackMapper",
    
    # 交互协调
    "MultimodalCoordinator"
]
