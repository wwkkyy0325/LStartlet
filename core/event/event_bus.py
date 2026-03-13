"""
事件总线
实现事件的发布、订阅和分发功能
"""

from typing import Dict, List, Set, Callable
from threading import Lock, RLock
from collections import defaultdict
import asyncio
from .base_event import BaseEvent
from .event_handler import EventHandler, LambdaEventHandler
from .event_type_registry import EventTypeRegistry


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
    
    def enable_async_support(self) -> None:
        """启用异步事件支持"""
        self._async_enabled = True
    
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
    
    def unsubscribe_all(self, event_type: str) -> None:
        """
        取消订阅指定事件类型的所有处理器
        
        Args:
            event_type: 事件类型
        """
        with self._rw_lock:
            if event_type in self._handlers:
                del self._handlers[event_type]
    
    def publish(self, event: BaseEvent) -> bool:
        """
        发布事件（同步）
        
        Args:
            event: 要发布的事件
            
        Returns:
            bool: 是否有处理器处理了事件
        """
        # 由于参数已通过类型注解确保是BaseEvent类型，无需isinstance检查
        if not self._type_registry.is_registered(event.event_type):
            raise ValueError(f"Event type '{event.event_type}' is not registered")
        
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
                except Exception:
                    # 处理器异常不应影响其他处理器
                    continue
        
        return handled
    
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
        
        # 由于参数已通过类型注解确保是BaseEvent类型，无需isinstance检查
        if not self._type_registry.is_registered(event.event_type):
            raise ValueError(f"Event type '{event.event_type}' is not registered")
        
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
                continue  # 处理器异常不应影响其他处理器
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
        except Exception:
            # 处理器异常不应影响其他处理器
            return False
    
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
    
    def get_all_subscribed_types(self) -> Set[str]:
        """
        获取所有已订阅的事件类型
        
        Returns:
            Set[str]: 已订阅的事件类型集合
        """
        with self._rw_lock:
            return set(self._handlers.keys())
    
    def clear_all_subscriptions(self) -> None:
        """清除所有订阅"""
        with self._rw_lock:
            self._handlers.clear()