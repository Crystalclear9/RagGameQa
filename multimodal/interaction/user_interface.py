# 用户界面
from typing import Dict, Any, Optional, List
import time


class UserInterface:
    """用户界面管理器

    提供与多模态结果的轻量级桥接：
    - 将多模态输出渲染为结构化UI数据（JSON）
    - 响应用户交互事件（占位实现）
    """

    def __init__(self, game_id: str):
        self.game_id = game_id

    async def render_interface(
        self, data: Dict[str, Any], user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """渲染用户界面（返回结构化JSON，前端可直接消费）"""
        user_type = (user_context or {}).get("user_type", "normal")

        # 基础卡片
        cards: List[Dict[str, Any]] = []

        # 语音结果卡片
        if "speech" in data:
            cards.append(
                {
                    "type": "speech_result",
                    "title": "语音识别",
                    "text": data["speech"].get("text", ""),
                    "confidence": data["speech"].get("confidence", 0.0),
                }
            )

        # 视觉结果卡片
        if "visual" in data:
            cards.append(
                {
                    "type": "image_description",
                    "title": "图像描述",
                    "description": data["visual"].get("description", ""),
                    "tags": data["visual"].get("tags", []),
                    "objects": data["visual"].get("objects", []),
                }
            )

        # 触觉结果卡片
        if "haptic" in data:
            h = data["haptic"]
            cards.append(
                {
                    "type": "haptic_feedback",
                    "title": "触觉反馈",
                    "pattern": h.get("pattern", []),
                    "sent": h.get("sent", False),
                    "sequence_sent": h.get("sequence_sent"),
                }
            )

        # 头部信息
        header = {
            "game_id": self.game_id,
            "rendered_at": time.time(),
            "user_type": user_type,
        }

        # 无障碍：老年用户启用大字模式标识
        accessibility = {"large_font": user_type == "elderly"}

        return {"header": header, "cards": cards, "accessibility": accessibility}

    async def handle_user_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户交互（占位实现）"""
        action = interaction.get("action", "unknown")
        payload = interaction.get("payload", {})
        return {"action": action, "status": "received", "payload": payload}
