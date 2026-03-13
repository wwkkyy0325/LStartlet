"""
基础UI组件类
所有UI组件都应继承此类，实现统一的接口
"""

from abc import ABC, abstractmethod
from typing import Optional

# 只使用PySide6，如果缺失则直接报错
from PySide6.QtWidgets import QWidget
from ..config.ui_config import UIConfig
from ..state.ui_state import UIState


class BaseComponent(ABC):
    """基础UI组件抽象类"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        self.parent = parent
        self._widget: Optional[QWidget] = None
        self._config: Optional[UIConfig] = None
        self._state: Optional[UIState] = None
        
    @property
    def widget(self) -> Optional[QWidget]:
        """获取组件的QWidget"""
        return self._widget
    
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
        if self._widget:
            self._widget.setParent(None)
            self._widget.deleteLater()
            self._widget = None