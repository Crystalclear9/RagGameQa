"""Database configuration and ORM models."""

from __future__ import annotations

import importlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from config.settings import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQLITE_FALLBACK_PATH = PROJECT_ROOT / "data" / "rag_game_qa.db"
DEFAULT_GAME_NAMES = {
    "wow": "World of Warcraft",
    "lol": "League of Legends",
    "genshin": "Genshin Impact",
    "minecraft": "Minecraft",
    "valorant": "Valorant",
    "apex": "Apex Legends",
}


def _module_available(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def _normalize_database_url(database_url: str) -> str:
    """Use an available postgres driver automatically."""
    db_url = (database_url or "").strip()
    if not db_url.startswith("postgresql://"):
        return db_url

    if _module_available("psycopg"):
        return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if _module_available("psycopg2"):
        return db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if _module_available("pg8000"):
        return db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    return db_url


def _mask_db_url(url: str) -> str:
    if "@" not in url:
        return url
    left, right = url.split("@", 1)
    if "://" not in left:
        return f"***@{right}"
    scheme, auth = left.split("://", 1)
    if ":" in auth:
        user = auth.split(":", 1)[0]
        return f"{scheme}://{user}:***@{right}"
    return f"{scheme}://***@{right}"


def _build_engine(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif database_url.startswith("postgresql+pg8000"):
        connect_args["timeout"] = 2
    elif database_url.startswith("postgresql"):
        connect_args["connect_timeout"] = 2
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


def _initialize_engine():
    requested_url = settings.get_database_url().strip()
    normalized_url = _normalize_database_url(requested_url)

    try:
        primary_engine = _build_engine(normalized_url)
        with primary_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connected: %s", _mask_db_url(normalized_url))
        return primary_engine, requested_url, normalized_url, False, ""
    except Exception as exc:
        error_message = str(exc)
        if requested_url.startswith("postgresql://") and normalized_url == requested_url:
            error_message = (
                "PostgreSQL driver missing. Install one of: "
                "pip install psycopg[binary] or pip install psycopg2-binary or pip install pg8000"
            )
        SQLITE_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        fallback_url = f"sqlite:///{SQLITE_FALLBACK_PATH.as_posix()}"
        logger.warning("Database connect failed, switching to SQLite fallback: %s", error_message)
        fallback_engine = _build_engine(fallback_url)
        with fallback_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return fallback_engine, requested_url, fallback_url, True, error_message


engine, REQUESTED_DATABASE_URL, ACTIVE_DATABASE_URL, USING_FALLBACK_DATABASE, DATABASE_INIT_ERROR = _initialize_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(50), unique=True, index=True)
    game_name = Column(String(100), nullable=False)
    version = Column(String(20))
    platforms = Column(Text)
    languages = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(50), ForeignKey("games.game_id"))
    content = Column(Text, nullable=False)
    title = Column(String(200))
    category = Column(String(50))
    source = Column(String(200))
    doc_metadata = Column(Text)
    embedding = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game = relationship("Game", back_populates="documents")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(50), ForeignKey("games.game_id"))
    user_id = Column(String(50))
    question = Column(Text, nullable=False)
    answer = Column(Text)
    confidence = Column(Float)
    processing_time = Column(Float)
    retrieved_docs_count = Column(Integer)
    user_context = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="query_logs")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(50), ForeignKey("games.game_id"))
    user_id = Column(String(50))
    query_log_id = Column(Integer, ForeignKey("query_logs.id"))
    feedback_type = Column(String(20))
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="feedbacks")
    query_log = relationship("QueryLog", back_populates="feedbacks")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True)
    user_type = Column(String(20))
    preferences = Column(Text)
    accessibility_settings = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("user_profiles.user_id"))
    session_duration = Column(Integer)
    break_intervals = Column(Text)
    eye_strain_level = Column(Integer)
    posture_data = Column(Text)
    health_score = Column(Float)
    recommendations = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserProfile", back_populates="health_records")


class AnalyticsData(Base):
    __tablename__ = "analytics_data"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(50), ForeignKey("games.game_id"))
    metric_name = Column(String(50))
    metric_value = Column(Float)
    metric_data = Column(Text)
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="analytics_data")


Game.documents = relationship("Document", back_populates="game")
Game.query_logs = relationship("QueryLog", back_populates="game")
Game.feedbacks = relationship("Feedback", back_populates="game")
Game.analytics_data = relationship("AnalyticsData", back_populates="game")
QueryLog.feedbacks = relationship("Feedback", back_populates="query_log")
UserProfile.health_records = relationship("HealthRecord", back_populates="user")


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)


def drop_tables():
    Base.metadata.drop_all(bind=engine)


def ensure_game_record(db: Session, game_id: str, game_name: str | None = None) -> Game:
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if game:
        return game

    game = Game(
        game_id=game_id,
        game_name=game_name or DEFAULT_GAME_NAMES.get(game_id, game_id.upper()),
        version="current",
        platforms=json.dumps(["pc", "mobile"], ensure_ascii=False),
        languages=json.dumps(["zh-CN"], ensure_ascii=False),
    )
    db.add(game)
    db.flush()
    return game


def is_external_database_enabled() -> bool:
    return ACTIVE_DATABASE_URL.startswith("postgresql") and not USING_FALLBACK_DATABASE


def database_status() -> dict:
    backend = "sqlite" if ACTIVE_DATABASE_URL.startswith("sqlite") else "postgresql"
    requested_backend = "postgresql" if REQUESTED_DATABASE_URL.startswith("postgresql") else "sqlite"
    return {
        "using_fallback": USING_FALLBACK_DATABASE,
        "backend": backend,
        "requested_backend": requested_backend,
        "active_url": _mask_db_url(ACTIVE_DATABASE_URL),
        "requested_url": _mask_db_url(REQUESTED_DATABASE_URL),
        "is_external": is_external_database_enabled(),
        "init_error": DATABASE_INIT_ERROR,
    }
