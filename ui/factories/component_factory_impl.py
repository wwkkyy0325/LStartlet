from typing import Dict, Any, Optional, List, Callable
from PySide6.QtWidgets import QWidget

# 使用项目自定义日志管理器
from core.logger import info, warning, error

# 导入UI组件
from ui.components import (
    BackgroundWidget, BorderWidget, CustomBorderManager, 
    CursorWidget, FrostedGlassWindow,
    SimpleMountAreaWidget, SimpleMountArea, TopMenuBar,
    DirectoryViewerComponent, ImageViewerComponent
)
from ui.components.central_content_manager_v2 import CentralContentManagerV2
from .component_factory_interface import IComponentFactory


class ComponentFactoryImpl(IComponentFactory):
    """组件工厂具体实现类"""
    
    def __init__(self):
        """初始化组件工厂"""
        self._supported_components = {
            "background": BackgroundWidget,
            "border": BorderWidget,
            "custom_border": CustomBorderManager,
            "simple_mount_area": SimpleMountAreaWidget,
            "cursor_widget": CursorWidget,
            "frosted_glass_window": FrostedGlassWindow,
            "top_menu_bar": TopMenuBar,
            "directory_viewer": DirectoryViewerComponent,
            "image_viewer": ImageViewerComponent,
            "central_content_manager_v2": CentralContentManagerV2
        }
        info("组件工厂初始化完成")
    
    def create_component(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """
        创建UI组件
        
        Args:
            component_type: 组件类型标识符
            config: 组件配置字典
            
        Returns:
            创建的UI组件实例
        """
        try:
            if component_type not in self._supported_components:
                error_msg = f"不支持的组件类型: {component_type}"
                error(error_msg)
                raise ValueError(error_msg)
            
            component_class = self._supported_components[component_type]
            
            # 其他组件使用标准创建方式
            if config:
                component = component_class(**config)
            else:
                component = component_class()
            
            info(f"组件创建成功: {component_type}")
            return component
            
        except Exception as e:
            error_msg = f"创建组件失败: {component_type}, 错误: {e}"
            error(error_msg)
            raise
    
    def register_component_type(self, component_type: str, factory_func: Callable[[Optional[Dict[str, Any]]], QWidget]) -> None:
        """
        注册组件类型和对应的工厂函数
        
        Args:
            component_type: 组件类型标识符
            factory_func: 工厂函数，接受配置参数并返回QWidget实例
        """
        self._supported_components[component_type] = factory_func
        info(f"组件类型已注册: {component_type}")
    
    def unregister_component_type(self, component_type: str) -> bool:
        """
        取消注册组件类型
        
        Args:
            component_type: 组件类型标识符
            
        Returns:
            bool: 是否成功取消注册
        """
        if component_type in self._supported_components:
            del self._supported_components[component_type]
            info(f"组件类型已取消注册: {component_type}")
            return True
        return False
    
    def get_registered_types(self) -> List[str]:
        """
        获取所有已注册的组件类型
        
        Returns:
            List[str]: 已注册的组件类型列表
        """
        return list(self._supported_components.keys())