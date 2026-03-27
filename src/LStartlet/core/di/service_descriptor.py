from __future__ import annotations
from enum import Enum
from typing import Type, TypeVar, Callable, Optional

T = TypeVar("T")


class ServiceLifetime(Enum):
    """服务生命周期"""

    TRANSIENT = "transient"  # 每次请求都创建新实例
    SCOPED = "scoped"  # 在作用域内单例
    SINGLETON = "singleton"  # 全局单例


class ServiceDescriptor:
    """服务描述符"""

    def __init__(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[["ServiceContainer"], T]] = None,  # type: ignore[name-defined]  # noqa: F821
        instance: Optional[T] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ):
        """
        初始化服务描述符

        Args:
            service_type: 服务接口类型
            implementation_type: 实现类型（如果与服务类型不同）
            factory: 工厂函数
            instance: 预创建的实例（用于单例）
            lifetime: 服务生命周期
        """
        if not service_type:
            raise ValueError("service_type cannot be None")

        self.service_type = service_type
        self.implementation_type = implementation_type or service_type
        self.factory = factory  # type: ignore
        self.instance = instance
        self.lifetime = lifetime

        # 验证参数组合
        provided_values = sum([factory is not None, instance is not None])

        if provided_values > 1:
            raise ValueError("只能指定 factory 或 instance 中的一个")

        # 对于单例，如果提供了实例，则使用该实例
        # 如果没有提供实例或工厂，则使用 implementation_type 创建实例
        # 这是合理的，因为很多情况下 service_type == implementation_type
