"""
简化挂载区域组件
只支持单个挂载点，便于组件挂载和管理
增强的生命周期管理：
- 支持组件挂载/卸载时的生命周期回调
- 自动管理旧组件的卸载
- 详细的日志记录
"""

from typing import Optional, Any, Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QScrollArea
from PySide6.QtCore import Qt, Signal
from .base_component import BaseComponent


class SimpleMountAreaWidget(QWidget):
    """简化挂载区域控件"""
    
    # 信号定义
    component_mounted = Signal(object)  # 组件对象
    component_unmounted = Signal(object)  # 组件对象
    area_cleared = Signal()  # 区域已清空
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # 创建滚动区域 - 这是关键！确保内容不会影响父容器尺寸
        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("mountAreaScroll")
        self._scroll_area.setWidgetResizable(True)  # 内容随滚动区域调整大小
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setStyleSheet("""
            QScrollArea#mountAreaScroll {
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QScrollArea#mountAreaScroll > QWidget {
                background-color: transparent;
            }
            /* 确保滚动条样式透明 */
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 80);
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 120);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                width: 0px;
                height: 0px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 80);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 120);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                width: 0px;
                height: 0px;
            }
        """)
        
        # 创建堆叠窗口用于内容管理
        self._stack = QStackedWidget()
        self._stack.setObjectName("mountAreaStack")
        self._stack.setStyleSheet("""
            background: transparent;
            border: none;
            margin: 0px;
            padding: 0px;
        """)
        
        # 将堆叠窗口设置为滚动区域的内容
        self._scroll_area.setWidget(self._stack)
        
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._scroll_area)
        self.setLayout(layout)
        
        self._current_component: Optional[QWidget] = None
    
    def mount_component(self, component: QWidget) -> bool:
        """
        挂载组件到挂载区域
        
        Args:
            component: 要挂载的组件
            
        Returns:
            bool: 是否成功挂载
        """
        try:
            if not isinstance(component, QWidget):
                from core.logger import error
                error(f"挂载组件失败: 组件必须是QWidget实例，当前类型: {type(component)}")
                return False
                
            # 如果已有组件，先卸载
            if self._current_component is not None:
                self.unmount_component()
            
            # 移除鼠标事件透明设置，让组件能正常接收鼠标事件
            # component.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            
            # 设置组件父级
            component.setParent(self._stack)
            
            # 添加到堆叠窗口
            self._stack.addWidget(component)
            self._stack.setCurrentWidget(component)
            
            # 更新当前组件引用
            self._current_component = component
            
            # 触发挂载信号
            self.component_mounted.emit(component)
            
            # 调用组件的on_mount方法（如果存在）
            if hasattr(component, 'on_mount'):
                try:
                    component.on_mount()
                except Exception as e:
                    from core.logger import warning
                    warning(f"组件 on_mount 方法执行失败: {e}")
            
            from core.logger import info
            info(f"组件挂载成功: {component.__class__.__name__}")
            return True
            
        except Exception as e:
            from core.logger import error
            error(f"挂载组件时发生错误: {e}")
            return False
    
    def unmount_component(self) -> bool:
        """
        卸载当前组件
        
        Returns:
            bool: 是否成功卸载
        """
        try:
            if self._current_component is None:
                return True
                
            component = self._current_component
            
            # 调用组件的on_unmount方法（如果存在）
            if hasattr(component, 'on_unmount'):
                try:
                    component.on_unmount()
                except Exception as e:
                    from core.logger import warning
                    warning(f"组件 on_unmount 方法执行失败: {e}")
            
            # 从堆叠窗口移除
            self._stack.removeWidget(component)
            
            # 清理组件
            component.setParent(None)
            component.deleteLater()
            
            # 更新当前组件引用
            self._current_component = None
            
            # 触发卸载信号
            self.component_unmounted.emit(component)
            
            from core.logger import info
            info(f"组件卸载成功: {component.__class__.__name__}")
            return True
            
        except Exception as e:
            from core.logger import error
            error(f"卸载组件时发生错误: {e}")
            return False
    
    def clear_area(self) -> bool:
        """
        清空挂载区域
        
        Returns:
            bool: 是否成功清空
        """
        if self._current_component is None:
            return True
            
        return self.unmount_component()
    
    def get_current_component(self) -> Optional[QWidget]:
        """获取当前挂载的组件"""
        return self._current_component


class SimpleMountArea(BaseComponent):
    """简化挂载区域管理器"""
    
    def __init__(self, parent: Optional[QWidget] = None, component_id: Optional[str] = None):
        super().__init__(parent)
        self.component_id = component_id or f"component_{id(self)}"
        self._widget: Optional[QWidget] = SimpleMountAreaWidget(parent)

    def create_widget(self) -> QWidget:
        """创建挂载区域组件的widget"""
        if self._widget is None:
            from core.logger import error
            error("SimpleMountAreaWidget _widget is None in create_widget")
            raise RuntimeError("SimpleMountAreaWidget not initialized properly")
        return self._widget
    
    def mount_component(self, component: QWidget) -> bool:
        """挂载组件到挂载区域"""
        if self._widget is None:
            return False
        from typing import cast
        widget = cast(SimpleMountAreaWidget, self._widget)
        return widget.mount_component(component)

    def unmount_component(self) -> bool:
        """卸载当前组件"""
        if self._widget is None:
            return False
        from typing import cast
        widget = cast(SimpleMountAreaWidget, self._widget)
        return widget.unmount_component()