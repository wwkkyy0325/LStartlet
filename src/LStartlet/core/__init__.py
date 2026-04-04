"""Core module exports"""

# 装饰器 - 导入所有实际存在的装饰器
from .decorators import (
    # 错误处理装饰器
    with_error_handling,
    with_error_handling_async,
    
    # 日志装饰器
    with_logging,
    with_logging_async,
    log_calls,  # 新增增强型日志装饰器
    
    # 权限装饰器  
    require_permission,
    require_permission_async,
    PermissionLevel,
    
    # 缓存装饰器
    cached,
    cached_async,
    
    # 监控装饰器
    monitor_metrics,
    monitor_metrics_async,
    MetricsCollector,
    
    # 配置装饰器
    config,
    
    # 插件装饰器
    plugin_component,
    plugin_event_handler,
    
    # DI装饰器
    service,
    service_factory,
    service_instance,
    get_service,
    auto_inject,
    
    # 事件装饰器
    publish_event,
)

# 统一注册装饰器  
from .register import (
    register_service,
    register_plugin,
    register_command,
)

# 命令系统
from .command import (
    BaseCommand,
    CommandResult,
    CommandMetadata,
)

# 配置系统
from .config import (
    get_config,
    set_config,
    watch_config,
    ConfigWatcher,
)

# 依赖注入系统
from .di import (
    ServiceContainer,
    ServiceLifetime,
    get_default_container,
)

# 错误处理
from .error import (
    ErrorHandler,
    handle_error,
    format_error,
    log_error,
    get_error_info,
    ErrorFormatter,
    register_global_error_handler,
    get_error_handler,  # 替代 error_handler 全局实例
)

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
    event_bus,
    EventInterceptor,  # 新增
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
    critical,
)

# 路径管理
from .path import PathManager, get_project_root, join_paths

# 持久化
from .persistence import PersistenceManager, initialize_persistence_system
# 持久化 - 模型和存储
from .persistence.models.persistence_models import (
    StorageItem,
    StorageConfig,
    TransactionRecord,
)
from .persistence.storage.kv_storage import KVStorage

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
    ThreadSafeScheduler,
)

# 系统检测
from .system import SystemDetector, SystemConfigManager

# 版本控制
from .version_control import (
    VersionController,
    ChangeAnalyzer,
    IncrementalPackageGenerator,
    DependencyResolver,
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
    DependencyInstaller,
)