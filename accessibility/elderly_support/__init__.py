# 老年玩家支持模块
"""
老年玩家支持模块

本模块专门为老年玩家提供无障碍游戏体验，包括：
- 语义耐心值模型：检测重复提问并触发分步引导
- 分步引导系统：将复杂任务分解为简单步骤
- 祖孙协作模式：生成带拼音标注的图文指南

主要功能：
1. 智能检测老年玩家的重复提问行为
2. 自动生成适合老年玩家的分步操作指南
3. 支持家庭协作，生成可分享的图文指南
4. 提供语音提示和视觉辅助功能
5. 简化游戏操作流程，降低学习门槛

使用示例：
    from accessibility.elderly_support import PatienceModel, StepGuide, FamilyCollaboration
    
    # 创建耐心值模型
    patience_model = PatienceModel("wow")
    
    # 检查用户耐心值
    result = await patience_model.check_patience("怎么组队？", "user_123")
    
    # 如果需要分步引导
    if result["needs_guidance"]:
        step_guide = StepGuide("wow")
        guide = await step_guide.generate_guide("组队任务", {"user_type": "elderly"})
    
    # 生成家庭协作指南
    family_collab = FamilyCollaboration("wow")
    family_guide = await family_collab.generate_family_guide("怎么组队？", "详细答案...")
"""

try:
    from .patience_model import PatienceModel
except ImportError:
    PatienceModel = None

from .step_guide import StepGuide
try:
    from .family_collaboration import FamilyCollaboration
except ImportError:
    FamilyCollaboration = None

__all__ = [
    "PatienceModel",
    "StepGuide", 
    "FamilyCollaboration"
]

__version__ = "1.0.0"
__author__ = "RAG Game QA System Team"
__description__ = "老年玩家无障碍支持模块"
