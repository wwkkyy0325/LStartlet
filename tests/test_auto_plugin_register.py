"""测试自动插件注册装饰器的功能"""

import unittest
from typing import Type, Dict, Any

from LStartlet.core.decorators import auto_plugin_register
from LStartlet.core.di import get_default_container, ServiceLifetime
from LStartlet.plugin.base.plugin_base import PluginBase


class TestAutoPluginRegister(unittest.TestCase):
    """测试自动插件注册装饰器"""

    def setUp(self):
        """测试前清理默认容器"""
        container = get_default_container()
        container._services.clear()
        container._singleton_instances.clear()

    def test_auto_plugin_register_basic(self):
        """测试基本的插件自动注册"""
        
        @auto_plugin_register(
            plugin_id="test.basic",
            name="Basic Plugin",
            version="1.0.0",
            description="A basic test plugin"
        )
        class BasicTestPlugin(PluginBase):
            def __init__(self):
                super().__init__(
                    plugin_id="test.basic",
                    name="Basic Plugin",
                    version="1.0.0",
                    description="A basic test plugin"
                )
            
            def initialize(self) -> None:
                pass
            
            def start(self) -> None:
                pass
            
            def stop(self) -> None:
                pass
            
            def cleanup(self) -> None:
                pass

        # 验证插件可以被解析
        container = get_default_container()
        plugin = container.resolve(BasicTestPlugin)
        
        self.assertIsInstance(plugin, BasicTestPlugin)
        self.assertEqual(plugin.plugin_id, "test.basic")
        self.assertEqual(plugin.name, "Basic Plugin")
        self.assertEqual(plugin.version, "1.0.0")
        self.assertEqual(plugin.description, "A basic test plugin")

    def test_auto_plugin_register_with_dependencies(self):
        """测试带依赖的插件自动注册"""
        
        @auto_plugin_register(
            plugin_id="test.dependent",
            name="Dependent Plugin",
            version="2.0.0",
            dependencies={"core.logger": ">=1.0.0", "core.config": ">=2.0.0"},
            order=5
        )
        class DependentTestPlugin(PluginBase):
            def __init__(self):
                super().__init__(
                    plugin_id="test.dependent",
                    name="Dependent Plugin",
                    version="2.0.0"
                )
            
            def initialize(self) -> None:
                pass
            
            def start(self) -> None:
                pass
            
            def stop(self) -> None:
                pass
            
            def cleanup(self) -> None:
                pass

        container = get_default_container()
        plugin = container.resolve(DependentTestPlugin)
        
        self.assertIsInstance(plugin, DependentTestPlugin)
        self.assertEqual(plugin.plugin_id, "test.dependent")
        # 注意：依赖信息存储在 PLUGIN_DEPENDENCIES 类属性中
        self.assertEqual(DependentTestPlugin.PLUGIN_DEPENDENCIES, {"core.logger": ">=1.0.0", "core.config": ">=2.0.0"})

    def test_auto_plugin_register_custom_lifetime(self):
        """测试自定义生命周期"""
        
        @auto_plugin_register(lifetime=ServiceLifetime.TRANSIENT)
        class TransientPlugin(PluginBase):
            def __init__(self):
                super().__init__(
                    plugin_id="test.transient",
                    name="Transient Plugin",
                    version="1.0.0"
                )
            
            def initialize(self) -> None:
                pass
            
            def start(self) -> None:
                pass
            
            def stop(self) -> None:
                pass
            
            def cleanup(self) -> None:
                pass

        container = get_default_container()
        plugin1 = container.resolve(TransientPlugin)
        plugin2 = container.resolve(TransientPlugin)
        
        # TRANSIENT 生命周期应该创建不同的实例
        self.assertIsNot(plugin1, plugin2)

    def test_auto_plugin_register_singleton_default(self):
        """测试默认单例生命周期"""
        
        @auto_plugin_register()
        class SingletonPlugin(PluginBase):
            def __init__(self):
                super().__init__(
                    plugin_id="test.singleton",
                    name="Singleton Plugin",
                    version="1.0.0"
                )
            
            def initialize(self) -> None:
                pass
            
            def start(self) -> None:
                pass
            
            def stop(self) -> None:
                pass
            
            def cleanup(self) -> None:
                pass

        container = get_default_container()
        plugin1 = container.resolve(SingletonPlugin)
        plugin2 = container.resolve(SingletonPlugin)
        
        # 默认应该是单例
        self.assertIs(plugin1, plugin2)

    def test_auto_plugin_register_validation_error(self):
        """测试非插件基类的注册错误"""
        
        with self.assertRaises(TypeError):
            @auto_plugin_register()
            class NonPluginClass:
                pass


if __name__ == "__main__":
    unittest.main()