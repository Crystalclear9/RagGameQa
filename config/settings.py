# 全局配置设置
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

try:
    from config.local_provider_config import LOCAL_PROVIDER_CONFIG
except ImportError:
    LOCAL_PROVIDER_CONFIG = {}


def _get_config_value(name: str, default: str = "") -> str:
    if name in LOCAL_PROVIDER_CONFIG and LOCAL_PROVIDER_CONFIG[name] not in {None, ""}:
        return str(LOCAL_PROVIDER_CONFIG[name])
    return os.getenv(name, default)


class Settings:
    """全局配置类"""

    # 应用基础配置
    APP_NAME: str = _get_config_value("APP_NAME", "RAG Game QA System")
    APP_VERSION: str = _get_config_value("APP_VERSION", "1.0.0")
    DEBUG: bool = _get_config_value("DEBUG", "False").lower() == "true"
    ENV: str = _get_config_value("ENV", "dev")  # dev | staging | prod

    # API配置
    API_HOST: str = _get_config_value("API_HOST", "0.0.0.0")
    API_PORT: int = int(_get_config_value("API_PORT", "8000"))
    CORS_ALLOW_ORIGINS: List[str] = (
        _get_config_value(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
    )
    LOG_LEVEL: str = _get_config_value("LOG_LEVEL", "info")

    # AI Provider配置
    AI_PROVIDER: str = _get_config_value("AI_PROVIDER", "mock")  # mock | claude | openai | gemini
    
    # Claude配置
    CLAUDE_API_KEY: str = _get_config_value("CLAUDE_API_KEY", "")
    CLAUDE_API_BASE: str = _get_config_value("CLAUDE_API_BASE", "https://api.anthropic.com")
    CLAUDE_MODEL: str = _get_config_value("CLAUDE_MODEL", "claude-sonnet-4-6")
    CLAUDE_MAX_TOKENS: int = int(_get_config_value("CLAUDE_MAX_TOKENS", "2000"))
    CLAUDE_TEMPERATURE: float = float(_get_config_value("CLAUDE_TEMPERATURE", "0.7"))
    CLAUDE_API_VERSION: str = _get_config_value("CLAUDE_API_VERSION", "2023-06-01")

    # Gemini配置
    GEMINI_API_KEY: str = _get_config_value("GEMINI_API_KEY", "")
    GEMINI_API_BASE: str = _get_config_value(
        "GEMINI_API_BASE",
        "https://generativelanguage.googleapis.com/v1beta",
    )
    GEMINI_MODEL: str = _get_config_value("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_MAX_TOKENS: int = int(_get_config_value("GEMINI_MAX_TOKENS", "2048"))
    GEMINI_TEMPERATURE: float = float(_get_config_value("GEMINI_TEMPERATURE", "0.7"))
    
    # 模型配置（保持向后兼容）
    DEFAULT_MODEL: str = _get_config_value("DEFAULT_MODEL", "claude-sonnet-4-6")
    RUNTIME_STORAGE_MODE: str = _get_config_value("RUNTIME_STORAGE_MODE", "session")
    EMBEDDING_MODEL: str = _get_config_value(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    MAX_TOKENS: int = int(_get_config_value("MAX_TOKENS", "2000"))

    # 检索配置
    TOP_K_RESULTS: int = int(_get_config_value("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD: float = float(_get_config_value("SIMILARITY_THRESHOLD", "0.7"))

    # 缓存配置
    CACHE_ENABLED: bool = _get_config_value("CACHE_ENABLED", "False").lower() == "true"
    CACHE_TTL: int = int(_get_config_value("CACHE_TTL", "3600"))
    
    # 性能配置
    TIMEOUT_SECONDS: int = int(_get_config_value("TIMEOUT_SECONDS", "30"))
    MAX_RETRIES: int = int(_get_config_value("MAX_RETRIES", "3"))

    # 数据库与缓存
    DB_POOL_SIZE: int = int(_get_config_value("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(_get_config_value("DB_MAX_OVERFLOW", "10"))

    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接URL"""
        return _get_config_value(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/rag_game_qa",
        )

    @classmethod
    def get_redis_url(cls) -> str:
        """获取Redis连接URL"""
        return _get_config_value("REDIS_URL", "redis://localhost:6379")

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
