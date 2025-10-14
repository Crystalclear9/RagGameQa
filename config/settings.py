# 全局配置设置
import os
from typing import Dict, Any, List


class Settings:
    """全局配置类"""

    # 应用基础配置
    APP_NAME: str = "RAG Game QA System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENV: str = os.getenv("ENV", "dev")  # dev | staging | prod

    # API配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ALLOW_ORIGINS: List[str] = (
        os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # 模型配置
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "deepseek-r1")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "100000"))

    # 检索配置
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

    # 多模态配置
    SUPPORTED_LANGUAGES: list = ["zh", "en", "yue", "sichuan"]
    MAX_AUDIO_DURATION: int = int(os.getenv("MAX_AUDIO_DURATION", "30"))  # 秒

    # 无障碍配置
    PATIENCE_THRESHOLD: int = int(os.getenv("PATIENCE_THRESHOLD", "3"))
    SIMILARITY_THRESHOLD_ELDERLY: float = float(
        os.getenv("SIMILARITY_THRESHOLD_ELDERLY", "0.85")
    )

    # 健康管理配置
    MAX_GAME_TIME: int = int(os.getenv("MAX_GAME_TIME", "3600"))  # 1小时
    BLUE_LIGHT_REDUCTION: float = float(os.getenv("BLUE_LIGHT_REDUCTION", "0.3"))

    # 数据库与缓存
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接URL"""
        return os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/rag_game_qa",
        )

    @classmethod
    def get_redis_url(cls) -> str:
        """获取Redis连接URL"""
        return os.getenv("REDIS_URL", "redis://localhost:6379")


# 全局配置实例
settings = Settings()
