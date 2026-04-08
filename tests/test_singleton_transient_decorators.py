"""
测试Component和Plugin装饰器的singleton参数支持
"""

import pytest
from LStartlet import Component, Plugin, get_di_container, PluginBase


def test_component_singleton_behavior():
    """测试组件的单例行为"""

    @Component
    class DefaultSingletonComponent:
        """默认单例组件"""

        def __init__(self):
            self.value = "singleton"

    @Component(singleton=True)
    class ExplicitSingletonComponent:
        """显式单例组件"""

        def __init__(self):
            self.value = "explicit_singleton"

    @Component(singleton=False)
    class TransientComponent:
        """瞬态组件"""

        def __init__(self):
            self.value = "transient"

    di_container = get_di_container()

    # 默认单例组件
    instance1 = di_container.resolve(DefaultSingletonComponent)
    instance2 = di_container.resolve(DefaultSingletonComponent)
    assert instance1 is instance2
    assert instance1.value == "singleton"

    # 显式单例组件
    instance3 = di_container.resolve(ExplicitSingletonComponent)
    instance4 = di_container.resolve(ExplicitSingletonComponent)
    assert instance3 is instance4
    assert instance3.value == "explicit_singleton"

    # 瞬态组件
    instance5 = di_container.resolve(TransientComponent)
    instance6 = di_container.resolve(TransientComponent)
    assert instance5 is not instance6  # 不同实例
    assert instance5.value == "transient"
    assert instance6.value == "transient"


def test_component_named_registration():
    """测试组件的命名注册"""

    @Component("named_singleton", singleton=True)
    class NamedSingletonComponent:
        """命名单例组件"""

        def __init__(self):
            self.value = "named_singleton"

    @Component("named_transient", singleton=False)
    class NamedTransientComponent:
        """命名瞬态组件"""

        def __init__(self):
            self.value = "named_transient"

    di_container = get_di_container()

    # 命名单例组件 - 通过组件名称获取类型，然后解析
    singleton_type = di_container._components["named_singleton"]
    instance1 = di_container.resolve(singleton_type)
    instance2 = di_container.resolve(singleton_type)
    assert instance1 is instance2
    assert instance1.value == "named_singleton"

    # 命名瞬态组件
    transient_type = di_container._components["named_transient"]
    instance3 = di_container.resolve(transient_type)
    instance4 = di_container.resolve(transient_type)
    assert instance3 is not instance4  # 不同实例
    assert instance3.value == "named_transient"
    assert instance4.value == "named_transient"


def test_plugin_singleton_behavior():
    """测试插件的单例行为"""

    class TestPlugin(PluginBase):
        """测试插件基类"""

        def initialize(self):
            """初始化插件"""
            return True

        def execute(self, **kwargs):
            """执行插件逻辑"""
            pass

        def cleanup(self):
            """清理插件资源"""
            pass

    @Plugin
    class DefaultSingletonPlugin(TestPlugin):
        """默认单例插件"""

        def __init__(self):
            super().__init__()
            self.value = "plugin_singleton"

    @Plugin(singleton=False)
    class TransientPlugin(TestPlugin):
        """瞬态插件"""

        def __init__(self):
            super().__init__()
            self.value = "plugin_transient"

    di_container = get_di_container()

    # 默认单例插件
    instance1 = di_container.resolve(DefaultSingletonPlugin)
    instance2 = di_container.resolve(DefaultSingletonPlugin)
    assert instance1 is instance2
    assert instance1.value == "plugin_singleton"

    # 瞬态插件
    instance3 = di_container.resolve(TransientPlugin)
    instance4 = di_container.resolve(TransientPlugin)
    assert instance3 is not instance4  # 不同实例
    assert instance3.value == "plugin_transient"
    assert instance4.value == "plugin_transient"


def test_metadata_contains_singleton_info():
    """测试元数据包含singleton信息"""

    @Component(singleton=True)
    class SingletonComponent:
        pass

    @Component(singleton=False)
    class TransientComp:
        pass

    class TestPlugin(PluginBase):
        def initialize(self):
            return True

        def execute(self, **kwargs):
            """执行插件逻辑"""
            pass

        def cleanup(self):
            pass

    @Plugin(singleton=True)
    class SingletonPlugin(TestPlugin):
        pass

    @Plugin(singleton=False)
    class TransientPlug(TestPlugin):
        pass

    # 组件元数据
    assert hasattr(SingletonComponent, "_component_metadata")
    assert getattr(SingletonComponent, "_component_metadata")["singleton"] is True

    assert hasattr(TransientComp, "_component_metadata")
    assert getattr(TransientComp, "_component_metadata")["singleton"] is False

    # 插件元数据
    assert hasattr(SingletonPlugin, "_component_metadata")
    assert getattr(SingletonPlugin, "_component_metadata")["singleton"] is True

    assert hasattr(TransientPlug, "_component_metadata")
    assert getattr(TransientPlug, "_component_metadata")["singleton"] is False


def test_resolve_transient_vs_singleton():
    """测试resolve_transient与singleton设置的关系"""
    from LStartlet import resolve_transient

    @Component(singleton=True)
    class SingletonService:
        def __init__(self):
            self.id = id(self)

    @Component(singleton=False)
    class TransientService:
        def __init__(self):
            self.id = id(self)

    # 即使组件注册为单例，resolve_transient也应该创建新实例
    instance1 = resolve_transient(SingletonService)
    instance2 = resolve_transient(SingletonService)
    assert instance1 is not instance2

    # 瞬态组件使用resolve_transient也创建新实例
    instance3 = resolve_transient(TransientService)
    instance4 = resolve_transient(TransientService)
    assert instance3 is not instance4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
