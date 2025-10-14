# 图像描述生成器
from typing import Optional, Dict, Any, List
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import cv2
import numpy as np

class ImageDescriptor:
    """图像描述生成器，为视障玩家生成带空间定位的按钮图解"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
    
    async def describe_image(
        self, 
        image_data: bytes, 
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成图像描述
        
        Args:
            image_data: 图像数据
            user_context: 用户上下文
            
        Returns:
            图像描述结果
        """
        try:
            # 1. 图像预处理
            processed_image = await self._preprocess_image(image_data)
            
            # 2. 检测UI元素
            ui_elements = await self._detect_ui_elements(processed_image)
            
            # 3. 生成基础描述
            base_description = await self._generate_base_description(processed_image)
            
            # 4. 生成空间定位描述
            spatial_description = await self._generate_spatial_description(ui_elements)
            
            # 5. 根据用户类型定制描述
            customized_description = await self._customize_description(
                base_description, 
                spatial_description, 
                user_context
            )
            
            return {
                "description": customized_description,
                "ui_elements": ui_elements,
                "spatial_info": spatial_description,
                "accessibility_features": await self._extract_accessibility_features(ui_elements)
            }
            
        except Exception as e:
            return {
                "description": f"图像描述生成失败: {str(e)}",
                "ui_elements": [],
                "spatial_info": "",
                "accessibility_features": []
            }
    
    async def _preprocess_image(self, image_data: bytes) -> Image.Image:
        """图像预处理"""
        # 将字节数据转换为PIL图像
        image = Image.open(io.BytesIO(image_data))
        
        # 转换为RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 调整大小（保持宽高比）
        max_size = 512
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        return image
    
    async def _detect_ui_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        """检测UI元素"""
        # 转换为OpenCV格式
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 检测按钮（使用模板匹配或边缘检测）
        buttons = await self._detect_buttons(cv_image)
        
        # 检测文本区域
        text_regions = await self._detect_text_regions(cv_image)
        
        # 检测图标
        icons = await self._detect_icons(cv_image)
        
        ui_elements = []
        ui_elements.extend(buttons)
        ui_elements.extend(text_regions)
        ui_elements.extend(icons)
        
        return ui_elements
    
    async def _detect_buttons(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """检测按钮"""
        # 使用边缘检测检测矩形区域
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        buttons = []
        for contour in contours:
            # 计算轮廓面积
            area = cv2.contourArea(contour)
            if area > 1000:  # 过滤小区域
                # 获取边界框
                x, y, w, h = cv2.boundingRect(contour)
                
                # 计算中心位置
                center_x = x + w // 2
                center_y = y + h // 2
                
                buttons.append({
                    "type": "button",
                    "position": {"x": center_x, "y": center_y},
                    "size": {"width": w, "height": h},
                    "bounds": {"x": x, "y": y, "width": w, "height": h}
                })
        
        return buttons
    
    async def _detect_text_regions(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """检测文本区域"""
        # 使用OCR检测文本区域
        # 这里使用简单的边缘检测作为示例
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 使用形态学操作检测文本区域
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        dilated = cv2.dilate(gray, kernel, iterations=1)
        
        # 查找轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 过滤小区域
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                
                text_regions.append({
                    "type": "text",
                    "position": {"x": center_x, "y": center_y},
                    "size": {"width": w, "height": h},
                    "bounds": {"x": x, "y": y, "width": w, "height": h}
                })
        
        return text_regions
    
    async def _detect_icons(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """检测图标"""
        # 使用特征检测检测图标
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 使用SIFT检测特征点
        sift = cv2.SIFT_create()
        keypoints, _ = sift.detectAndCompute(gray, None)
        
        icons = []
        for kp in keypoints:
            icons.append({
                "type": "icon",
                "position": {"x": int(kp.pt[0]), "y": int(kp.pt[1])},
                "size": {"width": 20, "height": 20},  # 默认大小
                "response": kp.response
            })
        
        return icons
    
    async def _generate_base_description(self, image: Image.Image) -> str:
        """生成基础图像描述"""
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            out = self.model.generate(**inputs, max_length=100)
        
        description = self.processor.decode(out[0], skip_special_tokens=True)
        return description
    
    async def _generate_spatial_description(self, ui_elements: List[Dict]) -> str:
        """生成空间定位描述"""
        if not ui_elements:
            return "未检测到明显的UI元素"
        
        descriptions = []
        
        for element in ui_elements:
            element_type = element["type"]
            position = element["position"]
            size = element["size"]
            
            # 计算相对位置
            relative_position = self._calculate_relative_position(position, size)
            
            description = f"在{relative_position}位置有一个{element_type}"
            descriptions.append(description)
        
        return "；".join(descriptions)
    
    def _calculate_relative_position(self, position: Dict, size: Dict) -> str:
        """计算相对位置描述"""
        x, y = position["x"], position["y"]
        w, h = size["width"], size["height"]
        
        # 假设图像尺寸为512x512
        image_width, image_height = 512, 512
        
        # 计算相对位置
        rel_x = x / image_width
        rel_y = y / image_height
        
        # 转换为文字描述
        if rel_x < 0.3:
            x_desc = "左侧"
        elif rel_x > 0.7:
            x_desc = "右侧"
        else:
            x_desc = "中间"
        
        if rel_y < 0.3:
            y_desc = "上方"
        elif rel_y > 0.7:
            y_desc = "下方"
        else:
            y_desc = "中间"
        
        return f"{y_desc}{x_desc}"
    
    async def _customize_description(
        self, 
        base_description: str, 
        spatial_description: str, 
        user_context: Optional[Dict]
    ) -> str:
        """根据用户类型定制描述"""
        if not user_context:
            return f"{base_description}。{spatial_description}"
        
        user_type = user_context.get('user_type', 'normal')
        
        if user_type == 'visual_impairment':
            # 视障用户：重点描述空间位置和功能
            return f"这是一个游戏界面。{spatial_description}。建议使用语音导航进行操作。"
        elif user_type == 'elderly':
            # 老年用户：使用简单语言
            simplified_description = self._simplify_description(base_description)
            return f"{simplified_description}。{spatial_description}"
        else:
            return f"{base_description}。{spatial_description}"
    
    def _simplify_description(self, description: str) -> str:
        """简化描述语言"""
        # 替换复杂词汇
        replacements = {
            "界面": "屏幕",
            "按钮": "按键",
            "图标": "图案",
            "菜单": "选项"
        }
        
        for old, new in replacements.items():
            description = description.replace(old, new)
        
        return description
    
    async def _extract_accessibility_features(self, ui_elements: List[Dict]) -> List[str]:
        """提取无障碍功能特征"""
        features = []
        
        for element in ui_elements:
            if element["type"] == "button":
                features.append("可点击按钮")
            elif element["type"] == "text":
                features.append("文本信息")
            elif element["type"] == "icon":
                features.append("图标元素")
        
        return features
