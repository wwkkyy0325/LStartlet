"""
LStartlet - 轻量级Python框架
"""

# 装饰器模块 - 核心装饰器
from ._di_decorator import (
    inject,  # 依赖注入函数（注意：是函数，不是装饰器）
    Service,  # 服务装饰器 - 自动注册和管理
    resolve_service,  # 服务解析函数
)

# 应用程序信息模块
from ._application_info import (
    ApplicationInfo,
)

from ._event_decorator import (
    Event,
    publish_event,
    subscribe_event,
)
from ._lifecycle_decorator import (
    Init,
    Start,
    Stop,
    Destroy,
)

# 工具函数模块
from ._config import (
    get_config,
    set_config,
)

# 日志模块（标准API）
from ._logging import (
    debug,
    info,
    warning,
    error,
    critical,
)

# 极简配置验证装饰器
from ._config import Config

# 框架启动和停止管理
from ._framework import (
    start_framework,
    stop_framework,
)

# 装饰器工具模块（拦截器和中间件）
from ._decorators import (
    # 核心装饰器
    Interceptor,
    ValidateParams,
    Timing,
)

__all__ = [
    # 核心装饰器
    "inject",  # 依赖注入函数
    "Service",  # 服务装饰器 - 自动注册和管理
    "resolve_service",  # 服务解析函数
    # 事件系统
    "Event",
    "publish_event",
    "subscribe_event",
    # 核心生命周期装饰器
    "Init",
    "Start",
    "Stop",
    "Destroy",
    # 核心应用信息API
    "ApplicationInfo",
    # 工具函数
    "get_config",
    "set_config",
    # 核心日志函数（标准API）
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    # 极简配置验证装饰器
    "Config",
    # 框架启动和停止管理
    "start_framework",
    "stop_framework",
    # 装饰器工具模块（核心装饰器）
    "Interceptor",
    "ValidateParams",
    "Timing",
]
