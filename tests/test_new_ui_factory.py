"""
UI工厂系统测试文件
测试新的DI驱动的UI工厂实现
"""

import unittest
from typing import Optional, Dict, Any

# 导入ServiceLifetime枚举和容器配置器
from core.di.service_descriptor import ServiceLifetime # type: ignore
from core.di.container_config import ContainerConfigurator # type: ignore
from core.di.service_container import ServiceContainer # type: ignore

# 测试目标模块
from ui.factories.ui_factory_impl import UIFactoryImpl # type: ignore
from ui.factories.component_factory_impl import ComponentFactoryImpl
from ui.components.base_component import BaseComponent # type: ignore

from PySide6.QtWidgets import QApplication, QWidget

from core.di.app_container import get_app_container, reset_app_container # type: ignore
from core.event.event_bus import EventBus # type: ignore
from core.scheduler.tick import TickComponent, TickConfig # type: ignore
from ui.factories.ui_factory_interface import IUIFactory
from ui.factories.component_factory_interface import IComponentFactory


class TestNewUIFactory(unittest.TestCase):
    """测试新的UI工厂系统"""
    
    @classmethod
    def setUpClass(cls):
        """测试类级别设置，创建QApplication"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
    
    def setUp(self) -> None:
        """测试前准备"""
        # 创建服务容器和配置器
        from core.di.service_container import ServiceContainer
        from core.di.container_config import ContainerConfigurator
        from core.event.event_bus import EventBus
        from core.scheduler.tick import TickComponent, TickConfig
        from ui.factories.component_factory_impl import ComponentFactoryImpl
        from ui.factories.ui_factory_impl import UIFactoryImpl
        from ui.factories.component_factory_interface import IComponentFactory
        from ui.factories.ui_factory_interface import IUIFactory
        from typing import Any
        
        container = ServiceContainer()
        configurator = ContainerConfigurator(container)
        
        # 注册核心服务
        configurator.register_singleton(EventBus)
        configurator.register_singleton(TickComponent)
        
        # 注册组件工厂
        def component_factory_factory(container_instance: Any) -> IComponentFactory:
            return ComponentFactoryImpl()
        
        configurator.register_singleton(
            IComponentFactory,
            factory=component_factory_factory
        )
        
        # 注册UI工厂
        def ui_factory_factory(container_instance: Any) -> IUIFactory:
            event_bus = container_instance.resolve(EventBus)
            tick_component = container_instance.resolve(TickComponent)
            component_factory = container_instance.resolve(IComponentFactory)
            return UIFactoryImpl(
                event_bus=event_bus,
                tick_component=tick_component,
                component_factory=component_factory
            )
        
        configurator.register_transient(
            IUIFactory,
            factory=ui_factory_factory
        )
        
        self.container = container
        
        # 创建UI工厂实例用于直接测试
        event_bus = EventBus()
        tick_component = TickComponent(TickConfig(interval=1.0, auto_start=False))
        component_factory = ComponentFactoryImpl()
        
        self.ui_factory = UIFactoryImpl(
            event_bus=event_bus,
            tick_component=tick_component,
            component_factory=component_factory
        )

    def tearDown(self):
        """测试后清理"""
        reset_app_container()
    
    def test_ui_factory_resolution(self):
        """测试UI工厂可以从DI容器中解析"""
        try:
            ui_factory = self.container.resolve(IUIFactory)
            self.assertIsNotNone(ui_factory)
            self.assertIsInstance(ui_factory, IUIFactory)
        except Exception as e:
            self.fail(f"UI工厂解析失败: {e}")
    
    def test_component_factory_resolution(self):
        """测试组件工厂可以从DI容器中解析"""
        try:
            component_factory = self.container.resolve(IComponentFactory)
            self.assertIsNotNone(component_factory)
            self.assertIsInstance(component_factory, IComponentFactory)
        except Exception as e:
            self.fail(f"组件工厂解析失败: {e}")
    
    def test_create_qt_application(self):
        """测试创建Qt应用程序"""
        ui_factory = self.container.resolve(IUIFactory)
        
        # 测试无参数创建
        app1 = ui_factory.create_qt_application()
        self.assertIsInstance(app1, QApplication)
        
        # 测试带参数创建
        app2 = ui_factory.create_qt_application(["test"])
        self.assertIsInstance(app2, QApplication)
        
        # 验证返回的是同一个实例
        self.assertIs(app1, app2)
    
    def test_get_qt_app(self):
        """测试获取Qt应用程序实例"""
        ui_factory = self.container.resolve(IUIFactory)
        
        # 先不创建应用
        app = ui_factory.get_qt_app()
        self.assertIsNone(app)
        
        # 创建应用后获取
        ui_factory.create_qt_application()
        app = ui_factory.get_qt_app()
        self.assertIsInstance(app, QApplication)
    
    def test_get_component_factory(self) -> None:
        """测试获取组件工厂"""
        factory = self.ui_factory
        
        # 获取组件工厂
        component_factory = factory.get_component_factory()
        self.assertIsNotNone(component_factory)
        self.assertIsInstance(component_factory, ComponentFactoryImpl)
        
        # 测试组件注册和创建
        from PySide6.QtWidgets import QLabel
        from typing import Optional, Dict, Any

        def test_component_factory(config: Optional[Dict[str, Any]] = None) -> QWidget:
            widget = QLabel("Test Component")
            widget.setObjectName("test_component")
            return widget
        
        component_factory.register_component_type("test", test_component_factory)
        self.assertIn("test", component_factory.get_registered_types())
        
        component = component_factory.create_component("test")
        self.assertIsNotNone(component)
        self.assertIsInstance(component, QLabel)
        from typing import cast
        component = cast(QLabel, component)  # 添加类型转换
        self.assertEqual(component.text(), "Test Component")

    def test_component_factory_integration(self):
        """测试组件工厂与UI工厂的集成"""
        ui_factory = self.container.resolve(IUIFactory)
        component_factory = ui_factory.get_component_factory()
        
        self.assertIsNotNone(component_factory)
        self.assertIsInstance(component_factory, IComponentFactory)
        
        # 测试注册和创建组件
        def dummy_component_factory(config: Optional[Dict[str, Any]] = None) -> QWidget:
            """测试用的虚拟组件工厂"""
            from PySide6.QtWidgets import QLabel
            widget = QLabel("Dummy Component")
            widget.setObjectName("test_component")
            if config and "text" in config:
                widget.setText(str(config["text"]))
            return widget

        component_factory.register_component_type("test", dummy_component_factory)
        self.assertIn("test", component_factory.get_registered_types())
        
        component = component_factory.create_component("test")
        self.assertIsInstance(component, QWidget)
        self.assertEqual(component.objectName(), "test_component")


if __name__ == "__main__":
    unittest.main()