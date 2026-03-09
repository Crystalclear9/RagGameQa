"""数据库配置与模型定义。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from config.settings import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQLITE_FALLBACK_PATH = PROJECT_ROOT / "data" / "rag_game_qa.db"
DEFAULT_GAME_NAMES = {
    "wow": "魔兽世界",
    "lol": "英雄联盟",
    "genshin": "原神",
    "minecraft": "我的世界",
    "valorant": "无畏契约",
    "apex": "Apex 英雄",
}


def _build_engine(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif database_url.startswith("postgresql"):
        connect_args["connect_timeout"] = 2
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


def _initialize_engine():
    requested_url = settings.get_database_url()

    try:
        engine = _build_engine(requested_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("数据库连接成功")
        return engine, requested_url, False
    except Exception as exc:
        SQLITE_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        fallback_url = f"sqlite:///{SQLITE_FALLBACK_PATH.as_posix()}"
        logger.warning("数据库连接失败，切换到SQLite回退模式: %s", exc)
        engine = _build_engine(fallback_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return engine, fallback_url, True


engine, ACTIVE_DATABASE_URL, USING_FALLBACK_DATABASE = _initialize_engine()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


class Game(Base):
    """游戏信息表"""

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
    """文档表"""

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
    """查询日志表"""

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
    """用户反馈表"""

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
    """用户档案表"""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True)
    user_type = Column(String(20))
    preferences = Column(Text)
    accessibility_settings = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HealthRecord(Base):
    """健康记录表"""

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
    """分析数据表"""

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
    """获取数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建所有表。"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除所有表。"""
    Base.metadata.drop_all(bind=engine)


def ensure_game_record(db: Session, game_id: str, game_name: str | None = None) -> Game:
    """在写入日志和反馈前，确保游戏记录存在。"""
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


def database_status() -> dict:
    """返回数据库运行状态，用于启动日志与前端展示。"""
    return {
        "using_fallback": USING_FALLBACK_DATABASE,
        "backend": "sqlite" if ACTIVE_DATABASE_URL.startswith("sqlite") else "configured",
    }
