#!/usr/bin/env python3
"""
UI组件模块单元测试
"""

import sys
import unittest
from pathlib import Path
from typing import Optional, Any, Dict
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 确保UI事件类型被注册
from core.event.events.ui_events import (
    UIStyleUpdateEvent, UIConfigChangeEvent, UIStateChangeEvent,
    UIMountAreaEvent, UIComponentLifecycleEvent
)
from core.event.event_type_registry import EventTypeRegistry
from core.event.event_bus import EventBus

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

from ui.components.base_component import BaseComponent
from ui.components.ui_event_handler import UIComponentManager, UIComponentEventHandler
from ui.state.ui_state import UIState
from ui.config.ui_config import UIConfig
from PySide6.QtWidgets import QWidget


# 创建一个可测试的具体组件
class TestableComponent(BaseComponent):
    """可测试的具体组件"""
    
    def __init__(self, parent: Optional[QWidget] = None, component_id: Optional[str] = None):
        # 跳过父类的自动注册逻辑
        self.component_id = component_id or "test_component"
        self._widget = None
        self._config = None
        self._state = None
        self._event_handler = None
        self._ui_manager = None
        self.widget_created = False
        self.config_updated = False
        self.state_updated = False
    
    def create_widget(self):
        """创建组件的QWidget"""
        from PySide6.QtWidgets import QWidget
        widget = QWidget()
        self._widget = widget
        self.widget_created = True
        return widget
    
    def update_config(self, config: UIConfig) -> None:
        """更新组件配置"""
        self._config = config
        self.config_updated = True
    
    def update_state(self, state: UIState) -> None:
        """更新组件状态"""
        self._state = state
        self.state_updated = True


class TestUIComponentManager(unittest.TestCase):
    """UIComponentManager类测试"""
    
    def setUp(self):
        """测试前准备"""
        # 确保UI事件类型已注册
        from core.event.events.ui_events import (
            UIStyleUpdateEvent, UIConfigChangeEvent, UIStateChangeEvent,
            UIMountAreaEvent, UIComponentLifecycleEvent
        )
        from core.event.event_bus import EventBus
        from core.event.base_event import BaseEvent
        
        bus = EventBus()
        registry = bus.get_type_registry()
        
        # 注册UI事件类型（如果尚未注册）
        ui_events: list[tuple[str, type[BaseEvent]]] = [
            (UIStyleUpdateEvent.EVENT_TYPE, UIStyleUpdateEvent),
            (UIConfigChangeEvent.EVENT_TYPE, UIConfigChangeEvent),
            (UIStateChangeEvent.EVENT_TYPE, UIStateChangeEvent),
            (UIMountAreaEvent.EVENT_TYPE, UIMountAreaEvent),
            (UIComponentLifecycleEvent.EVENT_TYPE, UIComponentLifecycleEvent)
        ]
        
        for event_type, event_class in ui_events:
            if not registry.is_registered(event_type):
                registry.register_event_type(event_type, event_class, "ui")
        
        self.manager = UIComponentManager()
    
    def test_manager_initialization(self):
        """测试UI组件管理器初始化"""
        # 使用公共API验证初始化状态
        event_bus = self.manager.get_event_bus()
        self.assertIsNotNone(event_bus)
        # 验证没有注册任何处理器
        # 由于没有公共API获取handlers数量，我们可以通过尝试注销不存在的处理器来间接验证
        result = self.manager.unregister_component_handler("non_existent")
        self.assertFalse(result)
    
    def test_get_event_bus(self):
        """测试获取事件总线"""
        event_bus = self.manager.get_event_bus()
        self.assertIsInstance(event_bus, EventBus)
        # 第二次调用应该返回同一个实例
        event_bus2 = self.manager.get_event_bus()
        self.assertIs(event_bus, event_bus2)
    
    def test_register_and_unregister_handler(self):
        """测试注册和注销处理器"""
        handler = Mock(spec=UIComponentEventHandler)
        handler.component_id = "test_component"
        
        # 注册处理器
        self.manager.register_component_handler(handler)
        # 验证处理器已注册（通过功能测试来验证）
        
        # 注销处理器
        result = self.manager.unregister_component_handler(handler.component_id)
        self.assertTrue(result)
        # 再次注销应该返回False
        result = self.manager.unregister_component_handler(handler.component_id)
        self.assertFalse(result)
    
    def test_unregister_nonexistent_handler(self):
        """测试注销不存在的处理器"""
        result = self.manager.unregister_component_handler("non_existent")
        self.assertFalse(result)
    
    def test_publish_style_update(self):
        """测试发布样式更新事件"""
        # 创建mock事件总线实例
        mock_bus_instance = Mock()
        mock_bus_instance.publish.return_value = True
        
        # 替换manager的get_event_bus方法
        original_get_event_bus = self.manager.get_event_bus
        self.manager.get_event_bus = Mock(return_value=mock_bus_instance)
        
        try:
            style_data: Dict[str, Any] = {"color": "red", "font_size": 12}
            result = self.manager.publish_style_update("test_component", style_data)
            
            self.assertTrue(result)
            mock_bus_instance.publish.assert_called_once()
        finally:
            # 恢复原始方法
            self.manager.get_event_bus = original_get_event_bus
    
    def test_publish_config_change(self):
        """测试发布配置变更事件"""
        # 创建mock事件总线实例
        mock_bus_instance = Mock()
        mock_bus_instance.publish.return_value = True
        
        # 替换manager的get_event_bus方法
        original_get_event_bus = self.manager.get_event_bus
        self.manager.get_event_bus = Mock(return_value=mock_bus_instance)
        
        try:
            config_data: Dict[str, Any] = {"theme": "dark", "language": "zh"}
            result = self.manager.publish_config_change("test_component", config_data)
            
            self.assertTrue(result)
            mock_bus_instance.publish.assert_called_once()
        finally:
            # 恢复原始方法
            self.manager.get_event_bus = original_get_event_bus
    
    def test_publish_state_change(self):
        """测试发布状态变更事件"""
        # 创建mock事件总线实例
        mock_bus_instance = Mock()
        mock_bus_instance.publish.return_value = True
        
        # 替换manager的get_event_bus方法
        original_get_event_bus = self.manager.get_event_bus
        self.manager.get_event_bus = Mock(return_value=mock_bus_instance)
        
        try:
            state_changes: Dict[str, Any] = {"message": "test", "progress": 0.5}
            result = self.manager.publish_state_change("test_component", state_changes)
            
            self.assertTrue(result)
            mock_bus_instance.publish.assert_called_once()
        finally:
            # 恢复原始方法
            self.manager.get_event_bus = original_get_event_bus
    
    def test_publish_mount_area_event(self):
        """测试发布挂载区域事件"""
        # 创建mock事件总线实例
        mock_bus_instance = Mock()
        mock_bus_instance.publish.return_value = True
        
        # 替换manager的get_event_bus方法
        original_get_event_bus = self.manager.get_event_bus
        self.manager.get_event_bus = Mock(return_value=mock_bus_instance)
        
        try:
            area_info: Dict[str, Any] = {"x": 100, "y": 200, "width": 300, "height": 400}
            result = self.manager.publish_mount_area_event("test_component", "mount", area_info)
            
            self.assertTrue(result)
            mock_bus_instance.publish.assert_called_once()
        finally:
            # 恢复原始方法
            self.manager.get_event_bus = original_get_event_bus
    
    def test_publish_lifecycle_event(self):
        """测试发布生命周期事件"""
        # 创建mock事件总线实例
        mock_bus_instance = Mock()
        mock_bus_instance.publish.return_value = True
        
        # 替换manager的get_event_bus方法
        original_get_event_bus = self.manager.get_event_bus
        self.manager.get_event_bus = Mock(return_value=mock_bus_instance)
        
        try:
            result = self.manager.publish_lifecycle_event("test_component", "mounted")
            
            self.assertTrue(result)
            mock_bus_instance.publish.assert_called_once()
        finally:
            # 恢复原始方法
            self.manager.get_event_bus = original_get_event_bus


class TestTestableComponent(unittest.TestCase):
    """可测试组件的集成测试"""
    
    @patch('PySide6.QtWidgets.QWidget')
    def test_component_initialization(self, mock_widget_class: Mock):
        """测试组件初始化"""
        mock_widget = Mock()
        mock_widget_class.return_value = mock_widget
        
        component = TestableComponent(component_id="test_comp")
        
        self.assertEqual(component.component_id, "test_comp")
        self.assertIsNone(component.get_event_handler())
        self.assertFalse(component.widget_created)
        self.assertFalse(component.config_updated)
        self.assertFalse(component.state_updated)
    
    @patch('PySide6.QtWidgets.QWidget')
    def test_component_create_widget(self, mock_widget_class: Mock):
        """测试组件创建widget"""
        mock_widget = Mock()
        mock_widget_class.return_value = mock_widget
        
        component = TestableComponent()
        widget = component.create_widget()
        
        self.assertEqual(widget, mock_widget)
        self.assertTrue(component.widget_created)
    
    def test_component_update_config(self):
        """测试组件更新配置"""
        component = TestableComponent()
        config = UIConfig()
        
        component.update_config(config)
        
        self.assertEqual(component.get_config(), config)
        self.assertTrue(component.config_updated)
    
    def test_component_update_state(self):
        """测试组件更新状态"""
        component = TestableComponent()
        state = UIState(message="test")
        
        component.update_state(state)
        
        self.assertEqual(component.get_state(), state)
        self.assertTrue(component.state_updated)


if __name__ == '__main__':
    unittest.main()