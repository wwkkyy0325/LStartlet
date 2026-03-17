"""
UI服务注册模块
负责将UI相关的服务注册到依赖注入容器中
"""

from typing import Any
from core.di.container_config import ContainerConfigurator
from ui.factories.ui_factory_interface import IUIFactory
from ui.factories.component_factory_interface import IComponentFactory


def register_ui_services(configurator: ContainerConfigurator) -> None:
    """注册UI相关服务到容器中"""
    
    def component_factory_factory(container: Any) -> IComponentFactory:
        """组件工厂的工厂函数"""
        from ui.factories.component_factory_impl import ComponentFactoryImpl
        return ComponentFactoryImpl()
    
    # 注册组件工厂为单例
    configurator.register_singleton(
        IComponentFactory,
        factory=component_factory_factory
    )
    
    def ui_factory_factory(container: Any) -> IUIFactory:
        """UI工厂的工厂函数"""
        from core.event.event_bus import EventBus
        from core.scheduler.tick import TickComponent
        from ui.factories.component_factory_interface import IComponentFactory
        from ui.factories.ui_factory_impl import UIFactoryImpl
        
        event_bus = container.resolve(EventBus)
        tick_component = container.resolve(TickComponent)
        component_factory = container.resolve(IComponentFactory)
        
        return UIFactoryImpl(
            event_bus=event_bus,
            tick_component=tick_component,
            component_factory=component_factory,
            on_close_callback=None  # 可以在需要时通过setter设置
        )
    
    # 注册UI工厂为瞬态服务（每次请求都创建新实例）
    configurator.register_transient(
        IUIFactory,
        factory=ui_factory_factory
    )