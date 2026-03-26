"""
路径管理器 - 高内聚低耦合的路径管理解决方案
对外暴露统一的路径访问接口，确保项目中所有路径操作都通过此管理器
"""

from .path_manager import PathManager
from .constants import PATH_CONSTANTS
from .utils import PathUtils
from typing import Optional

__all__ = [
    'get_project_root',
    'get_core_path',
    'get_logger_path',
    'get_error_path',
    'get_data_path',
    'get_config_path',
    'get_output_path',
    'get_logs_path',
    'join_paths',
    'normalize_path',
    'is_valid_path',
    'ensure_directory_exists',
    'path_manager',
    'PathManager',
    'PathUtils',
    'PATH_CONSTANTS',
    'PROJECT_ROOT',
    'CORE_PATH'
]

# 创建全局路径管理器实例
path_manager: PathManager = PathManager()

# 对外暴露的核心接口
def get_project_root() -> str:
    """获取项目根目录"""
    return path_manager.get_project_root()

def get_core_path() -> str:
    """获取 core 模块路径"""
    return path_manager.get_core_path()

def get_logger_path() -> str:
    """获取 logger 模块路径"""
    return path_manager.get_logger_path()

def get_error_path() -> str:
    """获取 error 模块路径"""
    return path_manager.get_error_path()

def get_data_path() -> str:
    """获取数据目录路径"""
    return path_manager.get_data_path()

def get_config_path() -> str:
    """获取配置文件目录路径"""
    return path_manager.get_config_path()

def get_output_path() -> str:
    """获取输出目录路径"""
    return path_manager.get_output_path()

def get_logs_path() -> str:
    """获取日志目录路径"""
    return path_manager.get_logs_path()

def join_paths(*paths: str) -> str:
    """安全地拼接路径"""
    return PathUtils.join_paths(*paths)

def normalize_path(path: str) -> str:
    """标准化路径格式"""
    return PathUtils.normalize_path(path)

def is_valid_path(path: Optional[str]) -> bool:
    """校验路径是否有效"""
    return PathUtils.is_valid_path(path)

def ensure_directory_exists(path: str) -> str:
    """确保目录存在，不存在则创建"""
    return PathUtils.ensure_directory_exists(path)

# 重新导出常量以便直接访问
PROJECT_ROOT = PATH_CONSTANTS['PROJECT_ROOT']
CORE_PATH = PATH_CONSTANTS['CORE_PATH']