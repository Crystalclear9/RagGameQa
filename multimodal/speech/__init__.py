# 语音模块
"""
语音交互模块

导出：
- ASRService：语音识别
- TTSService：语音合成
- DialectRecognizer：方言识别
- NoiseSuppression：噪声抑制
"""

from .asr_service import ASRService
from .tts_service import TTSService
from .dialect_recognizer import DialectRecognizer
from .noise_suppression import NoiseSuppression

__all__ = [
    "ASRService",
    "TTSService",
    "DialectRecognizer",
    "NoiseSuppression",
]
