"""
设置弹窗UI组件
提供自定义磨砂玻璃效果的设置对话框，具有与主窗口相同的底层架构
"""

from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QApplication
)
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QMouseEvent

# 导入简化挂载区域组件
from ui.components.simple_mount_area import SimpleMountAreaWidget
# 导入侧边栏组件
from ui.components.sidebar import SidebarWidget


class SettingsDialog(QWidget):
    """
    自定义磨砂玻璃效果的设置对话框
    使用与主窗口相同的底层架构，支持左侧菜单栏和挂载组件
    """
    
    def __init__(self, parent: Optional[QWidget] = None, on_close_callback: Optional[Callable[[], None]] = None):
        # 使用传入的parent作为父窗口，确保正确的层级关系
        super().__init__(parent)
        self._drag_position: QPoint = QPoint()
        self._on_close_callback = on_close_callback
        self._dragging: bool = False  # 添加拖动状态标志
        
        self._setup_ui()
        self._apply_frosted_glass_style()
        self.setMouseTracking(True)
        
        # 设置窗口属性
        self.setWindowTitle("设置")
        
        # 启用透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 禁用鼠标事件穿透，确保能接收点击事件
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # 无边框窗口 - 与主窗口保持一致
        # 移除Window标志，因为现在是子窗口
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowCloseButtonHint
        )
    
    def _setup_ui(self):
        """设置基础 UI - 与主窗口保持一致的结构"""
        # 创建主容器
        main_container = QFrame()
        main_container.setObjectName("mainContainer")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏 - 与主窗口相同的自定义标题栏
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(35)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_label = QLabel("设置")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 关闭按钮 - 与主窗口相同的样式
        close_btn = QLabel("×")
        close_btn.setObjectName("closeButton")
        close_btn.mousePressEvent = self._handle_close_click  # type: ignore
        title_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # === 重构内容区域布局 ===
        # 使用水平布局支持左侧侧边栏、中央内容区
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 0, 10, 10)  # 左右保留边距，上下无边距
        content_layout.setSpacing(0)
        
        # 左侧侧边栏区域（专用区域，固定宽度50px）
        self._left_sidebar_area = QWidget()
        self._left_sidebar_area.setObjectName("leftSidebarArea")
        self._left_sidebar_area.setFixedWidth(50)
        
        # 创建侧边栏组件
        self._sidebar = SidebarWidget()
        sidebar_layout = QVBoxLayout(self._left_sidebar_area)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(self._sidebar)
        
        content_layout.addWidget(self._left_sidebar_area)
        
        # 中央内容区域 - 使用与主窗口相同的挂载区域
        self._mount_area = SimpleMountAreaWidget()
        self._mount_area.setObjectName("contentWidget")
        content_layout.addWidget(self._mount_area)
        
        main_layout.addLayout(content_layout)
        # === 布局重构完成 ===
        
        # 设置主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(main_container)
    
    def _apply_frosted_glass_style(self):
        """应用与主窗口相同的磨砂玻璃样式"""
        style = """
            QWidget#mainContainer {
                background-color: rgba(30, 30, 50, 180);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            
            QWidget#titleBar {
                background-color: rgba(255, 255, 255, 10);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            
            QLabel#titleLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            
            QLabel#closeButton {
                color: white;
                font-size: 16px;
                width: 30px;
                height: 30px;
                padding: 5px;
                border-radius: 4px;
                text-align: center;
            }
            
            QLabel#closeButton:hover {
                background-color: rgba(255, 0, 0, 50);
            }
            
            QWidget#contentWidget {
                background-color: transparent;
                border: none;
            }
            
            QWidget#leftSidebarArea {
                background-color: transparent;
                border: none;
            }
        """
        self.setStyleSheet(style)
    
    def _handle_close_click(self, event: QMouseEvent) -> None:
        """处理关闭按钮点击"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.close()
    
    def _is_click_on_title_bar(self, pos: QPoint) -> bool:
        """检查点击位置是否在标题栏区域"""
        title_bar = self.findChild(QWidget, "titleBar")
        if title_bar is not None:
            # 将标题栏的局部坐标转换为窗口坐标
            title_bar_pos = title_bar.pos()
            title_bar_rect = QRect(title_bar_pos, title_bar.size())
            return title_bar_rect.contains(pos)
        return False

    def _is_click_on_title_buttons(self, pos: QPoint) -> bool:
        """检查点击位置是否在标题栏按钮区域"""
        from PySide6.QtWidgets import QLabel
        
        # 将点击位置转换为全局坐标
        global_pos = self.mapToGlobal(pos)
        
        # 获取关闭按钮
        close_btn = self.findChild(QLabel, "closeButton")
        
        # 检查是否点击在关闭按钮上（使用全局坐标）
        if close_btn is not None:
            # 获取按钮的全局几何区域
            button_global_rect = close_btn.geometry()
            button_global_rect.moveTopLeft(close_btn.mapToGlobal(QPoint(0, 0)))
            if button_global_rect.contains(global_pos):
                return True
                
        return False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件 - 支持拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            # 检查是否点击在标题栏区域且不在按钮上，只有标题栏可以拖动
            if self._is_click_on_title_bar(pos) and not self._is_click_on_title_buttons(pos):
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self._dragging = True
            else:
                # 点击内容区域或其他区域，不执行拖动
                self._dragging = False
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动事件 - 实现拖拽"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._dragging:
                self.move(event.globalPosition().toPoint() - self._drag_position)
                event.accept()
            else:
                super().mouseMoveEvent(event)
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件 - 重置拖动状态"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)
    
    def show(self):
        """重写show方法，作为子窗口显示"""
        # 作为子窗口，不需要复杂的定位逻辑
        # 设置合理的默认大小
        parent = self.parent()
        if parent and parent.isVisible():
            # 基于父窗口大小设置对话框大小
            parent_rect = parent.geometry()
            dialog_width = int(parent_rect.width() * 0.8)
            dialog_height = int(parent_rect.height() * 0.8)
            self.resize(dialog_width, dialog_height)
            
            # 正确计算居中位置：相对于父窗口的屏幕位置
            parent_global_pos = parent.mapToGlobal(QPoint(0, 0))
            x = parent_global_pos.x() + (parent_rect.width() - dialog_width) // 2
            y = parent_global_pos.y() + (parent_rect.height() - dialog_height) // 2
            self.move(x, y)
        else:
            # 如果没有父窗口或父窗口不可见，使用默认大小并居中显示在屏幕中央
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                dialog_width = int(screen_geometry.width() * 0.8)
                dialog_height = int(screen_geometry.height() * 0.8)
                self.resize(dialog_width, dialog_height)
                
                x = (screen_geometry.width() - dialog_width) // 2
                y = (screen_geometry.height() - dialog_height) // 2
                self.move(x, y)
            else:
                # 最后的备选方案
                self.resize(800, 600)
        
        super().show()
    
    def closeEvent(self, event) -> None:
        """关闭事件"""
        if self._on_close_callback:
            self._on_close_callback()
        super().closeEvent(event)
    
    def get_mount_area(self) -> SimpleMountAreaWidget:
        """获取挂载区域，用于外部挂载组件"""
        return self._mount_area
    
    def get_sidebar(self) -> SidebarWidget:
        """获取侧边栏组件"""
        return self._sidebar