"""
路径常量定义
定义项目中常用的路径常量，便于统一管理和维护
"""

from pathlib import Path
from typing import Dict


# 动态确定项目根目录
def _get_project_root() -> str:
    """获取项目根目录"""
    # 从当前文件位置向上查找
    current_file = Path(__file__).resolve()
    return str(current_file.parent.parent.parent)


# 路径常量字典
PATH_CONSTANTS: Dict[str, str] = {
    'PROJECT_ROOT': _get_project_root(),
    'CORE_PATH': str(Path(_get_project_root()) / 'core'),
    'LOGGER_PATH': str(Path(_get_project_root()) / 'core' / 'logger'),
    'ERROR_PATH': str(Path(_get_project_root()) / 'core' / 'error'),
    'DATA_PATH': str(Path(_get_project_root()) / 'data'),
    'CONFIG_PATH': str(Path(_get_project_root()) / 'config'),
    'LOGS_PATH': str(Path(_get_project_root()) / 'logs'),
    'SRC_PATH': str(Path(_get_project_root()) / 'src'),
    'TESTS_PATH': str(Path(_get_project_root()) / 'tests'),
}

# 预定义的目录结构
DEFAULT_DIRECTORIES = [
    PATH_CONSTANTS['DATA_PATH'],
    PATH_CONSTANTS['CONFIG_PATH'],
    PATH_CONSTANTS['LOGS_PATH'],
]