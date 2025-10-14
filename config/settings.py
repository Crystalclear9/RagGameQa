# 全局配置设置
import os
from typing import Dict, Any

class Settings:
    """全局配置类"""
    
    # 应用基础配置
    APP_NAME: str = "RAG Game QA System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # 模型配置
    DEFAULT_MODEL: str = "deepseek-r1"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    MAX_TOKENS: int = 100000
    
    # 检索配置
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    # 多模态配置
    SUPPORTED_LANGUAGES: list = ["zh", "en", "yue", "sichuan"]
    MAX_AUDIO_DURATION: int = 30  # 秒
    
    # 无障碍配置
    PATIENCE_THRESHOLD: int = 3
    SIMILARITY_THRESHOLD_ELDERLY: float = 0.85
    
    # 健康管理配置
    MAX_GAME_TIME: int = 3600  # 1小时
    BLUE_LIGHT_REDUCTION: float = 0.3
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接URL"""
        return os.getenv(
            "DATABASE_URL", 
            "postgresql://user:password@localhost:5432/rag_game_qa"
        )
    
    @classmethod
    def get_redis_url(cls) -> str:
        """获取Redis连接URL"""
        return os.getenv("REDIS_URL", "redis://localhost:6379")

# 全局配置实例
settings = Settings()
