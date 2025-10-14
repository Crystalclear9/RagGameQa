# 日志配置
from loguru import logger
import sys
import os
from typing import Optional


def setup_logging(level: str = "INFO", log_dir: str = "logs"):
    """设置日志配置"""
    logger.remove()

    # 控制台
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level.upper() if isinstance(level, str) else "INFO",
    )

    # 文件
    os.makedirs(log_dir, exist_ok=True)
    logger.add(
        f"{log_dir}/app.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
    )
    logger.add(
        f"{log_dir}/error.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
    )

    return logger


def get_logger(name: Optional[str] = None):
    """获取命名logger（loguru兼容封装）"""
    return logger.bind(name=name or "app")
