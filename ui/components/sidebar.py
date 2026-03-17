"""
VSCode风格左侧栏组件
提供类似VSCode的侧边栏功能，只包含图标按钮，通过信号与外部内容区域通信
"""

from typing import Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QSize, QEvent, QPoint, QTimer
from PySide6.QtGui import QMouseEvent


class SidebarTooltip(QWidget):
    """侧边栏自定义悬浮提示组件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.ToolTip | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 设置样式
        self.setStyleSheet("""
            SidebarTooltip {
                background-color: rgba(30, 30, 30, 240);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
                font-size: 12px;
                min-height: 24px;
                max-width: 200px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label)
        
        self.hide()
    
    def show_tooltip(self, text: str, pos: QPoint):
        """显示提示"""
        if not text:
            self.hide()
            return
            
        self.label.setText(text)
        self.adjustSize()
        self.move(pos)
        self.show()
    
    def hide_tooltip(self):
        """隐藏提示"""
        self.hide()


class SidebarWidget(QWidget):
    """
    VSCode风格左侧栏组件
    只包含顶部图标按钮区域，通过信号与外部内容区域通信
    """
    
    # 信号定义
    view_selected = Signal(str)  # 当选择视图时触发（传递视图ID）
    view_deselected = Signal()   # 当取消选择时触发
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_view = ""
        self._buttons: Dict[str, QPushButton] = {}
        self._button_tooltips: Dict[str, str] = {}  # 存储按钮的提示文本
        
        # 悬浮提示相关
        self._tooltip_widget = SidebarTooltip(self)
        self._hovered_button_id: Optional[str] = None
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._show_tooltip)
        self._hover_delay = 300  # 毫秒延迟
        
        self._setup_ui()
        self._apply_sidebar_style()
        
        # 启用鼠标追踪
        self.setMouseTracking(True)
    
    def _setup_ui(self):
        """设置UI布局"""
        # 主布局 - 垂直布局，只包含图标按钮
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 8)
        main_layout.setSpacing(8)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 添加默认的几个按钮（类似VSCode）
        self.add_button("explorer", "📁", "资源管理器")
        self.add_button("search", "🔍", "搜索")
        self.add_button("source_control", "📦", "源代码管理")
        self.add_button("run", "▶️", "运行和调试")
        self.add_button("extensions", "🧩", "扩展")
    
    def _apply_sidebar_style(self):
        """应用VSCode风格的侧边栏样式"""
        style = """
            SidebarWidget {
                background-color: rgba(30, 30, 30, 220);
                border-right: 1px solid rgba(255, 255, 255, 30);
                min-width: 50px;
                max-width: 50px;
            }
            
            QPushButton {
                background-color: transparent;
                border: none;
                color: rgba(255, 255, 255, 180);
                font-size: 16px;
                padding: 8px;
                border-radius: 4px;
                text-align: center;
            }
            
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 30);
            }
            
            QPushButton:checked {
                background-color: rgba(70, 130, 180, 120);
                color: white;
            }
        """
        self.setStyleSheet(style)
    
    def add_button(self, button_id: str, icon_text: str, tooltip: str = "") -> QPushButton:
        """
        添加侧边栏按钮
        
        Args:
            button_id: 按钮ID
            icon_text: 图标文本（可以是emoji或字体图标）
            tooltip: 工具提示文本
            
        Returns:
            QPushButton: 创建的按钮
        """
        button = QPushButton(icon_text)
        button.setObjectName(f"sidebarButton_{button_id}")
        button.setCheckable(True)
        # 不再使用标准tooltip，而是存储在字典中供自定义提示使用
        self._button_tooltips[button_id] = tooltip
        button.setFixedSize(QSize(32, 32))
        button.clicked.connect(lambda: self._on_button_clicked(button_id))
        
        # 连接鼠标事件
        button.installEventFilter(self)
        
        self._buttons[button_id] = button
        
        # 获取主布局并添加按钮
        main_layout = self.layout()
        if main_layout:
            main_layout.addWidget(button)
        
        return button
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理按钮的鼠标事件"""
        if isinstance(obj, QPushButton):
            # 找到对应的按钮ID
            button_id = None
            for bid, btn in self._buttons.items():
                if btn == obj:
                    button_id = bid
                    break
            
            if button_id:
                if event.type() == QEvent.Type.Enter:
                    self._on_button_enter(button_id)
                    return True
                elif event.type() == QEvent.Type.Leave:
                    self._on_button_leave(button_id)
                    return True
        
        return super().eventFilter(obj, event)
    
    def _on_button_enter(self, button_id: str):
        """按钮鼠标进入事件"""
        self._hovered_button_id = button_id
        self._hover_timer.start(self._hover_delay)
    
    def _on_button_leave(self, button_id: str):
        """按钮鼠标离开事件"""
        if self._hovered_button_id == button_id:
            self._hovered_button_id = None
            self._hover_timer.stop()
            self._tooltip_widget.hide_tooltip()
    
    def _show_tooltip(self):
        """显示悬浮提示"""
        if self._hovered_button_id and self._hovered_button_id in self._button_tooltips:
            tooltip_text = self._button_tooltips[self._hovered_button_id]
            if tooltip_text:
                # 计算提示位置：在按钮右侧
                button = self._buttons[self._hovered_button_id]
                button_global_pos = button.mapToGlobal(QPoint(0, 0))
                
                # 提示位置：按钮右侧 + 一些偏移
                tooltip_x = button_global_pos.x() + button.width() + 8
                tooltip_y = button_global_pos.y() + (button.height() - self._tooltip_widget.height()) // 2
                
                self._tooltip_widget.show_tooltip(tooltip_text, QPoint(tooltip_x, tooltip_y))
    
    def _on_button_clicked(self, button_id: str):
        """处理按钮点击事件"""
        # 如果点击的是当前选中的按钮，取消选择
        if button_id == self._current_view:
            self._deselect_current()
            self.view_deselected.emit()
        else:
            # 选择新按钮
            self._select_button(button_id)
            self.view_selected.emit(button_id)
    
    def _select_button(self, button_id: str):
        """选择指定按钮"""
        if button_id not in self._buttons:
            return
        
        # 取消所有按钮的选中状态
        for btn in self._buttons.values():
            btn.setChecked(False)
        
        # 选中指定按钮
        self._buttons[button_id].setChecked(True)
        self._current_view = button_id
    
    def _deselect_current(self):
        """取消当前选中的按钮"""
        if self._current_view in self._buttons:
            self._buttons[self._current_view].setChecked(False)
        self._current_view = ""
    
    def get_current_view(self) -> str:
        """获取当前选中的视图ID"""
        return self._current_view
    
    def select_view(self, view_id: str):
        """程序化选择视图"""
        if view_id in self._buttons:
            self._select_button(view_id)
            self.view_selected.emit(view_id)
    
    def deselect_view(self):
        """程序化取消选择"""
        self._deselect_current()
        self.view_deselected.emit()
    
    
    def on_mount(self):
        """组件挂载时的回调方法"""
        # 禁用鼠标事件穿透，确保侧边栏可以正常接收点击事件
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # 为所有子组件也禁用鼠标事件穿透
        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            
        # 特别确保按钮可以接收事件
        for button in self._buttons.values():
            button.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """重写鼠标按下事件，确保能接收到点击事件"""
        # 由于挂载区域设置了WA_TransparentForMouseEvents=True，
        # 我们需要手动处理鼠标事件
        super().mousePressEvent(event)
    
    def event(self, event: QEvent) -> bool:
        """重写事件处理，确保按钮点击事件能正常工作"""
        if event.type() == QEvent.Type.MouseButtonPress:
            # 确保鼠标事件能被正确处理
            return super().event(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            return super().event(event)
        elif event.type() == QEvent.Type.MouseMove:
            return super().event(event)
        else:
            return super().event(event)