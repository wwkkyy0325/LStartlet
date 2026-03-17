"""
UI工厂接口模块
定义UI工厂的标准接口，用于创建和管理不同类型的UI
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import QApplication, QWidget
from ui.factories.component_factory_interface import IComponentFactory


class IUIFactory(ABC):
    """UI工厂接口"""
    
    @abstractmethod
    def create_qt_application(self, argv: Optional[List[str]] = None) -> QApplication:
        """创建Qt应用程序实例"""
        pass
    
    @abstractmethod
    def create_standard_ui(self, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """创建标准UI（带系统边框）"""
        pass
    
    @abstractmethod
    def create_custom_ui(self, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """创建自定义UI（无边框磨砂玻璃效果）"""
        pass
    
    @abstractmethod
    def create_frosted_glass_ui(self, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """创建磨砂玻璃效果UI"""
        pass
    
    @abstractmethod
    def cleanup_resources(self) -> None:
        """清理UI相关资源"""
        pass
    
    @abstractmethod
    def get_qt_app(self) -> Optional[QApplication]:
        """获取Qt应用程序实例"""
        pass
    
    @abstractmethod
    def get_component_factory(self) -> IComponentFactory:
        """获取组件工厂实例"""
        pass