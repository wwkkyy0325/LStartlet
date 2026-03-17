"""
UI工厂模块初始化文件
"""

# 避免在__init__.py中导入具体实现类，只导出接口
from .ui_factory_interface import IUIFactory
from .component_factory_interface import IComponentFactory

__all__ = ['IUIFactory', 'IComponentFactory']