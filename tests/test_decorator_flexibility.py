"""
测试装饰器系统的灵活性 - 验证非@Component/@Plugin标记的类可以使用@Inject和事件装饰器
"""

import pytest
from LStartlet import (
    Inject,
    Event,
    OnEvent,
    publish_event,
    get_di_container,
    get_event_bus,
)


class TestService:
    """测试服务类 - 未被@Component标记"""

    def do_something(self):
        return "test service working"


class RegularClass:
    """普通类 - 未被@Component标记，但使用@Inject"""

    def __init__(self, test_service: TestService = Inject()):
        self.test_service = test_service

    @OnEvent(Event)
    def handle_event(self, event: Event):
        """事件处理器 - 在普通类中使用@OnEvent"""
        self.received_event = event


def test_resolve_regular_class_with_inject():
    """测试通过DI容器解析普通类（使用@Inject）"""
    # 首先注册TestService到DI容器
    di_container = get_di_container()
    di_container.register_service(TestService, TestService, singleton=True)

    # 注册RegularClass到DI容器
    di_container.register_service(RegularClass, RegularClass, singleton=False)

    # 通过DI容器解析RegularClass实例，应该能正常注入依赖
    regular_instance = di_container.resolve(RegularClass)

    # 验证依赖注入成功
    assert regular_instance.test_service is not None
    assert regular_instance.test_service.do_something() == "test service working"


def test_on_event_in_regular_class():
    """测试在普通类中使用@OnEvent装饰器"""
    # 清理之前的事件处理器
    event_bus = get_event_bus()
    event_bus._handlers.clear()
    event_bus._single_handlers.clear()

    # 创建实例，装饰器应该已经注册了事件处理器
    regular_instance = RegularClass()

    # 手动重新注册绑定后的实例方法（推荐做法）
    from LStartlet import subscribe_event

    subscribe_event(Event, regular_instance.handle_event)

    # 发布事件
    test_event = Event()
    publish_event(test_event)

    # 验证事件处理器被调用
    assert hasattr(regular_instance, "received_event")
    assert regular_instance.received_event is test_event


def test_standalone_function_with_on_event():
    """测试顶层函数使用@OnEvent装饰器"""
    event_bus = get_event_bus()
    event_bus._handlers.clear()

    received_events = []

    @OnEvent(Event)
    def standalone_handler(event: Event):
        received_events.append(event)

    # 发布事件
    test_event = Event()
    publish_event(test_event)

    # 验证顶层函数处理器被调用
    assert len(received_events) == 1
    assert received_events[0] is test_event


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
