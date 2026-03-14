"""
UI模块入口
"""

from .ui_factory import UIFactory # type: ignore
from .components.dialog import (
    FileSelectDialog, # type: ignore
    select_image_and_pdf_files, # type: ignore 
    select_directory_for_ocr    # type: ignore
)

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
    'UIFactory',
    # 弹窗组件
    'FileSelectDialog',
    'select_image_and_pdf_files', 
    'select_directory_for_ocr',
    # 核心组件
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