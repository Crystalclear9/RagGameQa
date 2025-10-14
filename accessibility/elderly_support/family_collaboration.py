# 祖孙协作模式
from typing import Dict, Any, List, Optional
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io
from pypinyin import lazy_pinyin, Style

class FamilyCollaboration:
    """祖孙协作模式，支持老年人语音提问→系统生成带拼音标注的图文指南"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.font_size = 24
        self.line_height = 35
        self.max_width = 800
        self.pinyin_color = (100, 100, 100)  # 灰色拼音
        self.text_color = (0, 0, 0)  # 黑色文字
        self.highlight_color = (255, 165, 0)  # 橙色高亮
        
    async def generate_family_guide(
        self, 
        question: str, 
        answer: str, 
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成家庭协作指南
        
        Args:
            question: 老年人提出的问题
            answer: 系统生成的答案
            user_context: 用户上下文信息
            
        Returns:
            包含图文指南的字典
        """
        try:
            # 1. 分析问题类型
            question_type = await self._analyze_question_type(question)
            
            # 2. 生成分步指南
            step_guide = await self._generate_step_guide(answer, question_type)
            
            # 3. 创建带拼音标注的图文指南
            guide_image = await self._create_guide_image(question, answer, step_guide)
            
            # 4. 生成语音说明
            voice_guide = await self._generate_voice_guide(step_guide)
            
            # 5. 创建分享内容
            share_content = await self._create_share_content(question, answer, step_guide)
            
            return {
                "guide_type": question_type,
                "step_guide": step_guide,
                "guide_image": guide_image,
                "voice_guide": voice_guide,
                "share_content": share_content,
                "family_tips": await self._generate_family_tips(question_type),
                "accessibility_features": await self._add_accessibility_features(step_guide)
            }
            
        except Exception as e:
            return {
                "error": f"生成家庭协作指南失败: {str(e)}",
                "fallback_content": await self._create_fallback_guide(question, answer)
            }
    
    async def _analyze_question_type(self, question: str) -> str:
        """分析问题类型"""
        # 游戏操作相关关键词
        operation_keywords = ["怎么", "如何", "操作", "点击", "选择", "进入"]
        # 装备技能相关
        equipment_keywords = ["装备", "技能", "武器", "道具", "获得"]
        # 任务相关
        task_keywords = ["任务", "完成", "目标", "要求"]
        # 社交相关
        social_keywords = ["组队", "好友", "聊天", "公会"]
        
        question_lower = question.lower()
        
        if any(keyword in question for keyword in operation_keywords):
            return "operation_guide"  # 操作指南
        elif any(keyword in question for keyword in equipment_keywords):
            return "equipment_guide"  # 装备指南
        elif any(keyword in question for keyword in task_keywords):
            return "task_guide"  # 任务指南
        elif any(keyword in question for keyword in social_keywords):
            return "social_guide"  # 社交指南
        else:
            return "general_guide"  # 通用指南
    
    async def _generate_step_guide(self, answer: str, question_type: str) -> List[Dict[str, Any]]:
        """生成分步指南"""
        steps = []
        
        # 根据问题类型生成不同的步骤
        if question_type == "operation_guide":
            steps = await self._parse_operation_steps(answer)
        elif question_type == "equipment_guide":
            steps = await self._parse_equipment_steps(answer)
        elif question_type == "task_guide":
            steps = await self._parse_task_steps(answer)
        elif question_type == "social_guide":
            steps = await self._parse_social_steps(answer)
        else:
            steps = await self._parse_general_steps(answer)
        
        # 为每个步骤添加拼音标注
        for i, step in enumerate(steps):
            step["step_number"] = i + 1
            step["pinyin"] = await self._add_pinyin_annotation(step["description"])
            step["visual_cues"] = await self._add_visual_cues(step["description"])
        
        return steps
    
    async def _parse_operation_steps(self, answer: str) -> List[Dict[str, Any]]:
        """解析操作步骤"""
        # 简单的步骤解析（实际应该使用更复杂的NLP技术）
        steps = []
        
        # 查找步骤指示词
        step_indicators = ["第一步", "第二步", "第三步", "然后", "接着", "最后"]
        
        sentences = answer.split("。")
        current_step = {"description": "", "action": "", "location": ""}
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 检查是否是步骤开始
            if any(indicator in sentence for indicator in step_indicators):
                if current_step["description"]:
                    steps.append(current_step)
                current_step = {
                    "description": sentence,
                    "action": await self._extract_action(sentence),
                    "location": await self._extract_location(sentence)
                }
            else:
                current_step["description"] += "。" + sentence
        
        if current_step["description"]:
            steps.append(current_step)
        
        return steps if steps else [{"description": answer, "action": "查看", "location": "游戏界面"}]
    
    async def _parse_equipment_steps(self, answer: str) -> List[Dict[str, Any]]:
        """解析装备相关步骤"""
        return await self._parse_general_steps(answer)
    
    async def _parse_task_steps(self, answer: str) -> List[Dict[str, Any]]:
        """解析任务相关步骤"""
        return await self._parse_general_steps(answer)
    
    async def _parse_social_steps(self, answer: str) -> List[Dict[str, Any]]:
        """解析社交相关步骤"""
        return await self._parse_general_steps(answer)
    
    async def _parse_general_steps(self, answer: str) -> List[Dict[str, Any]]:
        """解析通用步骤"""
        # 将答案分解为简单步骤
        sentences = [s.strip() for s in answer.split("。") if s.strip()]
        
        steps = []
        for i, sentence in enumerate(sentences[:5]):  # 最多5个步骤
            steps.append({
                "description": sentence,
                "action": await self._extract_action(sentence),
                "location": await self._extract_location(sentence)
            })
        
        return steps
    
    async def _extract_action(self, text: str) -> str:
        """提取动作"""
        action_keywords = {
            "点击": "click",
            "选择": "select", 
            "进入": "enter",
            "打开": "open",
            "关闭": "close",
            "查看": "view",
            "获得": "get",
            "使用": "use"
        }
        
        for keyword, action in action_keywords.items():
            if keyword in text:
                return action
        
        return "follow"
    
    async def _extract_location(self, text: str) -> str:
        """提取位置信息"""
        location_keywords = ["界面", "菜单", "背包", "技能", "任务", "地图"]
        
        for keyword in location_keywords:
            if keyword in text:
                return keyword
        
        return "游戏界面"
    
    async def _add_pinyin_annotation(self, text: str) -> str:
        """添加拼音标注"""
        try:
            # 使用pypinyin生成拼音
            pinyin_list = lazy_pinyin(text, style=Style.TONE)
            return " ".join(pinyin_list)
        except Exception:
            return text
    
    async def _add_visual_cues(self, text: str) -> List[str]:
        """添加视觉提示"""
        cues = []
        
        # 检测关键操作词
        if "点击" in text:
            cues.append("🖱️ 点击操作")
        if "选择" in text:
            cues.append("👆 选择操作")
        if "进入" in text:
            cues.append("🚪 进入操作")
        if "获得" in text:
            cues.append("🎁 获得物品")
        
        return cues
    
    async def _create_guide_image(
        self, 
        question: str, 
        answer: str, 
        steps: List[Dict[str, Any]]
    ) -> str:
        """创建图文指南"""
        try:
            # 计算图片高度
            total_height = 100 + len(steps) * 120  # 标题 + 步骤
            
            # 创建图片
            img = Image.new('RGB', (self.max_width, total_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # 尝试加载字体
            try:
                font_large = ImageFont.truetype("arial.ttf", 28)
                font_normal = ImageFont.truetype("arial.ttf", self.font_size)
                font_small = ImageFont.truetype("arial.ttf", 18)
            except:
                font_large = ImageFont.load_default()
                font_normal = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # 绘制标题
            title = f"《{self.game_id}》游戏指南"
            draw.text((20, 20), title, fill=self.text_color, font=font_large)
            
            # 绘制问题
            question_text = f"问题：{question}"
            draw.text((20, 60), question_text, fill=self.text_color, font=font_normal)
            
            # 绘制步骤
            y_offset = 100
            for step in steps:
                # 步骤编号
                step_text = f"第{step['step_number']}步："
                draw.text((20, y_offset), step_text, fill=self.highlight_color, font=font_normal)
                
                # 步骤描述
                description = step['description']
                draw.text((20, y_offset + 30), description, fill=self.text_color, font=font_normal)
                
                # 拼音标注
                if 'pinyin' in step:
                    pinyin_text = step['pinyin']
                    draw.text((20, y_offset + 60), pinyin_text, fill=self.pinyin_color, font=font_small)
                
                # 视觉提示
                if 'visual_cues' in step and step['visual_cues']:
                    cues_text = " ".join(step['visual_cues'])
                    draw.text((20, y_offset + 80), cues_text, fill=self.highlight_color, font=font_small)
                
                y_offset += 120
            
            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            return f"图片生成失败: {str(e)}"
    
    async def _generate_voice_guide(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成语音指南"""
        voice_text = "游戏指南语音说明：\n"
        
        for step in steps:
            voice_text += f"第{step['step_number']}步：{step['description']}\n"
            if 'pinyin' in step:
                voice_text += f"拼音：{step['pinyin']}\n"
        
        return {
            "text": voice_text,
            "duration": len(voice_text) * 0.1,  # 估算时长
            "speed": "slow",  # 慢速播放
            "language": "zh-CN"
        }
    
    async def _create_share_content(
        self, 
        question: str, 
        answer: str, 
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建分享内容"""
        share_text = f"🎮 {self.game_id} 游戏指南\n\n"
        share_text += f"❓ 问题：{question}\n\n"
        share_text += "📋 操作步骤：\n"
        
        for step in steps:
            share_text += f"{step['step_number']}. {step['description']}\n"
        
        share_text += "\n💡 提示：可以保存图片到相册，随时查看！"
        
        return {
            "text": share_text,
            "image": await self._create_guide_image(question, answer, steps),
            "wechat_format": share_text,
            "family_group_tips": await self._generate_family_group_tips()
        }
    
    async def _generate_family_tips(self, question_type: str) -> List[str]:
        """生成家庭协作提示"""
        tips = {
            "operation_guide": [
                "可以让家人帮忙点击屏幕",
                "建议先熟悉基本操作再尝试复杂功能",
                "遇到困难时可以截图发给家人"
            ],
            "equipment_guide": [
                "装备选择可以咨询有经验的家人",
                "建议先了解装备属性再购买",
                "可以请家人帮忙查看装备效果"
            ],
            "task_guide": [
                "任务可以分步骤完成，不用着急",
                "遇到卡关可以请家人协助",
                "建议记录任务进度，避免重复"
            ],
            "social_guide": [
                "社交功能可以让家人帮忙设置",
                "建议先了解基本功能再添加好友",
                "遇到问题可以请家人协助处理"
            ],
            "general_guide": [
                "游戏需要慢慢学习，不用着急",
                "遇到问题可以随时咨询家人",
                "建议定期休息，保护眼睛"
            ]
        }
        
        return tips.get(question_type, tips["general_guide"])
    
    async def _add_accessibility_features(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """添加无障碍功能"""
        return {
            "high_contrast": True,  # 高对比度
            "large_font": True,  # 大字体
            "voice_navigation": True,  # 语音导航
            "step_by_step": True,  # 分步引导
            "family_sharing": True,  # 家庭分享
            "pinyin_support": True,  # 拼音支持
            "visual_cues": True  # 视觉提示
        }
    
    async def _create_fallback_guide(self, question: str, answer: str) -> Dict[str, Any]:
        """创建备用指南"""
        return {
            "question": question,
            "answer": answer,
            "simple_steps": [
                {
                    "step": 1,
                    "description": "仔细阅读游戏界面",
                    "pinyin": "zǐ xì yuè dú yóu xì jiè miàn"
                },
                {
                    "step": 2,
                    "description": "按照提示进行操作",
                    "pinyin": "àn zhào tí shì jìn xíng cāo zuò"
                },
                {
                    "step": 3,
                    "description": "遇到问题可以咨询家人",
                    "pinyin": "yù dào wèn tí kě yǐ zī xún jiā rén"
                }
            ],
            "family_tips": [
                "游戏需要慢慢学习，不用着急",
                "遇到问题可以随时咨询家人",
                "建议定期休息，保护眼睛"
            ]
        }
    
    async def generate_family_group_tips(self) -> List[str]:
        """生成家庭群分享提示"""
        return [
            "📱 可以长按图片保存到相册",
            "🔗 分享链接给其他家庭成员",
            "💬 在家庭群里讨论游戏技巧",
            "📞 遇到问题可以语音通话求助",
            "⏰ 建议设置游戏时间提醒"
        ]
