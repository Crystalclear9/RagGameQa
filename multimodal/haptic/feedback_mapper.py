# 反馈映射
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class FeedbackMapper:
    """反馈映射器，将游戏动作和结果映射为触觉反馈"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.feedback_rules = self._load_feedback_rules()
        logger.info(f"反馈映射器初始化完成: {game_id}")
    
    async def map_feedback(self, action: str, result: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        映射反馈
        
        Args:
            action: 游戏动作
            result: 动作结果
            context: 上下文信息
            
        Returns:
            反馈映射结果
        """
        try:
            # 1. 确定反馈类型
            feedback_type = self._determine_feedback_type(action, result, context)
            
            # 2. 计算反馈强度
            intensity = self._calculate_intensity(action, result, context)
            
            # 3. 生成反馈模式
            pattern = self._generate_pattern(feedback_type, intensity, context)
            
            # 4. 添加游戏特定调整
            adjusted_pattern = self._adjust_for_game(pattern, context)
            
            return {
                "feedback_type": feedback_type,
                "intensity": intensity,
                "pattern": adjusted_pattern,
                "duration": sum(adjusted_pattern),
                "context": context or {},
                "game_id": self.game_id
            }
            
        except Exception as e:
            logger.error(f"反馈映射失败: {str(e)}")
            return self._get_default_feedback()
    
    async def map_sequence_feedback(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        映射序列反馈
        
        Args:
            actions: 动作序列
            
        Returns:
            反馈序列
        """
        feedbacks = []
        
        for i, action_data in enumerate(actions):
            action = action_data.get("action", "")
            result = action_data.get("result", "")
            context = action_data.get("context", {})
            
            # 添加序列上下文
            context["sequence_index"] = i
            context["total_actions"] = len(actions)
            
            feedback = await self.map_feedback(action, result, context)
            feedbacks.append(feedback)
        
        return feedbacks
    
    def _determine_feedback_type(self, action: str, result: str, context: Dict[str, Any]) -> str:
        """确定反馈类型"""
        # 基于结果确定反馈类型
        if result in ["success", "completed", "achieved"]:
            return "success"
        elif result in ["error", "failed", "missed"]:
            return "error"
        elif result in ["warning", "caution", "danger"]:
            return "warning"
        elif result in ["notification", "info", "update"]:
            return "notification"
        
        # 基于动作确定反馈类型
        action_lower = action.lower()
        if any(keyword in action_lower for keyword in ["attack", "hit", "damage"]):
            return "attack"
        elif any(keyword in action_lower for keyword in ["heal", "recover", "restore"]):
            return "heal"
        elif any(keyword in action_lower for keyword in ["move", "walk", "run"]):
            return "movement"
        elif any(keyword in action_lower for keyword in ["collect", "pickup", "gather"]):
            return "collection"
        
        # 默认反馈
        return "notification"
    
    def _calculate_intensity(self, action: str, result: str, context: Dict[str, Any]) -> float:
        """计算反馈强度"""
        base_intensity = 0.5
        
        # 根据结果调整强度
        if result in ["critical_hit", "massive_damage", "epic_achievement"]:
            base_intensity = 1.0
        elif result in ["minor_success", "small_gain"]:
            base_intensity = 0.3
        elif result in ["failure", "error"]:
            base_intensity = 0.7
        
        # 根据用户类型调整强度
        user_type = context.get("user_type", "normal")
        if user_type == "elderly":
            base_intensity *= 1.2  # 老年用户需要更强的反馈
        elif user_type == "hearing_impairment":
            base_intensity *= 1.5  # 听障用户需要更强的触觉反馈
        
        # 根据游戏状态调整强度
        game_state = context.get("game_state", {})
        if game_state.get("combat_mode", False):
            base_intensity *= 1.3  # 战斗模式下增强反馈
        
        return min(max(base_intensity, 0.1), 1.0)  # 限制在0.1-1.0范围内
    
    def _generate_pattern(self, feedback_type: str, intensity: float, context: Dict[str, Any]) -> List[int]:
        """生成反馈模式"""
        patterns = {
            "success": [100, 200, 100],  # 短-长-短
            "error": [500, 200, 500],     # 长-短-长
            "warning": [300, 100, 300],   # 中-短-中
            "notification": [200],         # 单次
            "attack": [150, 50, 150],     # 攻击模式
            "heal": [100, 100, 100],      # 治疗模式
            "movement": [100],             # 移动模式
            "collection": [80, 80, 80]    # 收集模式
        }
        
        base_pattern = patterns.get(feedback_type, [200])
        
        # 根据强度调整模式
        adjusted_pattern = [int(duration * intensity) for duration in base_pattern]
        
        return adjusted_pattern
    
    def _adjust_for_game(self, pattern: List[int], context: Dict[str, Any]) -> List[int]:
        """根据游戏特性调整模式"""
        game_id = self.game_id
        
        # 游戏特定调整
        if game_id == "wow":
            # 魔兽世界：更复杂的反馈模式
            if len(pattern) == 1:
                pattern = [pattern[0], 50, pattern[0]]
        elif game_id == "lol":
            # 英雄联盟：更快的反馈
            pattern = [int(duration * 0.8) for duration in pattern]
        elif game_id == "genshin":
            # 原神：更柔和的反馈
            pattern = [int(duration * 1.2) for duration in pattern]
        
        return pattern
    
    def _load_feedback_rules(self) -> Dict[str, Any]:
        """加载反馈规则"""
        return {
            "default_intensity": 0.5,
            "max_intensity": 1.0,
            "min_intensity": 0.1,
            "pattern_duration_limit": 2000,  # 最大模式时长(ms)
            "user_type_multipliers": {
                "elderly": 1.2,
                "hearing_impairment": 1.5,
                "visual_impairment": 1.3,
                "normal": 1.0
            }
        }
    
    def _get_default_feedback(self) -> Dict[str, Any]:
        """获取默认反馈"""
        return {
            "feedback_type": "notification",
            "intensity": 0.5,
            "pattern": [200],
            "duration": 200,
            "context": {},
            "game_id": self.game_id
        }
    
    async def get_feedback_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户反馈历史"""
        # 模拟返回历史记录
        return [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "action": "attack",
                "result": "success",
                "feedback_type": "success",
                "intensity": 0.8
            }
        ] * min(limit, 5)
    
    def get_supported_feedback_types(self) -> List[str]:
        """获取支持的反馈类型"""
        return [
            "success", "error", "warning", "notification",
            "attack", "heal", "movement", "collection"
        ]
