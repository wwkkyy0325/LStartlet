"""事件总线
实现事件的发布、订阅和分发功能"""

from typing import Dict, List, Set, Callable, Type
from threading import Lock, RLock
from collections import defaultdict
import asyncio
from .base_event import BaseEvent
from .event_handler import EventHandler, LambdaEventHandler
from .event_type_registry import EventTypeRegistry
# 使用项目自定义日志管理器
from core.logger import error
from core.decorators import with_error_handling, monitor_metrics


class EventBus:
    """
    事件总线核心类
    提供线程安全的事件发布/订阅机制
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """初始化事件总线"""
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._type_registry = EventTypeRegistry()
        self._rw_lock = RLock()
        self._async_enabled = False
        
        # 只注册调度事件类型
        self._register_scheduler_event_types()
    
    def _register_ui_event_types(self) -> None:
        """注册UI相关的事件类型 - 已禁用"""
        pass
    
    def _register_scheduler_event_types(self) -> None:
        """注册调度相关的事件类型"""
        try:
            from .events.scheduler_events import (
                SchedulerStatusEvent, TaskSubmittedEvent, TaskStartedEvent,
                TaskCompletedEvent, TaskFailedEvent, ProcessCreatedEvent,
                ProcessStartedEvent, ProcessStoppedEvent, ProcessFailedEvent,
                TickEvent, ConfigItemRegisteredEvent, ApplicationLifecycleEvent
            )
            registry = self._type_registry
            registry.register_event_type(SchedulerStatusEvent.EVENT_TYPE, SchedulerStatusEvent, "scheduler")
            registry.register_event_type(TaskSubmittedEvent.EVENT_TYPE, TaskSubmittedEvent, "scheduler")
            registry.register_event_type(TaskStartedEvent.EVENT_TYPE, TaskStartedEvent, "scheduler")
            registry.register_event_type(TaskCompletedEvent.EVENT_TYPE, TaskCompletedEvent, "scheduler")
            registry.register_event_type(TaskFailedEvent.EVENT_TYPE, TaskFailedEvent, "scheduler")
            registry.register_event_type(ProcessCreatedEvent.EVENT_TYPE, ProcessCreatedEvent, "scheduler")
            registry.register_event_type(ProcessStartedEvent.EVENT_TYPE, ProcessStartedEvent, "scheduler")
            registry.register_event_type(ProcessStoppedEvent.EVENT_TYPE, ProcessStoppedEvent, "scheduler")
            registry.register_event_type(ProcessFailedEvent.EVENT_TYPE, ProcessFailedEvent, "scheduler")
            registry.register_event_type(TickEvent.EVENT_TYPE, TickEvent, "scheduler")
            registry.register_event_type(ConfigItemRegisteredEvent.EVENT_TYPE, ConfigItemRegisteredEvent, "scheduler")
            registry.register_event_type(ApplicationLifecycleEvent.EVENT_TYPE, ApplicationLifecycleEvent, "scheduler")
        except ImportError:
            # 如果调度事件模块不存在，跳过注册（保持向后兼容）
            pass
    
    def _ensure_event_type_registered(self, event_type: str, event_class: Type[BaseEvent]) -> None:
        """确保事件类型已注册，如果未注册则尝试注册"""
        if not self._type_registry.is_registered(event_type):
            # 只尝试注册调度器相关的事件类型
            try:
                if event_type.startswith("scheduler."):
                    from .events.scheduler_events import (
                        SchedulerStatusEvent, TaskSubmittedEvent, TaskStartedEvent,
                        TaskCompletedEvent, TaskFailedEvent, ProcessCreatedEvent,
                        ProcessStartedEvent, ProcessStoppedEvent, ProcessFailedEvent,
                        TickEvent, ConfigItemRegisteredEvent
                    )
                    scheduler_event_map: Dict[str, Type[BaseEvent]] = {
                        SchedulerStatusEvent.EVENT_TYPE: SchedulerStatusEvent,
                        TaskSubmittedEvent.EVENT_TYPE: TaskSubmittedEvent,
                        TaskStartedEvent.EVENT_TYPE: TaskStartedEvent,
                        TaskCompletedEvent.EVENT_TYPE: TaskCompletedEvent,
                        TaskFailedEvent.EVENT_TYPE: TaskFailedEvent,
                        ProcessCreatedEvent.EVENT_TYPE: ProcessCreatedEvent,
                        ProcessStartedEvent.EVENT_TYPE: ProcessStartedEvent,
                        ProcessStoppedEvent.EVENT_TYPE: ProcessStoppedEvent,
                        ProcessFailedEvent.EVENT_TYPE: ProcessFailedEvent,
                        TickEvent.EVENT_TYPE: TickEvent,
                        ConfigItemRegisteredEvent.EVENT_TYPE: ConfigItemRegisteredEvent
                    }
                    if event_type in scheduler_event_map:
                        self._type_registry.register_event_type(event_type, scheduler_event_map[event_type], "scheduler")
                elif event_type == "scheduler.config.item.registered":
                    # 单独处理配置项注册事件，使用字符串字面量避免未绑定错误
                    from .events.scheduler_events import ConfigItemRegisteredEvent
                    self._type_registry.register_event_type(ConfigItemRegisteredEvent.EVENT_TYPE, ConfigItemRegisteredEvent, "scheduler")
            except ImportError:
                pass
    
    @monitor_metrics("eventbus_enable_async", include_labels=True)
    def enable_async_support(self) -> None:
        """启用异步事件支持"""
        self._async_enabled = True
    
    @with_error_handling(error_code="EVENT_SUBSCRIBE_ERROR", default_return=None)
    @monitor_metrics("eventbus_subscribe", include_labels=True)
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if not self._type_registry.is_registered(event_type):
            raise ValueError(f"Event type '{event_type}' is not registered")
        
        if not handler.supports_event_type(event_type):
            handler.add_supported_type(event_type)
        
        with self._rw_lock:
            self._handlers[event_type].append(handler)
    
    @with_error_handling(error_code="EVENT_SUBSCRIBE_LAMBDA_ERROR", default_return=None)
    @monitor_metrics("eventbus_subscribe_lambda", include_labels=True)
    def subscribe_lambda(self, event_type: str, handler_func: Callable[[BaseEvent], bool], name: str = "") -> None:
        """
        使用Lambda函数订阅事件
        
        Args:
            event_type: 事件类型
            handler_func: 处理函数
            name: 处理器名称
        """
        lambda_handler = LambdaEventHandler(handler_func, name)
        self.subscribe(event_type, lambda_handler)
    
    @with_error_handling(error_code="EVENT_UNSUBSCRIBE_ERROR", default_return=False)
    @monitor_metrics("eventbus_unsubscribe", include_labels=True)
    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            
        Returns:
            bool: 是否成功取消订阅
        """
        with self._rw_lock:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                    return True
                except ValueError:
                    return False
            return False
    
    @monitor_metrics("eventbus_unsubscribe_all", include_labels=True)
    def unsubscribe_all(self, event_type: str) -> None:
        """
        取消订阅指定事件类型的所有处理器
        
        Args:
            event_type: 事件类型
        """
        with self._rw_lock:
            if event_type in self._handlers:
                del self._handlers[event_type]
    
    @with_error_handling(error_code="EVENT_PUBLISH_ERROR", default_return=False)
    @monitor_metrics("eventbus_publish", include_labels=True)
    def publish(self, event: BaseEvent) -> bool:
        """
        发布事件（同步）
        
        Args:
            event: 要发布的事件
            
        Returns:
            bool: 是否有处理器处理了事件
        """
        # 确保事件类型已注册
        self._ensure_event_type_registered(event.event_type, type(event))
        
        handlers_to_execute = []
        with self._rw_lock:
            if event.event_type in self._handlers:
                # 创建处理器副本以避免在执行过程中修改列表
                handlers_to_execute = self._handlers[event.event_type].copy()
        
        handled = False
        for handler in handlers_to_execute:
            if handler.enabled and handler.supports_event_type(event.event_type):
                try:
                    if handler.handle(event):
                        handled = True
                        if event.handled:
                            break  # 如果事件已被标记为已处理，停止处理
                except Exception as e:
                    # 记录处理器异常，但不应影响其他处理器
                    error(f"事件处理器执行失败: {e}", extra={"handler": handler.name, "event_type": event.event_type})
                    continue
        
        return handled
    
    @with_error_handling(error_code="EVENT_PUBLISH_ASYNC_ERROR", default_return=False)
    @monitor_metrics("eventbus_publish_async", include_labels=True)
    async def publish_async(self, event: BaseEvent) -> bool:
        """
        异步发布事件
        
        Args:
            event: 要发布的事件
            
        Returns:
            bool: 是否有处理器处理了事件
        """
        if not self._async_enabled:
            raise RuntimeError("Async support is not enabled. Call enable_async_support() first.")
        
        # 确保事件类型已注册
        self._ensure_event_type_registered(event.event_type, type(event))
        
        handlers_to_execute = []
        with self._rw_lock:
            if event.event_type in self._handlers:
                handlers_to_execute = self._handlers[event.event_type].copy()
        
        if not handlers_to_execute:
            return False
        
        # 所有处理器都在线程池中异步执行
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, self._execute_handler, handler, event)
            for handler in handlers_to_execute
            if handler.enabled and handler.supports_event_type(event.event_type)
        ]
        
        if not tasks:
            return False
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        handled = False
        
        for result in results:
            if isinstance(result, Exception):
                # 记录处理器异常，但不应影响其他处理器
                error(f"异步事件处理器执行失败: {result}")
                continue
            elif result is True:
                handled = True
        
        return handled
    
    def _execute_handler(self, handler: EventHandler, event: BaseEvent) -> bool:
        """
        执行单个处理器的内部方法
        用于在线程池中执行
        """
        try:
            return handler.handle(event)
        except Exception as e:
            # 记录处理器异常，但不应影响其他处理器
            error(f"事件处理器执行失败: {e}", extra={"handler": handler.name, "event_type": event.event_type})
            return False
    
    @monitor_metrics("eventbus_get_type_registry", include_labels=True)
    def get_type_registry(self) -> EventTypeRegistry:
        """
        获取事件类型注册器
        
        Returns:
            EventTypeRegistry: 事件类型注册器实例
        """
        return self._type_registry
    
    @monitor_metrics("eventbus_get_subscribers_count", include_labels=True)
    def get_subscribers_count(self, event_type: str) -> int:
        """
        获取指定事件类型的订阅者数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            int: 订阅者数量
        """
        with self._rw_lock:
            return len(self._handlers.get(event_type, []))
    
    @monitor_metrics("eventbus_get_all_subscribed_types", include_labels=True)
    def get_all_subscribed_types(self) -> Set[str]:
        """
        获取所有已订阅的事件类型
        
        Returns:
            Set[str]: 已订阅的事件类型集合
        """
        with self._rw_lock:
            return set(self._handlers.keys())
    
    @monitor_metrics("eventbus_clear_all_subscriptions", include_labels=True)
    def clear_all_subscriptions(self) -> None:
        """清除所有订阅"""
        with self._rw_lock:
            self._handlers.clear()