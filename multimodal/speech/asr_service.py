# 语音识别服务
from typing import Optional, Dict, Any
import speech_recognition as sr
import pyttsx3
import io
import wave
from multimodal.speech.dialect_recognizer import DialectRecognizer
from multimodal.speech.noise_suppression import NoiseSuppression

class ASRService:
    """语音识别服务"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.recognizer = sr.Recognizer()
        self.dialect_recognizer = DialectRecognizer(game_id)
        self.noise_suppressor = NoiseSuppression(game_id)
        self.supported_languages = ["zh-CN", "en-US", "yue-CN", "sichuan-CN"]
    
    async def recognize_speech(
        self, 
        audio_data: bytes, 
        language: str = "zh-CN",
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        语音识别
        
        Args:
            audio_data: 音频数据
            language: 语言代码
            user_context: 用户上下文
            
        Returns:
            识别结果
        """
        try:
            # 1. 噪声抑制
            cleaned_audio = await self.noise_suppressor.suppress_noise(audio_data)
            
            # 2. 方言识别（如果需要）
            if user_context and user_context.get('enable_dialect', False):
                detected_dialect = await self.dialect_recognizer.detect_dialect(cleaned_audio)
                if detected_dialect:
                    language = detected_dialect
            
            # 3. 语音识别
            text = await self._perform_recognition(cleaned_audio, language)
            
            # 4. 后处理
            processed_text = await self._post_process_text(text, user_context)
            
            return {
                "text": processed_text,
                "language": language,
                "confidence": 0.9,  # 实际应该从识别结果获取
                "dialect_detected": user_context.get('enable_dialect', False)
            }
            
        except Exception as e:
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _perform_recognition(self, audio_data: bytes, language: str) -> str:
        """执行语音识别"""
        # 将字节数据转换为AudioData对象
        audio_file = io.BytesIO(audio_data)
        
        with sr.AudioFile(audio_file) as source:
            audio = self.recognizer.record(source)
        
        # 使用Google语音识别
        try:
            text = self.recognizer.recognize_google(audio, language=language)
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            raise Exception(f"语音识别服务错误: {e}")
    
    async def _post_process_text(self, text: str, user_context: Optional[Dict]) -> str:
        """文本后处理"""
        if not text:
            return text
        
        # 基础清理
        text = text.strip()
        
        # 根据用户类型特殊处理
        if user_context:
            user_type = user_context.get('user_type', 'normal')
            
            if user_type == 'elderly':
                # 老年用户：简化语言
                text = self._simplify_for_elderly(text)
            elif user_type == 'hearing_impairment':
                # 听障用户：添加视觉提示
                text = self._add_visual_cues(text)
        
        return text
    
    def _simplify_for_elderly(self, text: str) -> str:
        """为老年用户简化语言"""
        # 替换复杂词汇
        replacements = {
            '技能': '能力',
            '装备': '道具',
            '副本': '关卡'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _add_visual_cues(self, text: str) -> str:
        """为听障用户添加视觉提示"""
        # 在关键信息前添加视觉标记
        text = text.replace('注意', '[视觉] 注意')
        text = text.replace('重要', '[视觉] 重要')
        return text
