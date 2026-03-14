"""
插件系统初始化模块
"""

from plugin.manager.plugin_manager import PluginManager
from core.di import ServiceContainer
from core.event.event_bus import EventBus
from core.di.service_descriptor import ServiceLifetime


def initialize_plugin_system(container: ServiceContainer, event_bus: EventBus) -> PluginManager:
    """
    初始化插件系统
    
    Args:
        container: 依赖注入容器
        event_bus: 事件总线
        
    Returns:
        插件管理器实例
    """
    from core.logger import info
    
    info("正在初始化插件系统...")
    
    # 创建插件管理器
    plugin_manager = PluginManager(container, event_bus)
    
    # 注册到依赖注入容器
    container.register(PluginManager, instance=plugin_manager, lifetime=ServiceLifetime.SINGLETON)
    
    info("插件系统初始化完成")
    return plugin_manager