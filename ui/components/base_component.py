"""
基础UI组件类
所有UI组件都应继承此类，实现统一的接口和事件驱动机制
"""

from abc import ABC, abstractmethod
from typing import Optional
# 只使用PySide6，如果缺失则直接报错
from PySide6.QtWidgets import QWidget
from ..config.ui_config import UIConfig
from ..state.ui_state import UIState
from core.event.events.ui_events import (
    UIStyleUpdateEvent, UIConfigChangeEvent, UIStateChangeEvent,
    UIMountAreaEvent, UIComponentLifecycleEvent
)
from .ui_event_handler import UIComponentEventHandler, UIComponentManager
# 使用项目自定义日志管理器
from core.logger import error


class BaseComponent(ABC):
    """基础UI组件抽象类"""
    
    def __init__(self, parent: Optional[QWidget] = None, component_id: Optional[str] = None):
        self.parent = parent
        self.component_id = component_id or f"component_{id(self)}"
        self._widget: Optional[QWidget] = None
        self._config: Optional[UIConfig] = None
        self._state: Optional[UIState] = None
        self._event_handler: Optional[UIComponentEventHandler] = None
        self._ui_manager = UIComponentManager()
        
        # 创建事件处理器并注册
        self._create_event_handler()
        if self._event_handler is None:
            raise RuntimeError(f"Failed to create event handler for component {self.component_id}")
        self._ui_manager.register_component_handler(self._event_handler)
        
        # 发布创建事件
        self._publish_lifecycle_event("created")
    
    def _create_event_handler(self) -> None:
        """创建事件处理器"""
        try:
            self._event_handler = ComponentEventHandler(self.component_id, self)
        except Exception as e:
            error(f"创建事件处理器失败: {e}", extra={"component_id": self.component_id})
            raise
    
    @property
    def widget(self) -> Optional[QWidget]:
        """获取组件的QWidget"""
        return self._widget
    
    @property
    def config(self) -> Optional[UIConfig]:
        """获取组件的配置"""
        return self._config
    
    @property
    def state(self) -> Optional[UIState]:
        """获取组件的状态"""
        return self._state
    
    @abstractmethod
    def create_widget(self) -> QWidget:
        """创建组件的QWidget"""
        pass
    
    @abstractmethod
    def update_config(self, config: UIConfig) -> None:
        """更新组件配置"""
        pass
    
    @abstractmethod
    def update_state(self, state: UIState) -> None:
        """更新组件状态"""
        pass
    
    def destroy(self) -> None:
        """销毁组件"""
        try:
            # 发布销毁事件
            self._publish_lifecycle_event("destroyed")
            
            if self._widget:
                self._widget.setParent(None)
                self._widget.deleteLater()
                self._widget = None
            
            # 注销事件处理器
            if self._event_handler:
                self._ui_manager.unregister_component_handler(self.component_id)
                self._event_handler = None
        except Exception as e:
            error(f"销毁组件失败: {e}", extra={"component_id": self.component_id})
    
    def _publish_lifecycle_event(self, stage: str) -> None:
        """发布生命周期事件"""
        try:
            self._ui_manager.publish_lifecycle_event(self.component_id, stage)
        except Exception as e:
            error(f"发布生命周期事件失败: {e}", extra={"component_id": self.component_id, "stage": stage})
    
    def get_event_handler(self) -> Optional[UIComponentEventHandler]:
        """获取事件处理器"""
        return self._event_handler
    
    def get_config(self) -> Optional[UIConfig]:
        """获取配置"""
        return self._config
    
    def get_state(self) -> Optional[UIState]:
        """获取状态"""
        return self._state


class ComponentEventHandler(UIComponentEventHandler):
    """组件事件处理器实现"""
    
    def __init__(self, component_id: str, component: BaseComponent):
        super().__init__(component_id, f"ComponentHandler_{component_id}")
        self.component = component
    
    def _handle_style_update(self, event: UIStyleUpdateEvent) -> bool:
        """处理样式更新事件"""
        try:
            # 这里可以触发组件的重绘或样式更新
            if self.component.widget:
                self.component.widget.update()
            return True
        except Exception as e:
            error(f"处理样式更新事件失败: {e}", extra={"component_id": self.component_id, "event_type": event.event_type})
            return False
    
    def _handle_config_change(self, event: UIConfigChangeEvent) -> bool:
        """处理配置变更事件"""
        try:
            if self.component.config:
                # 更新配置并触发组件更新
                self.component.update_config(self.component.config)
            return True
        except Exception as e:
            error(f"处理配置变更事件失败: {e}", extra={"component_id": self.component_id, "event_type": event.event_type})
            return False
    
    def _handle_state_change(self, event: UIStateChangeEvent) -> bool:
        """处理状态变更事件"""
        try:
            if self.component.state:
                # 更新状态并触发组件更新
                self.component.update_state(self.component.state)
            return True
        except Exception as e:
            error(f"处理状态变更事件失败: {e}", extra={"component_id": self.component_id, "event_type": event.event_type})
            return False
    
    def _handle_mount_area_event(self, event: UIMountAreaEvent) -> bool:
        """处理挂载区域事件"""
        try:
            # 挂载区域相关的逻辑由具体组件实现
            return False
        except Exception as e:
            error(f"处理挂载区域事件失败: {e}", extra={"component_id": self.component_id, "event_type": event.event_type})
            return False
    
    def _handle_lifecycle_event(self, event: UIComponentLifecycleEvent) -> bool:
        """处理生命周期事件"""
        try:
            # 生命周期事件通常由组件自身管理
            return False
        except Exception as e:
            error(f"处理生命周期事件失败: {e}", extra={"component_id": self.component_id, "event_type": event.event_type})
            return False