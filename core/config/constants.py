"""
配置管理器常量定义
"""

from typing import Dict, Any, Callable

# 默认配置文件名
DEFAULT_CONFIG_FILENAME = "config.yaml"

# 配置类型枚举
CONFIG_TYPES = {
    "STRING": "string",
    "INTEGER": "integer", 
    "FLOAT": "float",
    "BOOLEAN": "boolean",
    "LIST": "list",
    "DICT": "dict",
    "PATH": "path"
}

# 系统默认配置
SYSTEM_DEFAULT_CONFIGS: Dict[str, Any] = {
    # 日志相关配置
    "log_level": "DEBUG",
    "log_console_enabled": True,
    "log_file_enabled": True,
    "log_max_size_mb": 100,
    "log_backup_count": 7,
    
    # 路径相关配置
    "data_dir": "data",
    "output_dir": "output",
    "temp_dir": "temp",
    
    # 应用相关配置
    "app_name": "Infrastructure Framework",
    "app_version": "1.0.0",
    "debug_mode": False,
    "auto_save_config": True,
    
    # 通用性能配置
    "max_workers": 4,
    "timeout": 30.0,
}

# 定义验证函数类型
ValidatorFunc = Callable[[Any], bool]

# 配置验证规则
CONFIG_VALIDATORS: Dict[str, ValidatorFunc] = {
    "log_level": lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    "log_max_size_mb": lambda x: isinstance(x, int) and x > 0,
    "log_backup_count": lambda x: isinstance(x, int) and x >= 0,
    "debug_mode": lambda x: isinstance(x, bool),
    "auto_save_config": lambda x: isinstance(x, bool),
    "max_workers": lambda x: isinstance(x, int) and x > 0,
    "timeout": lambda x: isinstance(x, (int, float)) and x > 0,
}