"""
UI管理器抽象基类
提供UI组件管理的通用功能，供具体实现类继承
"""

from typing import Optional, Dict, Any, Callable
from PySide6.QtWidgets import QWidget
from ..config.ui_config import UIConfig, UIConfigManager
from ..state.ui_state import UIState
from ..state.ui_state_manager import UIStateManager
from ..components.background import BackgroundManager
from ..components.simple_mount_area import SimpleMountArea


class AbstractUIManager:
    """UI管理器抽象基类，提供通用的组件管理和状态控制功能"""
    
    def __init__(self, config: Optional[UIConfig] = None):
        self.config_manager = UIConfigManager(config)
        self.state_manager = UIStateManager()
        self.central_widget: Optional[QWidget] = None
        
        # 组件管理器
        self.background_manager: Optional[BackgroundManager] = None
        self.mount_area_manager: Optional[SimpleMountArea] = None
        
        # 组件工厂
        self.component_factory: Optional[Callable[[str, Dict[str, Any]], QWidget]] = None
        
        # 监听配置变更
        self.config_manager.register_observer(self._on_config_changed)
        # 监听状态变更
        self.state_manager.add_observer(self._on_state_changed)
    
    def _initialize_components(self) -> None:
        """初始化所有组件"""
        if not self.central_widget:
            raise RuntimeError("中央控件未初始化")
            
        # 背景管理器
        self.background_manager = BackgroundManager(self.central_widget)
        background_widget = self.background_manager.create_widget()
        if background_widget:
            layout = self.central_widget.layout()
            if layout is not None:
                layout.addWidget(background_widget)
                # 将背景设为底层
                background_widget.lower()
        
        # 挂载区域管理器 - 在背景上方
        self.mount_area_manager = SimpleMountArea(self.central_widget)
        if self.component_factory:
            self.mount_area_manager.set_component_factory(self.component_factory)
        mount_area_widget = self.mount_area_manager.create_widget()
        if mount_area_widget:
            layout = self.central_widget.layout()
            if layout is not None:
                layout.addWidget(mount_area_widget)
    
    def _apply_config(self, config: UIConfig) -> None:
        """应用配置到所有组件"""
        if self.background_manager:
            self.background_manager.update_config(config)
        if self.mount_area_manager:
            self.mount_area_manager.update_config(config)
    
    def _on_config_changed(self, config: UIConfig) -> None:
        """配置变更回调"""
        self._apply_config(config)
    
    def _on_state_changed(self, state: UIState) -> None:
        """状态变更回调"""
        if self.background_manager:
            self.background_manager.update_state(state)
        if self.mount_area_manager:
            self.mount_area_manager.update_state(state)
    
    def set_component_factory(self, factory: Callable[[str, Dict[str, Any]], QWidget]) -> None:
        """设置组件工厂函数"""
        self.component_factory = factory
        if self.mount_area_manager:
            self.mount_area_manager.set_component_factory(factory)
    
    def mount_component(self, area_id: str, component: QWidget) -> bool:
        """在指定区域挂载组件"""
        if self.mount_area_manager:
            return self.mount_area_manager.mount_custom_component(area_id, component)
        return False
    
    def unmount_component(self, area_id: str) -> bool:
        """卸载指定区域的组件"""
        if self.mount_area_manager:
            return self.mount_area_manager.unmount_component(area_id)
        return False
    
    def update_state(self, message: str = "", state_type: str = "", progress: float = -1.0, data: Optional[Dict[str, Any]] = None) -> None:
        """更新UI状态"""
        self.state_manager.update_state(message=message, state_type=state_type, progress=progress, data=data)
    
    def get_config_manager(self) -> UIConfigManager:
        """获取配置管理器"""
        return self.config_manager
    
    def get_state_manager(self) -> UIStateManager:
        """获取状态管理器"""
        return self.state_manager