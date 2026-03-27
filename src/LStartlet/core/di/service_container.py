import inspect
from typing import Type, TypeVar, Dict, Any, Optional, List, Set, Callable
from threading import Lock

from .service_descriptor import ServiceDescriptor, ServiceLifetime
from .exceptions import ServiceResolutionError, ServiceRegistrationError

T = TypeVar("T")

# 全局默认服务容器
_default_container: Optional["ServiceContainer"] = None


def get_default_container() -> "ServiceContainer":
    """获取默认服务容器"""
    global _default_container
    if _default_container is None:
        _default_container = ServiceContainer()
    return _default_container


class ServiceContainer:
    """服务容器 - 实现依赖注入核心功能"""

    def __init__(self):
        self._services: Dict[Type[Any], ServiceDescriptor] = {}
        self._singleton_instances: Dict[Type[Any], Any] = {}
        self._lock = Lock()
        self._resolving_stack: Set[Type[Any]] = set()  # 用于检测循环依赖

    def register(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[["ServiceContainer"], T]] = None,
        instance: Optional[T] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> "ServiceContainer":
        """
        注册服务

        Args:
            service_type: 服务接口类型
            implementation_type: 实现类型
            factory: 工厂函数
            instance: 预创建的实例
            lifetime: 服务生命周期

        Returns:
            当前容器实例（支持链式调用）
        """
        try:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                instance=instance,
                lifetime=lifetime,
            )

            with self._lock:
                # 如果是单例且提供了实例，直接存储
                if lifetime == ServiceLifetime.SINGLETON and instance is not None:
                    self._singleton_instances[service_type] = instance

                self._services[service_type] = descriptor

            return self

        except ValueError as e:
            raise ServiceRegistrationError(service_type, str(e))

    def resolve(self, service_type: Type[T]) -> T:
        """
        解析服务实例

        Args:
            service_type: 要解析的服务类型

        Returns:
            服务实例
        """
        if service_type not in self._services:
            raise ServiceResolutionError(
                service_type, f"服务 {self._get_type_name(service_type)} 未注册"
            )

        descriptor = self._services[service_type]

        # 检查循环依赖
        if service_type in self._resolving_stack:
            cycle = (
                " -> ".join(self._get_type_name(t) for t in self._resolving_stack)
                + f" -> {self._get_type_name(service_type)}"
            )
            raise ServiceResolutionError(service_type, f"检测到循环依赖: {cycle}")

        try:
            self._resolving_stack.add(service_type)

            if descriptor.lifetime == ServiceLifetime.SINGLETON:  # type: ignore
                with self._lock:
                    if service_type in self._singleton_instances:
                        return self._singleton_instances[service_type]

                    instance = self._create_instance(descriptor)
                    self._singleton_instances[service_type] = instance
                    return instance  # type: ignore

            elif descriptor.lifetime == ServiceLifetime.SCOPED:  # type: ignore
                # 简化实现：Scoped 在这里等同于 Transient
                # 完整的 Scoped 实现需要作用域管理
                return self._create_instance(descriptor)  # type: ignore

            else:  # TRANSIENT
                return self._create_instance(descriptor)  # type: ignore

        finally:
            self._resolving_stack.discard(service_type)

    def _get_type_name(self, type_obj: Any) -> str:
        """获取类型名称，处理字符串类型注解"""
        if isinstance(type_obj, str):
            return type_obj
        elif hasattr(type_obj, "__name__"):
            name = getattr(type_obj, "__name__")
            if isinstance(name, str):
                return name
            else:
                return str(name)
        else:
            return str(type_obj)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例"""
        if descriptor.instance is not None:
            return descriptor.instance

        if descriptor.factory is not None:  # type: ignore
            return descriptor.factory(self)  # type: ignore

        # 使用构造函数注入
        implementation_type = descriptor.implementation_type
        constructor = implementation_type.__init__

        # 获取构造函数签名
        sig = inspect.signature(constructor)
        params = list(sig.parameters.values())[1:]  # 跳过 self 参数

        if not params:
            # 无参构造函数
            return implementation_type()

        # 解析依赖参数
        args: List[Any] = []
        kwargs = {}

        for param in params:
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                # *args 参数，跳过解析
                continue
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                # **kwargs 参数，跳过解析
                continue
            elif param.annotation != inspect.Parameter.empty:
                # 有类型注解，尝试解析
                annotation = param.annotation
                # 如果注解是字符串类型（forward reference），跳过解析
                if isinstance(annotation, str):
                    # 尝试从已注册的服务中查找匹配的类型
                    resolved_value = None
                    for registered_type in self._services.keys():
                        if self._get_type_name(registered_type) == annotation:
                            resolved_value = self.resolve(registered_type)
                            break

                    if resolved_value is not None:
                        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                            args.append(resolved_value)
                        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                            kwargs[param.name] = resolved_value
                    else:
                        # 如果无法解析且有默认值，使用默认值
                        if param.default != inspect.Parameter.empty:
                            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                                args.append(param.default)
                            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                                kwargs[param.name] = param.default
                        else:
                            raise ServiceResolutionError(
                                descriptor.service_type,
                                f"无法解析构造函数参数 {param.name}: {annotation} (字符串类型注解)",
                            )
                else:
                    # 正常的类型注解
                    try:
                        resolved_value = self.resolve(annotation)
                        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                            args.append(resolved_value)
                        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                            kwargs[param.name] = resolved_value
                    except ServiceResolutionError:
                        # 如果无法解析且有默认值，使用默认值
                        if param.default != inspect.Parameter.empty:
                            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                                args.append(param.default)
                            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                                kwargs[param.name] = param.default
                        else:
                            raise ServiceResolutionError(
                                descriptor.service_type,
                                f"无法解析构造函数参数 {param.name}: {self._get_type_name(annotation)}",
                            )
            else:
                # 无类型注解，检查是否有默认值
                if param.default != inspect.Parameter.empty:
                    if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        args.append(param.default)
                    elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                        kwargs[param.name] = param.default
                else:
                    raise ServiceResolutionError(
                        descriptor.service_type,
                        f"构造函数参数 {param.name} 缺少类型注解且无默认值",
                    )

        return implementation_type(*args, **kwargs)

    def has_service(self, service_type: Type[Any]) -> bool:
        """检查是否注册了指定服务"""
        return service_type in self._services

    def reset(self) -> None:
        """重置容器（主要用于测试）"""
        with self._lock:
            self._services.clear()
            self._singleton_instances.clear()
