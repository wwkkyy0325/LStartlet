"""核心装饰器模块
提供错误处理、日志记录、事件发布和配置验证等装饰器功能
"""

import time
import threading
from functools import wraps
from typing import Any, Callable, Optional, Dict, Type

from enum import Enum

# 核心模块导入
from core.error.exceptions import InfrastructureError
from core.logger import info, error as log_error, warning


class PermissionLevel(Enum):
    """权限级别枚举"""
    GUEST = 0
    USER = 1
    ADMIN = 2
    SYSTEM = 3


def with_error_handling(
    error_code: str = "UNHANDLED_ERROR",
    default_return: Any = None,
    log_level: str = "error"
):
    """
    错误处理装饰器
    
    Args:
        error_code: 错误代码
        default_return: 默认返回值
        log_level: 日志级别
        
    Returns:
        装饰器函数
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
    level: str = "info",
    measure_time: bool = False,
    include_args: bool = False
):
    """
    日志装饰器
    
    Args:
        level: 日志级别 ('debug', 'info', 'warning', 'error')
        measure_time: 是否测量执行时间
        include_args: 是否包含参数信息
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取日志函数
            log_func = getattr(__import__('core.logger'), level, __import__('core.logger').info)
            
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
    """指标收集器（模拟实现）"""
    
    _instance = None
    _metrics: Dict[str, Any]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._metrics = {}
        return cls._instance
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0):
        """增加计数器"""
        key = f"{name}_{str(labels) if labels else ''}"
        if key not in self._metrics:
            self._metrics[key] = 0.0
        self._metrics[key] += value
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """观察直方图值"""
        key = f"{name}_histogram_{str(labels) if labels else ''}"
        if key not in self._metrics:
            self._metrics[key] = []
        self._metrics[key].append(value)


# 异步装饰器
def with_error_handling_async(
    error_code: str = "UNHANDLED_ERROR",
    default_return: Any = None,
    log_level: str = "error"
):
    """异步错误处理装饰器"""
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
    level: str = "info",
    measure_time: bool = False,
    include_args: bool = False
):
    """异步日志装饰器"""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_func = getattr(__import__('core.logger'), level, __import__('core.logger').info)
            start_time = time.time() if measure_time else None
            if include_args:
                log_func(f"Starting async {func.__name__} with args={args}, kwargs={kwargs}")
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
                    log_func(f"Async {func.__name__} failed after {duration:.4f}s: {str(e)}")
                else:
                    log_func(f"Async {func.__name__} failed: {str(e)}")
                raise
        return wrapper
    return decorator


def cached_async(
    maxsize: int = 128,
    ttl: Optional[float] = None,
    typed: bool = False
):
    """异步缓存装饰器"""
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
):
    """权限检查装饰器"""
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
                        "function": func.__name__
                    }
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission_async(
    required_level: PermissionLevel,
    error_message: str = "Insufficient permissions"
):
    """异步权限检查装饰器"""
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
                        "function": func.__name__
                    }
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_metrics(
    metric_name: str,
    include_labels: bool = True
):
    """监控指标装饰器"""
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
                metrics_collector.increment_counter(f"{metric_name}_success_total", labels)
                metrics_collector.observe_histogram(f"{metric_name}_duration_seconds", duration, labels)
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_labels = {**labels, "error": type(e).__name__} if labels else {"error": type(e).__name__}
                metrics_collector.increment_counter(f"{metric_name}_failure_total", error_labels)
                metrics_collector.observe_histogram(f"{metric_name}_duration_seconds", duration, labels)
                raise
        return wrapper
    return decorator


def monitor_metrics_async(
    metric_name: str,
    include_labels: bool = True
):
    """异步监控指标装饰器"""
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
                metrics_collector.increment_counter(f"{metric_name}_success_total", labels)
                metrics_collector.observe_histogram(f"{metric_name}_duration_seconds", duration, labels)
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_labels = {**labels, "error": type(e).__name__} if labels else {"error": type(e).__name__}
                metrics_collector.increment_counter(f"{metric_name}_failure_total", error_labels)
                metrics_collector.observe_histogram(f"{metric_name}_duration_seconds", duration, labels)
                raise
        return wrapper
    return decorator


def publish_event(event_type: str, success_only: bool = True):
    """
    事件发布装饰器
    在函数执行成功或失败时自动发布事件
    
    Args:
        event_type: 事件类型
        success_only: 是否只在成功时发布事件
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                # 简化为记录日志
                info(f"Function {func.__name__} succeeded, event type: {event_type}.success")
                return result
            except Exception as e:
                if not success_only:
                    info(f"Function {func.__name__} failed, event type: {event_type}.error, error: {str(e)}")
                raise
        return wrapper
    return decorator


def validate_config(config_key: str, validator_func: Optional[Callable[[Any], bool]] = None):
    """
    配置验证装饰器
    在函数执行前验证配置项
    
    Args:
        config_key: 配置键
        validator_func: 自定义验证函数
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from core.config.config_manager import ConfigManager
            
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


def cached(
    maxsize: int = 128,
    ttl: Optional[float] = None,
    typed: bool = False
):
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
                        k for k, timestamp in timestamps.items() 
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


def plugin_event_handler(event_type: str, name: str = ""):
    """
    插件事件处理器装饰器
    用于标记方法为事件处理器
    
    Args:
        event_type: 事件类型
        name: 处理器名称
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., bool]) -> Callable[..., bool]:
        func._is_plugin_event_handler = True  # type: ignore
        func._handled_event_type = event_type  # type: ignore
        func._handler_name = name or func.__name__  # type: ignore
        return func
    return decorator
