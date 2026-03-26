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
        env_root = os.getenv('INFRA_PROJECT_ROOT')
        if env_root and os.path.exists(env_root):
            return PathUtils.normalize_path(env_root)
        
        # 从当前文件向上查找包含core目录的父目录
        current_file = Path(__file__).resolve()
        current_dir = current_file.parent
        
        # 向上查找直到找到包含core的目录
        for parent in [current_dir] + list(current_dir.parents):
            core_path = parent / 'core'
            if core_path.exists() and core_path.is_dir():
                # 检查是否是项目的core目录（包含logger子目录）
                logger_path = core_path / 'logger'
                if logger_path.exists() and logger_path.is_dir():
                    return PathUtils.normalize_path(str(parent))
        
        # 如果找不到，使用当前工作目录
        return PathUtils.normalize_path(os.getcwd())
    
    def _initialize_paths(self) -> None:
        """初始化所有路径常量"""
        # 更新全局常量
        PATH_CONSTANTS['PROJECT_ROOT'] = self._project_root
        PATH_CONSTANTS['CORE_PATH'] = PathUtils.join_paths(self._project_root, 'core')
        PATH_CONSTANTS['LOGGER_PATH'] = PathUtils.join_paths(PATH_CONSTANTS['CORE_PATH'], 'logger')
        PATH_CONSTANTS['ERROR_PATH'] = PathUtils.join_paths(PATH_CONSTANTS['CORE_PATH'], 'error')
        PATH_CONSTANTS['DATA_PATH'] = PathUtils.join_paths(self._project_root, 'data')
        PATH_CONSTANTS['CONFIG_PATH'] = PathUtils.join_paths(self._project_root, 'config')
        PATH_CONSTANTS['OUTPUT_PATH'] = PathUtils.join_paths(self._project_root, 'output')
        PATH_CONSTANTS['LOGS_PATH'] = PathUtils.join_paths(self._project_root, 'logs')
    
    def get_project_root(self) -> str:
        """获取项目根目录"""
        return self._project_root
    
    def get_core_path(self) -> str:
        """获取 core 模块路径"""
        return PATH_CONSTANTS['CORE_PATH']
    
    def get_logger_path(self) -> str:
        """获取 logger 模块路径"""
        return PATH_CONSTANTS['LOGGER_PATH']
    
    def get_error_path(self) -> str:
        """获取 error 模块路径"""
        return PATH_CONSTANTS['ERROR_PATH']
    
    def get_data_path(self) -> str:
        """获取数据目录路径"""
        return PATH_CONSTANTS['DATA_PATH']
    
    def get_config_path(self) -> str:
        """获取配置文件目录路径"""
        return PATH_CONSTANTS['CONFIG_PATH']
    
    def get_output_path(self) -> str:
        """获取输出目录路径"""
        return PATH_CONSTANTS['OUTPUT_PATH']
    
    def get_logs_path(self) -> str:
        """获取日志目录路径"""
        return PATH_CONSTANTS['LOGS_PATH']
    
    def get_all_paths(self) -> Dict[str, str]:
        """获取所有路径映射"""
        return PATH_CONSTANTS.copy()