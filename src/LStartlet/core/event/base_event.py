"""
基础事件类和抽象接口
定义事件系统的核心契约和通用功能
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time


@dataclass
class EventMetadata:
    """
    事件元数据
    
    包含事件的附加信息，如时间戳、来源、关联ID和优先级等。
    
    Attributes:
        timestamp (float): 事件创建的时间戳（Unix时间），默认为0.0
        source (Optional[str]): 事件来源标识符，默认为 None
        correlation_id (Optional[str]): 关联ID，用于追踪相关事件，默认为 None
        priority (int): 事件优先级，范围0-100，值越高优先级越高，默认为0
        
    Example:
        >>> metadata = EventMetadata(timestamp=time.time(), source="scheduler", priority=50)
    """

    timestamp: float = 0.0
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: int = 0  # 0-100, 越高优先级越高


class BaseEvent(ABC):
    """
    基础事件抽象类
    所有具体事件都应该继承此类
    
    提供事件的基本属性和状态管理功能，包括事件类型、载荷数据、元数据和处理状态。
    
    Attributes:
        _event_type (str): 事件类型标识符
        _payload (Dict[str, Any]): 事件载荷数据，可读写
        _metadata (EventMetadata): 事件元数据
        _handled (bool): 事件是否已被处理
        _modified (bool): 事件载荷是否已被修改
        
    Example:
        >>> class CustomEvent(BaseEvent):
        ...     EVENT_TYPE = "custom.event"
        ...     
        ...     def __init__(self, data: Dict[str, Any]):
        ...         super().__init__(self.EVENT_TYPE, data)
        ...
        >>> event = CustomEvent({"message": "hello"})
    """

    def __init__(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[EventMetadata] = None,
    ) -> None:
        """
        初始化基础事件
        
        Args:
            event_type (str): 事件类型标识符
            payload (Optional[Dict[str, Any]]): 事件载荷数据，默认为 None（空字典）
            metadata (Optional[EventMetadata]): 事件元数据，默认为 None（自动创建）
            
        Example:
            >>> event = BaseEvent("test.event", {"data": "value"})
        """
        self._event_type = event_type
        self._payload = payload or {}
        self._metadata = metadata or EventMetadata(timestamp=time.time())
        self._handled = False
        self._modified = False

    @property
    def event_type(self) -> str:
        """
        获取事件类型
        
        Returns:
            str: 事件类型标识符
            
        Example:
            >>> event = BaseEvent("my.event")
            >>> assert event.event_type == "my.event"
        """
        return self._event_type

    @property
    def payload(self) -> Dict[str, Any]:
        """
        获取事件载荷数据（可修改）
        
        Returns:
            Dict[str, Any]: 事件载荷数据字典
            
        Example:
            >>> event = BaseEvent("test", {"key": "value"})
            >>> event.payload["new_key"] = "new_value"
            >>> assert event.payload["new_key"] == "new_value"
        """
        return self._payload

    @payload.setter
    def payload(self, value: Dict[str, Any]) -> None:
        """
        设置事件载荷数据
        
        Args:
            value (Dict[str, Any]): 新的载荷数据字典
            
        Example:
            >>> event = BaseEvent("test")
            >>> event.payload = {"updated": True}
        """
        self._payload = value
        self._modified = True

    @property
    def metadata(self) -> EventMetadata:
        """
        获取事件元数据
        
        Returns:
            EventMetadata: 事件元数据对象
            
        Example:
            >>> event = BaseEvent("test")
            >>> print(event.metadata.timestamp)
        """
        return self._metadata

    @property
    def handled(self) -> bool:
        """
        检查事件是否已被处理
        
        Returns:
            bool: 如果事件已被处理返回 True，否则返回 False
            
        Example:
            >>> event = BaseEvent("test")
            >>> assert not event.handled
        """
        return self._handled

    @handled.setter
    def handled(self, value: bool) -> None:
        """
        设置事件处理状态
        
        Args:
            value (bool): 处理状态，True 表示已处理
            
        Example:
            >>> event = BaseEvent("test")
            >>> event.handled = True
            >>> assert event.handled
        """
        self._handled = value

    @property
    def modified(self) -> bool:
        """
        检查事件载荷是否已被修改
        
        Returns:
            bool: 如果载荷已被修改返回 True，否则返回 False
            
        Example:
            >>> event = BaseEvent("test")
            >>> assert not event.modified
            >>> event.payload["key"] = "value"
            >>> assert event.modified
        """
        return self._modified

    @abstractmethod
    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷的抽象方法
        
        子类必须实现此方法以返回具体的事件载荷数据。
        
        Returns:
            Dict[str, Any]: 事件载荷数据字典
            
        Raises:
            NotImplementedError: 如果子类未实现此方法
            
        Example:
            >>> class MyEvent(BaseEvent):
            ...     def get_payload(self) -> Dict[str, Any]:
            ...         return {"custom": "data"}
        """
        pass


class CancelableEvent(BaseEvent):
    """
    可取消事件基类
    
    扩展基础事件类，添加事件取消功能。事件处理器可以通过设置 cancel 标志来取消事件的进一步处理。
    
    Attributes:
        _cancel (bool): 事件是否被取消
        _cancel_reason (Optional[str]): 取消原因
        
    Example:
        >>> class CustomCancelableEvent(CancelableEvent):
        ...     EVENT_TYPE = "custom.cancelable"
        ...     
        ...     def __init__(self, data: Dict[str, Any]):
        ...         super().__init__(self.EVENT_TYPE, data)
        ...
        >>> event = CustomCancelableEvent({"message": "hello"})
        >>> event.cancel("Not authorized")
        >>> assert event.is_cancelled
    """

    def __init__(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[EventMetadata] = None,
    ) -> None:
        """
        初始化可取消事件
        
        Args:
            event_type (str): 事件类型标识符
            payload (Optional[Dict[str, Any]]): 事件载荷数据，默认为 None（空字典）
            metadata (Optional[EventMetadata]): 事件元数据，默认为 None（自动创建）
            
        Example:
            >>> event = CancelableEvent("test.cancelable", {"data": "value"})
        """
        super().__init__(event_type, payload, metadata)
        self._cancel = False
        self._cancel_reason: Optional[str] = None

    @property
    def is_cancelled(self) -> bool:
        """
        检查事件是否被取消
        
        Returns:
            bool: 如果事件被取消返回 True，否则返回 False
            
        Example:
            >>> event = CancelableEvent("test")
            >>> assert not event.is_cancelled
            >>> event.cancel("reason")
            >>> assert event.is_cancelled
        """
        return self._cancel

    @property
    def cancel_reason(self) -> Optional[str]:
        """
        获取事件取消原因
        
        Returns:
            Optional[str]: 取消原因，如果未取消则返回 None
            
        Example:
            >>> event = CancelableEvent("test")
            >>> event.cancel("Test reason")
            >>> assert event.cancel_reason == "Test reason"
        """
        return self._cancel_reason

    def cancel(self, reason: Optional[str] = None) -> None:
        """
        取消事件
        
        Args:
            reason (Optional[str]): 取消原因，默认为 None
            
        Example:
            >>> event = CancelableEvent("test")
            >>> event.cancel("Unauthorized access")
            >>> assert event.is_cancelled
        """
        self._cancel = True
        self._cancel_reason = reason

    def reset_cancel(self) -> None:
        """
        重置取消状态
        
        Example:
            >>> event = CancelableEvent("test")
            >>> event.cancel("reason")
            >>> event.reset_cancel()
            >>> assert not event.is_cancelled
        """
        self._cancel = False
        self._cancel_reason = None
