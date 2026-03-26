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
    CommandRegistry,
    command_registry,
    CommandExecutionEvent,
    CommandCompletedEvent, 
    CommandFailedEvent,
    CommandCancelledEvent
)

# 配置系统
from .config import (
    ConfigManager,
    get_config,
    set_config,
    has_config,
    get_all_configs,
    register_config,
    add_config_listener,
    remove_config_listener,
    add_config_key_listener,
    remove_config_key_listener,
    save_config,
    load_config,
    reset_all_configs,
    reset_config
)

# 依赖注入系统
from .di import (
    ServiceContainer,
    ServiceLifetime,
    configure_default_container,
    ServiceResolutionError,
    ServiceRegistrationError
)

# 错误处理
from .error import ErrorHandler

# 事件系统
from .event import (
    BaseEvent,
    CancelableEvent,
    EventMetadata,
    EventTypeRegistry,
    EventHandler,
    LambdaEventHandler,
    CompositeEventHandler,
    EventBus,
    event_bus
)

# 日志系统
from .logger import (
    MultiProcessLogger,
    LoggerCore,
    LogLevel,
    ConsoleHandler,
    RotatingFileHandler,
    configure_logger,
    set_process_type,
    debug,
    info,
    warning,
    error,
    critical
)

# 路径管理
from .path import PathManager, get_project_root, join_paths

# 持久化
from .persistence import PersistenceManager, initialize_persistence_system

# 进程管理
from .process import GlobalProcessManager, ProcessInfo

# 调度器
from .scheduler import (
    Scheduler,
    ProcessManager as SchedulerProcessManager,
    TaskDispatcher,
    ConfigManager as SchedulerConfigManager,
    SchedulerFactory,
    TickComponent,
    TickConfig,
    SimpleThreadScheduler,
    ThreadSafeScheduler
)

# 系统检测
from .system import SystemDetector, SystemConfigManager

# 版本控制
from .version_control import (
    VersionController,
    ChangeAnalyzer,
    IncrementalPackageGenerator,
    DependencyResolver
)

# CI/CD
from .cicd import (
    Pipeline,
    Stage,
    Step,
    Builder,
    Tester,
    Deployer,
    CICDController,
    DependencyInstaller
)

# 框架版本
__version__ = "1.0.0"

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
    'command_registry',
    'CommandExecutionEvent',
    'CommandCompletedEvent',
    'CommandFailedEvent',
    'CommandCancelledEvent',
    # 配置系统
    'ConfigManager',
    'get_config',
    'set_config',
    'has_config',
    'get_all_configs',
    'register_config',
    'add_config_listener',
    'remove_config_listener',
    'add_config_key_listener',
    'remove_config_key_listener',
    'save_config',
    'load_config',
    'reset_all_configs',
    'reset_config',
    # 依赖注入系统
    'ServiceContainer',
    'ServiceLifetime',
    'configure_default_container',
    'ServiceResolutionError',
    'ServiceRegistrationError',
    # 错误处理
    'ErrorHandler',
    # 事件系统
    'BaseEvent',
    'CancelableEvent',
    'EventMetadata',
    'EventTypeRegistry',
    'EventHandler',
    'LambdaEventHandler',
    'CompositeEventHandler',
    'EventBus',
    'event_bus',
    # 日志系统
    'MultiProcessLogger',
    'LoggerCore',
    'LogLevel',
    'ConsoleHandler',
    'RotatingFileHandler',
    'configure_logger',
    'set_process_type',
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    # 路径管理
    'PathManager',
    'get_project_root',
    'join_paths',
    # 持久化
    'PersistenceManager',
    'initialize_persistence_system',
    # 进程管理
    'GlobalProcessManager',
    'ProcessInfo',
    # 调度器
    'Scheduler',
    'SchedulerProcessManager',
    'TaskDispatcher',
    'SchedulerConfigManager',
    'SchedulerFactory',
    'TickComponent',
    'TickConfig',
    'SimpleThreadScheduler',
    'ThreadSafeScheduler',
    # 系统检测
    'SystemDetector',
    'SystemConfigManager',
    # 版本控制
    'VersionController',
    'ChangeAnalyzer',
    'IncrementalPackageGenerator',
    'DependencyResolver',
    # CI/CD
    'Pipeline',
    'Stage',
    'Step',
    'Builder',
    'Tester',
    'Deployer',
    'CICDController',
    'DependencyInstaller',
    # 版本
    '__version__'
]