# 噪声抑制
from typing import Dict, Any
import logging
import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)

class NoiseSuppression:
    """噪声抑制服务"""
    
    def __init__(self):
        logger.info("噪声抑制服务初始化完成")
    
    async def suppress_noise(self, audio_data: bytes) -> bytes:
        """
        抑制音频噪声
        
        Args:
            audio_data: 原始音频数据
            
        Returns:
            降噪后的音频数据
        """
        try:
            # 这里使用简单的噪声抑制算法
            # 实际应用中可以使用更复杂的算法如Wiener滤波、谱减法等
            
            # 将字节数据转换为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 应用简单的低通滤波器
            filtered_audio = self._apply_lowpass_filter(audio_array)
            
            # 应用噪声门限
            denoised_audio = self._apply_noise_gate(filtered_audio)
            
            # 转换回字节数据
            result_data = denoised_audio.astype(np.int16).tobytes()
            
            logger.info("噪声抑制完成")
            return result_data
            
        except Exception as e:
            logger.error(f"噪声抑制失败: {str(e)}")
            return audio_data
    
    def _apply_lowpass_filter(self, audio: np.ndarray, cutoff_freq: float = 8000) -> np.ndarray:
        """应用低通滤波器"""
        try:
            # 设计低通滤波器
            nyquist = 22050  # 假设采样率为44.1kHz
            normal_cutoff = cutoff_freq / nyquist
            b, a = signal.butter(4, normal_cutoff, btype='low', analog=False)
            
            # 应用滤波器
            filtered_audio = signal.filtfilt(b, a, audio)
            
            return filtered_audio
            
        except Exception as e:
            logger.error(f"低通滤波失败: {str(e)}")
            return audio
    
    def _apply_noise_gate(self, audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """应用噪声门限"""
        try:
            # 计算音频的RMS值
            rms = np.sqrt(np.mean(audio**2))
            
            # 如果RMS值低于阈值，认为是噪声
            if rms < threshold:
                # 将低音量部分设为0
                audio[np.abs(audio) < threshold * np.max(np.abs(audio))] = 0
            
            return audio
            
        except Exception as e:
            logger.error(f"噪声门限应用失败: {str(e)}")
            return audio
    
    async def enhance_speech(self, audio_data: bytes, enhancement_type: str = 'general') -> bytes:
        """
        语音增强
        
        Args:
            audio_data: 原始音频数据
            enhancement_type: 增强类型
            
        Returns:
            增强后的音频数据
        """
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if enhancement_type == 'elderly':
                # 为老年用户增强语音
                enhanced_audio = self._enhance_for_elderly(audio_array)
            elif enhancement_type == 'hearing_impairment':
                # 为听障用户增强语音
                enhanced_audio = self._enhance_for_hearing_impairment(audio_array)
            else:
                # 通用增强
                enhanced_audio = self._general_enhancement(audio_array)
            
            return enhanced_audio.astype(np.int16).tobytes()
            
        except Exception as e:
            logger.error(f"语音增强失败: {str(e)}")
            return audio_data
    
    def _enhance_for_elderly(self, audio: np.ndarray) -> np.ndarray:
        """为老年用户增强语音"""
        try:
            # 提高中频段，增强语音清晰度
            enhanced = audio.copy()
            
            # 简单的频率增强
            enhanced = enhanced * 1.2  # 提高音量
            
            # 限制最大音量
            enhanced = np.clip(enhanced, -32768, 32767)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"老年用户语音增强失败: {str(e)}")
            return audio
    
    def _enhance_for_hearing_impairment(self, audio: np.ndarray) -> np.ndarray:
        """为听障用户增强语音"""
        try:
            # 更激进的语音增强
            enhanced = audio.copy()
            
            # 提高音量
            enhanced = enhanced * 1.5
            
            # 增强高频成分
            enhanced = self._apply_high_frequency_boost(enhanced)
            
            # 限制最大音量
            enhanced = np.clip(enhanced, -32768, 32767)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"听障用户语音增强失败: {str(e)}")
            return audio
    
    def _general_enhancement(self, audio: np.ndarray) -> np.ndarray:
        """通用语音增强"""
        try:
            # 应用噪声抑制
            denoised = self._apply_noise_gate(audio)
            
            # 轻微的音量增强
            enhanced = denoised * 1.1
            
            # 限制最大音量
            enhanced = np.clip(enhanced, -32768, 32767)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"通用语音增强失败: {str(e)}")
            return audio
    
    def _apply_high_frequency_boost(self, audio: np.ndarray) -> np.ndarray:
        """应用高频增强"""
        try:
            # 设计高频增强滤波器
            nyquist = 22050
            high_cutoff = 3000 / nyquist
            b, a = signal.butter(2, high_cutoff, btype='high', analog=False)
            
            # 应用滤波器
            boosted = signal.filtfilt(b, a, audio)
            
            # 混合原始信号和增强信号
            result = audio + boosted * 0.3
            
            return result
            
        except Exception as e:
            logger.error(f"高频增强失败: {str(e)}")
            return audio
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'noise_suppression': True,
            'speech_enhancement': True,
            'elderly_support': True,
            'hearing_impairment_support': True
        }