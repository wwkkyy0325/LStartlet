"""测试统一装饰器系统"""

import unittest
from abc import ABC, abstractmethod
from typing import Type

from LStartlet import register_service, register_plugin, register_command, ServiceLifetime
from LStartlet.core.di import get_default_container
from LStartlet.plugin.base.plugin_base import PluginBase
from LStartlet.core.command.command_base import BaseCommand, CommandResult, CommandMetadata
from LStartlet.core.command.command_registry import command_registry


class TestUnifiedDecorators(unittest.TestCase):
    """统一装饰器测试类"""
    
    def setUp(self) -> None:
        """测试前清理"""
        # 清理服务容器
        container = get_default_container()
        container._services.clear()
        container._singleton_instances.clear()
        
        # 清理命令注册表
        command_registry._commands.clear()

    def test_service_decorator_basic(self):
        """测试基本的服务装饰器"""
        
        @register_service()
        class TestService:
            def do_work(self) -> str:
                return "work done"
        
        container = get_default_container()
        service = container.resolve(TestService)
        self.assertIsInstance(service, TestService)
        self.assertEqual(service.do_work(), "work done")

    def test_service_decorator_with_interface(self):
        """测试带接口的服务装饰器"""
        
        class IService:
            def process(self) -> str:
                pass
        
        @register_service(service_type=IService)
        class ConcreteService(IService):
            def process(self) -> str:
                return "processed"
        
        container = get_default_container()
        service = container.resolve(IService)
        self.assertIsInstance(service, ConcreteService)
        self.assertEqual(service.process(), "processed")

    def test_plugin_decorator_basic(self):
        """测试基本的插件装饰器"""
        @register_plugin(
            plugin_id="test.plugin.basic",
            name="Basic Test Plugin",
            version="1.0.0"
        )
        class BasicTestPlugin(PluginBase):
            def __init__(self):
                # 使用装饰器设置的元数据
                metadata = self.__class__._plugin_metadata
                super().__init__(
                    plugin_id=metadata['plugin_id'],
                    name=metadata['name'], 
                    version=metadata['version'],
                    description=metadata['description']
                )
                
            def initialize(self) -> bool:
                return True
                
            def start(self) -> bool:
                return True
                
            def stop(self) -> bool:
                return True
                
            def cleanup(self) -> bool:
                return True

        # 验证插件元数据被正确设置
        self.assertTrue(hasattr(BasicTestPlugin, '_plugin_metadata'))
        metadata = BasicTestPlugin._plugin_metadata
        self.assertEqual(metadata['plugin_id'], "test.plugin.basic")
        self.assertEqual(metadata['name'], "Basic Test Plugin")
        self.assertEqual(metadata['version'], "1.0.0")
        
        # 验证插件被注册为服务
        container = get_default_container()
        instance = container.resolve(BasicTestPlugin)
        self.assertIsInstance(instance, BasicTestPlugin)
        self.assertEqual(instance.plugin_id, "test.plugin.basic")

    def test_plugin_decorator_with_options(self):
        """测试带选项的插件装饰器"""
        
        @register_plugin(
            plugin_id="custom.plugin",
            name="Custom Plugin",
            version="2.0.0",
            description="Custom plugin with options",
            order=10,
            dependencies={"core.logger": ">=1.0.0"}
        )
        class CustomPlugin(PluginBase):
            def __init__(self):
                super().__init__(
                    plugin_id="custom.plugin",
                    name="Custom Plugin",
                    version="2.0.0",
                    description="Custom plugin with options"
                )
            
            def initialize(self) -> None: pass
            def start(self) -> None: pass
            def stop(self) -> None: pass
            def cleanup(self) -> None: pass
        
        container = get_default_container()
        plugin = container.resolve(CustomPlugin)
        self.assertIsInstance(plugin, CustomPlugin)

    def test_cmd_decorator_basic(self):
        """测试基本的命令装饰器"""
        @register_command(name="test")
        class TestCommand(BaseCommand):
            def __init__(self):
                super().__init__(self._command_metadata)
                
            def execute(self, **kwargs) -> CommandResult:
                return CommandResult(is_success=True, data="executed")

        # 验证命令已注册
        cmd = command_registry.get_command("test")
        self.assertIsNotNone(cmd)
        self.assertIsInstance(cmd, TestCommand)
        self.assertEqual(cmd.metadata.name, "test")

    def test_cmd_decorator_with_options(self):
        """测试带选项的命令装饰器"""
        @register_command(
            name="custom_cmd",
            description="A custom command",
            category="test",
            timeout=5.0
        )
        class CustomCommand(BaseCommand):
            def __init__(self):
                super().__init__(self._command_metadata)
                
            def execute(self, **kwargs) -> CommandResult:
                return CommandResult(is_success=True, data="custom executed")

        # 验证命令已注册且元数据正确
        cmd = command_registry.get_command("custom_cmd")
        self.assertIsNotNone(cmd)
        self.assertIsInstance(cmd, CustomCommand)
        self.assertEqual(cmd.metadata.description, "A custom command")
        self.assertEqual(cmd.metadata.category, "test")
        self.assertEqual(cmd.metadata.timeout, 5.0)

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 测试旧装饰器名称仍然可用（通过别名）
        from LStartlet.core.decorators import auto_register, auto_plugin_register, command as register_command_decorator
        
        class TestService:
            pass
            
        class ITestPlugin(ABC):
            @abstractmethod
            def do_something(self) -> bool:
                pass
                
        class TestPlugin(PluginBase, ITestPlugin):
            def __init__(self):
                super().__init__("test.plugin", "Test Plugin", "1.0.0")
                
            def do_something(self) -> bool:
                return True
                
            def initialize(self) -> bool:
                return True
                
            def start(self) -> bool:
                return True
                
            def stop(self) -> bool:
                return True
                
            def cleanup(self) -> bool:
                return True
                
        class TestCommand(BaseCommand):
            def __init__(self):
                super().__init__(CommandMetadata(name="test_cmd", description="Test command"))
                
            def execute(self, **kwargs) -> CommandResult:
                return CommandResult(is_success=True, data="test")
        
        # 测试旧装饰器仍然可用
        decorated_service = auto_register()(TestService)
        self.assertIsNotNone(decorated_service)
        
        decorated_plugin = auto_plugin_register(
            plugin_id="test.plugin",
            name="Test Plugin", 
            version="1.0.0"
        )(TestPlugin)
        self.assertIsNotNone(decorated_plugin)
        
        decorated_command = register_command_decorator(name="test_cmd")(TestCommand)
        self.assertIsNotNone(decorated_command)

if __name__ == '__main__':
    unittest.main()