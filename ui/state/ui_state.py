"""
UI状态数据类
定义UI组件的状态信息
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class UIState:
    """UI状态数据类"""
    message: str = ""
    state_type: str = "normal"  # normal, success, warning, error, loading
    progress: float = 0.0  # 0.0 - 1.0
    data: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}