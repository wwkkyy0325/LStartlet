from typing import Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal


class CentralContentManagerV2(QWidget):
    """
    中央内容管理器 V2
    支持上下分层布局：
    - 上半部分：可切换的内容区域（如资源管理器、搜索等）
    - 下半部分：常驻组件区域（如图片查看器）
    """
    
    content_changed = Signal(str)  # 当前内容改变时触发
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_content_id = ""
        self._content_widgets: Dict[str, QWidget] = {}
        self._permanent_widget: Optional[QWidget] = None  # 常驻组件（图片查看器）
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI布局 - 使用垂直分割器实现上下分层"""
        # 使用垂直分割器来实现上下分层
        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setContentsMargins(0, 0, 0, 0)
        
        # 设置分割器样式
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 30);
                height: 2px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._splitter)
        
        # 默认情况下不显示任何内容
        self.hide()
    
    def add_content(self, content_id: str, widget: QWidget, is_permanent: bool = False) -> bool:
        """
        添加内容组件
        
        Args:
            content_id: 内容ID
            widget: 内容组件
            is_permanent: 是否为常驻组件（下半部分）
            
        Returns:
            bool: 是否成功添加
        """
        if content_id in self._content_widgets or (is_permanent and self._permanent_widget is not None):
            return False
        
        if is_permanent:
            self._permanent_widget = widget
            widget.setParent(self)
        else:
            self._content_widgets[content_id] = widget
            widget.setParent(self)
            widget.hide()  # 初始隐藏非常驻组件
            
        return True
    
    def show_content(self, content_id: str):
        """显示指定内容在上半部分，常驻组件在下半部分"""
        # 清理当前分割器
        self._clear_splitter()
        
        if self._permanent_widget is None:
            # 如果没有常驻组件，直接显示指定内容占满整个区域
            if content_id not in self._content_widgets:
                self.hide()
                return
            
            widget = self._content_widgets[content_id]
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._splitter.addWidget(widget)
            widget.show()
            self._current_content_id = content_id
            self.show()
            self.content_changed.emit(content_id)
            return
        
        # 有常驻组件的情况
        if content_id not in self._content_widgets:
            # 只显示常驻组件，占满整个空间
            self._permanent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._splitter.addWidget(self._permanent_widget)
            self._permanent_widget.show()
            self._current_content_id = ""
            self.show()
            self.content_changed.emit("")
            return
        
        # 显示指定内容（上半部分）和常驻组件（下半部分）
        content_widget = self._content_widgets[content_id]
        
        # 设置大小策略
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._permanent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 添加到分割器
        self._splitter.addWidget(content_widget)
        self._splitter.addWidget(self._permanent_widget)
        
        content_widget.show()
        self._permanent_widget.show()
        
        # 设置初始分割比例：上半部分30%，下半部分70%
        self._splitter.setSizes([int(self.height() * 0.3), int(self.height() * 0.7)])
        
        self._current_content_id = content_id
        self.show()
        self.content_changed.emit(content_id)
    
    def hide_content(self):
        """隐藏所有可切换内容，只显示常驻组件"""
        self._clear_splitter()
        
        if self._permanent_widget is not None:
            self._permanent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._splitter.addWidget(self._permanent_widget)
            self._permanent_widget.show()
            self._current_content_id = ""
            self.show()
            self.content_changed.emit("")
        else:
            self.hide()
            self._current_content_id = ""
            self.content_changed.emit("")
    
    def _clear_splitter(self):
        """清理分割器中的所有组件"""
        while self._splitter.count() > 0:
            widget = self._splitter.widget(0)
            if widget:
                widget.setParent(None)
    
    def get_current_content(self) -> str:
        """获取当前显示的内容ID"""
        return self._current_content_id
    
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
        
        # 图片查看器 - 作为常驻组件（下半部分）
        from ui.components.image_viewer import ImageViewerComponent
        image_viewer_component = ImageViewerComponent()
        image_viewer_widget = image_viewer_component.create_widget()
        self.add_content("image_viewer", image_viewer_widget, is_permanent=True)
        
        # 建立组件间的信号连接
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
            
            # 连接目录查看器的点击事件到图片查看器
            directory_viewer_widget._tree_widget.itemClicked.connect(
                self._on_directory_item_clicked
            )
            
        except Exception as e:
            pass
    
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