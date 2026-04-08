"""
极简依赖注入装饰器 - 实现基于@Component和@Plugin的依赖注入
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


@dataclass
class ServiceRegistration:
    """服务注册信息"""

    service_type: Type
    implementation: Any
    is_singleton: bool = True
    instance: Any = None
    # 存储该服务的所有实例（包括单例和瞬态）
    instances: List[Any] = field(default_factory=list)


class SimpleDIContainer:
    """简单的依赖注入容器"""

    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._components: Dict[str, Type] = {}  # 组件类型映射
        self._plugins: Dict[str, Type] = {}  # 插件类型映射

        # 实例管理：使用弱引用集合自动跟踪所有实例
        self._all_instances: WeakSet[Any] = WeakSet()

        # 错误处理：存储生命周期错误
        self._lifecycle_errors: List[Dict[str, Any]] = []

        # 错误处理回调函数列表
        self._error_handlers: List[Callable[[Exception, str, Any], None]] = []

        # 存储所有已创建的瞬态实例，用于生命周期管理（可选）
        self._transient_instances: List[Any] = []

    def register_service(
        self, service_type: Type, implementation: Any = None, singleton: bool = True
    ):
        """注册服务"""
        if implementation is None:
            implementation = service_type

        self._services[service_type] = ServiceRegistration(
            service_type=service_type,
            implementation=implementation,
            is_singleton=singleton,
        )

    def register_component(
        self, name: str, component_type: Type, singleton: bool = True
    ):
        """注册组件"""
        self._components[name] = component_type
        # 自动注册组件类型为服务
        self.register_service(component_type, component_type, singleton=singleton)

    def register_plugin(self, name: str, plugin_type: Type, singleton: bool = True):
        """注册插件"""
        self._plugins[name] = plugin_type
        # 自动注册插件类型为服务
        self.register_service(plugin_type, plugin_type, singleton=singleton)

    def register_error_handler(self, handler: Callable[[Exception, str, Any], None]):
        """
        注册错误处理回调函数

        Args:
            handler: 错误处理函数，接收参数 (exception, phase, instance)
        """
        self._error_handlers.append(handler)

    def unregister_error_handler(self, handler: Callable[[Exception, str, Any], None]):
        """
        取消注册错误处理回调函数

        Args:
            handler: 要取消注册的错误处理函数
        """
        if handler in self._error_handlers:
            self._error_handlers.remove(handler)

    def _handle_lifecycle_error(self, exception: Exception, phase: str, instance: Any):
        """
        处理生命周期错误

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
                print(f"错误处理器执行失败: {e}")

        # 打印错误信息
        print(f"生命周期错误 [{phase}] - {type(instance).__name__}: {exception}")
        print(f"堆栈跟踪:\n{error_info['traceback']}")

    def get_all_instances(self) -> List[Any]:
        """
        获取所有跟踪的实例

        Returns:
            所有实例的列表
        """
        return list(self._all_instances)

    def get_instances_by_type(self, service_type: Type) -> List[Any]:
        """
        获取指定类型的所有实例

        Args:
            service_type: 服务类型

        Returns:
            该类型的所有实例列表
        """
        return [inst for inst in self._all_instances if isinstance(inst, service_type)]

    def get_lifecycle_errors(self) -> List[Dict[str, Any]]:
        """
        获取所有生命周期错误

        Returns:
            错误信息列表
        """
        return self._lifecycle_errors.copy()

    def clear_lifecycle_errors(self):
        """清除所有生命周期错误"""
        self._lifecycle_errors.clear()

    def get_instance_count(self) -> int:
        """
        获取当前跟踪的实例总数

        Returns:
            实例总数
        """
        return len(self._all_instances)

    def get_instance_count_by_type(self, service_type: Type) -> int:
        """
        获取指定类型的实例数量

        Args:
            service_type: 服务类型

        Returns:
            该类型的实例数量
        """
        return len(self.get_instances_by_type(service_type))

    def resolve(self, service_type: Type):
        """解析服务实例"""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type} not registered")

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

    def resolve_transient(self, service_type: Type):
        """
        解析瞬态服务实例

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
        """创建类实例，自动注入依赖"""
        # 移除强制组件检查，改为可选警告
        if not hasattr(cls, "_component_metadata"):
            # 发出警告但不阻止实例化（保持向后兼容性）
            print(
                f"警告: 类 {cls.__name__} 未被 @Component 或 @Plugin 标记，但仍可使用 @Inject 进行依赖注入"
            )

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
            from ._lifecycle_decorator import trigger_lifecycle_phase, LifecyclePhase

            trigger_lifecycle_phase(instance, LifecyclePhase.ON_DEPENDENCIES_RESOLVED)
        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

        # 自动触发完整的初始化生命周期序列
        self._trigger_init_lifecycle(instance)

        return instance

    def _inject_properties(self, cls: Type, instance: Any):
        """处理属性注入和方法注入"""
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
                try:
                    type_hints = get_type_hints(cls)
                    if attr_name in type_hints:
                        service_type = (
                            inject_marker.service_type or type_hints[attr_name]
                        )
                    else:
                        continue
                except Exception:
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
                    print(f"警告: 无法注入属性 {cls.__name__}.{attr_name}: {e}")

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
                                print(
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
        """按名称解析依赖"""
        # 在组件中查找
        if name in self._components:
            component_type = self._components[name]
            if service_type is None or issubclass(component_type, service_type):
                return self.resolve(component_type)

        # 在插件中查找
        if name in self._plugins:
            plugin_type = self._plugins[name]
            if service_type is None or issubclass(plugin_type, service_type):
                return self.resolve(plugin_type)

        raise ValueError(f"Named dependency '{name}' not found")

    def _resolve_all(self, service_type: Type) -> List[Any]:
        """解析所有匹配的服务"""
        instances = []

        # 遍历所有注册的服务
        for registered_type, registration in self._services.items():
            if issubclass(registered_type, service_type):
                instances.append(self.resolve(registered_type))

        return instances

    def _register_lifecycle_methods(self, cls: Type, instance: Any):
        """注册生命周期方法到生命周期管理器"""
        try:
            from ._lifecycle_decorator import get_lifecycle_manager

            lifecycle_manager = get_lifecycle_manager()

            # 遍历类的所有方法，查找带有生命周期元数据的方法
            for attr_name in dir(cls):
                attr = getattr(cls, attr_name)
                if callable(attr):
                    # 优先使用新的统一元数据 _decorator_metadata
                    metadata_list = getattr(attr, "_decorator_metadata", None)
                    if metadata_list:
                        for metadata in metadata_list:
                            if metadata.get("type") == "lifecycle":
                                lifecycle_manager.register_method(
                                    cls,
                                    attr,
                                    metadata["phase"],
                                    metadata.get("condition"),
                                    metadata.get("priority", 0),
                                )
                    else:
                        # 向后兼容：使用旧的 _lifecycle_metadata
                        old_metadata = getattr(attr, "_lifecycle_metadata", None)
                        if old_metadata:
                            for metadata in old_metadata:
                                lifecycle_manager.register_method(
                                    cls,
                                    attr,
                                    metadata["phase"],
                                    metadata["condition"],
                                    metadata["priority"],
                                )
        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

    def _register_event_handlers(self, cls: Type, instance: Any):
        """注册事件处理器到事件总线"""
        try:
            from ._event_decorator import get_event_bus

            event_bus = get_event_bus()

            # 遍历类的所有方法，查找带有事件元数据的方法
            for attr_name in dir(cls):
                attr = getattr(cls, attr_name)
                if callable(attr):
                    # 获取绑定到实例的方法
                    bound_method = getattr(instance, attr_name)

                    # 优先使用新的统一元数据 _decorator_metadata
                    metadata_list = getattr(attr, "_decorator_metadata", None)
                    if metadata_list:
                        for metadata in metadata_list:
                            if metadata.get("type") == "event":
                                event_type = metadata["event_type"]
                                condition = metadata.get("condition")
                                topic = metadata.get("topic")
                                handler_type = metadata.get("handler_type")

                                if handler_type == "multi":
                                    event_bus.subscribe(
                                        event_type, bound_method, condition, topic
                                    )
                                elif handler_type == "single":
                                    event_bus.subscribe_single(
                                        event_type, bound_method, condition, topic
                                    )
                                elif handler_type == "interceptor":
                                    event_bus.register_interceptor(
                                        event_type, bound_method
                                    )
                    else:
                        # 向后兼容：使用旧的 _event_metadata
                        old_metadata = getattr(attr, "_event_metadata", None)
                        if old_metadata:
                            for metadata in old_metadata:
                                event_type = metadata["event_type"]
                                condition = metadata.get("condition")
                                topic = metadata.get("topic")
                                handler_type = metadata["handler_type"]

                                if handler_type == "multi":
                                    event_bus.subscribe(
                                        event_type, bound_method, condition, topic
                                    )
                                elif handler_type == "single":
                                    event_bus.subscribe_single(
                                        event_type, bound_method, condition, topic
                                    )
                                elif handler_type == "interceptor":
                                    event_bus.register_interceptor(
                                        event_type, bound_method
                                    )
        except ImportError:
            # 如果事件模块未导入，跳过处理
            pass

    def _trigger_init_lifecycle(self, instance: Any):
        """自动触发完整的初始化生命周期序列（PreInit -> POST_INIT）"""
        try:
            from ._lifecycle_decorator import trigger_lifecycle_phase, LifecyclePhase

            # 按顺序触发初始化阶段
            # 1. 先触发 PRE_INIT 阶段（如果定义了）
            trigger_lifecycle_phase(instance, LifecyclePhase.PRE_INIT)

            # 2. 再触发 POST_INIT 阶段（@Init 装饰器）
            trigger_lifecycle_phase(instance, LifecyclePhase.POST_INIT)
        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

    def start_components(self):
        """启动所有已创建的单例组件，触发完整的启动生命周期序列（PRE_START -> POST_START）"""
        try:
            from ._lifecycle_decorator import trigger_lifecycle_phase, LifecyclePhase

            # 触发所有单例组件的启动生命周期
            for registration in self._services.values():
                if registration.is_singleton and registration.instance is not None:
                    instance = registration.instance
                    try:
                        # 按顺序触发启动阶段
                        # 1. 先触发 PRE_START 阶段（如果定义了）
                        trigger_lifecycle_phase(instance, LifecyclePhase.PRE_START)

                        # 2. 再触发 POST_START 阶段（@Start 装饰器）
                        trigger_lifecycle_phase(instance, LifecyclePhase.POST_START)
                    except Exception as e:
                        # 捕获并记录启动错误，但继续启动其他组件
                        self._handle_lifecycle_error(e, "START_COMPONENTS", instance)

        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

    def stop_components(self):
        """停止所有已创建的单例组件，触发完整的停止和销毁生命周期序列"""
        try:
            from ._lifecycle_decorator import trigger_lifecycle_phase, LifecyclePhase

            # 触发所有单例组件的停止和销毁生命周期
            for registration in self._services.values():
                if registration.is_singleton and registration.instance is not None:
                    instance = registration.instance
                    try:
                        # 按顺序触发停止和销毁阶段
                        # 1. 先触发 PRE_STOP 阶段（@Stop 装饰器）
                        trigger_lifecycle_phase(instance, LifecyclePhase.PRE_STOP)

                        # 2. 再触发 POST_STOP 阶段（如果定义了）
                        trigger_lifecycle_phase(instance, LifecyclePhase.POST_STOP)

                        # 3. 再触发 PRE_DESTROY 阶段（如果定义了）
                        trigger_lifecycle_phase(instance, LifecyclePhase.PRE_DESTROY)

                        # 4. 最后触发 POST_DESTROY 阶段（@Destroy 装饰器）
                        trigger_lifecycle_phase(instance, LifecyclePhase.POST_DESTROY)
                    except Exception as e:
                        # 捕获并记录停止错误，但继续停止其他组件
                        self._handle_lifecycle_error(e, "STOP_COMPONENTS", instance)

        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass

    def start_transient_instance(self, instance: Any):
        """启动瞬态实例，触发完整的启动生命周期序列（PRE_START -> POST_START）"""
        try:
            from ._lifecycle_decorator import trigger_lifecycle_phase, LifecyclePhase

            # 按顺序触发启动阶段
            # 1. 先触发 PRE_START 阶段（如果定义了）
            trigger_lifecycle_phase(instance, LifecyclePhase.PRE_START)

            # 2. 再触发 POST_START 阶段（@Start 装饰器）
            trigger_lifecycle_phase(instance, LifecyclePhase.POST_START)
        except Exception as e:
            # 捕获并记录启动错误
            self._handle_lifecycle_error(e, "START_TRANSIENT", instance)
            raise

    def stop_transient_instance(self, instance: Any):
        """停止瞬态实例，触发完整的停止和销毁生命周期序列"""
        try:
            from ._lifecycle_decorator import trigger_lifecycle_phase, LifecyclePhase

            # 按顺序触发停止和销毁阶段
            # 1. 先触发 PRE_STOP 阶段（@Stop 装饰器）
            trigger_lifecycle_phase(instance, LifecyclePhase.PRE_STOP)

            # 2. 再触发 POST_STOP 阶段（如果定义了）
            trigger_lifecycle_phase(instance, LifecyclePhase.POST_STOP)

            # 3. 再触发 PRE_DESTROY 阶段（如果定义了）
            trigger_lifecycle_phase(instance, LifecyclePhase.PRE_DESTROY)

            # 4. 最后触发 POST_DESTROY 阶段（@Destroy 装饰器）
            trigger_lifecycle_phase(instance, LifecyclePhase.POST_DESTROY)
        except Exception as e:
            # 捕获并记录停止错误
            self._handle_lifecycle_error(e, "STOP_TRANSIENT", instance)
            raise


# 全局唯一的DI容器实例
_di_container = SimpleDIContainer()


class _InjectMarker:
    """注入标记类 - 用于标记需要注入的参数"""

    def __init__(self, service_type: Optional[Type] = None):
        self.service_type = service_type


class _InjectPropertyMarker(_InjectMarker):
    """属性注入标记类 - 用于标记需要注入的属性"""

    def __init__(self, service_type: Optional[Type] = None, lazy: bool = False):
        super().__init__(service_type)
        self.lazy = lazy


class _InjectMethodMarker(_InjectMarker):
    """方法注入标记类 - 用于标记需要注入的方法"""

    def __init__(self):
        super().__init__(None)


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


def Inject(service_type: Optional[Type] = None):
    """
    依赖注入装饰器 - 用于标记需要注入的属性或参数

    注意：只有被@Component或@Plugin标记的类才能使用此装饰器进行依赖注入

    Args:
        service_type: 可选的服务类型，如果为None则从类型注解推断

    Example:
        @Component("my_service")
        class MyService:
            pass

        @Component("my_controller")
        class MyController:
            def __init__(self, my_service: MyService = Inject()):
                self.my_service = my_service
    """
    # 使用cast让类型检查器认为返回的是正确类型
    # 实际运行时返回_InjectMarker，但在DI容器解析时会被替换
    return cast(Any, _InjectMarker(service_type))


def InjectProperty(service_type: Optional[Type] = None, lazy: bool = False):
    """
    属性注入装饰器 - 用于标记需要注入的属性

    Args:
        service_type: 可选的服务类型，如果为None则从类型注解推断
        lazy: 是否延迟注入，True表示在第一次访问时才注入

    Example:
        @Component("my_service")
        class MyService:
            pass

        @Component("my_controller")
        class MyController:
            @InjectProperty()
            my_service: MyService

            @InjectProperty(lazy=True)
            lazy_service: MyService
    """
    return cast(Any, _InjectPropertyMarker(service_type, lazy))


def OptionalInject(service_type: Optional[Type] = None):
    """
    可选依赖注入装饰器 - 用于标记可选的依赖

    如果依赖不存在，则注入None而不是抛出异常

    Args:
        service_type: 可选的服务类型，如果为None则从类型注解推断

    Example:
        @Component("my_controller")
        class MyController:
            def __init__(self, optional_service: Optional[MyService] = OptionalInject()):
                self.optional_service = optional_service
    """
    return cast(Any, _OptionalInjectMarker(service_type))


def InjectNamed(name: str, service_type: Optional[Type] = None):
    """
    命名依赖注入装饰器 - 用于按名称注入依赖

    Args:
        name: 组件或插件的名称
        service_type: 可选的服务类型，如果为None则从类型注解推断

    Example:
        @Component("primary_db")
        class PrimaryDatabase:
            pass

        @Component("secondary_db")
        class SecondaryDatabase:
            pass

        @Component("my_controller")
        class MyController:
            def __init__(self, primary_db: Database = InjectNamed("primary_db")):
                self.primary_db = primary_db
    """
    return cast(Any, _InjectNamedMarker(name, service_type))


def InjectAll(service_type: Optional[Type] = None):
    """
    集合注入装饰器 - 用于注入同一类型的所有实现

    Args:
        service_type: 可选的服务类型，如果为None则从类型注解推断

    Example:
        @Component("handler1")
        class Handler1:
            pass

        @Component("handler2")
        class Handler2:
            pass

        @Component("my_controller")
        class MyController:
            def __init__(self, handlers: List[Handler] = InjectAll()):
                self.handlers = handlers
    """
    return cast(Any, _InjectAllMarker(service_type))


def InjectMethod(func: Optional[Callable] = None, **inject_kwargs):
    """
    方法注入装饰器 - 用于标记需要注入的方法

    Args:
        func: 要装饰的方法
        **inject_kwargs: 注入参数映射，格式为 {参数名: 服务类型}

    Example:
        @Component("my_service")
        class MyService:
            pass

        @Component("my_controller")
        class MyController:
            @InjectMethod(service=MyService)
            def process(self, service):
                service.do_something()
    """

    def decorator(f: Callable) -> Callable:
        f._inject_method_marker = _InjectMethodMarker()  # type: ignore
        f._inject_kwargs = inject_kwargs  # type: ignore
        return f

    if func is not None:
        return decorator(func)
    return decorator


def get_di_container() -> SimpleDIContainer:
    """
    获取全局DI容器实例

    返回框架的全局依赖注入容器，用于管理所有组件和服务的生命周期。
    通常情况下，用户不需要直接调用此函数，而是使用便捷函数。

    Returns:
        SimpleDIContainer: 全局DI容器实例

    Example:
        from LStartlet import get_di_container

        container = get_di_container()
        service = container.resolve(MyService)
    """
    return _di_container


def resolve_service(service_type: Type):
    """
    解析服务实例

    从DI容器中获取指定类型的服务实例。
    如果服务是单例，返回已存在的实例或创建新实例。
    如果服务是瞬态，总是创建新实例。

    Args:
        service_type: 服务类型（类对象）

    Returns:
        服务实例对象

    Raises:
        ValueError: 服务未注册时抛出

    Example:
        from LStartlet import resolve_service, Component

        @Component
        class MyService:
            pass

        # 解析服务
        service = resolve_service(MyService)
        print(f"服务实例: {service}")
    """
    return _di_container.resolve(service_type)


# 兼容性函数
inject = Inject


# 添加便捷函数用于框架级别的生命周期管理
def start_framework():
    """
    启动框架，触发所有组件的启动生命周期

    启动所有已创建的单例组件，触发完整的启动生命周期序列：
    1. PRE_START 阶段 - 启动前的准备工作
    2. POST_START 阶段 - 启动后的初始化工作

    此函数应该在所有组件创建完成后调用。

    Returns:
        None

    Example:
        from LStartlet import start_framework, stop_framework, Component

        @Component
        class MyService:
            @PostStart()
            def on_start(self):
                print("服务启动")

        # 启动框架
        start_framework()
        print("框架已启动")

        # 停止框架
        stop_framework()
    """
    _di_container.start_components()


def stop_framework():
    """
    停止框架，触发所有组件的停止和销毁生命周期

    停止所有已创建的单例组件，触发完整的停止和销毁生命周期序列：
    1. PRE_STOP 阶段 - 停止前的准备工作
    2. POST_STOP 阶段 - 停止后的清理工作
    3. PRE_DESTROY 阶段 - 销毁前的准备工作
    4. POST_DESTROY 阶段 - 销毁后的资源释放

    此函数应该在应用程序退出前调用。

    Returns:
        None

    Example:
        from LStartlet import start_framework, stop_framework, Component

        @Component
        class MyService:
            @PreStop()
            def on_stop(self):
                print("服务停止")

            @PostDestroy()
            def on_destroy(self):
                print("服务销毁")

        # 启动框架
        start_framework()

        # 停止框架
        stop_framework()
        print("框架已停止")
    """
    _di_container.stop_components()


# 添加瞬态实例解析和生命周期管理函数
def resolve_transient(service_type: Type):
    """
    解析瞬态服务实例

    创建指定类型的新实例，即使服务注册为单例也会创建新实例。
    如果服务未注册，则尝试直接实例化该类型。
    瞬态实例需要手动管理生命周期。

    Args:
        service_type: 服务类型（类对象）

    Returns:
        新创建的服务实例对象

    Raises:
        Exception: 实例化失败时抛出

    Example:
        from LStartlet import resolve_transient, start_transient_instance, stop_transient_instance, Component

        @Component(scope='transient')
        class TransientService:
            @PostStart()
            def on_start(self):
                print("瞬态服务启动")

        # 创建瞬态实例
        instance1 = resolve_transient(TransientService)
        instance2 = resolve_transient(TransientService)

        # 手动启动实例
        start_transient_instance(instance1)
        start_transient_instance(instance2)

        # 手动停止实例
        stop_transient_instance(instance1)
        stop_transient_instance(instance2)
    """
    return _di_container.resolve_transient(service_type)


def start_transient_instance(instance: Any):
    """
    启动瞬态实例，触发启动生命周期阶段

    手动启动瞬态实例，触发完整的启动生命周期序列：
    1. PRE_START 阶段 - 启动前的准备工作
    2. POST_START 阶段 - 启动后的初始化工作

    此函数必须在使用瞬态实例前调用。

    Args:
        instance: 瞬态实例对象

    Returns:
        None

    Raises:
        Exception: 启动失败时抛出

    Example:
        from LStartlet import resolve_transient, start_transient_instance, Component

        @Component(scope='transient')
        class TransientService:
            @PostStart()
            def on_start(self):
                print("瞬态服务启动")

        # 创建并启动瞬态实例
        instance = resolve_transient(TransientService)
        start_transient_instance(instance)
    """
    _di_container.start_transient_instance(instance)


def stop_transient_instance(instance: Any):
    """
    停止瞬态实例，触发停止和销毁生命周期阶段

    手动停止瞬态实例，触发完整的停止和销毁生命周期序列：
    1. PRE_STOP 阶段 - 停止前的准备工作
    2. POST_STOP 阶段 - 停止后的清理工作
    3. PRE_DESTROY 阶段 - 销毁前的准备工作
    4. POST_DESTROY 阶段 - 销毁后的资源释放

    此函数应该在使用完瞬态实例后调用，以释放资源。

    Args:
        instance: 瞬态实例对象

    Returns:
        None

    Raises:
        Exception: 停止失败时抛出

    Example:
        from LStartlet import resolve_transient, start_transient_instance, stop_transient_instance, Component

        @Component(scope='transient')
        class TransientService:
            @PreStop()
            def on_stop(self):
                print("瞬态服务停止")

        # 创建、启动、使用、停止瞬态实例
        instance = resolve_transient(TransientService)
        start_transient_instance(instance)
        # 使用实例...
        stop_transient_instance(instance)
    """
    _di_container.stop_transient_instance(instance)


# 实例管理相关函数
def register_error_handler(handler: Callable[[Exception, str, Any], None]):
    """
    注册错误处理回调函数

    注册一个错误处理函数，当生命周期方法执行失败时会被调用。
    可以注册多个错误处理函数，它们会按注册顺序依次执行。

    Args:
        handler: 错误处理函数，接收参数 (exception, phase, instance)
                 - exception: 异常对象
                 - phase: 生命周期阶段名称
                 - instance: 发生错误的实例对象

    Returns:
        None

    Example:
        from LStartlet import register_error_handler, Component, PostStart

        def my_error_handler(exception, phase, instance):
            print(f"错误发生: {phase} - {type(instance).__name__}")
            print(f"异常: {exception}")

        # 注册错误处理器
        register_error_handler(my_error_handler)

        @Component
        class MyService:
            @PostStart()
            def on_start(self):
                raise Exception("启动失败")
    """
    _di_container.register_error_handler(handler)


def unregister_error_handler(handler: Callable[[Exception, str, Any], None]):
    """
    取消注册错误处理回调函数

    从错误处理器列表中移除指定的错误处理函数。

    Args:
        handler: 要取消注册的错误处理函数

    Returns:
        None

    Example:
        from LStartlet import register_error_handler, unregister_error_handler

        def my_error_handler(exception, phase, instance):
            print(f"错误: {exception}")

        # 注册错误处理器
        register_error_handler(my_error_handler)

        # 取消注册错误处理器
        unregister_error_handler(my_error_handler)
    """
    _di_container.unregister_error_handler(handler)


def get_all_instances() -> List[Any]:
    """
    获取所有跟踪的实例

    返回DI容器中所有已创建的实例列表，包括单例和瞬态实例。
    使用弱引用跟踪，已销毁的实例不会出现在列表中。

    Returns:
        List[Any]: 所有实例的列表

    Example:
        from LStartlet import get_all_instances, Component

        @Component
        class MyService:
            pass

        # 获取所有实例
        instances = get_all_instances()
        print(f"实例数量: {len(instances)}")
        for instance in instances:
            print(f"  - {type(instance).__name__}")
    """
    return _di_container.get_all_instances()


def get_instances_by_type(service_type: Type) -> List[Any]:
    """
    获取指定类型的所有实例

    返回DI容器中所有指定类型的实例列表。
    使用弱引用跟踪，已销毁的实例不会出现在列表中。

    Args:
        service_type: 服务类型（类对象）

    Returns:
        List[Any]: 该类型的所有实例列表

    Example:
        from LStartlet import get_instances_by_type, Component

        @Component
        class MyService:
            pass

        # 获取指定类型的所有实例
        instances = get_instances_by_type(MyService)
        print(f"MyService实例数量: {len(instances)}")
        for instance in instances:
            print(f"  - {instance}")
    """
    return _di_container.get_instances_by_type(service_type)


def get_lifecycle_errors() -> List[Dict[str, Any]]:
    """
    获取所有生命周期错误

    返回所有生命周期方法执行过程中发生的错误列表。
    每个错误信息包含：异常对象、阶段名称、实例对象、实例类型、堆栈跟踪等。

    Returns:
        List[Dict[str, Any]]: 错误信息列表，每个元素是一个字典，包含：
            - exception: 异常对象
            - phase: 生命周期阶段名称
            - instance: 实例对象
            - instance_type: 实例类型名称
            - traceback: 堆栈跟踪信息

    Example:
        from LStartlet import get_lifecycle_errors, clear_lifecycle_errors, Component, PostStart

        @Component
        class MyService:
            @PostStart()
            def on_start(self):
                raise Exception("启动失败")

        # 检查错误
        errors = get_lifecycle_errors()
        if errors:
            print(f"发现 {len(errors)} 个错误")
            for error in errors:
                print(f"阶段: {error['phase']}")
                print(f"异常: {error['exception']}")
                print(f"堆栈: {error['traceback']}")

            # 清除错误
            clear_lifecycle_errors()
    """
    return _di_container.get_lifecycle_errors()


def clear_lifecycle_errors():
    """
    清除所有生命周期错误

    清空错误列表，通常在处理完错误后调用。

    Returns:
        None

    Example:
        from LStartlet import get_lifecycle_errors, clear_lifecycle_errors

        # 检查并处理错误
        errors = get_lifecycle_errors()
        if errors:
            for error in errors:
                print(f"错误: {error['exception']}")

            # 清除错误
            clear_lifecycle_errors()
    """
    _di_container.clear_lifecycle_errors()


def get_instance_count() -> int:
    """
    获取当前跟踪的实例总数

    返回DI容器中当前跟踪的实例总数，包括单例和瞬态实例。
    使用弱引用跟踪，已销毁的实例不会被计数。

    Returns:
        int: 实例总数

    Example:
        from LStartlet import get_instance_count, Component

        @Component
        class MyService:
            pass

        # 获取实例总数
        count = get_instance_count()
        print(f"实例总数: {count}")

    """
    return _di_container.get_instance_count()


def get_instance_count_by_type(service_type: Type) -> int:
    """
    获取指定类型的实例数量

    返回DI容器中指定类型的实例数量。
    使用弱引用跟踪，已销毁的实例不会被计数。

    Args:
        service_type: 服务类型（类对象）

    Returns:
        int: 该类型的实例数量

    Example:
        from LStartlet import get_instance_count_by_type, Component

        @Component
        class MyService:
            pass

        # 获取指定类型的实例数量
        count = get_instance_count_by_type(MyService)
        print(f"MyService实例数量: {count}")
    """
    return _di_container.get_instance_count_by_type(service_type)
