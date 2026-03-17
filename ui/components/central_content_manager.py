from typing import Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QResizeEvent


class CentralContentManager(QWidget):
    """
    中央内容管理器
    管理中央挂载区的内容显示，支持动态布局：
    - 单个组件：独占整个区域
    - 两个组件：水平均分，顶天立地
    """
    
    content_changed = Signal(str)  # 当前内容改变时触发
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_content_id = ""
        self._content_widgets: Dict[str, QWidget] = {}
        self._permanent_widget: Optional[QWidget] = None  # 常驻组件（图片查看器）
        self._main_layout: Optional[QVBoxLayout] = None
        self._current_layout: Optional[QHBoxLayout] = None
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI布局"""
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # 默认情况下不显示任何内容
        self.hide()
    
    def add_content(self, content_id: str, widget: QWidget, is_permanent: bool = False) -> bool:
        """
        添加内容组件
        
        Args:
            content_id: 内容ID
            widget: 内容组件
            is_permanent: 是否为常驻组件
            
        Returns:
            bool: 是否成功添加
        """
        if content_id in self._content_widgets or (is_permanent and self._permanent_widget is not None):
            return False
        
        if is_permanent:
            self._permanent_widget = widget
            widget.setParent(self)
            # 不再使用splitter，直接设置父容器
        else:
            self._content_widgets[content_id] = widget
            widget.setParent(self)
            widget.hide()  # 初始隐藏非常驻组件
            
        return True
    
    def show_content(self, content_id: str):
        """显示指定内容，与常驻组件水平布局"""
        # 清理当前布局
        self._clear_current_layout()
        
        if self._permanent_widget is None:
            # 如果没有常驻组件，直接显示指定内容
            if content_id not in self._content_widgets:
                self.hide()
                return
            
            # 单个组件：独占整个区域
            self._current_layout = QHBoxLayout()
            self._current_layout.setContentsMargins(0, 0, 0, 0)
            self._current_layout.setSpacing(0)
            self._main_layout.addLayout(self._current_layout)
            
            # 完全由布局管理器控制，不设置任何大小限制
            widget = self._content_widgets[content_id]
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            self._current_layout.addWidget(widget)
            widget.show()
            self._current_content_id = content_id
            self.show()
            self.content_changed.emit(content_id)
            return
        
        # 有常驻组件的情况
        if content_id not in self._content_widgets:
            # 只显示常驻组件，独占整个空间
            self._current_layout = QHBoxLayout()
            self._current_layout.setContentsMargins(0, 0, 0, 0)
            self._current_layout.setSpacing(0)
            self._main_layout.addLayout(self._current_layout)
            
            # 完全由布局管理器控制
            self._permanent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            self._current_layout.addWidget(self._permanent_widget)
            self._permanent_widget.show()
            self._current_content_id = ""
            self.show()
            self.content_changed.emit("")
            return
        
        # 显示指定内容和常驻组件：资源管理器最大30%，图片查看器贪心占用剩余空间
        self._current_layout = QHBoxLayout()
        self._current_layout.setContentsMargins(0, 0, 0, 0)
        self._current_layout.setSpacing(0)  # 移除间距，实现无缝分割
        self._main_layout.addLayout(self._current_layout)
        
        content_widget = self._content_widgets[content_id]
        permanent_widget = self._permanent_widget
        
        # 设置大小策略，让布局管理器完全控制
        content_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        permanent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 添加到布局
        self._current_layout.addWidget(content_widget)
        self._current_layout.addWidget(permanent_widget)
        
        content_widget.show()
        permanent_widget.show()
        
        # 设置拉伸因子：资源管理器占30%（拉伸因子3），图片查看器占70%（拉伸因子7）
        # 这样实现了资源管理器最大30%，图片查看器贪心占用剩余空间
        self._current_layout.setStretch(0, 3)  # 资源管理器：3份
        self._current_layout.setStretch(1, 7)  # 图片查看器：7份（贪心）
        
        self._current_content_id = content_id
        self.show()
        self.content_changed.emit(content_id)
    
    def hide_content(self):
        """隐藏所有可切换内容，只显示常驻组件"""
        self._clear_current_layout()
        
        if self._permanent_widget is not None:
            # 只显示常驻组件
            self._current_layout = QHBoxLayout()
            self._current_layout.setContentsMargins(0, 0, 0, 0)
            self._current_layout.setSpacing(0)
            self._main_layout.addLayout(self._current_layout)
            
            # 完全由布局管理器控制
            self._permanent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            self._current_layout.addWidget(self._permanent_widget)
            self._permanent_widget.show()
            self._current_content_id = ""
            self.show()
            self.content_changed.emit("")
        else:
            # 没有常驻组件，隐藏整个管理器
            self.hide()
            self._current_content_id = ""
            self.content_changed.emit("")
    
    def get_current_content(self) -> str:
        """获取当前显示的内容ID"""
        return self._current_content_id
    
    def _clear_current_layout(self):
        """清理当前布局"""
        if self._current_layout is not None:
            while self._current_layout.count():
                item = self._current_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            self._main_layout.removeItem(self._current_layout)
            self._current_layout = None
    
    # 移除 resizeEvent 方法，因为 QHBoxLayout 会自动处理大小调整
    # 不需要手动设置组件大小
    
    def create_default_contents(self):
        """创建默认的内容组件"""
        # 资源管理器内容 - 使用目录查看组件
        from ui.components.directory_viewer import DirectoryViewerComponent
        explorer_content = DirectoryViewerComponent()
        explorer_widget = explorer_content.create_widget()
        self.add_content("explorer", explorer_widget)
        
        # 搜索内容
        search_content = QWidget()
        search_layout = QVBoxLayout(search_content)
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_label = QLabel("🔍 搜索\n\n- 全局搜索\n- 文件搜索\n- 符号搜索")
        search_label.setStyleSheet("color: white; font-size: 14px;")
        search_layout.addWidget(search_label)
        search_layout.addStretch()
        self.add_content("search", search_content)
        
        # 源代码管理内容
        source_control_content = QWidget()
        source_control_layout = QVBoxLayout(source_control_content)
        source_control_layout.setContentsMargins(20, 20, 20, 20)
        source_control_label = QLabel("📦 源代码管理\n\n- Git状态\n- 更改列表\n- 提交历史")
        source_control_label.setStyleSheet("color: white; font-size: 14px;")
        source_control_layout.addWidget(source_control_label)
        source_control_layout.addStretch()
        self.add_content("source_control", source_control_content)
        
        # 运行和调试内容
        run_content = QWidget()
        run_layout = QVBoxLayout(run_content)
        run_layout.setContentsMargins(20, 20, 20, 20)
        run_label = QLabel("▶️ 运行和调试\n\n- 启动配置\n- 断点\n- 调用堆栈")
        run_label.setStyleSheet("color: white; font-size: 14px;")
        run_layout.addWidget(run_label)
        run_layout.addStretch()
        self.add_content("run", run_content)
        
        # 扩展内容
        extensions_content = QWidget()
        extensions_layout = QVBoxLayout(extensions_content)
        extensions_layout.setContentsMargins(20, 20, 20, 20)
        extensions_label = QLabel("🧩 扩展\n\n- 已安装\n- 推荐\n- 市场")
        extensions_label.setStyleSheet("color: white; font-size: 14px;")
        extensions_layout.addWidget(extensions_label)
        extensions_layout.addStretch()
        self.add_content("extensions", extensions_content)
        
        # 图片查看器 - 作为常驻组件
        from ui.components.image_viewer import ImageViewerComponent
        image_viewer_component = ImageViewerComponent()
        image_viewer_widget = image_viewer_component.create_widget()
        self.add_content("image_viewer", image_viewer_widget, is_permanent=True)
        
        # 建立目录查看器和图片查看器的信号连接
        self._setup_component_connections(explorer_widget, image_viewer_widget)
        
        # 如果有常驻组件，自动显示
        if self._permanent_widget is not None:
            self.show()
    
    def _setup_component_connections(self, directory_viewer_widget, image_viewer_widget):
        """建立组件间的信号连接"""
        try:
            # 存储组件引用以供后续使用
            self._directory_viewer = directory_viewer_widget
            self._image_viewer = image_viewer_widget
            
            # 连接目录查看器的点击事件到图片查看器（而不是勾选事件）
            directory_viewer_widget._tree_widget.itemClicked.connect(
                self._on_directory_item_clicked
            )
            
            # 不再连接勾选事件
            # directory_viewer_widget._tree_widget.itemChanged.connect(
            #     self._on_directory_check_state_changed
            # )
        except Exception as e:
            print(f"建立组件连接失败: {e}")
    
    def _on_directory_item_clicked(self, item, column):
        """处理目录项点击事件"""
        try:
            # 检查组件是否仍然有效
            if not hasattr(self, '_directory_viewer') or not hasattr(self, '_image_viewer'):
                return
                
            image_viewer_widget = self._image_viewer
            
            # 获取点击的文件路径
            path_str = item.data(0, Qt.ItemDataRole.UserRole)
            if not path_str:
                return
                
            from pathlib import Path
            path = Path(path_str)
            
            # 检查是否是支持的文件类型（图片或PDF）
            if path.is_file():
                suffix = path.suffix.lower()
                if suffix in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.pdf'}:
                    # 显示点击的文件
                    image_viewer_widget.set_image(str(path))
                else:
                    # 如果不是支持的文件类型，清空图片查看器
                    image_viewer_widget.clear()
            else:
                # 如果是目录，清空图片查看器
                image_viewer_widget.clear()
                
        except Exception as e:
            # 静默处理错误，避免影响主程序
            pass