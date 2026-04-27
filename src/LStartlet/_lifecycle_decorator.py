"""
生命周期装饰器模块 - 提供简化的组件生命周期管理（内部实现）

支持以下生命周期阶段：
1. 初始化阶段：@Init
2. 启动阶段：@Start
3. 停止阶段：@Stop
4. 销毁阶段：@Destroy
5. 配置阶段：@_OnConfigChange（内部实现）
6. 依赖注入阶段：@_OnDependenciesResolved（内部实现）

每个装饰器都支持条件执行和优先级控制。
"""

import inspect
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
from dataclasses import dataclass, field
from enum import Enum

# 导入Event基类
from ._event_decorator import Event


class _LifecyclePhase(Enum):
    """生命周期阶段枚举（内部实现）"""

    POST_INIT = "post_init"
    POST_START = "post_start"
    POST_STOP = "post_stop"
    POST_DESTROY = "post_destroy"
    ON_CONFIG_CHANGE = "on_config_change"
    ON_DEPENDENCIES_RESOLVED = "on_dependencies_resolved"


@dataclass
class _LifecycleMethod:
    """生命周期方法包装器（内部实现）"""

    method: Callable
    phase: _LifecyclePhase
    condition: Optional[Callable] = None
    priority: int = 0
    enabled: bool = True


class _LifecycleManager:
    """生命周期管理器（内部实现）"""

    def __init__(self):
        self._methods: Dict[Type, Dict[_LifecyclePhase, List[_LifecycleMethod]]] = {}

    def _register_method(
        self,
        cls: Type,
        method: Callable,
        phase: _LifecyclePhase,
        condition: Optional[Callable] = None,
        priority: int = 0,
        enabled: bool = True,
    ):
        """注册生命周期方法（内部方法）"""
        if cls not in self._methods:
            self._methods[cls] = {}

        if phase not in self._methods[cls]:
            self._methods[cls][phase] = []

        lifecycle_method = _LifecycleMethod(
            method=method,
            phase=phase,
            condition=condition,
            priority=priority,
            enabled=enabled,
        )
        self._methods[cls][phase].append(lifecycle_method)

        self._methods[cls][phase].sort(key=lambda x: x.priority)

    def _get_methods(self, cls: Type, phase: _LifecyclePhase) -> List[_LifecycleMethod]:
        """获取指定类和阶段的生命周期方法（内部方法）"""
        if cls not in self._methods:
            return []
        return self._methods[cls].get(phase, [])

    def _execute_phase(self, instance: Any, phase: _LifecyclePhase, **kwargs):
        """执行指定阶段的所有生命周期方法（内部方法）"""
        cls = type(instance)
        methods = self._get_methods(cls, phase)

        for method_wrapper in methods:
            if not method_wrapper.enabled:
                continue

            if method_wrapper.condition is not None:
                try:
                    if not method_wrapper.condition(instance, **kwargs):
                        continue
                except Exception:
                    continue

            try:
                sig = inspect.signature(method_wrapper.method)
                method_params = list(sig.parameters.keys())

                method_kwargs = {}
                if "self" in method_params:
                    method_params.remove("self")

                for param in method_params:
                    if param in kwargs:
                        method_kwargs[param] = kwargs[param]

                method_wrapper.method(instance, **method_kwargs)
            except Exception:
                pass


# 全局生命周期管理器实例
_lifecycle_manager = _LifecycleManager()


def _get_lifecycle_manager() -> _LifecycleManager:
    """获取生命周期管理器实例（内部函数）"""
    return _lifecycle_manager


def _create_lifecycle_decorator(phase: _LifecyclePhase):
    """为指定生命周期阶段创建装饰器（内部函数）"""

    def decorator(obj_or_name=None, **kwargs):
        condition = kwargs.get("condition")
        priority = kwargs.get("priority", 0)
        enabled = kwargs.get("enabled", True)
        name = kwargs.get("name")

        def wrapper(func):
            if not hasattr(func, "_decorator_metadata"):
                setattr(func, "_decorator_metadata", [])

            metadata = {
                "type": "lifecycle",
                "phase": phase,
                "condition": condition,
                "priority": priority,
                "enabled": enabled,
            }

            getattr(func, "_decorator_metadata").append(metadata)

            if phase == _LifecyclePhase.ON_CONFIG_CHANGE:
                config_key = kwargs.get("config_key", name)
                metadata["config_key"] = config_key

            return func

        if callable(obj_or_name) and not kwargs:
            func = obj_or_name
            if not hasattr(func, "_decorator_metadata"):
                setattr(func, "_decorator_metadata", [])

            metadata = {
                "type": "lifecycle",
                "phase": phase,
                "condition": None,
                "priority": 0,
                "enabled": True,
            }

            getattr(func, "_decorator_metadata").append(metadata)

            return func

        return wrapper

    return decorator


def _OnConfigChange(config_key: Optional[str] = None):
    """配置变更监听装饰器（内部实现）"""

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_decorator_metadata"):
            setattr(func, "_decorator_metadata", [])

        metadata = {
            "type": "lifecycle",
            "phase": _LifecyclePhase.ON_CONFIG_CHANGE,
            "condition": None,
            "priority": 0,
            "enabled": True,
            "config_key": config_key,
        }
        getattr(func, "_decorator_metadata").append(metadata)

        return func

    return decorator


def _OnDependenciesResolved():
    """依赖注入完成监听装饰器（内部实现）"""

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_decorator_metadata"):
            setattr(func, "_decorator_metadata", [])

        metadata = {
            "type": "lifecycle",
            "phase": _LifecyclePhase.ON_DEPENDENCIES_RESOLVED,
            "condition": None,
            "priority": 0,
            "enabled": True,
        }
        getattr(func, "_decorator_metadata").append(metadata)

        return func

    return decorator


def _trigger_lifecycle_phase(instance: Any, phase: _LifecyclePhase, **kwargs):
    """触发生命周期阶段（内部函数）"""
    cls = type(instance)

    methods = _lifecycle_manager._get_methods(cls, phase)

    if not hasattr(instance, "_executed_lifecycle_methods"):
        setattr(instance, "_executed_lifecycle_methods", set())

    executed_methods = getattr(instance, "_executed_lifecycle_methods")

    for method_wrapper in methods:
        method_key = (phase, method_wrapper.method.__name__)
        if method_key not in executed_methods:
            if not method_wrapper.enabled:
                continue

            if method_wrapper.condition is not None:
                try:
                    if not method_wrapper.condition(instance, **kwargs):
                        continue
                except Exception:
                    continue

            try:
                sig = inspect.signature(method_wrapper.method)
                method_params = list(sig.parameters.keys())

                method_kwargs = {}
                if "self" in method_params:
                    method_params.remove("self")

                for param in method_params:
                    if param in kwargs:
                        method_kwargs[param] = kwargs[param]

                method_wrapper.method(instance, **method_kwargs)
                executed_methods.add(method_key)
            except Exception:
                pass


def _trigger_all_lifecycle_phases(
    instance: Any, phases: List[_LifecyclePhase], **kwargs
):
    """触发多个生命周期阶段（内部函数）"""
    for phase in phases:
        _trigger_lifecycle_phase(instance, phase, **kwargs)


@dataclass
class _ConfigChangeEvent(Event):
    """配置变更事件（内部实现）"""

    key: str = ""
    old_value: Any = None
    new_value: Any = None


def _notify_config_change(key: str, old_value: Any, new_value: Any):
    """通知配置变更（内部函数）"""
    event = _ConfigChangeEvent(key, old_value, new_value)

    for cls, methods_dict in _lifecycle_manager._methods.items():
        if _LifecyclePhase.ON_CONFIG_CHANGE in methods_dict:
            methods = methods_dict[_LifecyclePhase.ON_CONFIG_CHANGE]
            for method_wrapper in methods:
                config_key = getattr(method_wrapper.method, "_config_key", None)
                if config_key is None or config_key == key:
                    try:
                        pass
                    except Exception:
                        pass


def _register_lifecycle_methods_for_class(cls: Type):
    """为已注册的类注册生命周期方法（内部函数）"""
    if cls in _lifecycle_manager._methods:
        return

    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        metadata = getattr(method, "_decorator_metadata", None)
        if metadata:
            for meta in metadata:
                if meta.get("type") == "lifecycle":
                    phase = meta["phase"]
                    condition = meta.get("condition")
                    priority = meta.get("priority", 0)
                    enabled = meta.get("enabled", True)

                    _lifecycle_manager._register_method(
                        cls,
                        method,
                        phase,
                        condition=condition,
                        priority=priority,
                        enabled=enabled,
                    )

                    if phase == _LifecyclePhase.ON_CONFIG_CHANGE:
                        config_key = meta.get("config_key")
                        if config_key:
                            _setup_config_change_handler(cls, method, config_key)


def _get_class_instances(cls: Type) -> List[Any]:
    """获取指定类的所有活跃实例（内部函数）"""
    return []


def _setup_config_change_handler(cls: Type, method: Callable, config_key: str):
    """设置配置变更处理器（内部函数）"""
    try:
        from ._event_decorator import _subscribe_event

        from dataclasses import dataclass
        from typing import Any

        @dataclass
        class ConfigChangeEvent(Event):
            """配置变更事件"""

            key: str = ""
            old_value: Any = None
            new_value: Any = None

        def handle_config_change(event: ConfigChangeEvent):
            if event.key == config_key:
                instances = _get_class_instances(cls)
                for instance in instances:
                    metadata = getattr(method, "_lifecycle_metadata", [])
                    if isinstance(metadata, list):
                        for meta in metadata:
                            if meta.get("enabled", True):
                                condition = meta.get("condition")
                                if condition is None or condition(
                                    instance,
                                    old_value=event.old_value,
                                    new_value=event.new_value,
                                ):
                                    method(instance, event.old_value, event.new_value)

        _subscribe_event(ConfigChangeEvent, handle_config_change)

    except (ImportError, AttributeError):
        pass


def Init(condition=None, priority=0, enabled=True):
    """
    初始化生命周期装饰器 - 在组件初始化后触发

    Args:
        condition: 条件函数，接收实例和kwargs，返回True时执行
        priority: 优先级，数值越小优先级越高，默认为0
        enabled: 是否启用，默认为True

    Returns:
        装饰后的方法

    Example:
        class MyService:
            @Init()
            def initialize_resources(self):
                print("初始化资源")

            @Init(priority=-1)
            def critical_initialization(self):
                print("关键初始化，优先执行")

    Note:
        - 在组件实例化时自动触发
        - 支持条件执行，只有满足条件才会调用
        - 支持优先级控制，数值越小优先级越高
        - 每个方法只会执行一次
        - 适用于初始化资源、建立连接等操作
    """
    return _create_lifecycle_decorator(_LifecyclePhase.POST_INIT)(
        condition=condition, priority=priority, enabled=enabled
    )


def Start(condition=None, priority=0, enabled=True):
    """
    启动生命周期装饰器 - 在框架启动时、组件启动后触发

    Args:
        condition: 条件函数，接收实例和kwargs，返回True时执行
        priority: 优先级，数值越小优先级越高，默认为0
        enabled: 是否启用，默认为True

    Returns:
        装饰后的方法

    Example:
        class MyService:
            @Start()
            def start_service(self):
                print("启动服务")

            @Start(priority=1)
            def start_background_tasks(self):
                print("启动后台任务")

    Note:
        - 在调用 start_framework() 时自动触发
        - 支持条件执行，只有满足条件才会调用
        - 支持优先级控制，数值越小优先级越高
        - 适用于启动服务、开启后台任务等操作
    """
    return _create_lifecycle_decorator(_LifecyclePhase.POST_START)(
        condition=condition, priority=priority, enabled=enabled
    )


def Stop(condition=None, priority=0, enabled=True):
    """
    停止生命周期装饰器 - 在框架停止时、组件停止后触发

    Args:
        condition: 条件函数，接收实例和kwargs，返回True时执行
        priority: 优先级，数值越小优先级越高，默认为0
        enabled: 是否启用，默认为True

    Returns:
        装饰后的方法

    Example:
        class MyService:
            @Stop()
            def cleanup_after_stop(self):
                print("停止后清理")

            @Stop(priority=-1)
            def critical_cleanup(self):
                print("关键清理，优先执行")

    Note:
        - 在调用 stop_framework() 时自动触发
        - 支持条件执行，只有满足条件才会调用
        - 支持优先级控制，数值越小优先级越高
        - 适用于停止后的清理工作、保存状态等操作
    """
    return _create_lifecycle_decorator(_LifecyclePhase.POST_STOP)(
        condition=condition, priority=priority, enabled=enabled
    )


def Destroy(condition=None, priority=0, enabled=True):
    """
    销毁生命周期装饰器 - 在组件销毁后触发

    Args:
        condition: 条件函数，接收实例和kwargs，返回True时执行
        priority: 优先级，数值越小优先级越高，默认为0
        enabled: 是否启用，默认为True

    Returns:
        装饰后的方法

    Example:
        class MyService:
            @Destroy()
            def release_resources(self):
                print("释放资源")

            @Destroy(priority=1)
            def cleanup_temp_files(self):
                print("清理临时文件")

    Note:
        - 在调用 stop_framework() 时自动触发
        - 支持条件执行，只有满足条件才会调用
        - 支持优先级控制，数值越小优先级越高
        - 适用于资源释放、清理临时文件等操作
    """
    return _create_lifecycle_decorator(_LifecyclePhase.POST_DESTROY)(
        condition=condition, priority=priority, enabled=enabled
    )
