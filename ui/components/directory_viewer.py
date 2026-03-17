"""
目录查看组件
支持树状图显示目录结构，并可以过滤指定类型的文件类型
"""

from typing import List, Optional, Set
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon

from .base_component import BaseComponent
from ..config.ui_config import UIConfig
from ..state.ui_state import UIState
# 导入日志管理器
from core.logger import info


class DirectoryViewerWidget(QWidget):
    """
    目录查看组件的UI部件
    提供树状图显示目录结构，支持文件类型过滤功能和复选框选择
    """
    
    # 支持的文件扩展名（图片和PDF）
    SUPPORTED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.pdf'
    }
    
    # 移除原有的信号，只保留必要的信号（如果需要的话）
    # directory_selected = Signal(str)  # 已移除
    # file_selected = Signal(str)       # 已移除  
    # file_double_clicked = Signal(str) # 已移除
    # selection_changed = Signal()      # 已移除
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._root_directory: Optional[Path] = None  # 主要根目录（用于初始加载）
        self._show_hidden_files: bool = False       # 是否显示隐藏文件
        self._updating_check_state = False          # 防止递归更新的标志
        
        # 设置最大宽度限制，防止无限延伸
        self.setMaximumWidth(800)  # 最大800像素宽
        
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        """设置UI布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(5)
        
        # 只保留添加目录按钮
        self._add_directory_button = QPushButton("添加目录")
        self._add_directory_button.setObjectName("addDirectoryButton")
        control_layout.addWidget(self._add_directory_button)
        
        # 移除选中目录按钮
        self._remove_selected_button = QPushButton("移除选中目录")
        self._remove_selected_button.setObjectName("removeSelectedButton")
        self._remove_selected_button.setEnabled(False)
        control_layout.addWidget(self._remove_selected_button)
        
        # 移除所有目录按钮
        self._remove_all_button = QPushButton("移除所有目录")
        self._remove_all_button.setObjectName("removeAllButton")
        self._remove_all_button.setEnabled(False)
        control_layout.addWidget(self._remove_all_button)
        
        # 当前目录显示
        self._current_dir_label = QLabel("未添加目录")
        self._current_dir_label.setObjectName("currentDirLabel")
        self._current_dir_label.setStyleSheet("color: #aaa;")
        control_layout.addWidget(self._current_dir_label)
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # 目录树
        self._tree_widget = QTreeWidget()
        self._tree_widget.setObjectName("directoryTree")
        self._tree_widget.setHeaderLabels(["名称"])
        self._tree_widget.setColumnWidth(0, 300)
        self._tree_widget.setAlternatingRowColors(True)
        self._tree_widget.setIndentation(15)
        
        # 启用多选模式，支持Windows风格的选择逻辑
        self._tree_widget.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self._tree_widget.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        
        # 禁用焦点矩形（移除框选样式）
        self._tree_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # 设置列数为1以支持复选框
        self._tree_widget.setColumnCount(1)
        
        main_layout.addWidget(self._tree_widget)
        
        # 应用样式
        self._apply_style()
        
    def _setup_connections(self):
        """设置信号连接"""
        self._add_directory_button.clicked.connect(self._on_add_directory_clicked)
        self._remove_selected_button.clicked.connect(self._on_remove_selected_clicked)
        self._remove_all_button.clicked.connect(self._on_remove_all_clicked)
        # 只保留复选框状态变化信号
        self._tree_widget.itemChanged.connect(self._on_item_check_state_changed)
        # 用于更新移除按钮状态
        self._tree_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def _apply_style(self):
        """应用组件样式"""
        style = """
            QPushButton#addDirectoryButton {
                background-color: rgba(70, 130, 180, 180);
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
            }
            
            QPushButton#addDirectoryButton:hover {
                background-color: rgba(70, 130, 180, 220);
            }
            
            QPushButton#removeSelectedButton,
            QPushButton#removeAllButton {
                background-color: rgba(220, 20, 60, 180);
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
            }
            
            QPushButton#removeSelectedButton:hover,
            QPushButton#removeAllButton:hover {
                background-color: rgba(220, 20, 60, 220);
            }
            
            QPushButton#removeSelectedButton:disabled,
            QPushButton#removeAllButton:disabled {
                background-color: rgba(100, 100, 100, 120);
                color: #888;
            }
            
            QLineEdit#filterInput {
                background-color: rgba(255, 255, 255, 30);
                color: white;
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 12px;
            }
            
            QTreeWidget#directoryTree {
                background-color: rgba(255, 255, 255, 20);
                color: white;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 4px;
                outline: none;
            }
            
            QTreeWidget#directoryTree::item {
                padding: 3px;
            }
            
            QTreeWidget#directoryTree::item:selected {
                background-color: rgba(70, 130, 180, 120);
            }
            
            QTreeWidget#directoryTree::item:hover {
                background-color: rgba(255, 255, 255, 30);
            }
            
            QLabel#currentDirLabel {
                font-size: 12px;
                padding: 3px 0;
            }
        """
        self.setStyleSheet(style)
        
    def _update_button_states(self):
        """更新移除按钮的启用状态"""
        has_root_items = self._tree_widget.topLevelItemCount() > 0
        has_selected_root_items = False
        
        selected_items = self._tree_widget.selectedItems()
        for item in selected_items:
            if not item.parent():  # 选中了顶级目录项
                has_selected_root_items = True
                break
                
        self._remove_selected_button.setEnabled(has_selected_root_items)
        # 修复：只要有目录就启用移除所有目录按钮
        self._remove_all_button.setEnabled(has_root_items)
        
    def _update_current_dir_label(self):
        """更新当前目录标签显示"""
        root_count = self._tree_widget.topLevelItemCount()
        if root_count == 0:
            self._current_dir_label.setText("未添加目录")
        elif root_count == 1:
            root_item = self._tree_widget.topLevelItem(0)
            path_str = root_item.data(0, Qt.ItemDataRole.UserRole)
            if path_str:
                path = Path(path_str)
                self._current_dir_label.setText(f"当前目录: {path.name}")
            else:
                self._current_dir_label.setText("当前目录: 1个目录")
        else:
            self._current_dir_label.setText(f"当前目录: {root_count}个目录")
            
    def add_directory(self, directory_path: str):
        """添加目录到现有的树中（作为新的顶级节点）"""
        try:
            path = Path(directory_path)
            if not path.exists() or not path.is_dir():
                return
                
            # 创建顶级项并立即添加到树中
            root_item = QTreeWidgetItem()
            root_item.setText(0, path.name)
            root_item.setData(0, Qt.ItemDataRole.UserRole, str(path.resolve()))
            root_item.setCheckState(0, Qt.CheckState.Unchecked)
            self._tree_widget.addTopLevelItem(root_item)
            
            # 然后递归添加子项
            # 直接添加所有子项，不再根据文件类型过滤
            self._add_children_to_item(root_item, path)
            
            self._update_current_dir_label()
            self._update_button_states()
            
        except Exception as e:
            pass
            
    def _add_children_to_item(self, parent_item: QTreeWidgetItem, path: Path):
        """向现有项添加子项"""
        if not path.is_dir():
            return
            
        try:
            for child in path.iterdir():
                if child.is_dir():
                    child_item = QTreeWidgetItem()
                    child_item.setText(0, child.name)
                    child_item.setData(0, Qt.ItemDataRole.UserRole, str(child.resolve()))
                    child_item.setCheckState(0, Qt.CheckState.Unchecked)
                    parent_item.addChild(child_item)
                    self._add_children_to_item(child_item, child)
                elif child.is_file():
                    if self._show_hidden_files or not child.name.startswith("."):
                        # 只添加支持的文件类型（图片和PDF）
                        if child.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                            file_item = QTreeWidgetItem()
                            file_item.setText(0, child.name)
                            file_item.setData(0, Qt.ItemDataRole.UserRole, str(child.resolve()))
                            file_item.setCheckState(0, Qt.CheckState.Unchecked)
                            parent_item.addChild(file_item)
        except (OSError, PermissionError):
            # 跳过无法访问的目录
            pass
            
    def clear(self):
        """清空目录树"""
        self._tree_widget.clear()
        self._update_current_dir_label()
        self._update_button_states()
        
    def _on_remove_selected_clicked(self):
        """处理移除选中目录按钮点击"""
        selected_items = self._tree_widget.selectedItems()
        root_items_to_remove = []
        
        # 找出选中的顶级目录项
        for item in selected_items:
            if not item.parent():  # 顶级项
                root_items_to_remove.append(item)
                
        # 从后往前删除，避免索引问题
        for item in reversed(root_items_to_remove):
            index = self._tree_widget.indexOfTopLevelItem(item)
            if index >= 0:
                self._tree_widget.takeTopLevelItem(index)
                
        self._update_button_states()
        self._update_current_dir_label()
            
    def _on_remove_all_clicked(self):
        """处理移除所有目录按钮点击"""
        self.clear()
            
    def _on_selection_changed(self):
        """处理选中状态变化 - 更新按钮状态"""
        self._update_button_states()
        
        # 使用日志管理器输出调试信息
        selected_files = self.get_selected_files()
        selected_dirs = self.get_selected_directories()
        info(f"选中文件 ({len(selected_files)}): {selected_files}")
        info(f"选中目录 ({len(selected_dirs)}): {selected_dirs}")
        
    def set_show_hidden_files(self, show: bool):
        """设置是否显示隐藏文件"""
        self._show_hidden_files = show
        self._update_tree()
        
    def _add_directory_to_tree(self, parent_item: Optional[QTreeWidgetItem], path: Path):
        """将目录添加到树中"""
        item = QTreeWidgetItem()
        item.setText(0, path.name)
        item.setData(0, Qt.ItemDataRole.UserRole, str(path))
        item.setCheckState(0, Qt.CheckState.Unchecked)
        
        # 只有目录才需要展开子项
        if path.is_dir():
            # 添加子目录和文件
            try:
                for child in path.iterdir():
                    if child.is_dir():
                        self._add_directory_to_tree(item, child)
                    elif child.is_file():
                        if self._show_hidden_files or not child.name.startswith("."):
                            if not self._allowed_extensions or child.suffix in self._allowed_extensions:
                                self._add_file_to_tree(item, child)
            except (OSError, PermissionError):
                # 跳过无法访问的目录
                pass
        
        if parent_item is None:
            self._tree_widget.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
            
        return item
        
    def _add_file_to_tree(self, parent_item: QTreeWidgetItem, file_path: Path):
        """将文件添加到树中"""
        item = QTreeWidgetItem(parent_item)
        item.setText(0, file_path.name)
        item.setData(0, Qt.ItemDataRole.UserRole, str(file_path))
        item.setCheckState(0, Qt.CheckState.Unchecked)
        # 文件不需要展开，所以不递归
        
    def _update_tree(self):
        """更新目录树"""
        root_items = []
        for i in range(self._tree_widget.topLevelItemCount()):
            root_items.append(self._tree_widget.topLevelItem(i))
            
        self._tree_widget.clear()
        for item in root_items:
            path_str = item.data(0, Qt.ItemDataRole.UserRole)
            if path_str:
                path = Path(path_str)
                self._add_directory_to_tree(None, path)
                
    def _on_add_directory_clicked(self):
        """处理添加目录按钮点击"""
        directory_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory_path:
            self.add_directory(directory_path)
            
    def _on_item_check_state_changed(self, item: QTreeWidgetItem, column: int):
        """处理复选框状态变化"""
        if self._updating_check_state:
            return
            
        check_state = item.checkState(0)
        self._updating_check_state = True
        self._update_child_items_check_state(item, check_state)
        self._update_parent_items_check_state(item)
        self._updating_check_state = False
        
    def _update_child_items_check_state(self, item: QTreeWidgetItem, check_state: Qt.CheckState):
        """更新子项的复选框状态"""
        for i in range(item.childCount()):
            child_item = item.child(i)
            child_item.setCheckState(0, check_state)
            self._update_child_items_check_state(child_item, check_state)
            
    def _update_parent_items_check_state(self, item: QTreeWidgetItem):
        """更新父项的复选框状态"""
        parent_item = item.parent()
        if parent_item is None:
            return
            
        all_checked = True
        all_unchecked = True
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            if child_item.checkState(0) == Qt.CheckState.Checked:
                all_unchecked = False
            elif child_item.checkState(0) == Qt.CheckState.Unchecked:
                all_checked = False
                
        if all_checked:
            parent_item.setCheckState(0, Qt.CheckState.Checked)
        elif all_unchecked:
            parent_item.setCheckState(0, Qt.CheckState.Unchecked)
        else:
            parent_item.setCheckState(0, Qt.CheckState.PartiallyChecked)
            
        self._update_parent_items_check_state(parent_item)
        
    def get_selected_files(self) -> List[str]:
        """获取所有选中的文件路径"""
        selected_files = set()
        self._collect_selected_files(self._tree_widget.invisibleRootItem(), selected_files)
        return sorted(list(selected_files))
        
    def _collect_selected_files(self, item: QTreeWidgetItem, selected_files: Set[str]):
        """递归收集选中的文件路径 - 只返回支持的文件类型"""
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if path_str:
            path = Path(path_str)
            if path.is_file() and item.checkState(0) == Qt.CheckState.Checked:
                # 确保只返回支持的文件类型
                if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    selected_files.add(str(path))
                
        for i in range(item.childCount()):
            child_item = item.child(i)
            self._collect_selected_files(child_item, selected_files)
            
    def get_selected_directories(self) -> List[str]:
        """获取所有选中的目录路径"""
        selected_dirs = set()
        self._collect_selected_directories(self._tree_widget.invisibleRootItem(), selected_dirs)
        return sorted(list(selected_dirs))
        
    def _collect_selected_directories(self, item: QTreeWidgetItem, selected_dirs: Set[str]):
        """递归收集选中的目录路径"""
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if path_str:
            path = Path(path_str)
            if path.is_dir() and item.checkState(0) == Qt.CheckState.Checked:
                selected_dirs.add(str(path))
                
        for i in range(item.childCount()):
            child_item = item.child(i)
            self._collect_selected_directories(child_item, selected_dirs)
            
    def get_all_files_in_selected_directories(self) -> List[str]:
        """获取选中目录中所有符合过滤条件的文件（已去重）"""
        all_files = set()
        self._collect_all_files_in_selected_directories(self._tree_widget.invisibleRootItem(), all_files)
        return sorted(list(all_files))
        
    def _collect_all_files_in_selected_directories(self, item: QTreeWidgetItem, all_files: Set[str]):
        """递归收集选中目录中的所有支持的文件"""
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if path_str:
            path = Path(path_str)
            if path.is_file() and item.checkState(0) == Qt.CheckState.Checked:
                # 确保只返回支持的文件类型
                if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    all_files.add(str(path))
            elif path.is_dir() and item.checkState(0) == Qt.CheckState.Checked:
                for child in path.iterdir():
                    if child.is_file():
                        if self._show_hidden_files or not child.name.startswith("."):
                            # 只添加支持的文件类型
                            if child.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                                all_files.add(str(child))
                    elif child.is_dir():
                        self._collect_all_files_in_selected_directories(child, all_files)
        
    def clear_selection(self):
        """清空选中状态"""
        self._tree_widget.clearSelection()
        
class DirectoryViewerComponent(BaseComponent):
    """
    目录查看组件
    封装DirectoryViewerWidget并提供标准组件接口
    """
    
    def __init__(self, parent: Optional[QWidget] = None, component_id: Optional[str] = None):
        super().__init__(parent, component_id)
        self._widget = DirectoryViewerWidget(parent)
        
    def create_widget(self) -> QWidget:
        """创建组件的QWidget"""
        return self._widget
        
    def update_config(self, config: UIConfig) -> None:
        """更新组件配置"""
        self._config = config
        # 这里可以添加具体的配置更新逻辑
        pass
        
    def update_state(self, state: UIState) -> None:
        """更新组件状态"""
        self._state = state
        # 这里可以添加具体的状态更新逻辑
        pass
        
    # 代理方法
    def add_directory(self, directory_path: str):
        """添加目录到现有树中"""
        return self._widget.add_directory(directory_path)
        
    def set_show_hidden_files(self, show: bool):
        """设置是否显示隐藏文件"""
        return self._widget.set_show_hidden_files(show)
        
    def clear(self):
        """清空目录树"""
        return self._widget.clear()
        
    def get_selected_files(self) -> List[str]:
        """获取所有选中的文件路径"""
        return self._widget.get_selected_files()
        
    def get_selected_directories(self) -> List[str]:
        """获取所有选中的目录路径"""
        return self._widget.get_selected_directories()
        
    def get_all_files_in_selected_directories(self) -> List[str]:
        """获取选中目录中所有符合过滤条件的文件（已去重）"""
        return self._widget.get_all_files_in_selected_directories()
        
    def clear_selection(self):
        """清空选中状态"""
        return self._widget.clear_selection()