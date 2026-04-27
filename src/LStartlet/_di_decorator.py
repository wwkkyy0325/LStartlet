"""
极简依赖注入装饰器
支持多种注入方式：构造函数注入、属性注入、方法注入等
"""

import inspect
import traceback
import types
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
    get_type_hints,
)
from dataclasses import dataclass, field
from functools import wraps
from weakref import WeakSet

# 导入框架日志函数
from ._logging import (
    _log_framework_debug,
    _log_framework_info,
    _log_framework_warning,
    _log_framework_error,
)


@dataclass
class _ServiceRegistration:
    """服务注册信息（内部类）"""

    service_type: Type
    implementation: Any
    is_singleton: bool = True
    instance: Any = None
    # 存储该服务的所有实例（包括单例和瞬态）
    instances: List[Any] = field(default_factory=list)


class _SimpleDIContainer:
    """简单的依赖注入容器（内部类）"""

    def __init__(self):
        self._services: Dict[Type, _ServiceRegistration] = {}
        self._components: Dict[str, Type] = {}  # 组件类型映射

        # 实例管理：使用弱引用集合自动跟踪所有实例
        self._all_instances: WeakSet[Any] = WeakSet()

        # 错误处理：存储生命周期错误
        self._lifecycle_errors: List[Dict[str, Any]] = []

        # 错误处理回调函数列表
        self._error_handlers: List[Callable[[Exception, str, Any], None]] = []

        # 存储所有已创建的瞬态实例，用于生命周期管理（可选）
        self._transient_instances: List[Any] = []

    def _register_service(
        self, service_type: Type, implementation: Any = None, singleton: bool = True
    ):
        """注册服务（内部方法）"""
        if implementation is None:
            implementation = service_type

        self._services[service_type] = _ServiceRegistration(
            service_type=service_type,
            implementation=implementation,
            is_singleton=singleton,
        )

    def register_service(
        self, service_type: Type, implementation: Any = None, singleton: bool = True
    ):
        """
        注册服务（公共API，供框架使用）

        Args:
            service_type: 服务类型
            implementation: 实现类型（如果为None则使用service_type）
            singleton: 是否为单例（默认True）
        """
        self._register_service(service_type, implementation, singleton)

    def _register_component(
        self, name: str, component_type: Type, singleton: bool = True
    ):
        """注册组件（内部方法）"""
        self._components[name] = component_type
        # 自动注册组件类型为服务
        self._register_service(component_type, component_type, singleton=singleton)

    def _register_error_handler(self, handler: Callable[[Exception, str, Any], None]):
        """
        注册错误处理回调函数（内部方法）

        Args:
            handler: 错误处理函数，接收参数 (exception, phase, instance)
        """
        self._error_handlers.append(handler)

    def _unregister_error_handler(self, handler: Callable[[Exception, str, Any], None]):
        """
        取消注册错误处理回调函数（内部方法）

        Args:
            handler: 要取消注册的错误处理函数
        """
        if handler in self._error_handlers:
            self._error_handlers.remove(handler)

    def _handle_lifecycle_error(self, exception: Exception, phase: str, instance: Any):
        """
        处理生命周期错误（内部方法）

        Args:
            exception: 异常对象
            phase: 生命周期阶段
            instance: 实例对象
        """
        # 记录错误
        error_info = {
            "exception": exception,
            "phase": phase,
            "instance": instance,
            "instance_type": type(instance).__name__,
            "traceback": traceback.format_exc(),
        }
        self._lifecycle_errors.append(error_info)

        # 调用所有注册的错误处理器
        for handler in self._error_handlers:
            try:
                handler(exception, phase, instance)
            except Exception as e:
                # 避免错误处理器本身抛出异常
                _log_framework_error(f"错误处理器执行失败: {e}")

        # 打印错误信息
        _log_framework_error(
            f"生命周期错误 [{phase}] - {type(instance).__name__}: {exception}"
        )
        _log_framework_error(f"堆栈跟踪:\n{error_info['traceback']}")

    def _get_all_instances(self) -> List[Any]:
        """
        获取所有跟踪的实例（内部方法）

        Returns:
            所有实例的列表
        """
        return list(self._all_instances)

    def _get_instances_by_type(self, service_type: Type) -> List[Any]:
        """
        获取指定类型的所有实例（内部方法）

        Args:
            service_type: 服务类型

        Returns:
            该类型的所有实例列表
        """
        return [inst for inst in self._all_instances if isinstance(inst, service_type)]

    def _get_lifecycle_errors(self) -> List[Dict[str, Any]]:
        """
        获取所有生命周期错误（内部方法）

        Returns:
            错误信息列表
        """
        return self._lifecycle_errors.copy()

    def _clear_lifecycle_errors(self):
        """清除所有生命周期错误（内部方法）"""
        self._lifecycle_errors.clear()

    def _get_instance_count(self) -> int:
        """
        获取当前跟踪的实例总数（内部方法）

        Returns:
            实例总数
        """
        return len(self._all_instances)

    def _get_instance_count_by_type(self, service_type: Type) -> int:
        """
        获取指定类型的实例数量（内部方法）

        Args:
            service_type: 服务类型

        Returns:
            该类型的实例数量
        """
        return len(self._get_instances_by_type(service_type))

    def _resolve(self, service_type: Type):
        """内部解析服务实例（框架内部使用）"""
        if service_type not in self._services:
            self._register_service(service_type, service_type, singleton=True)

        registration = self._services[service_type]

        if registration.is_singleton and registration.instance is not None:
            return registration.instance

        # 创建新实例
        try:
            instance = self._create_instance(registration.implementation)
        except Exception as e:
            self._handle_lifecycle_error(
                e, "CREATE_INSTANCE", registration.implementation
            )
            raise

        if registration.is_singleton:
            registration.instance = instance
        else:
            # 对于瞬态实例，可以选择是否跟踪它们用于生命周期管理
            # 这里我们选择不自动跟踪，因为瞬态实例通常由用户手动管理
            pass

        # 添加到实例跟踪
        registration.instances.append(instance)
        self._all_instances.add(instance)

        return instance

    def resolve(self, service_type: Type):
        """解析服务实例，自动注册未注册的服务"""
        return self._resolve(service_type)

    def _resolve_transient(self, service_type: Type):
        """
        解析瞬态服务实例（内部方法）

        即使服务注册为单例，此方法也会创建新的实例
        如果服务未注册，则尝试直接实例化该类型
        """
        try:
            if service_type in self._services:
                registration = self._services[service_type]
                # 忽略单例设置，总是创建新实例
                instance = self._create_instance(registration.implementation)

                # 添加到实例跟踪
                registration.instances.append(instance)
            else:
                # 服务未注册，尝试直接实例化
                instance = self._create_instance(service_type)

            # 添加到全局实例跟踪
            self._all_instances.add(instance)

            return instance
        except Exception as e:
            self._handle_lifecycle_error(e, "RESOLVE_TRANSIENT", service_type)
            raise

    def _create_instance(self, cls: Type):
        """创建类实例，自动注入依赖（内部方法）"""
        # 获取构造函数签名
        try:
            sig = inspect.signature(cls.__init__)
            type_hints = get_type_hints(cls.__init__)
        except (ValueError, AttributeError):
            # 如果无法获取签名，直接实例化
            instance = cls()
            # 处理属性注入
            self._inject_properties(cls, instance)
            # 处理生命周期元数据
            self._register_lifecycle_methods(cls, instance)
            # 自动触发完整的初始化生命周期序列
            self._trigger_init_lifecycle(instance)
            return instance

        # 准备依赖参数
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # 跳过没有类型注解的参数
            if param_name not in type_hints:
                continue

            param_type = type_hints[param_name]

            # 检查默认值是否为各种特定的Inject标记（从具体到一般）
            if isinstance(param.default, _InjectAllMarker):  # 最具体
                # 集合注入
                inject_all_marker = param.default
                service_type = inject_all_marker.service_type or param_type

                # 解析所有匹配的服务
                try:
                    dependencies = self._resolve_all(service_type)
                    kwargs[param_name] = dependencies
                except ValueError as e:
                    raise ValueError(
                        f"Cannot resolve all dependencies {service_type} for {cls.__name__}.{param_name}"
                    ) from e
            elif isinstance(param.default, _OptionalInjectMarker):  # 次具体
                # 可选依赖注入
                optional_inject_marker = param.default
                service_type = optional_inject_marker.service_type or param_type

                # 检查是否是 typing.Any 类型，如果是则直接返回 None
                # 避免尝试解析 typing.Any 导致不必要的错误记录
                if service_type is Any:
                    kwargs[param_name] = None  # type: ignore[assignment]
                else:
                    # 尝试解析依赖，失败时返回None
                    try:
                        dependency = self.resolve(service_type)
                        kwargs[param_name] = dependency
                    except ValueError:
                        kwargs[param_name] = None  # type: ignore[assignment]
            elif isinstance(param.default, _InjectNamedMarker):  # 次具体
                # 命名依赖注入
                named_inject_marker = param.default
                service_type = named_inject_marker.service_type or param_type

                # 按名称解析依赖
                try:
                    dependency = self._resolve_named(
                        named_inject_marker.name, service_type
                    )
                    kwargs[param_name] = dependency
                except ValueError as e:
                    raise ValueError(
                        f"Cannot resolve named dependency {named_inject_marker.name} for {cls.__name__}.{param_name}"
                    ) from e
            elif isinstance(param.default, _InjectMarker):  # 最一般
                inject_marker = param.default
                # 使用标记中指定的类型或从类型注解推断
                service_type = inject_marker.service_type or param_type

                # 解析依赖
                try:
                    dependency = self.resolve(service_type)
                    kwargs[param_name] = dependency
                except ValueError as e:
                    raise ValueError(
                        f"Cannot resolve dependency {service_type} for {cls.__name__}.{param_name}"
                    ) from e

        # 创建实例
        instance = cls(**kwargs)

        # 处理属性注入
        self._inject_properties(cls, instance)

        # 处理生命周期元数据
        self._register_lifecycle_methods(cls, instance)

        # 处理事件处理器元数据
        self._register_event_handlers(cls, instance)

        # 触发依赖注入完成事件
        try:
            from ._lifecycle_decorator import _trigger_lifecycle_phase, _LifecyclePhase

            _trigger_lifecycle_phase(instance, _LifecyclePhase.ON_DEPENDENCIES_RESOLVED)
        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

        # 自动触发完整的初始化生命周期序列
        self._trigger_init_lifecycle(instance)

        return instance

    def _inject_properties(self, cls: Type, instance: Any):
        """处理属性注入和方法注入（内部方法）"""
        # 缓存类型注解，避免重复调用 get_type_hints
        type_hints = {}
        try:
            type_hints = get_type_hints(cls)
        except Exception:
            pass

        # 遍历类的所有属性
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue  # 跳过私有属性

            # 获取属性描述符
            attr = getattr(cls, attr_name, None)

            # 检查是否为属性注入标记
            if isinstance(attr, _InjectPropertyMarker):
                inject_marker = attr

                # 获取类型注解
                if attr_name in type_hints:
                    service_type = inject_marker.service_type or type_hints[attr_name]
                    _log_framework_info(f"类型注解: {attr_name} -> {service_type}")
                else:
                    _log_framework_warning(f"属性 {attr_name} 没有类型注解")
                    continue

                # 解析依赖
                try:
                    if inject_marker.lazy:
                        # 延迟注入：创建一个属性描述符，在第一次访问时才注入
                        def lazy_getter(service_type):
                            def getter(self):
                                if not hasattr(self, f"_{attr_name}_cached"):
                                    setattr(
                                        self,
                                        f"_{attr_name}_cached",
                                        self.resolve(service_type),
                                    )
                                return getattr(self, f"_{attr_name}_cached")

                            return property(getter)

                        setattr(cls, attr_name, lazy_getter(service_type))
                    else:
                        # 立即注入
                        dependency = self.resolve(service_type)
                        setattr(instance, attr_name, dependency)
                except ValueError as e:
                    _log_framework_warning(
                        f"警告: 无法注入属性 {cls.__name__}.{attr_name}: {e}"
                    )

        # 处理实例属性注入（处理在 __init__ 中使用 inject() 的情况）
        for attr_name in dir(instance):
            if attr_name.startswith("__") and attr_name.endswith("__"):
                continue  # 跳过特殊方法

            # 获取实例属性
            attr = getattr(instance, attr_name, None)

            # 检查是否为属性注入标记
            if isinstance(attr, _InjectPropertyMarker):
                inject_marker = attr

                # 优先使用标记对象中的服务类型
                service_type = inject_marker.service_type

                # 如果标记对象中没有指定服务类型，则从类型注解中获取
                if service_type is None:
                    if attr_name in type_hints:
                        service_type = type_hints[attr_name]
                    else:
                        _log_framework_warning(
                            f"实例属性 {attr_name} 没有类型注解且标记对象中未指定服务类型"
                        )
                        continue

                # 解析依赖
                try:
                    if inject_marker.lazy:
                        # 延迟注入：创建一个属性描述符，在第一次访问时才注入
                        def lazy_getter(service_type):
                            def getter(self):
                                if not hasattr(self, f"_{attr_name}_cached"):
                                    setattr(
                                        self,
                                        f"_{attr_name}_cached",
                                        self.resolve(service_type),
                                    )
                                return getattr(self, f"_{attr_name}_cached")

                            return property(getter)

                        setattr(cls, attr_name, lazy_getter(service_type))
                    else:
                        # 立即注入
                        dependency = self.resolve(service_type)
                        setattr(instance, attr_name, dependency)
                        _log_framework_info(
                            f"成功注入实例属性 {cls.__name__}.{attr_name}: {dependency}"
                        )
                except ValueError as e:
                    _log_framework_warning(
                        f"警告: 无法注入实例属性 {cls.__name__}.{attr_name}: {e}"
                    )

        # 处理方法注入
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue

            attr = getattr(cls, attr_name)

            # 检查是否为方法注入标记
            if hasattr(attr, "_inject_method_marker"):
                inject_kwargs = getattr(attr, "_inject_kwargs", {})

                # 获取原始方法
                original_method = attr

                # 创建包装器
                def make_wrapper(original_func, inject_params, method_name):
                    @wraps(original_func)
                    def wrapper(self, *args, **kwargs):
                        # 解析注入的依赖
                        injected_kwargs = {}
                        for param_name, service_type in inject_params.items():
                            try:
                                injected_kwargs[param_name] = self.resolve(service_type)
                            except ValueError as e:
                                _log_framework_warning(
                                    f"警告: 无法注入方法参数 {cls.__name__}.{method_name}.{param_name}: {e}"
                                )

                        # 合并注入的参数和用户提供的参数
                        all_kwargs = {**injected_kwargs, **kwargs}
                        return original_func(self, *args, **all_kwargs)

                    return wrapper

                # 创建包装方法
                wrapped_method = make_wrapper(original_method, inject_kwargs, attr_name)

                # 替换实例方法
                setattr(instance, attr_name, types.MethodType(wrapped_method, instance))

    def _resolve_named(self, name: str, service_type: Optional[Type] = None):
        """按名称解析依赖（内部方法）"""
        # 在组件中查找
        if name in self._components:
            component_type = self._components[name]
            if service_type is None or issubclass(component_type, service_type):
                return self._resolve(component_type)
        raise ValueError(f"Named dependency '{name}' not found")

    def _resolve_all(self, service_type: Type) -> List[Any]:
        """解析所有匹配的服务（内部方法，性能优化）"""
        instances = []

        # 使用列表推导式提高性能
        for registered_type in self._services.keys():
            if issubclass(registered_type, service_type):
                instances.append(self._resolve(registered_type))

        return instances

    def _register_lifecycle_methods(self, cls: Type, instance: Any):
        """注册生命周期方法到生命周期管理器（内部方法，性能优化）"""
        try:
            from ._lifecycle_decorator import _get_lifecycle_manager

            lifecycle_manager = _get_lifecycle_manager()

            # 遍历类的所有方法，查找带有生命周期元数据的方法
            for attr_name in dir(cls):
                if attr_name.startswith("_"):
                    continue  # 跳过私有方法

                attr = getattr(cls, attr_name)
                if callable(attr):
                    # 使用统一元数据 _decorator_metadata
                    metadata_list = getattr(attr, "_decorator_metadata", None)
                    if metadata_list:
                        for metadata in metadata_list:
                            if metadata.get("type") == "lifecycle":
                                lifecycle_manager._register_method(
                                    cls,
                                    attr,
                                    metadata["phase"],
                                    metadata.get("condition"),
                                    metadata.get("priority", 0),
                                    metadata.get("enabled", True),
                                )
        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

    def _register_event_handlers(self, cls: Type, instance: Any):
        """注册事件处理器到事件总线（内部方法，性能优化）"""
        try:
            from ._event_decorator import _get_event_bus

            event_bus = _get_event_bus()

            # 遍历类的所有方法，查找带有事件元数据的方法
            for attr_name in dir(cls):
                if attr_name.startswith("_"):
                    continue  # 跳过私有方法

                attr = getattr(cls, attr_name)
                if callable(attr):
                    # 获取绑定到实例的方法
                    bound_method = getattr(instance, attr_name)

                    # 使用统一元数据 _decorator_metadata
                    metadata_list = getattr(attr, "_decorator_metadata", None)
                    if metadata_list:
                        for metadata in metadata_list:
                            if metadata.get("type") == "event":
                                event_type = metadata["event_type"]
                                condition = metadata.get("condition")

                                # 使用统一的subscribe方法
                                event_bus._subscribe(
                                    event_type, bound_method, condition
                                )
        except ImportError:
            # 如果事件模块未导入，跳过处理
            pass

    def _trigger_init_lifecycle(self, instance: Any):
        """自动触发完整的初始化生命周期序列（POST_INIT）（内部方法）"""
        try:
            from ._lifecycle_decorator import _trigger_lifecycle_phase, _LifecyclePhase

            # 触发初始化阶段
            _trigger_lifecycle_phase(instance, _LifecyclePhase.POST_INIT)
        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

    def _start_components(self):
        """启动所有已创建的单例组件，触发完整的启动生命周期序列（POST_START）（内部方法）"""
        try:
            from ._lifecycle_decorator import _trigger_lifecycle_phase, _LifecyclePhase

            # 先创建所有已注册但未创建的单例实例
            _log_framework_info(
                f"开始创建服务实例，已注册服务: {[service_type.__name__ for service_type in self._services.keys()]}"
            )
            for service_type in list(self._services.keys()):
                registration = self._services[service_type]
                if registration.is_singleton and registration.instance is None:
                    try:
                        # 创建实例（会自动触发 @Init() 装饰器）
                        instance = self._create_instance(registration.implementation)
                        registration.instance = instance
                        _log_framework_info(f"已创建服务实例: {service_type.__name__}")
                    except Exception as e:
                        self._handle_lifecycle_error(e, "CREATE_INSTANCE", service_type)
                elif registration.is_singleton and registration.instance is not None:
                    _log_framework_info(
                        f"服务 {service_type.__name__} 已有实例，跳过创建"
                    )

            # 触发所有单例组件的启动生命周期
            for registration in self._services.values():
                if registration.is_singleton and registration.instance is not None:
                    instance = registration.instance
                    try:
                        # 触发启动阶段
                        _trigger_lifecycle_phase(instance, _LifecyclePhase.POST_START)
                    except Exception as e:
                        # 捕获并记录启动错误，但继续启动其他组件
                        self._handle_lifecycle_error(e, "START_COMPONENTS", instance)

        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

    def start_components(self):
        """
        启动所有已创建的单例组件（公共API，供框架使用）

        触发完整的启动生命周期序列（POST_START）
        """
        self._start_components()

    def _stop_components(self):
        """停止所有已创建的单例组件，触发完整的停止和销毁生命周期序列（内部方法）"""
        try:
            from ._lifecycle_decorator import _trigger_lifecycle_phase, _LifecyclePhase

            # 触发所有单例组件的停止和销毁生命周期
            for registration in self._services.values():
                if registration.is_singleton and registration.instance is not None:
                    instance = registration.instance
                    try:
                        # 按顺序触发停止和销毁阶段
                        # 1. 先触发 POST_STOP 阶段（@Stop 装饰器）
                        _trigger_lifecycle_phase(instance, _LifecyclePhase.POST_STOP)

                        # 2. 最后触发 POST_DESTROY 阶段（@Destroy 装饰器）
                        _trigger_lifecycle_phase(instance, _LifecyclePhase.POST_DESTROY)
                    except Exception as e:
                        # 捕获并记录停止错误，但继续停止其他组件
                        self._handle_lifecycle_error(e, "STOP_COMPONENTS", instance)

        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

    def stop_components(self):
        """
        停止所有已创建的单例组件（公共API，供框架使用）

        触发完整的停止和销毁生命周期序列
        """
        self._stop_components()

    def _start_transient_instance(self, instance: Any):
        """启动瞬态实例，触发完整的启动生命周期序列（POST_START）（内部方法）"""
        try:
            from ._lifecycle_decorator import _trigger_lifecycle_phase, _LifecyclePhase

            # 先注册生命周期方法（如果还没有注册过）
            cls = type(instance)
            self._register_lifecycle_methods(cls, instance)

            # 先触发初始化阶段（如果还没有触发过）
            _trigger_lifecycle_phase(instance, _LifecyclePhase.POST_INIT)

            # 然后触发启动阶段
            _trigger_lifecycle_phase(instance, _LifecyclePhase.POST_START)
        except Exception as e:
            # 捕获并记录启动错误
            self._handle_lifecycle_error(e, "START_TRANSIENT", instance)
            raise

    def start_transient_instance(self, instance: Any):
        """
        启动瞬态实例（公共API，供框架使用）

        触发完整的启动生命周期序列（POST_START）

        Args:
            instance: 瞬态实例对象
        """
        self._start_transient_instance(instance)

    def _stop_transient_instance(self, instance: Any):
        """停止瞬态实例，触发完整的停止和销毁生命周期序列（内部方法）"""
        try:
            from ._lifecycle_decorator import _trigger_lifecycle_phase, _LifecyclePhase

            # 按顺序触发停止和销毁阶段
            # 1. 先触发 POST_STOP 阶段（@Stop 装饰器）
            _trigger_lifecycle_phase(instance, _LifecyclePhase.POST_STOP)

            # 2. 最后触发 POST_DESTROY 阶段（@Destroy 装饰器）
            _trigger_lifecycle_phase(instance, _LifecyclePhase.POST_DESTROY)
        except Exception as e:
            # 捕获并记录停止错误
            self._handle_lifecycle_error(e, "STOP_TRANSIENT", instance)
            raise

    def stop_transient_instance(self, instance: Any):
        """
        停止瞬态实例（公共API，供框架使用）

        触发完整的停止和销毁生命周期序列

        Args:
            instance: 瞬态实例对象
        """
        self._stop_transient_instance(instance)


# 全局唯一的DI容器实例
_di_container = _SimpleDIContainer()


# ============================================================================
# 高级自动化装饰器 - 替代手动调用
# ============================================================================


class _ServiceMarker:
    """服务标记类 - 用于标记需要自动注册的服务"""

    def __init__(self, singleton: bool = True, auto_start: bool = False):
        self.singleton = singleton
        self.auto_start = auto_start


def Service(singleton: bool = True, auto_start: bool = False):
    """
    服务装饰器 - 自动注册服务并管理生命周期

    Args:
        singleton: 是否为单例服务（默认 True）
        auto_start: 是否在框架启动时自动启动（默认 False）

    Returns:
        装饰后的服务类

    Example:
        @Service(singleton=True, auto_start=True)
        class DatabaseService:
            def __init__(self):
                self.connected = False

            @Start()
            def connect(self):
                self.connected = True

    Note:
        - 使用此装饰器标记的服务会自动注册到DI容器
        - 单例服务在整个应用中只有一个实例
        - auto_start=True 的服务会在框架启动时自动调用 @Start 装饰的方法
        - 支持依赖注入，其他服务可以通过 inject() 注入此服务
    """

    def decorator(cls):
        cls._is_service = True
        cls._service_singleton = singleton
        cls._service_auto_start = auto_start

        di_container = _get_di_container()
        di_container.register_service(cls, cls, singleton=singleton)

        _log_framework_info(
            f"已注册服务: {cls.__name__} (单例: {singleton}, 自动启动: {auto_start})"
        )

        return cls

    return decorator


class _InjectMarker:
    """注入标记类 - 用于标记需要注入的参数"""

    def __init__(self, service_type: Optional[Type] = None):
        self.service_type = service_type


class _InjectPropertyMarker(_InjectMarker):
    """属性注入标记类 - 用于标记需要注入的属性"""

    def __init__(self, service_type: Optional[Type] = None, lazy: bool = False):
        super().__init__(service_type)
        self.lazy = lazy


class _OptionalInjectMarker(_InjectMarker):
    """可选依赖注入标记类 - 用于标记可选的依赖"""

    def __init__(self, service_type: Optional[Type] = None):
        super().__init__(service_type)


class _InjectNamedMarker(_InjectMarker):
    """命名依赖注入标记类 - 用于按名称注入依赖"""

    def __init__(self, name: str, service_type: Optional[Type] = None):
        super().__init__(service_type)
        self.name = name


class _InjectAllMarker(_InjectMarker):
    """集合注入标记类 - 用于注入同一类型的所有实现"""

    def __init__(self, service_type: Optional[Type] = None):
        super().__init__(service_type)


def inject(service_type: Optional[Type] = None):
    """
    依赖注入函数 - 标记需要注入的属性或参数

    Args:
        service_type: 可选的服务类型，如果为None则从类型注解推断

    Returns:
        注入标记对象，在DI容器解析时会被替换为实际服务实例

    Example:
        class MyService:
            pass

        class MyController:
            def __init__(self):
                self.my_service: MyService = inject(MyService)
                self.another_service: MyService = inject()

    Note:
        - 这是一个函数，不是装饰器，使用时需要调用
        - 支持类型注解自动推断服务类型
        - 在框架启动时自动解析依赖
    """
    return cast(Any, _InjectPropertyMarker(service_type, lazy=False))


def _inject_property(service_type: Optional[Type] = None, lazy: bool = False):
    """属性注入函数（内部方法）"""
    return cast(Any, _InjectPropertyMarker(service_type, lazy))


def _optional_inject(service_type: Optional[Type] = None):
    """可选依赖注入函数（内部方法）"""
    return cast(Any, _OptionalInjectMarker(service_type))


def _inject_named(name: str, service_type: Optional[Type] = None):
    """命名依赖注入函数（内部方法）"""
    return cast(Any, _InjectNamedMarker(name, service_type))


def _inject_all(service_type: Optional[Type] = None):
    """集合注入函数（内部方法）"""
    return cast(Any, _InjectAllMarker(service_type))


def _get_di_container() -> _SimpleDIContainer:
    """获取全局DI容器实例（内部方法）"""
    return _di_container


def _resolve_service(service_type: Type):
    """解析服务实例（内部函数）"""
    return _di_container.resolve(service_type)


def resolve_service(service_type: Type):
    """
    解析服务实例 - 从DI容器中获取服务实例

    Args:
        service_type: 服务类型

    Returns:
        服务实例

    Example:
        from LStartlet import resolve_service, Service

        @Service(singleton=True)
        class MyService:
            def do_something(self):
                return "Hello"

        # 获取服务实例
        service = resolve_service(MyService)
        result = service.do_something()

    Note:
        - 如果服务是单例，则返回同一个实例
        - 如果服务不是单例，则每次调用都创建新实例
        - 如果服务未注册，则自动注册并创建实例
    """
    return _di_container.resolve(service_type)


def _start_framework():
    """启动框架，触发所有组件的启动生命周期（内部函数）"""
    from ._logging import _configure_logging

    _configure_logging()

    from ._application_info import (
        _check_all_applications,
        _print_check_report,
        _check_circular_dependencies,
        _print_circular_dependencies,
        _list_applications,
        _save_check_report,
    )

    registered_apps = _list_applications()
    if not registered_apps:
        _log_framework_error("框架启动失败：未注册应用程序信息")
        raise RuntimeError(
            "框架启动失败：使用 LStartlet 框架必须注册应用程序信息。"
            "请使用 @ApplicationInfo 装饰器定义应用程序信息类。"
            "例如：\n"
            "  from LStartlet import ApplicationInfo\n"
            "  \n"
            "  @ApplicationInfo\n"
            "  class MyAppInfo:\n"
            "      def get_directory_name(self) -> str:\n"
            '          return "my_app"\n'
            "      \n"
            "      def get_display_name(self) -> str:\n"
            '          return "我的应用"\n'
            "  \n"
            "  # 装饰器会自动注册，不需要手动调用"
        )

    _log_framework_info("正在检查框架健康状态...")
    report = _check_all_applications()

    cycles = _check_circular_dependencies()
    if cycles:
        _log_framework_error("框架启动失败：发现循环依赖")
        _print_circular_dependencies()
        raise RuntimeError(f"框架启动失败：发现 {len(cycles)} 个循环依赖")

    if report.unhealthy_apps > 0:
        _log_framework_error("框架启动失败：存在不健康的应用程序")
        _print_check_report(report)
        raise RuntimeError(f"框架启动失败：{report.unhealthy_apps} 个应用程序不健康")

    from ._application_info import _save_check_report

    report_path = _save_check_report(report)
    _log_framework_info(f"框架健康检查报告已保存到: {report_path}")
    _log_framework_info("框架健康检查通过")

    _di_container.start_components()


def _activate_framework(
    app_info_class: Optional[type] = None,
    services: Optional[List[type]] = None,
    auto_register: bool = True,
) -> None:
    """激活框架 - 统一的框架启动入口（内部函数）"""
    if app_info_class is not None:
        from ._application_info import ApplicationInfo
        from typing import cast

        if not hasattr(app_info_class, "_is_application_info"):
            application_info_instance = ApplicationInfo(app_info_class)
        else:
            application_info_instance = cast(ApplicationInfo, app_info_class)

        metadata = application_info_instance._get_metadata()
        app_name = metadata.display_name or metadata.directory_name

        _log_framework_info(f"已激活应用程序: {app_name} v{metadata.version}")

    if services is not None:
        di_container = _get_di_container()

        for service_class in services:
            di_container.register_service(service_class, service_class, singleton=True)
            _log_framework_info(f"已注册服务: {service_class.__name__}")

    _start_framework()

    _log_framework_info("框架已完全激活")


def _stop_framework():
    """停止框架，触发所有组件的停止和销毁生命周期（内部函数）"""
    _di_container.stop_components()


def _resolve_transient(service_type: Type):
    """解析瞬态服务实例（内部函数）"""
    return _di_container._resolve_transient(service_type)


def _start_transient_instance(instance: Any):
    """启动瞬态实例（内部函数）"""
    _di_container.start_transient_instance(instance)


def _stop_transient_instance(instance: Any):
    """停止瞬态实例（内部函数）"""
    _di_container.stop_transient_instance(instance)


def _register_error_handler(handler: Callable[[Exception, str, Any], None]):
    """注册错误处理回调函数（内部函数）"""
    _di_container._register_error_handler(handler)


def _unregister_error_handler(handler: Callable[[Exception, str, Any], None]):
    """取消注册错误处理回调函数（内部函数）"""
    _di_container._unregister_error_handler(handler)


def _get_all_instances() -> List[Any]:
    """获取所有跟踪的实例（内部函数）"""
    return _di_container._get_all_instances()


def _get_instances_by_type(service_type: Type) -> List[Any]:
    """获取指定类型的所有实例（内部函数）"""
    return _di_container._get_instances_by_type(service_type)


def _get_lifecycle_errors() -> List[Dict[str, Any]]:
    """获取所有生命周期错误（内部函数）"""
    return _di_container._get_lifecycle_errors()


def _clear_lifecycle_errors():
    """清除所有生命周期错误（内部函数）"""
    _di_container._clear_lifecycle_errors()


def _get_instance_count() -> int:
    """获取当前跟踪的实例总数（内部函数）"""
    return _di_container._get_instance_count()


def _get_instance_count_by_type(service_type: Type) -> int:
    """获取指定类型的实例数量（内部函数）"""
    return _di_container._get_instance_count_by_type(service_type)
