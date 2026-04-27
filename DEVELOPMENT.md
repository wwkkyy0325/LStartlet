# 开发指南

## 概述

LStartlet 是一个轻量级、模块化的 Python 应用框架，提供依赖注入、事件系统、生命周期管理和配置管理等功能。本指南将帮助开发者理解框架的设计理念、核心概念和最佳实践。

## 设计理念

### 简化API

LStartlet 提供23个核心API，大幅降低学习成本和使用复杂度：

- **装饰器**：8个核心装饰器
  - `Service` - 服务装饰器
  - `Event` - 事件基类
  - `Init` - 初始化
  - `Start` - 启动
  - `Stop` - 停止
  - `Destroy` - 销毁
  - `ApplicationInfo` - 应用信息
  - `Config` - 配置装饰器

- **函数**：13个核心函数
  - `inject` - 依赖注入函数
  - `resolve_service` - 服务解析函数
  - `publish_event` - 发布事件
  - `subscribe_event` - 订阅事件
  - `unsubscribe_event` - 取消订阅事件
  - `get_config` - 获取配置
  - `set_config` - 设置配置
  - `debug` - 调试日志
  - `info` - 信息日志
  - `warning` - 警告日志
  - `error` - 错误日志
  - `critical` - 严重错误日志
  - `start_framework` - 启动框架
  - `stop_framework` - 停止框架

- **装饰器工具**：3个装饰器工具
  - `Interceptor` - 拦截器装饰器
  - `ValidateParams` - 参数验证装饰器
  - `Timing` - 性能监控装饰器

### 全自动化

- **依赖注入**：自动解析和注入依赖，无需手动注册
- **生命周期管理**：自动调用生命周期方法，无需手动触发
- **事件系统**：自动路由事件到订阅者，无需手动发布
- **配置管理**：自动保存和加载配置，支持自动保存

### 零配置

- **自动目录管理**：自动创建应用目录和子目录
- **自动日志配置**：自动配置日志输出和文件轮转
- **自动健康检查**：自动检查应用健康状态和依赖关系

## 核心概念

### 1. 依赖注入（DI）

LStartlet 使用装饰器和函数实现依赖注入，自动解析和注入依赖服务。

#### 基本用法

```python
from LStartlet import Service, inject, start_framework

@Service(singleton=True)
class DatabaseService:
    def query(self, sql):
        return f"Query result: {sql}"

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

#### 工作原理

1. 当框架启动时，`@Service` 装饰器自动注册服务到DI容器
2. 框架检测到 `db` 属性的默认值是 `inject(DatabaseService)`
3. 框架自动查找 `DatabaseService` 类并创建实例
4. 框架将实例注入到 `UserService` 的 `db` 属性中

### 2. 事件系统

LStartlet 提供事件驱动架构，实现组件间松耦合。

#### 基本用法

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
        print(f"Sending welcome email to {event.username}")

# 发布事件
publish_event(UserCreatedEvent(user_id=123, username="John Doe"))
```

#### 事件命名空间

框架使用应用名称作为事件命名空间，确保不同应用的事件不会冲突。

### 3. 生命周期管理

LStartlet 提供标准化的生命周期管理，自动调用生命周期方法。

#### 生命周期阶段

1. **Init** - 初始化阶段
   - 在对象创建后立即调用
   - 用于初始化资源和配置

2. **Start** - 启动阶段
   - 在框架启动时调用
   - 用于启动服务和连接

3. **Stop** - 停止阶段
   - 在框架停止时调用
   - 用于停止服务和断开连接

4. **Destroy** - 销毁阶段
   - 在框架停止后调用
   - 用于清理资源和释放内存

#### 基本用法

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

### 4. 配置管理

LStartlet 提供智能的配置管理，自动保存和加载配置。

#### 基本用法

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

#### 配置存储

- **应用配置**：`~/.lstartlet/{app_name}/config/app_config.yaml`
- **框架配置**：`~/.lstartlet/config.yaml`

### 5. 日志系统

LStartlet 提供简化的日志系统，自动配置日志输出和文件轮转。

#### 基本用法

```python
from LStartlet import debug, info, warning, error, critical

# 记录日志
debug("Debug information")
info("Application started")
warning("Configuration using default values")
error("Database connection failed")
critical("System crash")
```

#### 日志存储

- **应用日志**：`~/.lstartlet/{app_name}/logs/{app_name}.log`
- **框架日志**：`~/.lstartlet/logs/lstartlet.log`

## 目录结构

```
~/.lstartlet/
├── MyApp/
│   ├── config.yaml          # 配置文件
│   ├── logs/
│   │   ├── app.log         # 应用日志
│   │   └── myapp.log       # 应用日志（小写）
│   ├── cache/               # 缓存目录
│   ├── data/                # 数据目录
│   ├── plugins/             # 插件目录
│   └── ui/                  # UI 配置目录
│       └── ui_config.yaml   # UI 配置文件
├── logs/
│   └── lstartlet.log        # 框架日志
└── config.yaml              # 框架配置
```

## 最佳实践

### 1. 应用命名

- 使用有意义的名称
- 避免特殊字符
- 使用驼峰命名法（PascalCase）

```python
@ApplicationInfo
class MyWebApplication:
    def get_name(self) -> str:
        return "MyWebApplication"  # ✅ 推荐
```

### 2. 依赖注入

- 优先在类级别定义依赖注入
- 避免循环依赖
- 保持依赖简单

```python
class UserService:
    # 在类级别定义依赖注入，框架会自动注入
    db: DatabaseService = inject(DatabaseService)
    
    def __init__(self):
        pass  # ✅ 推荐：类级别注入
```

### 3. 事件处理

- 使用有意义的事件名称
- 保持事件处理器简单
- 避免在事件处理器中执行长时间操作

```python
from dataclasses import dataclass

@dataclass
class UserCreatedEvent(Event):
    user_id: int
    username: str  # ✅ 推荐：有意义的事件名称

class EmailService:
    def __init__(self):
        subscribe_event(UserCreatedEvent, self.send_welcome_email)
    
    def send_welcome_email(self, event: UserCreatedEvent):
        # 发送邮件（快速操作）
        pass  # ✅ 推荐：简单的事件处理器
```

### 4. 生命周期管理

- 在 `@Init` 中初始化资源
- 在 `@Start` 中启动服务
- 在 `@Stop` 中停止服务
- 在 `@Destroy` 中清理资源

```python
class DatabaseService:
    @Init
    def initialize(self):
        # 初始化连接池
        pass  # ✅ 推荐：初始化资源
    
    @Start
    def connect(self):
        # 连接数据库
        pass  # ✅ 推荐：启动服务
    
    @Stop
    def disconnect(self):
        # 断开连接
        pass  # ✅ 推荐：停止服务
    
    @Destroy
    def cleanup(self):
        # 清理资源
        pass  # ✅ 推荐：清理资源
```

### 5. 配置管理

- 使用字段名作为配置键
- 提供合理的默认值
- 避免在配置中存储敏感信息

```python
from LStartlet import Config, get_config, set_config

@Config("app_config", "应用配置")
class AppConfig:
    database_url: str = "postgresql://localhost/mydb"
    port: int = 8080

# 设置配置 - 使用字段名
set_config("database_url", "postgresql://localhost/mydb")
set_config("port", 8080)

# 获取配置（提供默认值）
app_name = get_config("database_url", "DefaultApp")  # ✅ 推荐：提供默认值
```

### 6. 日志记录

- 使用合适的日志级别
- 记录有意义的消息
- 避免记录敏感信息

```python
from LStartlet import debug, info, warning, error, critical

debug("Debug information")  # ✅ 推荐：有意义的消息
info("Application started")  # ✅ 推荐：合适的日志级别
warning("Configuration using default values")  # ✅ 推荐：警告级别
error("Database connection failed")  # ✅ 推荐：错误级别
critical("System crash")  # ✅ 推荐：严重错误级别
```

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config_manager.py

# 运行特定测试
pytest tests/test_config_manager.py::test_basic_config_operations

# 显示详细输出
pytest -v

# 显示打印输出
pytest -s
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=LStartlet --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 开发工作流

### 1. 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/wwkkyy0325/LStartlet.git
cd LStartlet

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. 运行示例

```bash
# 运行简化API示例
python examples/simplified_api_example.py
```

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并显示覆盖率
pytest --cov=LStartlet --cov-report=html
```

### 4. 代码质量检查

```bash
# 格式化代码
black src/ tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/
```

## 贡献指南

### 1. Fork 仓库

Fork LStartlet 仓库到你的 GitHub 账户。

### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 3. 提交更改

```bash
git add .
git commit -m "Add your feature"
```

### 4. 推送到分支

```bash
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

在 GitHub 上创建 Pull Request，描述你的更改。

## 常见问题

### Q: 如何调试依赖注入问题？

A: 使用框架的日志功能查看依赖注入过程：

```python
from LStartlet import log

log("Debug mode enabled", level="debug")
```

### Q: 如何处理循环依赖？

A: 重构代码，避免循环依赖。可以考虑：
- 使用事件系统解耦
- 引入中间层
- 重新设计组件结构

### Q: 如何自定义日志格式？

A: 目前框架使用固定的日志格式。如需自定义，请使用 Python 标准库的 logging 模块。

### Q: 如何迁移旧代码？

A: 旧代码使用的是已删除的 API，需要迁移到新的简化 API：

```python
# 旧代码（已删除）
from LStartlet import register_service, resolve_service

register_service(MyService, MyService, singleton=True)
service = resolve_service(MyService)

# 新代码（推荐）
from LStartlet import Inject

class MyService:
    def __init__(self):
        pass

service = MyService()  # 自动注入
```

## 许可证

MIT License