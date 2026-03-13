"""
按钮样式组件
提供基础按钮样式和可自定义的按钮样式接口
"""

from typing import Optional, Dict, Any, Callable, cast
from pathlib import Path

from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QPaintEvent, QMouseEvent
from PySide6.QtCore import Qt, QPoint, QEvent, QObject

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
        
        # 按下状态跟踪
        self._pressed: bool = False
        self._press_pos: QPoint = QPoint()
        
        # 应用默认样式
        self._apply_default_style()
        
        # 如果提供了样式配置，应用自定义样式
        if self._style_config:
            self.apply_style(self._style_config)
        
        # 安装事件过滤器以拦截鼠标事件
        self.installEventFilter(self)
        
        # 连接信号
        self.clicked.connect(self._on_button_clicked)
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """事件过滤器，处理鼠标按下/释放事件"""
        try:
            if event.type() == QEvent.Type.MouseButtonPress:
                self._pressed = True
                # 将事件转换为鼠标事件以获取位置
                if isinstance(event, QMouseEvent):
                    self._press_pos = event.pos()
                self._update_pressed_style(True)
                return False  # 继续传递事件
            
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self._pressed:
                    # 检查是否在按钮范围内释放
                    if isinstance(event, QMouseEvent):
                        if self.rect().contains(event.pos()):
                            self._update_pressed_style(False)
                            self._pressed = False
                            # 执行点击逻辑
                            self.clicked.emit()
                        else:
                            # 在按钮外释放，不触发点击
                            self._update_pressed_style(False)
                            self._pressed = False
                return False
            
            elif event.type() == QEvent.Type.Leave:
                # 鼠标离开按钮区域
                if self._pressed:
                    self._update_pressed_style(False)
                    self._pressed = False
                return False
            
            return super().eventFilter(obj, event)
            
        except Exception as e:
            from core.error import handle_error
            handle_error(e)
            return False
    
    def _update_pressed_style(self, pressed: bool) -> None:
        """更新按钮按下状态的样式"""
        if not self._original_style_config:
            return
        
        # 获取原始背景色（始终从原始配置读取）
        base_color: str = self._original_style_config.get('background_color', '#4A90E2')
        
        if pressed:
            # 按下状态 - 颜色变深
            pressed_color: str = self._darken_color(base_color, 20)
            new_style: Dict[str, Any] = {
                'background_color': pressed_color,
                'border_radius': self._original_style_config.get('border_radius', 8),
                'text_color': self._original_style_config.get('text_color', '#FFFFFF'),
                'font_size': self._original_style_config.get('font_size', 14)
            }
            
            # 保留边框设置
            if self._original_style_config.get('border_width', 1) > 0:
                new_style['border_width'] = self._original_style_config.get('border_width', 1)
                new_style['border_color'] = self._original_style_config.get('border_color', '#357ABD')
            
            self.apply_style(new_style)
        else:
            # 恢复原始样式 - 使用完整原始配置
            restored_style: Dict[str, Any] = {
                'width': self._original_style_config.get('width', self.width()),
                'height': self._original_style_config.get('height', self.height()),
                'border_radius': self._original_style_config.get('border_radius', 8),
                'background_color': base_color,
                'text_color': self._original_style_config.get('text_color', '#FFFFFF'),
                'border_color': self._original_style_config.get('border_color', '#357ABD'),
                'border_width': self._original_style_config.get('border_width', 1),
                'font_size': self._original_style_config.get('font_size', 14),
                'shape': self._original_style_config.get('shape', 'rounded')
            }
            
            # 如果有悬停颜色，也恢复
            if 'hover_background_color' in self._original_style_config:
                restored_style['hover_background_color'] = self._original_style_config['hover_background_color']
            
            self.apply_style(restored_style)
    
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
                - opacity: 透明度 (0.0-1.0)
                - background_image: 背景图片路径
                - shape: 按钮形状 ('rectangle', 'circle', 'rounded')
        """
        self._style_config.update(style_config)
        
        # 设置尺寸
        if 'width' in style_config or 'height' in style_config:
            width = style_config.get('width', self.width())
            height = style_config.get('height', self.height())
            self.setFixedSize(width, height)
        
        # 构建基础样式表
        stylesheet = ""
        
        # 背景色（仅当没有图片背景时）
        if 'background_image' not in style_config:
            bg_color = style_config.get('background_color', '#4A90E2')
            stylesheet += f"background-color: {bg_color};"
        else:
            # 图片背景使用透明背景
            stylesheet += "background-color: transparent;"
        
        # 文本颜色
        text_color = style_config.get('text_color', '#FFFFFF')
        stylesheet += f"color: {text_color};"
        
        # 字体
        font_size = style_config.get('font_size', 14)
        stylesheet += f"font-size: {font_size}px;"
        
        # 边框
        border_width = style_config.get('border_width', 1)
        border_color = style_config.get('border_color', '#357ABD')
        stylesheet += f"border: {border_width}px solid {border_color};"
        
        # 圆角
        shape = style_config.get('shape', 'rounded')
        if shape == 'circle':
            radius = min(self.width(), self.height()) // 2
            stylesheet += f"border-radius: {radius}px;"
        elif shape == 'rounded' or 'border_radius' in style_config:
            border_radius = style_config.get('border_radius', 8)
            stylesheet += f"border-radius: {border_radius}px;"
        else:  # rectangle
            stylesheet += "border-radius: 0px;"
        
        # 设置基础样式
        self.setStyleSheet(stylesheet)
        
        # 处理背景图片
        if 'background_image' in style_config:
            image_path = style_config['background_image']
            if isinstance(image_path, str) and Path(image_path).exists():
                self._background_image = QPixmap(image_path)
            else:
                self._background_image = None
        else:
            self._background_image = None
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """重写绘制事件以支持图片背景"""
        if self._background_image is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 获取按钮矩形区域
            rect = self.rect()
            
            # 绘制裁切后的背景图片
            scaled_pixmap = self._background_image.scaled(
                rect.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(rect, scaled_pixmap)
            
            # 绘制边框（如果需要）
            if self._style_config.get('border_width', 0) > 0:
                border_color = QColor(self._style_config.get('border_color', '#357ABD'))
                pen = QPen(border_color, self._style_config.get('border_width', 1))
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                
                shape = self._style_config.get('shape', 'rounded')
                if shape == 'circle':
                    radius = min(rect.width(), rect.height()) // 2
                    center = rect.center()
                    painter.drawEllipse(center, radius, radius)
                elif shape == 'rounded':
                    border_radius = self._style_config.get('border_radius', 8)
                    painter.drawRoundedRect(rect, border_radius, border_radius)
                else:  # rectangle
                    painter.drawRect(rect)
            
            # 绘制文本
            if self.text():
                text_color = QColor(self._style_config.get('text_color', '#FFFFFF'))
                painter.setPen(text_color)
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        else:
            # 使用默认绘制
            super().paintEvent(event)
    
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
            'hover_background_color': '#357ABD'
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
            'hover_background_color': '#E0E0E0'
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
            'hover_background_color': '#C0392B'
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
            'hover_background_color': '#219653'
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
            'font_size': 16
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
        style_name: 预定义样式名称 ('primary', 'secondary', 'danger', 'success', 'circle')
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
            'circle': lambda: ButtonStyles.circle_icon()
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
