#!/usr/bin/env python3
"""
测试简化的生命周期装饰器功能
"""

import pytest
from typing import Any
from LStartlet import Component, Plugin, PluginBase, Inject, get_di_container
from LStartlet import (
    Init,
    Start,
    Stop,
    Destroy,
    PostInit,  # 添加PostInit导入
    trigger_lifecycle_phase,
    LifecyclePhase,
    get_lifecycle_manager,
    start_framework,
    stop_framework,  # 添加缺失的导入
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


def test_automated_simple_lifecycle_basic():
    """测试简化的生命周期自动初始化功能 - Init应自动触发"""
    cleanup_test_state()

    class MockDependency:
        def __init__(self):
            self.initialized = False

    @Component
    class TestSimpleLifecycleService:
        def __init__(self, test_dependency: MockDependency = Inject()):
            self.test_dependency = test_dependency
            self.events = []

        @Init()
        def simple_init(self):
            self.events.append("simple_init")
            self.test_dependency.initialized = True

    # 使用DI容器注册依赖
    di_container = get_di_container()
    di_container.register_service(MockDependency, MockDependency, singleton=True)

    # 创建实例 - Init应该自动触发
    instance = di_container.resolve(TestSimpleLifecycleService)

    # 验证Init已自动触发
    assert "simple_init" in instance.events
    assert instance.test_dependency.initialized


def test_framework_lifecycle_management():
    """测试框架级别的生命周期管理"""
    cleanup_test_state()

    class MockDependency:
        def __init__(self):
            self.initialized = False
            self.started = False
            self.stopped = False
            self.destroyed = False

    @Component
    class TestSimpleLifecycleService:
        def __init__(self, test_dependency: MockDependency = Inject()):
            self.test_dependency = test_dependency
            self.events = []

        @Init()
        def simple_init(self):
            self.events.append("simple_init")
            self.test_dependency.initialized = True

        @Start()
        def simple_start(self):
            self.events.append("simple_start")
            self.test_dependency.started = True

        @Stop()
        def simple_stop(self):
            self.events.append("simple_stop")
            self.test_dependency.stopped = True

        @Destroy()
        def simple_destroy(self):
            self.events.append("simple_destroy")
            self.test_dependency.destroyed = True

    # 使用DI容器注册依赖
    di_container = get_di_container()
    di_container.register_service(MockDependency, MockDependency, singleton=True)

    # 创建实例 - Init自动触发
    instance = di_container.resolve(TestSimpleLifecycleService)
    assert "simple_init" in instance.events
    instance.events.clear()

    # 启动框架 - 触发Start
    start_framework()
    assert "simple_start" in instance.events
    instance.events.clear()

    # 停止框架 - 触发Stop和Destroy
    stop_framework()
    assert "simple_stop" in instance.events
    assert "simple_destroy" in instance.events


def test_simple_lifecycle_priority():
    """测试简化的生命周期优先级"""
    cleanup_test_state()

    @Component
    class TestPrioritySimpleService:
        def __init__(self):
            self.events = []

        @Init(priority=1)
        def high_priority_init(self):
            self.events.append("high_priority_init")

        @Init(priority=10)
        def low_priority_init(self):
            self.events.append("low_priority_init")

        @Start(priority=1)
        def high_priority_start(self):
            self.events.append("high_priority_start")

        @Start(priority=10)
        def low_priority_start(self):
            self.events.append("low_priority_start")

    di_container = get_di_container()

    instance = di_container.resolve(TestPrioritySimpleService)

    # 验证Init优先级（高优先级先执行）
    assert instance.events == ["high_priority_init", "low_priority_init"]
    instance.events.clear()

    # 手动触发Start阶段
    trigger_lifecycle_phase(instance, LifecyclePhase.POST_START)
    # 验证Start优先级
    assert instance.events == ["high_priority_start", "low_priority_start"]


def test_simple_lifecycle_plugin():
    """测试简化的插件生命周期"""
    cleanup_test_state()

    @Plugin
    class TestSimpleLifecyclePlugin(PluginBase):
        def __init__(self):
            super().__init__()
            self.plugin_events = []

        def initialize(self) -> bool:
            return True

        def execute(self, **kwargs) -> Any:
            return None

        def cleanup(self) -> None:
            pass

        @Init()
        def plugin_init(self):
            self.plugin_events.append("plugin_init")

        @Start()
        def plugin_start(self):
            self.plugin_events.append("plugin_start")

        @Stop()
        def plugin_stop(self):
            self.plugin_events.append("plugin_stop")

        @Destroy()
        def plugin_destroy(self):
            self.plugin_events.append("plugin_destroy")

    instance = TestSimpleLifecyclePlugin()

    trigger_lifecycle_phase(instance, LifecyclePhase.POST_INIT)
    trigger_lifecycle_phase(instance, LifecyclePhase.POST_START)
    trigger_lifecycle_phase(instance, LifecyclePhase.PRE_STOP)
    trigger_lifecycle_phase(instance, LifecyclePhase.POST_DESTROY)

    # 使用hasattr/getattr处理动态属性
    assert hasattr(instance, "plugin_events")
    plugin_events = getattr(instance, "plugin_events", [])
    expected_events = ["plugin_init", "plugin_start", "plugin_stop", "plugin_destroy"]
    assert plugin_events == expected_events


def test_simple_vs_detailed_lifecycle_equivalence():
    """测试简化生命周期与详细生命周期的等价性"""
    cleanup_test_state()

    class MockDependency:
        def __init__(self):
            self.initialized = False

    @Component
    class TestDetailedService:
        def __init__(self, dep: MockDependency = Inject()):
            self.dep = dep
            self.events = []

        @PostInit()
        def detailed_init(self):
            self.events.append("detailed_init")
            self.dep.initialized = True

    @Component
    class TestSimpleService:
        def __init__(self, dep: MockDependency = Inject()):
            self.dep = dep
            self.events = []

        @Init()
        def simple_init(self):
            self.events.append("simple_init")
            self.dep.initialized = True

    di_container = get_di_container()
    di_container.register_service(MockDependency, MockDependency, singleton=True)

    # 详细生命周期服务
    detailed_instance = di_container.resolve(TestDetailedService)
    detailed_events = set(detailed_instance.events)

    # 简化生命周期服务
    simple_instance = di_container.resolve(TestSimpleService)
    simple_events = set(simple_instance.events)

    # 验证核心事件存在
    assert "detailed_init" in detailed_events
    assert "simple_init" in simple_events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
