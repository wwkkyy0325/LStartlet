"""
事件装饰器测试 - 验证@OnEvent功能
"""

import sys
from pathlib import Path
from dataclasses import dataclass

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import Event, OnEvent, Component, publish_event


@dataclass
class _TestEvent(Event):
    """测试事件"""

    message: str


@Component
class _TestEventHandler:
    """测试事件处理器"""

    def __init__(self):
        self.received_messages = []
        self.handler1_calls = []
        self.handler2_calls = []

        # 手动注册实例方法作为事件处理器
        from LStartlet._event_decorator import _event_bus

        _event_bus.subscribe(_TestEvent, self.handle_test_event)
        _event_bus.subscribe(_TestEvent, self.handler1)
        _event_bus.subscribe(_TestEvent, self.handler2)

    def handle_test_event(self, event: _TestEvent):
        self.received_messages.append(event.message)

    def handler1(self, event: _TestEvent):
        self.handler1_calls.append(f"h1:{event.message}")

    def handler2(self, event: _TestEvent):
        self.handler2_calls.append(f"h2:{event.message}")


def test_sync_event_handler():
    """测试同步事件处理器"""
    handler = _TestEventHandler()

    # 发布事件
    event1 = _TestEvent("hello")
    event2 = _TestEvent("world")

    publish_event(event1)
    publish_event(event2)

    assert len(handler.received_messages) == 2
    assert handler.received_messages[0] == "hello"
    assert handler.received_messages[1] == "world"


def test_multiple_handlers():
    """测试多个处理器"""
    handler = _TestEventHandler()

    event = _TestEvent("test")
    publish_event(event)

    assert len(handler.handler1_calls) == 1
    assert len(handler.handler2_calls) == 1
    assert handler.handler1_calls[0] == "h1:test"
    assert handler.handler2_calls[0] == "h2:test"
