"""
装饰器工具模块 - 精简版
提供核心装饰器：拦截器、参数验证、性能监控
"""

from typing import Callable, Any, Optional, Dict, get_type_hints
from functools import wraps
from inspect import signature
from ._logging import (
    _log_framework_debug,
    _log_framework_info,
    _log_framework_warning,
    _log_framework_error,
)

# ============================================================================
# 拦截器装饰器
# ============================================================================


def Interceptor(
    intercept_params: Optional[Callable] = None,
    intercept_result: Optional[Callable] = None,
    intercept_exception: Optional[Callable] = None,
    log_intercept: bool = False,
):
    """
    拦截器装饰器 - 通用函数拦截和修改

    Args:
        intercept_params: 拦截参数的回调函数，接收 (args, kwargs)，返回修改后的 (args, kwargs)
        intercept_result: 拦截结果的回调函数，接收结果，返回修改后的结果
        intercept_exception: 拦截异常的回调函数，接收异常，返回处理后的异常或新结果
        log_intercept: 是否记录拦截日志（默认 False）

    Returns:
        装饰后的函数

    Example:
        # 结果转换
        @Interceptor(intercept_result=lambda result: result.upper())
        def my_function(name: str) -> str:
            return name

        # 输入清理
        @Interceptor(intercept_params=lambda args, kwargs: (args, {k: v.strip() if isinstance(v, str) else v for k, v in kwargs.items()}))
        def my_function(name: str, email: str) -> None:
            pass

        # 异常处理
        @Interceptor(intercept_exception=lambda e: "默认值")
        def my_function():
            raise Exception("错误")

    Note:
        - 支持同时拦截参数、结果和异常
        - 拦截器按顺序执行，可以链式调用
        - 异常拦截器可以返回新结果来替代异常
        - log_intercept=True 时会记录所有拦截操作
        - 适用于输入验证、结果转换、异常处理等场景
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if intercept_params:
                try:
                    intercepted = intercept_params(*args, **kwargs)

                    if isinstance(intercepted, dict):
                        kwargs.update(intercepted)
                    elif isinstance(intercepted, tuple) and len(intercepted) == 2:
                        args, kwargs = intercepted

                    if log_intercept:
                        _log_framework_debug(f"拦截参数: {func.__name__}")

                except Exception as e:
                    _log_framework_warning(f"拦截参数失败: {func.__name__}, 错误: {e}")

            try:
                result = func(*args, **kwargs)

                if intercept_result:
                    try:
                        result = intercept_result(result)
                        if log_intercept:
                            _log_framework_debug(f"拦截结果: {func.__name__}")
                    except Exception as e:
                        _log_framework_warning(
                            f"拦截结果失败: {func.__name__}, 错误: {e}"
                        )

                return result

            except Exception as e:
                if intercept_exception:
                    try:
                        handled = intercept_exception(e)

                        if not isinstance(handled, Exception):
                            if log_intercept:
                                _log_framework_info(
                                    f"拦截异常并返回默认值: {func.__name__}"
                                )
                            return handled

                        if log_intercept:
                            _log_framework_debug(f"拦截异常并重新抛出: {func.__name__}")
                        raise handled

                    except Exception as callback_error:
                        if log_intercept:
                            _log_framework_debug(
                                f"拦截异常回调失败，重新抛出: {func.__name__}"
                            )
                        raise callback_error

                raise

        return wrapper

    return decorator


# ============================================================================
# 参数验证装饰器
# ============================================================================


def ValidateParams():
    """
    参数验证装饰器 - 根据类型注解自动验证函数参数

    Returns:
        装饰后的函数

    Example:
        @ValidateParams()
        def my_function(name: str, age: int) -> None:
            pass

    Note:
        - 根据类型注解自动验证参数类型
        - 验证失败时抛出 TypeError 异常
        - 自动记录验证失败的详细信息
        - 支持所有标准 Python 类型（int, str, bool, float, list, dict 等）
        - 适用于需要严格参数类型检查的函数
    """

    def decorator(func: Callable) -> Callable:
        type_hints = get_type_hints(func)
        func_signature = signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound_args = func_signature.bind(*args, **kwargs)
            bound_args.apply_defaults()

            for param_name, param_value in bound_args.arguments.items():
                if param_name in type_hints:
                    expected_type = type_hints[param_name]

                    if not isinstance(param_value, expected_type):
                        error_msg = (
                            f"参数类型错误: {func.__name__}.{param_name}, "
                            f"期望类型: {expected_type.__name__}, "
                            f"实际类型: {type(param_value).__name__}"
                        )
                        _log_framework_error(error_msg)
                        raise TypeError(error_msg)

            return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# 性能监控装饰器
# ============================================================================


def Timing(log_threshold: float = 1.0):
    """
    性能监控装饰器 - 自动记录函数执行时间

    Args:
        log_threshold: 日志记录阈值（秒），超过此阈值才记录警告（默认 1.0）

    Returns:
        装饰后的函数

    Example:
        @Timing(log_threshold=0.1)
        def my_function():
            pass

        @Timing(log_threshold=0.5)
        def slow_function():
            pass

    Note:
        - 自动记录函数执行时间
        - 执行时间超过阈值时记录警告日志
        - 即使未超过阈值，也会记录调试日志
        - 适用于性能分析和优化
        - 不影响函数的正常执行和返回值
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                execution_time = time.time() - start_time

                if execution_time > log_threshold:
                    _log_framework_warning(
                        f"函数执行时间: {func.__name__}, 耗时: {execution_time:.3f}秒"
                    )
                else:
                    _log_framework_debug(
                        f"函数执行时间: {func.__name__}, 耗时: {execution_time:.3f}秒"
                    )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                _log_framework_error(
                    f"函数执行失败: {func.__name__}, 耗时: {execution_time:.3f}秒, 错误: {e}"
                )
                raise

        return wrapper

    return decorator
