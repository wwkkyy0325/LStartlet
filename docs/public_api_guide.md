# LStartlet 公共 API 使用指南

本文档详细介绍 LStartlet 框架的 23 个核心公共 API 的使用方法和最佳实践。

## 目录

- [依赖注入](#依赖注入)
- [事件系统](#事件系统)
- [生命周期管理](#生命周期管理)
- [应用信息](#应用信息)
- [配置管理](#配置管理)
- [日志系统](#日志系统)
- [框架管理](#框架管理)
- [装饰器工具](#装饰器工具)

## 依赖注入

### inject - 依赖注入函数

标记需要注入的属性或参数，在框架启动时自动解析依赖。

#### 基本用法

```python
from LStartlet import inject, Service, start_framework

# 定义服务
@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connected = False

@Service(singleton=True)
class CacheService:
    def __init__(self):
        self.cache = {}

# 使用依赖注入 - 在类级别定义
@Service(singleton=True)
class UserService:
    # 在类级别定义依赖注入，框架会自动注入
    db: DatabaseService = inject(DatabaseService)
    cache: CacheService = inject(CacheService)
    
    def __init__(self):
        pass

    def get_user(self, user_id: int):
        return self.db.query(user_id)

# 启动框架
start_framework()
```

#### 注意事项

- `inject()` 是一个函数，不是装饰器，使用时需要调用
- 推荐在类级别定义依赖注入，而不是在 `__init__` 方法中
- 在框架启动时自动解析依赖
- 单例服务在整个应用中只有一个实例

### Service - 服务装饰器

自动注册服务到 DI 容器并管理生命周期。

#### 基本用法

```python
from LStartlet import Service, Start, start_framework

# 单例服务
@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connected = False

    @Start()
    def connect(self):
        self.connected = True
        print("数据库已连接")

# 多实例服务
@Service(singleton=False)
class RequestHandler:
    def __init__(self):
        self.request_id = None

# 自动启动服务
@Service(singleton=True, auto_start=True)
class BackgroundWorker:
    @Start()
    def start_work(self):
        print("后台工作已启动")

start_framework()
```

#### 参数说明

- `singleton`: 是否为单例服务（默认 True）
- `auto_start`: 是否在框架启动时自动启动（默认 False）

#### 最佳实践

- 大多数服务应该使用单例模式
- 只有需要独立状态的服务才使用多实例模式
- 需要在框架启动时立即运行的服务设置 `auto_start=True`

## 事件系统

### Event - 事件基类

所有自定义事件必须继承此类。

#### 基本用法

```python
from LStartlet import Event, publish_event, subscribe_event
from dataclasses import dataclass

# 定义事件 - 需要使用 @dataclass 装饰器
@dataclass
class UserCreatedEvent(Event):
    user_id: int
    username: str

@dataclass
class UserLoginEvent(Event):
    user_id: int
    login_time: float

# 发布事件
publish_event(UserCreatedEvent(user_id=1, username="Alice"))

# 订阅事件
def handle_user_created(event: UserCreatedEvent):
    print(f"用户创建: {event.username}")

subscribe_event(UserCreatedEvent, handle_user_created)
```

#### 注意事项

- 事件子类需要使用 `@dataclass` 装饰器自动生成 `__init__` 方法
- 事件字段可以是任意类型
- 发布事件时使用 `publish_event()` 函数
- 订阅事件时使用 `subscribe_event()` 函数

### publish_event - 发布事件函数

向事件总线发布事件，支持同步和异步模式。

#### 基本用法

```python
from LStartlet import Event, publish_event

class MyEvent(Event):
    message: str

# 同步发布
publish_event(MyEvent(message="Hello"))

# 异步发布
import asyncio
async def main():
    await publish_event(MyEvent(message="Hello"), async_mode=True)

asyncio.run(main())
```

#### 参数说明

- `event`: 要发布的事件对象（必须继承自 Event）
- `async_mode`: 是否异步发布（默认为 False，同步发布）

#### 注意事项

- 同步模式：所有订阅者按顺序执行，阻塞直到完成
- 异步模式：所有订阅者并发执行，返回协程对象
- 事件发布失败不会影响其他订阅者
- 支持条件订阅，只有满足条件的订阅者才会收到事件

### subscribe_event - 订阅事件函数

为指定事件类型注册处理器。

#### 基本用法

```python
from LStartlet import Event, subscribe_event

class MyEvent(Event):
    message: str

# 基本订阅
def handler(event: MyEvent):
    print(f"收到事件: {event.message}")

subscribe_event(MyEvent, handler)

# 带条件过滤
def condition_handler(event: MyEvent):
    return len(event.message) > 5

subscribe_event(MyEvent, condition_handler, condition=lambda e: e.message.startswith("important"))
```

#### 参数说明

- `event_type`: 事件类型（必须继承自 Event）
- `handler`: 事件处理函数，接收事件对象作为参数
- `condition`: 可选的条件过滤器函数，返回 True 时才处理事件

#### 注意事项

- 同一个事件类型可以有多个订阅者
- 订阅者按注册顺序执行
- 异步订阅者会自动并发执行
- 条件函数接收事件对象作为参数
- 使用 `unsubscribe_event()` 取消订阅

## 生命周期管理

### Init - 初始化装饰器

在组件初始化后触发，用于初始化资源。

#### 基本用法

```python
from LStartlet import Init, Service, start_framework

@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connection = None

    @Init()
    def initialize_resources(self):
        print("初始化资源")
        self.connection = "connected"

    @Init(priority=-1)
    def critical_initialization(self):
        print("关键初始化，优先执行")

start_framework()
```

#### 参数说明

- `condition`: 条件函数，接收实例和kwargs，返回True时执行
- `priority`: 优先级，数值越小优先级越高，默认为0
- `enabled`: 是否启用，默认为True

#### 注意事项

- 在组件实例化时自动触发
- 支持条件执行，只有满足条件才会调用
- 支持优先级控制，数值越小优先级越高
- 每个方法只会执行一次
- 适用于初始化资源、建立连接等操作

### Start - 启动装饰器

在框架启动时、组件启动后触发，用于启动服务。

#### 基本用法

```python
from LStartlet import Start, Service, start_framework

@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connected = False

    @Start()
    def start_service(self):
        print("启动服务")
        self.connected = True

    @Start(priority=1)
    def start_background_tasks(self):
        print("启动后台任务")

start_framework()
```

#### 参数说明

- `condition`: 条件函数，接收实例和kwargs，返回True时执行
- `priority`: 优先级，数值越小优先级越高，默认为0
- `enabled`: 是否启用，默认为True

#### 注意事项

- 在调用 `start_framework()` 时自动触发
- 支持条件执行，只有满足条件才会调用
- 支持优先级控制，数值越小优先级越高
- 适用于启动服务、开启后台任务等操作

### Stop - 停止装饰器

在框架停止时、组件停止后触发，用于停止服务和清理。

#### 基本用法

```python
from LStartlet import Stop, Service, start_framework, stop_framework

@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connected = True

    @Stop()
    def cleanup_after_stop(self):
        print("停止后清理")
        self.connected = False

    @Stop(priority=-1)
    def critical_cleanup(self):
        print("关键清理，优先执行")

start_framework()
stop_framework()
```

#### 参数说明

- `condition`: 条件函数，接收实例和kwargs，返回True时执行
- `priority`: 优先级，数值越小优先级越高，默认为0
- `enabled`: 是否启用，默认为True

#### 注意事项

- 在调用 `stop_framework()` 时自动触发
- 支持条件执行，只有满足条件才会调用
- 支持优先级控制，数值越小优先级越高
- 适用于停止后的清理工作、保存状态等操作

### Destroy - 销毁装饰器

在组件销毁前触发，用于释放资源。

#### 基本用法

```python
from LStartlet import Destroy, Service, start_framework, stop_framework

@Service(singleton=True)
class FileService:
    def __init__(self):
        self.file_handle = None

    @Destroy()
    def release_resources(self):
        print("释放资源")
        if self.file_handle:
            self.file_handle.close()

    @Destroy(priority=1)
    def cleanup_temp_files(self):
        print("清理临时文件")

start_framework()
stop_framework()
```

#### 参数说明

- `condition`: 条件函数，接收实例和kwargs，返回True时执行
- `priority`: 优先级，数值越小优先级越高，默认为0
- `enabled`: 是否启用，默认为True

#### 注意事项

- 在调用 `stop_framework()` 时自动触发
- 支持条件执行，只有满足条件才会调用
- 支持优先级控制，数值越小优先级越高
- 适用于资源释放、清理临时文件等操作

## 应用信息

### ApplicationInfo - 应用信息装饰器

标记应用程序的元数据类，框架会自动收集和管理这些信息。

#### 基本用法

```python
from LStartlet import ApplicationInfo, start_framework

@ApplicationInfo
class MyAppInfo:
    def get_directory_name(self) -> str:
        return "my_app"

    def get_display_name(self) -> Optional[str]:
        return "我的应用"

    def get_author(self) -> Optional[str]:
        return "Author Name"

    def get_email(self) -> Optional[str]:
        return "author@example.com"

    def get_description(self) -> Optional[str]:
        return "My application description"

    def get_dependencies(self) -> Optional[List[str]]:
        return ["OtherApp"]

    def get_version(self) -> Optional[str]:
        return "1.0.0"

start_framework(app_info=MyAppInfo)
```

#### 注意事项

- `get_directory_name()` 是必需的，用于目录命名，必须符合命名规范
- `get_display_name()` 是可选的，用于UI显示，可以是中文或特殊字符
- 如果没有提供 `get_display_name()`，则使用 `get_directory_name()` 作为显示名
- 目录命名规范：字母开头，只能包含字母、数字、下划线、连字符
- 框架会自动收集和管理这些信息

## 配置管理

### Config - 配置装饰器

定义配置类并自动处理验证。

#### 基本用法

```python
from LStartlet import Config, get_config, set_config

@Config("app_config", "应用配置")
class AppConfig:
    database_url: str = "postgresql://localhost/mydb"
    port: int = 8080
    debug: bool = False
    max_connections: int = 10

# 获取配置 - 使用字段名而不是配置名
database_url = get_config("database_url")
port = get_config("port", default=8080)

# 设置配置
set_config("debug", True)
```

#### 注意事项

- 框架自动处理所有验证，用户只需定义配置类
- 使用 `get_config()` 时使用字段名，而不是 `config_name.field_name`
- 支持自动推断验证规则：
  - 类型验证：从类型注解自动推断
  - 范围验证：从默认值和类型自动推断（如 `port: int = 8080` → 1-65535）
  - 长度验证：从字符串类型自动推断
  - 正则表达式验证：从字段名自动推断（如 email、url）
- 配置值会自动进行类型转换和验证
- 验证失败会抛出详细的错误信息
- 支持嵌套配置和复杂类型

### get_config - 获取配置函数

从配置管理器中读取配置。

#### 基本用法

```python
from LStartlet import get_config

# 获取简单配置 - 使用字段名
database_url = get_config("database_url")

# 获取带默认值的配置
port = get_config("port", default=8080)

# 获取嵌套配置
timeout = get_config("timeout", default=30)
```

#### 参数说明

- `key`: 配置键名（使用字段名，不是 `config_name.field_name`）
- `default`: 默认值，当配置不存在时返回此值

#### 注意事项

- 使用字段名作为配置键，而不是 `config_name.field_name` 格式
- 如果配置不存在且未提供默认值，返回 None
- 配置值会自动进行类型转换
- 支持从配置文件中读取预定义的配置

### set_config - 设置配置函数

向配置管理器中写入配置。

#### 基本用法

```python
from LStartlet import set_config

# 设置简单配置 - 使用字段名
set_config("database_url", "postgresql://localhost/mydb")

# 设置嵌套配置
set_config("port", 8080)

# 设置复杂配置
set_config("features", {"feature1": True, "feature2": False})
```

#### 参数说明

- `key`: 配置键名（使用字段名，不是 `config_name.field_name`）
- `value`: 配置值

#### 注意事项

- 使用字段名作为配置键，而不是 `config_name.field_name` 格式
- 设置的配置会自动验证（如果配置类定义了验证规则）
- 配置变更会触发 `@OnConfigChange` 装饰的方法
- 配置会持久化到配置文件
- 如果验证失败，返回 False

## 日志系统

### debug - 调试日志函数

记录详细的调试信息。

#### 基本用法

```python
from LStartlet import debug

debug("初始化数据库连接")
debug(f"用户ID: {user_id}")
```

#### 注意事项

- DEBUG 级别日志通常只在开发和调试时使用
- 日志会同时输出到终端和文件
- 终端使用彩色输出，文件使用纯文本
- 日志文件按天自动拆分，保留30天

### info - 信息日志函数

记录一般信息。

#### 基本用法

```python
from LStartlet import info

info("应用启动")
info("处理用户请求")
```

#### 注意事项

- INFO 级别日志用于记录正常运行状态
- 日志会同时输出到终端和文件
- 终端使用彩色输出，文件使用纯文本
- 日志文件按天自动拆分，保留30天

### warning - 警告日志函数

记录警告信息。

#### 基本用法

```python
from LStartlet import warning

warning("配置文件使用默认值")
warning("连接池接近上限")
```

#### 注意事项

- WARNING 级别日志用于记录潜在问题
- 日志会同时输出到终端和文件
- 终端使用彩色输出，文件使用纯文本
- 日志文件按天自动拆分，保留30天

### error - 错误日志函数

记录错误信息。

#### 基本用法

```python
from LStartlet import error

error("数据库连接失败")
error(f"处理请求失败: {error_message}")
```

#### 注意事项

- ERROR 级别日志用于记录错误但程序仍可继续运行
- 日志会同时输出到终端和文件
- 终端使用彩色输出，文件使用纯文本
- 日志文件按天自动拆分，保留30天

### critical - 严重错误日志函数

记录严重错误。

#### 基本用法

```python
from LStartlet import critical

critical("系统崩溃")
critical("无法恢复的严重错误")
```

#### 注意事项

- CRITICAL 级别日志用于记录严重错误，可能导致程序终止
- 日志会同时输出到终端和文件
- 终端使用彩色输出，文件使用纯文本
- 日志文件按天自动拆分，保留30天

## 框架管理

### start_framework - 启动框架函数

一行代码启动框架，自动处理所有复杂操作。

#### 基本用法

```python
from LStartlet import start_framework, ApplicationInfo, Service, Start

@ApplicationInfo
class MyApp:
    def get_directory_name(self) -> str:
        return "MyApp"

@Service(singleton=True, auto_start=True)
class MyService:
    @Start()
    def on_start(self):
        print("服务已启动")

# 一行启动框架
start_framework(app_info=MyApp)
```

#### 参数说明

- `app_info`: 应用程序信息类或实例（可选）
- `services`: 需要注册的服务类列表（可选，已废弃，使用 @Service 装饰器）
- `framework_instance`: 框架实例（可选，用于插件系统）

#### 注意事项

- 自动创建应用程序目录（~/.lstartlet/{app_name}）
- 自动配置日志系统（终端和文件输出）
- 自动注册所有 @Service 装饰的服务
- 自动启动所有标记为 auto_start 的服务
- 自动加载插件（如果提供了 framework_instance）
- 自动触发所有 @Init 和 @Start 装饰的方法
- 支持 console_log_level 和 file_log_level 参数配置日志级别

### stop_framework - 停止框架函数

停止当前运行的框架实例。

#### 基本用法

```python
from LStartlet import start_framework, stop_framework

# 启动框架
start_framework()

# 停止框架
stop_framework()
```

#### 注意事项

- 自动触发所有 @Stop 和 @Destroy 装饰的方法
- 按照优先级顺序执行（数值越小优先级越高）
- 清理所有已注册的服务
- 释放所有占用的资源
- 关闭日志系统
- 可以多次调用，不会报错

## 装饰器工具

### Interceptor - 拦截器装饰器

通用函数拦截和修改，支持拦截参数、结果和异常。

#### 基本用法

```python
from LStartlet import Interceptor

# 结果转换
@Interceptor(intercept_result=lambda result: result.upper())
def my_function(name: str) -> str:
    return name

# 输入清理
@Interceptor(intercept_params=lambda args, kwargs: (args, {k: v.strip() if isinstance(v, str) else v for k, v in kwargs.items()}))
def my_function(name: str, email: str) -> None:
    pass

# 异常处理
@Interceptor(intercept_exception=lambda e: "默认值")
def my_function():
    raise Exception("错误")
```

#### 参数说明

- `intercept_params`: 拦截参数的回调函数，接收 (args, kwargs)，返回修改后的 (args, kwargs)
- `intercept_result`: 拦截结果的回调函数，接收结果，返回修改后的结果
- `intercept_exception`: 拦截异常的回调函数，接收异常，返回处理后的异常或新结果
- `log_intercept`: 是否记录拦截日志（默认 False）

#### 注意事项

- 支持同时拦截参数、结果和异常
- 拦截器按顺序执行，可以链式调用
- 异常拦截器可以返回新结果来替代异常
- log_intercept=True 时会记录所有拦截操作
- 适用于输入验证、结果转换、异常处理等场景

### ValidateParams - 参数验证装饰器

根据类型注解自动验证函数参数。

#### 基本用法

```python
from LStartlet import ValidateParams

@ValidateParams()
def my_function(name: str, age: int) -> None:
    pass

# 调用时会自动验证参数类型
my_function("Alice", 25)  # 正确
my_function("Alice", "25")  # 抛出 TypeError
```

#### 注意事项

- 根据类型注解自动验证参数类型
- 验证失败时抛出 TypeError 异常
- 自动记录验证失败的详细信息
- 支持所有标准 Python 类型（int, str, bool, float, list, dict 等）
- 适用于需要严格参数类型检查的函数

### Timing - 性能监控装饰器

自动记录函数执行时间。

#### 基本用法

```python
from LStartlet import Timing

@Timing(log_threshold=0.1)
def my_function():
    pass

@Timing(log_threshold=0.5)
def slow_function():
    pass
```

#### 参数说明

- `log_threshold`: 日志记录阈值（秒），超过此阈值才记录警告（默认 1.0）

#### 注意事项

- 自动记录函数执行时间
- 执行时间超过阈值时记录警告日志
- 即使未超过阈值，也会记录调试日志
- 适用于性能分析和优化
- 不影响函数的正常执行和返回值

## 完整示例

下面是一个完整的示例，展示了如何组合使用多个 API：

```python
from LStartlet import (
    ApplicationInfo, Service, inject,
    Event, publish_event, subscribe_event,
    Init, Start, Stop, Destroy,
    Config, get_config, set_config,
    debug, info, warning, error, critical,
    start_framework, stop_framework,
    Interceptor, ValidateParams, Timing
)

# 1. 定义应用信息
@ApplicationInfo
class MyAppInfo:
    def get_directory_name(self) -> str:
        return "my_app"

    def get_display_name(self) -> Optional[str]:
        return "我的应用"

    def get_author(self) -> Optional[str]:
        return "Author Name"

    def get_version(self) -> Optional[str]:
        return "1.0.0"

# 2. 定义配置
@Config("app_config", "应用配置")
class AppConfig:
    database_url: str = "postgresql://localhost/mydb"
    port: int = 8080
    debug: bool = False

# 3. 定义事件
from dataclasses import dataclass

@dataclass
class UserCreatedEvent(Event):
    user_id: int
    username: str

# 4. 定义服务
@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connected = False

    @Init()
    def initialize(self):
        debug("初始化数据库连接")

    @Start()
    def connect(self):
        self.connected = True
        info("数据库已连接")

    @Stop()
    def disconnect(self):
        self.connected = False
        info("数据库已断开")

@Service(singleton=True)
class UserService:
    # 在类级别定义依赖注入
    db: DatabaseService = inject(DatabaseService)
    
    def __init__(self):
        pass

    @ValidateParams()
    @Timing(log_threshold=0.1)
    def create_user(self, username: str) -> int:
        user_id = 123
        publish_event(UserCreatedEvent(user_id=user_id, username=username))
        return user_id

# 5. 订阅事件
def handle_user_created(event: UserCreatedEvent):
    info(f"用户创建: {event.username}")

subscribe_event(UserCreatedEvent, handle_user_created)

# 6. 启动框架
start_framework(app_info=MyAppInfo)

# 7. 使用服务
user_service = UserService()
user_id = user_service.create_user("Alice")

# 8. 停止框架
stop_framework()
```

## 最佳实践

1. **使用装饰器**：优先使用装饰器，代码更简洁易读
2. **合理使用依赖注入**：单例服务使用依赖注入，多实例服务直接创建
3. **事件驱动**：使用事件系统解耦组件
4. **生命周期管理**：合理使用生命周期装饰器管理资源
5. **配置管理**：使用 `@Config` 装饰器定义配置，使用 `get_config`/`set_config` 访问配置
6. **日志记录**：使用标准日志 API，合理选择日志级别
7. **框架管理**：使用 `start_framework`/`stop_framework` 管理框架生命周期
8. **装饰器工具**：使用 `Interceptor`、`ValidateParams`、`Timing` 增强函数功能

## 常见问题

### Q: 如何处理循环依赖？

A: 框架会自动检测循环依赖并抛出错误。如果确实需要循环依赖，考虑重构代码或使用事件系统解耦。

### Q: 如何调试依赖注入？

A: 使用 `debug()` 日志级别查看依赖注入的详细信息，框架会记录所有依赖解析过程。

### Q: 如何自定义配置验证规则？

A: 使用 `@Config` 装饰器定义配置类，框架会自动推断验证规则。如果需要更复杂的验证，可以在设置配置时进行验证。

### Q: 如何处理异步事件？

A: 使用 `publish_event(event, async_mode=True)` 发布异步事件，订阅者会并发执行。

### Q: 如何优化性能？

A: 使用 `@Timing` 装饰器监控函数执行时间，找出性能瓶颈。使用 `@Interceptor` 缓存结果或优化输入。

## 总结

LStartlet 框架提供了 23 个核心 API，涵盖了依赖注入、事件系统、生命周期管理、配置管理、日志系统、框架管理和装饰器工具等方面。通过合理使用这些 API，可以快速构建功能强大、易于维护的应用程序。

记住：**让简单的事情保持简单，让复杂的事情成为可能但不强制**。