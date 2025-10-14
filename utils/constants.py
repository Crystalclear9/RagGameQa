# 常量定义
from enum import Enum

class UserType(Enum):
    """用户类型"""
    NORMAL = "normal"
    ELDERLY = "elderly"
    VISUAL_IMPAIRMENT = "visual_impairment"
    HEARING_IMPAIRMENT = "hearing_impairment"

class GamePlatform(Enum):
    """游戏平台"""
    STEAM = "steam"
    EPIC = "epic"
    BATTLE_NET = "battle_net"
    ORIGIN = "origin"

class FeedbackType(Enum):
    """反馈类型"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    BALANCE_FEEDBACK = "balance_feedback"
    GENERAL_QUESTION = "general_question"

# 系统常量
MAX_QUESTION_LENGTH = 1000
MAX_ANSWER_LENGTH = 2000
DEFAULT_CONFIDENCE_THRESHOLD = 0.7
MAX_RETRIEVAL_RESULTS = 10
DEFAULT_EMBEDDING_DIMENSION = 384

# API常量
API_VERSION = "v1"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 多模态常量
SUPPORTED_AUDIO_FORMATS = ["wav", "mp3", "m4a"]
SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "gif"]
MAX_AUDIO_DURATION = 30  # 秒
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# 无障碍常量
PATIENCE_THRESHOLD = 3
SIMILARITY_THRESHOLD_ELDERLY = 0.85
MAX_GAME_SESSION_TIME = 3600  # 1小时
BLUE_LIGHT_REDUCTION_RATIO = 0.3
