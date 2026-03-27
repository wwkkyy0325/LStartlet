from typing import Callable, Type, Any, Optional
from .service_container import ServiceContainer, ServiceLifetime


class ContainerConfigurator:
    """容器配置器 - 用于批量注册服务"""

    def __init__(self, container: ServiceContainer):
        self._container = container

    def register_singleton(
        self,
        service_type: Type[Any],
        implementation_type: Optional[Type[Any]] = None,
        factory: Optional[Callable[["ServiceContainer"], Any]] = None,
        instance: Any = None,
    ) -> "ContainerConfigurator":
        """注册单例服务"""
        self._container.register(
            service_type,
            implementation_type,
            factory,
            instance,
            ServiceLifetime.SINGLETON,  # type: ignore
        )
        return self

    def register_transient(
        self,
        service_type: Type[Any],
        implementation_type: Optional[Type[Any]] = None,
        factory: Optional[Callable[["ServiceContainer"], Any]] = None,
    ) -> "ContainerConfigurator":
        """注册瞬态服务"""
        self._container.register(
            service_type,
            implementation_type,
            factory,
            None,
            ServiceLifetime.TRANSIENT,  # type: ignore
        )
        return self

    def register_scoped(
        self,
        service_type: Type[Any],
        implementation_type: Optional[Type[Any]] = None,
        factory: Optional[Callable[["ServiceContainer"], Any]] = None,
    ) -> "ContainerConfigurator":
        """注册作用域服务"""
        self._container.register(
            service_type,
            implementation_type,
            factory,
            None,
            ServiceLifetime.SCOPED,  # type: ignore
        )
        return self


def configure_default_container(
    configure_func: Callable[[ContainerConfigurator], None],
) -> ServiceContainer:
    """
    配置默认容器

    Args:
        configure_func: 配置函数

    Returns:
        配置后的容器
    """
    from .service_container import get_default_container

    container = get_default_container()
    configurator = ContainerConfigurator(container)
    configure_func(configurator)
    return container
