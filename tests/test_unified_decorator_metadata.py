"""
测试统一的装饰器元数据结构
"""

import pytest
from LStartlet import Component, get_di_container
from LStartlet import Init, Start, Stop, Destroy
from LStartlet import Event, OnEvent, OnSingleEvent, EventInterceptor
from LStartlet import (
    resolve_transient,
    start_transient_instance,
    stop_transient_instance,
)
from LStartlet import publish_event


class EventData(Event):
    """测试事件数据"""

    def __init__(self, message: str):
        self.message = message


@Component
class UnifiedMetadataService:
    """用于测试统一元数据结构的服务"""

    def __init__(self):
        self.lifecycle_events = []
        self.event_messages = []

    # 生命周期方法
    @Init(condition=lambda self: True, priority=10, enabled=True)
    def init_with_metadata(self):
        self.lifecycle_events.append("init_with_metadata")

    @Start(priority=5)
    def start_with_metadata(self):
        self.lifecycle_events.append("start_with_metadata")

    @Stop(enabled=False)  # 禁用的方法
    def disabled_stop(self):
        self.lifecycle_events.append("disabled_stop")

    @Destroy()
    def destroy_default(self):
        self.lifecycle_events.append("destroy_default")

    # 事件处理器
    @OnEvent(EventData, condition=lambda e: "good" in e.message)
    def handle_good_events(self, event: EventData):
        self.event_messages.append(f"good: {event.message}")

    @OnSingleEvent(EventData)
    def handle_single_events(self, event: EventData):
        self.event_messages.append(f"single: {event.message}")

    @EventInterceptor(EventData)
    def intercept_test_events(self, event: EventData):
        # 拦截器不阻止传播
        self.event_messages.append(f"intercepted: {event.message}")
        return True


def test_lifecycle_metadata_structure():
    """测试生命周期装饰器的统一元数据结构"""
    instance = resolve_transient(UnifiedMetadataService)

    # 检查Init方法的元数据
    init_method = getattr(UnifiedMetadataService, "init_with_metadata")
    metadata_list = getattr(init_method, "_lifecycle_metadata", [])

    assert len(metadata_list) == 1
    metadata = metadata_list[0]

    # 验证统一的元数据结构
    assert "phase" in metadata
    assert "condition" in metadata
    assert "priority" in metadata
    assert "enabled" in metadata

    assert metadata["phase"].value == "post_init"
    assert metadata["priority"] == 10
    assert metadata["enabled"] == True

    # 检查默认值
    destroy_method = getattr(UnifiedMetadataService, "destroy_default")
    destroy_metadata = getattr(destroy_method, "_lifecycle_metadata", [])[0]

    assert destroy_metadata["condition"] is None
    assert destroy_metadata["priority"] == 0
    assert destroy_metadata["enabled"] == True


def test_event_metadata_structure():
    """测试事件装饰器的统一元数据结构"""
    instance = resolve_transient(UnifiedMetadataService)

    # 检查OnEvent方法的元数据
    on_event_method = getattr(UnifiedMetadataService, "handle_good_events")
    event_metadata_list = getattr(on_event_method, "_event_metadata", [])

    assert len(event_metadata_list) == 1
    event_metadata = event_metadata_list[0]

    # 验证统一的事件元数据结构
    assert "event_type" in event_metadata
    assert "condition" in event_metadata
    assert "topic" in event_metadata
    assert "handler_type" in event_metadata

    assert event_metadata["event_type"] == EventData
    assert event_metadata["handler_type"] == "multi"

    # 检查OnSingleEvent方法的元数据
    single_event_method = getattr(UnifiedMetadataService, "handle_single_events")
    single_metadata = getattr(single_event_method, "_event_metadata", [])[0]

    assert single_metadata["handler_type"] == "single"

    # 检查EventInterceptor方法的元数据
    interceptor_method = getattr(UnifiedMetadataService, "intercept_test_events")
    interceptor_metadata = getattr(interceptor_method, "_event_metadata", [])[0]

    assert interceptor_metadata["handler_type"] == "interceptor"


def test_functional_behavior_with_unified_metadata():
    """测试使用统一元数据结构的功能行为"""
    instance = resolve_transient(UnifiedMetadataService)

    # 验证生命周期方法正确执行（只验证Init）
    assert "init_with_metadata" in instance.lifecycle_events
    assert "destroy_default" not in instance.lifecycle_events  # Destroy在stop时才调用

    # 验证禁用的方法没有执行
    assert "disabled_stop" not in instance.lifecycle_events

    # 触发启动
    start_transient_instance(instance)
    assert "start_with_metadata" in instance.lifecycle_events

    # 测试事件处理
    publish_event(EventData("good message"))
    publish_event(EventData("bad message"))

    # 验证事件处理器正确工作
    assert "good: good message" in instance.event_messages
    assert "single: good message" in instance.event_messages
    assert "intercepted: good message" in instance.event_messages
    assert "intercepted: bad message" in instance.event_messages

    # 触发停止和销毁
    stop_transient_instance(instance)
    assert "destroy_default" in instance.lifecycle_events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
