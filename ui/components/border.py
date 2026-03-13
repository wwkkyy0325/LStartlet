"""
边框管理器组件
支持多种边框样式和配置
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QFrame
from PySide6.QtGui import QPen, QPainter, QColor, QPaintEvent
from PySide6.QtCore import Qt
from ..config.ui_config import UIConfig, BorderStyle, BorderConfig
from ..state.ui_state import UIState
from .base_component import BaseComponent


class BorderWidget(QFrame):
    """边框绘制控件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.border_config = None
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
    
    def set_border_config(self, config: BorderConfig) -> None:
        """设置边框配置"""
        self.border_config = config
        self.update()  # 触发重绘
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制边框"""
        super().paintEvent(event)
        
        if not self.border_config or self.border_config.style == BorderStyle.NONE:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 设置画笔
        pen = QPen()
        pen.setColor(QColor(self.border_config.color))
        pen.setWidth(self.border_config.width)
        
        if self.border_config.style == BorderStyle.SOLID:
            pen.setStyle(Qt.PenStyle.SolidLine)
        elif self.border_config.style == BorderStyle.DASHED:
            pen.setStyle(Qt.PenStyle.DashLine)
        elif self.border_config.style == BorderStyle.DOTTED:
            pen.setStyle(Qt.PenStyle.DotLine)
        elif self.border_config.style == BorderStyle.DOUBLE:
            pen.setStyle(Qt.PenStyle.SolidLine)
            # 双线需要绘制两次
            inner_rect = self.rect().adjusted(
                self.border_config.width + 2, 
                self.border_config.width + 2,
                -self.border_config.width - 2, 
                -self.border_config.width - 2
            )
            painter.setPen(pen)
            painter.drawRoundedRect(
                inner_rect, 
                self.border_config.radius, 
                self.border_config.radius
            )
        
        painter.setPen(pen)
        rect = self.rect().adjusted(1, 1, -1, -1)  # 避免超出边界
        painter.drawRoundedRect(
            rect, 
            self.border_config.radius, 
            self.border_config.radius
        )
        
        painter.end()


class BorderManager(BaseComponent):
    """边框管理器"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._widget = BorderWidget(parent)
    
    def create_widget(self) -> QWidget:
        """创建边框控件"""
        assert self._widget is not None, "Widget should be initialized in constructor"
        return self._widget
    
    def update_config(self, config: UIConfig) -> None:
        """更新边框配置"""
        self._config = config
        if self._widget is not None:
            # 使用类型断言告诉类型检查器这是 BorderWidget
            assert isinstance(self._widget, BorderWidget)
            self._widget.set_border_config(config.border)
    
    def update_state(self, state: UIState) -> None:
        """更新状态（边框通常不需要响应状态变化）"""
        self._state = state