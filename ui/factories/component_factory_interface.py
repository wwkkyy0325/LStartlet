"""
组件工厂接口定义
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, List, Optional
from PySide6.QtWidgets import QWidget


class IComponentFactory(ABC):
    """组件工厂接口"""
    
    @abstractmethod
    def create_component(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """
        创建UI组件
        
        Args:
            component_type: 组件类型标识符
            config: 组件配置字典
            
        Returns:
            创建的UI组件实例
        """
        pass
    
    @abstractmethod
    def register_component_type(self, component_type: str, factory_func: Callable[[Optional[Dict[str, Any]]], QWidget]) -> None:
        """
        注册组件类型和对应的工厂函数
        
        Args:
            component_type: 组件类型标识符
            factory_func: 工厂函数，接受配置参数并返回QWidget实例
        """
        raise NotImplementedError()

    @abstractmethod
    def unregister_component_type(self, component_type: str) -> bool:
        """
        取消注册组件类型
        
        Args:
            component_type: 组件类型标识符
            
        Returns:
            bool: 是否成功取消注册
        """
        pass
    
    @abstractmethod
    def get_registered_types(self) -> List[str]:
        """
        获取所有已注册的组件类型
        
        Returns:
            List[str]: 已注册的组件类型列表
        """
        raise NotImplementedError()
