"""
自定义光点widget组件
"""

from typing import Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPaintEvent, QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QPoint


class CursorWidget(QWidget):
    """自定义光点widget"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 设置鼠标穿透，避免拦截鼠标事件
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("background: transparent;")
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制发光光点"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制多层发光效果
        center = QPoint(10, 10)  # 中心点
        
        # 外层发光（多层半透明圆圈）
        for i in range(3):
            alpha = 80 - i * 25
            if alpha <= 0:
                break
            pen = QPen(QColor(255, 255, 255, alpha), 2 + i * 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            radius = 8 + i * 4
            painter.drawEllipse(center, radius, radius)
        
        # 内层实心圆点
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.drawEllipse(center, 6, 6)
        
        painter.end()