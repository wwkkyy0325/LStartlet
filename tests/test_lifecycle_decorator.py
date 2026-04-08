"""
测试生命周期装饰器功能
"""

import pytest
from typing import Any
from LStartlet import Component, Plugin, PluginBase, Inject, get_di_container
from LStartlet import (
    PreInit,
    PostInit,
    PreStart,
    PostStart,
    PreExecute,
    PostExecute,
    PreStop,
    PostStop,
    PreDestroy,
    PostDestroy,
    OnConfigChange,
    OnDependenciesResolved,
    trigger_lifecycle_phase,
    LifecyclePhase,
    get_lifecycle_manager,
)


class MockDependency:
    """测试依赖服务"""

    def __init__(self):
        self.initialized = False
        self.started = False
        self.executed = False
        self.stopped = False
        self.destroyed = False


def cleanup_test_state():
    """清理测试状态"""
    # 清理DI容器
    di_container = get_di_container()
    di_container._services.clear()
    di_container._components.clear()
    di_container._plugins.clear()

    # 清理生命周期管理器
    lifecycle_manager = get_lifecycle_manager()
    lifecycle_manager._methods.clear()


@Component
class LifecycleTestService:
    """生命周期测试服务"""

    def __init__(self, test_dependency: MockDependency = Inject()):
        self.test_dependency = test_dependency
        self.lifecycle_events = []

    @PreInit(priority=1)
    def pre_init_high_priority(self):
        self.lifecycle_events.append("pre_init_high")

    @PreInit(priority=10)
    def pre_init_low_priority(self):
        self.lifecycle_events.append("pre_init_low")

    @PostInit()
    def post_init_with_condition(self):
        self.lifecycle_events.append("post_init")
        self.test_dependency.initialized = True

    @OnDependenciesResolved()
    def on_dependencies_resolved(self):
        self.lifecycle_events.append("dependencies_resolved")


@Plugin
class LifecycleTestPlugin(PluginBase):
    """生命周期测试插件"""

    def __init__(self):
        super().__init__()
        self.plugin_events = []

    def initialize(self) -> bool:
        return True

    def execute(self, **kwargs) -> Any:
        return None

    def cleanup(self) -> None:
        pass

    @PostInit()
    def plugin_post_init(self):
        self.plugin_events.append("plugin_post_init")


def test_lifecycle_method_registration():
    """测试生命周期方法注册"""
    cleanup_test_state()

    # 在测试函数内部定义类
    @Component
    class TestLifecycleService:
        def __init__(self):
            self.lifecycle_events = []

        @PreInit(priority=1)
        def pre_init_high_priority(self):
            self.lifecycle_events.append("pre_init_high")

        @PreInit(priority=10)
        def pre_init_low_priority(self):
            self.lifecycle_events.append("pre_init_low")

        @PostInit()
        def post_init_with_condition(self):
            self.lifecycle_events.append("post_init")

    lifecycle_manager = get_lifecycle_manager()
    methods = lifecycle_manager.get_methods(
        TestLifecycleService, LifecyclePhase.POST_INIT
    )
    assert len(methods) == 1
    assert methods[0].method.__name__ == "post_init_with_condition"

    # 验证优先级排序
    pre_init_methods = lifecycle_manager.get_methods(
        TestLifecycleService, LifecyclePhase.PRE_INIT
    )
    assert len(pre_init_methods) == 2
    assert pre_init_methods[0].priority == 1  # 高优先级先执行
    assert pre_init_methods[1].priority == 10


def test_automated_lifecycle_execution():
    """测试自动化的生命周期执行 - POST_INIT应自动触发"""
    cleanup_test_state()

    class MockDependency:
        def __init__(self):
            self.initialized = False

    @Component
    class TestLifecycleService:
        def __init__(self, test_dependency: MockDependency = Inject()):
            self.test_dependency = test_dependency
            self.lifecycle_events = []

        @OnDependenciesResolved()
        def on_dependencies_resolved(self):
            self.lifecycle_events.append("dependencies_resolved")

        @PostInit()
        def post_init_with_condition(self):
            self.lifecycle_events.append("post_init")
            self.test_dependency.initialized = True

    # 使用DI容器注册依赖
    di_container = get_di_container()
    di_container.register_service(MockDependency, MockDependency, singleton=True)

    # 通过DI容器创建实例，这样会自动触发ON_DEPENDENCIES_RESOLVED和POST_INIT
    instance = di_container.resolve(TestLifecycleService)

    # 验证ON_DEPENDENCIES_RESOLVED和POST_INIT都已自动触发
    assert "dependencies_resolved" in instance.lifecycle_events
    assert "post_init" in instance.lifecycle_events

    # 验证依赖已正确初始化
    assert instance.test_dependency.initialized


def test_simple_lifecycle_execution():
    """测试简化的生命周期装饰器"""
    cleanup_test_state()

    class MockDependency:
        def __init__(self):
            self.initialized = False

    from LStartlet import Init

    @Component
    class SimpleInitService:
        def __init__(self, dep: MockDependency = Inject()):
            self.dep = dep
            self.init_called = False

        @Init()
        def simple_init(self):
            self.init_called = True
            self.dep.initialized = True

    di_container = get_di_container()
    di_container.register_service(MockDependency, MockDependency, singleton=True)

    instance = di_container.resolve(SimpleInitService)
    assert instance.init_called
    assert instance.dep.initialized


def test_plugin_lifecycle():
    """测试插件生命周期"""
    cleanup_test_state()

    @Plugin
    class TestPlugin(PluginBase):
        def __init__(self):
            super().__init__()
            self.plugin_events = []

        def initialize(self) -> bool:
            return True

        def execute(self, **kwargs) -> Any:
            return None

        def cleanup(self) -> None:
            pass

        @PostInit()
        def plugin_post_init(self):
            self.plugin_events.append("plugin_post_init")

    instance = TestPlugin()

    trigger_lifecycle_phase(instance, LifecyclePhase.POST_INIT)
    # 使用hasattr检查动态属性
    assert hasattr(instance, "plugin_events")
    assert "plugin_post_init" in getattr(instance, "plugin_events", [])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
