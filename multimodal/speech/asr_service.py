# 语音识别服务
import io
import wave
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 可选依赖
try:
    import torch
    from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import torchaudio
    HAS_TORCHAUDIO = True
except ImportError:
    HAS_TORCHAUDIO = False

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    sr = None

from .dialect_recognizer import DialectRecognizer
from .noise_suppression import NoiseSuppression

class ASRService:
    """语音识别服务 (Wav2Vec2 真实模型集成)"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        
        self.processor = None
        self.model = None
        self._model_loaded = False
        
        self.dialect_recognizer = DialectRecognizer()
        self.noise_suppressor = NoiseSuppression()
        
        # 兼容旧版的后备模式
        self.fallback_recognizer = sr.Recognizer() if HAS_SPEECH_RECOGNITION else None
        
        logger.info(f"ASR服务初始化完成: {game_id}")

    def _load_model(self):
        """惰性加载音频识别模型"""
        if not HAS_TRANSFORMERS or not HAS_TORCHAUDIO:
            logger.warning("未安装 transformers 或 torchaudio，语音识别可能回退到在线占位 API。")
            return
            
        if not self._model_loaded:
            try:
                logger.info("Initializing Wav2Vec2.0 model for Speech Recognition...")
                model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
                self.processor = Wav2Vec2Processor.from_pretrained(model_name)
                self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
                self._model_loaded = True
                logger.info("Wav2Vec2.0 model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Wav2Vec2.0 model: {str(e)}")

    async def recognize_speech(self, audio_data: bytes, language: str = "zh-CN") -> Dict[str, Any]:
        """
        语音识别
        """
        try:
            self._load_model()
            
            # 1. 噪声抑制
            cleaned_audio = await self.noise_suppressor.suppress_noise(audio_data)
            duration = self._estimate_duration(cleaned_audio)
            
            text = ""
            confidence = 0.0
            
            # 2. 真实模型识别尝试
            if self._model_loaded and HAS_TORCHAUDIO:
                try:
                    # 使用 torchaudio 处理字节数据（真实实现需要保存临时文件或用 io 转换）
                    waveform, sample_rate = torchaudio.load(io.BytesIO(cleaned_audio))
                    if sample_rate != 16000:
                        waveform = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)(waveform)
                    
                    input_values = self.processor(waveform.squeeze().numpy(), return_tensors="pt", sampling_rate=16000).input_values
                    logits = self.model(input_values).logits
                    predicted_ids = torch.argmax(logits, dim=-1)
                    text = self.processor.batch_decode(predicted_ids)[0]
                    confidence = 0.92
                except Exception as eval_err:
                    logger.warning(f"本地 Wav2Vec2 推理失败，回退到备用方案: {str(eval_err)}")
                    text = ""

            # 3. 回退模式
            if not text and self.fallback_recognizer:
                with sr.AudioFile(io.BytesIO(cleaned_audio)) as source:
                    audio = self.fallback_recognizer.record(source)
                try:
                    text = self.fallback_recognizer.recognize_google(audio, language=language)
                    confidence = 0.85
                except Exception as fallback_err:
                    logger.error(f"Google 备用语音识别也失败了: {str(fallback_err)}")
            elif not text:
                text = "（系统提示：缺少 transformers 或 speech_recognition，无法解析音频内容）"
                confidence = 0.1
                
            # 4. 方言识别
            dialect_info = await self.dialect_recognizer.recognize_dialect(text)
            
            result = {
                'text': text,
                'confidence': confidence,
                'language': language,
                'dialect': dialect_info.get('dialect', 'standard'),
                'dialect_confidence': dialect_info.get('confidence', 0.0),
                'duration': duration,
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
                'duration': self._estimate_duration(audio_data),
                'error': str(e)
            }
    
    async def recognize_with_context(self, audio_data: bytes, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            language = context.get('language', 'zh-CN')
            user_type = context.get('user_type', 'normal')
            
            result = await self.recognize_speech(audio_data, language)
            
            if user_type == 'elderly':
                result = self._adapt_for_elderly(result)
            elif user_type == 'hearing_impairment':
                result = self._adapt_for_hearing_impairment(result)
            
            return result
        except Exception as e:
            logger.error(f"上下文语音识别失败: {str(e)}")
            return await self.recognize_speech(audio_data)
    
    def _adapt_for_elderly(self, result: Dict[str, Any]) -> Dict[str, Any]:
        text = result.get('text', '')
        replacements = {
            '技能': '功能', '装备': '道具', '副本': '关卡', '任务': '工作'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        result['text'] = text
        result['adapted_for_elderly'] = True
        return result
    
    def _adapt_for_hearing_impairment(self, result: Dict[str, Any]) -> Dict[str, Any]:
        result['visual_hints'] = True
        result['enhanced_text'] = f"[语音识别] {result.get('text', '')}"
        return result
    
    def get_supported_languages(self) -> list:
        return ['zh-CN', 'en-US', 'yue', 'sichuan']
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'game_id': self.game_id,
            'supported_languages': self.get_supported_languages(),
            'dialect_support': True,
            'noise_suppression': True,
            'speech_recognition_fallback': HAS_SPEECH_RECOGNITION,
            'transformers_accelerated': self._model_loaded
        }

    def _estimate_duration(self, audio_data: bytes) -> float:
        try:
            with wave.open(io.BytesIO(audio_data), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return round(frames / float(rate), 2) if rate else 0.0
        except Exception:
            return 0.0
