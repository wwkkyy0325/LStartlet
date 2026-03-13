"""
UI组件模块公共接口
"""

from .base_component import BaseComponent
from .mount_area import MountArea
from .background import BackgroundManager
from .border import BorderManager
from .ui_event_handler import UIComponentEventHandler, UIComponentManager

__all__ = [
    'BaseComponent',
    'MountArea', 
    'BackgroundManager',
    'BorderManager',
    'UIComponentEventHandler',
    'UIComponentManager'
]