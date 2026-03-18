from core.di.container_config import ContainerConfigurator
from core.config.config_manager import ConfigManager
from core.event.event_bus import EventBus
from core.logger.logger import MultiProcessLogger


def register_core_services(configurator: ContainerConfigurator) -> None:
    """注册核心服务到容器中"""
    # 配置管理器 - 单例
    configurator.register_singleton(ConfigManager)
    
    # 事件总线 - 单例  
    configurator.register_singleton(EventBus)
    
    # 日志管理器 - 单例
    configurator.register_singleton(MultiProcessLogger)


def register_application_services(configurator: ContainerConfigurator) -> None:
    """注册应用程序特定服务"""
    # 注册核心服务
    register_core_services(configurator)
    
    # 这里可以添加更多应用特定的服务
    # configurator.register_transient(SomeService)