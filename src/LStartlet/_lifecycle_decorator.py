"""
生命周期装饰器模块 - 提供细粒度的组件生命周期管理

支持以下生命周期阶段：
1. 初始化阶段：@PreInit, @PostInit
2. 启动阶段：@PreStart, @PostStart
3. 运行阶段：@PreExecute, @PostExecute
4. 停止阶段：@PreStop, @PostStop
5. 销毁阶段：@PreDestroy, @PostDestroy
6. 配置阶段：@OnConfigChange
7. 依赖注入阶段：@OnDependenciesResolved

每个装饰器都支持条件执行和优先级控制。
"""

import inspect
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
from dataclasses import dataclass, field
from enum import Enum


class LifecyclePhase(Enum):
    """生命周期阶段枚举"""

    PRE_INIT = "pre_init"
    POST_INIT = "post_init"
    PRE_START = "pre_start"
    POST_START = "post_start"
    PRE_EXECUTE = "pre_execute"
    POST_EXECUTE = "post_execute"
    PRE_STOP = "pre_stop"
    POST_STOP = "post_stop"
    PRE_DESTROY = "pre_destroy"
    POST_DESTROY = "post_destroy"
    ON_CONFIG_CHANGE = "on_config_change"
    ON_DEPENDENCIES_RESOLVED = "on_dependencies_resolved"


@dataclass
class LifecycleMethod:
    """生命周期方法包装器"""

    method: Callable
    phase: LifecyclePhase
    condition: Optional[Callable] = None
    priority: int = 0  # 数字越小优先级越高
    enabled: bool = True


class LifecycleManager:
    """生命周期管理器"""

    def __init__(self):
        self._methods: Dict[Type, Dict[LifecyclePhase, List[LifecycleMethod]]] = {}

    def register_method(
        self,
        cls: Type,
        method: Callable,
        phase: LifecyclePhase,
        condition: Optional[Callable] = None,
        priority: int = 0,
        enabled: bool = True,
    ):
        """注册生命周期方法"""
        if cls not in self._methods:
            self._methods[cls] = {}

        if phase not in self._methods[cls]:
            self._methods[cls][phase] = []

        lifecycle_method = LifecycleMethod(
            method=method,
            phase=phase,
            condition=condition,
            priority=priority,
            enabled=enabled,
        )
        self._methods[cls][phase].append(lifecycle_method)

        # 按优先级排序
        self._methods[cls][phase].sort(key=lambda x: x.priority)

    def get_methods(self, cls: Type, phase: LifecyclePhase) -> List[LifecycleMethod]:
        """获取指定类和阶段的生命周期方法"""
        if cls not in self._methods:
            return []
        return self._methods[cls].get(phase, [])

    def execute_phase(self, instance: Any, phase: LifecyclePhase, **kwargs):
        """执行指定阶段的所有生命周期方法"""
        cls = type(instance)
        methods = self.get_methods(cls, phase)

        for method_wrapper in methods:
            if not method_wrapper.enabled:
                continue

            # 检查条件
            if method_wrapper.condition is not None:
                try:
                    if not method_wrapper.condition(instance, **kwargs):
                        continue
                except Exception:
                    continue

            # 执行方法
            try:
                # 获取方法签名以确定参数
                sig = inspect.signature(method_wrapper.method)
                method_params = list(sig.parameters.keys())

                # 准备参数
                method_kwargs = {}
                if "self" in method_params:
                    method_params.remove("self")

                # 传递相关参数
                for param in method_params:
                    if param in kwargs:
                        method_kwargs[param] = kwargs[param]

                method_wrapper.method(instance, **method_kwargs)
            except Exception:
                pass


# 全局生命周期管理器实例
_lifecycle_manager = LifecycleManager()


def get_lifecycle_manager() -> LifecycleManager:
    """获取生命周期管理器实例"""
    return _lifecycle_manager


def _create_lifecycle_decorator(phase: LifecyclePhase):
    """为指定生命周期阶段创建装饰器"""

    def decorator(obj_or_name=None, **kwargs):
        condition = kwargs.get("condition")
        priority = kwargs.get("priority", 0)
        enabled = kwargs.get("enabled", True)
        name = kwargs.get("name")

        def wrapper(func):
            # 使用统一的元数据属性名 _decorator_metadata
            if not hasattr(func, "_decorator_metadata"):
                setattr(func, "_decorator_metadata", [])

            # 统一的元数据结构
            metadata = {
                "type": "lifecycle",
                "phase": phase,
                "condition": condition,
                "priority": priority,
                "enabled": enabled,
            }

            getattr(func, "_decorator_metadata").append(metadata)

            # 如果是OnConfigChange阶段，存储配置键
            if phase == LifecyclePhase.ON_CONFIG_CHANGE:
                config_key = kwargs.get("config_key", name)
                metadata["config_key"] = config_key

            # 保持向后兼容性：同时设置旧的 _lifecycle_metadata 属性
            if not hasattr(func, "_lifecycle_metadata"):
                setattr(func, "_lifecycle_metadata", [])
            getattr(func, "_lifecycle_metadata").append(
                {
                    "phase": phase,
                    "condition": condition,
                    "priority": priority,
                    "enabled": enabled,
                }
            )

            return func

        # 处理无参调用情况
        if callable(obj_or_name) and not kwargs:
            func = obj_or_name
            if not hasattr(func, "_decorator_metadata"):
                setattr(func, "_decorator_metadata", [])

            # 统一的元数据结构
            metadata = {
                "type": "lifecycle",
                "phase": phase,
                "condition": None,
                "priority": 0,
                "enabled": True,
            }

            getattr(func, "_decorator_metadata").append(metadata)

            # 保持向后兼容性：同时设置旧的 _lifecycle_metadata 属性
            if not hasattr(func, "_lifecycle_metadata"):
                setattr(func, "_lifecycle_metadata", [])
            getattr(func, "_lifecycle_metadata").append(
                {"phase": phase, "condition": None, "priority": 0, "enabled": True}
            )

            return func

        return wrapper

    return decorator


# 定义具体的生命周期装饰器，每个都附带完整的文档字符串
PreInit = _create_lifecycle_decorator(LifecyclePhase.PRE_INIT)
PreInit.__doc__ = """
初始化前生命周期装饰器

在组件实例化后、初始化前触发，适用于准备工作。
这是组件实例化过程中的第一个生命周期阶段。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PreInit(priority=1)
        def prepare_resources(self):
            print("准备资源")
            
        @PreInit(condition=lambda self: self.enabled)
        def conditional_prepare(self):
            print("条件性准备")
"""

PostInit = _create_lifecycle_decorator(LifecyclePhase.POST_INIT)
PostInit.__doc__ = """
初始化后生命周期装饰器（简化版：@Init）

在组件初始化后触发，适用于初始化资源。
这是组件实例化时自动触发的阶段之一。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PostInit()
        def initialize_resources(self):
            print("初始化资源")
            
        @PostInit(priority=-1)
        def critical_initialization(self):
            print("关键初始化，优先执行")
"""

PreStart = _create_lifecycle_decorator(LifecyclePhase.PRE_START)
PreStart.__doc__ = """
启动前生命周期装饰器

在框架启动时、组件启动前触发，适用于启动准备工作。
调用 start_framework() 时自动触发。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PreStart()
        def prepare_for_start(self):
            print("准备启动")
            
        @PreStart(condition=lambda self: self.is_ready)
        def conditional_start_prep(self):
            print("条件性启动准备")
"""

PostStart = _create_lifecycle_decorator(LifecyclePhase.POST_START)
PostStart.__doc__ = """
启动后生命周期装饰器（简化版：@Start）

在框架启动时、组件启动后触发，适用于启动服务。
调用 start_framework() 时自动触发。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PostStart()
        def start_service(self):
            print("启动服务")
            
        @PostStart(priority=1)
        def start_background_tasks(self):
            print("启动后台任务")
"""

PreExecute = _create_lifecycle_decorator(LifecyclePhase.PRE_EXECUTE)
PreExecute.__doc__ = """
执行前生命周期装饰器

在执行业务逻辑前触发，适用于执行前的准备工作。
需要手动调用 trigger_lifecycle_phase() 触发。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PreExecute()
        def prepare_execution(self):
            print("准备执行")
            
        def execute_task(self):
            trigger_lifecycle_phase(self, LifecyclePhase.PRE_EXECUTE)
            print("执行任务")
"""

PostExecute = _create_lifecycle_decorator(LifecyclePhase.POST_EXECUTE)
PostExecute.__doc__ = """
执行后生命周期装饰器

在执行业务逻辑后触发，适用于执行后的清理工作。
需要手动调用 trigger_lifecycle_phase() 触发。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PostExecute()
        def cleanup_execution(self):
            print("清理执行")
            
        def execute_task(self):
            print("执行任务")
            trigger_lifecycle_phase(self, LifecyclePhase.POST_EXECUTE)
"""

PreStop = _create_lifecycle_decorator(LifecyclePhase.PRE_STOP)
PreStop.__doc__ = """
停止前生命周期装饰器

在框架停止时、组件停止前触发，适用于停止准备工作。
调用 stop_framework() 时自动触发。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PreStop()
        def prepare_for_stop(self):
            print("准备停止")
            
        @PreStop(priority=1)
        def save_state_before_stop(self):
            print("停止前保存状态")
"""

PostStop = _create_lifecycle_decorator(LifecyclePhase.POST_STOP)
PostStop.__doc__ = """
停止后生命周期装饰器（简化版：@Stop）

在框架停止时、组件停止后触发，适用于停止后的清理工作。
调用 stop_framework() 时自动触发。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PostStop()
        def cleanup_after_stop(self):
            print("停止后清理")
            
        @PostStop(priority=-1)
        def critical_cleanup(self):
            print("关键清理，优先执行")
"""

PreDestroy = _create_lifecycle_decorator(LifecyclePhase.PRE_DESTROY)
PreDestroy.__doc__ = """
销毁前生命周期装饰器

在组件销毁前触发，适用于销毁前的准备工作。
调用 stop_framework() 时自动触发。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PreDestroy()
        def prepare_for_destroy(self):
            print("准备销毁")
            
        @PreDestroy(condition=lambda self: self.needs_cleanup)
        def conditional_cleanup_prep(self):
            print("条件性清理准备")
"""

PostDestroy = _create_lifecycle_decorator(LifecyclePhase.POST_DESTROY)
PostDestroy.__doc__ = """
销毁后生命周期装饰器（简化版：@Destroy）

在组件销毁后触发，适用于资源释放。
调用 stop_framework() 时自动触发。

Args:
    condition: 条件函数，接收实例和kwargs，返回True时执行
    priority: 优先级，数值越小优先级越高，默认为0
    enabled: 是否启用，默认为True

Example:
    @Component
    class MyService:
        @PostDestroy()
        def release_resources(self):
            print("释放资源")
            
        @PostDestroy(priority=1)
        def cleanup_temp_files(self):
            print("清理临时文件")
"""


def OnConfigChange(config_key: Optional[str] = None):
    """
    配置变更监听装饰器

    Args:
        config_key: 监听的配置键，如果为None则监听所有配置变更

    Example:
        @Component
        class ConfigurableService:
            @OnConfigChange("database.url")
            def on_database_url_change(self, old_value, new_value):
                # 处理数据库URL变更
                pass
    """

    def decorator(func: Callable) -> Callable:
        # 使用统一的元数据属性名 _decorator_metadata
        if not hasattr(func, "_decorator_metadata"):
            setattr(func, "_decorator_metadata", [])

        metadata = {
            "type": "lifecycle",
            "phase": LifecyclePhase.ON_CONFIG_CHANGE,
            "condition": None,
            "priority": 0,
            "enabled": True,
            "config_key": config_key,
        }
        getattr(func, "_decorator_metadata").append(metadata)

        # 保持向后兼容性：同时设置旧的 _lifecycle_metadata 属性
        setattr(func, "_config_key", config_key)
        if not hasattr(func, "_lifecycle_metadata"):
            setattr(func, "_lifecycle_metadata", [])

        getattr(func, "_lifecycle_metadata").append(
            {"phase": LifecyclePhase.ON_CONFIG_CHANGE, "condition": None, "priority": 0}
        )

        return func

    return decorator


def OnDependenciesResolved():
    """
    依赖注入完成监听装饰器

    在所有依赖注入完成后调用，适用于需要在依赖就绪后进行初始化的场景

    Example:
        @Component
        class ComplexService:
            def __init__(self, dep1: Service1 = Inject(), dep2: Service2 = Inject()):
                self.dep1 = dep1
                self.dep2 = dep2

            @OnDependenciesResolved()
            def setup_complex_logic(self):
                # 此时所有依赖都已经注入完成
                self.complex_state = self.dep1.initialize() + self.dep2.initialize()
    """

    def decorator(func: Callable) -> Callable:
        # 使用统一的元数据属性名 _decorator_metadata
        if not hasattr(func, "_decorator_metadata"):
            setattr(func, "_decorator_metadata", [])

        metadata = {
            "type": "lifecycle",
            "phase": LifecyclePhase.ON_DEPENDENCIES_RESOLVED,
            "condition": None,
            "priority": 0,
            "enabled": True,
        }
        getattr(func, "_decorator_metadata").append(metadata)

        # 保持向后兼容性：同时设置旧的 _lifecycle_metadata 属性
        if not hasattr(func, "_lifecycle_metadata"):
            setattr(func, "_lifecycle_metadata", [])

        getattr(func, "_lifecycle_metadata").append(
            {
                "phase": LifecyclePhase.ON_DEPENDENCIES_RESOLVED,
                "condition": None,
                "priority": 0,
            }
        )

        return func

    return decorator


# 便捷函数用于手动触发生命周期阶段
def trigger_lifecycle_phase(instance: Any, phase: LifecyclePhase, **kwargs):
    """
    手动触发生命周期阶段

    触发指定实例的特定生命周期阶段，执行该阶段的所有生命周期方法。
    每个方法只会执行一次，避免重复执行。

    Args:
        instance: 组件实例
        phase: 生命周期阶段（LifecyclePhase枚举值）
        **kwargs: 传递给生命周期方法的额外参数

    Returns:
        None

    Raises:
        无异常，方法执行失败会被静默处理

    Example:
        from LStartlet import trigger_lifecycle_phase, LifecyclePhase

        # 触发执行前阶段
        trigger_lifecycle_phase(my_instance, LifecyclePhase.PRE_EXECUTE)

        # 传递额外参数
        trigger_lifecycle_phase(my_instance, LifecyclePhase.POST_EXECUTE, result="success")

        # 在组件内部使用
        @Component
        class MyService:
            def execute_task(self):
                trigger_lifecycle_phase(self, LifecyclePhase.PRE_EXECUTE)
                print("执行任务")
                trigger_lifecycle_phase(self, LifecyclePhase.POST_EXECUTE)
    """
    cls = type(instance)

    # 获取要执行的方法
    methods = _lifecycle_manager.get_methods(cls, phase)

    # 初始化已执行方法集合
    if not hasattr(instance, "_executed_lifecycle_methods"):
        setattr(instance, "_executed_lifecycle_methods", set())

    executed_methods = getattr(instance, "_executed_lifecycle_methods")

    # 只执行未执行过的方法
    for method_wrapper in methods:
        method_key = (phase, method_wrapper.method.__name__)
        if method_key not in executed_methods:
            # 执行方法
            if not method_wrapper.enabled:
                continue

            # 检查条件
            if method_wrapper.condition is not None:
                try:
                    if not method_wrapper.condition(instance, **kwargs):
                        continue
                except Exception:
                    continue

            # 执行方法
            try:
                # 获取方法签名以确定参数
                sig = inspect.signature(method_wrapper.method)
                method_params = list(sig.parameters.keys())

                # 准备参数
                method_kwargs = {}
                if "self" in method_params:
                    method_params.remove("self")

                # 传递相关参数
                for param in method_params:
                    if param in kwargs:
                        method_kwargs[param] = kwargs[param]

                method_wrapper.method(instance, **method_kwargs)
                # 标记为已执行
                executed_methods.add(method_key)
            except Exception:
                pass


def trigger_all_lifecycle_phases(instance: Any, phases: List[LifecyclePhase], **kwargs):
    """
    手动触发多个生命周期阶段

    按顺序触发指定的多个生命周期阶段，每个阶段的所有方法都会被执行。
    常用于需要一次性执行多个阶段的场景。

    Args:
        instance: 组件实例
        phases: 生命周期阶段列表（LifecyclePhase枚举值列表）
        **kwargs: 传递给生命周期方法的额外参数

    Returns:
        None

    Raises:
        无异常，方法执行失败会被静默处理

    Example:
        from LStartlet import trigger_all_lifecycle_phases, LifecyclePhase

        # 触发所有初始化相关阶段
        trigger_all_lifecycle_phases(
            my_instance,
            [LifecyclePhase.PRE_INIT, LifecyclePhase.POST_INIT]
        )

        # 触发完整的启动流程
        trigger_all_lifecycle_phases(
            my_instance,
            [LifecyclePhase.PRE_START, LifecyclePhase.POST_START]
        )

        # 触发完整的停止流程
        trigger_all_lifecycle_phases(
            my_instance,
            [LifecyclePhase.PRE_STOP, LifecyclePhase.POST_STOP]
        )
    """
    for phase in phases:
        trigger_lifecycle_phase(instance, phase, **kwargs)


# 配置变更事件处理
@dataclass
class ConfigChangeEvent:
    """配置变更事件"""

    key: str
    old_value: Any
    new_value: Any


def notify_config_change(key: str, old_value: Any, new_value: Any):
    """通知配置变更"""
    event = ConfigChangeEvent(key, old_value, new_value)

    # 遍历所有注册了ON_CONFIG_CHANGE的类
    for cls, methods_dict in _lifecycle_manager._methods.items():
        if LifecyclePhase.ON_CONFIG_CHANGE in methods_dict:
            methods = methods_dict[LifecyclePhase.ON_CONFIG_CHANGE]
            for method_wrapper in methods:
                # 检查是否监听特定配置键
                config_key = getattr(method_wrapper.method, "_config_key", None)
                if config_key is None or config_key == key:
                    try:
                        # 创建实例（如果是单例，这里可能需要特殊处理）
                        # 简化处理：假设实例已经存在并通过其他方式管理
                        pass
                    except Exception:
                        pass


def register_lifecycle_methods_for_class(cls: Type):
    """为已注册的类注册生命周期方法"""
    # 检查是否已经注册过
    if cls in _lifecycle_manager._methods:
        return

    # 遍历类的所有方法，查找带有生命周期元数据的方法
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        # 优先使用新的统一元数据 _decorator_metadata
        metadata = getattr(method, "_decorator_metadata", None)
        if metadata:
            # 处理统一元数据格式
            for meta in metadata:
                if meta.get("type") == "lifecycle":
                    phase = meta["phase"]
                    condition = meta.get("condition")
                    priority = meta.get("priority", 0)
                    enabled = meta.get("enabled", True)

                    # 直接调用register_method，不要创建LifecycleMethod对象
                    _lifecycle_manager.register_method(
                        cls,
                        method,
                        phase,
                        condition=condition,
                        priority=priority,
                        enabled=enabled,
                    )

                    # 处理OnConfigChange特殊逻辑
                    if phase == LifecyclePhase.ON_CONFIG_CHANGE:
                        config_key = meta.get("config_key")
                        if config_key:
                            _setup_config_change_handler(cls, method, config_key)
        else:
            # 向后兼容：使用旧的 _lifecycle_metadata
            old_metadata = getattr(method, "_lifecycle_metadata", None)
            if old_metadata:
                # 处理两种格式：单个字典或字典列表，统一转换为列表处理
                if isinstance(old_metadata, dict):
                    metadata_list = [old_metadata]
                elif isinstance(old_metadata, list):
                    metadata_list = old_metadata
                else:
                    continue

                for meta in metadata_list:
                    phase = meta["phase"]
                    condition = meta.get("condition")
                    priority = meta.get("priority", 0)
                    enabled = meta.get("enabled", True)

                    # 直接调用register_method，不要创建LifecycleMethod对象
                    _lifecycle_manager.register_method(
                        cls,
                        method,
                        phase,
                        condition=condition,
                        priority=priority,
                        enabled=enabled,
                    )

                    # 处理OnConfigChange特殊逻辑
                    if phase == LifecyclePhase.ON_CONFIG_CHANGE:
                        config_key = getattr(method, "_config_key", None)
                        if config_key:
                            _setup_config_change_handler(cls, method, config_key)


def _get_class_instances(cls: Type) -> List[Any]:
    """获取指定类的所有活跃实例"""
    # 由于DI容器不维护实例列表，暂时返回空列表
    # 在实际使用中，用户需要自己管理实例或通过其他方式获取
    return []


def _setup_config_change_handler(cls: Type, method: Callable, config_key: str):
    """设置配置变更处理器"""
    # 延迟导入以避免循环依赖
    try:
        from ._event_decorator import subscribe_event, Event

        # 动态创建ConfigChangeEvent类，继承Event基类
        from dataclasses import dataclass
        from typing import Any

        @dataclass
        class ConfigChangeEvent(Event):
            """配置变更事件"""

            key: str
            old_value: Any
            new_value: Any

        def handle_config_change(event: ConfigChangeEvent):
            if event.key == config_key:
                # 获取所有该类的实例
                instances = _get_class_instances(cls)
                for instance in instances:
                    # 使用getattr安全获取元数据
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

        # 订阅配置变更事件
        subscribe_event(ConfigChangeEvent, handle_config_change)

    except (ImportError, AttributeError):
        # 如果无法设置事件处理器，静默失败
        pass


# 简化的四阶段生命周期装饰器
def Init(condition=None, priority=0, enabled=True):
    """
    简化的初始化阶段装饰器

    相当于 @PostInit，用于组件初始化完成后的逻辑处理
    推荐在一般场景下使用此装饰器进行初始化操作

    Args:
        condition: 条件函数，返回True时执行方法
        priority: 优先级，数值越小优先级越高（默认0）
        enabled: 是否启用此生命周期方法（默认True）

    Example:
        @Component
        class MyService:
            @Init()
            def initialize_service(self):
                # 初始化服务逻辑
                pass

            @Init(priority=1)  # 高优先级
            def setup_critical_resources(self):
                # 设置关键资源
                pass
    """
    return PostInit(condition=condition, priority=priority, enabled=enabled)


def Start(condition=None, priority=0, enabled=True):
    """
    简化的启动阶段装饰器

    相当于 @PostStart，用于组件启动完成后的逻辑处理
    推荐在一般场景下使用此装饰器进行启动操作

    Args:
        condition: 条件函数，返回True时执行方法
        priority: 优先级，数值越小优先级越高（默认0）
        enabled: 是否启用此生命周期方法（默认True）

    Example:
        @Component
        class MyService:
            @Start()
            def start_background_tasks(self):
                # 启动后台任务
                pass
    """
    return PostStart(condition=condition, priority=priority, enabled=enabled)


def Stop(condition=None, priority=0, enabled=True):
    """
    简化的停止阶段装饰器

    相当于 @PreStop，用于组件停止前的清理逻辑处理
    推荐在一般场景下使用此装饰器进行停止前的清理操作

    Args:
        condition: 条件函数，返回True时执行方法
        priority: 优先级，数值越小优先级越高（默认0）
        enabled: 是否启用此生命周期方法（默认True）

    Example:
        @Component
        class MyService:
            @Stop()
            def cleanup_resources(self):
                # 清理资源
                pass
    """
    return PreStop(condition=condition, priority=priority, enabled=enabled)


def Destroy(condition=None, priority=0, enabled=True):
    """
    简化的销毁阶段装饰器

    相当于 @PostDestroy，用于组件销毁完成后的最终清理
    推荐在一般场景下使用此装饰器进行最终的资源释放

    Args:
        condition: 条件函数，返回True时执行方法
        priority: 优先级，数值越小优先级越高（默认0）
        enabled: 是否启用此生命周期方法（默认True）

    Example:
        @Component
        class MyService:
            @Destroy()
            def release_final_resources(self):
                # 释放最终资源
                pass
    """
    return PostDestroy(condition=condition, priority=priority, enabled=enabled)


# 兼容性别名
Lifecycle = {
    "PreInit": PreInit,
    "PostInit": PostInit,
    "PreStart": PreStart,
    "PostStart": PostStart,
    "PreExecute": PreExecute,
    "PostExecute": PostExecute,
    "PreStop": PreStop,
    "PostStop": PostStop,
    "PreDestroy": PreDestroy,
    "PostDestroy": PostDestroy,
    "OnConfigChange": OnConfigChange,
    "OnDependenciesResolved": OnDependenciesResolved,
}
