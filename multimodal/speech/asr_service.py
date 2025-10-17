# 语音识别服务
from typing import Dict, Any, Optional
import logging

# 可选依赖
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    sr = None

from .dialect_recognizer import DialectRecognizer
from .noise_suppression import NoiseSuppression

logger = logging.getLogger(__name__)

class ASRService:
    """语音识别服务"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.recognizer = sr.Recognizer()
        self.dialect_recognizer = DialectRecognizer()
        self.noise_suppressor = NoiseSuppression()
        logger.info(f"ASR服务初始化完成: {game_id}")
    
    async def recognize_speech(self, audio_data: bytes, language: str = "zh-CN") -> Dict[str, Any]:
        """
        语音识别
        
        Args:
            audio_data: 音频数据
            language: 语言代码
            
        Returns:
            识别结果
        """
        try:
            # 1. 噪声抑制
            cleaned_audio = await self.noise_suppressor.suppress_noise(audio_data)
            
            # 2. 基础语音识别
            with sr.AudioFile(cleaned_audio) as source:
                audio = self.recognizer.record(source)
            
            # 3. 识别文本
            text = self.recognizer.recognize_google(audio, language=language)
            
            # 4. 方言识别
            dialect_info = await self.dialect_recognizer.recognize_dialect(text)
            
            result = {
                'text': text,
                'confidence': 0.9,  # 模拟置信度
                'language': language,
                'dialect': dialect_info.get('dialect', 'standard'),
                'dialect_confidence': dialect_info.get('confidence', 0.0)
            }
            
            logger.info(f"语音识别完成: {text[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}")
            return {
                'text': '',
                'confidence': 0.0,
                'language': language,
                'dialect': 'unknown',
                'dialect_confidence': 0.0,
                'error': str(e)
            }
    
    async def recognize_with_context(self, audio_data: bytes, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        带上下文的语音识别
        
        Args:
            audio_data: 音频数据
            context: 上下文信息
            
        Returns:
            识别结果
        """
        try:
            # 根据上下文调整识别参数
            language = context.get('language', 'zh-CN')
            user_type = context.get('user_type', 'normal')
            
            # 基础识别
            result = await self.recognize_speech(audio_data, language)
            
            # 根据用户类型调整结果
            if user_type == 'elderly':
                result = self._adapt_for_elderly(result)
            elif user_type == 'hearing_impairment':
                result = self._adapt_for_hearing_impairment(result)
            
            return result
            
        except Exception as e:
            logger.error(f"上下文语音识别失败: {str(e)}")
            return await self.recognize_speech(audio_data)
    
    def _adapt_for_elderly(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """为老年用户适配识别结果"""
        # 简化语言，提高识别准确度
        text = result.get('text', '')
        
        # 替换复杂词汇
        replacements = {
            '技能': '功能',
            '装备': '道具',
            '副本': '关卡',
            '任务': '工作'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        result['text'] = text
        result['adapted_for_elderly'] = True
        
        return result
    
    def _adapt_for_hearing_impairment(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """为听障用户适配识别结果"""
        # 添加视觉提示
        result['visual_hints'] = True
        result['enhanced_text'] = f"[语音识别] {result.get('text', '')}"
        
        return result
    
    def get_supported_languages(self) -> list:
        """获取支持的语言列表"""
        return ['zh-CN', 'en-US', 'yue', 'sichuan']
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            'game_id': self.game_id,
            'supported_languages': self.get_supported_languages(),
            'dialect_support': True,
            'noise_suppression': True
        }