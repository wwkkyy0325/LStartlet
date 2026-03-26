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
    """事件元数据"""
    timestamp: float = 0.0
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: int = 0  # 0-100, 越高优先级越高


class BaseEvent(ABC):
    """
    基础事件抽象类
    所有具体事件都应该继承此类
    """
    
    def __init__(self, event_type: str, payload: Optional[Dict[str, Any]] = None, metadata: Optional[EventMetadata] = None):
        self._event_type = event_type
        self._payload = payload or {}
        self._metadata = metadata or EventMetadata(timestamp=time.time())
        self._handled = False
        self._modified = False
    
    @property
    def event_type(self) -> str:
        """获取事件类型"""
        return self._event_type
    
    @property
    def payload(self) -> Dict[str, Any]:
        """获取事件载荷数据（可修改）"""
        return self._payload
    
    @payload.setter
    def payload(self, value: Dict[str, Any]) -> None:
        """设置事件载荷数据"""
        self._payload = value
        self._modified = True
    
    @property
    def metadata(self) -> EventMetadata:
        """获取事件元数据"""
        return self._metadata
    
    @property
    def handled(self) -> bool:
        """检查事件是否已被处理"""
        return self._handled
    
    @property
    def modified(self) -> bool:
        """检查事件载荷是否被修改过"""
        return self._modified
    
    def mark_handled(self) -> None:
        """标记事件为已处理"""
        self._handled = True
    
    def reset_modified(self) -> None:
        """重置修改标记"""
        self._modified = False
    
    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷数据
        返回当前的载荷数据
        """
        return self._payload


class CancelableEvent(BaseEvent):
    """
    可取消事件基类
    支持事件处理过程中的取消操作
    """
    
    def __init__(self, event_type: str, payload: Optional[Dict[str, Any]] = None, metadata: Optional[EventMetadata] = None):
        super().__init__(event_type, payload, metadata)
        self._canceled = False
    
    @property
    def canceled(self) -> bool:
        """检查事件是否被取消"""
        return self._canceled
    
    def cancel(self) -> None:
        """取消事件"""
        self._canceled = True