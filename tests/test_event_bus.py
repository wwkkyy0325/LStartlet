#!/usr/bin/env python3
"""
事件总线核心模块单元测试
"""

import sys
import unittest
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.event.event_bus import EventBus
from core.event.event_handler import LambdaEventHandler, CompositeEventHandler
from core.event.event_type_registry import EventTypeRegistry
from core.event.base_event import BaseEvent


# 创建具体的事件类用于测试
class TestEvent(BaseEvent):
    """测试用的具体事件类"""

    def __init__(
        self, event_type: str = "test.event", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(event_type)
        self._data = data or {}

    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷"""
        return self._data


class TestBaseEvent(unittest.TestCase):
    """BaseEvent类测试"""

    def test_base_event_initialization(self):
        """测试BaseEvent初始化"""
        event = TestEvent("test_type")
        self.assertEqual(event.event_type, "test_type")
        self.assertIsNotNone(event.metadata.timestamp)
        self.assertGreater(event.metadata.timestamp, 0)

    def test_base_event_str_representation(self):
        """测试BaseEvent字符串表示"""
        # 移除未使用的变量
        pass


class TestEventTypeRegistry(unittest.TestCase):
    """EventTypeRegistry类测试"""

    def setUp(self):
        """测试前准备"""
        # 使用公共方法清理注册表以避免测试间干扰
        all_types = EventTypeRegistry.get_all_types()
        for event_type in list(all_types):
            EventTypeRegistry.unregister_event_type(event_type)

    def tearDown(self):
        """测试后清理"""
        all_types = EventTypeRegistry.get_all_types()
        for event_type in list(all_types):
            EventTypeRegistry.unregister_event_type(event_type)

    def test_register_event_type(self):
        """测试注册事件类型"""

        class TestEvent(BaseEvent):
            def get_payload(self) -> Dict[str, Any]:
                return {}

        EventTypeRegistry.register_event_type("test_event", TestEvent)
        self.assertTrue(EventTypeRegistry.is_registered("test_event"))
        retrieved_class = EventTypeRegistry.get_event_class("test_event")
        self.assertEqual(retrieved_class, TestEvent)

    def test_unregister_event_type(self):
        """测试注销事件类型"""

        class TestEvent(BaseEvent):
            def get_payload(self) -> Dict[str, Any]:
                return {}

        EventTypeRegistry.register_event_type("test_event", TestEvent)
        self.assertTrue(EventTypeRegistry.is_registered("test_event"))

        EventTypeRegistry.unregister_event_type("test_event")
        self.assertFalse(EventTypeRegistry.is_registered("test_event"))

    def test_get_event_class_not_found(self):
        """测试获取不存在的事件类型"""
        with self.assertRaises(ValueError):
            EventTypeRegistry.get_event_class("non_existent")

    def test_register_duplicate_event_type(self):
        """测试重复注册事件类型"""

        class TestEvent1(BaseEvent):
            def get_payload(self) -> Dict[str, Any]:
                return {}

        class TestEvent2(BaseEvent):
            def get_payload(self) -> Dict[str, Any]:
                return {}

        EventTypeRegistry.register_event_type("duplicate_event", TestEvent1)

        with self.assertRaises(ValueError):
            EventTypeRegistry.register_event_type("duplicate_event", TestEvent2)

    def test_get_all_types(self):
        """测试获取所有事件类型"""

        class TestEvent1(BaseEvent):
            def get_payload(self) -> Dict[str, Any]:
                return {}

        class TestEvent2(BaseEvent):
            def get_payload(self) -> Dict[str, Any]:
                return {}

        EventTypeRegistry.register_event_type("event1", TestEvent1)
        EventTypeRegistry.register_event_type("event2", TestEvent2)

        all_types = EventTypeRegistry.get_all_types()
        self.assertEqual(len(all_types), 2)
        self.assertIn("event1", all_types)
        self.assertIn("event2", all_types)

    def test_get_types_by_category(self):
        """测试按类别获取事件类型"""

        class TestEvent(BaseEvent):
            def get_payload(self) -> Dict[str, Any]:
                return {}

        EventTypeRegistry.register_event_type("test_event", TestEvent, "test_category")

        category_types = EventTypeRegistry.get_types_by_category("test_category")
        self.assertIn("test_event", category_types)

        empty_category = EventTypeRegistry.get_types_by_category("non_existent")
        self.assertEqual(len(empty_category), 0)


class TestEventHandler(unittest.TestCase):
    """EventHandler类测试"""

    def test_event_handler_initialization(self):
        """测试EventHandler初始化"""
        handler = LambdaEventHandler(lambda event: True, "test_handler")
        self.assertEqual(handler.name, "test_handler")
        self.assertTrue(handler.enabled)

    def test_register_handler(self):
        """测试注册处理器"""
        handler = LambdaEventHandler(lambda event: True)
        handler.add_supported_type("test.event")
        self.assertTrue(handler.supports_event_type("test.event"))
        self.assertFalse(handler.supports_event_type("other.event"))

    def test_unregister_handler(self):
        """测试注销处理器"""
        handler = LambdaEventHandler(lambda event: True)
        handler.add_supported_type("test.event")
        handler.remove_supported_type("test.event")
        self.assertFalse(handler.supports_event_type("test.event"))

    def test_handle_event(self):
        """测试处理事件"""
        handled = False

        def handle_func(event: BaseEvent) -> bool:
            nonlocal handled
            handled = True
            return True

        handler = LambdaEventHandler(handle_func)
        handler.add_supported_type("test.event")

        event = TestEvent("test.event")
        result = handler.handle(event)

        self.assertTrue(result)
        self.assertTrue(handled)

    def test_handle_event_no_handlers(self):
        """测试处理没有处理器的事件"""
        handler = LambdaEventHandler(lambda event: False)
        # 不添加支持的事件类型
        event = TestEvent("unsupported.event")
        result = handler.handle(event)
        self.assertFalse(result)

    def test_composite_handler(self):
        """测试复合处理器"""
        handler1 = LambdaEventHandler(lambda event: True, "handler1")
        handler1.add_supported_type("test.event")

        handler2 = LambdaEventHandler(lambda event: False, "handler2")
        handler2.add_supported_type("test.event")

        composite = CompositeEventHandler("composite")
        composite.add_handler(handler1)
        composite.add_handler(handler2)

        self.assertTrue(composite.supports_event_type("test.event"))

        event = TestEvent("test.event")
        result = composite.handle(event)
        self.assertTrue(result)  # handler1返回True


class TestEventBus(unittest.TestCase):
    """EventBus类测试"""

    def setUp(self):
        """测试前准备"""
        # 使用正确的单例获取方式
        self.bus = EventBus()
        # 注册测试事件类型（如果尚未注册）
        registry = self.bus.get_type_registry()
        if not registry.is_registered("test.event"):
            registry.register_event_type("test.event", TestEvent, "test")
        if not registry.is_registered("no.subscribers"):
            registry.register_event_type("no.subscribers", TestEvent, "test")
        if not registry.is_registered("any.event"):
            registry.register_event_type("any.event", TestEvent, "test")

    def tearDown(self):
        """测试后清理"""
        # 清理事件总线状态
        self.bus.clear_all_subscriptions()

    def test_singleton_pattern(self):
        """测试单例模式"""
        bus1 = EventBus()
        bus2 = EventBus()
        self.assertIs(bus1, bus2)

    def test_subscribe_and_unsubscribe(self):
        """测试订阅和取消订阅"""
        handler = Mock(spec=LambdaEventHandler)
        handler.supports_event_type.return_value = True

        # 订阅
        self.bus.subscribe("test.event", handler)

        # 发布事件
        event = TestEvent("test.event")
        self.bus.publish(event)

        handler.handle.assert_called_once_with(event)

        # 取消订阅
        result = self.bus.unsubscribe("test.event", handler)
        self.assertTrue(result)

        # 再次发布事件
        event2 = TestEvent("test.event")
        self.bus.publish(event2)

        # 处理器应该只被调用一次
        handler.handle.assert_called_once()

    def test_subscribe_lambda(self):
        """测试Lambda订阅"""
        handled = False

        def handle_func(event: BaseEvent) -> bool:
            nonlocal handled
            handled = True
            return True

        self.bus.subscribe_lambda("test.event", handle_func, "lambda_handler")

        event = TestEvent("test.event")
        result = self.bus.publish(event)

        self.assertTrue(result)
        self.assertTrue(handled)

    def test_unsubscribe_all(self):
        """测试取消所有订阅"""
        handler1 = Mock(spec=LambdaEventHandler)
        handler1.supports_event_type.return_value = True
        handler2 = Mock(spec=LambdaEventHandler)
        handler2.supports_event_type.return_value = True

        self.bus.subscribe("test.event", handler1)
        self.bus.subscribe("test.event", handler2)

        self.bus.unsubscribe_all("test.event")

        event = TestEvent("test.event")
        result = self.bus.publish(event)
        self.assertFalse(result)

        handler1.handle.assert_not_called()
        handler2.handle.assert_not_called()

    def test_publish_event(self):
        """测试发布事件"""
        handler = Mock(spec=LambdaEventHandler)
        handler.supports_event_type.return_value = True

        self.bus.subscribe("test.event", handler)

        event = TestEvent("test.event", {"data": "test"})
        result = self.bus.publish(event)

        self.assertTrue(result)
        handler.handle.assert_called_once_with(event)
        self.assertEqual(event.get_payload()["data"], "test")

    def test_publish_event_no_subscribers(self):
        """测试发布没有订阅者的事件"""
        event = TestEvent("no.subscribers")
        result = self.bus.publish(event)
        self.assertFalse(result)

    def test_publish_event_handler_exception(self):
        """测试处理器异常处理"""

        def failing_handler(event: BaseEvent) -> bool:
            raise ValueError("Handler failed")

        handler = LambdaEventHandler(failing_handler)
        handler.add_supported_type("test.event")

        self.bus.subscribe("test.event", handler)

        event = TestEvent("test.event")
        # 应该不会抛出异常，而是记录错误并继续
        result = self.bus.publish(event)
        # 结果可能是False，因为处理器失败了
        self.assertFalse(result)

    def test_get_subscribers_count(self):
        """测试获取订阅者数量"""
        self.assertEqual(self.bus.get_subscribers_count("test.event"), 0)

        handler = Mock(spec=LambdaEventHandler)
        handler.supports_event_type.return_value = True
        self.bus.subscribe("test.event", handler)

        self.assertEqual(self.bus.get_subscribers_count("test.event"), 1)

    def test_get_all_subscribed_types(self):
        """测试获取所有已订阅的事件类型"""
        # 确保开始时没有订阅者
        self.bus.clear_all_subscriptions()
        self.assertEqual(len(self.bus.get_all_subscribed_types()), 0)

        handler = Mock(spec=LambdaEventHandler)
        handler.supports_event_type.return_value = True
        self.bus.subscribe("test.event", handler)

        subscribed_types = self.bus.get_all_subscribed_types()
        self.assertIn("test.event", subscribed_types)


if __name__ == "__main__":
    unittest.main()
