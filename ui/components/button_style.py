"""
按钮样式组件
提供基础按钮样式和可自定义的按钮样式接口
"""

from typing import Optional, Dict, Any, Callable, cast
from pathlib import Path

from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QPaintEvent, QMouseEvent, QBrush, QRadialGradient, QImage
from PySide6.QtCore import Qt, QPoint, QEvent, QObject, QRect, QPropertyAnimation, QEasingCurve, Property

from core.event.event_bus import EventBus
from core.logger import info, debug


class StyledButton(QPushButton):
    """
    样式化按钮类
    提供基础按钮样式，并支持高度自定义的外观设置
    集成事件系统，支持点击事件和自定义回调
    支持按下/弹起的视觉反馈和长按保持功能
    """
    
    def __init__(
        self, 
        text: str = "", 
        parent: Optional[QWidget] = None,
        style_config: Optional[Dict[str, Any]] = None,
        event_bus: Optional[EventBus] = None,
        click_callback: Optional[Callable[[], None]] = None,
        button_id: str = ""
    ):
        """
        初始化样式化按钮
        
        Args:
            text: 按钮文本
            parent: 父窗口部件
            style_config: 按钮样式配置字典
            event_bus: 事件总线实例（可选）
            click_callback: 点击回调函数（可选）
            button_id: 按钮唯一标识符（用于事件识别）
        """
        super().__init__(text, parent)
        
        # 深拷贝原始样式配置，避免被后续修改影响
        self._original_style_config: Dict[str, Any] = {}
        if style_config:
            for key, value in style_config.items():
                self._original_style_config[key] = value
        
        self._style_config: Dict[str, Any] = style_config or {}
        self._background_image: Optional[QPixmap] = None
        self._event_bus: Optional[EventBus] = event_bus
        self._click_callback: Optional[Callable[[], None]] = click_callback
        self._button_id: str = button_id or f"button_{id(self)}"
        
        # 按钮状态标志
        self._is_hovered: bool = False
        self._is_pressed: bool = False
        
        # 发光动画相关
        self._glow_radius: float = 0.0
        self._target_glow_radius: float = 0.0
        self._glow_animation: Optional[QPropertyAnimation] = None
        
        # 应用初始样式
        if self._original_style_config:
            self.apply_style(self._original_style_config)
        else:
            self._apply_default_style()
        
        # 连接信号
        self.clicked.connect(self._on_button_clicked)
        
        # 启用鼠标追踪
        self.setMouseTracking(True)
    
    def enterEvent(self, event: QEvent) -> None:
        """鼠标进入事件"""
        self._is_hovered = True
        # 启动发光动画 - 扩展到全按钮
        max_radius = max(self.width(), self.height()) * 0.7
        self._start_glow_animation(max_radius)
        super().enterEvent(event)
    
    def leaveEvent(self, event: QEvent) -> None:
        """鼠标离开事件"""
        self._is_hovered = False
        self._is_pressed = False
        # 启动发光动画 - 收缩到0
        self._start_glow_animation(0.0)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self._update_button_style()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = False
            self._update_button_style()
        super().mouseReleaseEvent(event)
    
    def _update_button_style(self) -> None:
        """根据当前状态更新按钮样式"""
        if not self._original_style_config:
            return
            
        # 使用原始配置重新应用样式
        self.apply_style(self._original_style_config)
    
    def get_glow_radius(self) -> float:
        """获取当前发光半径"""
        return self._glow_radius
    
    def set_glow_radius(self, radius: float) -> None:
        """设置发光半径并触发重绘"""
        self._glow_radius = radius
        self.update()
    
    glow_radius = Property(float, get_glow_radius, set_glow_radius)
    
    def _start_glow_animation(self, target_radius: float) -> None:
        """启动发光动画"""
        if self._glow_animation is not None:
            self._glow_animation.stop()
        
        self._glow_animation = QPropertyAnimation(self, b"glow_radius")
        self._glow_animation.setDuration(300)  # 300ms 动画时长
        self._glow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._glow_animation.setStartValue(self._glow_radius)
        self._glow_animation.setEndValue(target_radius)
        self._glow_animation.start()
    
    def _darken_color(self, color_str: str, amount: int) -> str:
        """将颜色变暗指定数值"""
        try:
            # 解析颜色
            color = QColor(color_str)
            
            # 调整亮度 - 使用 cast 解决 PySide6 类型推断问题
            hslf = cast(tuple[float, float, float, float], color.getHslF())
            h, s, l, a = hslf
            new_l = max(0.0, l - (amount / 100.0))
            
            # 创建新颜色
            new_color = QColor.fromHslF(h, s, new_l, a)
            
            return new_color.name()
        except Exception:
            # 如果解析失败，返回原色
            return color_str
    
    def _lighten_color(self, color_str: str, amount: int) -> str:
        """将颜色变亮指定数值"""
        try:
            # 解析颜色
            color = QColor(color_str)
            
            # 调整亮度 - 使用 cast 解决 PySide6 类型推断问题
            hslf = cast(tuple[float, float, float, float], color.getHslF())
            h, s, l, a = hslf
            new_l = min(1.0, l + (amount / 100.0))
            
            # 创建新颜色
            new_color = QColor.fromHslF(h, s, new_l, a)
            
            return new_color.name()
        except Exception:
            # 如果解析失败，返回原色
            return color_str
    
    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        """将十六进制颜色转换为RGBA元组字符串"""
        try:
            color = QColor(hex_color)
            r, g, b, _ = color.getRgb()
            return f"({r}, {g}, {b}, {alpha})"
        except Exception:
            return "(255, 255, 255, 1.0)"
    
    def _on_button_clicked(self) -> None:
        """处理按钮点击事件"""
        try:
            button_info: Dict[str, Any] = {
                'button_id': self._button_id,
                'text': self.text(),
                'timestamp': self._get_current_timestamp()
            }
            
            # 发布按钮点击事件（如果事件总线可用）
            if self._event_bus:
                from core.event.base_event import EventMetadata
                # 创建简单的事件对象
                metadata = EventMetadata(timestamp=self._get_current_timestamp())
                event_data = type('SimpleEvent', (object,), {
                    'event_type': 'button_clicked',
                    'data': button_info,
                    'metadata': metadata
                })()
                self._event_bus.publish(event_data)  # type: ignore
                debug(f"按钮点击事件已发布：{button_info}")
            
            # 执行自定义回调
            if self._click_callback:
                self._click_callback()
                debug(f"按钮点击回调已执行：{self._button_id}")
            
            # 记录日志
            info(f"按钮被点击：{self._button_id} - {self.text()}")
            
        except Exception as e:
            from core.error import handle_error
            error_msg = f"按钮点击处理失败：{e}"
            handle_error(Exception(error_msg))
    
    def _get_current_timestamp(self) -> float:
        """获取当前时间戳"""
        import time
        return time.time()
    
    def set_click_callback(self, callback: Callable[[], None]) -> None:
        """设置点击回调函数"""
        self._click_callback = callback
    
    def set_button_id(self, button_id: str) -> None:
        """设置按钮ID"""
        self._button_id = button_id
    
    def get_button_id(self) -> str:
        """获取按钮ID"""
        return self._button_id
    
    def _apply_default_style(self) -> None:
        """应用默认按钮样式"""
        default_style: Dict[str, Any] = {
            'width': 120,
            'height': 40,
            'border_radius': 8,
            'background_color': '#4A90E2',
            'text_color': '#FFFFFF',
            'border_color': '#357ABD',
            'border_width': 1,
            'font_size': 14,
            'opacity': 1.0
        }
        
        self.apply_style(default_style)
    
    def apply_style(self, style_config: Dict[str, Any]) -> None:
        """
        应用按钮样式
        
        Args:
            style_config: 样式配置字典，支持以下键：
                - width: 按钮宽度
                - height: 按钮高度  
                - border_radius: 边框圆角半径
                - background_color: 背景颜色 (十六进制或颜色名称)
                - text_color: 文本颜色
                - border_color: 边框颜色
                - border_width: 边框宽度
                - font_size: 字体大小
                - glow_effect_enabled: 是否启用悬浮发光效果
                - glow_color: 发光颜色
                - glow_opacity: 发光透明度 (0.0-1.0)
                - hover_background_color: 悬停背景颜色
                - hover_border_color: 悬停边框颜色
                - pressed_background_color: 按下背景颜色
        """
        self._style_config.update(style_config)
        
        # 设置尺寸
        if 'width' in style_config or 'height' in style_config:
            width = style_config.get('width', self.width())
            height = style_config.get('height', self.height())
            self.setFixedSize(width, height)
        
        # 触发重绘
        self.update()
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """重写绘制事件以支持高级视觉效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        rect = self.rect()
        border_radius = self._style_config.get('border_radius', 8)
        
        # 获取当前状态的颜色配置
        base_bg_color = QColor(self._style_config.get('background_color', '#4A90E2'))
        if self._is_pressed:
            bg_color_str = self._style_config.get('pressed_background_color', self._darken_color(base_bg_color.name(), 20))
            bg_color = QColor(bg_color_str)
        elif self._is_hovered:
            bg_color_str = self._style_config.get('hover_background_color', self._lighten_color(base_bg_color.name(), 20))
            bg_color = QColor(bg_color_str)
        else:
            bg_color = base_bg_color
        
        # 绘制圆角背景
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, border_radius, border_radius)
        
        # 绘制边框
        border_width = self._style_config.get('border_width', 1)
        if border_width > 0:
            border_color = QColor(self._style_config.get('border_color', '#357ABD'))
            if self._is_hovered and 'hover_border_color' in self._style_config:
                border_color = QColor(self._style_config['hover_border_color'])
            
            pen = QPen(border_color, border_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, border_radius, border_radius)
        
        # 绘制悬浮发光效果（使用动画控制的半径）
        if self._glow_radius > 0:
            self._draw_glow_effect(painter, rect, border_radius)
        
        # 绘制文本
        text_color = QColor(self._style_config.get('text_color', '#FFFFFF'))
        painter.setPen(text_color)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        font_size = self._style_config.get('font_size', 14)
        font = painter.font()
        font.setPointSize(font_size)
        painter.setFont(font)
        
        text_rect = rect.adjusted(border_width, border_width, -border_width, -border_width)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())
    
    def _draw_glow_effect(self, painter: QPainter, rect: QRect, border_radius: int) -> None:
        """绘制悬浮发光效果 - 使用与按钮完全相同的圆角形状"""
        if self._glow_radius <= 0:
            return
            
        # 创建径向渐变
        center_x = rect.center().x()
        center_y = rect.center().y()
        
        glow_color = QColor(self._style_config.get('glow_color', '#FFFFFF'))
        glow_opacity = self._style_config.get('glow_opacity', 0.6)
        glow_color.setAlphaF(glow_opacity)
        
        # 使用动画控制的发光半径
        gradient = QRadialGradient(center_x, center_y, self._glow_radius)
        gradient.setColorAt(0, glow_color)
        gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        # 绘制发光效果 - 使用与按钮相同的圆角比例
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        
        # 计算发光区域的尺寸和位置
        glow_expand = int(self._glow_radius)
        glow_rect = rect.adjusted(-glow_expand, -glow_expand, glow_expand, glow_expand)
        
        # 计算发光区域的圆角半径 - 保持与原始按钮相同的比例
        original_short_side = min(rect.width(), rect.height())
        glow_short_side = min(glow_rect.width(), glow_rect.height())
        
        if original_short_side > 0:
            radius_ratio = glow_short_side / original_short_side
            glow_border_radius = max(1, int(border_radius * radius_ratio))
        else:
            glow_border_radius = border_radius
        
        # 确保圆角半径不超过发光区域的一半
        max_radius = min(glow_rect.width(), glow_rect.height()) // 2
        glow_border_radius = min(glow_border_radius, max_radius)
        
        painter.drawRoundedRect(glow_rect, glow_border_radius, glow_border_radius)
    
    def get_current_style(self) -> Dict[str, Any]:
        """获取当前按钮样式配置"""
        return self._style_config.copy()
    
    def set_background_image(self, image_path: str) -> bool:
        """
        设置背景图片
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            是否成功设置
        """
        if Path(image_path).exists():
            self._background_image = QPixmap(image_path)
            self._style_config['background_image'] = image_path
            self.update()
            return True
        return False
    
    def remove_background_image(self) -> None:
        """移除背景图片"""
        self._background_image = None
        if 'background_image' in self._style_config:
            del self._style_config['background_image']
        self.update()


# 预定义的按钮样式
class ButtonStyles:
    """预定义的常用按钮样式"""
    
    @staticmethod
    def primary() -> Dict[str, Any]:
        """主要按钮样式"""
        return {
            'width': 120,
            'height': 40,
            'border_radius': 8,
            'background_color': '#4A90E2',
            'text_color': '#FFFFFF',
            'border_color': '#357ABD',
            'border_width': 1,
            'font_size': 14,
            'hover_background_color': '#357ABD',
            'pressed_background_color': '#2C5AA0'
        }
    
    @staticmethod
    def secondary() -> Dict[str, Any]:
        """次要按钮样式"""
        return {
            'width': 120,
            'height': 40,
            'border_radius': 8,
            'background_color': '#F0F0F0',
            'text_color': '#333333',
            'border_color': '#CCCCCC',
            'border_width': 1,
            'font_size': 14,
            'hover_background_color': '#E0E0E0',
            'pressed_background_color': '#D0D0D0'
        }
    
    @staticmethod
    def danger() -> Dict[str, Any]:
        """危险操作按钮样式"""
        return {
            'width': 120,
            'height': 40,
            'border_radius': 8,
            'background_color': '#E74C3C',
            'text_color': '#FFFFFF',
            'border_color': '#C0392B',
            'border_width': 1,
            'font_size': 14,
            'hover_background_color': '#C0392B',
            'pressed_background_color': '#962D1F'
        }
    
    @staticmethod
    def success() -> Dict[str, Any]:
        """成功操作按钮样式"""
        return {
            'width': 120,
            'height': 40,
            'border_radius': 8,
            'background_color': '#27AE60',
            'text_color': '#FFFFFF',
            'border_color': '#219653',
            'border_width': 1,
            'font_size': 14,
            'hover_background_color': '#219653',
            'pressed_background_color': '#1D8348'
        }
    
    @staticmethod
    def frosted_glass() -> Dict[str, Any]:
        """透明玻璃样式按钮 - 白色半透明背景，带匀速发光动画效果"""
        return {
            'width': 120,
            'height': 40,
            'border_radius': 12,
            # 白色半透明背景
            'background_color': 'rgba(255, 255, 255, 40)',
            # 靓丽文字颜色
            'text_color': '#E0E0FF',
            # 白边描边
            'border_color': 'rgba(255, 255, 255, 120)',
            'border_width': 1,
            'font_size': 14,
            # 悬停状态
            'hover_background_color': 'rgba(255, 255, 255, 80)',
            'hover_border_color': 'rgba(255, 255, 255, 200)',
            # 按下状态
            'pressed_background_color': 'rgba(255, 255, 255, 20)',
            # 悬浮发光效果
            'glow_effect_enabled': True,
            'glow_color': '#FFFFFF',
            'glow_opacity': 0.6
        }
    
    @staticmethod
    def circle_icon(size: int = 40) -> Dict[str, Any]:
        """圆形图标按钮样式"""
        return {
            'width': size,
            'height': size,
            'shape': 'circle',
            'background_color': '#4A90E2',
            'text_color': '#FFFFFF',
            'border_color': '#357ABD',
            'border_width': 1,
            'font_size': 16,
            'hover_background_color': '#357ABD',
            'pressed_background_color': '#2C5AA0'
        }
    
    @staticmethod
    def custom_image_button(image_path: str, width: int = 120, height: int = 40) -> Dict[str, Any]:
        """自定义图片按钮样式"""
        return {
            'width': width,
            'height': height,
            'background_image': image_path,
            'text_color': '#FFFFFF',
            'border_width': 0,
            'font_size': 14
        }


# 便捷函数
def create_styled_button(
    text: str = "",
    parent: Optional[QWidget] = None,
    style_name: Optional[str] = None,
    custom_style: Optional[Dict[str, Any]] = None,
    event_bus: Optional[EventBus] = None,
    click_callback: Optional[Callable[[], None]] = None,
    button_id: str = ""
) -> StyledButton:
    """
    创建样式化按钮的便捷函数
    
    Args:
        text: 按钮文本
        parent: 父窗口部件
        style_name: 预定义样式名称 ('primary', 'secondary', 'danger', 'success', 'circle', 'frosted_glass')
        custom_style: 自定义样式配置
        event_bus: 事件总线实例
        click_callback: 点击回调函数
        button_id: 按钮唯一标识符
        
    Returns:
        StyledButton实例
    """
    if style_name:
        style_map = {
            'primary': ButtonStyles.primary,
            'secondary': ButtonStyles.secondary,
            'danger': ButtonStyles.danger,
            'success': ButtonStyles.success,
            'circle': lambda: ButtonStyles.circle_icon(),
            'frosted_glass': ButtonStyles.frosted_glass
        }
        if style_name in style_map:
            style_config = style_map[style_name]()
        else:
            style_config = ButtonStyles.primary()
    elif custom_style:
        style_config = custom_style
    else:
        style_config = None
    
    return StyledButton(
        text, 
        parent, 
        style_config, 
        event_bus, 
        click_callback, 
        button_id
    )


def create_image_button(
    image_path: str,
    text: str = "",
    parent: Optional[QWidget] = None,
    width: int = 120,
    height: int = 40,
    event_bus: Optional[EventBus] = None,
    click_callback: Optional[Callable[[], None]] = None,
    button_id: str = ""
) -> StyledButton:
    """
    创建图片背景按钮的便捷函数
    
    Args:
        image_path: 图片路径
        text: 按钮文本
        parent: 父窗口部件
        width: 按钮宽度
        height: 按钮高度
        event_bus: 事件总线实例
        click_callback: 点击回调函数
        button_id: 按钮唯一标识符
        
    Returns:
        StyledButton实例
    """
    style_config = ButtonStyles.custom_image_button(image_path, width, height)
    return StyledButton(
        text, 
        parent, 
        style_config, 
        event_bus, 
        click_callback, 
        button_id
    )
