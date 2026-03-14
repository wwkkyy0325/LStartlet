"""
磨砂玻璃效果窗口组件
负责具体的窗口行为和交互逻辑
"""

from typing import Optional, Callable

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QPaintEvent, QMouseEvent, QCloseEvent, QEnterEvent
from PySide6.QtCore import Qt, QPoint, QRect, QEvent, QSize
from ui.components.cursor_widget import CursorWidget


class FrostedGlassWindow(QWidget):
    """
    透明磨砂玻璃效果的窗口
    使用半透明背景和模糊效果实现磨砂玻璃视觉
    """
    
    def __init__(self, parent: Optional[QWidget] = None, on_close_callback: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self._drag_position: QPoint = QPoint()
        self._resizing: bool = False
        self._resize_edge: str = ""
        self._edge_threshold: int = 20  # 边缘检测阈值，增加到 20px 以便更容易触发
        self._initial_geometry: Optional[QRect] = None  # 初始窗口几何信息
        self._initial_mouse_pos: Optional[QPoint] = None  # 初始鼠标位置
        self._cursor_changeded: bool = False  # 标记光标是否被改变
        self._on_close_callback = on_close_callback  # 窗口关闭回调
        self._mouse_in_window: bool = False  # 标记鼠标是否在窗口内
        self._mouse_pos: QPoint = QPoint()  # 当前鼠标位置（相对于窗口）
        self._cursor_widget: Optional[QWidget] = None  # 光点widget
        self._is_maximized_state: bool = False  # 标记窗口是否处于最大化状态
        self._normal_geometry: Optional[QRect] = None  # 保存正常状态下的窗口几何信息
        self._drag_disabled_until: float = 0  # 禁用拖拽直到的时间戳
        
        # 初始化窗口边框位置和大小相关属性
        self._window_geometry: Optional[QRect] = None
        self._window_frame_geometry: Optional[QRect] = None
        self._window_position: Optional[QPoint] = None
        self._window_size: Optional[QSize] = None
        self._frame_position: Optional[QPoint] = None
        self._frame_size: Optional[QSize] = None
        
        self._setup_ui()
        self._apply_frosted_glass_style()
        # 创建光点widget
        self._create_cursor_widget()
        # 启用鼠标追踪以支持实时鼠标位置检测
        self.setMouseTracking(True)
        # 确保所有子widget也启用鼠标追踪
        self._enable_mouse_tracking_recursive(self)
    
    def _enable_mouse_tracking_recursive(self, widget: QWidget):
        """递归启用所有子widget的鼠标追踪"""
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)
    
    def update_mouse_state_via_tick(self):
        """通过系统的tick更新鼠标状态"""
        try:
            # 获取当前鼠标全局位置
            from PySide6.QtGui import QCursor
            global_pos = QCursor.pos()
            
            # 获取并存储窗口边框位置和大小信息，供后续操作使用
            self._window_geometry = self.geometry()
            self._window_frame_geometry = self.frameGeometry()
            self._window_position = self._window_geometry.topLeft()
            self._window_size = self._window_geometry.size()
            self._frame_position = self._window_frame_geometry.topLeft()
            self._frame_size = self._window_frame_geometry.size()
            
            # 检查鼠标是否在窗口内
            is_mouse_in_window = self._window_geometry.contains(global_pos)
            
            # 更新鼠标在窗口内的状态
            if is_mouse_in_window != self._mouse_in_window:
                self._mouse_in_window = is_mouse_in_window
            
            # 如果鼠标在窗口内，更新鼠标相对于窗口的位置并显示光点
            if self._mouse_in_window:
                self._mouse_pos = self.mapFromGlobal(global_pos)
                if hasattr(self, '_cursor_widget') and self._cursor_widget:
                    self._update_cursor_widget_position()
            else:
                # 鼠标不在窗口内，隐藏光点
                if hasattr(self, '_cursor_widget') and self._cursor_widget:
                    self._cursor_widget.hide()
                    
        except Exception:
            # 静默处理异常
            pass
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """窗口关闭事件 - 清理资源"""
        if self._on_close_callback:
            self._on_close_callback()
        super().closeEvent(event)
    
    def _setup_ui(self):
        """设置基础 UI"""
        # 设置窗口属性
        self.setWindowTitle("OCR 文字识别系统")
        self.resize(800, 600)
        # 移除最小尺寸限制
        # self.setMinimumSize(400, 300)
        
        # 启用透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 无边框窗口（保留系统按钮）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinMaxButtonsHint
        )
        
        # 创建主布局 - 整体容器（移除边距，让容器填满整个窗口）
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏区域（可拖动）
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        # 标题标签
        title_label = QLabel("OCR 文字识别系统")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 最小化按钮
        min_btn = QLabel("─")
        min_btn.setObjectName("minButton")
        min_btn.mousePressEvent = self._handle_minimize_click  # type: ignore
        title_layout.addWidget(min_btn)
        
        # 最大化/恢复按钮
        self.max_restore_btn = QLabel("□")
        self.max_restore_btn.setObjectName("maxRestoreButton")
        self.max_restore_btn.mousePressEvent = self._toggle_maximize_restore  # type: ignore
        title_layout.addWidget(self.max_restore_btn)
        
        # 关闭按钮
        close_btn = QLabel("×")
        close_btn.setObjectName("closeButton")
        close_btn.mousePressEvent = self._handle_close_click  # type: ignore
        title_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加内容提示
        content_label = QLabel("主内容区域\n\n磨砂玻璃效果已启用")
        content_label.setObjectName("contentLabel")
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(content_label)
        
        main_layout.addWidget(content_widget)
        
        # 设置主布局 - 使用零边距确保容器填满窗口
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 修改为零边距
        layout.setSpacing(0)
        layout.addWidget(main_container)
    
    def _apply_frosted_glass_style(self):
        """应用磨砂玻璃样式"""
        # 整体容器样式 - 统一的圆角边框
        self.setStyleSheet("""
            QWidget#mainContainer {
                background-color: rgba(30, 30, 50, 180);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            
            QWidget#titleBar {
                background-color: rgba(255, 255, 255, 10);
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
            
            QLabel#titleLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
            }
            
            QLabel#minButton, QLabel#maxRestoreButton, QLabel#closeButton {
                color: white;
                font-size: 20px;
                padding: 5px 10px;
                border-radius: 10px;
            }
            
            QLabel#minButton:hover, QLabel#maxRestoreButton:hover, QLabel#closeButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
            
            QLabel#closeButton:hover {
                background-color: rgba(255, 100, 100, 150);
            }
            
            QWidget#contentWidget {
                background-color: transparent;
            }
            
            QLabel#contentLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                padding: 20px;
            }
        """)
        
        # 移除最小尺寸设置
        # self.setMinimumWidth(400)
        # self.setMinimumHeight(300)
    
    def _get_resize_edge(self, pos: QPoint) -> str:
        """判断鼠标位置对应的调整边缘（仅四个角）"""
        x, y = pos.x(), pos.y()
        width, height = self.width(), self.height()
        
        # 只检测四个角
        if x <= self._edge_threshold and y <= self._edge_threshold:
            return "top-left"
        elif x >= width - self._edge_threshold and y <= self._edge_threshold:
            return "top-right"
        elif x <= self._edge_threshold and y >= height - self._edge_threshold:
            return "bottom-left"
        elif x >= width - self._edge_threshold and y >= height - self._edge_threshold:
            return "bottom-right"
        
        return ""
    
    def _update_cursor(self, pos: QPoint):
        """根据鼠标位置更新光标样式（仅在拖动时使用）"""
        if not self._resizing:
            # 未拖动时恢复默认光标
            if self._cursor_changeded:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self._cursor_changeded = False
            return
        
        # 拖动时根据边缘方向设置对应的光标
        edge = self._get_resize_edge(pos)
        
        cursor_map = {
            "top-left": Qt.CursorShape.SizeFDiagCursor,      # ↖↘ 对角线
            "top-right": Qt.CursorShape.SizeBDiagCursor,     # ↙↗ 对角线
            "bottom-left": Qt.CursorShape.SizeBDiagCursor,   # ↙↗ 对角线
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,  # ↖↘ 对角线
        }
        
        if edge:
            self.setCursor(cursor_map[edge])
            self._cursor_changeded = True
    
    def _is_click_on_title_buttons(self, pos: QPoint) -> bool:
        """检查点击位置是否在标题栏按钮区域"""
        from PySide6.QtWidgets import QLabel
        
        # 将点击位置转换为全局坐标
        global_pos = self.mapToGlobal(pos)
        
        # 获取所有标题栏按钮
        min_btn = self.findChild(QLabel, "minButton")
        max_btn = getattr(self, 'max_restore_btn', None)
        close_btn = self.findChild(QLabel, "closeButton")
        
        # 检查是否点击在任何一个按钮上（使用全局坐标）
        buttons: list[QLabel] = []
        if min_btn is not None:
            buttons.append(min_btn)
        if max_btn is not None:
            buttons.append(max_btn)
        if close_btn is not None:
            buttons.append(close_btn)
            
        for button in buttons:
            # 获取按钮的全局几何区域
            button_global_rect = button.geometry()
            button_global_rect.moveTopLeft(button.mapToGlobal(QPoint(0, 0)))
            if button_global_rect.contains(global_pos):
                return True
                
        return False
    
    def _disable_drag_for_duration(self, duration: float):
        """禁用拖拽指定时长（秒）"""
        import time
        self._drag_disabled_until = time.time() + duration
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件 - 开始拖动或调整大小"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            edge = self._get_resize_edge(pos)
            
            if edge:
                # 开始调整大小
                self._resizing = True
                self._resize_edge = edge
                # 保存初始窗口几何信息
                self._initial_geometry = self.geometry()
                # 保存初始鼠标全局位置
                self._initial_mouse_pos = event.globalPos()
                # 立即设置光标为调整样式
                cursor_map = {
                    "top-left": Qt.CursorShape.SizeFDiagCursor,
                    "top-right": Qt.CursorShape.SizeBDiagCursor,
                    "bottom-left": Qt.CursorShape.SizeBDiagCursor,
                    "bottom-right": Qt.CursorShape.SizeFDiagCursor,
                }
                self.setCursor(cursor_map[edge])
                self._cursor_changeded = True
                
                # 更新几何信息到tick系统维护的状态
                if hasattr(self, '_window_geometry'):
                    self._window_geometry = self.geometry()
                    self._window_frame_geometry = self.frameGeometry()
                    self._window_position = self._window_geometry.topLeft()
                    self._window_size = self._window_geometry.size()
                    self._frame_position = self._window_frame_geometry.topLeft()
                    self._frame_size = self._window_frame_geometry.size()
            else:
                # 检查是否点击在标题栏按钮上，如果是则不触发拖拽
                if not self._is_click_on_title_buttons(pos):
                    # 检查拖拽是否被禁用
                    import time
                    if time.time() < self._drag_disabled_until:
                        # 拖拽被禁用，不执行拖拽逻辑
                        pass
                    else:
                        # 开始拖动窗口
                        self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - 拖动窗口或调整大小"""
        # 仍然保存鼠标位置用于交互操作
        self._mouse_pos = event.pos()
        
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._resizing and self._resize_edge and self._initial_geometry and self._initial_mouse_pos:
                # 计算鼠标移动的增量（相对于初始位置）
                delta: QPoint = event.globalPos() - self._initial_mouse_pos
                
                # 从初始几何信息开始计算
                new_geometry = QRect(self._initial_geometry)
                
                edge = self._resize_edge
                
                # 处理左右边界
                if "left" in edge:
                    # 左边调整：x随鼠标移动，宽度相应变化
                    new_x = new_geometry.x() + delta.x()
                    new_width = new_geometry.width() - delta.x()
                    # 确保宽度至少为最小值（311像素，根据错误日志中的minimum size）
                    if new_width < 311:
                        new_width = 311
                        # 固定右边缘位置：右边缘 = 初始右边缘位置
                        right_edge = self._initial_geometry.x() + self._initial_geometry.width()
                        new_x = right_edge - new_width
                    new_geometry.setX(new_x)
                    new_geometry.setWidth(new_width)
                
                if "right" in edge:
                    # 右边调整：仅改变宽度
                    new_width = new_geometry.width() + delta.x()
                    if new_width < 311:
                        new_width = 311
                    new_geometry.setWidth(new_width)
                
                # 处理上下边界
                if "top" in edge:
                    # 上边调整：y随鼠标移动，高度相应变化
                    new_y = new_geometry.y() + delta.y()
                    new_height = new_geometry.height() - delta.y()
                    # 确保高度至少为最小值（180像素，根据错误日志中的minimum size）
                    if new_height < 180:
                        new_height = 180
                        # 固定下边缘位置：下边缘 = 初始下边缘位置
                        bottom_edge = self._initial_geometry.y() + self._initial_geometry.height()
                        new_y = bottom_edge - new_height
                    new_geometry.setY(new_y)
                    new_geometry.setHeight(new_height)
                
                if "bottom" in edge:
                    # 下边调整：仅改变高度
                    new_height = new_geometry.height() + delta.y()
                    if new_height < 180:
                        new_height = 180
                    new_geometry.setHeight(new_height)
                
                self.setGeometry(new_geometry)
                # 拖动过程中不需要更新光标，保持mousePressEvent中设置的光标样式
                # self._update_cursor(event.pos())
            
            else:
                # 拖动窗口
                self.move(event.globalPos() - self._drag_position)
            
            event.accept()
        else:
            # 鼠标未按下时，更新光标样式（用于悬停检测）
            self._update_cursor_for_hover(event.pos())
        
        # 为了确保交互时的响应性，在鼠标移动时也更新几何状态
        # 这样即使tick系统有延迟，用户交互时也能立即更新几何信息
        if hasattr(self, '_window_geometry'):
            self._window_geometry = self.geometry()
            self._window_frame_geometry = self.frameGeometry()
            self._window_position = self._window_geometry.topLeft()
            self._window_size = self._window_geometry.size()
            self._frame_position = self._window_frame_geometry.topLeft()
            self._frame_size = self._window_frame_geometry.size()
        
        # 更新光点位置（无论是否按下鼠标按钮）
        if hasattr(self, '_cursor_widget') and self._cursor_widget:
            self._update_cursor_widget_position()
    
    def _update_cursor_for_hover(self, pos: QPoint):
        """根据鼠标悬停位置更新光标样式"""
        edge = self._get_resize_edge(pos)
        
        if edge:
            cursor_map = {
                "top-left": Qt.CursorShape.SizeFDiagCursor,
                "top-right": Qt.CursorShape.SizeBDiagCursor,
                "bottom-left": Qt.CursorShape.SizeBDiagCursor,
                "bottom-right": Qt.CursorShape.SizeFDiagCursor,
            }
            self.setCursor(cursor_map[edge])
        else:
            # 不在边缘区域，恢复默认光标
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._resizing = False
            self._resize_edge = ""
            # 恢复默认光标
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._cursor_changeded = False
            
            # 更新几何信息到tick系统维护的状态
            if hasattr(self, '_window_geometry'):
                self._window_geometry = self.geometry()
                self._window_frame_geometry = self.frameGeometry()
                self._window_position = self._window_geometry.topLeft()
                self._window_size = self._window_geometry.size()
                self._frame_position = self._window_frame_geometry.topLeft()
                self._frame_size = self._window_frame_geometry.size()
            
            event.accept()
    
    def _update_cursor_widget_position(self):
        """更新光点widget位置"""
        if self._cursor_widget:
            if self._mouse_in_window:
                # 计算光点中心位置（鼠标位置减去半径）
                # 光点widget大小为20x20，所以半径是10
                x = self._mouse_pos.x() - 10
                y = self._mouse_pos.y() - 10
                self._cursor_widget.move(x, y)
                self._cursor_widget.show()
            else:
                self._cursor_widget.hide()
    
    def enterEvent(self, event: QEnterEvent) -> None:
        """鼠标进入窗口事件"""
        self._mouse_in_window = True
        if self._cursor_widget:
            self._update_cursor_widget_position()
        super().enterEvent(event)
    
    def leaveEvent(self, event: QEvent) -> None:
        """鼠标离开窗口事件"""
        self._mouse_in_window = False
        if self._cursor_widget:
            self._update_cursor_widget_position()
        super().leaveEvent(event)
    
    def paintEvent(self, event: QPaintEvent):
        """重写绘制事件以实现磨砂效果"""
        # 现在由样式表处理外观，不需要手动绘制光点
        super().paintEvent(event)
    
    def _create_cursor_widget(self):
        """创建光点widget"""
        self._cursor_widget = CursorWidget(self)
        self._cursor_widget.hide()
    
    def _handle_minimize_click(self, event: QMouseEvent):
        """处理最小化按钮点击"""
        self._disable_drag_for_duration(1.25)
        self.showMinimized()

    def _handle_close_click(self, event: QMouseEvent):
        """处理关闭按钮点击"""
        self._disable_drag_for_duration(1.25)
        self.close()
    
    def _toggle_maximize_restore(self, event: QMouseEvent):
        """切换最大化/恢复状态"""
        # 禁用拖拽1.25秒
        self._disable_drag_for_duration(1.25)
        
        if self._is_maximized_state:
            # 恢复到正常状态
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            self._is_maximized_state = False
            self.max_restore_btn.setText("□")
        else:
            # 最大化窗口
            # 保存当前正常状态的几何信息
            self._normal_geometry = self.geometry()
            # 获取屏幕可用几何区域（排除任务栏等）
            screen_geometry = self.screen().availableGeometry()
            self.setGeometry(screen_geometry)
            self._is_maximized_state = True
            self.max_restore_btn.setText("❐")