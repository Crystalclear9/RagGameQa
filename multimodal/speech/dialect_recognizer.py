# 方言识别器 - 结合NLP增强策略
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DialectRecognizer:
    """方言识别器 - 结合文本特征分析预测方言模式"""
    
    def __init__(self):
        # 简单方言词库用于文本级别回退识别
        self.dialect_keywords = {
            "sichuan": ["啥子", "巴适", "要得", "安逸", "晓得", "锤子"],
            "yue": ["唔明", "点样", "几多", "返工", "靓仔", "系啊", "咩事"]
        }
    
    async def recognize_dialect(self, text: str) -> Dict[str, Any]:
        """识别方言
        
        Args:
            text: 输入文本
            
        Returns:
            方言识别结果
        """
        if not text:
            return {
                "dialect": "standard",
                "confidence": 1.0
            }

        # 文本级别方言特征粗略检测
        scores = {"sichuan": 0, "yue": 0, "standard": 1}
        
        for d, keywords in self.dialect_keywords.items():
            for kw in keywords:
                if kw in text:
                    scores[d] += 2
        
        best_dialect = max(scores, key=scores.get)
        
        # 如果是标准，置信度高，否则取决于匹配数量
        confidence = 0.95 if best_dialect == "standard" else min(0.9, 0.5 + 0.1 * scores[best_dialect])

        if best_dialect != "standard":
            logger.info(f"探测到方言意向 [{best_dialect}] (置信度 {confidence})")

        return {
            "dialect": best_dialect,
            "confidence": confidence
        }
