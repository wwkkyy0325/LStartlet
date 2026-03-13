"""
自定义窗口管理器
使用完全自定义的UI绘制逻辑，包括自定义边框和窗口控制
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from ..config.ui_config import UIConfig
from ..components.custom_border import CustomBorderManager, CustomWindowFrame
from .abstract_ui_manager import AbstractUIManager


class CustomWindowManager(AbstractUIManager):
    """自定义窗口管理器主类，使用完全自定义的UI绘制逻辑"""
    
    def __init__(self, config: Optional[UIConfig] = None):
        super().__init__(config)
        self.main_window: Optional[CustomWindowFrame] = None  # 使用具体的CustomWindowFrame类型
        
        # 组件管理器 - 使用自定义边框
        self.border_manager: Optional[CustomBorderManager] = None
        
        # 初始化UI
        self._initialize_ui()
    
    def _initialize_ui(self) -> None:
        """初始化UI结构 - 使用自定义窗口框架"""
        # 创建自定义窗口框架作为主窗口
        self.border_manager = CustomBorderManager()
        
        # 创建中心控件
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        
        # 将中心控件设置给自定义边框管理器
        widget = self.border_manager.create_widget()
        if isinstance(widget, CustomWindowFrame):
            self.main_window = widget
            widget.set_content_widget(self.central_widget)
            widget.set_title(self.config_manager.config.window_title)
            widget.resize(*self.config_manager.config.window_size)
        
        # 创建布局
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 初始化组件
        self._initialize_components()
        
        # 应用初始配置
        self._apply_config(self.config_manager.config)
    
    def _apply_config(self, config: UIConfig) -> None:
        """应用配置到所有组件"""
        super()._apply_config(config)
        
        # 自定义边框管理器配置
        if self.border_manager:
            self.border_manager.update_config(config)
        
        # 更新窗口属性
        if self.main_window:
            self.main_window.set_title(config.window_title)
            self.main_window.resize(*config.window_size)
    
    def show(self) -> None:
        """显示主窗口"""
        if self.main_window:
            self.main_window.show()
    
    def hide(self) -> None:
        """隐藏主窗口"""
        if self.main_window:
            self.main_window.hide()
    
    def close(self) -> None:
        """关闭UI"""
        if self.main_window:
            self.main_window.close()
    
    def get_main_window(self) -> Optional[QWidget]:
        """获取主窗口"""
        return self.main_window