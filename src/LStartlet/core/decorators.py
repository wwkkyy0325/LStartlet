"""核心装饰器模块
提供错误处理、日志记录、事件发布和配置验证等装饰器功能
"""

import time
import threading
from functools import wraps
from typing import Any, Callable, Optional, Dict, Type, Union

from enum import Enum

# 核心模块导入
from LStartlet.core.error.exceptions import InfrastructureError
from LStartlet.core.logger import info, error as log_error, warning
from LStartlet.core.di import ServiceContainer, ServiceLifetime, get_default_container
from LStartlet.core.di.exceptions import ServiceResolutionError
from typing import Type, TypeVar, Callable, Optional, Any, Union, get_type_hints

T = TypeVar("T")


class PermissionLevel(Enum):
    """权限级别枚举
    
    Attributes:
        GUEST: 访客权限，最低权限级别
        USER: 普通用户权限
        ADMIN: 管理员权限
        SYSTEM: 系统权限，最高权限级别
    """

    GUEST = 0
    USER = 1
    ADMIN = 2
    SYSTEM = 3


def with_error_handling(
    error_code: str = "UNHANDLED_ERROR",
    default_return: Any = None,
    log_level: str = "error",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    错误处理装饰器
    
    自动捕获函数执行过程中的异常，记录日志并返回默认值。
    支持自定义错误代码、默认返回值和日志级别。
    
    Args:
        error_code (str): 自定义错误代码，用于标识错误类型。默认为 "UNHANDLED_ERROR"。
        default_return (Any): 当发生异常时返回的默认值。默认为 None。
        log_level (str): 日志记录级别，可选值: "debug", "info", "warning", "error"。默认为 "error"。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的原函数
        
    Raises:
        No exceptions are raised by this decorator itself, but it handles all exceptions 
        from the decorated function.
        
    Example:
        >>> @with_error_handling(error_code="DIVISION_ERROR", default_return=0)
        ... def divide(a: int, b: int) -> float:
        ...     return a / b
        ...
        >>> result = divide(10, 0)  # 不会抛出异常
        >>> print(result)
        0
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 记录错误日志
                error_msg = f"Error in {func.__name__}: {str(e)}"
                if log_level == "error":
                    log_error(error_msg)
                elif log_level == "warning":
                    warning(error_msg)
                else:
                    info(error_msg)

                return default_return

        return wrapper

    return decorator


def with_logging(
    level: str = "info", measure_time: bool = False, include_args: bool = False
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    日志装饰器
    
    在函数执行前后自动记录日志，支持执行时间测量和参数记录。
    
    Args:
        level (str): 日志级别，可选值: "debug", "info", "warning", "error"。默认为 "info"。
        measure_time (bool): 是否测量并记录函数执行时间。默认为 False。
        include_args (bool): 是否在日志中包含函数的参数信息。默认为 False。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的原函数
        
    Raises:
        AttributeError: 如果指定的日志级别不存在
        
    Example:
        >>> @with_logging(level="debug", measure_time=True, include_args=True)
        ... def greet(name: str) -> str:
        ...     return f"Hello, {name}!"
        ...
        >>> result = greet("Alice")
        # 会记录类似：Starting greet with args=('Alice',), kwargs={}
        # 以及：greet completed in 0.0001s
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取日志函数
            log_func = getattr(
                __import__("LStartlet.core.logger"),
                level,
                __import__("LStartlet.core.logger").info,
            )

            # 记录开始日志
            start_time = time.time() if measure_time else None
            if include_args:
                log_func(f"Starting {func.__name__} with args={args}, kwargs={kwargs}")
            else:
                log_func(f"Starting {func.__name__}")

            try:
                result = func(*args, **kwargs)
                if measure_time and start_time is not None:
                    duration = time.time() - start_time
                    log_func(f"{func.__name__} completed in {duration:.4f}s")
                else:
                    log_func(f"{func.__name__} completed successfully")

                return result
            except Exception as e:
                if measure_time and start_time is not None:
                    duration = time.time() - start_time
                    log_func(f"{func.__name__} failed after {duration:.4f}s: {str(e)}")
                else:
                    log_func(f"{func.__name__} failed: {str(e)}")
                raise

        return wrapper

    return decorator


def _get_current_user_permission_level() -> PermissionLevel:
    """
    获取当前用户权限级别（模拟实现）

    Returns:
        当前用户的权限级别
    """
    # 模拟实现：默认返回USER权限
    return PermissionLevel.USER


class MetricsCollector:
    """指标收集器（模拟实现）
    
    单例模式的指标收集器，用于收集和存储各种监控指标数据。
    支持计数器（counter）和直方图（histogram）两种指标类型。
    
    Attributes:
        _instance (Optional[MetricsCollector]): 单例实例
        _metrics (Dict[str, Any]): 存储所有指标的字典
        
    Example:
        >>> collector = MetricsCollector()
        >>> collector.increment_counter("requests_total", {"method": "GET"})
        >>> collector.observe_histogram("request_duration", 0.5, {"endpoint": "/api"})
    """

    _instance = None
    _metrics: Dict[str, Any]

    def __new__(cls) -> "MetricsCollector":
        """创建或返回单例实例
        
        Returns:
            MetricsCollector: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._metrics = {}
        return cls._instance

    def increment_counter(
        self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0
    ) -> None:
        """
        增加计数器指标
        
        Args:
            name (str): 计数器名称
            labels (Optional[Dict[str, str]]): 标签字典，用于区分不同的指标维度。默认为 None。
            value (float): 增加的值。默认为 1.0。
            
        Example:
            >>> collector = MetricsCollector()
            >>> collector.increment_counter("http_requests_total", {"method": "POST", "status": "200"})
        """
        key = f"{name}_{str(labels) if labels else ''}"
        if key not in self._metrics:
            self._metrics[key] = 0.0
        self._metrics[key] += value

    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        观察直方图指标
        
        记录一个观测值到直方图指标中，用于统计分布情况。
        
        Args:
            name (str): 直方图名称
            value (float): 观测值
            labels (Optional[Dict[str, str]]): 标签字典，用于区分不同的指标维度。默认为 None。
            
        Example:
            >>> collector = MetricsCollector()
            >>> collector.observe_histogram("http_request_duration_seconds", 0.25)
        """
        key = f"{name}_histogram_{str(labels) if labels else ''}"
        if key not in self._metrics:
            self._metrics[key] = []
        self._metrics[key].append(value)


# 异步装饰器
def with_error_handling_async(
    error_code: str = "UNHANDLED_ERROR",
    default_return: Any = None,
    log_level: str = "error",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    异步错误处理装饰器
    
    为异步函数提供错误处理功能，自动捕获异常、记录日志并返回默认值。
    
    Args:
        error_code (str): 自定义错误代码，用于标识错误类型。默认为 "UNHANDLED_ERROR"。
        default_return (Any): 当发生异常时返回的默认值。默认为 None。
        log_level (str): 日志记录级别，可选值: "debug", "info", "warning", "error"。默认为 "error"。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的异步函数
        
    Raises:
        No exceptions are raised by this decorator itself, but it handles all exceptions 
        from the decorated async function.
        
    Example:
        >>> @with_error_handling_async(error_code="ASYNC_ERROR", default_return=None)
        ... async def fetch_data(url: str) -> dict:
        ...     return await http_get(url)
        ...
        >>> result = await fetch_data("invalid_url")  # 不会抛出异常
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in async {func.__name__}: {str(e)}"
                if log_level == "error":
                    log_error(error_msg)
                elif log_level == "warning":
                    warning(error_msg)
                else:
                    info(error_msg)
                return default_return

        return wrapper

    return decorator


def with_logging_async(
    level: str = "info", measure_time: bool = False, include_args: bool = False
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    异步日志装饰器
    
    为异步函数提供日志记录功能，支持执行时间测量和参数记录。
    
    Args:
        level (str): 日志级别，可选值: "debug", "info", "warning", "error"。默认为 "info"。
        measure_time (bool): 是否测量并记录函数执行时间。默认为 False。
        include_args (bool): 是否在日志中包含函数的参数信息。默认为 False。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的异步函数
        
    Raises:
        AttributeError: 如果指定的日志级别不存在
        
    Example:
        >>> @with_logging_async(level="info", measure_time=True)
        ... async def process_data(data: list) -> list:
        ...     await asyncio.sleep(0.1)
        ...     return [x * 2 for x in data]
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_func = getattr(
                __import__("LStartlet.core.logger"),
                level,
                __import__("LStartlet.core.logger").info,
            )
            start_time = time.time() if measure_time else None
            if include_args:
                log_func(
                    f"Starting async {func.__name__} with args={args}, kwargs={kwargs}"
                )
            else:
                log_func(f"Starting async {func.__name__}")

            try:
                result = await func(*args, **kwargs)
                if measure_time and start_time is not None:
                    duration = time.time() - start_time
                    log_func(f"Async {func.__name__} completed in {duration:.4f}s")
                else:
                    log_func(f"Async {func.__name__} completed successfully")
                return result
            except Exception as e:
                if measure_time and start_time is not None:
                    duration = time.time() - start_time
                    log_func(
                        f"Async {func.__name__} failed after {duration:.4f}s: {str(e)}"
                    )
                else:
                    log_func(f"Async {func.__name__} failed: {str(e)}")
                raise

        return wrapper

    return decorator


def cached_async(
    maxsize: int = 128, 
    ttl: Optional[float] = None, 
    typed: bool = False
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    异步缓存装饰器
    
    为异步函数提供 LRU 缓存功能，支持最大缓存大小限制。
    注意：当前实现未完全支持 TTL 和 typed 参数。
    
    Args:
        maxsize (int): 缓存最大条目数，超过时会移除最旧的条目。默认为 128。
        ttl (Optional[float]): 缓存过期时间（秒），超过此时间的缓存条目将失效。默认为 None（不过期）。
        typed (bool): 是否区分参数类型（如 1 和 1.0 视为不同键）。默认为 False。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的带缓存异步函数
        
    Example:
        >>> @cached_async(maxsize=100)
        ... async def get_user(user_id: int) -> dict:
        ...     return await db.query(user_id)
        ...
        >>> user1 = await get_user(1)  # 首次调用会执行查询
        >>> user2 = await get_user(1)  # 从缓存返回
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache: Dict[Any, Any] = {}
        cache_lock = threading.Lock()

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (args, tuple(sorted(kwargs.items())))

            with cache_lock:
                if key in cache:
                    return cache[key]

            result = await func(*args, **kwargs)

            with cache_lock:
                cache[key] = result
                if len(cache) > maxsize:
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]

            return result

        return wrapper

    return decorator


def require_permission(
    required_level: PermissionLevel, 
    error_message: str = "Insufficient permissions"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    权限检查装饰器
    
    在函数执行前检查当前用户的权限级别，如果权限不足则抛出异常。
    
    Args:
        required_level (PermissionLevel): 所需的最低权限级别。
        error_message (str): 权限不足时抛出的错误消息。默认为 "Insufficient permissions"。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的函数
        
    Raises:
        InfrastructureError: 当当前用户权限级别低于所需级别时抛出，错误代码为 "PERMISSION_DENIED"。
        
    Example:
        >>> @require_permission(PermissionLevel.ADMIN)
        ... def delete_user(user_id: int) -> bool:
        ...     return True
        ...
        >>> delete_user(1)  # 如果当前用户不是 ADMIN，将抛出 InfrastructureError
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_level = _get_current_user_permission_level()
            if current_level.value < required_level.value:
                raise InfrastructureError(
                    message=error_message,
                    error_code="PERMISSION_DENIED",
                    context={
                        "required_level": required_level.name,
                        "current_level": current_level.name,
                        "function": func.__name__,
                    },
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission_async(
    required_level: PermissionLevel, 
    error_message: str = "Insufficient permissions"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    异步权限检查装饰器
    
    为异步函数提供权限检查功能，在函数执行前验证用户权限级别。
    
    Args:
        required_level (PermissionLevel): 所需的最低权限级别。
        error_message (str): 权限不足时抛出的错误消息。默认为 "Insufficient permissions"。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的异步函数
        
    Raises:
        InfrastructureError: 当当前用户权限级别低于所需级别时抛出，错误代码为 "PERMISSION_DENIED"。
        
    Example:
        >>> @require_permission_async(PermissionLevel.SYSTEM)
        ... async def shutdown_system() -> bool:
        ...     return True
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_level = _get_current_user_permission_level()
            if current_level.value < required_level.value:
                raise InfrastructureError(
                    message=error_message,
                    error_code="PERMISSION_DENIED",
                    context={
                        "required_level": required_level.name,
                        "current_level": current_level.name,
                        "function": func.__name__,
                    },
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def monitor_metrics(
    metric_name: str, 
    include_labels: bool = True
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    监控指标装饰器
    
    自动收集函数的执行指标，包括调用次数、成功/失败次数和执行时间。
    使用单例的 MetricsCollector 存储指标数据。
    
    Args:
        metric_name (str): 指标名称前缀，会自动添加 _total, _success_total, _failure_total, 
                          _duration_seconds 等后缀。
        include_labels (bool): 是否包含函数名作为标签。默认为 True。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的带监控函数
        
    Raises:
        Exception: 原函数抛出的任何异常都会被重新抛出，但在抛出前会记录失败指标。
        
    Example:
        >>> @monitor_metrics("api_requests", include_labels=True)
        ... def handle_request(path: str) -> Response:
        ...     return process(path)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            metrics_collector = MetricsCollector()
            labels = {"function": func.__name__} if include_labels else None
            metrics_collector.increment_counter(f"{metric_name}_total", labels)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics_collector.increment_counter(
                    f"{metric_name}_success_total", labels
                )
                metrics_collector.observe_histogram(
                    f"{metric_name}_duration_seconds", duration, labels
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_labels = (
                    {**labels, "error": type(e).__name__}
                    if labels
                    else {"error": type(e).__name__}
                )
                metrics_collector.increment_counter(
                    f"{metric_name}_failure_total", error_labels
                )
                metrics_collector.observe_histogram(
                    f"{metric_name}_duration_seconds", duration, labels
                )
                raise

        return wrapper

    return decorator


def monitor_metrics_async(
    metric_name: str, 
    include_labels: bool = True
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    异步监控指标装饰器
    
    为异步函数提供指标收集功能，自动记录调用次数、成功/失败次数和执行时间。
    
    Args:
        metric_name (str): 指标名称前缀，会自动添加 _total, _success_total, _failure_total, 
                          _duration_seconds 等后缀。
        include_labels (bool): 是否包含函数名作为标签。默认为 True。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的带监控异步函数
        
    Raises:
        Exception: 原函数抛出的任何异常都会被重新抛出，但在抛出前会记录失败指标。
        
    Example:
        >>> @monitor_metrics_async("async_operations")
        ... async def process_batch(items: list) -> int:
        ...     return len(items)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            metrics_collector = MetricsCollector()
            labels = {"function": func.__name__} if include_labels else None
            metrics_collector.increment_counter(f"{metric_name}_total", labels)

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics_collector.increment_counter(
                    f"{metric_name}_success_total", labels
                )
                metrics_collector.observe_histogram(
                    f"{metric_name}_duration_seconds", duration, labels
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_labels = (
                    {**labels, "error": type(e).__name__}
                    if labels
                    else {"error": type(e).__name__}
                )
                metrics_collector.increment_counter(
                    f"{metric_name}_failure_total", error_labels
                )
                metrics_collector.observe_histogram(
                    f"{metric_name}_duration_seconds", duration, labels
                )
                raise

        return wrapper

    return decorator


def publish_event(
    event_type: str, 
    success_only: bool = True
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    事件发布装饰器
    
    在函数执行成功或失败时自动发布事件。
    可用于解耦业务逻辑和事件通知。
    
    Args:
        event_type (str): 事件类型标识符，会在成功/失败时添加 .success 或 .error 后缀。
        success_only (bool): 是否只在函数执行成功时发布事件。如果为 False，失败时也会发布。默认为 True。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的函数
        
    Raises:
        Exception: 原函数抛出的异常会被重新抛出（无论 success_only 为何值）。
        
    Example:
        >>> @publish_event("user.created", success_only=True)
        ... def create_user(username: str) -> User:
        ...     return User(username)
        ...
        >>> @publish_event("payment.processed", success_only=False)
        ... def process_payment(amount: float) -> bool:
        ...     return True
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from LStartlet.core import event_bus, BaseEvent
            
            try:
                result = func(*args, **kwargs)
                # 发布成功事件
                success_event_type = f"{event_type}.success"
                if not event_bus._type_registry.is_registered(success_event_type):
                    # 动态注册简单事件类型
                    class SuccessEvent(BaseEvent):
                        EVENT_TYPE = success_event_type
                        
                        def __init__(self, func_name: str, result: Any):
                            super().__init__(self.EVENT_TYPE)
                            self.func_name = func_name
                            self.result = result
                        
                        def get_payload(self) -> dict:
                            return {"function": self.func_name, "result": self.result}
                    
                    event_bus._type_registry.register_event_type(
                        success_event_type, SuccessEvent, "decorator"
                    )
                
                success_event = event_bus._type_registry.create_event(
                    success_event_type, func.__name__, result
                )
                event_bus.publish(success_event)
                return result
            except Exception as e:
                if not success_only:
                    # 发布失败事件
                    error_event_type = f"{event_type}.error"
                    if not event_bus._type_registry.is_registered(error_event_type):
                        class ErrorEvent(BaseEvent):
                            EVENT_TYPE = error_event_type
                            
                            def __init__(self, func_name: str, error: Exception):
                                super().__init__(self.EVENT_TYPE)
                                self.func_name = func_name
                                self.error = str(error)
                                self.error_type = type(error).__name__
                            
                            def get_payload(self) -> dict:
                                return {
                                    "function": self.func_name,
                                    "error": self.error,
                                    "error_type": self.error_type
                                }
                    
                        event_bus._type_registry.register_event_type(
                            error_event_type, ErrorEvent, "decorator"
                        )
                    
                    error_event = event_bus._type_registry.create_event(
                        error_event_type, func.__name__, e
                    )
                    event_bus.publish(error_event)
                raise

        return wrapper

    return decorator


def validate_config(
    config_key: str, 
    validator_func: Optional[Callable[[Any], bool]] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    配置验证装饰器
    
    在函数执行前验证指定的配置项，确保配置有效后再执行业务逻辑。
    支持使用默认验证（检查配置是否存在）或自定义验证函数。
    
    Args:
        config_key (str): 配置项的键名，用于从配置管理器获取配置值。
        validator_func (Optional[Callable[[Any], bool]]): 自定义验证函数，接收配置值并返回布尔值。
                                                         如果为 None，则只检查配置值是否为 None。默认为 None。
        
    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: 装饰器函数，返回包装后的函数
        
    Raises:
        ValueError: 当配置项验证失败时抛出，包含配置键和当前值的信息。
        
    Example:
        >>> @validate_config("database.url")
        ... def connect_to_db() -> Connection:
        ...     return create_connection()
        ...
        >>> @validate_config("api.timeout", lambda x: x > 0 and x < 60)
        ... def call_external_api() -> Response:
        ...     return http_get()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from LStartlet.core.config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_value = config_manager.get_config(config_key)

            is_valid = True
            if validator_func:
                is_valid = validator_func(config_value)
            elif config_value is None:
                is_valid = False

            if not is_valid:
                raise ValueError(f"配置项 '{config_key}' 验证失败，值: {config_value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def cached(maxsize: int = 128, ttl: Optional[float] = None, typed: bool = False):
    """
    缓存装饰器
    提供LRU缓存和TTL过期功能

    Args:
        maxsize: 缓存最大大小
        ttl: 缓存过期时间（秒）
        typed: 是否区分参数类型

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache: Dict[Any, Any] = {}
        cache_lock = threading.Lock()
        timestamps: Dict[Any, float] = {}

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 构建缓存键
            key_args = args
            if kwargs:
                key = (key_args, tuple(sorted(kwargs.items())))
            else:
                key = key_args

            current_time = time.time()

            with cache_lock:
                # 清理过期缓存
                if ttl is not None:
                    expired_keys = [
                        k
                        for k, timestamp in timestamps.items()
                        if current_time - timestamp > ttl
                    ]
                    for k in expired_keys:
                        cache.pop(k, None)
                        timestamps.pop(k, None)

                # 检查缓存命中
                if key in cache:
                    return cache[key]

            # 执行函数
            result = func(*args, **kwargs)

            with cache_lock:
                # 管理缓存大小
                if len(cache) >= maxsize:
                    # 移除最旧的项（简单的FIFO策略）
                    oldest_key = next(iter(cache))
                    cache.pop(oldest_key, None)
                    timestamps.pop(oldest_key, None)

                cache[key] = result
                timestamps[key] = current_time

            return result

        return wrapper

    return decorator


def plugin_component(component_id: Optional[str] = None, category: str = "general"):
    """
    插件组件装饰器
    用于标记类为插件组件，支持延迟注册到插件管理器

    Args:
        component_id: 组件ID，如果为None则使用类名
        category: 组件分类

    Returns:
        装饰器函数
    """

    def decorator(cls: Type[Any]) -> Type[Any]:
        # 设置组件元数据
        cls._is_plugin_component = True  # type: ignore
        cls._plugin_component_id = component_id or cls.__name__  # type: ignore
        cls._plugin_category = category  # type: ignore
        return cls

    return decorator


def plugin_event_handler(
    event_type: Optional[str] = None,
    priority: int = 0,
    cancelable: bool = False,
):
    """
    插件事件处理器装饰器
    
    将方法标记为事件处理器，并自动注册到事件总线。
    
    Args:
        event_type (Optional[str]): 事件类型名称，如果为None则从方法参数推断
        priority (int): 处理器优先级，默认为0（数值越大优先级越高）
        cancelable (bool): 是否可取消事件，默认为False
        
    Returns:
        Callable: 装饰器函数
        
    Example:
        >>> class MyPlugin(PluginBase):
        ...     @plugin_event_handler(event_type="app.startup")
        ...     def on_startup(self, event):
        ...         pass
    """
    def decorator(func):
        # 设置事件处理器元数据
        func._event_handler_metadata = {
            'event_type': event_type,
            'priority': priority,
            'cancelable': cancelable
        }
        return func
    return decorator


def config(
    key: Optional[str] = None,
    default_value: Any = None,
    value_type: Optional[Type[Any]] = None,
    description: str = "",
    validator: Optional[Callable[[Any], bool]] = None,
    schema: Optional[Dict] = None,
    protected: bool = False,
    auto_register: bool = True
):
    """
    配置项装饰器
    
    用于声明式地定义和注册配置项，简化配置管理。
    支持类属性和函数两种使用方式。
    
    Args:
        key (Optional[str]): 配置键名，如果为None则从被装饰的对象名推断
        default_value (Any): 默认值
        value_type (Optional[Type[Any]]): 值的类型，如果为None则从default_value推断
        description (str): 配置项描述
        validator (Optional[Callable[[Any], bool]]): 自定义验证函数
        schema (Optional[Dict]): JSON Schema验证规则
        protected (bool): 是否为受保护配置（用户不可修改），默认为False
        auto_register (bool): 是否自动注册到配置管理器，默认为True
        
    Returns:
        Callable: 装饰器函数
        
    Example:
        # 类属性装饰器用法
        >>> class AppConfig:
        ...     @config(key="database.host", default_value="localhost", description="数据库主机")
        ...     def database_host(self): pass
        ...     
        ...     @config(default_value=5432, description="数据库端口")
        ...     def database_port(self): pass
        
        # 函数装饰器用法  
        >>> @config(key="app.debug", default_value=False, description="调试模式")
        ... def app_debug_config(): pass
    """
    def decorator(obj):
        from LStartlet.core.config import register_config
        
        # 推断配置键名
        actual_key = key or getattr(obj, '__name__', obj.__class__.__name__)
        
        # 推断值类型
        actual_value_type = value_type or type(default_value) if default_value is not None else str
        
        # 自动注册配置项
        if auto_register:
            try:
                register_config(
                    key=actual_key,
                    default_value=default_value,
                    value_type=actual_value_type,
                    description=description,
                    validator=validator,
                    schema=schema
                )
                
                # 如果是受保护配置，需要特殊处理（当前ConfigManager不直接支持）
                # 这里可以记录到特殊的配置源中
                if protected:
                    from LStartlet.core.config import set_config
                    # 标记为系统配置源
                    set_config(f"_system.{actual_key}", True)
                    
            except Exception as e:
                from LStartlet.core.logger import error
                error(f"Failed to register config {actual_key}: {e}")
        
        # 设置配置元数据供其他组件使用
        if hasattr(obj, '__dict__'):
            obj._config_metadata = {
                'key': actual_key,
                'default_value': default_value,
                'value_type': actual_value_type,
                'description': description,
                'protected': protected
            }
        
        return obj
    
    return decorator


def service(
    lifetime: Union[str, ServiceLifetime] = "transient",
    container: Optional[ServiceContainer] = None
):
    """
    服务装饰器 - 自动注册类到DI容器
    
    Args:
        lifetime: 服务生命周期 ("transient", "singleton", "scoped")
        container: 指定容器实例，默认使用默认容器
        
    Example:
        @service(lifetime="singleton")
        class DatabaseService:
            def __init__(self, connection_string: str = "default"):
                self.connection_string = connection_string
                
        @service(lifetime="transient")  
        class BusinessService:
            def __init__(self, db: DatabaseService):
                self.db = db
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # 解析生命周期
        if isinstance(lifetime, str):
            lifetime_enum = ServiceLifetime(lifetime.lower())
        else:
            lifetime_enum = lifetime
            
        # 获取容器
        target_container = container or get_default_container()
        
        # 注册服务
        target_container.register(
            service_type=cls,
            implementation_type=cls,
            lifetime=lifetime_enum
        )
        
        # 添加元数据供其他组件使用
        cls._service_metadata = {
            'lifetime': lifetime_enum,
            'container': target_container
        }
        
        return cls
    return decorator


def service_factory(
    lifetime: Union[str, ServiceLifetime] = "transient",
    container: Optional[ServiceContainer] = None
):
    """
    服务工厂装饰器 - 使用工厂函数创建服务
    
    Args:
        lifetime: 服务生命周期
        container: 指定容器实例
        
    Example:
        @service_factory(lifetime="singleton")
        def create_database_service(container: ServiceContainer) -> DatabaseService:
            config = container.resolve(ConfigManager)
            conn_str = config.get_config("database.connection")
            return DatabaseService(conn_str)
    """
    def decorator(factory_func: Callable[[ServiceContainer], T]) -> Callable[[ServiceContainer], T]:
        # 解析生命周期
        if isinstance(lifetime, str):
            lifetime_enum = ServiceLifetime(lifetime.lower())
        else:
            lifetime_enum = lifetime
            
        # 获取容器
        target_container = container or get_default_container()
        
        # 注册工厂函数
        target_container.register(
            service_type=get_type_hints(factory_func).get('return'),
            factory=factory_func,
            lifetime=lifetime_enum
        )
        
        return factory_func
    return decorator


def service_instance(
    lifetime: Union[str, ServiceLifetime] = "singleton",
    container: Optional[ServiceContainer] = None
):
    """
    服务实例装饰器 - 注册预创建的实例
    
    Args:
        lifetime: 服务生命周期（通常为singleton）
        container: 指定容器实例
        
    Example:
        @service_instance(lifetime="singleton")
        def database_instance() -> DatabaseService:
            return DatabaseService("pre_configured_connection")
    """
    def decorator(instance_func: Callable[[], T]) -> Callable[[], T]:
        # 解析生命周期
        if isinstance(lifetime, str):
            lifetime_enum = ServiceLifetime(lifetime.lower())
        else:
            lifetime_enum = lifetime
            
        # 获取容器
        target_container = container or get_default_container()
        
        # 创建实例
        instance = instance_func()
        
        # 注册实例
        target_container.register(
            service_type=get_type_hints(instance_func).get('return'),
            instance=instance,
            lifetime=lifetime_enum
        )
        
        return instance_func
    return decorator


def get_service(service_type: Type[T], container: Optional[ServiceContainer] = None) -> T:
    """
    获取服务实例 - 简化版resolve
    
    Args:
        service_type: 服务类型
        container: 指定容器实例，默认使用默认容器
        
    Returns:
        服务实例
        
    Example:
        db_service = get_service(DatabaseService)
    """
    target_container = container or get_default_container()
    return target_container.resolve(service_type)


def auto_inject(func: Callable[..., T]) -> Callable[..., T]:
    """
    自动注入装饰器 - 自动将DI容器中的服务注入到函数参数
    
    Example:
        @auto_inject
        def process_data(data_id: int, db: DatabaseService, logger: MultiProcessLogger):
            logger.info(f"Processing data {data_id}")
            return db.query(f"SELECT * FROM data WHERE id = {data_id}")
            
        # 调用时只需传递非DI参数
        result = process_data(123)  # db和logger自动注入
    """
    from inspect import signature, Parameter
    from typing import get_type_hints
    
    sig = signature(func)
    # 使用eval_str=True来处理字符串类型注解
    type_hints = get_type_hints(func, globalns=func.__globals__, localns=None, include_extras=False)
    container = get_default_container()
    
    def wrapper(*args, **kwargs):
        # 获取已提供的参数
        bound_args = sig.bind_partial(*args, **kwargs)
        provided_args = set(bound_args.arguments.keys())
        
        # 准备完整参数
        full_kwargs = dict(bound_args.arguments)
        
        # 为缺失的参数尝试从DI容器注入
        for param_name, param in sig.parameters.items():
            if param_name in provided_args:
                continue
                
            # 跳过VAR_POSITIONAL和VAR_KEYWORD参数
            if param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
                continue
                
            # 检查是否有类型注解
            if param.annotation != Parameter.empty:
                param_type = type_hints.get(param_name, param.annotation)
                try:
                    # 尝试从DI容器解析
                    service_instance = container.resolve(param_type)
                    full_kwargs[param_name] = service_instance
                except ServiceResolutionError:
                    # 如果无法解析，检查是否有默认值
                    if param.default != Parameter.empty:
                        full_kwargs[param_name] = param.default
                    else:
                        raise ValueError(f"Cannot resolve parameter {param_name} of type {param_type}")
            else:
                # 无类型注解，检查默认值
                if param.default != Parameter.empty:
                    full_kwargs[param_name] = param.default
                else:
                    raise ValueError(f"Parameter {param_name} has no type annotation and no default value")
        
        return func(**full_kwargs)
    
    return wrapper


def handle_errors(
    on_error: Optional[Callable[[Exception, Dict[str, Any]], Any]] = None,
    on_success: Optional[Callable[[Any, Dict[str, Any]], Any]] = None,
    default_return: Any = None,
    error_code: str = "UNHANDLED_ERROR",
    context: Optional[Dict[str, Any]] = None,
    re_raise: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    增强型错误处理装饰器
    
    提供更灵活的错误处理能力，支持自定义错误回调、成功回调和上下文。
    
    Args:
        on_error: 错误处理回调函数，接收异常和上下文，返回任意值
        on_success: 成功处理回调函数，接收结果和上下文，无返回值
        default_return: 发生异常时的默认返回值（当on_error未提供或返回None时使用）
        error_code: 错误代码标识
        context: 额外的上下文信息
        re_raise: 是否在处理后重新抛出异常
        
    Returns:
        装饰器函数
        
    Example:
        >>> @handle_errors(
        ...     on_error=lambda e, ctx: print(f"Error: {e}, Context: {ctx}"),
        ...     on_success=lambda r, ctx: print(f"Success: {r}"),
        ...     context={"module": "calculator"}
        ... )
        ... def divide(a: int, b: int) -> float:
        ...     return a / b
        ...
        >>> result = divide(10, 2)  # Success: 5.0
        >>> result = divide(10, 0)  # Error: division by zero, Context: {...}
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 构建完整的上下文
            full_context = {
                "function": func.__name__,
                "module": func.__module__,
                "error_code": error_code,
                **(context or {})
            }
            
            try:
                result = func(*args, **kwargs)
                # 成功回调
                if on_success is not None:
                    on_success(result, full_context)
                return result
            except Exception as e:
                # 错误回调
                error_result = None
                if on_error is not None:
                    try:
                        error_result = on_error(e, full_context)
                    except Exception as callback_error:
                        # 回调函数自身出错，记录但不影响主流程
                        warning(f"Error handler callback failed: {callback_error}")
                
                # 如果回调没有返回值，使用默认返回值
                if error_result is None:
                    error_result = default_return
                
                # 记录错误到全局错误处理器
                from LStartlet.core.error import handle_error
                handle_error(e, full_context)
                
                # 决定是否重新抛出异常
                if re_raise:
                    raise
                else:
                    return error_result
                    
        return wrapper
    return decorator

# 向后兼容的装饰器别名
from .register import register_service as auto_register
from .register import register_plugin as auto_plugin_register  
from .register import register_command as command

__all__ = [
    # 枚举
    "PermissionLevel",
    # 类
    "MetricsCollector",
    # 错误处理装饰器
    "with_error_handling",
    "with_error_handling_async",
    "handle_errors",
    # 日志装饰器
    "with_logging",
    "with_logging_async",
    # 权限装饰器
    "require_permission",
    "require_permission_async",
    # 监控指标装饰器
    "monitor_metrics",
    "monitor_metrics_async",
    # 事件发布装饰器
    "publish_event",
    # 配置验证装饰器
    "validate_config",
    # 缓存装饰器
    "cached",
    "cached_async",
    # 插件装饰器
    "plugin_component",
    "plugin_event_handler",
    # 配置装饰器
    "config",
    # DI装饰器
    "service",
    "service_factory",
    "service_instance",
    "get_service",
    "auto_inject",
]
