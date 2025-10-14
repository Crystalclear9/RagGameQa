# 语义耐心值模型
from typing import Dict, Any, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class PatienceModel:
    """语义耐心值模型，检测老年玩家重复提问"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.similarity_threshold = 0.85
        self.max_patience = 3
        self.question_history = []
    
    async def check_patience(self, question: str, user_id: str) -> Dict[str, Any]:
        """
        检查用户耐心值
        
        Args:
            question: 当前问题
            user_id: 用户ID
            
        Returns:
            耐心值检查结果
        """
        # 1. 获取用户历史问题
        user_history = self._get_user_history(user_id)
        
        # 2. 计算相似度
        similarities = []
        for hist_question in user_history:
            similarity = await self._calculate_similarity(question, hist_question)
            similarities.append(similarity)
        
        # 3. 判断是否重复
        max_similarity = max(similarities) if similarities else 0
        is_repetitive = max_similarity > self.similarity_threshold
        
        # 4. 更新耐心值
        patience_level = self._update_patience(user_id, is_repetitive)
        
        # 5. 判断是否需要触发分步引导
        needs_guidance = patience_level >= self.max_patience
        
        return {
            "patience_level": patience_level,
            "is_repetitive": is_repetitive,
            "similarity_score": max_similarity,
            "needs_guidance": needs_guidance,
            "guidance_type": "step_by_step" if needs_guidance else None
        }
    
    def _get_user_history(self, user_id: str) -> List[str]:
        """获取用户历史问题"""
        # 这里应该从数据库获取用户历史
        return self.question_history[-5:]  # 临时实现
    
    async def _calculate_similarity(self, question1: str, question2: str) -> float:
        """计算问题相似度"""
        # 使用简单的文本相似度计算
        # 实际实现应该使用更复杂的语义相似度算法
        words1 = set(question1.split())
        words2 = set(question2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _update_patience(self, user_id: str, is_repetitive: bool) -> int:
        """更新耐心值"""
        # 这里应该维护用户耐心值状态
        # 临时实现
        if is_repetitive:
            return 3  # 达到最大耐心值
        else:
            return 1  # 正常耐心值
