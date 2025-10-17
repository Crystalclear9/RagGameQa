# 工具模块
"""
工具模块

提供文本处理、文件操作、日志配置和常量定义等工具函数。
支持系统运行所需的各种辅助功能。
"""

# 可选导入，避免导入错误
try:
    from .text_utils import TextUtils
except ImportError:
    TextUtils = None

try:
    from .file_utils import *
except ImportError:
    pass

try:
    from .logging_config import *
except ImportError:
    pass

try:
    from .constants import *
except ImportError:
    pass

__all__ = ["TextUtils"]
