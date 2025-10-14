# 噪声抑制
from typing import Optional, Dict, Any
import numpy as np
import librosa
from scipy import signal
import noisereduce as nr

class NoiseSuppression:
    """噪声抑制，提升嘈杂环境下的语音识别准确率"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.sample_rate = 16000
        self.noise_profile = None
    
    async def suppress_noise(
        self, 
        audio_data: bytes, 
        noise_profile: Optional[np.ndarray] = None
    ) -> bytes:
        """
        抑制音频噪声
        
        Args:
            audio_data: 原始音频数据
            noise_profile: 噪声模板（可选）
            
        Returns:
            降噪后的音频数据
        """
        try:
            # 1. 转换为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 2. 重采样到目标采样率
            if len(audio_float) > 0:
                audio_resampled = librosa.resample(
                    audio_float, 
                    orig_sr=22050, 
                    target_sr=self.sample_rate
                )
            else:
                return audio_data
            
            # 3. 噪声抑制
            if noise_profile is not None:
                # 使用提供的噪声模板
                denoised_audio = nr.reduce_noise(
                    y=audio_resampled,
                    sr=self.sample_rate,
                    y_noise=noise_profile
                )
            else:
                # 自动噪声抑制
                denoised_audio = nr.reduce_noise(
                    y=audio_resampled,
                    sr=self.sample_rate
                )
            
            # 4. 后处理
            processed_audio = await self._post_process(denoised_audio)
            
            # 5. 转换回字节格式
            audio_int16 = (processed_audio * 32768).astype(np.int16)
            return audio_int16.tobytes()
            
        except Exception as e:
            print(f"噪声抑制失败: {e}")
            return audio_data
    
    async def _post_process(self, audio: np.ndarray) -> np.ndarray:
        """音频后处理"""
        # 1. 归一化
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
        
        # 2. 高通滤波（去除低频噪声）
        b, a = signal.butter(4, 80, btype='high', fs=self.sample_rate)
        audio = signal.filtfilt(b, a, audio)
        
        # 3. 动态范围压缩
        audio = await self._dynamic_range_compression(audio)
        
        return audio
    
    async def _dynamic_range_compression(self, audio: np.ndarray) -> np.ndarray:
        """动态范围压缩"""
        # 简单的动态范围压缩
        threshold = 0.1
        ratio = 4.0
        
        compressed_audio = np.copy(audio)
        
        # 对超过阈值的部分进行压缩
        mask = np.abs(audio) > threshold
        compressed_audio[mask] = np.sign(audio[mask]) * (
            threshold + (np.abs(audio[mask]) - threshold) / ratio
        )
        
        return compressed_audio
    
    async def extract_noise_profile(self, audio_data: bytes, duration: float = 1.0) -> np.ndarray:
        """
        提取噪声模板
        
        Args:
            audio_data: 音频数据
            duration: 噪声持续时间（秒）
            
        Returns:
            噪声模板
        """
        try:
            # 转换为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 重采样
            audio_resampled = librosa.resample(
                audio_float, 
                orig_sr=22050, 
                target_sr=self.sample_rate
            )
            
            # 提取前几秒作为噪声模板
            noise_samples = int(duration * self.sample_rate)
            noise_profile = audio_resampled[:noise_samples]
            
            return noise_profile
            
        except Exception as e:
            print(f"噪声模板提取失败: {e}")
            return np.array([])
    
    async def adaptive_noise_suppression(self, audio_data: bytes) -> bytes:
        """
        自适应噪声抑制
        
        Args:
            audio_data: 音频数据
            
        Returns:
            降噪后的音频数据
        """
        try:
            # 1. 提取噪声模板（使用音频开头）
            noise_profile = await self.extract_noise_profile(audio_data, duration=0.5)
            
            # 2. 使用噪声模板进行降噪
            if len(noise_profile) > 0:
                return await self.suppress_noise(audio_data, noise_profile)
            else:
                return await self.suppress_noise(audio_data)
                
        except Exception as e:
            print(f"自适应噪声抑制失败: {e}")
            return audio_data
    
    def get_noise_level(self, audio_data: bytes) -> float:
        """
        获取音频噪声水平
        
        Args:
            audio_data: 音频数据
            
        Returns:
            噪声水平 (0-1)
        """
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 计算信噪比
            signal_power = np.mean(audio_float ** 2)
            noise_power = np.var(audio_float)
            
            if signal_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
                # 将SNR转换为0-1的噪声水平
                noise_level = max(0, min(1, (30 - snr) / 30))
            else:
                noise_level = 1.0
            
            return noise_level
            
        except Exception as e:
            print(f"噪声水平计算失败: {e}")
            return 0.5
