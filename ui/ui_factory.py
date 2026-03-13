"""
UI工厂模块
负责UI的创建、管理和生命周期控制
"""

import sys
from typing import Optional, Callable, cast

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QPaintEvent, QMouseEvent
from PySide6.QtCore import Qt, QPoint, QRect

from core.logger import info, error
from core.event.event_bus import EventBus
from core.event.events.ui_events import RenderProcessReadyEvent

# 修复导入路径
from ui.core.standard_window_manager import StandardWindowManager


class FrostedGlassWindow(QWidget):
    """
    透明磨砂玻璃效果的窗口
    使用半透明背景和模糊效果实现磨砂玻璃视觉
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drag_position: QPoint = QPoint()
        self._resizing: bool = False
        self._resize_edge: str = ""
        self._edge_threshold: int = 20  # 边缘检测阈值，增加到 20px 以便更容易触发
        self._initial_geometry: Optional[QRect] = None  # 初始窗口几何信息
        self._initial_mouse_pos: Optional[QPoint] = None  # 初始鼠标位置
        self._setup_ui()
        self._apply_frosted_glass_style()
    
    def _setup_ui(self):
        """设置基础 UI"""
        # 设置窗口属性
        self.setWindowTitle("OCR 应用 - 磨砂玻璃效果")
        self.resize(800, 600)
        self.setMinimumSize(400, 300)
        
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
        min_btn.mousePressEvent = lambda e: self.showMinimized()  # type: ignore
        title_layout.addWidget(min_btn)
        
        # 关闭按钮
        close_btn = QLabel("×")
        close_btn.setObjectName("closeButton")
        close_btn.mousePressEvent = lambda e: self.close()  # type: ignore
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
            
            QLabel#minButton, QLabel#closeButton {
                color: white;
                font-size: 20px;
                padding: 5px 10px;
                border-radius: 10px;
            }
            
            QLabel#minButton:hover, QLabel#closeButton:hover {
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
        
        # 设置最小透明度
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
    
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
        """根据鼠标位置更新光标样式"""
        edge = self._get_resize_edge(pos)
        
        cursor_map = {
            "top-left": Qt.CursorShape.SizeFDiagCursor,      # ↖↘ 对角线
            "top-right": Qt.CursorShape.SizeBDiagCursor,     # ↙↗ 对角线
            "bottom-left": Qt.CursorShape.SizeBDiagCursor,   # ↙↗ 对角线
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,  # ↖↘ 对角线
        }
        
        self.setCursor(cursor_map.get(edge, Qt.CursorShape.ArrowCursor))
        self._resize_edge = edge
    
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
            else:
                # 开始拖动窗口
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - 拖动窗口或调整大小"""
        # 先更新光标（无论是否按下）
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            self._update_cursor(event.pos())
        
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._resizing and self._resize_edge and self._initial_geometry and self._initial_mouse_pos:
                # 计算鼠标移动的增量（相对于初始位置）
                delta: QPoint = event.globalPos() - self._initial_mouse_pos
                
                # 从初始几何信息开始计算
                new_geometry = QRect(self._initial_geometry)
                
                edge = self._resize_edge
                
                # 处理左右边界
                if "left" in edge:
                    new_x: int = new_geometry.x() + delta.x()
                    new_width: int = new_geometry.width() - delta.x()
                    if new_width >= self.minimumWidth():
                        new_geometry.setX(new_x)
                        new_geometry.setWidth(new_width)
                
                if "right" in edge:
                    new_width = new_geometry.width() + delta.x()
                    if new_width >= self.minimumWidth():
                        new_geometry.setWidth(new_width)
                
                # 处理上下边界
                if "top" in edge:
                    new_y: int = new_geometry.y() + delta.y()
                    new_height: int = new_geometry.height() - delta.y()
                    if new_height >= self.minimumHeight():
                        new_geometry.setY(new_y)
                        new_geometry.setHeight(new_height)
                
                if "bottom" in edge:
                    new_height = new_geometry.height() + delta.y()
                    if new_height >= self.minimumHeight():
                        new_geometry.setHeight(new_height)
                
                self.setGeometry(new_geometry)
            
            else:
                # 拖动窗口
                self.move(event.globalPos() - self._drag_position)
            
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._resizing = False
            self._resize_edge = ""
            # 恢复光标检测
            self._update_cursor(event.pos())
            event.accept()
    
    def paintEvent(self, event: QPaintEvent):
        """重写绘制事件以实现磨砂效果"""
        # 现在由样式表处理外观，不需要手动绘制
        super().paintEvent(event)


class UIFactory:
    """UI工厂类，负责UI的创建和管理"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.custom_ui_callback: Optional[Callable[[], None]] = None
        self.qt_app: Optional[QApplication] = None
        
    def start_render_process(self, timeout: float = 5.0) -> bool:
        """启动 UI 渲染（实际是在主线程中创建 UI）"""
        try:
            info("开始初始化UI...")
            
            # 初始化 Qt 应用
            self.qt_app = QApplication(sys.argv)
            
            # 直接创建磨砂玻璃 UI
            self.create_frosted_glass_ui()
            
            return True
            
        except Exception as e:
            error(f"UI 初始化失败：{e}")
            return False
    
    def _create_default_ui(self) -> None:
        """创建默认 UI"""
        try:
            info("创建默认 UI...")
            ui_manager = StandardWindowManager()
            ui_manager.show()
            info("默认 UI 创建成功")
            
        except Exception as e:
            error(f"默认 UI 创建失败：{e}")
    
    def create_frosted_glass_ui(self) -> FrostedGlassWindow:
        """创建磨砂玻璃效果的自定义 UI"""
        try:
            info("创建磨砂玻璃效果 UI...")
            window = FrostedGlassWindow()
            window.show()
            info("磨砂玻璃 UI 创建成功")
            return window
            
        except Exception as e:
            error(f"磨砂玻璃 UI 创建失败：{e}")
            raise
    
    def _on_render_process_ready(self, event: RenderProcessReadyEvent) -> bool:
        """处理渲染进程准备就绪事件 - 此方法已废弃，UI 在 start_render_process 中直接创建"""
        try:
            info(f"接收到渲染进程准备就绪事件（事件监听模式），进程 ID: {event.process_id}")
            # 不再通过事件回调创建 UI，UI 已在 start_render_process 中创建
            return True
            
        except Exception as e:
            error(f"处理渲染进程准备就绪事件失败：{e}")
            return False
    
    def cleanup_resources(self) -> None:
        """清理 UI 相关资源"""
        try:
            info("开始清理 UI 资源...")
            # Qt 应用会在退出时自动清理
            info("UI 资源清理完成")
            
        except Exception as e:
            error(f"UI 资源清理过程中发生错误：{e}")
    
    def get_qt_app(self) -> Optional[QApplication]:
        """获取 Qt 应用实例"""
        return self.qt_app
    
    def register_event_listeners(self) -> None:
        """注册UI 相关的事件监听器"""
        try:
            # 监听渲染进程准备就绪事件
            self.event_bus.subscribe_lambda(
                RenderProcessReadyEvent.EVENT_TYPE,
                lambda event: self._on_render_process_ready(cast(RenderProcessReadyEvent, event)),
                "render_process_ready_handler"
            )
            
            info("UI事件监听器注册完成")
            
        except Exception as e:
            error(f"UI事件监听器注册失败：{e}")
