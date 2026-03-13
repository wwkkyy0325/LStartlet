"""
UI组件模块入口
"""

# 基础组件
from .base_component import BaseComponent
from .background import BackgroundManager
from .border import BorderManager
from .button_style import StyledButton, ButtonStyles, create_styled_button, create_image_button
from .custom_border import CustomBorderManager
from .mount_area import MountArea, MountAreaWidget
from .ui_event_handler import UIComponentEventHandler, UIComponentManager

# 弹窗组件
from .dialog import (
    FileSelectDialog,
    select_image_and_pdf_files,
    select_directory_for_ocr
)

__all__ = [
    # 基础组件
    'BaseComponent',
    'BackgroundManager', 
    'BorderManager',
    'StyledButton',
    'ButtonStyles',
    'create_styled_button',
    'create_image_button',
    'CustomBorderManager',
    'MountArea',
    'MountAreaWidget',
    'UIComponentEventHandler',
    'UIComponentManager',
    # 弹窗组件
    'FileSelectDialog',
    'select_image_and_pdf_files', 
    'select_directory_for_ocr'
]