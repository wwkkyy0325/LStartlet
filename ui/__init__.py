"""
OCR UI 模块公共API
"""

from .core import UIManager
from .core.custom_window_manager import CustomWindowManager
from .config import UIConfig, UIConfigManager
from .state import UIState, UIStateManager
from .components import BaseComponent

# 配置相关的枚举和常量
from .config.ui_config import BackgroundType, BorderStyle

__all__ = [
    'UIManager',
    'CustomWindowManager',
    'UIConfig', 
    'UIConfigManager',
    'UIState',
    'UIStateManager',
    'BaseComponent',
    'BackgroundType',
    'BorderStyle'
]