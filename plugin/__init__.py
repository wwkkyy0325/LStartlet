"""Plugin module exports"""

# 延迟导入以避免循环依赖
def _get_plugin_base():
    from .base.plugin_base import PluginBase
    return PluginBase

def _get_iplugin():
    from .base.plugin_interface import IPlugin
    return IPlugin

def _get_iplugin_manager():
    from .base.plugin_interface import IPluginManager
    return IPluginManager

def _get_plugin_manager():
    from .manager.plugin_manager import PluginManager
    return PluginManager

# 插件系统核心类
PluginBase = _get_plugin_base()
IPlugin = _get_iplugin()
IPluginManager = _get_iplugin_manager()
PluginManager = _get_plugin_manager()

# 插件装饰器
from core.decorators import plugin_component, plugin_event_handler

# 明确导出的符号
__all__ = [
    'PluginBase',
    'IPlugin', 
    'IPluginManager',
    'PluginManager',
    'plugin_component',
    'plugin_event_handler'
]