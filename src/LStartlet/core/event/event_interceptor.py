"""事件拦截器接口
提供事件处理链中的拦截和修改功能
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable
from .base_event import BaseEvent

# 定义拦截器函数类型
InterceptorFunc = Callable[[BaseEvent], Optional[BaseEvent]]


class EventInterceptor(ABC):
    """
    事件拦截器抽象基类
    在事件分发前进行拦截、修改或取消操作
    """

    def __init__(self, name: str = ""):
        self._name = name or self.__class__.__name__
        self._enabled = True

    @property
    def name(self) -> str:
        """获取拦截器名称"""
        return self._name

    @property
    def enabled(self) -> bool:
        """检查拦截器是否启用"""
        return self._enabled

    def enable(self) -> None:
        """启用拦截器"""
        self._enabled = True

    def disable(self) -> None:
        """禁用拦截器"""
        self._enabled = False

    @abstractmethod
    def intercept(self, event: BaseEvent) -> Optional[BaseEvent]:
        """
        拦截事件

        Args:
            event: 要拦截的事件

        Returns:
            Optional[BaseEvent]: 返回修改后的事件，如果返回None则取消事件分发
        """
        pass


class LambdaEventInterceptor(EventInterceptor):
    """
    Lambda事件拦截器
    允许使用函数作为事件拦截器
    """

    def __init__(self, interceptor_func: InterceptorFunc, name: str = ""):
        super().__init__(name)
        self._interceptor_func = interceptor_func

    def intercept(self, event: BaseEvent) -> Optional[BaseEvent]:
        """拦截事件"""
        if not self.enabled:
            return event
        return self._interceptor_func(event)
