# 配置模块
"""
配置模块

包含系统全局配置、数据库配置、模型配置和游戏特定配置。
提供统一的配置管理接口。
"""

from .settings import settings
from .database import engine, SessionLocal, Base, get_db, create_tables, drop_tables
from .model_config import ModelConfig
from .game_configs import (
    load_game_config,
    get_supported_games,
    save_game_config,
    get_game_info,
    get_accessibility_config,
    get_health_config
)

__all__ = [
    # 全局配置
    "settings",
    
    # 数据库配置
    "engine",
    "SessionLocal", 
    "Base",
    "get_db",
    "create_tables",
    "drop_tables",
    
    # 模型配置
    "ModelConfig",
    
    # 游戏配置
    "load_game_config",
    "get_supported_games",
    "save_game_config", 
    "get_game_info",
    "get_accessibility_config",
    "get_health_config"
]
