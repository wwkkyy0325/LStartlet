"""
配置管理器 - 高内聚低耦合的配置管理解决方案
对外暴露统一的配置访问接口，确保项目中所有配置操作都通过此管理器
"""

from typing import Any, Dict, Optional, Callable
from .config_manager import ConfigManager
from .constants import SYSTEM_DEFAULT_CONFIGS, CONFIG_VALIDATORS, DEFAULT_CONFIG_FILENAME

# 创建全局配置管理器实例
_config_manager: ConfigManager = ConfigManager()

# 初始化配置管理器
_config_manager.initialize()

# 对外暴露的核心接口
def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        key: 配置键名
        default: 默认值（如果配置不存在）
        
    Returns:
        配置值
    """
    return _config_manager.get_config(key, default)


def set_config(key: str, value: Any, validate: bool = True) -> bool:
    """
    设置配置值
    
    Args:
        key: 配置键名
        value: 配置值
        validate: 是否进行验证
        
    Returns:
        是否设置成功
    """
    return _config_manager.set_config(key, value, validate)


def has_config(key: str) -> bool:
    """
    检查配置项是否存在
    
    Args:
        key: 配置键名
        
    Returns:
        是否存在
    """
    return _config_manager.has_config(key)


def get_all_configs() -> Dict[str, Any]:
    """
    获取所有配置
    
    Returns:
        所有配置的副本
    """
    return _config_manager.get_all_configs()


def register_config(
    key: str, 
    default_value: Any, 
    validator: Optional[Callable[[Any], bool]] = None,
    description: str = ""
) -> None:
    """
    注册配置项
    
    Args:
        key: 配置键名
        default_value: 默认值
        validator: 验证函数
        description: 配置描述
    """
    _config_manager.register_config(key, default_value, validator, description)


def add_config_listener(key: str, listener: Callable[[str, Any, Any], None]) -> None:
    """
    添加配置监听器
    
    Args:
        key: 配置键名
        listener: 监听器函数
    """
    _config_manager.add_listener(key, listener)


def remove_config_listener(key: str, listener: Callable[[str, Any, Any], None]) -> bool:
    """
    移除配置监听器
    
    Args:
        key: 配置键名
        listener: 监听器函数
        
    Returns:
        是否成功移除
    """
    return _config_manager.remove_listener(key, listener)


def save_config(filename: str = DEFAULT_CONFIG_FILENAME) -> bool:
    """
    保存配置到文件
    
    Args:
        filename: 文件名
        
    Returns:
        是否保存成功
    """
    return _config_manager.save_to_file(filename)


def load_config(filename: str = DEFAULT_CONFIG_FILENAME) -> bool:
    """
    从文件加载配置
    
    Args:
        filename: 文件名
        
    Returns:
        是否加载成功
    """
    return _config_manager.load_from_file(filename)


def reset_config(key: str) -> bool:
    """
    重置配置项为默认值
    
    Args:
        key: 配置键名
        
    Returns:
        是否重置成功
    """
    return _config_manager.reset_config(key)


def reset_all_configs() -> None:
    """重置所有配置为默认值"""
    _config_manager.reset_all_configs()


def get_config_manager() -> ConfigManager:
    """
    获取配置管理器实例（用于高级操作）
    
    Returns:
        配置管理器实例
    """
    return _config_manager


# 预注册系统默认配置
def _register_default_configs() -> None:
    """注册系统默认配置"""
    for key, default_value in SYSTEM_DEFAULT_CONFIGS.items():
        validator = CONFIG_VALIDATORS.get(key)
        _config_manager.register_config(key, default_value, validator)


# 执行默认配置注册
_register_default_configs()