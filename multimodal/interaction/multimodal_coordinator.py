# 多模态协调器
from typing import Dict, Any, Optional, List
import logging
from multimodal.speech.asr_service import ASRService
from multimodal.visual.image_descriptor import ImageDescriptor
from multimodal.haptic.vibration_encoder import VibrationEncoder

logger = logging.getLogger(__name__)


class MultimodalCoordinator:
    """多模态交互协调器

    负责编排语音、视觉、触觉子模块的调用顺序与结果整合，
    提供多模态输入的一站式处理与输出聚合。
    """

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.speech_service = ASRService(game_id)
        self.visual_service = ImageDescriptor(game_id)
        self.haptic_service = VibrationEncoder(game_id)

    async def process_multimodal_input(
        self,
        input_data: Dict[str, Any],
        user_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """处理多模态输入

        支持的输入键：
        - audio: bytes 音频数据
        - image: bytes 图像数据
        - haptic_feedback: str 触觉反馈类型
        - custom_patterns: List[List[int]] 自定义触觉模式序列
        """
        results: Dict[str, Any] = {"game_id": self.game_id}

        try:
            # 语音
            if "audio" in input_data and input_data["audio"] is not None:
                speech_result = await self.speech_service.recognize_speech(
                    input_data["audio"], language=(user_context or {}).get("language", "zh-CN")
                )
                results["speech"] = speech_result

            # 视觉
            if "image" in input_data and input_data["image"] is not None:
                # ImageDescriptor为占位，保持接口一致
                try:
                    visual_result = await self.visual_service.describe_image(
                        input_data["image"],
                        user_context=user_context,
                    )
                except Exception:
                    # 若未实现，返回占位结果
                    visual_result = {
                        "description": "图像描述模块未实现，占位结果。",
                        "tags": [],
                        "objects": [],
                    }
                results["visual"] = visual_result

            # 触觉
            if "haptic_feedback" in input_data and input_data["haptic_feedback"]:
                pattern = await self.haptic_service.encode_feedback(
                    input_data["haptic_feedback"],
                    (user_context or {}).get("intensity", 0.5),
                )
                ok = await self.haptic_service.send_vibration(
                    pattern, (user_context or {}).get("device_id", "default"), user_context
                )
                results["haptic"] = {"pattern": pattern, "sent": ok}

            # 自定义触觉序列
            if "custom_patterns" in input_data and isinstance(input_data["custom_patterns"], list):
                seq_ok = await self.haptic_service.send_sequence_vibration(
                    input_data["custom_patterns"], (user_context or {}).get("device_id", "default")
                )
                results.setdefault("haptic", {})["sequence_sent"] = seq_ok

        except Exception as e:
            logger.error(f"多模态处理失败: {e}")
            results["error"] = str(e)

        return results
