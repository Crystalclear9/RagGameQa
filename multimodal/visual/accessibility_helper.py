# 无障碍辅助
from typing import Dict, Any, Optional, List
import io
from PIL import Image


class AccessibilityHelper:
    """无障碍辅助工具

    - 生成Alt文本（占位：简单启发式）
    - 生成语音导航脚本（按UI元素顺序）
    """

    def __init__(self, game_id: str):
        self.game_id = game_id

    async def generate_alt_text(self, image_data: bytes) -> str:
        """生成Alt文本（轻量占位实现）"""
        try:
            image = Image.open(io.BytesIO(image_data))
            w, h = image.size
            mode = image.mode
            return f"{self.game_id} 游戏界面截图，尺寸 {w}x{h}，色彩模式 {mode}。"
        except Exception:
            return "游戏界面截图。"

    async def create_voice_navigation(self, ui_elements: List[Dict]) -> Dict[str, Any]:
        """创建语音导航（根据元素位置排序，输出朗读脚本）"""
        if not ui_elements:
            return {"script": ["未检测到可交互元素。"]}

        # 按从上到下、从左到右排序
        sorted_elements = sorted(
            ui_elements,
            key=lambda e: (e.get("position", {}).get("y", 0), e.get("position", {}).get("x", 0)),
        )

        script: List[str] = []
        for i, el in enumerate(sorted_elements, start=1):
            et = el.get("type", "元素")
            pos = el.get("position", {})
            script.append(
                f"第{i}项：{et}，位置x={pos.get('x', '?')}, y={pos.get('y', '?')}。"
            )

        return {"script": script}
