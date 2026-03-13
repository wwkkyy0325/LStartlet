"""
事件类型注册器
用于管理事件类型的注册和验证，避免硬编码
"""

from typing import Dict, Set, Type
from .base_event import BaseEvent


class EventTypeRegistry:
    """
    事件类型注册器
    提供事件类型的集中管理和验证功能
    """
    
    _instance = None
    _registered_types: Dict[str, Type[BaseEvent]] = {}
    _type_categories: Dict[str, Set[str]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_event_type(cls, event_type: str, event_class: Type[BaseEvent], category: str = "general") -> None:
        """
        注册事件类型
        
        Args:
            event_type: 事件类型字符串
            event_class: 事件类
            category: 事件类别（用于分组管理）
        """
        if event_type in cls._registered_types:
            raise ValueError(f"Event type '{event_type}' is already registered")
        
        cls._registered_types[event_type] = event_class
        
        if category not in cls._type_categories:
            cls._type_categories[category] = set()
        cls._type_categories[category].add(event_type)
    
    @classmethod
    def unregister_event_type(cls, event_type: str) -> None:
        """
        注销事件类型
        
        Args:
            event_type: 要注销的事件类型
        """
        if event_type not in cls._registered_types:
            raise ValueError(f"Event type '{event_type}' is not registered")
        
        # 从所有类别中移除
        for category in cls._type_categories.values():
            category.discard(event_type)
        
        del cls._registered_types[event_type]
    
    @classmethod
    def is_registered(cls, event_type: str) -> bool:
        """
        检查事件类型是否已注册
        
        Args:
            event_type: 事件类型字符串
            
        Returns:
            bool: 是否已注册
        """
        return event_type in cls._registered_types
    
    @classmethod
    def get_event_class(cls, event_type: str) -> Type[BaseEvent]:
        """
        获取事件类型对应的类
        
        Args:
            event_type: 事件类型字符串
            
        Returns:
            Type[BaseEvent]: 事件类
            
        Raises:
            ValueError: 如果事件类型未注册
        """
        if not cls.is_registered(event_type):
            raise ValueError(f"Event type '{event_type}' is not registered")
        return cls._registered_types[event_type]
    
    @classmethod
    def get_all_types(cls) -> Set[str]:
        """
        获取所有已注册的事件类型
        
        Returns:
            Set[str]: 所有事件类型集合
        """
        return set(cls._registered_types.keys())
    
    @classmethod
    def get_types_by_category(cls, category: str) -> Set[str]:
        """
        获取指定类别的所有事件类型
        
        Args:
            category: 事件类别
            
        Returns:
            Set[str]: 指定类别的事件类型集合
        """
        return cls._type_categories.get(category, set()).copy()
    
    @classmethod
    def get_all_categories(cls) -> Set[str]:
        """
        获取所有事件类别
        
        Returns:
            Set[str]: 所有事件类别集合
        """
        return set(cls._type_categories.keys())