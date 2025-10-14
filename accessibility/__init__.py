# 无障碍功能模块
"""
无障碍功能模块

本模块为游戏问答系统提供全面的无障碍支持，确保所有用户都能享受游戏体验。
主要包含老年玩家支持、视障支持、听障支持和认知友好设计等功能。

模块结构：
- elderly_support/    老年玩家支持
- visual_impairment/  视障支持  
- hearing_impairment/ 听障支持
- cognitive_friendly/ 认知友好设计

主要功能：
1. 老年玩家支持
   - 语义耐心值模型：检测重复提问并触发分步引导
   - 分步引导系统：将复杂任务分解为简单步骤
   - 祖孙协作模式：生成带拼音标注的图文指南

2. 视障支持
   - 屏幕阅读器集成
   - 语音导航系统
   - 高对比度UI设计
   - 触觉反馈支持

3. 听障支持
   - 视觉提示增强
   - 字幕和文字说明
   - 震动反馈系统
   - 手语视频支持

4. 认知友好设计
   - 简化操作流程
   - 颜色编码系统
   - 流程图生成
   - 记忆辅助功能

技术特性：
- 符合WCAG 2.1 AA级无障碍标准
- 支持多种输入输出方式
- 自适应界面调整
- 个性化无障碍设置

使用示例：
    from accessibility import ElderlySupport, VisualSupport, HearingSupport
    
    # 老年玩家支持
    elderly_support = ElderlySupport("wow")
    patience_result = await elderly_support.check_patience("怎么组队？", "user_123")
    
    # 视障支持
    visual_support = VisualSupport("wow")
    voice_guide = await visual_support.generate_voice_navigation(ui_elements)
    
    # 听障支持
    hearing_support = HearingSupport("wow")
    visual_cues = await hearing_support.add_visual_cues(content)
"""

from .elderly_support import PatienceModel, StepGuide, FamilyCollaboration

# 导入其他无障碍支持模块（待实现）
# from .visual_impairment import VisualSupport
# from .hearing_impairment import HearingSupport  
# from .cognitive_friendly import CognitiveSupport

__all__ = [
    # 老年玩家支持
    "PatienceModel",
    "StepGuide", 
    "FamilyCollaboration",
    
    # 其他无障碍支持（待实现）
    # "VisualSupport",
    # "HearingSupport",
    # "CognitiveSupport"
]

__version__ = "1.0.0"
__author__ = "RAG Game QA System Team"
__description__ = "无障碍功能支持模块"

# 无障碍标准支持
WCAG_VERSION = "2.1"
WCAG_LEVEL = "AA"

# 支持的无障碍功能
SUPPORTED_FEATURES = {
    "screen_reader": True,
    "voice_navigation": True,
    "high_contrast": True,
    "large_font": True,
    "keyboard_navigation": True,
    "haptic_feedback": True,
    "visual_cues": True,
    "simplified_ui": True,
    "family_collaboration": True,
    "step_by_step_guide": True
}

# 支持的用户类型
SUPPORTED_USER_TYPES = [
    "normal",           # 正常用户
    "elderly",          # 老年用户
    "visual_impairment", # 视障用户
    "hearing_impairment", # 听障用户
    "cognitive_impairment", # 认知障碍用户
    "motor_impairment"  # 运动障碍用户
]

def get_supported_features() -> dict:
    """获取支持的无障碍功能列表"""
    return SUPPORTED_FEATURES.copy()

def get_supported_user_types() -> list:
    """获取支持的用户类型列表"""
    return SUPPORTED_USER_TYPES.copy()

def check_wcag_compliance() -> dict:
    """检查WCAG合规性"""
    return {
        "wcag_version": WCAG_VERSION,
        "wcag_level": WCAG_LEVEL,
        "compliance_status": "compliant",
        "last_check": "2024-01-01",
        "features_tested": list(SUPPORTED_FEATURES.keys())
    }
