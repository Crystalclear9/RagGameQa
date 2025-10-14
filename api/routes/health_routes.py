# 健康路由
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

router = APIRouter()

# 数据模型
class HealthMonitorRequest(BaseModel):
    """健康监控请求模型"""
    user_id: str
    game_id: str
    session_duration: int  # 游戏时长（秒）
    break_intervals: Optional[List[int]] = None  # 休息间隔
    eye_strain_level: Optional[int] = None  # 眼疲劳程度 1-10
    posture_data: Optional[Dict[str, Any]] = None  # 姿势数据

class HealthMonitorResponse(BaseModel):
    """健康监控响应模型"""
    user_id: str
    session_id: str
    health_score: float  # 健康评分 0-100
    recommendations: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    next_break_time: Optional[str] = None
    eye_care_suggestions: List[str]
    posture_corrections: List[str]

class HealthInterventionRequest(BaseModel):
    """健康干预请求模型"""
    user_id: str
    intervention_type: str  # "break_reminder", "eye_care", "posture", "blue_light"
    trigger_reason: str
    severity: str  # "low", "medium", "high"
    custom_settings: Optional[Dict[str, Any]] = None

class HealthInterventionResponse(BaseModel):
    """健康干预响应模型"""
    intervention_id: str
    intervention_type: str
    status: str  # "active", "completed", "dismissed"
    duration: int  # 干预持续时间（秒）
    effectiveness_score: Optional[float] = None
    user_feedback: Optional[str] = None

class WearableDataRequest(BaseModel):
    """穿戴设备数据请求模型"""
    user_id: str
    device_type: str  # "smartwatch", "fitness_band", "eye_tracker"
    heart_rate: Optional[int] = None
    stress_level: Optional[int] = None
    sleep_quality: Optional[float] = None
    eye_blink_rate: Optional[float] = None
    timestamp: str

class HealthReportRequest(BaseModel):
    """健康报告请求模型"""
    user_id: str
    report_period: str  # "daily", "weekly", "monthly"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class HealthReportResponse(BaseModel):
    """健康报告响应模型"""
    user_id: str
    report_period: str
    total_gaming_time: int
    average_session_duration: float
    break_compliance_rate: float
    eye_strain_trend: List[Dict[str, Any]]
    health_improvements: List[str]
    recommendations: List[Dict[str, Any]]
    overall_health_score: float

@router.post("/monitor", response_model=HealthMonitorResponse)
async def health_monitor(request: HealthMonitorRequest):
    """
    健康监控接口
    
    监控用户游戏健康状态，提供实时健康评估和建议
    """
    try:
        # 执行健康监控分析
        monitor_result = await _perform_health_monitoring(request)
        
        return HealthMonitorResponse(
            user_id=request.user_id,
            session_id=monitor_result["session_id"],
            health_score=monitor_result["health_score"],
            recommendations=monitor_result["recommendations"],
            alerts=monitor_result["alerts"],
            next_break_time=monitor_result["next_break_time"],
            eye_care_suggestions=monitor_result["eye_care_suggestions"],
            posture_corrections=monitor_result["posture_corrections"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康监控失败: {str(e)}")

@router.post("/intervention", response_model=HealthInterventionResponse)
async def health_intervention(request: HealthInterventionRequest):
    """
    健康干预接口
    
    根据健康监控结果触发相应的健康干预措施
    """
    try:
        # 执行健康干预
        intervention_result = await _perform_health_intervention(request)
        
        return HealthInterventionResponse(
            intervention_id=intervention_result["intervention_id"],
            intervention_type=request.intervention_type,
            status=intervention_result["status"],
            duration=intervention_result["duration"],
            effectiveness_score=intervention_result.get("effectiveness_score"),
            user_feedback=intervention_result.get("user_feedback")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康干预失败: {str(e)}")

@router.post("/wearable-data")
async def receive_wearable_data(request: WearableDataRequest):
    """
    接收穿戴设备数据接口
    
    接收来自智能穿戴设备的健康数据
    """
    try:
        # 处理穿戴设备数据
        processed_data = await _process_wearable_data(request)
        
        return {
            "status": "success",
            "processed_at": datetime.now().isoformat(),
            "data_summary": processed_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"穿戴设备数据处理失败: {str(e)}")

@router.post("/health-report", response_model=HealthReportResponse)
async def generate_health_report(request: HealthReportRequest):
    """
    生成健康报告接口
    
    生成用户健康报告，包含游戏习惯分析和健康建议
    """
    try:
        # 生成健康报告
        report_data = await _generate_health_report(request)
        
        return HealthReportResponse(
            user_id=request.user_id,
            report_period=request.report_period,
            total_gaming_time=report_data["total_gaming_time"],
            average_session_duration=report_data["average_session_duration"],
            break_compliance_rate=report_data["break_compliance_rate"],
            eye_strain_trend=report_data["eye_strain_trend"],
            health_improvements=report_data["health_improvements"],
            recommendations=report_data["recommendations"],
            overall_health_score=report_data["overall_health_score"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康报告生成失败: {str(e)}")

@router.get("/break-reminder")
async def get_break_reminder(
    user_id: str = Query(..., description="用户ID"),
    session_duration: int = Query(..., description="当前会话时长（分钟）")
):
    """
    获取休息提醒接口
    
    根据用户游戏时长提供休息提醒
    """
    try:
        reminder_data = await _get_break_reminder(user_id, session_duration)
        return reminder_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"休息提醒获取失败: {str(e)}")

@router.post("/blue-light-filter")
async def adjust_blue_light_filter(
    user_id: str = Query(..., description="用户ID"),
    intensity: float = Query(0.3, description="蓝光过滤强度 0-1")
):
    """
    调整蓝光过滤接口
    
    根据用户需求调整蓝光过滤强度
    """
    try:
        filter_result = await _adjust_blue_light_filter(user_id, intensity)
        return filter_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"蓝光过滤调整失败: {str(e)}")

@router.get("/eye-care-exercises")
async def get_eye_care_exercises(
    user_id: str = Query(..., description="用户ID"),
    exercise_type: str = Query("basic", description="练习类型")
):
    """
    获取护眼练习接口
    
    提供个性化的护眼练习建议
    """
    try:
        exercises = await _get_eye_care_exercises(user_id, exercise_type)
        return exercises
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"护眼练习获取失败: {str(e)}")

@router.post("/posture-correction")
async def posture_correction(
    user_id: str = Query(..., description="用户ID"),
    posture_data: Dict[str, Any] = None
):
    """
    姿势纠正接口
    
    基于姿势数据提供纠正建议
    """
    try:
        correction_result = await _perform_posture_correction(user_id, posture_data)
        return correction_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"姿势纠正失败: {str(e)}")

# 辅助函数
async def _perform_health_monitoring(request: HealthMonitorRequest) -> Dict[str, Any]:
    """执行健康监控分析"""
    session_duration_minutes = request.session_duration // 60
    
    # 计算健康评分
    health_score = 100.0
    
    # 根据游戏时长扣分
    if session_duration_minutes > 60:
        health_score -= (session_duration_minutes - 60) * 0.5
    
    # 根据眼疲劳程度扣分
    if request.eye_strain_level:
        health_score -= request.eye_strain_level * 2
    
    # 根据休息间隔加分
    if request.break_intervals:
        avg_break_interval = sum(request.break_intervals) / len(request.break_intervals)
        if avg_break_interval <= 30:  # 30分钟内有休息
            health_score += 10
    
    health_score = max(0, min(100, health_score))
    
    # 生成建议
    recommendations = []
    alerts = []
    
    if session_duration_minutes > 60:
        recommendations.append({
            "type": "break_reminder",
            "message": "建议立即休息15分钟",
            "priority": "high"
        })
        alerts.append({
            "type": "warning",
            "message": "游戏时长过长，请注意休息",
            "timestamp": datetime.now().isoformat()
        })
    
    if request.eye_strain_level and request.eye_strain_level > 6:
        recommendations.append({
            "type": "eye_care",
            "message": "眼疲劳程度较高，建议进行护眼练习",
            "priority": "medium"
        })
    
    # 计算下次休息时间
    next_break_time = None
    if session_duration_minutes >= 45:
        next_break_time = (datetime.now() + timedelta(minutes=15)).isoformat()
    
    return {
        "session_id": f"session_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "health_score": health_score,
        "recommendations": recommendations,
        "alerts": alerts,
        "next_break_time": next_break_time,
        "eye_care_suggestions": [
            "每20分钟看20英尺外的物体20秒",
            "眨眼练习：快速眨眼10次",
            "眼球转动：顺时针和逆时针各转5圈"
        ],
        "posture_corrections": [
            "保持背部挺直",
            "屏幕与眼睛保持一臂距离",
            "双脚平放在地面上"
        ]
    }

async def _perform_health_intervention(request: HealthInterventionRequest) -> Dict[str, Any]:
    """执行健康干预"""
    intervention_id = f"intervention_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 根据干预类型设置持续时间
    duration_map = {
        "break_reminder": 900,  # 15分钟
        "eye_care": 300,        # 5分钟
        "posture": 180,         # 3分钟
        "blue_light": 3600      # 1小时
    }
    
    duration = duration_map.get(request.intervention_type, 300)
    
    return {
        "intervention_id": intervention_id,
        "status": "active",
        "duration": duration,
        "effectiveness_score": None,
        "user_feedback": None
    }

async def _process_wearable_data(request: WearableDataRequest) -> Dict[str, Any]:
    """处理穿戴设备数据"""
    return {
        "device_type": request.device_type,
        "data_quality": "good",
        "processed_metrics": {
            "heart_rate": request.heart_rate,
            "stress_level": request.stress_level,
            "sleep_quality": request.sleep_quality,
            "eye_blink_rate": request.eye_blink_rate
        },
        "health_indicators": {
            "overall_stress": "low" if request.stress_level and request.stress_level < 5 else "medium",
            "sleep_adequacy": "good" if request.sleep_quality and request.sleep_quality > 7 else "poor",
            "eye_fatigue": "low" if request.eye_blink_rate and request.eye_blink_rate > 15 else "high"
        }
    }

async def _generate_health_report(request: HealthReportRequest) -> Dict[str, Any]:
    """生成健康报告"""
    return {
        "total_gaming_time": 3600,  # 1小时
        "average_session_duration": 45.5,
        "break_compliance_rate": 0.75,
        "eye_strain_trend": [
            {"date": "2024-01-01", "level": 3},
            {"date": "2024-01-02", "level": 4},
            {"date": "2024-01-03", "level": 2},
            {"date": "2024-01-04", "level": 3},
            {"date": "2024-01-05", "level": 2}
        ],
        "health_improvements": [
            "休息间隔时间缩短了20%",
            "眼疲劳程度降低了15%",
            "整体健康评分提升了8分"
        ],
        "recommendations": [
            {
                "type": "break_schedule",
                "message": "建议每45分钟休息一次",
                "priority": "medium"
            },
            {
                "type": "eye_care",
                "message": "增加护眼练习频率",
                "priority": "low"
            }
        ],
        "overall_health_score": 78.5
    }

async def _get_break_reminder(user_id: str, session_duration: int) -> Dict[str, Any]:
    """获取休息提醒"""
    if session_duration >= 60:
        return {
            "should_break": True,
            "break_duration": 15,
            "message": "建议立即休息15分钟",
            "priority": "high",
            "suggestions": [
                "起身活动一下",
                "看看窗外的风景",
                "做简单的伸展运动"
            ]
        }
    elif session_duration >= 45:
        return {
            "should_break": True,
            "break_duration": 10,
            "message": "建议休息10分钟",
            "priority": "medium",
            "suggestions": [
                "闭目养神",
                "做护眼练习",
                "活动手腕和颈部"
            ]
        }
    else:
        return {
            "should_break": False,
            "break_duration": 0,
            "message": "可以继续游戏",
            "priority": "low",
            "suggestions": [
                "保持良好的坐姿",
                "记得眨眼",
                "保持适当的屏幕距离"
            ]
        }

async def _adjust_blue_light_filter(user_id: str, intensity: float) -> Dict[str, Any]:
    """调整蓝光过滤"""
    return {
        "user_id": user_id,
        "filter_intensity": intensity,
        "status": "applied",
        "effectiveness": "high" if intensity >= 0.3 else "medium",
        "message": f"蓝光过滤强度已调整为{intensity * 100}%"
    }

async def _get_eye_care_exercises(user_id: str, exercise_type: str) -> Dict[str, Any]:
    """获取护眼练习"""
    exercises = {
        "basic": [
            {
                "name": "20-20-20法则",
                "description": "每20分钟看20英尺外的物体20秒",
                "duration": 20,
                "difficulty": "easy"
            },
            {
                "name": "眨眼练习",
                "description": "快速眨眼10次，然后闭眼休息10秒",
                "duration": 30,
                "difficulty": "easy"
            }
        ],
        "advanced": [
            {
                "name": "眼球转动",
                "description": "顺时针和逆时针各转5圈",
                "duration": 60,
                "difficulty": "medium"
            },
            {
                "name": "焦点调节",
                "description": "交替看近处和远处的物体",
                "duration": 90,
                "difficulty": "medium"
            }
        ]
    }
    
    return {
        "exercise_type": exercise_type,
        "exercises": exercises.get(exercise_type, exercises["basic"]),
        "total_duration": sum(ex["duration"] for ex in exercises.get(exercise_type, exercises["basic"])),
        "recommended_frequency": "每2小时一次"
    }

async def _perform_posture_correction(user_id: str, posture_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行姿势纠正"""
    return {
        "user_id": user_id,
        "posture_score": 85,
        "corrections": [
            {
                "area": "back",
                "issue": "轻微驼背",
                "correction": "挺直背部，肩膀向后",
                "priority": "medium"
            },
            {
                "area": "neck",
                "issue": "颈部前倾",
                "correction": "保持头部与身体垂直",
                "priority": "high"
            }
        ],
        "recommendations": [
            "使用符合人体工学的椅子",
            "调整屏幕高度与眼睛平齐",
            "定期起身活动"
        ]
    }
