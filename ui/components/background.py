"""
背景管理器组件
支持纯色、渐变、图片、自定义渲染等多种背景类型
"""

from typing import Optional, Callable
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QLinearGradient, QPixmap, QColor, QPaintEvent, QBrush
from PySide6.QtCore import Qt, QRect
from ..config.ui_config import UIConfig, BackgroundType, BackgroundConfig
from ..state.ui_state import UIState
from .base_component import BaseComponent


class BackgroundWidget(QWidget):
    """背景绘制控件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.background_config = None
        self.custom_renderer: Optional[Callable[[QPainter, QRect], None]] = None
    
    def set_background_config(self, config: BackgroundConfig) -> None:
        """设置背景配置"""
        self.background_config = config
        self.update()  # 触发重绘
    
    def set_custom_renderer(self, renderer: Optional[Callable[[QPainter, QRect], None]]) -> None:
        """设置自定义渲染器"""
        self.custom_renderer = renderer
        self.update()
    
    def _draw_glass_effect(self, painter: QPainter, rect: QRect) -> None:
        """绘制透明玻璃效果"""
        if not self.background_config:
            return
        
        # 设置半透明背景
        glass_color = QColor(self.background_config.glass_tint_color)
        glass_color.setAlphaF(self.background_config.glass_tint_opacity)
        painter.fillRect(rect, glass_color)
        
        # 添加微妙的噪点效果（模拟玻璃纹理）
        if self.background_config.glass_noise_opacity > 0:
            noise_color = QColor(255, 255, 255)
            noise_color.setAlphaF(self.background_config.glass_noise_opacity)
            brush = QBrush(noise_color)
            painter.fillRect(rect, brush)
        
        # 添加边缘高光效果
        highlight_thickness = max(1, min(5, int(rect.height() * 0.01)))  # 限制在1-5像素之间
        highlight_color = QColor(255, 255, 255, 60)
        highlight_rect = QRect(
            rect.left(), 
            rect.top(), 
            rect.width(), 
            highlight_thickness
        )
        painter.fillRect(highlight_rect, highlight_color)
        
        # 添加底部阴影效果
        shadow_thickness = max(1, min(5, int(rect.height() * 0.01)))  # 限制在1-5像素之间
        shadow_color = QColor(0, 0, 0, 30)
        shadow_rect = QRect(
            rect.left(), 
            rect.bottom() - shadow_thickness, 
            rect.width(), 
            shadow_thickness
        )
        painter.fillRect(shadow_rect, shadow_color)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制背景"""
        if not self.background_config:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.custom_renderer and self.background_config.type == BackgroundType.CUSTOM:
            # 使用自定义渲染器
            self.custom_renderer(painter, self.rect())
        elif self.background_config.type == BackgroundType.SOLID_COLOR:
            # 纯色背景
            color = QColor(self.background_config.color)
            color.setAlphaF(self.background_config.opacity)
            painter.fillRect(self.rect(), color)
        elif self.background_config.type == BackgroundType.GRADIENT:
            # 渐变背景
            gradient = QLinearGradient()
            if self.background_config.gradient_direction == "vertical":
                gradient.setStart(0, 0)
                gradient.setFinalStop(0, self.height())
            elif self.background_config.gradient_direction == "horizontal":
                gradient.setStart(0, 0)
                gradient.setFinalStop(self.width(), 0)
            else:  # diagonal
                gradient.setStart(0, 0)
                gradient.setFinalStop(self.width(), self.height())
            
            colors = self.background_config.gradient_colors
            if len(colors) >= 2:
                gradient.setColorAt(0, QColor(colors[0]))
                gradient.setColorAt(1, QColor(colors[1]))
                if len(colors) > 2:
                    # 支持更多颜色点
                    step = 1.0 / (len(colors) - 1)
                    for i, color in enumerate(colors):
                        gradient.setColorAt(i * step, QColor(color))
            
            painter.fillRect(self.rect(), gradient)
        elif self.background_config.type == BackgroundType.IMAGE:
            # 图片背景
            if self.background_config.image_path:
                try:
                    pixmap = QPixmap(self.background_config.image_path)
                    if not pixmap.isNull():
                        target_rect = self.rect()
                        if self.background_config.image_mode == "stretch":
                            painter.drawPixmap(target_rect, pixmap)
                        elif self.background_config.image_mode == "tile":
                            # 平铺模式
                            for x in range(0, self.width(), pixmap.width()):
                                for y in range(0, self.height(), pixmap.height()):
                                    painter.drawPixmap(x, y, pixmap)
                        elif self.background_config.image_mode == "center":
                            # 居中模式
                            x = (self.width() - pixmap.width()) // 2
                            y = (self.height() - pixmap.height()) // 2
                            painter.drawPixmap(x, y, pixmap)
                        elif self.background_config.image_mode == "fit":
                            # 适应模式（保持比例）
                            scaled_pixmap = pixmap.scaled(
                                self.size(), 
                                Qt.AspectRatioMode.KeepAspectRatio, 
                                Qt.TransformationMode.SmoothTransformation
                            )
                            x = (self.width() - scaled_pixmap.width()) // 2
                            y = (self.height() - scaled_pixmap.height()) // 2
                            painter.drawPixmap(x, y, scaled_pixmap)
                except Exception:
                    # 图片加载失败时使用默认背景
                    painter.fillRect(self.rect(), QColor("#f0f0f0"))
        elif self.background_config.type == BackgroundType.GLASS:
            # 透明玻璃背景
            self._draw_glass_effect(painter, self.rect())
        
        painter.end()


class BackgroundManager(BaseComponent):
    """背景管理器"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._widget = BackgroundWidget(parent)
    
    def create_widget(self) -> QWidget:
        """创建背景控件"""
        assert self._widget is not None, "Background widget should be initialized"
        return self._widget
    
    def update_config(self, config: UIConfig) -> None:
        """更新背景配置"""
        self._config = config
        background_widget = self._widget
        if isinstance(background_widget, BackgroundWidget):
            background_widget.set_background_config(config.background)
            if config.background.custom_renderer:
                background_widget.set_custom_renderer(config.background.custom_renderer)
    
    def update_state(self, state: UIState) -> None:
        """更新状态（背景通常不需要响应状态变化）"""
        self._state = state