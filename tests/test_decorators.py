import pytest
from LStartlet import Component, Plugin, ComponentRegistry, set_project_root, PluginBase
import os
import tempfile


@pytest.fixture(autouse=True)
def setup_test_env():
    """为每个测试设置临时项目根目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_root = set_project_root(temp_dir)
        yield temp_dir
        if original_root:
            set_project_root(original_root)


@pytest.mark.decorator
class TestComponentDecorator:
    """测试Component装饰器"""

    def test_component_basic_usage(self):
        """测试基本的Component装饰器用法"""

        @Component
        class TestService:
            def __init__(self):
                self.value = "test"

        # 验证组件被正确注册
        assert "TestService" in ComponentRegistry._components
        assert ComponentRegistry._components["TestService"].__name__ == "TestService"

    def test_component_with_name(self):
        """测试带名称的Component装饰器"""

        @Component("CustomName")
        class TestService:
            pass

        assert "CustomName" in ComponentRegistry._components
        assert ComponentRegistry._components["CustomName"].__name__ == "TestService"


@pytest.mark.decorator
class TestPluginDecorator:
    """测试Plugin装饰器"""

    def test_plugin_basic_usage(self):
        """测试基本的Plugin装饰器用法"""

        @Plugin
        class TestPlugin(PluginBase):
            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "plugin executed"

            def cleanup(self) -> None:
                pass

        # 验证插件被正确注册
        assert "TestPlugin" in ComponentRegistry._plugins
        assert ComponentRegistry._plugins["TestPlugin"].__name__ == "TestPlugin"

    def test_plugin_with_name(self):
        """测试带名称的Plugin装饰器"""

        @Plugin("CustomPlugin")
        class TestPlugin(PluginBase):
            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "custom plugin executed"

            def cleanup(self) -> None:
                pass

        assert "CustomPlugin" in ComponentRegistry._plugins
        assert ComponentRegistry._plugins["CustomPlugin"].__name__ == "TestPlugin"


@pytest.mark.decorator
class TestComponentRegistry:
    """测试ComponentRegistry功能"""

    def test_registry_class_methods(self):
        """测试ComponentRegistry使用类方法而不是实例"""
        # ComponentRegistry应该通过类方法访问，而不是实例
        registry = ComponentRegistry()
        # 验证类属性和实例属性指向相同的数据
        assert registry._components is ComponentRegistry._components
        assert registry._plugins is ComponentRegistry._plugins

    def test_clear_registry(self):
        """测试清空注册表"""

        @Component
        class TempService:
            pass

        @Plugin
        class TempPlugin(PluginBase):
            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "temp plugin"

            def cleanup(self) -> None:
                pass

        assert len(ComponentRegistry._components) > 0
        assert len(ComponentRegistry._plugins) > 0

        # 清空注册表
        ComponentRegistry.clear()
        assert len(ComponentRegistry._components) == 0
        assert len(ComponentRegistry._plugins) == 0
