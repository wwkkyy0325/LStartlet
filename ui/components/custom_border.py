"""
自定义窗口组件
实现完全自定义的UI绘制逻辑，包括自定义标题栏和窗口控制按钮
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QPainter, QColor, QPaintEvent, QCursor, QMouseEvent
from PySide6.QtCore import Qt, QPoint
from ..config.ui_config import UIConfig, BorderConfig
from ..state.ui_state import UIState
from .base_component import BaseComponent


class CustomWindowButton(QPushButton):
    """自定义窗口按钮"""
    
    def __init__(self, button_type: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.button_type = button_type  # 'minimize', 'maximize', 'close'
        self.setFixedSize(46, 30)
        self.setStyleSheet(self._get_style())
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def _get_style(self) -> str:
        """获取按钮样式"""
        if self.button_type == 'close':
            return """
                QPushButton {
                    background-color: rgba(232, 17, 35, 0);
                    border: none;
                    font-size: 14px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(232, 17, 35, 0.8);
                }
            """
        else:
            return """
                QPushButton {
                    background-color: rgba(0, 0, 0, 0);
                    border: none;
                    font-size: 14px;
                    color: gray;
                }
                QPushButton:hover {
                    background-color: rgba(192, 192, 192, 0.2);
                }
            """
    
    def set_button_type(self, button_type: str):
        """设置按钮类型"""
        self.button_type = button_type
        self.setStyleSheet(self._get_style())


class CustomTitleBar(QWidget):
    """自定义标题栏"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题标签
        self.title_label = QLabel("OCR 应用程序")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setStyleSheet("color: white; font-size: 12px;")
        
        # 控制按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        
        # 最小化按钮
        self.minimize_btn = CustomWindowButton('minimize')
        self.minimize_btn.setText("-")
        self.minimize_btn.clicked.connect(self.on_minimize_clicked)
        
        # 最大化/还原按钮
        self.maximize_btn = CustomWindowButton('maximize')
        self.maximize_btn.setText("□")
        self.maximize_btn.clicked.connect(self.on_maximize_clicked)
        
        # 关闭按钮
        self.close_btn = CustomWindowButton('close')
        self.close_btn.setText("×")
        self.close_btn.clicked.connect(self.on_close_clicked)
        
        button_layout.addWidget(self.minimize_btn)
        button_layout.addWidget(self.maximize_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(button_container)
        
    def set_title(self, title: str):
        """设置标题"""
        self.title_label.setText(title)
        
    def on_minimize_clicked(self):
        """最小化按钮点击事件"""
        parent_window = self.window()  # 获取顶级窗口
        if parent_window:
            parent_window.showMinimized()
            
    def on_maximize_clicked(self):
        """最大化/还原按钮点击事件"""
        parent_window = self.window()  # 获取顶级窗口
        if parent_window:
            if parent_window.isMaximized():
                parent_window.showNormal()
            else:
                parent_window.showMaximized()
                
    def on_close_clicked(self):
        """关闭按钮点击事件"""
        parent_window = self.window()  # 获取顶级窗口
        if parent_window:
            parent_window.close()


class CustomWindowFrame(QWidget):
    """自定义窗口框架，实现完全自定义的边框和绘制逻辑"""
    
    def __init__(self, content_widget: Optional[QWidget] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.content_widget = content_widget
        self.border_config = None
        self.is_dragging = False
        self.drag_position = QPoint()
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # 无边框窗口
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 添加自定义标题栏
        self.title_bar = CustomTitleBar(self)
        layout.addWidget(self.title_bar)
        
        # 添加内容区域
        if self.content_widget:
            layout.addWidget(self.content_widget)
    
    def set_content_widget(self, widget: QWidget):
        """设置内容部件"""
        # 获取布局并进行类型检查
        layout = self.layout()
        if layout is None:
            return  # 如果布局不存在，则退出
        
        # 查找现有的内容部件并替换
        for i in range(layout.count()):
            if i > 0:  # 跳过标题栏
                item = layout.itemAt(i)
                if item is not None:
                    existing_widget = item.widget()
                    if existing_widget:
                        existing_widget.setParent(None)
        
        layout.addWidget(widget)
        self.content_widget = widget
    
    def set_title(self, title: str):
        """设置窗口标题"""
        self.title_bar.set_title(title)
        
    def set_border_config(self, config: BorderConfig):
        """设置边框配置"""
        self.border_config = config
        self.update()  # 触发重绘
    
    def paintEvent(self, event: QPaintEvent):
        """绘制窗口框架"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制整体窗口背景（包含圆角边框效果）
        if self.border_config:
            # 使用圆角矩形作为窗口背景
            painter.setBrush(QColor(255, 255, 255, 240))  # 几乎不透明的白色背景
            painter.setPen(QColor(self.border_config.color))
            painter.setPen(painter.pen())
            painter.drawRoundedRect(
                self.rect(), 
                self.border_config.radius, 
                self.border_config.radius
            )
        else:
            # 默认绘制
            painter.setBrush(QColor(255, 255, 255, 240))
            painter.drawRect(self.rect())
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件，用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() <= 30:  # 标题栏区域
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件，用于拖动窗口"""
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        self.is_dragging = False
        event.accept()


class CustomBorderManager(BaseComponent):
    """自定义边框管理器，实现完全自定义的绘制逻辑"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._widget = None
        self._content_widget = parent  # 保存原始内容部件
        self._custom_frame = None
        
    def create_widget(self) -> QWidget:
        """创建自定义边框控件"""
        # 创建自定义窗口框架，传入原始内容部件
        self._custom_frame = CustomWindowFrame(self._content_widget)
        self._widget = self._custom_frame
        return self._custom_frame
    
    def update_config(self, config: UIConfig) -> None:
        """更新边框配置"""
        self._config = config
        if self._custom_frame:
            self._custom_frame.set_border_config(config.border)
            self._custom_frame.set_title(config.window_title)
    
    def update_state(self, state: UIState) -> None:
        """更新状态"""
        self._state = state