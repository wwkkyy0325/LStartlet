"""
错误处理装饰器 - 最小化实现，作为日志管理器的附庸
只提供简单的try-catch包装，在不重要位置报错时跳过让程序继续运行
"""

from functools import wraps
from typing import Any, Callable, Optional

from ._logging_functions import error, warning


def skip_on_error(
    default_return: Any = None,
    log_level: str = "warning",
    error_message: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    最小化错误处理装饰器

    在函数执行出错时记录日志并返回默认值，让程序继续运行。
    适用于不重要的代码路径，避免因为非关键错误导致程序中断。

    Args:
        default_return: 发生异常时返回的默认值，默认为None
        log_level: 日志级别，可选"warning"或"error"，默认为"warning"
        error_message: 自定义错误消息模板，如果为None则使用默认格式

    Returns:
        装饰后的函数

    Example:
        >>> @skip_on_error(default_return=[], log_level="warning")
        ... def get_user_list():
        ...     # 可能失败的非关键操作
        ...     return fetch_from_unreliable_api()
        ...
        >>> users = get_user_list()  # 即使API失败也会返回[]，程序继续运行
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 构建错误消息
                if error_message:
                    msg = error_message.format(func_name=func.__name__, error=str(e))
                else:
                    msg = f"Function '{func.__name__}' failed with error: {str(e)}"

                # 根据日志级别记录错误
                if log_level == "error":
                    error(msg)
                else:
                    warning(msg)

                return default_return

        return wrapper

    return decorator


# 兼容性别名
handle_errors = skip_on_error
