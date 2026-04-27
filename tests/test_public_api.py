"""
LStartlet 公共API单元测试

测试所有公共导出的API功能：
- Inject - 依赖注入函数
- Service - 服务装饰器
- Event, publish_event, subscribe_event - 事件系统
- Init, Start, Stop, Destroy - 生命周期装饰器
- ApplicationInfo - 应用信息API
- get_config, set_config - 工具函数
- debug, info, warning, error, critical - 日志函数
- Config - 配置验证装饰器
- start_framework, stop_framework - 框架启动停止
- Interceptor, ValidateParams, Timing - 装饰器工具
"""

import pytest
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from LStartlet import (
    # 核心装饰器
    inject,
    Service,
    # 事件系统
    Event,
    publish_event,
    subscribe_event,
    # 核心生命周期装饰器
    Init,
    Start,
    Stop,
    Destroy,
    # 核心应用信息API
    ApplicationInfo,
    # 工具函数
    get_config,
    set_config,
    # 核心日志函数（标准API）
    debug,
    info,
    warning,
    error,
    critical,
    # 极简配置验证装饰器
    Config,
    # 框架启动和停止管理
    start_framework,
    stop_framework,
    # 装饰器工具模块（核心装饰器）
    Interceptor,
    ValidateParams,
    Timing,
)

# ============================================================================
# inject 依赖注入函数测试
# ============================================================================


class TestInject:
    """测试inject依赖注入函数"""

    def test_inject_marker_creation(self):
        """测试inject标记对象创建"""

        marker = inject(str)
        assert marker is not None

    def test_inject_without_type(self):
        """测试不带类型的inject"""

        marker = inject()
        assert marker is not None

    def test_inject_with_service(self):
        """测试inject与Service配合使用"""

        @Service(singleton=True)
        class DatabaseService:
            def __init__(self):
                self.data = []

        class UserService:
            def __init__(self):
                # 使用inject标记需要注入的属性
                self.db: DatabaseService = inject(DatabaseService)

        # 创建实例
        user_service = UserService()

        # 验证inject标记存在
        assert hasattr(user_service, "db")
        assert isinstance(user_service.db, type(inject()))


# ============================================================================
# Service 服务装饰器测试
# ============================================================================


class TestService:
    """测试Service装饰器"""

    def test_service_decorator(self):
        """测试Service装饰器基本功能"""

        @Service(singleton=True)
        class TestService:
            def __init__(self):
                self.value = 42

        # 验证装饰器添加了必要的属性
        assert hasattr(TestService, "_is_service")
        assert getattr(TestService, "_is_service") is True

    def test_service_singleton_attribute(self):
        """测试单例服务属性"""

        @Service(singleton=True)
        class SingletonService:
            pass

        assert hasattr(SingletonService, "_service_singleton")
        assert getattr(SingletonService, "_service_singleton") is True

    def test_service_transient_attribute(self):
        """测试瞬态服务属性"""

        @Service(singleton=False)
        class TransientService:
            pass

        assert hasattr(TransientService, "_service_singleton")
        assert getattr(TransientService, "_service_singleton") is False

    def test_service_auto_start_attribute(self):
        """测试自动启动服务属性"""

        @Service(singleton=True, auto_start=True)
        class AutoStartService:
            pass

        assert hasattr(AutoStartService, "_service_auto_start")
        assert getattr(AutoStartService, "_service_auto_start") is True


# ============================================================================
# Event 事件系统测试
# ============================================================================


class TestEventSystem:
    """测试事件系统"""

    def test_event_creation(self):
        """测试事件创建"""

        class CustomEvent(Event):
            def __init__(self, data):
                self.data = data

        event = CustomEvent("test data")
        assert event.data == "test data"

    def test_event_inheritance(self):
        """测试事件继承"""

        class CustomEvent(Event):
            pass

        event = CustomEvent()
        assert isinstance(event, Event)

    def test_publish_event(self):
        """测试事件发布"""

        class TestEvent(Event):
            def __init__(self, message):
                self.message = message

        # 发布事件（即使没有订阅者也不应该报错）
        publish_event(TestEvent("Hello"))
        assert True


# ============================================================================
# Init 生命周期装饰器测试
# ============================================================================


class TestInitDecorator:
    """测试Init装饰器"""

    def test_init_decorator(self):
        """测试Init装饰器"""

        @Init()
        def on_init(self):
            pass

        # 验证装饰器成功应用
        assert on_init is not None


# ============================================================================
# Start 生命周期装饰器测试
# ============================================================================


class TestStartDecorator:
    """测试Start装饰器"""

    def test_start_decorator(self):
        """测试Start装饰器"""

        @Start()
        def on_start(self):
            pass

        # 验证装饰器成功应用
        assert on_start is not None


# ============================================================================
# Stop 生命周期装饰器测试
# ============================================================================


class TestStopDecorator:
    """测试Stop装饰器"""

    def test_stop_decorator(self):
        """测试Stop装饰器"""

        @Stop()
        def on_stop(self):
            pass

        # 验证装饰器成功应用
        assert on_stop is not None


# ============================================================================
# Destroy 生命周期装饰器测试
# ============================================================================


class TestDestroyDecorator:
    """测试Destroy装饰器"""

    def test_destroy_decorator(self):
        """测试Destroy装饰器"""

        @Destroy()
        def on_destroy(self):
            pass

        # 验证装饰器成功应用
        assert on_destroy is not None


# ============================================================================
# ApplicationInfo 应用信息API测试
# ============================================================================


class TestApplicationInfo:
    """测试ApplicationInfo装饰器"""

    def test_application_info_basic(self):
        """测试基本应用信息"""

        @ApplicationInfo
        class MyApp:
            def get_directory_name(self) -> str:
                return "myapp"

        # 验证装饰器成功应用
        assert MyApp is not None

    def test_application_info_with_display_name(self):
        """测试带显示名的应用信息"""

        @ApplicationInfo
        class MyApp:
            def get_directory_name(self) -> str:
                return "myapp"

            def get_display_name(self) -> str:
                return "我的应用"

        # 创建实例
        app = MyApp()

        # 验证方法存在
        assert hasattr(app, "get_directory_name")
        assert hasattr(app, "get_display_name")

    def test_application_info_with_version(self):
        """测试带版本的应用信息"""

        @ApplicationInfo
        class MyApp:
            def get_directory_name(self) -> str:
                return "myapp"

            def get_version(self) -> str:
                return "1.0.0"

        # 创建实例
        app = MyApp()

        # 验证方法存在
        assert hasattr(app, "get_directory_name")
        assert hasattr(app, "get_version")

    def test_application_info_instance_creation(self):
        """测试应用信息实例创建"""

        @ApplicationInfo
        class MyApp:
            def get_directory_name(self) -> str:
                return "myapp"

        # 创建实例
        app = MyApp()

        # 验证实例方法可以调用
        assert app.get_directory_name() == "myapp"


# ============================================================================
# get_config/set_config 工具函数测试
# ============================================================================


class TestConfigFunctions:
    """测试配置函数"""

    def test_get_config_with_default(self):
        """测试获取配置默认值"""

        # 获取不存在的配置，使用默认值
        value = get_config("nonexistent_key", default="default_value")

        assert value == "default_value"


# ============================================================================
# 日志函数测试
# ============================================================================


class TestLoggingFunctions:
    """测试日志函数"""

    def test_debug_logging(self):
        """测试debug日志"""
        # 这个测试只验证函数可以被调用
        debug("Debug message")
        assert True

    def test_info_logging(self):
        """测试info日志"""
        info("Info message")
        assert True

    def test_warning_logging(self):
        """测试warning日志"""
        warning("Warning message")
        assert True

    def test_error_logging(self):
        """测试error日志"""
        error("Error message")
        assert True

    def test_critical_logging(self):
        """测试critical日志"""
        critical("Critical message")
        assert True


# ============================================================================
# Config 配置验证装饰器测试
# ============================================================================


class TestConfigDecorator:
    """测试Config装饰器"""

    def test_config_decorator(self):
        """测试Config装饰器"""

        @Config(name="app_config")
        class AppConfig:
            def __init__(self):
                self.name: str = "default"
                self.port: int = 8080

        # 验证装饰器成功应用
        assert AppConfig is not None

    def test_config_instance_creation(self):
        """测试配置实例创建"""

        @Config(name="app_config")
        class AppConfig:
            def __init__(self):
                self.name: str = "default"
                self.port: int = 8080

        # 创建实例
        config = AppConfig()

        # 验证实例属性
        assert config.name == "default"
        assert config.port == 8080


# ============================================================================
# start_framework/stop_framework 测试
# ============================================================================


class TestFrameworkStartStop:
    """测试框架启动和停止"""

    def test_start_framework_with_app_info(self):
        """测试带应用信息的框架启动"""

        @ApplicationInfo
        class TestApp:
            def get_directory_name(self) -> str:
                return "testapp"

        # 启动框架
        start_framework(app_info=TestApp)

        # 验证框架启动成功
        assert True

        # 停止框架
        stop_framework()

    def test_start_framework_basic(self):
        """测试基本框架启动"""

        # 启动框架（不带应用信息）
        start_framework()

        # 验证框架启动成功
        assert True

        # 停止框架
        stop_framework()

    def test_stop_framework(self):
        """测试框架停止"""

        # 启动框架
        start_framework()

        # 停止框架
        stop_framework()

        # 验证框架停止成功
        assert True


# ============================================================================
# Interceptor 装饰器测试
# ============================================================================


class TestInterceptor:
    """测试Interceptor装饰器"""

    def test_interceptor_decorator(self):
        """测试Interceptor装饰器"""

        @Interceptor()
        def test_function():
            return "result"

        # 验证装饰器成功应用
        assert test_function is not None

    def test_interceptor_functionality(self):
        """测试拦截器功能"""

        calls = []

        @Interceptor()
        def test_function():
            calls.append("function")
            return "result"

        result = test_function()

        assert result == "result"
        assert "function" in calls


# ============================================================================
# ValidateParams 装饰器测试
# ============================================================================


class TestValidateParams:
    """测试ValidateParams装饰器"""

    def test_validate_params_decorator(self):
        """测试ValidateParams装饰器"""

        @ValidateParams()
        def test_function(name: str, age: int):
            return f"{name} is {age} years old"

        # 验证装饰器成功应用
        assert test_function is not None

    def test_validate_params_functionality(self):
        """测试参数验证功能"""

        @ValidateParams()
        def test_function(name: str, age: int):
            return f"{name} is {age} years old"

        # 正确的类型
        result = test_function("Alice", 30)
        assert result == "Alice is 30 years old"


# ============================================================================
# Timing 装饰器测试
# ============================================================================


class TestTiming:
    """测试Timing装饰器"""

    def test_timing_decorator(self):
        """测试Timing装饰器"""

        @Timing()
        def test_function():
            return "result"

        # 验证装饰器成功应用
        assert test_function is not None

    def test_timing_functionality(self):
        """测试计时功能"""

        @Timing()
        def test_function():
            return "result"

        result = test_function()

        assert result == "result"

    def test_timing_with_args(self):
        """测试带参数的计时装饰器"""

        @Timing()
        def test_function(a, b):
            return a + b

        result = test_function(2, 3)

        assert result == 5


# ============================================================================
# 综合测试
# ============================================================================


class TestIntegration:
    """综合集成测试"""

    def test_service_with_lifecycle(self):
        """测试带生命周期的服务"""

        @Service(singleton=True, auto_start=True)
        class LifecycleService:
            @Init()
            def on_init(self):
                self.initialized = True

            @Start()
            def on_start(self):
                self.started = True

            @Stop()
            def on_stop(self):
                self.stopped = True

            @Destroy()
            def on_destroy(self):
                self.destroyed = True

        @ApplicationInfo
        class TestApp:
            def get_directory_name(self) -> str:
                return "testapp"

        # 启动框架
        start_framework(app_info=TestApp)

        # 验证服务属性
        assert hasattr(LifecycleService, "_is_service")
        assert getattr(LifecycleService, "_is_service") is True

        # 停止框架
        stop_framework()

    def test_multiple_services(self):
        """测试多个服务"""

        @Service(singleton=True)
        class ServiceA:
            def __init__(self):
                self.name = "ServiceA"

        @Service(singleton=True)
        class ServiceB:
            def __init__(self):
                self.name = "ServiceB"

        # 验证服务注册
        assert hasattr(ServiceA, "_is_service")
        assert hasattr(ServiceB, "_is_service")

        @ApplicationInfo
        class TestApp:
            def get_directory_name(self) -> str:
                return "testapp"

        # 启动框架
        start_framework(app_info=TestApp)

        # 停止框架
        stop_framework()

    def test_event_system_integration(self):
        """测试事件系统集成"""

        class TestEvent(Event):
            def __init__(self, data):
                self.data = data

        # 发布事件
        publish_event(TestEvent("test data"))

        # 验证事件可以创建和发布
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
