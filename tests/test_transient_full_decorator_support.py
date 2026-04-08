"""
验证瞬态实例对所有装饰器的完整支持
"""

import pytest
from LStartlet import Component, Inject, get_di_container
from LStartlet import (
    Init,
    Start,
    Stop,
    Destroy,
    PreInit,
    PostInit,
    PreStart,
    PostStart,
    PreStop,
    PostStop,
    PreDestroy,
    PostDestroy,
    OnDependenciesResolved,
    trigger_lifecycle_phase,
    LifecyclePhase,
    subscribe_event,
)
from LStartlet import (
    resolve_transient,
    start_transient_instance,
    stop_transient_instance,
)
from LStartlet import Event, OnEvent, publish_event


# 定义事件
class EventData(Event):
    def __init__(self, message: str):
        self.message = message


@Component
class FullFeatureTransientService:
    """支持所有装饰器特性的瞬态服务"""

    def __init__(self):
        self.events = []
        self.lifecycle_events = []
        # 手动注册事件处理器（推荐方式）
        subscribe_event(EventData, self.handle_test_event)

    # 细粒度生命周期装饰器
    @PreInit()
    def pre_init_hook(self):
        self.lifecycle_events.append("pre_init")

    @PostInit()
    def post_init_hook(self):
        self.lifecycle_events.append("post_init")

    @OnDependenciesResolved()
    def dependencies_resolved_hook(self):
        self.lifecycle_events.append("dependencies_resolved")

    @PreStart()
    def pre_start_hook(self):
        self.lifecycle_events.append("pre_start")

    @PostStart()
    def post_start_hook(self):
        self.lifecycle_events.append("post_start")

    @PreStop()
    def pre_stop_hook(self):
        self.lifecycle_events.append("pre_stop")

    @PostStop()
    def post_stop_hook(self):
        self.lifecycle_events.append("post_stop")

    @PreDestroy()
    def pre_destroy_hook(self):
        self.lifecycle_events.append("pre_destroy")

    @PostDestroy()
    def post_destroy_hook(self):
        self.lifecycle_events.append("post_destroy")

    # 简化版生命周期装饰器
    @Init()
    def init_method(self):
        self.lifecycle_events.append("init")

    @Start()
    def start_method(self):
        self.lifecycle_events.append("start")

    @Stop()
    def stop_method(self):
        self.lifecycle_events.append("stop")

    @Destroy()
    def destroy_method(self):
        self.lifecycle_events.append("destroy")

    # 事件处理器（现在作为普通方法，不使用@OnEvent装饰器）
    def handle_test_event(self, event: EventData):
        self.events.append(event.message)


def test_transient_auto_triggered_lifecycle():
    """测试瞬态实例自动触发的生命周期阶段"""
    # 创建瞬态实例（自动触发初始化相关阶段）
    instance = resolve_transient(FullFeatureTransientService)

    # 验证自动触发的阶段（根据改进后的LStartlet规范，PRE_INIT和POST_INIT都自动触发）
    expected_auto_phases = [
        "pre_init",  # @PreInit() -> PRE_INIT (新增)
        "init",  # @Init() -> POST_INIT
        "post_init",  # @PostInit()
        "dependencies_resolved",  # @OnDependenciesResolved()
    ]

    for phase in expected_auto_phases:
        assert phase in instance.lifecycle_events

    # 验证所有预期阶段都被触发
    assert len(instance.lifecycle_events) >= len(expected_auto_phases)


def test_transient_manual_lifecycle_control():
    """测试瞬态实例的手动生命周期控制"""
    instance = resolve_transient(FullFeatureTransientService)

    # 手动触发PRE_INIT（虽然通常不需要，但技术上可行）
    trigger_lifecycle_phase(instance, LifecyclePhase.PRE_INIT)
    assert "pre_init" in instance.lifecycle_events

    # 手动触发启动阶段
    start_transient_instance(instance)
    expected_start_phases = ["pre_start", "start", "post_start"]
    for phase in expected_start_phases:
        assert phase in instance.lifecycle_events

    # 手动触发停止和销毁阶段
    stop_transient_instance(instance)
    expected_stop_phases = [
        "pre_stop",
        "stop",
        "post_stop",
        "pre_destroy",
        "destroy",
        "post_destroy",
    ]
    for phase in expected_stop_phases:
        assert phase in instance.lifecycle_events


def test_transient_event_support():
    """测试瞬态实例的事件处理支持"""
    instance = resolve_transient(FullFeatureTransientService)

    # 发布事件
    publish_event(EventData("hello from transient"))

    # 验证事件处理器被调用
    assert "hello from transient" in instance.events


def test_transient_vs_singleton_consistency():
    """比较瞬态实例和单例实例的装饰器行为一致性"""
    di_container = get_di_container()

    # 注册为单例
    di_container.register_service(
        FullFeatureTransientService, FullFeatureTransientService, singleton=True
    )

    # 获取单例实例
    singleton = di_container.resolve(FullFeatureTransientService)

    # 获取瞬态实例
    transient = resolve_transient(FullFeatureTransientService)

    # 验证两者都正确触发了相同的自动阶段
    auto_phases = ["init", "post_init", "dependencies_resolved"]

    for phase in auto_phases:
        assert phase in singleton.lifecycle_events
        assert phase in transient.lifecycle_events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
