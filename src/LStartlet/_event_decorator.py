"""
极简事件监听装饰器 - 实现唯一的事件总线
支持命名空间隔离，类似于配置管理和日志系统
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Type, Optional
from dataclasses import dataclass

from ._logging import (
    _log_framework_warning,
    _log_framework_error,
    _log_framework_debug,
)


# 从 _application_info 导入统一的 _get_current_app_name 函数
_get_current_app_name = None


def _ensure_get_current_app_name():
    """确保 _get_current_app_name 函数已导入"""
    global _get_current_app_name
    if _get_current_app_name is None:
        from ._application_info import _get_current_app_name as _get_app_name

        _get_current_app_name = _get_app_name


class Event:
    """
    基础事件类 - 所有自定义事件必须继承此类

    Example:
        @dataclass
        class MyEvent(Event):
            message: str

        @dataclass
        class UserLoginEvent(Event):
            username: str
            login_time: float

    Note:
        - 事件子类需要使用 @dataclass 装饰器自动生成 __init__ 方法
        - 事件字段可以是任意类型
        - 发布事件时使用 publish_event() 函数
        - 订阅事件时使用 subscribe_event() 函数
    """

    pass


@dataclass
class _EventHandler:
    """事件处理器包装器（内部类）"""

    func: Callable
    condition: Optional[Callable] = None


class _EventBusManager:
    """事件总线管理器（内部类）"""

    def __init__(self):
        self._buses: Dict[str, "_EventBus"] = {}
        self._framework_bus: Optional["_EventBus"] = None

    def _get_bus(self) -> "_EventBus":
        """获取当前应用的事件总线（内部方法）"""
        _ensure_get_current_app_name()

        namespace = "lstartlet"
        if _get_current_app_name is not None:
            app_name = _get_current_app_name()
            if app_name is not None:
                namespace = app_name

        if namespace == "lstartlet":
            if self._framework_bus is None:
                self._framework_bus = _EventBus()
            return self._framework_bus

        if namespace not in self._buses:
            self._buses[namespace] = _EventBus()
        return self._buses[namespace]

    def _clear_namespace(self, namespace: str):
        """清除指定命名空间的事件总线（内部方法）"""
        if namespace in self._buses:
            del self._buses[namespace]

    def _clear_all(self):
        """清除所有命名空间的事件总线（内部方法）"""
        self._buses.clear()
        self._framework_bus = None


class _EventBus:
    """事件总线实现（内部类）"""

    def __init__(self):
        self._handlers: Dict[Type[Event], List[_EventHandler]] = {}
        self._async_handlers: Dict[Callable, bool] = {}
        self._filters: List[Dict] = []

    def _register_filter(
        self,
        filter_func: Callable[[Event], bool],
        event_type: Optional[Type[Event]] = None,
        namespace: Optional[str] = None,
        priority: int = 0,
    ):
        """注册事件过滤器（内部方法）"""
        filter_info = {
            "func": filter_func,
            "event_type": event_type,
            "namespace": namespace,
            "priority": priority,
        }
        self._filters.append(filter_info)
        self._filters.sort(key=lambda x: -x["priority"])

    def _unregister_filter(self, filter_func: Callable[[Event], bool]):
        """取消注册事件过滤器（内部方法）"""
        self._filters = [f for f in self._filters if f["func"] is not filter_func]

    def _should_propagate(self, event: Event) -> bool:
        """检查事件是否应该传播（内部方法）"""
        for filter_info in self._filters:
            filter_func = filter_info["func"]
            filter_event_type = filter_info["event_type"]
            filter_namespace = filter_info["namespace"]

            if filter_event_type is not None and not isinstance(
                event, filter_event_type
            ):
                continue

            if filter_namespace is not None:
                _ensure_get_current_app_name()
                current_namespace = "lstartlet"
                if _get_current_app_name is not None:
                    app_name = _get_current_app_name()
                    if app_name is not None:
                        current_namespace = app_name
                if current_namespace != filter_namespace:
                    continue

            try:
                if not filter_func(event):
                    return False
            except Exception as e:
                _log_framework_warning(f"事件过滤器执行失败: {e}")
                return False
        return True

    def _subscribe(
        self,
        event_type: Type[Event],
        handler: Callable,
        condition: Optional[Callable] = None,
    ):
        """订阅事件（内部方法）"""
        is_async = asyncio.iscoroutinefunction(handler)
        self._async_handlers[handler] = is_async

        wrapper = _EventHandler(handler, condition)
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        for existing_wrapper in self._handlers[event_type]:
            if (
                existing_wrapper.func is handler
                and existing_wrapper.condition == condition
            ):
                return

        self._handlers[event_type].append(wrapper)

    def _unsubscribe(
        self,
        event_type: Type[Event],
        handler: Callable,
    ):
        """取消订阅事件（内部方法）"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h.func is not handler
            ]
            if handler in self._async_handlers:
                del self._async_handlers[handler]

    def _should_handle(self, handler: _EventHandler, event: Event) -> bool:
        """检查处理器是否应该处理该事件（内部方法）"""
        if handler.condition is not None:
            try:
                if not handler.condition(event):
                    return False
            except Exception as e:
                _log_framework_warning(f"事件条件过滤器执行失败: {e}")
                return False

        return True

    def _publish(self, event: Event):
        """发布事件（内部方法）"""
        event_type = type(event)

        if not self._should_propagate(event):
            _log_framework_debug(f"事件被过滤器阻止: {event_type.__name__}")
            return

        if event_type in self._handlers:
            for handler_wrapper in self._handlers[event_type]:
                if self._should_handle(handler_wrapper, event):
                    handler = handler_wrapper.func
                    if self._async_handlers.get(handler, False):
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(handler(event))
                        except RuntimeError:
                            _log_framework_warning(
                                f"异步事件处理器 {handler.__name__} 在同步上下文中被调用，但没有运行的事件循环"
                            )
                    else:
                        try:
                            handler(event)
                        except Exception as e:
                            import traceback

                            _log_framework_error(f"事件处理器执行失败: {e}")
                            _log_framework_error(f"处理器: {handler.__name__}")
                            _log_framework_error(traceback.format_exc())

    async def _publish_async(self, event: Event):
        """异步发布事件（内部方法）"""
        event_type = type(event)

        if not self._should_propagate(event):
            _log_framework_debug(f"事件被过滤器阻止: {event_type.__name__}")
            return

        if event_type in self._handlers:
            for handler_wrapper in self._handlers[event_type]:
                if self._should_handle(handler_wrapper, event):
                    handler = handler_wrapper.func
                    if self._async_handlers.get(handler, False):
                        try:
                            await handler(event)
                        except Exception as e:
                            import traceback

                            _log_framework_error(f"异步事件处理器执行失败: {e}")
                            _log_framework_error(f"处理器: {handler.__name__}")
                            _log_framework_error(traceback.format_exc())
                    else:
                        try:
                            handler(event)
                        except Exception as e:
                            import traceback

                            _log_framework_error(f"事件处理器执行失败: {e}")
                            _log_framework_error(f"处理器: {handler.__name__}")
                            _log_framework_error(traceback.format_exc())


# 全局事件总线管理器
_event_bus_manager = _EventBusManager()


# 公共API函数
def get_event_bus() -> "_EventBus":
    """
    获取当前应用的事件总线（公共API）

    命名空间自动从元数据定义的应用名获取。

    Returns:
        当前应用的事件总线
    """
    return _event_bus_manager._get_bus()


def publish_event(event: Event, async_mode: bool = False):
    """
    发布事件 - 向事件总线发布事件

    Args:
        event: 要发布的事件对象（必须继承自 Event）
        async_mode: 是否异步发布（默认为 False，同步发布）

    Returns:
        异步模式下返回协程对象，同步模式下返回 None

    Example:
        class MyEvent(Event):
            message: str

        publish_event(MyEvent(message="Hello"))

        await publish_event(MyEvent(message="Hello"), async_mode=True)

    Note:
        - 同步模式：所有订阅者按顺序执行，阻塞直到完成
        - 异步模式：所有订阅者并发执行，返回协程对象
        - 事件发布失败不会影响其他订阅者
        - 支持条件订阅，只有满足条件的订阅者才会收到事件
    """
    event_bus = _event_bus_manager._get_bus()

    if async_mode:
        return event_bus._publish_async(event)
    else:
        event_bus._publish(event)


def subscribe_event(
    event_type: Type[Event],
    handler: Callable,
    condition: Optional[Callable] = None,
):
    """
    订阅事件 - 为指定事件类型注册处理器

    Args:
        event_type: 事件类型（必须继承自 Event）
        handler: 事件处理函数，接收事件对象作为参数
        condition: 可选的条件过滤器函数，返回 True 时才处理事件

    Returns:
        None

    Example:
        class MyEvent(Event):
            message: str

        def handler(event: MyEvent):
            print(f"收到事件: {event.message}")

        subscribe_event(MyEvent, handler)

        # 带条件过滤
        def condition_handler(event: MyEvent):
            return len(event.message) > 5

        subscribe_event(MyEvent, condition_handler, condition=lambda e: e.message.startswith("important"))

    Note:
        - 同一个事件类型可以有多个订阅者
        - 订阅者按注册顺序执行
        - 异步订阅者会自动并发执行
        - 条件函数接收事件对象作为参数
        - 使用 unsubscribe_event() 取消订阅
    """
    event_bus = _event_bus_manager._get_bus()
    event_bus._subscribe(event_type, handler, condition)


def unsubscribe_event(
    event_type: Type[Event],
    handler: Callable,
):
    """
    取消订阅事件（公共API）

    Args:
        event_type: 事件类型
        handler: 要移除的事件处理函数

    Example:
        unsubscribe_event(MyEvent, handler)
    """
    event_bus = _event_bus_manager._get_bus()
    event_bus._unsubscribe(event_type, handler)


def register_event_filter(
    filter_func: Callable[[Event], bool],
    event_type: Optional[Type[Event]] = None,
    namespace: Optional[str] = None,
    priority: int = 0,
):
    """
    注册事件过滤器（公共API）

    注册一个全局事件过滤器，所有事件都会经过这个过滤器。

    Args:
        filter_func: 过滤器函数，接收事件对象，返回True表示允许传播
        event_type: 可选的事件类型
        namespace: 可选的命名空间
        priority: 过滤器优先级，数值越小优先级越高

    Example:
        def my_filter(event: Event) -> bool:
            return True  # 允许所有事件

        register_event_filter(my_filter)
    """
    event_bus = _event_bus_manager._get_bus()
    event_bus._register_filter(filter_func, event_type, namespace, priority)


def unregister_event_filter(filter_func: Callable[[Event], bool]):
    """
    取消注册事件过滤器（公共API）

    Args:
        filter_func: 要移除的过滤器函数

    Example:
        unregister_event_filter(my_filter)
    """
    event_bus = _event_bus_manager._get_bus()
    event_bus._unregister_filter(filter_func)


# 内部函数（框架内部使用）
def _get_event_bus() -> "_EventBus":
    """获取当前应用的事件总线实例（内部函数）"""
    return _event_bus_manager._get_bus()


def _subscribe_event(
    event_type: Type[Event],
    handler: Callable,
    condition: Optional[Callable] = None,
):
    """手动订阅事件（内部函数）"""
    event_bus = _event_bus_manager._get_bus()
    event_bus._subscribe(event_type, handler, condition)


def _unsubscribe_event(
    event_type: Type[Event],
    handler: Callable,
):
    """手动取消订阅事件（内部函数）"""
    event_bus = _event_bus_manager._get_bus()
    event_bus._unsubscribe(event_type, handler)


def _register_event_filter(
    filter_func: Callable[[Event], bool],
    event_type: Optional[Type[Event]] = None,
    namespace: Optional[str] = None,
    priority: int = 0,
):
    """注册事件过滤器（内部函数）"""
    event_bus = _event_bus_manager._get_bus()
    event_bus._register_filter(filter_func, event_type, namespace, priority)


def _unregister_event_filter(filter_func: Callable[[Event], bool]):
    """取消注册事件过滤器（内部函数）"""
    event_bus = _event_bus_manager._get_bus()
    event_bus._unregister_filter(filter_func)


def _publish_event(event: Event):
    """发布事件（内部函数）"""
    event_bus = _event_bus_manager._get_bus()
    event_bus._publish(event)


async def _publish_event_async(event: Event):
    """异步发布事件（内部函数）"""
    event_bus = _event_bus_manager._get_bus()
    await event_bus._publish_async(event)
