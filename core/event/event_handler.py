"""
事件处理器
提供事件处理的扩展点和通用功能
"""

from abc import ABC, abstractmethod
from typing import Set, List, Callable
from threading import Lock
from .base_event import BaseEvent


class EventHandler(ABC):
    """
    事件处理器抽象基类
    所有具体事件处理器都应该继承此类
    """
    
    def __init__(self, name: str = ""):
        self._name = name or self.__class__.__name__
        self._supported_types: Set[str] = set()
        self._enabled = True
        self._lock = Lock()
    
    @property
    def name(self) -> str:
        """获取处理器名称"""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """检查处理器是否启用"""
        return self._enabled
    
    def enable(self) -> None:
        """启用处理器"""
        with self._lock:
            self._enabled = True
    
    def disable(self) -> None:
        """禁用处理器"""
        with self._lock:
            self._enabled = False
    
    def supports_event_type(self, event_type: str) -> bool:
        """
        检查处理器是否支持指定事件类型
        
        Args:
            event_type: 事件类型
            
        Returns:
            bool: 是否支持
        """
        return event_type in self._supported_types
    
    def add_supported_type(self, event_type: str) -> None:
        """
        添加支持的事件类型
        
        Args:
            event_type: 事件类型
        """
        with self._lock:
            self._supported_types.add(event_type)
    
    def remove_supported_type(self, event_type: str) -> None:
        """
        移除支持的事件类型
        
        Args:
            event_type: 事件类型
        """
        with self._lock:
            self._supported_types.discard(event_type)
    
    def get_supported_types(self) -> Set[str]:
        """
        获取所有支持的事件类型
        
        Returns:
            Set[str]: 支持的事件类型集合
        """
        with self._lock:
            return self._supported_types.copy()
    
    @abstractmethod
    def handle(self, event: BaseEvent) -> bool:
        """
        处理事件
        
        Args:
            event: 要处理的事件
            
        Returns:
            bool: 是否成功处理事件
        """
        pass


class LambdaEventHandler(EventHandler):
    """
    Lambda事件处理器
    允许使用函数作为事件处理器
    """
    
    def __init__(self, handler_func: Callable[[BaseEvent], bool], name: str = ""):
        super().__init__(name)
        self._handler_func = handler_func
    
    def handle(self, event: BaseEvent) -> bool:
        """处理事件"""
        if not self.enabled:
            return False
        return self._handler_func(event)


class CompositeEventHandler(EventHandler):
    """
    复合事件处理器
    可以组合多个处理器一起处理事件
    """
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self._handlers: List[EventHandler] = []
    
    def add_handler(self, handler: EventHandler) -> None:
        """
        添加子处理器
        
        Args:
            handler: 子处理器
        """
        with self._lock:
            self._handlers.append(handler)
            # 合并支持的事件类型
            for event_type in handler.get_supported_types():
                self._supported_types.add(event_type)
    
    def remove_handler(self, handler: EventHandler) -> bool:
        """
        移除子处理器
        
        Args:
            handler: 要移除的子处理器
            
        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
                # 重新计算支持的事件类型
                self._supported_types.clear()
                for h in self._handlers:
                    self._supported_types.update(h.get_supported_types())
                return True
            return False
    
    def handle(self, event: BaseEvent) -> bool:
        """处理事件"""
        if not self.enabled:
            return False
        
        success = False
        for handler in self._handlers:
            if handler.enabled and handler.supports_event_type(event.event_type):
                if handler.handle(event):
                    success = True
                    if event.handled:
                        break  # 如果事件已被标记为已处理，停止处理
        return success