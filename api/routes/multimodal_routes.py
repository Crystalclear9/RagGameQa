# 多模态路由
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from multimodal.haptic.vibration_encoder import VibrationEncoder
from multimodal.interaction.multimodal_coordinator import MultimodalCoordinator
from multimodal.speech.asr_service import ASRService
from multimodal.speech.tts_service import TTSService
from multimodal.visual.image_descriptor import ImageDescriptor

router = APIRouter()


class SpeechRecognitionResponse(BaseModel):
    text: str
    confidence: float
    language: str
    dialect: Optional[str] = None
    duration: float


class SpeechSynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1)
    game_id: str = Field("wow")
    user_context: Optional[Dict[str, Any]] = Field(default=None)
    emotion: Optional[str] = Field(default=None)


class SpeechSynthesisResponse(BaseModel):
    text: str
    success: bool
    duration: float
    voice_settings: Dict[str, Any] = {}
    emotion: Optional[str] = None


class HapticFeedbackRequest(BaseModel):
    feedback_type: str = Field(...)
    intensity: float = Field(0.5, ge=0.0, le=1.0)
    device_id: str = Field("default")
    user_type: Optional[str] = Field(None)
    game_id: str = Field("wow")


class HapticFeedbackResponse(BaseModel):
    status: str
    pattern: List[int]


class ImageDescriptionResponse(BaseModel):
    description: str
    ui_elements: List[Dict[str, Any]]
    spatial_info: str
    accessibility_features: List[str]


class MultimodalProcessResponse(BaseModel):
    game_id: str
    speech: Optional[Dict[str, Any]] = None
    visual: Optional[Dict[str, Any]] = None
    haptic: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.get("/capabilities")
async def get_capabilities(game_id: str = "wow"):
    """返回当前多模态子系统能力，用于前端能力展示。"""
    try:
        asr = ASRService(game_id)
        tts = TTSService(game_id)
        encoder = VibrationEncoder(game_id)
        return {
            "game_id": game_id,
            "speech_recognition": asr.get_stats(),
            "speech_synthesis": tts.get_stats(),
            "haptic_patterns": encoder.get_supported_patterns(),
            "visual_description": {
                "enabled": True,
                "output": ["description", "ui_elements", "spatial_info"],
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取多模态能力失败: {exc}")


@router.post("/speech/recognize", response_model=SpeechRecognitionResponse)
async def recognize_speech(
    audio_file: UploadFile = File(...),
    language: str = Form("zh-CN"),
    dialect: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    game_id: str = Form("wow"),
):
    try:
        data = await audio_file.read()
        asr = ASRService(game_id)
        result = await asr.recognize_speech(data, language)
        return SpeechRecognitionResponse(
            text=result.get("text", ""),
            confidence=float(result.get("confidence", 0.0)),
            language=result.get("language", language),
            dialect=result.get("dialect") or dialect,
            duration=float(result.get("duration", 0.0)),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {exc}")


@router.post("/speech/synthesize", response_model=SpeechSynthesisResponse)
async def synthesize_speech(req: SpeechSynthesisRequest):
    try:
        tts = TTSService(req.game_id)
        if req.emotion:
            result = await tts.synthesize_with_emotion(req.text, req.emotion)
        else:
            result = await tts.synthesize_speech(req.text, req.user_context)
        return SpeechSynthesisResponse(
            text=result.get("text", req.text),
            success=bool(result.get("success", False)),
            duration=float(result.get("duration", 0.0)),
            voice_settings=result.get("voice_settings", {}),
            emotion=result.get("emotion"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {exc}")


@router.post("/visual/describe", response_model=ImageDescriptionResponse)
async def describe_image(
    image_file: UploadFile = File(...),
    user_type: str = Form("normal"),
    game_id: str = Form("wow"),
):
    try:
        descriptor = ImageDescriptor(game_id)
        image_data = await image_file.read()
        result = await descriptor.describe_image(image_data, {"user_type": user_type})
        return ImageDescriptionResponse(
            description=result.get("description", ""),
            ui_elements=result.get("ui_elements", []),
            spatial_info=result.get("spatial_info", ""),
            accessibility_features=result.get("accessibility_features", []),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"图像描述失败: {exc}")


@router.post("/haptic/feedback", response_model=HapticFeedbackResponse)
async def send_haptic_feedback(req: HapticFeedbackRequest):
    try:
        encoder = VibrationEncoder(req.game_id)
        pattern = await encoder.encode_feedback(req.feedback_type, req.intensity)
        ok = await encoder.send_vibration(pattern, req.device_id, {"user_type": req.user_type or "normal"})
        return HapticFeedbackResponse(status="sent" if ok else "failed", pattern=pattern)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"触觉反馈发送失败: {exc}")


@router.post("/process", response_model=MultimodalProcessResponse)
async def process_multimodal(
    game_id: str = Form("wow"),
    language: str = Form("zh-CN"),
    user_type: str = Form("normal"),
    feedback_type: Optional[str] = Form(None),
    intensity: float = Form(0.5),
    custom_patterns: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
):
    """一站式处理语音、图像与触觉请求。"""
    try:
        coordinator = MultimodalCoordinator(game_id)
        payload: Dict[str, Any] = {}
        if audio_file is not None:
            payload["audio"] = await audio_file.read()
        if image_file is not None:
            payload["image"] = await image_file.read()
        if feedback_type:
            payload["haptic_feedback"] = feedback_type
        if custom_patterns:
            payload["custom_patterns"] = json.loads(custom_patterns)

        result = await coordinator.process_multimodal_input(
            payload,
            {
                "language": language,
                "user_type": user_type,
                "intensity": intensity,
            },
        )
        return MultimodalProcessResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"多模态处理失败: {exc}")
