"""
标准窗口管理器
负责协调背景、边框、挂载区域等组件，使用标准QMainWindow实现
"""

from typing import Optional
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from ..config.ui_config import UIConfig
from ..components.border import BorderManager
from ..state.ui_state import UIState
from .abstract_ui_manager import AbstractUIManager


class StandardWindowManager(AbstractUIManager):
    """标准窗口管理器主类，使用标准QMainWindow"""
    
    def __init__(self, config: Optional[UIConfig] = None):
        super().__init__(config)
        self.main_window: Optional[QMainWindow] = None
        
        # 边框管理器（仅在标准UI中使用）
        self.border_manager: Optional[BorderManager] = None
        
        # 初始化UI
        self._initialize_ui()
    
    def _initialize_ui(self) -> None:
        """初始化UI结构"""
        # 创建主窗口
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle(self.config_manager.config.window_title)
        self.main_window.resize(*self.config_manager.config.window_size)
        self.main_window.setMinimumSize(*self.config_manager.config.window_min_size)
        
        # 创建中心控件
        self.central_widget = QWidget()
        self.main_window.setCentralWidget(self.central_widget)
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.central_widget.setLayout(layout)
        
        # 初始化组件
        self._initialize_components()
        
        # 初始化边框管理器（标准UI特有）
        self._initialize_border()
        
        # 应用初始配置
        self._apply_config(self.config_manager.config)
    
    def _initialize_components(self) -> None:
        """初始化所有组件"""
        super()._initialize_components()
        
        # 边框管理器 - 在最顶层（标准UI特有）
        if self.central_widget and self.border_manager:
            border_widget = self.border_manager.create_widget()
            if border_widget:
                layout = self.central_widget.layout()
                if layout is not None:
                    layout.addWidget(border_widget)
                    # 将边框设为顶层
                    border_widget.raise_()
    
    def _initialize_border(self) -> None:
        """初始化边框管理器（标准UI特有）"""
        if self.central_widget:
            self.border_manager = BorderManager(self.central_widget)
    
    def _apply_config(self, config: UIConfig) -> None:
        """应用配置到所有组件"""
        super()._apply_config(config)
        
        # 边框管理器配置（标准UI特有）
        if self.border_manager:
            self.border_manager.update_config(config)
        
        # 更新窗口属性
        if self.main_window:
            self.main_window.setWindowTitle(config.window_title)
            self.main_window.resize(*config.window_size)
            self.main_window.setMinimumSize(*config.window_size)
    
    def _on_state_changed(self, state: UIState) -> None:
        """状态变更回调"""
        super()._on_state_changed(state)
        
        # 边框管理器状态更新（标准UI特有）
        if self.border_manager:
            self.border_manager.update_state(state)
    
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
    
    def get_main_window(self) -> Optional[QMainWindow]:
        """获取主窗口"""
        return self.main_window