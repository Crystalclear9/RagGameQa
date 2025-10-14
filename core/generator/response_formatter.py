# 响应格式化器
from typing import Dict, Any, Optional
import re

try:
    from pypinyin import lazy_pinyin
except Exception:
    lazy_pinyin = None  # 可选依赖


class ResponseFormatter:
    """响应格式化器，根据用户需求格式化响应"""

    def __init__(self, game_id: str):
        self.game_id = game_id

    async def format(self, response: str, user_context: Optional[Dict] = None) -> str:
        """
        格式化响应

        Args:
            response: 原始响应
            user_context: 用户上下文

        Returns:
            格式化后的响应
        """
        # 1. 基础格式化
        formatted_response = self._basic_format(response)

        # 2. 根据用户类型特殊格式化
        if user_context:
            formatted_response = self._user_specific_format(
                formatted_response, user_context
            )

        # 3. 添加无障碍支持
        formatted_response = self._add_accessibility_features(
            formatted_response, user_context
        )

        return formatted_response

    def _basic_format(self, response: str) -> str:
        """基础格式化"""
        # 清理多余的空格和换行
        response = re.sub(r"\n\s*\n", "\n\n", response)
        response = response.strip()

        # 添加适当的标点符号
        if not response.endswith((".", "!", "?", "。", "！", "？")):
            response += "。"

        return response

    def _user_specific_format(self, response: str, user_context: Dict) -> str:
        """根据用户类型特殊格式化"""
        user_type = user_context.get("user_type", "normal")

        if user_type == "elderly":
            # 老年用户：使用更简单的语言，步骤化表达
            response = self._simplify_for_elderly(response)
        elif user_type == "visual_impairment":
            # 视障用户：添加语音提示
            response = self._add_voice_hints(response)
        elif user_type == "hearing_impairment":
            # 听障用户：添加视觉提示
            response = self._add_visual_hints(response)

        return response

    def _simplify_for_elderly(self, response: str) -> str:
        """为老年用户简化语言"""
        # 替换复杂词汇
        replacements = {
            "技能": "能力",
            "装备": "道具",
            "副本": "关卡",
            "任务": "工作",
            "宏": "快捷操作",
            "机制": "规则",
        }

        for old, new in replacements.items():
            response = response.replace(old, new)

        # 简单步骤化（尝试将长句断句）
        response = response.replace("；", "。").replace(";", ".")
        return response

    def _add_voice_hints(self, response: str) -> str:
        """为视障用户添加语音提示"""
        response = response.replace("注意：", "[语音提示] 注意：")
        response = response.replace("重要：", "[语音提示] 重要：")
        return response

    def _add_visual_hints(self, response: str) -> str:
        """为听障用户添加视觉提示"""
        response = response.replace("注意：", "[视觉提示] 注意：")
        response = response.replace("重要：", "[视觉提示] 重要：")
        return response

    def _add_accessibility_features(
        self, response: str, user_context: Optional[Dict]
    ) -> str:
        """添加无障碍功能"""
        if not user_context:
            return response

        # 添加拼音标注（如果需要且依赖可用）
        if user_context.get("need_pinyin", False) and lazy_pinyin is not None:
            response = self._add_pinyin(response)

        return response

    def _add_pinyin(self, text: str) -> str:
        """添加拼音标注（简易实现：每个汉字后加括号拼音）"""
        if lazy_pinyin is None:
            return text

        result_chars = []
        for ch in text:
            # 仅对中文字符标注
            if "\u4e00" <= ch <= "\u9fff":
                p = lazy_pinyin(ch)[0]
                result_chars.append(f"{ch}({p})")
            else:
                result_chars.append(ch)
        return "".join(result_chars)
