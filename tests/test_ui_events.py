"""
UI事件系统测试
"""

import unittest
from unittest.mock import Mock
from core.event import (
    EventBus, UIStyleUpdateEvent, UIConfigChangeEvent, 
    UIStateChangeEvent, UIMountAreaEvent, UIComponentLifecycleEvent
)
from ui.components import UIComponentEventHandler, UIComponentManager
from core.event.event_type_registry import EventTypeRegistry


class TestUIEvents(unittest.TestCase):
    """UI事件系统测试"""
    
    def setUp(self):
        """测试前准备"""
        # 确保UI事件类型被注册
        from core.event.events.ui_events import (
            UIStyleUpdateEvent, UIConfigChangeEvent, UIStateChangeEvent,
            UIMountAreaEvent, UIComponentLifecycleEvent
        )
        registry = EventTypeRegistry()
        if not registry.is_registered(UIStyleUpdateEvent.EVENT_TYPE):
            registry.register_event_type(UIStyleUpdateEvent.EVENT_TYPE, UIStyleUpdateEvent, "ui")
        if not registry.is_registered(UIConfigChangeEvent.EVENT_TYPE):
            registry.register_event_type(UIConfigChangeEvent.EVENT_TYPE, UIConfigChangeEvent, "ui")
        if not registry.is_registered(UIStateChangeEvent.EVENT_TYPE):
            registry.register_event_type(UIStateChangeEvent.EVENT_TYPE, UIStateChangeEvent, "ui")
        if not registry.is_registered(UIMountAreaEvent.EVENT_TYPE):
            registry.register_event_type(UIMountAreaEvent.EVENT_TYPE, UIMountAreaEvent, "ui")
        if not registry.is_registered(UIComponentLifecycleEvent.EVENT_TYPE):
            registry.register_event_type(UIComponentLifecycleEvent.EVENT_TYPE, UIComponentLifecycleEvent, "ui")
        
        # 使用正确的EventBus实例化方式
        self.event_bus = EventBus()
        # 清除所有订阅以确保测试独立性
        self.event_bus.clear_all_subscriptions()
    
    def test_ui_event_types_registered(self):
        """测试UI事件类型是否已注册"""
        # 使用类方法而不是实例
        self.assertTrue(EventTypeRegistry.is_registered(UIStyleUpdateEvent.EVENT_TYPE))
        self.assertTrue(EventTypeRegistry.is_registered(UIConfigChangeEvent.EVENT_TYPE))
        self.assertTrue(EventTypeRegistry.is_registered(UIStateChangeEvent.EVENT_TYPE))
        self.assertTrue(EventTypeRegistry.is_registered(UIMountAreaEvent.EVENT_TYPE))
        self.assertTrue(EventTypeRegistry.is_registered(UIComponentLifecycleEvent.EVENT_TYPE))
    
    def test_ui_component_event_handler(self):
        """测试UI组件事件处理器"""
        handler = UIComponentEventHandler("test_component")
        
        # 测试支持的事件类型
        self.assertTrue(handler.supports_event_type(UIStyleUpdateEvent.EVENT_TYPE))
        self.assertTrue(handler.supports_event_type(UIConfigChangeEvent.EVENT_TYPE))
        self.assertTrue(handler.supports_event_type(UIStateChangeEvent.EVENT_TYPE))
        self.assertTrue(handler.supports_event_type(UIMountAreaEvent.EVENT_TYPE))
        self.assertTrue(handler.supports_event_type(UIComponentLifecycleEvent.EVENT_TYPE))
    
    def test_publish_ui_events(self):
        """测试发布UI事件"""
        # 创建处理器并订阅
        handler = Mock(spec=UIComponentEventHandler)
        handler.enabled = True
        handler.supports_event_type.return_value = True
        handler.handle.return_value = True
        
        self.event_bus.subscribe(UIStyleUpdateEvent.EVENT_TYPE, handler)
        
        # 发布事件
        event = UIStyleUpdateEvent("test_component", {"color": "red"})
        result = self.event_bus.publish(event)
        
        # 验证事件被处理
        self.assertTrue(result)
        handler.handle.assert_called_once_with(event)
    
    def test_ui_component_manager(self):
        """测试UI组件管理器"""
        manager = UIComponentManager()
        
        # 创建处理器
        handler = UIComponentEventHandler("test_component")
        
        # 注册处理器
        manager.register_component_handler(handler)
        
        # 验证处理器已注册到事件总线
        self.assertEqual(manager.get_event_bus().get_subscribers_count(UIStyleUpdateEvent.EVENT_TYPE), 1)
        
        # 发布事件
        result = manager.publish_style_update("test_component", {"opacity": 0.5})
        self.assertFalse(result)  # 处理器没有实际处理逻辑，返回False
        
        # 注销处理器
        success = manager.unregister_component_handler("test_component")
        self.assertTrue(success)
        self.assertEqual(manager.get_event_bus().get_subscribers_count(UIStyleUpdateEvent.EVENT_TYPE), 0)


if __name__ == "__main__":
    unittest.main()