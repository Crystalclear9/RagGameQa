# 多模态路由
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from multimodal.speech.asr_service import ASRService
from multimodal.speech.tts_service import TTSService
from multimodal.haptic.vibration_encoder import VibrationEncoder

router = APIRouter()


class SpeechRecognitionResponse(BaseModel):
    text: str
    confidence: float
    language: str
    dialect: Optional[str] = None
    duration: float


@router.post("/speech/recognize", response_model=SpeechRecognitionResponse)
async def recognize_speech(
    audio_file: UploadFile = File(...),
    language: str = Form("zh-CN"),
    dialect: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    game_id: str = Form("wow"),
):
    try:
        # 简化调用示例（真实实现参考 multimodal/speech/asr_service.py）
        data = await audio_file.read()
        asr = ASRService(game_id)
        result = await asr.recognize_speech(data, language)
        return SpeechRecognitionResponse(
            text=result.get("text", ""),
            confidence=float(result.get("confidence", 0.0)),
            language=result.get("language", language),
            dialect=result.get("dialect"),
            duration=float(result.get("duration", 0.0)),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {e}")


class HapticFeedbackRequest(BaseModel):
    feedback_type: str = Field(...)
    intensity: float = Field(0.5, ge=0.0, le=1.0)
    device_id: str = Field("default")
    user_type: Optional[str] = Field(None)
    game_id: str = Field("wow")


class HapticFeedbackResponse(BaseModel):
    status: str
    pattern: List[int]


@router.post("/haptic/feedback", response_model=HapticFeedbackResponse)
async def send_haptic_feedback(req: HapticFeedbackRequest):
    try:
        encoder = VibrationEncoder(req.game_id)
        pattern = await encoder.encode_feedback(req.feedback_type, req.intensity)
        ok = await encoder.send_vibration(pattern, req.device_id, {"user_type": req.user_type or "normal"})
        return HapticFeedbackResponse(status="sent" if ok else "failed", pattern=pattern)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触觉反馈发送失败: {e}")
