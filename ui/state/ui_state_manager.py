"""
UI状态管理器
负责管理UI状态的更新和通知
"""

from typing import List, Callable, Optional, Dict, Any
from .ui_state import UIState
import time


class UIStateManager:
    """UI状态管理器"""
    
    def __init__(self):
        self._current_state: UIState = UIState()
        self._observers: List[Callable[[UIState], None]] = []
        self._async_observers: List[Callable[[UIState], None]] = []
    
    def get_current_state(self) -> UIState:
        """获取当前状态"""
        return self._current_state
    
    def update_state(self, 
                    message: str = "",
                    state_type: str = "",
                    progress: float = -1.0,
                    data: Optional[Dict[str, Any]] = None) -> None:
        """更新状态"""
        # 更新状态字段
        if message:
            self._current_state.message = message
        if state_type:
            self._current_state.state_type = state_type
        if progress >= 0.0:
            self._current_state.progress = min(1.0, max(0.0, progress))
        if data is not None:
            # 确保current_state.data不是None后再调用update
            if self._current_state.data is None:
                self._current_state.data = {}
            self._current_state.data.update(data)
        
        # 更新时间戳
        self._current_state.timestamp = time.time()
        
        # 通知所有观察者
        self._notify_observers()
    
    def add_observer(self, observer: Callable[[UIState], None]) -> None:
        """添加同步观察者"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[UIState], None]) -> None:
        """移除同步观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def add_async_observer(self, observer: Callable[[UIState], None]) -> None:
        """添加异步观察者"""
        if observer not in self._async_observers:
            self._async_observers.append(observer)
    
    def remove_async_observer(self, observer: Callable[[UIState], None]) -> None:
        """移除异步观察者"""
        if observer in self._async_observers:
            self._async_observers.remove(observer)
    
    def _notify_observers(self) -> None:
        """通知所有观察者"""
        # 同步通知
        for observer in self._observers:
            try:
                observer(self._current_state)
            except Exception:
                # 观察者异常不应影响状态管理
                pass
        
        # 异步通知（在实际应用中可能需要使用线程或事件循环）
        for observer in self._async_observers:
            try:
                observer(self._current_state)
            except Exception:
                # 观察者异常不应影响状态管理
                pass