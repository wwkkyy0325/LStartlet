import os
from typing import Dict
from pathlib import Path
from .constants import PATH_CONSTANTS
from .utils import PathUtils


class PathManager:
    """路径管理器 - 负责管理项目中所有关键路径"""

    def __init__(self):
        self._project_root = self._determine_project_root()
        self._initialize_paths()

    def _determine_project_root(self) -> str:
        """确定项目根目录
        
        使用明确的优先级策略：
        1. 环境变量 INFRA_PROJECT_ROOT
        2. 包含项目标识文件的目录（setup.py, pyproject.toml, .git, README.md, requirements.txt）
        3. 当前工作目录（最后回退方案）
        """
        # 1. 尝试从环境变量获取
        env_root = os.getenv("INFRA_PROJECT_ROOT")
        if env_root and os.path.exists(env_root):
            return PathUtils.normalize_path(env_root)

        # 2. 从当前文件向上查找包含项目标识文件的目录
        current_file = Path(__file__).resolve()
        current_dir = current_file.parent
        
        # 项目根目录标识文件列表
        project_indicators = [
            "setup.py",
            "pyproject.toml", 
            ".git",
            "README.md",
            "requirements.txt"
        ]
        
        # 向上查找直到找到包含项目标识文件的目录
        for parent in [current_dir] + list(current_dir.parents):
            has_project_indicator = any(
                (parent / indicator).exists() for indicator in project_indicators
            )
            if has_project_indicator:
                return PathUtils.normalize_path(str(parent))
        
        # 3. 最后的回退方案：使用当前工作目录
        return PathUtils.normalize_path(os.getcwd())

    def set_project_root(self, root_path: str) -> None:
        """显式设置项目根目录

        Args:
            root_path: 项目根目录路径

        Usage:
            # 在用户的main.py中调用
            from LStartlet.core.path import path_manager
            path_manager.set_project_root(os.path.dirname(os.path.abspath(__file__)))
        """
        if not os.path.exists(root_path):
            raise ValueError(f"Project root path does not exist: {root_path}")

        self._project_root = PathUtils.normalize_path(root_path)
        self._initialize_paths()

    def _initialize_paths(self) -> None:
        """初始化所有路径常量"""
        # 更新全局常量
        PATH_CONSTANTS["PROJECT_ROOT"] = self._project_root
        PATH_CONSTANTS["CORE_PATH"] = PathUtils.join_paths(self._project_root, "core")
        PATH_CONSTANTS["LOGGER_PATH"] = PathUtils.join_paths(
            PATH_CONSTANTS["CORE_PATH"], "logger"
        )
        PATH_CONSTANTS["ERROR_PATH"] = PathUtils.join_paths(
            PATH_CONSTANTS["CORE_PATH"], "error"
        )
        PATH_CONSTANTS["DATA_PATH"] = PathUtils.join_paths(self._project_root, "data")
        PATH_CONSTANTS["CONFIG_PATH"] = PathUtils.join_paths(
            self._project_root, "config"
        )
        PATH_CONSTANTS["LOGS_PATH"] = PathUtils.join_paths(self._project_root, "logs")

        # 自动创建默认目录结构
        self._create_default_directories()

    def _create_default_directories(self) -> None:
        """自动创建默认的目录结构"""
        # 动态获取当前的目录路径，而不是使用预定义的常量
        directories_to_create = [
            PATH_CONSTANTS["DATA_PATH"],
            PATH_CONSTANTS["CONFIG_PATH"],
            PATH_CONSTANTS["LOGS_PATH"],
        ]

        for directory in directories_to_create:
            PathUtils.ensure_directory_exists(directory)

    def get_project_root(self) -> str:
        """获取项目根目录"""
        return self._project_root

    def get_core_path(self) -> str:
        """获取 core 模块路径"""
        core_path = PATH_CONSTANTS["CORE_PATH"]
        assert isinstance(core_path, str)
        return core_path

    def get_logger_path(self) -> str:
        """获取 logger 模块路径"""
        return PATH_CONSTANTS["LOGGER_PATH"]

    def get_error_path(self) -> str:
        """获取 error 模块路径"""
        return PATH_CONSTANTS["ERROR_PATH"]

    def get_data_path(self) -> str:
        """获取数据目录路径"""
        return PATH_CONSTANTS["DATA_PATH"]

    def get_config_path(self) -> str:
        """获取配置文件目录路径"""
        return PATH_CONSTANTS["CONFIG_PATH"]

    def get_logs_path(self) -> str:
        """获取日志目录路径"""
        return PATH_CONSTANTS["LOGS_PATH"]
