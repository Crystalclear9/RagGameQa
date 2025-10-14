# 多模态路由
from fastapi import APIRouter

router = APIRouter()

@router.post("/speech/recognize")
async def recognize_speech():
    """语音识别接口"""
    pass

@router.post("/image/describe")
async def describe_image():
    """图像描述接口"""
    pass

@router.post("/haptic/feedback")
async def send_haptic_feedback():
    """触觉反馈接口"""
    pass
