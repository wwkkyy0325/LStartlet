# LStartlet

A modular, high-cohesion, low-coupling infrastructure framework for Python applications.

LStartlet is a lightweight application startup and management framework that provides standardized lifecycle management, configuration management, and system interaction capabilities for Python applications.

## Features

- **Modular & Decoupled**: Dependency injection (DI) and plugin system to solve high coupling issues in large Python applications
- **Automated Operations Support**: Built-in CI/CD controllers, builders, testers, and deployers to simplify build and deployment processes
- **Unified Configuration & Logging**: Standardized configuration management and logging formatting to reduce development and maintenance costs
- **Cross-platform Compatibility**: System detection and local environment check scripts for different operating systems
- **Plugin System**: Dynamic plugin loading, dependency management, and metadata management
- **Event-driven Architecture**: Event bus and event handlers for loose coupling between components
- **Lifecycle Management**: Standardized component lifecycle phases (PRE_INIT, POST_INIT, ON_DEPENDENCIES_RESOLVED, PRE_START, POST_START, etc.)

## Installation

```bash
pip install LStartlet
```

Or install from source:

```bash
git clone https://github.com/wwkkyy0325/LStartlet.git
cd LStartlet
pip install -e .
```

## Quick Start

### Basic Component Registration

```python
from LStartlet import Component, di_container

@Component
class MyService:
    def __init__(self):
        self.name = "My Service"
    
    def do_something(self):
        return f"Hello from {self.name}"

# Resolve the component from DI container
service = di_container.resolve(MyService)
print(service.do_something())
```

### Dependency Injection

```python
from LStartlet import Component, Inject, di_container

@Component
class DatabaseService:
    def query(self, sql):
        return f"Executing: {sql}"

@Component  
class UserService:
    def __init__(self, db: DatabaseService = Inject()):
        self.db = db
    
    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Both services will be automatically registered and injected
user_service = di_container.resolve(UserService)
result = user_service.get_user(123)
```

### Plugin System

```python
from LStartlet import Plugin, PluginBase

@Plugin
class MyPlugin(PluginBase):
    def on_load(self):
        print("Plugin loaded!")
    
    def on_activate(self):
        print("Plugin activated!")
```

### Event Handling

```python
from LStartlet import Component, OnEvent, publish_event

class UserCreatedEvent:
    def __init__(self, user_id):
        self.user_id = user_id

@Component
class EmailService:
    @OnEvent(UserCreatedEvent)
    def send_welcome_email(self, event):
        print(f"Sending welcome email to user {event.user_id}")

# Publish an event
publish_event(UserCreatedEvent(123))
```

## Project Structure

```
LStartlet/
├── src/
│   └── LStartlet/
│       ├── __init__.py
│       ├── _cicd_decorator.py
│       ├── _config_manager.py
│       ├── _context_manager.py
│       ├── _decorators.py          # Main decorators (@Component, @Plugin, @Inject, etc.)
│       ├── _di_decorator.py        # Dependency injection implementation
│       ├── _error_handler.py
│       ├── _event_decorator.py     # Event handling decorators
│       ├── _lifecycle_decorator.py # Lifecycle management
│       ├── _log_formatter.py
│       ├── _logging_functions.py
│       ├── _path_manager.py
│       ├── _plugin_automation.py
│       ├── _plugin_base.py
│       └── _plugin_manager.py
├── tests/                          # Unit tests
├── scripts/                        # Helper scripts
├── requirements.txt                # Runtime dependencies
├── requirements-dev.txt            # Development dependencies
├── pyproject.toml                  # Build configuration
├── pytest.ini                      # Test configuration
├── mypy.ini                        # Type checking configuration
└── setup.py                        # Package setup
```

## Development

### Prerequisites

- Python 3.8+
- pip

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/wwkkyy0325/LStartlet.git
cd LStartlet

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=LStartlet

# Run specific test file
pytest tests/test_decorators.py
```

### Type Checking

```bash
mypy src/LStartlet
```

### Code Formatting

```bash
# Check formatting
black --check .

# Apply formatting
black .
```

## Core Concepts

### Decorators

- `@Component`: Marks a class as a component that can be managed by the DI container
- `@Plugin`: Marks a class as a plugin that extends the framework functionality
- `@Inject`: Marks a parameter or attribute for dependency injection
- `@OnEvent`: Registers an event handler method
- `@Init`, `@Start`, `@Stop`, `@Destroy`: Lifecycle method decorators

### Instance Modes

- **Singleton (default)**: The DI container returns the same instance every time
- **Transient**: A new instance is created each time through the DI container

```python
@Component(scope="transient")  # or singleton=False (deprecated)
class TransientService:
    pass
```

### Testing Best Practices

- Always resolve instances through `di_container.resolve(Class)` instead of direct instantiation
- Use dynamic class definition in test functions rather than module-level decorated classes
- Clean up registration state before each test to ensure isolation

## License

MIT License

## Author

wwkkyy0325 (1074446976@qq.com)