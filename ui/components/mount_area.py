"""
挂载区域组件
支持九宫格布局，每个区域可以挂载不同的组件
"""

from typing import Dict, Optional, Any, Callable
from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout
from PySide6.QtCore import Qt
from ..config.ui_config import UIConfig, MountAreaConfig
from ..state.ui_state import UIState
from .base_component import BaseComponent


class MountAreaWidget(QWidget):
    """挂载区域控件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._areas: Dict[str, QWidget] = {}
        self._area_layouts: Dict[str, QVBoxLayout] = {}
        self._layout = QGridLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        
        # 初始化九宫格区域
        for row in range(3):
            for col in range(3):
                area_id = f"area_{row}_{col}"
                area_widget = QWidget()
                area_widget.setObjectName(area_id)
                area_widget.setStyleSheet("background: transparent;")
                self._areas[area_id] = area_widget
                self._layout.addWidget(area_widget, row, col)
    
    def get_area(self, area_id: str) -> Optional[QWidget]:
        """获取指定区域"""
        return self._areas.get(area_id)
    
    def _create_area_layout(self, area_id: str, config: Optional[MountAreaConfig] = None) -> QVBoxLayout:
        """创建区域布局，支持自定义对齐方式"""
        if area_id in self._area_layouts:
            return self._area_layouts[area_id]
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 根据配置设置对齐方式
        if config and hasattr(config, 'alignment'):
            alignment_map = {
                'center': Qt.AlignmentFlag.AlignCenter,
                'top': Qt.AlignmentFlag.AlignTop,
                'bottom': Qt.AlignmentFlag.AlignBottom,
                'left': Qt.AlignmentFlag.AlignLeft,
                'right': Qt.AlignmentFlag.AlignRight,
                'top_left': Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                'top_right': Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
                'bottom_left': Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                'bottom_right': Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
            }
            alignment = alignment_map.get(getattr(config, 'alignment', 'center'), Qt.AlignmentFlag.AlignCenter)
            layout.setAlignment(alignment)
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._area_layouts[area_id] = layout
        return layout
    
    def mount_component(self, area_id: str, component: QWidget, config: Optional[MountAreaConfig] = None) -> bool:
        """在指定区域挂载组件，支持动态适配大小和位置"""
        if area_id not in self._areas:
            return False
        
        area_widget = self._areas[area_id]
        
        # 清空现有内容
        layout = area_widget.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item and item.widget():
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
        else:
            layout = self._create_area_layout(area_id, config)
            area_widget.setLayout(layout)
        
        # 设置组件大小策略
        if config and hasattr(config, 'size_ratio') and config.size_ratio != 1.0:
            # 如果有大小比例配置，设置组件的最大尺寸
            area_size = area_widget.size()
            max_width = int(area_size.width() * getattr(config, 'size_ratio', 1.0))
            max_height = int(area_size.height() * getattr(config, 'size_ratio', 1.0))
            component.setMaximumSize(max_width, max_height)
        
        layout.addWidget(component)
        return True
    
    def unmount_component(self, area_id: str) -> bool:
        """卸载指定区域的组件"""
        if area_id not in self._areas:
            return False
        
        area_widget = self._areas[area_id]
        layout = area_widget.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item and item.widget():
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
        return True
    
    def update_layout_config(self, config: UIConfig) -> None:
        """更新布局配置，包括网格比例和区域可见性"""
        # 更新网格行高和列宽比例（如果配置中有的话）
        if hasattr(config, 'grid_row_ratios') and hasattr(config, 'grid_col_ratios'):
            row_ratios = getattr(config, 'grid_row_ratios', [1, 1, 1])
            col_ratios = getattr(config, 'grid_col_ratios', [1, 1, 1])
            
            for i, ratio in enumerate(row_ratios[:3]):
                self._layout.setRowStretch(i, ratio)
            for i, ratio in enumerate(col_ratios[:3]):
                self._layout.setColumnStretch(i, ratio)
        
        # 更新各个区域的配置
        for area_id, area_config in config.mount_areas.items():
            if area_id in self._areas:
                area_widget = self._areas[area_id]
                area_widget.setVisible(area_config.visible and area_config.enabled)
                
                # 更新区域布局的对齐方式
                if area_id in self._area_layouts:
                    layout = self._area_layouts[area_id]
                    if hasattr(area_config, 'alignment'):
                        alignment_map = {
                            'center': Qt.AlignmentFlag.AlignCenter,
                            'top': Qt.AlignmentFlag.AlignTop,
                            'bottom': Qt.AlignmentFlag.AlignBottom,
                            'left': Qt.AlignmentFlag.AlignLeft,
                            'right': Qt.AlignmentFlag.AlignRight,
                            'top_left': Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                            'top_right': Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
                            'bottom_left': Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                            'bottom_right': Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
                        }
                        alignment = alignment_map.get(area_config.alignment, Qt.AlignmentFlag.AlignCenter)
                        layout.setAlignment(alignment)


class MountArea(BaseComponent):
    """挂载区域管理器"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._widget = MountAreaWidget(parent)
        self._mounted_components: Dict[str, Any] = {}
        self._component_factory: Optional[Callable[[str, Dict[str, Any]], QWidget]] = None
    
    def set_component_factory(self, factory: Callable[[str, Dict[str, Any]], QWidget]) -> None:
        """设置组件工厂函数"""
        self._component_factory = factory
    
    def create_widget(self) -> QWidget:
        """创建挂载区域控件"""
        assert isinstance(self._widget, MountAreaWidget)
        return self._widget
    
    def update_config(self, config: UIConfig) -> None:
        """更新挂载区域配置"""
        self._config = config
        
        # 更新布局配置
        if self._widget and isinstance(self._widget, MountAreaWidget):
            self._widget.update_layout_config(config)
        
        # 根据配置更新各个区域
        for area_id, area_config in config.mount_areas.items():
            mount_area_widget = self._widget
            if not mount_area_widget:
                continue
            
            # Type cast to MountAreaWidget for type checker
            assert isinstance(mount_area_widget, MountAreaWidget)
            area_widget = mount_area_widget.get_area(area_id)
            if not area_widget:
                continue
            
            # 设置区域可见性
            area_widget.setVisible(area_config.visible and area_config.enabled)
            
            # 如果区域启用且有组件类型，尝试挂载组件
            if area_config.enabled and area_config.component_type and self._component_factory:
                try:
                    component = self._component_factory(
                        area_config.component_type, 
                        area_config.component_config
                    )
                    if component:
                        mount_area_widget.mount_component(area_id, component, area_config)
                        self._mounted_components[area_id] = component
                except Exception:
                    # 组件创建失败，保持区域为空
                    mount_area_widget.unmount_component(area_id)
                    if area_id in self._mounted_components:
                        del self._mounted_components[area_id]
    
    def update_state(self, state: UIState) -> None:
        """更新状态（将状态传递给已挂载的组件）"""
        self._state = state
        # 这里可以扩展为向所有挂载的组件广播状态变更
        pass
    
    def mount_custom_component(self, area_id: str, component: QWidget, config: Optional[MountAreaConfig] = None) -> bool:
        """挂载自定义组件到指定区域，支持配置"""
        if self._widget and isinstance(self._widget, MountAreaWidget):
            return self._widget.mount_component(area_id, component, config)
        return False
    
    def unmount_component(self, area_id: str) -> bool:
        """卸载指定区域的组件"""
        if self._widget and isinstance(self._widget, MountAreaWidget):
            result = self._widget.unmount_component(area_id)
            if result and area_id in self._mounted_components:
                del self._mounted_components[area_id]
            return result
        return False