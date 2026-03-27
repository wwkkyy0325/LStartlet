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
- **Caching**: `cached_async`
- **Permissions**: `require_permission`, `require_permission_async`, `PermissionLevel`
- **Metrics**: `monitor_metrics`, `monitor_metrics_async`, `MetricsCollector`

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

## License

MIT License - see [LICENSE](LICENSE) for details.
