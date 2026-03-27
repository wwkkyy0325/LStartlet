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
        """确定项目根目录"""
        # 尝试从环境变量获取
        env_root = os.getenv("INFRA_PROJECT_ROOT")
        if env_root and os.path.exists(env_root):
            return PathUtils.normalize_path(env_root)

        # 从当前文件向上查找
        current_file = Path(__file__).resolve()
        current_dir = current_file.parent

        # 向上查找直到找到项目根目录标识
        for parent in [current_dir] + list(current_dir.parents):
            # 检查是否包含core目录（我们的框架核心）
            core_path = parent / "core"
            if core_path.exists() and core_path.is_dir():
                # 进一步检查是否是真正的项目根目录
                # 真正的项目根目录应该包含项目标识文件
                project_indicators = [
                    "setup.py",
                    "pyproject.toml",
                    ".git",
                    "README.md",
                    "requirements.txt",
                ]

                # 检查当前parent目录是否包含这些标识文件
                has_project_indicator = any(
                    (parent / indicator).exists() for indicator in project_indicators
                )

                if has_project_indicator:
                    # 这很可能是真正的项目根目录
                    return PathUtils.normalize_path(str(parent))

                # 如果没有项目标识文件，但有core目录，检查parent的父目录
                # 这处理src布局的情况：src/LStartlet/core -> src/LStartlet 可能不是根目录
                # 继续向上查找真正的根目录
                continue

            # 如果当前目录没有core，但有项目标识文件，也可能是根目录
            # （比如在测试环境中直接运行）
            project_indicators = [
                "setup.py",
                "pyproject.toml",
                ".git",
                "README.md",
                "requirements.txt",
            ]
            has_project_indicator = any(
                (parent / indicator).exists() for indicator in project_indicators
            )
            if has_project_indicator:
                return PathUtils.normalize_path(str(parent))

        # 如果找不到合适的根目录，回退到包含core的最高层级目录
        for parent in [current_dir] + list(current_dir.parents):
            core_path = parent / "core"
            if core_path.exists() and core_path.is_dir():
                logger_path = core_path / "logger"
                if logger_path.exists() and logger_path.is_dir():
                    return PathUtils.normalize_path(str(parent))

        # 最后的回退方案：使用当前工作目录
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
