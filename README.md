# Core Infrastructure Framework

A modular, high-cohesion, low-coupling infrastructure framework for Python applications.

## Core Components

### Configuration Management (`core.config`)
- Unified configuration access and management
- Type-safe configuration registration
- Validation and change listeners
- File-based persistence

### Dependency Injection (`core.di`)
- Service container with singleton/transient/scoped lifetimes
- Automatic dependency resolution
- Circular dependency detection

### Event System (`core.event`)
- Thread-safe event bus
- Publish/subscribe pattern
- Event type registry
- Async event support

### Logging System (`core.logger`)
- Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Console and file handlers
- Caller-aware logging (shows actual calling file/line)
- Structured logging with extra context

### Command System (`core.command`)
- Command pattern implementation
- Command execution tracking
- Event-driven command lifecycle

### Scheduler (`core.scheduler`)
- Process and task management
- Configurable scheduling
- Async task support
- Health monitoring

### Path Management (`core.path`)
- Unified path access
- Project structure awareness
- Cross-platform path handling

### Persistence (`core.persistence`)
- Data storage and retrieval
- Multiple storage backends
- Transaction support

### Error Handling (`core.error`)
- Unified error handling
- Global exception catching
- Structured error formatting
- Context-aware error logging

### Plugin System (`plugin`)
- Extensible plugin architecture
- Dynamic plugin loading
- Plugin lifecycle management

## Usage Examples

### Configuration
```python
from core.config import get_config, set_config, register_config

# Register a new config
register_config("my_setting", "default_value", str, "My custom setting")

# Get config value
value = get_config("my_setting")

# Set config value
set_config("my_setting", "new_value")
```

### Logging
```python
from core.logger import info, debug, warning, error

info("This is an info message")
debug("Debug information")
warning("This is a warning")
error("An error occurred")
```

### Dependency Injection
```python
from core.di import get_default_container

container = get_default_container()
container.register(MyServiceInterface, MyServiceImplementation)

service = container.resolve(MyServiceInterface)
```

### Events
```python
from core.event import event_bus, BaseEvent

class MyEvent(BaseEvent):
    def __init__(self, data):
        self.data = data

# Subscribe to events
def handle_event(event):
    print(f"Received event: {event.data}")

event_bus.subscribe(MyEvent, handle_event)

# Publish event
event_bus.publish(MyEvent("test data"))
```

## Testing

Run all tests:
```bash
python tests/run_tests.py
```

## Requirements

- Python 3.7+
- psutil

Install dependencies:
```bash
pip install -r requirements.txt
```