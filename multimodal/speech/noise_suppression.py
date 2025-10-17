# 噪声抑制 - 占位实现
from typing import Any


class NoiseSuppression:
    """噪声抑制 - 占位实现
    
    注：多模态功能已移除依赖，此为占位实现
    """
    
    def __init__(self):
        pass
    
    async def suppress_noise(self, audio_data: bytes) -> bytes:
        """抑制噪声
        
        Args:
            audio_data: 音频数据
            
        Returns:
            处理后的音频数据（当前无处理，直接返回）
        """
        # 占位实现：直接返回原始数据
        return audio_data
