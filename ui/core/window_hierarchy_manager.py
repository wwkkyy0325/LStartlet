"""
窗口层级管理器
负责管理主窗口和对话框的层级关系，确保正确的模态行为
"""

from typing import Optional, Dict, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt


class WindowHierarchyManager:
    """
    窗口层级管理器
    管理主窗口和其子对话框的层级关系，确保模态对话框行为
    """
    
    def __init__(self):
        self._main_window: Optional[QWidget] = None
        self._active_dialogs: Dict[str, QWidget] = {}
        self._dialog_stack: List[QWidget] = []
    
    def set_main_window(self, main_window: QWidget) -> None:
        """设置主窗口"""
        self._main_window = main_window
    
    def get_main_window(self) -> Optional[QWidget]:
        """获取主窗口"""
        return self._main_window
    
    def show_modal_dialog(self, dialog: QWidget, dialog_id: str = "") -> None:
        """
        显示模态对话框
        
        Args:
            dialog: 要显示的对话框
            dialog_id: 对话框ID，用于管理多个对话框
        """
        if self._main_window is None:
            raise RuntimeError("主窗口未设置")
        
        # 设置对话框的父窗口为主窗口
        dialog.setParent(self._main_window)
        
        # 设置模态属性
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # 如果有对话框ID，存储对话框引用
        if dialog_id:
            self._active_dialogs[dialog_id] = dialog
        
        # 添加到对话框栈
        self._dialog_stack.append(dialog)
        
        # 显示对话框
        dialog.show()
    
    def close_dialog(self, dialog_id: str = "") -> bool:
        """
        关闭指定对话框
        
        Args:
            dialog_id: 对话框ID
            
        Returns:
            bool: 是否成功关闭
        """
        if dialog_id and dialog_id in self._active_dialogs:
            dialog = self._active_dialogs[dialog_id]
            dialog.close()
            del self._active_dialogs[dialog_id]
            
            # 从栈中移除
            if dialog in self._dialog_stack:
                self._dialog_stack.remove(dialog)
            
            return True
        elif self._dialog_stack:
            # 关闭最顶层的对话框
            dialog = self._dialog_stack.pop()
            dialog.close()
            
            # 从字典中移除（如果存在）
            for key, value in list(self._active_dialogs.items()):
                if value == dialog:
                    del self._active_dialogs[key]
                    break
            
            return True
        
        return False
    
    def is_any_dialog_active(self) -> bool:
        """检查是否有任何对话框处于活动状态"""
        return len(self._dialog_stack) > 0
    
    def get_active_dialog_count(self) -> int:
        """获取活动对话框数量"""
        return len(self._dialog_stack)
    
    def close_all_dialogs(self) -> None:
        """关闭所有对话框"""
        # 从栈顶开始关闭（后进先出）
        while self._dialog_stack:
            dialog = self._dialog_stack.pop()
            dialog.close()
        
        self._active_dialogs.clear()