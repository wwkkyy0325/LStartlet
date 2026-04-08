"""
超级简化的路径管理器 - 只提供最基本的路径功能
作为工具函数集合，不包含复杂的类结构和自动检测逻辑
"""

import os
from pathlib import Path
from typing import Optional


# 全局项目根目录，默认为当前工作目录
_PROJECT_ROOT: str = os.getcwd()


def set_project_root(root_path: str) -> None:
    """
    设置项目根目录

    Args:
        root_path: 项目根目录的绝对路径

    Example:
        >>> import os
        >>> from LStartlet.core.utils import set_project_root
        >>> set_project_root(os.path.dirname(os.path.abspath(__file__)))
    """
    global _PROJECT_ROOT
    if not os.path.exists(root_path):
        raise ValueError(f"Project root path does not exist: {root_path}")
    _PROJECT_ROOT = str(Path(root_path).resolve())


def get_project_root() -> str:
    """
    获取项目根目录

    Returns:
        项目根目录的绝对路径

    Example:
        >>> from LStartlet.core.utils import get_project_root
        >>> root = get_project_root()
    """
    return _PROJECT_ROOT


def join_paths(*paths: str) -> str:
    """
    安全地拼接路径

    Args:
        *paths: 要拼接的路径片段

    Returns:
        拼接后的标准化路径

    Example:
        >>> from LStartlet.core.utils import join_paths
        >>> config_path = join_paths(get_project_root(), "config", "app.conf")
    """
    if not paths:
        return ""

    result = Path(paths[0])
    for path in paths[1:]:
        if path:
            result = result / path

    return str(result.resolve())


def ensure_directory_exists(path: str) -> str:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        标准化后的目录路径
    """
    if not path:
        return ""

    normalized_path = str(Path(path).resolve())
    Path(normalized_path).mkdir(parents=True, exist_ok=True)
    return normalized_path


# 兼容性别名（保持与旧API一致）
get_core_path = lambda: join_paths(get_project_root(), "src", "LStartlet", "core")
get_logger_path = lambda: join_paths(
    get_project_root(), "src", "LStartlet", "core", "logger"
)
get_data_path = lambda: join_paths(get_project_root(), "data")
get_config_path = lambda: join_paths(get_project_root(), "config")
get_logs_path = lambda: join_paths(get_project_root(), "logs")


# 简单的tick函数 - 替代原来的复杂调度器
import time


def get_tick_time() -> float:
    """
    获取当前时间戳（秒）

    Returns:
        当前时间戳（浮点数，秒）
    """
    return time.time()


def get_tick_ms() -> int:
    """
    获取当前时间戳（毫秒）

    Returns:
        当前时间戳（整数，毫秒）
    """
    return int(time.time() * 1000)
