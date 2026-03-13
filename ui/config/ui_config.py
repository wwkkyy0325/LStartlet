"""
UI配置定义和管理
支持背景、边框、挂载区域的配置驱动
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Tuple, Union
from enum import Enum


class BackgroundType(Enum):
    """背景类型枚举"""
    SOLID_COLOR = "solid_color"
    GRADIENT = "gradient"
    IMAGE = "image"
    CUSTOM = "custom"
    GLASS = "glass"  # 透明玻璃效果


class BorderStyle(Enum):
    """边框样式枚举"""
    NONE = "none"
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    DOUBLE = "double"


@dataclass
class BackgroundConfig:
    """背景配置"""
    type: BackgroundType = BackgroundType.SOLID_COLOR
    color: str = "#ffffff"  # 十六进制颜色或颜色名称
    gradient_colors: List[str] = field(default_factory=lambda: ["#ffffff", "#f0f0f0"])
    gradient_direction: str = "vertical"  # vertical, horizontal, diagonal
    image_path: Optional[str] = None
    image_mode: str = "stretch"  # stretch, tile, center, fit
    opacity: float = 1.0  # 0.0 - 1.0
    custom_renderer: Optional[Callable[..., Any]] = None
    # 玻璃效果配置
    glass_blur_radius: int = 20  # 模糊半径
    glass_tint_color: str = "#ffffff"  # 色调颜色
    glass_tint_opacity: float = 0.3  # 色调不透明度
    glass_noise_opacity: float = 0.1  # 噪点不透明度


@dataclass
class BorderConfig:
    """边框配置"""
    style: BorderStyle = BorderStyle.SOLID
    width: int = 2
    color: str = "#000000"
    radius: int = 0  # 圆角半径
    padding: int = 10  # 内边距


@dataclass
class MountAreaConfig:
    """挂载区域配置"""
    enabled: bool = True
    visible: bool = True
    component_type: Optional[str] = None  # 组件类型标识符
    component_config: Dict[str, Any] = field(default_factory=lambda: {})
    position: Tuple[int, int] = (0, 0)  # 在九宫格中的位置 (row, col)
    size_ratio: float = 1.0  # 相对于区域的比例
    alignment: str = "center"  # 对齐方式: center, top, bottom, left, right, top_left, top_right, bottom_left, bottom_right


@dataclass
class UIConfig:
    """完整的UI配置"""
    window_title: str = "OCR Application"
    window_size: Tuple[int, int] = (800, 600)
    window_min_size: Tuple[int, int] = (400, 300)
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    border: BorderConfig = field(default_factory=BorderConfig)
    mount_areas: Dict[str, MountAreaConfig] = field(default_factory=lambda: {})
    custom_components: Dict[str, Any] = field(default_factory=lambda: {})
    grid_row_ratios: List[int] = field(default_factory=lambda: [1, 1, 1])  # 网格行高比例
    grid_col_ratios: List[int] = field(default_factory=lambda: [1, 1, 1])  # 网格列宽比例
    
    def __post_init__(self):
        """初始化九宫格挂载区域"""
        if not self.mount_areas:
            # 初始化九宫格区域 (0,0) 到 (2,2)
            for row in range(3):
                for col in range(3):
                    area_id = f"area_{row}_{col}"
                    self.mount_areas[area_id] = MountAreaConfig(
                        enabled=True,
                        visible=True,
                        position=(row, col)
                    )


class UIConfigManager:
    """UI配置管理器"""
    
    def __init__(self, config: Optional[UIConfig] = None):
        self._config = config or UIConfig()
        self._observers: List[Callable[[UIConfig], None]] = []
    
    @property
    def config(self) -> UIConfig:
        """获取当前配置"""
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """更新配置并通知观察者"""
        self._update_nested_config(self._config, updates)
        self._notify_observers()
    
    def register_observer(self, observer: Callable[[UIConfig], None]) -> None:
        """注册配置变更观察者"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def unregister_observer(self, observer: Callable[[UIConfig], None]) -> None:
        """注销配置变更观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _update_nested_config(self, obj: Any, updates: Dict[str, Any]) -> None:
        """递归更新嵌套配置对象"""
        for key, value in updates.items():
            if hasattr(obj, key):
                attr = getattr(obj, key)
                if isinstance(value, dict) and hasattr(attr, '__dict__'):
                    self._update_nested_config(attr, value)  # type: ignore
                else:
                    setattr(obj, key, value)
    
    def _notify_observers(self) -> None:
        """通知所有观察者配置已变更"""
        for observer in self._observers:
            observer(self._config)
    
    def load_from_file(self, file_path: str) -> bool:
        """从文件加载配置"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.update_config(data)
            return True
        except Exception:
            return False
    
    def save_to_file(self, file_path: str) -> bool:
        """保存配置到文件"""
        try:
            import json
            # 转换为可序列化的字典
            config_dict = self._serialize_config(self._config)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def _serialize_config(self, obj: Any) -> Union[Dict[str, Any], List[Any], Any]:
        """序列化配置对象为JSON兼容格式"""
        if hasattr(obj, '__dict__'):
            result: Dict[str, Any] = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, Enum):
                        result[key] = value.value
                    elif callable(value):
                        result[key] = None  # 跳过可调用对象
                    else:
                        result[key] = self._serialize_config(value)
            return result
        elif isinstance(obj, list):
            return [self._serialize_config(item) for item in obj]  # type: ignore
        elif isinstance(obj, dict):
            return {k: self._serialize_config(v) for k, v in obj.items()}  # type: ignore
        else:
            return obj