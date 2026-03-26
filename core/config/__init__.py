"""
配置管理器 - 高内聚低耦合的配置管理解决方案
对外暴露统一的配置访问接口，确保项目中所有配置操作都通过此管理器
"""

from typing import Any, Dict, Callable, Type, Optional
from .config_manager import ConfigManager
from .constants import DEFAULT_CONFIG_FILENAME

# 延迟初始化的全局配置管理器实例
_config_manager: Optional[ConfigManager] = None

__all__ = [
    'get_config_manager',
    'get_config',
    'set_config', 
    'has_config',
    'get_all_configs',
    'register_config',
    'add_config_listener',
    'remove_config_listener',
    'add_config_key_listener', 
    'remove_config_key_listener',
    'save_config',
    'load_config',
    'reset_all_configs',
    'reset_config',
    'ConfigManager',
    'DEFAULT_CONFIG_FILENAME'
]


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例（延迟初始化）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

# 对外暴露的核心接口，全部委托给 get_config_manager()
def get_config(key: str, default: Any = None) -> Any:
    return get_config_manager().get_config(key, default)

def set_config(key: str, value: Any) -> bool:
    return get_config_manager().set_config(key, value)

def has_config(key: str) -> bool:
    return get_config_manager().has_config(key)

def get_all_configs() -> Dict[str, Any]:
    return get_config_manager().get_all_configs()

def register_config(
    key: str, 
    default_value: Any, 
    value_type: Type[Any],
    description: str = ""
) -> None:
    get_config_manager().register_config(key, default_value, value_type, description)

def add_config_listener(listener: Callable[[str, Any, Any], None]) -> None:
    get_config_manager().add_global_listener(listener)

def remove_config_listener(listener: Callable[[str, Any, Any], None]) -> bool:
    get_config_manager().remove_global_listener(listener)
    return True

def add_config_key_listener(key: str, listener: Callable[[str, Any, Any], None]) -> None:
    get_config_manager().add_key_listener(key, listener)

def remove_config_key_listener(key: str, listener: Callable[[str, Any, Any], None]) -> bool:
    return get_config_manager().remove_key_listener(key, listener)

def save_config(filename: str = DEFAULT_CONFIG_FILENAME) -> bool:
    return get_config_manager().save_to_file(filename)

def load_config(filename: str = DEFAULT_CONFIG_FILENAME) -> bool:
    return get_config_manager().load(filename)

def reset_all_configs() -> None:
    get_config_manager().reset_to_defaults()

def reset_config(key: str) -> bool:
    return get_config_manager().reset_config(key)
