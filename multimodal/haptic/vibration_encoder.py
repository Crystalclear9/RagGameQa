# 震动编码器
from typing import Dict, Any, List, Optional
import time
import logging
import asyncio

logger = logging.getLogger(__name__)

class VibrationEncoder:
    """震动编码器，定义震动频率与语义反馈的映射规则"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.vibration_patterns = {
            "success": [100, 200, 100],  # 3次短震表示"操作成功"
            "error": [500, 200, 500],    # 长震-短震-长震表示"错误"
            "warning": [300, 100, 300],  # 警告模式
            "notification": [200],        # 单次震动表示"通知"
            "direction_up": [150],       # 向上
            "direction_down": [150, 150], # 向下
            "direction_left": [100, 100, 100], # 向左
            "direction_right": [200, 200],     # 向右
            "attack": [150, 50, 150],     # 攻击反馈
            "heal": [100, 100, 100],      # 治疗反馈
            "movement": [100],             # 移动反馈
            "collection": [80, 80, 80]    # 收集反馈
        }
        self.active_devices = {}  # 活跃设备列表
        logger.info(f"震动编码器初始化完成: {game_id}")
    
    async def encode_feedback(self, feedback_type: str, intensity: float = 1.0, 
                            custom_pattern: Optional[List[int]] = None) -> List[int]:
        """
        编码触觉反馈
        
        Args:
            feedback_type: 反馈类型
            intensity: 强度 (0.0-1.0)
            custom_pattern: 自定义模式
            
        Returns:
            调整后的震动模式
        """
        try:
            # 使用自定义模式或预设模式
            if custom_pattern:
                pattern = custom_pattern
            else:
                pattern = self.vibration_patterns.get(feedback_type, [200])
            
            # 根据强度调整震动时长
            intensity = max(0.0, min(1.0, intensity))  # 限制强度范围
            adjusted_pattern = [int(duration * intensity) for duration in pattern]
            
            # 确保最小震动时长
            adjusted_pattern = [max(duration, 50) for duration in adjusted_pattern]
            
            logger.debug(f"编码反馈: {feedback_type}, 强度: {intensity}, 模式: {adjusted_pattern}")
            return adjusted_pattern
            
        except Exception as e:
            logger.error(f"反馈编码失败: {str(e)}")
            return [200]  # 返回默认模式
    
    async def send_vibration(self, pattern: List[int], device_id: str = "default", 
                           user_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        发送震动信号
        
        Args:
            pattern: 震动模式
            device_id: 设备ID
            user_context: 用户上下文
            
        Returns:
            是否发送成功
        """
        try:
            # 检查设备是否支持震动
            if not await self._check_device_support(device_id):
                logger.warning(f"设备不支持震动: {device_id}")
                return False
            
            # 根据用户类型调整模式
            if user_context:
                pattern = self._adjust_for_user_type(pattern, user_context)
            
            # 发送震动信号
            success = await self._execute_vibration(pattern, device_id)
            
            if success:
                logger.info(f"震动发送成功: 设备={device_id}, 模式={pattern}")
            else:
                logger.error(f"震动发送失败: 设备={device_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"震动发送异常: {str(e)}")
            return False
    
    async def send_sequence_vibration(self, patterns: List[List[int]], 
                                    device_id: str = "default",
                                    interval: int = 500) -> bool:
        """
        发送序列震动
        
        Args:
            patterns: 震动模式序列
            device_id: 设备ID
            interval: 模式间隔(ms)
            
        Returns:
            是否发送成功
        """
        try:
            for i, pattern in enumerate(patterns):
                success = await self.send_vibration(pattern, device_id)
                if not success:
                    logger.error(f"序列震动第{i+1}个模式发送失败")
                    return False
                
                # 等待间隔时间
                if i < len(patterns) - 1:  # 最后一个模式后不需要等待
                    await asyncio.sleep(interval / 1000.0)
            
            logger.info(f"序列震动发送完成: {len(patterns)}个模式")
            return True
            
        except Exception as e:
            logger.error(f"序列震动发送异常: {str(e)}")
            return False
    
    async def register_device(self, device_id: str, device_info: Dict[str, Any]) -> bool:
        """注册设备"""
        try:
            self.active_devices[device_id] = {
                "device_info": device_info,
                "last_used": time.time(),
                "vibration_support": device_info.get("haptic_feedback", False)
            }
            logger.info(f"设备注册成功: {device_id}")
            return True
        except Exception as e:
            logger.error(f"设备注册失败: {str(e)}")
            return False
    
    async def unregister_device(self, device_id: str) -> bool:
        """注销设备"""
        try:
            if device_id in self.active_devices:
                del self.active_devices[device_id]
                logger.info(f"设备注销成功: {device_id}")
            return True
        except Exception as e:
            logger.error(f"设备注销失败: {str(e)}")
            return False
    
    def get_supported_patterns(self) -> List[str]:
        """获取支持的震动模式"""
        return list(self.vibration_patterns.keys())
    
    def get_active_devices(self) -> Dict[str, Dict[str, Any]]:
        """获取活跃设备列表"""
        return self.active_devices.copy()
    
    async def _check_device_support(self, device_id: str) -> bool:
        """检查设备是否支持震动"""
        if device_id == "default":
            return True  # 默认设备总是支持
        
        device = self.active_devices.get(device_id)
        if not device:
            return False
        
        return device.get("vibration_support", False)
    
    def _adjust_for_user_type(self, pattern: List[int], user_context: Dict[str, Any]) -> List[int]:
        """根据用户类型调整震动模式"""
        user_type = user_context.get("user_type", "normal")
        
        if user_type == "elderly":
            # 老年用户：增强震动强度
            return [int(duration * 1.2) for duration in pattern]
        elif user_type == "hearing_impairment":
            # 听障用户：大幅增强震动
            return [int(duration * 1.5) for duration in pattern]
        elif user_type == "visual_impairment":
            # 视障用户：适度增强震动
            return [int(duration * 1.1) for duration in pattern]
        
        return pattern
    
    async def _execute_vibration(self, pattern: List[int], device_id: str) -> bool:
        """执行震动"""
        try:
            # 模拟震动执行
            # 实际实现中会调用设备特定的API
            
            for duration in pattern:
                # 模拟震动持续时间
                await asyncio.sleep(duration / 1000.0)
                
                # 模拟震动间隔
                if duration != pattern[-1]:  # 不是最后一个
                    await asyncio.sleep(50 / 1000.0)  # 50ms间隔
            
            return True
            
        except Exception as e:
            logger.error(f"震动执行失败: {str(e)}")
            return False
    
    async def test_vibration(self, device_id: str = "default") -> Dict[str, Any]:
        """测试震动功能"""
        try:
            test_pattern = [200, 100, 200]  # 测试模式
            success = await self.send_vibration(test_pattern, device_id)
            
            return {
                "device_id": device_id,
                "test_pattern": test_pattern,
                "success": success,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"震动测试失败: {str(e)}")
            return {
                "device_id": device_id,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
