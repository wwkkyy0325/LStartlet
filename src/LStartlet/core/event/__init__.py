"""
事件系统公共API
"""

from .base_event import BaseEvent, CancelableEvent, EventMetadata
from .event_type_registry import EventTypeRegistry
from .event_handler import EventHandler, LambdaEventHandler, CompositeEventHandler
from .event_bus import EventBus
from .events.scheduler_events import (
    SchedulerStatusEvent,
    ApplicationLifecycleEvent,
    ConfigItemRegisteredEvent,
    TaskSubmittedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    ProcessCreatedEvent,
    ProcessStartedEvent,
    ProcessStoppedEvent,
    ProcessFailedEvent,
    TickEvent,
)
from .events.ui_events import (
    UIStyleUpdateEvent,
    UIConfigChangeEvent,
    UIStateChangeEvent,
    UIMountAreaEvent,
    UIComponentLifecycleEvent,
    RenderProcessReadyEvent,
)

# 创建全局事件总线实例
event_bus = EventBus()

# 定义基础__all__
__all__ = [
    "BaseEvent",
    "CancelableEvent",
    "EventMetadata",
    "EventTypeRegistry",
    "EventHandler",
    "LambdaEventHandler",
    "CompositeEventHandler",
    "EventBus",
    "event_bus",
    # 调度器事件
    "SchedulerStatusEvent",
    "ApplicationLifecycleEvent",
    "ConfigItemRegisteredEvent",
    "TaskSubmittedEvent",
    "TaskStartedEvent",
    "TaskCompletedEvent", 
    "TaskFailedEvent",
    "ProcessCreatedEvent",
    "ProcessStartedEvent",
    "ProcessStoppedEvent",
    "ProcessFailedEvent",
    "TickEvent",
    # UI事件
    "UIStyleUpdateEvent",
    "UIConfigChangeEvent",
    "UIStateChangeEvent",
    "UIMountAreaEvent",
    "UIComponentLifecycleEvent",
    "RenderProcessReadyEvent",
]