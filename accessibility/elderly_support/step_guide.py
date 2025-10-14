# 分步引导
from typing import List, Dict, Any

class StepGuide:
    """分步引导系统"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
    
    async def generate_guide(self, task: str, user_context: Dict) -> List[Dict[str, Any]]:
        """生成分步引导"""
        pass
