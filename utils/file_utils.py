# 文件工具
import os
import json
from typing import Dict, Any, Optional


class FileUtils:
    """文件处理工具（兼容旧接口）"""

    @staticmethod
    def ensure_dir(directory: str):
        """确保目录存在"""
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def load_json(file_path: str) -> Optional[Dict[str, Any]]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载JSON文件失败: {e}")
            return None

    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str):
        """保存JSON文件"""
        try:
            FileUtils.ensure_dir(os.path.dirname(file_path))
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存JSON文件失败: {e}")


# 为utils.__init__中的导出提供新接口别名
class FileManager:
    """文件管理器（对FileUtils的简单封装）"""

    @staticmethod
    def ensure_dir(directory: str):
        return FileUtils.ensure_dir(directory)

    @staticmethod
    def load_json(file_path: str) -> Optional[Dict[str, Any]]:
        return FileUtils.load_json(file_path)

    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str):
        return FileUtils.save_json(data, file_path)


class ConfigLoader:
    """配置加载工具"""

    @staticmethod
    def load_json_config(path: str) -> Dict[str, Any]:
        cfg = FileUtils.load_json(path)
        return cfg or {}

    @staticmethod
    def dump_json_config(cfg: Dict[str, Any], path: str):
        FileUtils.save_json(cfg, path)
