"""
配置管理器 - 高内聚低耦合的配置管理解决方案
对外暴露统一的配置访问接口，确保项目中所有配置操作都通过此管理器
"""

from typing import Any, Callable, Optional, Union, List, Type
from .config_manager import ConfigManager

# 延迟初始化的全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def _get_config_manager() -> ConfigManager:
    """获取配置管理器实例（内部使用，不对外暴露）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


# ==================== 核心公共接口 ====================

def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置项的值
    
    Args:
        key: 配置键名（支持点号分隔的嵌套键）
        default: 默认值，当配置不存在时返回
        
    Returns:
        配置值或默认值
    """
    return _get_config_manager().get_config(key, default)


def set_config(key: str, value: Any) -> bool:
    """
    设置配置项的值
    
    Args:
        key: 配置键名
        value: 配置值
        
    Returns:
        是否设置成功（类型验证通过且非受保护配置）
    """
    return _get_config_manager().set_config(key, value)


class ConfigWatcher:
    """配置监听器句柄"""
    
    def __init__(self, manager: ConfigManager, keys: Optional[List[str]] = None):
        self._manager = manager
        self._keys = keys or []
        self._active = True
    
    def stop(self):
        """停止监听"""
        if self._active:
            self._manager.remove_watcher(self)
            self._active = False


def watch_config(
    key: Union[str, List[str], None] = None,
    callback: Optional[Callable[[str, Any, Any], None]] = None
) -> ConfigWatcher:
    """
    监听配置变更
    
    Args:
        key: 要监听的配置键，可以是单个键、键列表或None（监听所有）
        callback: 配置变更回调函数，签名: (key: str, old_value: Any, new_value: Any) -> None
        
    Returns:
        ConfigWatcher 对象，可用于停止监听
        
    Example:
        # 监听单个配置
        watcher = watch_config("database.host", lambda k, old, new: print(f"{k} changed"))
        
        # 监听多个配置
        watcher = watch_config(["app.debug", "server.port"], my_callback)
        
        # 监听所有配置
        watcher = watch_config(callback=global_callback)
    """
    if callback is None:
        raise ValueError("callback function is required")
    
    manager = _get_config_manager()
    
    if key is None:
        # 监听所有配置
        manager.add_global_listener(callback)
        return ConfigWatcher(manager)
    elif isinstance(key, str):
        # 监听单个配置
        manager.add_key_listener(key, callback)
        return ConfigWatcher(manager, [key])
    else:
        # 监听多个配置
        for k in key:
            manager.add_key_listener(k, callback)
        return ConfigWatcher(manager, key)


def register_config(
    key: str, 
    default_value: Any, 
    value_type: Type[Any], 
    description: str = "",
    validator: Optional[Callable[[Any], bool]] = None,
    schema: Optional[dict] = None,
) -> None:
    """注册新的配置项（内部使用）"""
    _get_config_manager().register_config(
        key, default_value, value_type, description, 
        validator=validator, schema=schema
    )


# 对外暴露的公共API
__all__ = [
    "get_config",
    "set_config", 
    "watch_config",
    "ConfigWatcher",
    # 注意：register_config 不在 __all__ 中，仅供内部模块直接导入使用
]
