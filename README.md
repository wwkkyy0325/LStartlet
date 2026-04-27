# LStartlet

一个模块化、高内聚、低耦合的Python应用基础设施框架。

LStartlet 是一个轻量级的应用启动和管理框架，为Python应用程序提供标准化的生命周期管理、配置管理和系统交互能力。

## 特性

- **模块化与解耦**：依赖注入（DI）和事件系统，解决大型Python应用的高耦合问题
- **全自动化**：依赖注入、生命周期管理、事件系统、配置管理完全自动化
- **统一配置与日志**：标准化的配置管理和日志格式，降低开发和维护成本
- **简化API**：仅23个核心API，学习成本低，使用简单
- **事件驱动架构**：事件总线和事件处理器，实现组件间松耦合
- **生命周期管理**：标准化的组件生命周期阶段（INIT、START、STOP、DESTROY）
- **装饰器工具**：拦截器、参数验证、性能监控等实用工具

## 安装

```bash
pip install LStartlet
```

或从源码安装：

```bash
git clone https://github.com/wwkkyy0325/LStartlet.git
cd LStartlet
pip install -e .
```

## 快速开始

### 基础应用

```python
from LStartlet import ApplicationInfo, start_framework

# 定义应用信息
@ApplicationInfo
class MyApp:
    def get_directory_name(self) -> str:
        return "MyApp"

    def get_display_name(self) -> str:
        return "MyApp"

    def get_author(self) -> str:
        return "Your Name"

    def get_version(self) -> str:
        return "1.0.0"

# 启动框架
start_framework(app_info=MyApp)
```

### 依赖注入

```python
from LStartlet import Service, inject, start_framework

@Service(singleton=True)
class DatabaseService:
    def query(self, sql):
        return f"Executing: {sql}"

@Service(singleton=True)
class UserService:
    # 在类级别定义依赖注入，框架会自动注入
    db: DatabaseService = inject(DatabaseService)
    
    def __init__(self):
        pass
    
    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# 启动框架
start_framework()

# 使用服务（自动注入）
user_service = UserService()
result = user_service.get_user(123)
```

### 事件处理

```python
from LStartlet import Event, publish_event, subscribe_event
from dataclasses import dataclass

@dataclass
class UserCreatedEvent(Event):
    user_id: int
    username: str

class EmailService:
    def __init__(self):
        subscribe_event(UserCreatedEvent, self.send_welcome_email)
    
    def send_welcome_email(self, event: UserCreatedEvent):
        print(f"Sending welcome email to user {event.user_id}")

# 发布事件
publish_event(UserCreatedEvent(user_id=123, username="John Doe"))
```

### 生命周期管理

```python
from LStartlet import Service, Init, Start, Stop, Destroy, start_framework

@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connected = False
    
    @Init
    def initialize(self):
        print("Database initialized")
    
    @Start
    def connect(self):
        self.connected = True
        print("Database connected")
    
    @Stop
    def disconnect(self):
        self.connected = False
        print("Database disconnected")
    
    @Destroy
    def cleanup(self):
        print("Database cleanup")

# 启动框架，生命周期自动管理
start_framework()
```

### 配置管理

```python
from LStartlet import Config, get_config, set_config

@Config("app_config", "应用配置")
class AppConfig:
    database_url: str = "postgresql://localhost/mydb"
    port: int = 8080
    debug: bool = False

# 设置配置 - 使用字段名
set_config("database_url", "postgresql://localhost/mydb")
set_config("port", 8080)
set_config("debug", True)

# 获取配置 - 使用字段名
app_name = get_config("database_url")
debug = get_config("debug")
```

### 日志记录

```python
from LStartlet import debug, info, warning, error, critical

# 记录日志
debug("Debug information")
info("Application started")
warning("Configuration using default values")
error("Database connection failed")
critical("System crash")
```

## 完整示例

```python
from LStartlet import (
    ApplicationInfo,
    Service,
    inject,
    Event,
    publish_event,
    subscribe_event,
    Init,
    Start,
    Stop,
    Destroy,
    Config,
    get_config,
    set_config,
    debug,
    info,
    warning,
    error,
    critical,
    start_framework,
    stop_framework,
)
from dataclasses import dataclass

# 1. 定义应用信息
@ApplicationInfo
class MyApp:
    def get_directory_name(self) -> str:
        return "MyApp"
    
    def get_display_name(self) -> str:
        return "MyApp"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_author(self) -> str:
        return "Your Name"

# 2. 定义配置
@Config("app_config", "应用配置")
class AppConfig:
    database_url: str = "postgresql://localhost/mydb"
    port: int = 8080
    debug: bool = False

# 3. 定义事件
@dataclass
class UserCreatedEvent(Event):
    user_id: int
    username: str

# 4. 定义服务
@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connected = False
    
    @Init
    def initialize(self):
        info("Database service initialized")
    
    @Start
    def connect(self):
        self.connected = True
        info("Database connected")
    
    @Stop
    def disconnect(self):
        self.connected = False
        info("Database disconnected")
    
    def query(self, sql):
        if not self.connected:
            error("Database not connected")
            return None
        return f"Query result: {sql}"

@Service(singleton=True)
class EmailService:
    def __init__(self):
        subscribe_event(UserCreatedEvent, self.send_welcome_email)
    
    def send_welcome_email(self, event: UserCreatedEvent):
        info(f"Sending welcome email to {event.username}")

@Service(singleton=True)
class UserService:
    # 在类级别定义依赖注入，框架会自动注入
    db: DatabaseService = inject(DatabaseService)
    
    def __init__(self):
        pass
    
    @Init
    def initialize(self):
        info("User service initialized")
    
    def create_user(self, username):
        user_id = 123
        info(f"Creating user: {username}")
        
        # 发布事件
        publish_event(UserCreatedEvent(user_id=user_id, username=username))
        
        return user_id
    
    def get_user(self, user_id):
        result = self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
        return result

# 5. 配置管理
set_config("database_url", "postgresql://localhost/mydb")
set_config("port", 8080)
set_config("debug", True)

# 6. 使用服务
try:
    # 启动框架
    start_framework(app_info=MyApp)
    
    # 创建用户
    user_id = UserService().create_user("John Doe")
    info(f"User created with ID: {user_id}")

    # 获取用户
    user = UserService().get_user(user_id)
    info(f"User data: {user}")
    
finally:
    # 停止框架
    stop_framework()
```

## 核心API

### 装饰器

#### `Service`

服务装饰器，标记服务类并配置服务行为。

```python
@Service(singleton=True)
class MyService:
    def __init__(self):
        pass
```

#### `Event`

事件基类，所有事件都应继承此类。

```python
from dataclasses import dataclass

@dataclass
class MyEvent(Event):
    data: str
```

#### `Init`

初始化装饰器，标记初始化方法。

```python
class MyService:
    @Init
    def initialize(self):
        print("Service initialized")
```

#### `Start`

启动装饰器，标记启动方法。

```python
class MyService:
    @Start
    def start(self):
        print("Service started")
```

#### `Stop`

停止装饰器，标记停止方法。

```python
class MyService:
    @Stop
    def stop(self):
        print("Service stopped")
```

#### `Destroy`

销毁装饰器，标记销毁方法。

```python
class MyService:
    @Destroy
    def destroy(self):
        print("Service destroyed")
```

#### `ApplicationInfo`

应用信息装饰器，标记应用信息类。

```python
@ApplicationInfo
class MyApp:
    def get_directory_name(self) -> str:
        return "MyApp"
    
    def get_display_name(self) -> str:
        return "MyApp"
    
    def get_author(self) -> str:
        return "Your Name"
    
    def get_version(self) -> str:
        return "1.0.0"
```

#### `Config`

配置装饰器，标记配置类。

```python
@Config("app_config", "应用配置")
class AppConfig:
    database_url: str = "postgresql://localhost/mydb"
    port: int = 8080
    debug: bool = False
```

### 函数

#### `inject(service_type)`

依赖注入函数，用于标记需要注入的依赖服务。

```python
class MyService:
    db: DatabaseService = inject(DatabaseService)
```

#### `resolve_service(service_type)`

服务解析函数，从DI容器中获取服务实例。

```python
db_service = resolve_service(DatabaseService)
```

#### `publish_event(event)`

发布事件到事件总线。

```python
publish_event(UserCreatedEvent(user_id=123, username="John Doe"))
```

#### `subscribe_event(event_type, handler)`

订阅事件。

```python
subscribe_event(UserCreatedEvent, self.handle_user_created)
```

#### `unsubscribe_event(event_type, handler)`

取消订阅事件。

```python
unsubscribe_event(UserCreatedEvent, self.handle_user_created)
```

#### `get_config(key, default=None)`

获取配置值。

```python
value = get_config("database_url")
```

#### `set_config(key, value)`

设置配置值。

```python
set_config("database_url", "postgresql://localhost/mydb")
```

#### `debug(message)`

记录调试日志。

```python
debug("Debug information")
```

#### `info(message)`

记录信息日志。

```python
info("Application started")
```

#### `warning(message)`

记录警告日志。

```python
warning("Configuration using default values")
```

#### `error(message)`

记录错误日志。

```python
error("Database connection failed")
```

#### `critical(message)`

记录严重错误日志。

```python
critical("System crash")
```

#### `start_framework(app_info=None)`

启动框架。

```python
start_framework(app_info=MyApp)
```

#### `stop_framework()`

停止框架。

```python
stop_framework()
```

### 装饰器工具

#### `Interceptor`

拦截器装饰器，用于方法拦截和增强。

```python
@Interceptor
def log_interceptor(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}")
        return result
    return wrapper

class MyService:
    @log_interceptor
    def do_something(self):
        pass
```

#### `ValidateParams`

参数验证装饰器，自动验证方法参数。

```python
class MyService:
    @ValidateParams()
    def create_user(self, username: str, age: int) -> int:
        return 123
```

#### `Timing`

性能监控装饰器，记录方法执行时间。

```python
class MyService:
    @Timing(log_threshold=0.1)
    def slow_operation(self):
        pass
```

## 设计理念

### 简化API

LStartlet 提供23个核心API，大幅降低学习成本和使用复杂度：

- **装饰器**：8个核心装饰器（Service, Event, Init, Start, Stop, Destroy, ApplicationInfo, Config）
- **函数**：13个核心函数（inject, resolve_service, publish_event, subscribe_event, unsubscribe_event, get_config, set_config, debug, info, warning, error, critical, start_framework, stop_framework）
- **装饰器工具**：3个装饰器工具（Interceptor, ValidateParams, Timing）

### 全自动化

- **依赖注入**：自动解析和注入依赖，无需手动注册
- **生命周期管理**：自动调用生命周期方法，无需手动触发
- **事件系统**：自动路由事件到订阅者
- **配置管理**：自动保存和加载配置，支持自动保存

### 零配置

- **自动目录管理**：自动创建应用目录和子目录
- **自动日志配置**：自动配置日志输出和文件轮转
- **自动健康检查**：自动检查应用健康状态和依赖关系

## 目录结构

```
~/.lstartlet/
├── MyApp/
│   ├── config/              # 配置目录
│   │   └── app_config.yaml  # 应用配置文件
│   ├── logs/                # 日志目录
│   │   └── myapp.log        # 应用日志
│   ├── cache/               # 缓存目录
│   ├── data/                # 数据目录
│   ├── plugins/             # 插件目录
│   └── ui/                  # UI 配置目录
│       └── ui_config.yaml   # UI 配置文件
├── logs/
│   └── lstartlet.log        # 框架日志
└── config.yaml              # 框架配置
```

## 开发指南

详细的开发指南请参考 [DEVELOPMENT.md](DEVELOPMENT.md)

## 许可证

MIT License