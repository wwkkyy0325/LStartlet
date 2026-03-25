# Core Infrastructure Framework

A modular, high-cohesion, low-coupling infrastructure framework for Python applications.

## Core Components

### Configuration Management ([core.config](file:///f:/workspace-new/python/ocr/core/config/__init__.py#L0-L174))
- Unified configuration access and management
- Type-safe configuration registration
- Validation and change listeners
- File-based persistence

### Dependency Injection ([core.di](file:///f:/workspace-new/python/ocr/core/di/service_container.py#L0-L174))
- Service container with singleton/transient/scoped lifetimes
- Automatic dependency resolution
- Circular dependency detection

### Event System ([core.event](file:///f:/workspace-new/python/ocr/core/event/event_bus.py#L0-L111))
- Thread-safe event bus
- Publish/subscribe pattern
- Event type registry
- Async event support

### Logging System ([core.logger](file:///f:/workspace-new/python/ocr/core/logger/logger.py#L0-L241))
- Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Console and file handlers
- Caller-aware logging (shows actual calling file/line)
- Structured logging with extra context

### Command System ([core.command](file:///f:/workspace-new/python/ocr/core/command/command_base.py#L0-L44))
- Command pattern implementation
- Command execution tracking
- Event-driven command lifecycle

### Scheduler ([core.scheduler](file:///f:/workspace-new/python/ocr/core/scheduler/scheduler.py#L0-L244))
- Process and task management
- Configurable scheduling
- Async task support
- Health monitoring

### Path Management ([core.path](file:///f:/workspace-new/python/ocr/core/path/path_manager.py#L0-L49))
- Unified path access
- Project structure awareness
- Cross-platform path handling

### Persistence ([core.persistence](file:///f:/workspace-new/python/ocr/core/persistence/persistence_manager.py#L0-L35))
- Data storage and retrieval
- Multiple storage backends
- Transaction support

### Error Handling ([core.error](file:///f:/workspace-new/python/ocr/core/error/error_handler.py#L0-L78))
- Unified error handling
- Global exception catching
- Structured error formatting
- Context-aware error logging

### Plugin System ([plugin](file:///f:/workspace-new/python/ocr/plugin/manager/plugin_manager.py#L0-L111))
- Extensible plugin architecture
- Dynamic plugin loading
- Plugin lifecycle management

### Version Control ([core.version_control](file:///f:/workspace-new/python/ocr/core/version_control/version_controller.py#L0-L244))
- Version management and tagging
- Incremental package generation
- Dependency analysis and management
- Change tracking and reporting

### CI/CD Pipeline ([core.cicd](file:///f:/workspace-new/python/ocr/core/cicd/cicd_controller.py#L0-L244))
- Continuous integration and deployment automation
- Build, test, and deployment orchestration
- Pipeline definition and execution
- Deployment history and rollback

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

# Listen for config changes
def my_listener(key, old_value, new_value):
    print(f"Config {key} changed from {old_value} to {new_value}")

add_config_listener(my_listener)
set_config("my_setting", "another_value")  # Will trigger listener

# Save/load configs to/from file
save_config("my_settings.yaml")  # Save current configs
load_config("my_settings.yaml")  # Load configs from file
```

### Logging
```python
from core.logger import info, debug, warning, error

info("This is an info message")
debug("Debug information")
warning("This is a warning")
error("An error occurred")

# Structured logging with extra context
info("User login attempt", extra={
    "user_id": 12345,
    "ip_address": "192.168.1.1",
    "success": True
})
```

### Dependency Injection
```python
from core.di import get_default_container

# Define an interface和服务
class DatabaseInterface:
    def save(self, data): pass

class MySQLDatabase(DatabaseInterface):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
    
    def save(self, data):
        print(f"Saving {data} to MySQL at {self.host}:{self.port}")

# Register a service with the container
container = get_default_container()
container.register(DatabaseInterface, MySQLDatabase, host="localhost", port=3306)

# Resolve the service
database = container.resolve(DatabaseInterface)
database.save("some data")  # Output: Saving some data to MySQL at localhost:3306
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
event_bus.publish(MyEvent("test data"))  # Output: Received event: test data
```

### Scheduler
```python
from core.scheduler import Scheduler
from core.scheduler.config_manager import SchedulerConfig

# Create scheduler with custom config
config = SchedulerConfig(
    max_processes=6,
    process_timeout=45.0,
    max_concurrent_tasks=15,
    scheduling_strategy="priority"
)

scheduler = Scheduler(config)

# Start the scheduler
scheduler.start()

# Submit a task (example)
def sample_task():
    print("Executing scheduled task")
    return "Task completed"

# Stop the scheduler
scheduler.stop()
```

### Path Management
```python
from core.path import get_project_root, get_data_dir, join_path

# Get common paths
project_root = get_project_root()
data_dir = get_data_dir()

# Join paths safely across platforms
config_path = join_path(get_project_root(), "config", "app_config.yaml")
```

### Plugin System
```python
from plugin.manager.plugin_manager import PluginManager
from plugin.base.plugin_interface import PluginInterface

# Create a simple plugin
class MyPlugin(PluginInterface):
    def __init__(self):
        super().__init__()
        self.name = "MyPlugin"
        self.version = "1.0.0"
    
    def activate(self):
        print(f"{self.name} activated")
    
    def deactivate(self):
        print(f"{self.name} deactivated")

# Use plugin manager
plugin_manager = PluginManager()
plugin_manager.load_plugin(MyPlugin())
plugin_manager.activate_plugin("MyPlugin")
```

### Version Control
```python
from core.version_control import VersionController

# Create version controller instance
vc = VersionController()

# Get current version
current_version = vc.get_current_version()
print(f"Current version: {current_version}")

# Create a new tag
vc.create_tag("v1.0.1", "Release version 1.0.1")

# Generate incremental package between two versions
package_path = vc.generate_incremental_package("v1.0.0", "v1.0.1")
if package_path:
    print(f"Incremental package generated: {package_path}")

# Analyze dependencies
from core.version_control import DependencyResolver
resolver = DependencyResolver()
external_deps = resolver.get_external_dependencies()
print(f"External dependencies: {external_deps}")

# Generate requirements.txt based on code analysis
resolver.generate_requirements_txt("requirements_new.txt")
```

### CI/CD Pipeline
```python
from core.cicd import CICDController, Pipeline, Stage, Step

# Create CI/CD controller
cicd = CICDController()

# Define a simple pipeline
pipeline = Pipeline("main-pipeline", "Main CI/CD pipeline for the application")

# Create stages
build_stage = Stage("build", "Build the application")
test_stage = Stage("test", "Run tests")
deploy_stage = Stage("deploy", "Deploy to environment")

# Add steps to build stage
def run_build():
    return cicd.builder.build()

build_step = Step("build-app", run_build, "Build the application")
build_stage.add_step(build_step)

# Add steps to test stage
def run_tests():
    results = cicd.tester.run_tests()
    return results['passed'] > 0 and results['errors'] == 0 and results['failures'] == 0

test_step = Step("run-unit-tests", run_tests, "Run unit tests")
test_stage.add_step(test_step)

# Add steps to deploy stage
def run_deploy():
    return cicd.deployer.deploy("staging")

deploy_step = Step("deploy-staging", run_deploy, "Deploy to staging environment")
deploy_stage.add_step(deploy_step)

# Add stages to pipeline
pipeline.add_stages([build_stage, test_stage, deploy_stage])

# Run the pipeline
success = cicd.run_pipeline(pipeline, version_tag="v1.0.2", deploy_target="staging")
if success:
    print("Pipeline executed successfully!")
else:
    print("Pipeline failed!")
```

## Advanced Examples

### Using Dependency Injection with Events and Configuration
```python
from core.di import get_default_container
from core.config import get_config
from core.event import event_bus, BaseEvent

class TaskCompletedEvent(BaseEvent):
    def __init__(self, task_id: str, result: str):
        self.task_id = task_id
        self.result = result

class TaskProcessor:
    def __init__(self):
        self.max_retries = get_config("max_task_retries", 3)
    
    def process_task(self, task_id: str):
        # Simulate task processing
        result = f"Processed task {task_id}"
        
        # Publish event when task completes
        event_bus.publish(TaskCompletedEvent(task_id, result))
        return result

# Register and use the service
container = get_default_container()
container.register(TaskProcessor, TaskProcessor)

# Subscribe to events
def on_task_completed(event):
    print(f"Task {event.task_id} completed with result: {event.result}")

event_bus.subscribe(TaskCompletedEvent, on_task_completed)

# Use the processor
processor = container.resolve(TaskProcessor)
processor.process_task("123")
```

### Comprehensive Error Handling
```python
from core.error import handle_error
from core.logger import error as log_error

try:
    # Some risky operation
    risky_operation_result = perform_risky_operation()
except Exception as e:
    # Handle error with context
    handle_error(e)
    log_error(f"Operation failed: {str(e)}", extra={
        "operation_type": "risky_operation",
        "context": "during processing"
    })
```

## Testing

Run all tests:
```bash
python tests/run_tests.py
```

## Requirements

- Python 3.7+
- psutil
- PyYAML

Install dependencies:
```bash
pip install -r requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`python tests/run_tests.py`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](file:///f:/workspace-new/python/ocr/LICENSE) file for details.