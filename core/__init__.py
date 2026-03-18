"""Core module exports"""

# 装饰器
from .decorators import (
    with_error_handling,
    with_logging,
    plugin_component,
    plugin_event_handler,
    # 异步装饰器
    with_error_handling_async,
    with_logging_async,
    cached_async,
    # 权限装饰器
    require_permission,
    require_permission_async,
    PermissionLevel,
    # 监控装饰器
    monitor_metrics,
    monitor_metrics_async,
    MetricsCollector
)

# 命令系统
from .command import (
    BaseCommand,
    CommandResult,
    CommandMetadata,
    CommandExecutor,
    CommandRegistry
)

# 配置系统
from .config import ConfigManager

# 错误处理
from .error import ErrorHandler

# 事件系统
from .event import EventBus

# 日志系统函数
from .logger import info, debug, warning, error

# 路径管理
from .path import PathManager

# 持久化
from .persistence import PersistenceManager

# 调度器
from .scheduler import Scheduler

# 明确导出的符号
__all__ = [
    # 装饰器
    'with_error_handling',
    'with_logging', 
    'plugin_component',
    'plugin_event_handler',
    'with_error_handling_async',
    'with_logging_async',
    'cached_async',
    'require_permission',
    'require_permission_async',
    'PermissionLevel',
    'monitor_metrics',
    'monitor_metrics_async',
    'MetricsCollector',
    # 命令系统
    'BaseCommand',
    'CommandResult',
    'CommandMetadata',
    'CommandExecutor',
    'CommandRegistry',
    # 配置系统
    'ConfigManager',
    # 错误处理
    'ErrorHandler',
    # 事件系统
    'EventBus',
    # 日志系统
    'info',
    'debug',
    'warning',
    'error',
    # 路径管理
    'PathManager',
    # 持久化
    'PersistenceManager',
    # 调度器
    'Scheduler'
]
