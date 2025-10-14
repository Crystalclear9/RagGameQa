# 震动编码器
from typing import Dict, Any, List
import time

class VibrationEncoder:
    """震动编码器，定义震动频率与语义反馈的映射规则"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.vibration_patterns = {
            "success": [100, 200, 100],  # 3次短震表示"操作成功"
            "error": [500, 200, 500],    # 长震-短震-长震表示"错误"
            "warning": [300, 100, 300],  # 警告模式
            "notification": [200],        # 单次震动表示"通知"
            "direction_up": [150],       # 向上
            "direction_down": [150, 150], # 向下
            "direction_left": [100, 100, 100], # 向左
            "direction_right": [200, 200]     # 向右
        }
    
    async def encode_feedback(self, feedback_type: str, intensity: float = 1.0) -> List[int]:
        """编码触觉反馈"""
        pattern = self.vibration_patterns.get(feedback_type, [200])
        
        # 根据强度调整震动时长
        adjusted_pattern = [int(duration * intensity) for duration in pattern]
        
        return adjusted_pattern
    
    async def send_vibration(self, pattern: List[int], device_id: str = "default"):
        """发送震动信号"""
        # 这里需要与具体的触觉设备通信
        # 例如Xbox Adaptive Controller或其他触觉设备
        pass
