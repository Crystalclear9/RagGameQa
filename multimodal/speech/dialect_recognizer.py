# 方言识别器 - 占位实现
from typing import Dict, Any


class DialectRecognizer:
    """方言识别器 - 占位实现
    
    注：多模态功能已移除依赖，此为占位实现
    """
    
    def __init__(self):
        pass
    
    async def recognize_dialect(self, text: str) -> Dict[str, Any]:
        """识别方言
        
        Args:
            text: 输入文本
            
        Returns:
            方言识别结果
        """
        return {
            "dialect": "standard",  # 标准普通话
            "confidence": 1.0
        }
