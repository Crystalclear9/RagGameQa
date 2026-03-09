# 全局配置设置
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Settings:
    """全局配置类"""

    # 应用基础配置
    APP_NAME: str = os.getenv("APP_NAME", "RAG Game QA System")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENV: str = os.getenv("ENV", "dev")  # dev | staging | prod

    # API配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ALLOW_ORIGINS: List[str] = (
        os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # AI Provider配置
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")  # mock | claude | openai | gemini
    
    # Claude配置
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_API_BASE: str = os.getenv("CLAUDE_API_BASE", "https://api.anthropic.com")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    CLAUDE_MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "2000"))
    CLAUDE_TEMPERATURE: float = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))
    CLAUDE_API_VERSION: str = os.getenv("CLAUDE_API_VERSION", "2023-06-01")

    # Gemini配置
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_BASE: str = os.getenv(
        "GEMINI_API_BASE",
        "https://generativelanguage.googleapis.com/v1beta",
    )
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
    
    # 模型配置（保持向后兼容）
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-6")
    RUNTIME_STORAGE_MODE: str = os.getenv("RUNTIME_STORAGE_MODE", "session")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))

    # 检索配置
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

    # 缓存配置
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "False").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    
    # 性能配置
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

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

    @classmethod
    def has_live_llm_config(cls) -> bool:
        """是否配置了真实可调用的外部大模型。"""
        provider = cls.AI_PROVIDER.lower()
        if provider == "gemini":
            return bool(cls.GEMINI_API_KEY)
        if provider == "claude":
            return bool(cls.CLAUDE_API_KEY)
        return False


# 全局配置实例
settings = Settings()
