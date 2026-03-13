"""
核心错误处理器
提供统一的错误处理、日志记录和全局异常捕获功能
"""

import sys
import threading
import types
from typing import Dict, Any, Optional, Callable, List, Type
from .exceptions import OCRError
from .formatter import ErrorFormatter
from core.logger import error as log_error_func, warning


class ErrorHandler:
    """错误处理器 - 负责统一处理和记录错误"""
    
    def __init__(self):
        self._handlers: List[Callable[[Exception, Optional[Dict[str, Any]]], bool]] = []
        self._lock = threading.Lock()
        self._default_context: Dict[str, Any] = {}
    
    def add_handler(self, handler: Callable[[Exception, Optional[Dict[str, Any]]], bool]) -> None:
        """
        添加错误处理回调
        
        Args:
            handler: 错误处理回调函数，返回True表示已处理，False表示继续传播
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)
    
    def remove_handler(self, handler: Callable[[Exception, Optional[Dict[str, Any]]], bool]) -> None:
        """
        移除错误处理回调
        
        Args:
            handler: 要移除的错误处理回调函数
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
    
    def get_handler_count(self) -> int:
        """
        获取当前注册的错误处理器数量
        
        Returns:
            处理器数量
        """
        with self._lock:
            return len(self._handlers)
    
    def get_default_context(self) -> Dict[str, Any]:
        """
        获取当前的默认上下文信息
        
        Returns:
            默认上下文字典的副本
        """
        with self._lock:
            return self._default_context.copy()
    
    def set_default_context(self, context: Dict[str, Any]) -> None:
        """
        设置默认上下文信息
        
        Args:
            context: 默认上下文字典
        """
        with self._lock:
            self._default_context = context.copy()
    
    def handle_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        处理错误
        
        Args:
            exception: 异常对象
            context: 错误上下文信息
            
        Returns:
            是否成功处理了错误
        """
        # 合并上下文
        full_context: Dict[str, Any] = {}
        with self._lock:
            full_context.update(self._default_context)
        if context:
            full_context.update(context)
        
        # 调用自定义处理程序
        with self._lock:
            for handler in self._handlers:
                try:
                    if handler(exception, full_context):
                        return True
                except Exception as handler_error:
                    # 处理程序自身的错误不应该影响主流程
                    warning(f"错误处理器失败: {handler_error}")
        
        # 默认处理：记录日志
        self.log_error(exception, full_context)
        return True
    
    def log_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        记录错误日志
        
        Args:
            exception: 异常对象
            context: 错误上下文信息
        """
        try:
            # 使用格式化器获取错误信息
            error_info = ErrorFormatter.get_error_info(exception)
            
            # 构建日志消息
            message = f"{error_info['error_type']}: {error_info['message']}"
            if error_info.get('error_code'):
                message += f" (错误码: {error_info['error_code']})"
            
            # 添加上下文信息到extra
            extra: Dict[str, Any] = {'error_info': error_info}
            if context:
                extra['context'] = context
            
            # 记录错误日志
            if isinstance(exception, OCRError):
                log_error_func(message, extra=extra)
            else:
                # 对于非OCR异常，也记录但可能需要特殊处理
                log_error_func(f"未预期的错误: {message}", extra=extra)
                
        except Exception as log_error:
            # 日志记录失败时，输出到stderr
            print(f"记录错误失败: {log_error}", file=sys.stderr)
            print(f"原始错误: {exception}", file=sys.stderr)


def register_global_error_handler() -> None:
    """注册全局错误处理器"""
    def global_excepthook(
        exc_type: Type[BaseException], 
        exc_value: Optional[BaseException], 
        exc_traceback: Optional[types.TracebackType]
    ) -> None:
        """全局异常处理钩子"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 允许键盘中断正常退出
            if exc_value is not None:
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 确保有异常值
        if exc_value is None:
            exc_value = exc_type()
        
        # 只处理Exception类型的异常（不包括SystemExit等BaseException子类）
        if not isinstance(exc_value, Exception):
            # 对于非Exception的BaseException，直接调用原始处理器
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 获取全局错误处理器实例
        from . import error_handler
        error_handler.handle_error(exc_value, {
            'global_handler': True,
            'traceback_obj': exc_traceback
        })
    
    # 设置全局异常处理器
    sys.excepthook = global_excepthook