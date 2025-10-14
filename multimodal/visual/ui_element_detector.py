# UI元素检测器
from typing import List, Dict, Any
import io
from PIL import Image
import cv2
import numpy as np


class UIElementDetector:
    """UI元素检测器（轻量实现）"""

    def __init__(self, game_id: str):
        self.game_id = game_id

    async def detect_elements(self, image_data: bytes) -> List[Dict[str, Any]]:
        """检测UI元素（按钮/文本/图标）"""
        image = Image.open(io.BytesIO(image_data))
        if image.mode != "RGB":
            image = image.convert("RGB")
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        buttons = await self._detect_buttons(cv_image)
        texts = await self._detect_text_regions(cv_image)
        icons = await self._detect_icons(cv_image)

        return [*buttons, *texts, *icons]

    async def _detect_buttons(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        results: List[Dict[str, Any]] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1200:
                x, y, w, h = cv2.boundingRect(contour)
                results.append(
                    {
                        "type": "button",
                        "position": {"x": x + w // 2, "y": y + h // 2},
                        "size": {"width": w, "height": h},
                        "bounds": {"x": x, "y": y, "width": w, "height": h},
                    }
                )
        return results

    async def _detect_text_regions(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        dilated = cv2.dilate(gray, kernel, iterations=1)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        results: List[Dict[str, Any]] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 600:
                x, y, w, h = cv2.boundingRect(contour)
                results.append(
                    {
                        "type": "text",
                        "position": {"x": x + w // 2, "y": y + h // 2},
                        "size": {"width": w, "height": h},
                        "bounds": {"x": x, "y": y, "width": w, "height": h},
                    }
                )
        return results

    async def _detect_icons(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        orb = cv2.ORB_create(nfeatures=150)
        keypoints = orb.detect(gray, None)
        results: List[Dict[str, Any]] = []
        for kp in keypoints[:200]:
            results.append(
                {
                    "type": "icon",
                    "position": {"x": int(kp.pt[0]), "y": int(kp.pt[1])},
                    "size": {"width": 20, "height": 20},
                }
            )
        return results
