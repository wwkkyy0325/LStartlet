"""
事件系统公共API
"""

from .base_event import BaseEvent, CancelableEvent, EventMetadata
from .event_type_registry import EventTypeRegistry
from .event_handler import EventHandler, LambdaEventHandler, CompositeEventHandler
from .event_bus import EventBus

# 创建全局事件总线实例
event_bus = EventBus()

# 定义基础__all__
__all__ = [
    'BaseEvent',
    'CancelableEvent', 
    'EventMetadata',
    'EventTypeRegistry',
    'EventHandler',
    'LambdaEventHandler',
    'CompositeEventHandler',
    'EventBus',
    'event_bus'
]

# 导入UI事件并确保它们被注册
try:
    from .events.ui_events import (
        UIComponentEvent, UIStyleUpdateEvent, UIConfigChangeEvent,
        UIStateChangeEvent, UIMountAreaEvent, UIComponentLifecycleEvent
    )
    # 扩展__all__列表
    __all__.extend([
        'UIComponentEvent', 'UIStyleUpdateEvent', 'UIConfigChangeEvent',
        'UIStateChangeEvent', 'UIMountAreaEvent', 'UIComponentLifecycleEvent'
    ])
    
    # 确保UI事件类型被注册到全局事件总线
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
        
except ImportError:
    # 如果UI事件模块不存在，跳过导入（保持向后兼容）
    pass