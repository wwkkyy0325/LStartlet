"""
设置内容组件
用于挂载到设置弹窗中的具体设置选项
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt


class SettingsContentWidget(QWidget):
    """
    设置内容组件
    空的可挂载容器，用于后续动态添加设置选项
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI - 创建空容器"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 添加一个占位标签或保持完全空白
        # 根据需求，这里保持完全空白，等待后续动态挂载内容
        
        # 确保布局有适当的伸缩性
        layout.addStretch()
    
    def mount_setting_component(self, component: QWidget) -> bool:
        """
        挂载设置子组件到此容器中
        
        Args:
            component: 要挂载的设置组件
            
        Returns:
            bool: 是否成功挂载
        """
        try:
            layout = self.layout()
            if layout is None:
                return False
            
            # 清除现有的伸缩项（如果有）
            while layout.count() > 0:
                item = layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            
            # 添加新组件
            layout.addWidget(component)
            layout.addStretch()
            return True
        except Exception as e:
            print(f"❌ 设置组件挂载失败: {e}")
            return False