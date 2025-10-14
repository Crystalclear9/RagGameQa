# 数据库配置
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config.settings import settings

# 创建数据库引擎
engine = create_engine(settings.get_database_url())

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 数据模型定义
class Game(Base):
    """游戏信息表"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(50), unique=True, index=True)
    game_name = Column(String(100), nullable=False)
    version = Column(String(20))
    platforms = Column(Text)  # JSON字符串
    languages = Column(Text)  # JSON字符串
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
    metadata = Column(Text)  # JSON字符串
    embedding = Column(Text)  # 向量嵌入
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
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
    user_context = Column(Text)  # JSON字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    game = relationship("Game", back_populates="query_logs")

class Feedback(Base):
    """用户反馈表"""
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(50), ForeignKey("games.game_id"))
    user_id = Column(String(50))
    query_log_id = Column(Integer, ForeignKey("query_logs.id"))
    feedback_type = Column(String(20))  # positive, negative, neutral
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    game = relationship("Game", back_populates="feedbacks")
    query_log = relationship("QueryLog", back_populates="feedbacks")

class UserProfile(Base):
    """用户档案表"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True)
    user_type = Column(String(20))  # normal, elderly, visual_impairment, hearing_impairment
    preferences = Column(Text)  # JSON字符串
    accessibility_settings = Column(Text)  # JSON字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HealthRecord(Base):
    """健康记录表"""
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("user_profiles.user_id"))
    session_duration = Column(Integer)  # 游戏时长（秒）
    break_intervals = Column(Text)  # JSON字符串
    eye_strain_level = Column(Integer)  # 1-10
    posture_data = Column(Text)  # JSON字符串
    health_score = Column(Float)
    recommendations = Column(Text)  # JSON字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("UserProfile", back_populates="health_records")

class AnalyticsData(Base):
    """分析数据表"""
    __tablename__ = "analytics_data"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(50), ForeignKey("games.game_id"))
    metric_name = Column(String(50))
    metric_value = Column(Float)
    metric_data = Column(Text)  # JSON字符串
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    game = relationship("Game", back_populates="analytics_data")

# 添加反向关系
Game.documents = relationship("Document", back_populates="game")
Game.query_logs = relationship("QueryLog", back_populates="game")
Game.feedbacks = relationship("Feedback", back_populates="game")
Game.analytics_data = relationship("AnalyticsData", back_populates="game")
QueryLog.feedbacks = relationship("Feedback", back_populates="query_log")
UserProfile.health_records = relationship("HealthRecord", back_populates="user")

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)
