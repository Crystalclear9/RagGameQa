# 分步引导
from typing import List, Dict, Any, Optional
import re
import json
from datetime import datetime

class StepGuide:
    """分步引导系统，为老年玩家提供详细的操作步骤"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.step_templates = self._load_step_templates()
        self.user_progress = {}  # 用户进度跟踪
        self.step_difficulty_levels = {
            "beginner": {"max_steps": 3, "detail_level": "high"},
            "intermediate": {"max_steps": 5, "detail_level": "medium"},
            "advanced": {"max_steps": 8, "detail_level": "low"}
        }
    
    def _load_step_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载步骤模板"""
        return {
            "operation": {
                "click": {
                    "steps": [
                        {"action": "找到目标", "description": "在屏幕上找到要点击的按钮或图标", "visual_cue": "👆"},
                        {"action": "点击操作", "description": "用手指轻触目标位置", "visual_cue": "🖱️"},
                        {"action": "确认结果", "description": "观察屏幕变化，确认操作成功", "visual_cue": "✅"}
                    ]
                },
                "select": {
                    "steps": [
                        {"action": "打开菜单", "description": "点击菜单按钮打开选项列表", "visual_cue": "📋"},
                        {"action": "浏览选项", "description": "上下滑动查看所有可用选项", "visual_cue": "👀"},
                        {"action": "选择项目", "description": "点击想要的选项", "visual_cue": "✅"},
                        {"action": "确认选择", "description": "点击确认按钮完成选择", "visual_cue": "✔️"}
                    ]
                },
                "navigate": {
                    "steps": [
                        {"action": "找到导航", "description": "在界面上找到导航按钮或菜单", "visual_cue": "🧭"},
                        {"action": "选择目标", "description": "点击想要前往的位置", "visual_cue": "🎯"},
                        {"action": "等待加载", "description": "等待页面加载完成", "visual_cue": "⏳"},
                        {"action": "确认到达", "description": "确认已经到达目标位置", "visual_cue": "📍"}
                    ]
                }
            },
            "equipment": {
                "equip_item": {
                    "steps": [
                        {"action": "打开背包", "description": "点击背包图标打开物品栏", "visual_cue": "🎒"},
                        {"action": "选择装备", "description": "找到要装备的物品", "visual_cue": "👕"},
                        {"action": "装备物品", "description": "点击装备按钮", "visual_cue": "⚔️"},
                        {"action": "确认装备", "description": "确认装备成功", "visual_cue": "✅"}
                    ]
                },
                "upgrade_item": {
                    "steps": [
                        {"action": "找到升级", "description": "在装备界面找到升级选项", "visual_cue": "⬆️"},
                        {"action": "选择材料", "description": "选择升级所需的材料", "visual_cue": "💎"},
                        {"action": "确认升级", "description": "点击升级按钮", "visual_cue": "🔨"},
                        {"action": "查看结果", "description": "查看升级后的属性", "visual_cue": "📊"}
                    ]
                }
            },
            "social": {
                "add_friend": {
                    "steps": [
                        {"action": "打开好友", "description": "点击好友按钮打开好友列表", "visual_cue": "👥"},
                        {"action": "添加好友", "description": "点击添加好友按钮", "visual_cue": "➕"},
                        {"action": "输入信息", "description": "输入好友的游戏ID或昵称", "visual_cue": "✏️"},
                        {"action": "发送请求", "description": "点击发送好友请求", "visual_cue": "📤"},
                        {"action": "等待确认", "description": "等待对方接受好友请求", "visual_cue": "⏳"}
                    ]
                },
                "join_team": {
                    "steps": [
                        {"action": "找到组队", "description": "在游戏界面找到组队功能", "visual_cue": "👥"},
                        {"action": "创建队伍", "description": "点击创建队伍按钮", "visual_cue": "➕"},
                        {"action": "邀请好友", "description": "从好友列表邀请玩家", "visual_cue": "📨"},
                        {"action": "等待加入", "description": "等待好友加入队伍", "visual_cue": "⏳"},
                        {"action": "开始游戏", "description": "所有成员加入后开始游戏", "visual_cue": "🎮"}
                    ]
                }
            },
            "task": {
                "complete_quest": {
                    "steps": [
                        {"action": "查看任务", "description": "打开任务面板查看任务详情", "visual_cue": "📋"},
                        {"action": "前往地点", "description": "按照任务指引前往指定地点", "visual_cue": "🗺️"},
                        {"action": "完成任务", "description": "完成任务要求的目标", "visual_cue": "🎯"},
                        {"action": "返回交任务", "description": "返回NPC处提交任务", "visual_cue": "🏠"},
                        {"action": "领取奖励", "description": "领取任务完成奖励", "visual_cue": "🎁"}
                    ]
                }
            }
        }
    
    async def generate_guide(
        self, 
        task: str, 
        user_context: Dict[str, Any],
        difficulty_level: str = "beginner"
    ) -> List[Dict[str, Any]]:
        """
        生成分步引导
        
        Args:
            task: 要完成的任务描述
            user_context: 用户上下文信息
            difficulty_level: 难度等级 (beginner/intermediate/advanced)
            
        Returns:
            分步引导列表
        """
        try:
            # 1. 分析任务类型
            task_type = await self._analyze_task_type(task)
            
            # 2. 获取基础步骤模板
            base_steps = await self._get_base_steps(task_type, task)
            
            # 3. 根据用户类型调整步骤
            adjusted_steps = await self._adjust_steps_for_user(base_steps, user_context)
            
            # 4. 根据难度等级调整步骤
            final_steps = await self._adjust_steps_for_difficulty(adjusted_steps, difficulty_level)
            
            # 5. 添加进度跟踪
            steps_with_progress = await self._add_progress_tracking(final_steps, user_context)
            
            # 6. 添加无障碍支持
            accessible_steps = await self._add_accessibility_features(steps_with_progress, user_context)
            
            return accessible_steps
            
        except Exception as e:
            return await self._create_fallback_guide(task, user_context)
    
    async def _analyze_task_type(self, task: str) -> str:
        """分析任务类型"""
        task_lower = task.lower()
        
        # 操作类任务
        if any(keyword in task_lower for keyword in ["点击", "选择", "进入", "打开", "关闭"]):
            return "operation"
        # 装备类任务
        elif any(keyword in task_lower for keyword in ["装备", "武器", "道具", "升级", "强化"]):
            return "equipment"
        # 社交类任务
        elif any(keyword in task_lower for keyword in ["好友", "组队", "邀请", "聊天"]):
            return "social"
        # 任务类
        elif any(keyword in task_lower for keyword in ["任务", "完成", "目标", "挑战"]):
            return "task"
        else:
            return "operation"  # 默认为操作类
    
    async def _get_base_steps(self, task_type: str, task: str) -> List[Dict[str, Any]]:
        """获取基础步骤"""
        # 尝试从模板中匹配具体操作
        templates = self.step_templates.get(task_type, {})
        
        # 根据任务描述匹配最合适的模板
        best_template = None
        best_score = 0
        
        for template_name, template_data in templates.items():
            score = await self._calculate_template_match_score(task, template_name)
            if score > best_score:
                best_score = score
                best_template = template_data
        
        if best_template:
            return best_template["steps"]
        else:
            # 如果没有匹配的模板，生成通用步骤
            return await self._generate_generic_steps(task)
    
    async def _calculate_template_match_score(self, task: str, template_name: str) -> float:
        """计算模板匹配分数"""
        task_words = set(task.lower().split())
        template_words = set(template_name.split("_"))
        
        if not task_words or not template_words:
            return 0.0
        
        intersection = len(task_words.intersection(template_words))
        union = len(task_words.union(template_words))
        
        return intersection / union if union > 0 else 0.0
    
    async def _generate_generic_steps(self, task: str) -> List[Dict[str, Any]]:
        """生成通用步骤"""
        return [
            {
                "action": "准备操作",
                "description": "仔细阅读任务要求，了解需要完成的目标",
                "visual_cue": "📖",
                "estimated_time": "30秒"
            },
            {
                "action": "开始执行",
                "description": "按照要求开始执行任务",
                "visual_cue": "🚀",
                "estimated_time": "2分钟"
            },
            {
                "action": "检查结果",
                "description": "检查任务是否完成，确认结果",
                "visual_cue": "✅",
                "estimated_time": "30秒"
            }
        ]
    
    async def _adjust_steps_for_user(self, steps: List[Dict[str, Any]], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据用户类型调整步骤"""
        user_type = user_context.get("user_type", "normal")
        
        adjusted_steps = []
        for step in steps:
            adjusted_step = step.copy()
            
            if user_type == "elderly":
                # 老年用户：增加详细说明和视觉提示
                adjusted_step["description"] = await self._simplify_description(step["description"])
                adjusted_step["tips"] = await self._add_elderly_tips(step["action"])
                adjusted_step["voice_hint"] = f"语音提示：{step['description']}"
                
            elif user_type == "visual_impairment":
                # 视障用户：增加语音描述和触觉反馈
                adjusted_step["voice_description"] = step["description"]
                adjusted_step["haptic_feedback"] = await self._get_haptic_feedback(step["action"])
                
            elif user_type == "hearing_impairment":
                # 听障用户：增加视觉提示
                adjusted_step["visual_emphasis"] = True
                adjusted_step["text_size"] = "large"
            
            adjusted_steps.append(adjusted_step)
        
        return adjusted_steps
    
    async def _simplify_description(self, description: str) -> str:
        """简化描述语言"""
        # 替换复杂词汇
        replacements = {
            "操作": "动作",
            "界面": "屏幕",
            "按钮": "按键",
            "菜单": "选项",
            "确认": "确定",
            "执行": "做"
        }
        
        simplified = description
        for old, new in replacements.items():
            simplified = simplified.replace(old, new)
        
        return simplified
    
    async def _add_elderly_tips(self, action: str) -> str:
        """为老年用户添加提示"""
        tips_map = {
            "点击": "如果点击没有反应，可以稍微用力一点",
            "选择": "不确定选择什么时，可以请家人帮忙",
            "等待": "加载可能需要一些时间，请耐心等待",
            "确认": "如果不确定，可以重新检查一遍"
        }
        
        for keyword, tip in tips_map.items():
            if keyword in action:
                return tip
        
        return "如果遇到困难，可以请家人协助"
    
    async def _get_haptic_feedback(self, action: str) -> str:
        """获取触觉反馈"""
        haptic_map = {
            "点击": "短震一次",
            "选择": "长震一次",
            "确认": "震动两次",
            "错误": "震动三次"
        }
        
        for keyword, feedback in haptic_map.items():
            if keyword in action:
                return feedback
        
        return "无特殊反馈"
    
    async def _adjust_steps_for_difficulty(self, steps: List[Dict[str, Any]], difficulty_level: str) -> List[Dict[str, Any]]:
        """根据难度等级调整步骤"""
        difficulty_config = self.step_difficulty_levels.get(difficulty_level, self.step_difficulty_levels["beginner"])
        max_steps = difficulty_config["max_steps"]
        detail_level = difficulty_config["detail_level"]
        
        # 限制步骤数量
        if len(steps) > max_steps:
            steps = steps[:max_steps]
        
        # 根据详细程度调整描述
        adjusted_steps = []
        for step in steps:
            adjusted_step = step.copy()
            
            if detail_level == "low":
                # 简化描述
                adjusted_step["description"] = step["action"]
            elif detail_level == "high":
                # 增加更多细节
                adjusted_step["detailed_description"] = await self._add_detailed_description(step)
            
            adjusted_steps.append(adjusted_step)
        
        return adjusted_steps
    
    async def _add_detailed_description(self, step: Dict[str, Any]) -> str:
        """添加详细描述"""
        action = step["action"]
        base_description = step["description"]
        
        detailed_templates = {
            "点击": f"{base_description}。请确保手指完全接触屏幕，点击后稍等片刻观察反应。",
            "选择": f"{base_description}。可以上下滑动查看所有选项，选择后会有高亮显示。",
            "等待": f"{base_description}。如果等待时间超过30秒，可以尝试重新操作。",
            "确认": f"{base_description}。请仔细检查所有信息是否正确，确认后无法撤销。"
        }
        
        for keyword, template in detailed_templates.items():
            if keyword in action:
                return template
        
        return f"{base_description}。请按照提示操作，如有疑问可以寻求帮助。"
    
    async def _add_progress_tracking(self, steps: List[Dict[str, Any]], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """添加进度跟踪"""
        user_id = user_context.get("user_id", "anonymous")
        
        steps_with_progress = []
        for i, step in enumerate(steps):
            step_with_progress = step.copy()
            step_with_progress["step_number"] = i + 1
            step_with_progress["total_steps"] = len(steps)
            step_with_progress["progress_percentage"] = int((i + 1) / len(steps) * 100)
            step_with_progress["is_completed"] = False
            step_with_progress["completion_time"] = None
            
            steps_with_progress.append(step_with_progress)
        
        return steps_with_progress
    
    async def _add_accessibility_features(self, steps: List[Dict[str, Any]], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """添加无障碍功能"""
        accessible_steps = []
        
        for step in steps:
            accessible_step = step.copy()
            
            # 添加高对比度支持
            accessible_step["high_contrast"] = True
            
            # 添加大字体支持
            accessible_step["large_font"] = True
            
            # 添加语音支持
            accessible_step["voice_support"] = True
            
            # 添加键盘导航支持
            accessible_step["keyboard_navigation"] = True
            
            # 添加屏幕阅读器支持
            accessible_step["screen_reader_support"] = True
            
            accessible_steps.append(accessible_step)
        
        return accessible_steps
    
    async def mark_step_completed(self, user_id: str, step_number: int, task_id: str):
        """标记步骤完成"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        
        if task_id not in self.user_progress[user_id]:
            self.user_progress[user_id][task_id] = {}
        
        self.user_progress[user_id][task_id][step_number] = {
            "completed": True,
            "completion_time": datetime.now().isoformat()
        }
    
    async def get_user_progress(self, user_id: str, task_id: str) -> Dict[str, Any]:
        """获取用户进度"""
        if user_id not in self.user_progress or task_id not in self.user_progress[user_id]:
            return {"completed_steps": [], "total_steps": 0, "progress_percentage": 0}
        
        user_task_progress = self.user_progress[user_id][task_id]
        completed_steps = list(user_task_progress.keys())
        
        return {
            "completed_steps": completed_steps,
            "total_steps": len(user_task_progress),
            "progress_percentage": len(completed_steps) / len(user_task_progress) * 100 if user_task_progress else 0
        }
    
    async def reset_user_progress(self, user_id: str, task_id: str):
        """重置用户进度"""
        if user_id in self.user_progress and task_id in self.user_progress[user_id]:
            del self.user_progress[user_id][task_id]
    
    async def _create_fallback_guide(self, task: str, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建备用引导"""
        return [
            {
                "step_number": 1,
                "action": "明确信息",
                "description": "仔细阅读并理解系统的文字解答",
                "visual_cue": "📖",
                "tips": "如果字体较小，可使用设备的放大功能",
                "estimated_time": "1分钟"
            },
            {
                "step_number": 2,
                "action": "实践应用",
                "description": "在真实的对局或游戏场景中尝试此技巧",
                "visual_cue": "🎯",
                "tips": "熟能生巧，不要害怕失败",
                "estimated_time": "5分钟"
            },
            {
                "step_number": 3,
                "action": "总结调整",
                "description": "根据结果总结经验并随时向我提问",
                "visual_cue": "✅",
                "tips": "可以随时开始新的对话向我寻求进一步帮助",
                "estimated_time": "30秒"
            }
        ]
