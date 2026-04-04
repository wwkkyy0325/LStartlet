# LStartlet

A modular, high-cohesion, low-coupling infrastructure framework for Python applications.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20optimized-orange)]()

## Overview

LStartlet provides a comprehensive foundation for building robust Python applications with standardized components. Designed as a pure scaffolding framework without domain-specific code, it offers unified solutions for configuration management, dependency injection, event handling, logging, and more.

## Quick Start

```python
from LStartlet import (
    ConfigManager, ServiceContainer, EventBus, PluginManager,
    info, debug, error, handle_error, format_error,
    Scheduler, PathManager, PersistenceManager
)

# Initialize core components
config = ConfigManager()
container = ServiceContainer()
event_bus = EventBus()

# Use built-in utilities
info("Application started")
scheduler = Scheduler()
```

## Public API Reference

### Core Framework Components

#### Configuration Management
- **Classes**: `ConfigManager`
- **Functions**: `get_config()`, `set_config()`, `has_config()`, `get_all_configs()`, `register_config()`, `save_config()`, `load_config()`, `reset_config()`, `reset_all_configs()`
- **Event Listeners**: `add_config_listener()`, `remove_config_listener()`, `add_config_key_listener()`, `remove_config_key_listener()`

#### Dependency Injection
- **Classes**: `ServiceContainer`, `ServiceLifetime`
- **Functions**: `configure_default_container()`
- **Exceptions**: `ServiceResolutionError`, `ServiceRegistrationError`

#### Event System
- **Classes**: `BaseEvent`, `CancelableEvent`, `EventMetadata`, `EventTypeRegistry`, `EventHandler`, `LambdaEventHandler`, `CompositeEventHandler`, `EventBus`
- **Instances**: `event_bus` (global instance)

#### Logging System
- **Classes**: `MultiProcessLogger`, `LoggerCore`, `LogLevel`, `ConsoleHandler`, `RotatingFileHandler`
- **Functions**: `configure_logger()`, `set_process_type()`
- **Log Methods**: `debug()`, `info()`, `warning()`, `error()`, `critical()`

#### Command System
- **Classes**: `BaseCommand`, `CommandResult`, `CommandMetadata`, `CommandExecutor`, `CommandRegistry`
- **Instances**: `command_registry` (global instance)
- **Events**: `CommandExecutionEvent`, `CommandCompletedEvent`, `CommandFailedEvent`, `CommandCancelledEvent`

#### Error Handling
- **Classes**: `ErrorHandler`, `ErrorFormatter`
- **Functions**: `handle_error()`, `format_error()`, `log_error()`, `get_error_info()`, `register_global_error_handler()`
- **Instances**: `error_handler` (global instance)

#### Task Scheduling
- **Classes**: `Scheduler`, `SchedulerProcessManager`, `TaskDispatcher`, `SchedulerConfigManager`, `SchedulerFactory`, `TickComponent`, `TickConfig`, `SimpleThreadScheduler`, `ThreadSafeScheduler`

#### Path Management
- **Classes**: `PathManager`
- **Functions**: `get_project_root()`, `join_paths()`

#### Persistence
- **Classes**: `PersistenceManager`
- **Functions**: `initialize_persistence_system()`

#### Process Management
- **Classes**: `GlobalProcessManager`, `ProcessInfo`

#### System Detection
- **Classes**: `SystemDetector`, `SystemConfigManager`

#### Version Control & CI/CD
- **Version Control**: `VersionController`, `ChangeAnalyzer`, `IncrementalPackageGenerator`, `DependencyResolver`
- **CI/CD**: `Pipeline`, `Stage`, `Step`, `Builder`, `Tester`, `Deployer`, `CICDController`, `DependencyInstaller`

### Plugin System
- **Classes**: `PluginBase`, `IPlugin`, `IPluginManager`, `PluginManager`
- **Decorators**: `plugin_component`, `plugin_event_handler`

### Decorators & Utilities
- **Error Handling**: `with_error_handling`, `with_error_handling_async`
- **Logging**: `with_logging`, `with_logging_async`
- **Caching**: `cached_async`, `cached`
- **Permissions**: `require_permission`, `require_permission_async`, `PermissionLevel`
- **Metrics**: `monitor_metrics`, `monitor_metrics_async`, `MetricsCollector`
- **Service Registration**: `auto_register`
- **Plugin Registration**: `auto_plugin_register`

## Usage Examples

### Basic Configuration
```python
from LStartlet import get_config, set_config, register_config

# Register and use configuration
register_config("app.debug", False, bool, "Debug mode")
debug_mode = get_config("app.debug")
set_config("app.debug", True)
```

### Dependency Injection
```python
from LStartlet import ServiceContainer

class DatabaseService:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

container = ServiceContainer()
container.register(DatabaseService, DatabaseService, connection_string="sqlite:///:memory:")
db = container.resolve(DatabaseService)
```

### Event Handling
```python
from LStartlet import event_bus, BaseEvent

class UserLoginEvent(BaseEvent):
    def __init__(self, user_id: str):
        self.user_id = user_id

def on_user_login(event):
    print(f"User {event.user_id} logged in")

event_bus.subscribe(UserLoginEvent, on_user_login)
event_bus.publish(UserLoginEvent("user123"))
```

### Error Handling
```python
from LStartlet import handle_error, format_error

try:
    risky_operation()
except Exception as e:
    handle_error(e)
    error_details = format_error(e)
    print(error_details)
```

### Plugin Development
```python
from LStartlet import PluginBase

class MyPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "MyPlugin"
        self.version = "1.0.0"
    
    def activate(self):
        print(f"{self.name} activated")
```

### Automatic Service Registration
```python
from LStartlet import auto_register, ServiceLifetime, get_default_container

# Register as self-type service (TRANSIENT lifecycle)
@auto_register()
class EmailService:
    def send_email(self, to: str, subject: str, body: str):
        print(f"Sending email to {to}: {subject}")

# Register as interface service (SINGLETON lifecycle)
from abc import ABC, abstractmethod

class NotificationService(ABC):
    @abstractmethod
    def notify(self, message: str):
        pass

@auto_register(service_type=NotificationService, lifetime=ServiceLifetime.SINGLETON)
class EmailNotificationService(NotificationService):
    def notify(self, message: str):
        print(f"Email notification: {message}")

# Services are automatically registered and can be resolved
container = get_default_container()
email_service = container.resolve(EmailService)
notification_service = container.resolve(NotificationService)
```

### Automatic Plugin Registration
```python
from LStartlet import auto_plugin_register, PluginBase, get_default_container

# Automatically register a plugin with metadata and dependencies
@auto_plugin_register(
    plugin_id="com.example.email",
    name="Email Plugin",
    version="1.0.0",
    description="Handles email notifications",
    order=10,
    dependencies={"core.logger": ">=1.0.0"},
    lifetime=ServiceLifetime.SINGLETON
)
class EmailPlugin(PluginBase):
    def __init__(self):
        # Must call parent constructor with the same parameters
        super().__init__(
            plugin_id="com.example.email",
            name="Email Plugin",
            version="1.0.0",
            description="Handles email notifications"
        )
    
    def initialize(self) -> None:
        print(f"{self.name} initialized")
    
    def start(self) -> None:
        print(f"{self.name} started")
    
    def stop(self) -> None:
        print(f"{self.name} stopped")
    
    def cleanup(self) -> None:
        print(f"{self.name} cleaned up")

# Plugin is automatically registered and can be resolved
container = get_default_container()
email_plugin = container.resolve(EmailPlugin)
```

### Automatic Command Registration
```python
from LStartlet import command, BaseCommand, CommandResult

@command(name="echo", description="回显输入的消息", category="utility")
class EchoCommand(BaseCommand):
    def __init__(self):
        # 必须调用父类构造函数并传入装饰器设置的元数据
        super().__init__(self._command_metadata)
    
    def execute(self, **kwargs: Any) -> CommandResult:
        message = kwargs.get("message", "")
        if not message:
            return CommandResult(False, "message parameter is required")
        return CommandResult(True, f"Echo: {message}", {"original_message": message})

# 命令会自动注册到全局命令注册表中
from LStartlet.core.command import command_registry
echo_cmd = command_registry.get_command("echo")
result = echo_cmd.execute(message="Hello World")
```

## Installation

```bash
pip install -r requirements.txt
```

## Testing

Run the complete test suite:

```bash
python tests/run_tests.py
```

## Requirements

- **Python**: 3.9+
- **Core Dependencies**: 
  - `PyYAML>=6.0`
  - `psutil>=5.9.0`
- **Platform**: Optimized for Windows (compatible with WSL)

## Architecture Principles

- **High Cohesion, Low Coupling**: Each module has clear responsibilities with minimal dependencies
- **Unified Component Management**: Standardized interfaces across all framework components  
- **Type Safety**: Strong typing with runtime validation where appropriate
- **Extensibility**: Plugin system for adding custom functionality without modifying core code
- **Cross-Platform**: Windows-optimized with WSL compatibility

## 核心特性

### 1. 统一注册装饰器系统

LStartlet 提供了一套统一的装饰器系统，用于自动注册服务、插件和命令，大大简化了框架的使用。

#### 服务注册装饰器

```python
from LStartlet import register_service, ServiceLifetime

# 基本用法 - 自动注册为 TRANSIENT 服务
@register_service()
class EmailService:
    def send_email(self, message: str):
        print(f"Sending email: {message}")

# 指定接口和服务实现
class NotificationService:
    def notify(self, message: str):
        pass

@register_service(service_type=NotificationService, lifetime=ServiceLifetime.SINGLETON)
class EmailNotificationService(NotificationService):
    def notify(self, message: str):
        print(f"Email notification: {message}")
```

#### 插件注册装饰器

```python
from LStartlet import register_plugin, PluginBase

@register_plugin(
    plugin_id="com.example.email",
    name="Email Plugin", 
    version="1.0.0",
    description="Handles email notifications",
    order=10,
    dependencies={"core.logger": ">=1.0.0"}
)
class EmailPlugin(PluginBase):
    def __init__(self):
        super().__init__(
            plugin_id="com.example.email",
            name="Email Plugin",
            version="1.0.0",
            description="Handles email notifications"
        )
    
    def initialize(self) -> None:
        print("Email plugin initialized")
    
    def start(self) -> None:
        print("Email plugin started")
    
    def stop(self) -> None:
        print("Email plugin stopped")
    
    def cleanup(self) -> None:
        print("Email plugin cleaned up")
```

#### 命令注册装饰器

```python
from LStartlet import register_command, BaseCommand, CommandResult

@register_command(
    name="send_email",
    description="Send an email message",
    category="communication",
    timeout=30.0
)
class SendEmailCommand(BaseCommand):
    def __init__(self):
        super().__init__(self._command_metadata)
    
    def execute(self, recipient: str, subject: str, body: str) -> CommandResult:
        # 执行发送邮件的逻辑
        print(f"Sending email to {recipient}: {subject}")
        return CommandResult(is_success=True, data="Email sent successfully")
```

#### 向后兼容性

为了保持向后兼容，LStartlet 仍然支持原有的装饰器：

- `auto_register` - 等同于 `register_service`
- `auto_plugin_register` - 等同于 `register_plugin`  
- `register_command_decorator` - 等同于 `register_command`

### 2. 统一的入参格式

所有注册装饰器都遵循统一的入参格式：

- **基本用法**: `@decorator()` - 使用默认配置
- **自定义配置**: `@decorator(param1=value1, param2=value2)` - 指定具体参数
- **内部处理**: 装饰器内部自动处理具体的注册逻辑，用户只需关注业务实现

这种统一的设计使得框架更加易用和一致，符合高内聚低耦合的设计原则.

## License

MIT License - see [LICENSE](LICENSE) for details.
