"""
配置常量定义
"""

from typing import Dict, Any, Callable

# 默认配置文件名
DEFAULT_CONFIG_FILENAME = "config.yaml"

# 路径相关常量
PATH_CONSTANTS: Dict[str, str] = {
    "CONFIG_DIR": "config",
    "LOG_DIR": "logs",
    "DATA_DIR": "data",
    "OUTPUT_DIR": "output",
    "TEMP_DIR": "temp"
}

# 配置验证规则
CONFIG_VALIDATORS: Dict[str, Callable[[Any], bool]] = {
    "log_level": lambda x: isinstance(x, str) and x.upper() in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"},
    "debug_mode": lambda x: isinstance(x, bool),
    "config_file": lambda x: isinstance(x, str)
}
