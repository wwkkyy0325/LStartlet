"""
LStartlet Core Infrastructure Framework

A modular Python infrastructure framework providing high cohesion and low coupling
for Python applications through unified component management.

This framework offers standardized solutions for:
- Configuration Management: Type-safe configuration registration, validation, and persistence
- Dependency Injection: Service container with singleton/transient/scoped lifetimes
- Event System: Thread-safe event bus with publish/subscribe pattern
- Logging System: Multi-level logging with console/file output and structured logging
- Command System: Command pattern execution with event-driven lifecycle
- Task Scheduling: Process/task management with configurable scheduling strategies
- Path Management: Unified project structure awareness with cross-platform support
- Persistence: Multi-backend data storage with transaction support
- Error Handling: Global exception handling with structured error formatting
- Plugin System: Dynamic loading with lifecycle management and dependency resolution

Usage:
    from core import ConfigManager, ServiceContainer, EventBus, PluginManager
    
    # Initialize the framework
    config = ConfigManager()
    container = ServiceContainer()
    event_bus = EventBus()
    plugin_manager = PluginManager()
"""

import importlib.metadata

# Get version from package metadata (setuptools_scm)
try:
    __version__ = importlib.metadata.version("LStartlet")
except importlib.metadata.PackageNotFoundError:
    # Package is not installed, fallback to development version
    __version__ = "0.1.0.dev0"

# Import core module exports
from LStartlet.core import (
    # Decorators
    with_error_handling,
    with_logging,
    plugin_component,
    plugin_event_handler,
    with_error_handling_async,
    with_logging_async,
    cached_async,
    require_permission,
    require_permission_async,
    PermissionLevel,
    monitor_metrics,
    monitor_metrics_async,
    MetricsCollector,
    # Command System
    BaseCommand,
    CommandResult,
    CommandMetadata,
    CommandExecutor,
    CommandRegistry,
    command_registry,
    CommandExecutionEvent,
    CommandCompletedEvent,
    CommandFailedEvent,
    CommandCancelledEvent,
    # Specific command implementations
    EchoCommand,
    ShutdownCommand,
    ClearCacheCommand,
    SystemInfoCommand,
    # Configuration System
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
    reset_config,
    # Dependency Injection System
    ServiceContainer,
    ServiceLifetime,
    configure_default_container,
    ServiceResolutionError,
    ServiceRegistrationError,
    # Error Handling
    ErrorHandler,
    handle_error,
    format_error,
    log_error,
    get_error_info,
    ErrorFormatter,
    register_global_error_handler,
    error_handler,
    # Event System
    BaseEvent,
    CancelableEvent,
    EventMetadata,
    EventTypeRegistry,
    EventHandler,
    LambdaEventHandler,
    CompositeEventHandler,
    EventBus,
    event_bus,
    # Scheduler events
    SchedulerStatusEvent,
    ApplicationLifecycleEvent,
    ConfigItemRegisteredEvent,
    TaskSubmittedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    ProcessCreatedEvent,
    ProcessStartedEvent,
    ProcessStoppedEvent,
    ProcessFailedEvent,
    TickEvent,
    # UI events
    UIStyleUpdateEvent,
    UIConfigChangeEvent,
    UIStateChangeEvent,
    UIMountAreaEvent,
    UIComponentLifecycleEvent,
    RenderProcessReadyEvent,
    # Logging System
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
    # Path Management
    PathManager,
    get_project_root,
    join_paths,
    # Persistence
    PersistenceManager,
    initialize_persistence_system,
    # Persistence models and storage
    StorageItem,
    StorageConfig,
    TransactionRecord,
    KVStorage,
    # Process Management
    GlobalProcessManager,
    ProcessInfo,
    # Scheduler
    Scheduler,
    SchedulerProcessManager,
    TaskDispatcher,
    SchedulerConfigManager,
    SchedulerFactory,
    TickComponent,
    TickConfig,
    SimpleThreadScheduler,
    ThreadSafeScheduler,
    # System Detection
    SystemDetector,
    SystemConfigManager,
    # Version Control
    VersionController,
    ChangeAnalyzer,
    IncrementalPackageGenerator,
    DependencyResolver,
    # CI/CD
    Pipeline,
    Stage,
    Step,
    Builder,
    Tester,
    Deployer,
    CICDController,
    DependencyInstaller,
)

# Import plugin system exports
from LStartlet.plugin import (
    PluginBase,
    IPlugin,
    IPluginManager,
    PluginManager,
    plugin_component,
    plugin_event_handler,
)

# Define public API
__all__ = [
    # Core framework version
    "__version__",
    # Core module exports (same as core.__all__)
    # Decorators
    "with_error_handling",
    "with_logging",
    "plugin_component",
    "plugin_event_handler",
    "with_error_handling_async",
    "with_logging_async",
    "cached_async",
    "require_permission",
    "require_permission_async",
    "PermissionLevel",
    "monitor_metrics",
    "monitor_metrics_async",
    "MetricsCollector",
    # Command System
    "BaseCommand",
    "CommandResult",
    "CommandMetadata",
    "CommandExecutor",
    "CommandRegistry",
    "command_registry",
    "CommandExecutionEvent",
    "CommandCompletedEvent",
    "CommandFailedEvent",
    "CommandCancelledEvent",
    # Specific command implementations
    "EchoCommand",
    "ShutdownCommand",
    "ClearCacheCommand",
    "SystemInfoCommand",
    # Configuration System
    "ConfigManager",
    "get_config",
    "set_config",
    "has_config",
    "get_all_configs",
    "register_config",
    "add_config_listener",
    "remove_config_listener",
    "add_config_key_listener",
    "remove_config_key_listener",
    "save_config",
    "load_config",
    "reset_all_configs",
    "reset_config",
    # Dependency Injection System
    "ServiceContainer",
    "ServiceLifetime",
    "configure_default_container",
    "ServiceResolutionError",
    "ServiceRegistrationError",
    # Error Handling
    "ErrorHandler",
    "handle_error",
    "format_error",
    "log_error",
    "get_error_info",
    "ErrorFormatter",
    "register_global_error_handler",
    "error_handler",
    # Event System
    "BaseEvent",
    "CancelableEvent",
    "EventMetadata",
    "EventTypeRegistry",
    "EventHandler",
    "LambdaEventHandler",
    "CompositeEventHandler",
    "EventBus",
    "event_bus",
    # Scheduler events
    "SchedulerStatusEvent",
    "ApplicationLifecycleEvent",
    "ConfigItemRegisteredEvent",
    "TaskSubmittedEvent",
    "TaskStartedEvent",
    "TaskCompletedEvent",
    "TaskFailedEvent",
    "ProcessCreatedEvent",
    "ProcessStartedEvent",
    "ProcessStoppedEvent",
    "ProcessFailedEvent",
    "TickEvent",
    # UI events
    "UIStyleUpdateEvent",
    "UIConfigChangeEvent",
    "UIStateChangeEvent",
    "UIMountAreaEvent",
    "UIComponentLifecycleEvent",
    "RenderProcessReadyEvent",
    # Logging System
    "MultiProcessLogger",
    "LoggerCore",
    "LogLevel",
    "ConsoleHandler",
    "RotatingFileHandler",
    "configure_logger",
    "set_process_type",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    # Path Management
    "PathManager",
    "get_project_root",
    "join_paths",
    # Persistence
    "PersistenceManager",
    "initialize_persistence_system",
    # Persistence models and storage
    "StorageItem",
    "StorageConfig",
    "TransactionRecord",
    "KVStorage",
    # Process Management
    "GlobalProcessManager",
    "ProcessInfo",
    # Scheduler
    "Scheduler",
    "SchedulerProcessManager",
    "TaskDispatcher",
    "SchedulerConfigManager",
    "SchedulerFactory",
    "TickComponent",
    "TickConfig",
    "SimpleThreadScheduler",
    "ThreadSafeScheduler",
    # System Detection
    "SystemDetector",
    "SystemConfigManager",
    # Version Control
    "VersionController",
    "ChangeAnalyzer",
    "IncrementalPackageGenerator",
    "DependencyResolver",
    # CI/CD
    "Pipeline",
    "Stage",
    "Step",
    "Builder",
    "Tester",
    "Deployer",
    "CICDController",
    "DependencyInstaller",
    # Plugin System
    "PluginBase",
    "IPlugin",
    "IPluginManager",
    "PluginManager",
]
