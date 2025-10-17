# 语音合成服务
from typing import Dict, Any, Optional
import logging
import asyncio

# 可选依赖
try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False
    pyttsx3 = None

logger = logging.getLogger(__name__)

class TTSService:
    """语音合成服务"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.engine = pyttsx3.init()
        self._configure_engine()
        logger.info(f"TTS服务初始化完成: {game_id}")
    
    def _configure_engine(self):
        """配置TTS引擎"""
        try:
            # 设置语音参数
            voices = self.engine.getProperty('voices')
            
            # 选择中文语音
            for voice in voices:
                if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            # 设置语速和音量
            self.engine.setProperty('rate', 150)  # 语速
            self.engine.setProperty('volume', 0.8)  # 音量
            
        except Exception as e:
            logger.error(f"TTS引擎配置失败: {str(e)}")
    
    async def synthesize_speech(self, text: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        语音合成
        
        Args:
            text: 要合成的文本
            user_context: 用户上下文
            
        Returns:
            合成结果
        """
        try:
            # 根据用户上下文调整语音参数
            if user_context:
                self._adjust_for_user_context(user_context)
            
            # 执行语音合成
            await self._synthesize_async(text)
            
            result = {
                'text': text,
                'success': True,
                'duration': len(text) * 0.1,  # 估算时长
                'voice_settings': self._get_voice_settings()
            }
            
            logger.info(f"语音合成完成: {text[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"语音合成失败: {str(e)}")
            return {
                'text': text,
                'success': False,
                'error': str(e)
            }
    
    async def _synthesize_async(self, text: str):
        """异步语音合成"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.engine.say, text)
        await loop.run_in_executor(None, self.engine.runAndWait)
    
    def _adjust_for_user_context(self, user_context: Dict[str, Any]):
        """根据用户上下文调整语音参数"""
        user_type = user_context.get('user_type', 'normal')
        
        if user_type == 'elderly':
            # 老年用户：降低语速，提高音量
            self.engine.setProperty('rate', 120)
            self.engine.setProperty('volume', 0.9)
        elif user_type == 'hearing_impairment':
            # 听障用户：提高音量，降低语速
            self.engine.setProperty('rate', 130)
            self.engine.setProperty('volume', 1.0)
        elif user_type == 'visual_impairment':
            # 视障用户：正常语速，适中音量
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.8)
    
    def _get_voice_settings(self) -> Dict[str, Any]:
        """获取当前语音设置"""
        return {
            'rate': self.engine.getProperty('rate'),
            'volume': self.engine.getProperty('volume'),
            'voice': self.engine.getProperty('voice')
        }
    
    async def synthesize_with_emotion(self, text: str, emotion: str = 'neutral') -> Dict[str, Any]:
        """
        带情感的语音合成
        
        Args:
            text: 要合成的文本
            emotion: 情感类型
            
        Returns:
            合成结果
        """
        try:
            # 根据情感调整语音参数
            if emotion == 'excited':
                self.engine.setProperty('rate', 180)
                self.engine.setProperty('volume', 0.9)
            elif emotion == 'calm':
                self.engine.setProperty('rate', 120)
                self.engine.setProperty('volume', 0.7)
            elif emotion == 'urgent':
                self.engine.setProperty('rate', 200)
                self.engine.setProperty('volume', 1.0)
            
            result = await self.synthesize_speech(text)
            result['emotion'] = emotion
            
            return result
            
        except Exception as e:
            logger.error(f"情感语音合成失败: {str(e)}")
            return await self.synthesize_speech(text)
    
    def get_available_voices(self) -> list:
        """获取可用的语音列表"""
        try:
            voices = self.engine.getProperty('voices')
            return [
                {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': voice.languages
                }
                for voice in voices
            ]
        except Exception as e:
            logger.error(f"获取语音列表失败: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            'game_id': self.game_id,
            'available_voices': len(self.get_available_voices()),
            'current_settings': self._get_voice_settings(),
            'emotion_support': True
        }