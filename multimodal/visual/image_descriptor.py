# 图像描述生成器
from typing import Optional, Dict, Any, List
import io
from PIL import Image
import cv2
import numpy as np


class ImageDescriptor:
    """图像描述生成器，为视障玩家生成带空间定位的按钮图解（轻量实现）"""

    def __init__(self, game_id: str):
        self.game_id = game_id

    async def describe_image(
        self,
        image_data: bytes,
        user_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        生成图像描述（使用传统CV方法占位，避免重量模型依赖）
        """
        try:
            # 1. 图像预处理
            processed_image = await self._preprocess_image(image_data)

            # 2. 检测UI元素
            ui_elements = await self._detect_ui_elements(processed_image)

            # 3. 生成基础描述（占位：按元素数量组织）
            base_description = self._build_base_description(ui_elements)

            # 4. 生成空间定位描述
            spatial_description = await self._generate_spatial_description(ui_elements)

            # 5. 定制描述
            customized_description = await self._customize_description(
                base_description, spatial_description, user_context
            )

            return {
                "description": customized_description,
                "ui_elements": ui_elements,
                "spatial_info": spatial_description,
                "accessibility_features": await self._extract_accessibility_features(ui_elements),
            }

        except Exception as e:
            return {
                "description": f"图像描述生成失败: {str(e)}",
                "ui_elements": [],
                "spatial_info": "",
                "accessibility_features": [],
            }

    async def _preprocess_image(self, image_data: bytes) -> Image.Image:
        image = Image.open(io.BytesIO(image_data))
        if image.mode != "RGB":
            image = image.convert("RGB")
        max_size = 512
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return image

    async def _detect_ui_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        buttons = await self._detect_buttons(cv_image)
        text_regions = await self._detect_text_regions(cv_image)
        icons = await self._detect_icons(cv_image)
        return [*buttons, *text_regions, *icons]

    async def _detect_buttons(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        buttons: List[Dict[str, Any]] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                buttons.append(
                    {
                        "type": "button",
                        "position": {"x": x + w // 2, "y": y + h // 2},
                        "size": {"width": w, "height": h},
                        "bounds": {"x": x, "y": y, "width": w, "height": h},
                    }
                )
        return buttons

    async def _detect_text_regions(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        dilated = cv2.dilate(gray, kernel, iterations=1)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        text_regions: List[Dict[str, Any]] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                text_regions.append(
                    {
                        "type": "text",
                        "position": {"x": x + w // 2, "y": y + h // 2},
                        "size": {"width": w, "height": h},
                        "bounds": {"x": x, "y": y, "width": w, "height": h},
                    }
                )
        return text_regions

    async def _detect_icons(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        # 使用ORB替代SIFT（避免专利问题且更轻量）
        orb = cv2.ORB_create(nfeatures=200)
        keypoints = orb.detect(gray, None)
        icons: List[Dict[str, Any]] = []
        for kp in keypoints:
            icons.append(
                {
                    "type": "icon",
                    "position": {"x": int(kp.pt[0]), "y": int(kp.pt[1])},
                    "size": {"width": 20, "height": 20},
                    "response": getattr(kp, "response", 0.0),
                }
            )
        return icons

    def _build_base_description(self, ui_elements: List[Dict[str, Any]]) -> str:
        num_buttons = sum(1 for e in ui_elements if e.get("type") == "button")
        num_texts = sum(1 for e in ui_elements if e.get("type") == "text")
        num_icons = sum(1 for e in ui_elements if e.get("type") == "icon")
        return f"检测到{num_buttons}个按钮、{num_texts}处文本与{num_icons}个图标"

    async def _generate_spatial_description(self, ui_elements: List[Dict]) -> str:
        if not ui_elements:
            return "未检测到明显的UI元素"
        descs = []
        for element in ui_elements[:6]:  # 最多口播6条
            element_type = element.get("type", "元素")
            position = element.get("position", {})
            size = element.get("size", {})
            relative_position = self._calculate_relative_position(position, size)
            descs.append(f"在{relative_position}位置有{element_type}")
        return "；".join(descs)

    def _calculate_relative_position(self, position: Dict, size: Dict) -> str:
        x = position.get("x", 0)
        y = position.get("y", 0)
        image_width, image_height = 512, 512
        rel_x = x / image_width
        rel_y = y / image_height
        x_desc = "左侧" if rel_x < 0.3 else ("右侧" if rel_x > 0.7 else "中间")
        y_desc = "上方" if rel_y < 0.3 else ("下方" if rel_y > 0.7 else "中间")
        return f"{y_desc}{x_desc}"

    async def _customize_description(
        self, base_description: str, spatial_description: str, user_context: Optional[Dict]
    ) -> str:
        if not user_context:
            return f"{base_description}。{spatial_description}"
        user_type = user_context.get("user_type", "normal")
        if user_type == "visual_impairment":
            return f"这是一个游戏界面。{spatial_description}。建议使用语音导航进行操作。"
        elif user_type == "elderly":
            return f"{self._simplify_description(base_description)}。{spatial_description}"
        return f"{base_description}。{spatial_description}"

    def _simplify_description(self, description: str) -> str:
        replacements = {"界面": "屏幕", "按钮": "按键", "图标": "图案", "菜单": "选项"}
        for old, new in replacements.items():
            description = description.replace(old, new)
        return description

    async def _extract_accessibility_features(self, ui_elements: List[Dict]) -> List[str]:
        features: List[str] = []
        for element in ui_elements:
            if element.get("type") == "button":
                features.append("可点击按钮")
            elif element.get("type") == "text":
                features.append("文本信息")
            elif element.get("type") == "icon":
                features.append("图标元素")
        return features
