# 多模态协调器
from typing import Dict, Any, Optional
from multimodal.speech.asr_service import ASRService
from multimodal.visual.image_descriptor import ImageDescriptor
from multimodal.haptic.vibration_encoder import VibrationEncoder

class MultimodalCoordinator:
    """多模态交互协调器"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.speech_service = ASRService(game_id)
        self.visual_service = ImageDescriptor(game_id)
        self.haptic_service = VibrationEncoder(game_id)
    
    async def process_multimodal_input(
        self, 
        input_data: Dict[str, Any], 
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """处理多模态输入"""
        results = {}
        
        # 处理语音输入
        if 'audio' in input_data:
            speech_result = await self.speech_service.recognize_speech(
                input_data['audio'], 
                user_context=user_context
            )
            results['speech'] = speech_result
        
        # 处理视觉输入
        if 'image' in input_data:
            visual_result = await self.visual_service.describe_image(
                input_data['image'], 
                user_context=user_context
            )
            results['visual'] = visual_result
        
        # 处理触觉输入
        if 'haptic_feedback' in input_data:
            haptic_result = await self.haptic_service.encode_feedback(
                input_data['haptic_feedback']
            )
            results['haptic'] = haptic_result
        
        return results
