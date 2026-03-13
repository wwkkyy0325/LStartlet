"""
UI事件处理器基类
用于处理UI组件相关的事件，实现样式与逻辑的连接
"""

from typing import Dict, Any
from core.event.event_handler import EventHandler
from core.event.events.ui_events import (
    UIStyleUpdateEvent, UIConfigChangeEvent, UIStateChangeEvent,
    UIMountAreaEvent, UIComponentLifecycleEvent
)
from core.event.base_event import BaseEvent


class UIComponentEventHandler(EventHandler):
    """UI组件事件处理器基类"""
    
    def __init__(self, component_id: str, name: str = ""):
        super().__init__(name or f"UIComponentHandler_{component_id}")
        self.component_id = component_id
        self._supported_types.update([
            UIStyleUpdateEvent.EVENT_TYPE,
            UIConfigChangeEvent.EVENT_TYPE,
            UIStateChangeEvent.EVENT_TYPE,
            UIMountAreaEvent.EVENT_TYPE,
            UIComponentLifecycleEvent.EVENT_TYPE
        ])
    
    def handle(self, event: BaseEvent) -> bool:
        """处理UI相关事件"""
        if not self.enabled:
            return False
        
        if event.event_type == UIStyleUpdateEvent.EVENT_TYPE:
            return self._handle_style_update(event)  # type: ignore
        elif event.event_type == UIConfigChangeEvent.EVENT_TYPE:
            return self._handle_config_change(event)  # type: ignore
        elif event.event_type == UIStateChangeEvent.EVENT_TYPE:
            return self._handle_state_change(event)  # type: ignore
        elif event.event_type == UIMountAreaEvent.EVENT_TYPE:
            return self._handle_mount_area_event(event)  # type: ignore
        elif event.event_type == UIComponentLifecycleEvent.EVENT_TYPE:
            return self._handle_lifecycle_event(event)  # type: ignore
        
        return False
    
    def _handle_style_update(self, event: UIStyleUpdateEvent) -> bool:
        """处理样式更新事件"""
        # 子类可重写此方法
        return False
    
    def _handle_config_change(self, event: UIConfigChangeEvent) -> bool:
        """处理配置变更事件"""
        # 子类可重写此方法
        return False
    
    def _handle_state_change(self, event: UIStateChangeEvent) -> bool:
        """处理状态变更事件"""
        # 子类可重写此方法
        return False
    
    def _handle_mount_area_event(self, event: UIMountAreaEvent) -> bool:
        """处理挂载区域事件"""
        # 子类可重写此方法
        return False
    
    def _handle_lifecycle_event(self, event: UIComponentLifecycleEvent) -> bool:
        """处理生命周期事件"""
        # 子类可重写此方法
        return False


class UIComponentManager:
    """UI组件管理器，负责注册和管理UI组件事件处理器"""
    
    def __init__(self):
        self._handlers: Dict[str, UIComponentEventHandler] = {}
        self._event_bus = None  # 延迟初始化
    
    def get_event_bus(self):
        """获取事件总线实例"""
        if self._event_bus is None:
            from core.event.event_bus import EventBus
            self._event_bus = EventBus()
            # UI事件类型已经在EventBus初始化时注册，无需再次注册
            # 这里只是确保事件总线已正确初始化
        
        return self._event_bus
    
    def register_component_handler(self, handler: UIComponentEventHandler) -> None:
        """注册UI组件事件处理器"""
        self._handlers[handler.component_id] = handler
        event_bus = self.get_event_bus()
        event_bus.subscribe(UIStyleUpdateEvent.EVENT_TYPE, handler)
        event_bus.subscribe(UIConfigChangeEvent.EVENT_TYPE, handler)
        event_bus.subscribe(UIStateChangeEvent.EVENT_TYPE, handler)
        event_bus.subscribe(UIMountAreaEvent.EVENT_TYPE, handler)
        event_bus.subscribe(UIComponentLifecycleEvent.EVENT_TYPE, handler)
    
    def unregister_component_handler(self, component_id: str) -> bool:
        """注销UI组件事件处理器"""
        if component_id not in self._handlers:
            return False
        
        handler = self._handlers[component_id]
        event_bus = self.get_event_bus()
        event_bus.unsubscribe(UIStyleUpdateEvent.EVENT_TYPE, handler)
        event_bus.unsubscribe(UIConfigChangeEvent.EVENT_TYPE, handler)
        event_bus.unsubscribe(UIStateChangeEvent.EVENT_TYPE, handler)
        event_bus.unsubscribe(UIMountAreaEvent.EVENT_TYPE, handler)
        event_bus.unsubscribe(UIComponentLifecycleEvent.EVENT_TYPE, handler)
        
        del self._handlers[component_id]
        return True
    
    def publish_style_update(self, component_id: str, style_data: Dict[str, Any]) -> bool:
        """发布样式更新事件"""
        from core.event.events.ui_events import UIStyleUpdateEvent
        event = UIStyleUpdateEvent(component_id, style_data)
        return self.get_event_bus().publish(event)
    
    def publish_config_change(self, component_id: str, config_changes: Dict[str, Any]) -> bool:
        """发布配置变更事件"""
        from core.event.events.ui_events import UIConfigChangeEvent
        event = UIConfigChangeEvent(component_id, config_changes)
        return self.get_event_bus().publish(event)
    
    def publish_state_change(self, component_id: str, state_changes: Dict[str, Any]) -> bool:
        """发布状态变更事件"""
        from core.event.events.ui_events import UIStateChangeEvent
        event = UIStateChangeEvent(component_id, state_changes)
        return self.get_event_bus().publish(event)
    
    def publish_mount_area_event(self, component_id: str, area_action: str, area_data: Dict[str, Any]) -> bool:
        """发布挂载区域事件"""
        from core.event.events.ui_events import UIMountAreaEvent
        event = UIMountAreaEvent(component_id, area_action, area_data)
        return self.get_event_bus().publish(event)
    
    def publish_lifecycle_event(self, component_id: str, lifecycle_stage: str) -> bool:
        """发布生命周期事件"""
        from core.event.events.ui_events import UIComponentLifecycleEvent
        event = UIComponentLifecycleEvent(component_id, lifecycle_stage)
        return self.get_event_bus().publish(event)