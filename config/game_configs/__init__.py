# 游戏配置模块
"""
游戏特定配置模块

包含各游戏的配置文件，支持多游戏快速适配。
提供游戏配置的加载、管理和验证功能。
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path

def load_game_config(game_id: str) -> Dict[str, Any]:
    """
    加载指定游戏的配置文件
    
    Args:
        game_id: 游戏ID
        
    Returns:
        游戏配置字典
        
    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置文件格式错误
    """
    config_path = Path(__file__).parent / f"{game_id}_config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"游戏配置文件不存在: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 验证配置格式
        _validate_config(config, game_id)
        
        return config
        
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件格式错误: {e}")

def get_supported_games() -> List[str]:
    """
    获取支持的游戏列表
    
    Returns:
        支持的游戏ID列表
    """
    config_dir = Path(__file__).parent
    config_files = [f for f in config_dir.glob("*_config.json")]
    return [f.stem.replace("_config", "") for f in config_files]

def save_game_config(game_id: str, config: Dict[str, Any]) -> None:
    """
    保存游戏配置
    
    Args:
        game_id: 游戏ID
        config: 配置字典
    """
    config_path = Path(__file__).parent / f"{game_id}_config.json"
    
    # 验证配置格式
    _validate_config(config, game_id)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def _validate_config(config: Dict[str, Any], game_id: str) -> None:
    """
    验证配置文件格式
    
    Args:
        config: 配置字典
        game_id: 游戏ID
        
    Raises:
        ValueError: 配置格式错误
    """
    required_fields = ["game_name", "game_id", "version"]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"配置文件缺少必需字段: {field}")
    
    if config["game_id"] != game_id:
        raise ValueError(f"配置文件中的game_id({config['game_id']})与请求的game_id({game_id})不匹配")

def get_game_info(game_id: str) -> Dict[str, Any]:
    """
    获取游戏基本信息
    
    Args:
        game_id: 游戏ID
        
    Returns:
        游戏基本信息
    """
    config = load_game_config(game_id)
    
    return {
        "game_id": config["game_id"],
        "game_name": config["game_name"],
        "version": config["version"],
        "platforms": config.get("platforms", []),
        "languages": config.get("languages", []),
        "has_accessibility": bool(config.get("accessibility_config")),
        "has_health_config": bool(config.get("health_config"))
    }

def list_game_categories(game_id: str) -> List[str]:
    """
    获取游戏的知识分类
    
    Args:
        game_id: 游戏ID
        
    Returns:
        知识分类列表
    """
    config = load_game_config(game_id)
    return config.get("knowledge_categories", [])

def get_crawler_config(game_id: str) -> Dict[str, Any]:
    """
    获取游戏的爬虫配置
    
    Args:
        game_id: 游戏ID
        
    Returns:
        爬虫配置
    """
    config = load_game_config(game_id)
    return config.get("crawler_config", {})

def get_accessibility_config(game_id: str) -> Dict[str, Any]:
    """
    获取游戏的无障碍配置
    
    Args:
        game_id: 游戏ID
        
    Returns:
        无障碍配置
    """
    config = load_game_config(game_id)
    return config.get("accessibility_config", {})

def get_health_config(game_id: str) -> Dict[str, Any]:
    """
    获取游戏的健康配置
    
    Args:
        game_id: 游戏ID
        
    Returns:
        健康配置
    """
    config = load_game_config(game_id)
    return config.get("health_config", {})

# 导出函数
__all__ = [
    "load_game_config",
    "get_supported_games", 
    "save_game_config",
    "get_game_info",
    "list_game_categories",
    "get_crawler_config",
    "get_accessibility_config",
    "get_health_config"
]
