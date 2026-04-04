"""
现代化错误处理器 - 高内聚低耦合的错误处理解决方案
提供统一的错误处理入口、全局错误捕获和错误格式化功能
"""

from typing import Dict, Any, Optional
from .error_handler import ErrorHandler, register_global_error_handler  # type: ignore
from .formatter import ErrorFormatter

# 内部全局错误处理器实例（不对外暴露）
_error_handler_instance: ErrorHandler = ErrorHandler()

__all__ = [
    "handle_error",
    "format_error", 
    "log_error",
    "get_error_info",
    "ErrorHandler",
    "register_global_error_handler",
    "ErrorFormatter",
    "get_error_handler",  # 新增获取函数替代全局实例
]


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器实例"""
    return _error_handler_instance


# 对外暴露的核心接口
def handle_error(
    exception: Exception, context: Optional[Dict[str, Any]] = None
) -> bool:
    """处理错误"""
    return _error_handler_instance.handle_error(exception, context)


def format_error(exception: Exception, include_traceback: bool = True) -> str:
    """格式化错误信息"""
    return ErrorFormatter.format_error(exception, include_traceback)


def log_error(exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """记录错误日志"""
    _error_handler_instance.log_error(exception, context)


def get_error_info(exception: Exception) -> Dict[str, Any]:
    """获取错误详细信息"""
    return ErrorFormatter.get_error_info(exception)


# 移除顶层的全局错误处理器注册
# 根据项目规范，应在主程序入口统一注册