"""
极简事件监听装饰器 - 实现唯一的事件总线
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Type, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Event:
    """基础事件类"""

    pass


@dataclass
class EventHandler:
    """事件处理器包装器"""

    func: Callable
    condition: Optional[Callable] = None
    topic: Optional[str] = None


class EventBus:
    """简单的事件总线实现"""

    def __init__(self):
        # 事件类型到处理器列表的映射（包含条件和主题）
        self._handlers: Dict[Type[Event], List[EventHandler]] = {}
        # 单线事件处理器（只有一个）
        self._single_handlers: Dict[Type[Event], EventHandler] = {}
        # 异步处理器标记
        self._async_handlers: Dict[Callable, bool] = {}
        # 拦截器映射
        self._interceptors: Dict[Type[Event], Callable] = {}

    def subscribe(
        self,
        event_type: Type[Event],
        handler: Callable,
        condition: Optional[Callable] = None,
        topic: Optional[str] = None,
    ):
        """订阅事件（多线）"""
        wrapper = EventHandler(handler, condition, topic)
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(wrapper)

    def subscribe_single(
        self,
        event_type: Type[Event],
        handler: Callable,
        condition: Optional[Callable] = None,
        topic: Optional[str] = None,
    ):
        """订阅事件（单线）"""
        wrapper = EventHandler(handler, condition, topic)
        self._single_handlers[event_type] = wrapper

    def register_interceptor(self, event_type: Type[Event], interceptor: Callable):
        """注册事件拦截器"""
        self._interceptors[event_type] = interceptor

    def unsubscribe(self, event_type: Type[Event], handler: Callable):
        """取消订阅事件"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h.func is not handler
            ]
            if handler in self._async_handlers:
                del self._async_handlers[handler]
        elif (
            event_type in self._single_handlers
            and self._single_handlers[event_type].func is handler
        ):
            del self._single_handlers[event_type]
            if handler in self._async_handlers:
                del self._async_handlers[handler]

    def _should_handle(self, handler: EventHandler, event: Event) -> bool:
        """检查处理器是否应该处理该事件"""
        # 检查条件过滤器
        if handler.condition is not None:
            try:
                if not handler.condition(event):
                    return False
            except Exception as e:
                print(f"事件条件过滤器执行失败: {e}")
                return False

        # 检查主题匹配
        if handler.topic is not None:
            event_topic = getattr(event, "topic", None)
            if event_topic != handler.topic:
                return False

        return True

    def publish(self, event: Event):
        """发布事件（同步）"""
        event_type = type(event)

        # 检查是否有拦截器
        should_propagate_to_multi = True
        if event_type in self._interceptors:
            interceptor = self._interceptors[event_type]
            try:
                should_continue = interceptor(event)
                if should_continue is False:
                    # 拦截器返回False，阻止多线事件传播
                    should_propagate_to_multi = False
            except Exception as e:
                print(f"事件拦截器执行失败: {e}")
                should_propagate_to_multi = False

        # 优先处理单线事件（不受拦截器影响）
        if event_type in self._single_handlers:
            handler_wrapper = self._single_handlers[event_type]
            if self._should_handle(handler_wrapper, event):
                handler = handler_wrapper.func
                if self._async_handlers.get(handler, False):
                    # 异步处理器：检查是否有运行的事件循环
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(handler(event))
                    except RuntimeError:
                        # 没有运行的事件循环，记录警告
                        print(
                            f"警告: 异步事件处理器 {handler.__name__} 在同步上下文中被调用，但没有运行的事件循环"
                        )
                else:
                    try:
                        handler(event)
                    except Exception as e:
                        import traceback

                        print(f"事件处理器执行失败: {e}")
                        print(f"处理器: {handler.__name__}")
                        traceback.print_exc()

        # 处理多线事件（受拦截器控制）
        if should_propagate_to_multi and event_type in self._handlers:
            for handler_wrapper in self._handlers[event_type]:
                if self._should_handle(handler_wrapper, event):
                    handler = handler_wrapper.func
                    if self._async_handlers.get(handler, False):
                        # 异步处理器：检查是否有运行的事件循环
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(handler(event))
                        except RuntimeError:
                            # 没有运行的事件循环，记录警告
                            print(
                                f"警告: 异步事件处理器 {handler.__name__} 在同步上下文中被调用，但没有运行的事件循环"
                            )
                    else:
                        try:
                            handler(event)
                        except Exception as e:
                            print(f"事件处理器执行失败: {e}")

    async def publish_async(self, event: Event):
        """异步发布事件"""
        event_type = type(event)

        # 检查是否有拦截器
        should_propagate_to_multi = True
        if event_type in self._interceptors:
            interceptor = self._interceptors[event_type]
            try:
                should_continue = interceptor(event)
                if should_continue is False:
                    # 拦截器返回False，阻止多线事件传播
                    should_propagate_to_multi = False
            except Exception as e:
                print(f"事件拦截器执行失败: {e}")
                should_propagate_to_multi = False

        # 优先处理单线事件（不受拦截器影响）
        tasks = []
        if event_type in self._single_handlers:
            handler_wrapper = self._single_handlers[event_type]
            if self._should_handle(handler_wrapper, event):
                handler = handler_wrapper.func
                if self._async_handlers.get(handler, False):
                    tasks.append(handler(event))
                else:
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"事件处理器执行失败: {e}")

        # 处理多线事件（受拦截器控制）
        if should_propagate_to_multi and event_type in self._handlers:
            for handler_wrapper in self._handlers[event_type]:
                if self._should_handle(handler_wrapper, event):
                    handler = handler_wrapper.func
                    if self._async_handlers.get(handler, False):
                        tasks.append(handler(event))
                    else:
                        try:
                            handler(event)
                        except Exception as e:
                            print(f"事件处理器执行失败: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# 全局事件总线实例
_event_bus = EventBus()


def subscribe_event(
    event_type: Type[Event],
    handler: Callable,
    condition: Optional[Callable] = None,
    topic: Optional[str] = None,
):
    """
    手动订阅事件（多线）

    为指定事件类型注册一个事件处理器，可以有多个处理器同时监听同一事件。
    当事件发布时，所有匹配的处理器都会被调用。

    Args:
        event_type: 事件类型（继承自Event的类）
        handler: 事件处理函数，接收事件对象作为参数
        condition: 可选的条件过滤器函数，接收事件对象，返回True时才处理
        topic: 可选的事件主题/通道，用于事件路由

    Returns:
        None

    Example:
        from LStartlet import subscribe_event, publish_event, Event

        class ButtonClickEvent(Event):
            button_id: str

        # 订阅事件
        def handle_click(event: ButtonClickEvent):
            print(f"按钮被点击: {event.button_id}")

        subscribe_event(ButtonClickEvent, handle_click)

        # 发布事件
        event = ButtonClickEvent(button_id="save_btn")
        publish_event(event)
    """
    _event_bus.subscribe(event_type, handler, condition, topic)


def subscribe_single_event(
    event_type: Type[Event],
    handler: Callable,
    condition: Optional[Callable] = None,
    topic: Optional[str] = None,
):
    """
    手动订阅事件（单线）

    为指定事件类型注册一个唯一的事件处理器，同一事件类型只能有一个单线处理器。
    如果注册了新的单线处理器，旧的会被替换。
    单线处理器不受拦截器影响。

    Args:
        event_type: 事件类型（继承自Event的类）
        handler: 事件处理函数，接收事件对象作为参数
        condition: 可选的条件过滤器函数，接收事件对象，返回True时才处理
        topic: 可选的事件主题/通道，用于事件路由

    Returns:
        None

    Example:
        from LStartlet import subscribe_single_event, publish_event, Event

        class ExitEvent(Event):
            reason: str

        # 订阅单线事件
        def handle_exit(event: ExitEvent):
            print(f"应用程序退出: {event.reason}")

        subscribe_single_event(ExitEvent, handle_exit)

        # 发布事件
        event = ExitEvent(reason="用户请求")
        publish_event(event)
    """
    _event_bus.subscribe_single(event_type, handler, condition, topic)


def register_event_interceptor(event_type: Type[Event], interceptor: Callable):
    """
    手动注册事件拦截器

    为指定事件类型注册一个拦截器，在事件处理器执行前被调用。
    拦截器可以阻止事件传播到多线处理器，但不影响单线处理器。

    Args:
        event_type: 事件类型（继承自Event的类）
        interceptor: 拦截器函数，接收事件对象作为参数，返回False可阻止传播

    Returns:
        None

    Example:
        from LStartlet import register_event_interceptor, publish_event, Event

        class DataChangeEvent(Event):
            data: str

        # 注册拦截器
        def intercept_data_change(event: DataChangeEvent):
            print(f"拦截数据变更: {event.data}")
            # 返回False阻止事件传播
            return False

        register_event_interceptor(DataChangeEvent, intercept_data_change)

        # 发布事件（会被拦截）
        event = DataChangeEvent(data="test")
        publish_event(event)
    """
    _event_bus.register_interceptor(event_type, interceptor)


def OnEvent(
    event_type: Type[Event],
    condition: Optional[Callable] = None,
    topic: Optional[str] = None,
):
    """
    事件监听装饰器

    Args:
        event_type: 要监听的事件类型
        condition: 条件过滤器函数，接收事件对象，返回bool
        topic: 事件主题/通道，用于事件路由

    Note:
        支持任何类或顶层函数使用此装饰器，不再强制要求@Component或@Plugin标记

    Example:
        class ButtonClickEvent(Event):
            button_id: str
            topic: str

        # 普通类也可以使用
        class MyController:
            @OnEvent(ButtonClickEvent, condition=lambda e: e.button_id == "save_btn")
            def handle_save_button(self, event: ButtonClickEvent):
                print(f"保存按钮被点击: {event.button_id}")

        # 顶层函数也可以使用
        @OnEvent(ButtonClickEvent)
        def global_handler(event: ButtonClickEvent):
            print("全局事件处理")
    """

    def decorator(func: Callable) -> Callable:
        # 使用统一的元数据属性名 _decorator_metadata
        if not hasattr(func, "_decorator_metadata"):
            setattr(func, "_decorator_metadata", [])

        event_metadata = {
            "type": "event",
            "event_type": event_type,
            "condition": condition,
            "topic": topic,
            "handler_type": "multi",  # 多线处理器
        }
        getattr(func, "_decorator_metadata").append(event_metadata)

        # 保持向后兼容性：同时设置旧的 _event_metadata 属性
        if not hasattr(func, "_event_metadata"):
            setattr(func, "_event_metadata", [])

        old_metadata = {
            "event_type": event_type,
            "condition": condition,
            "topic": topic,
            "handler_type": "multi",
        }
        getattr(func, "_event_metadata").append(old_metadata)

        # 直接注册事件处理器（保持向后兼容性）
        _event_bus.subscribe(event_type, func, condition, topic)
        return func

    return decorator


def OnSingleEvent(
    event_type: Type[Event],
    condition: Optional[Callable] = None,
    topic: Optional[str] = None,
):
    """
    单线事件监听装饰器（只有一个处理器）

    Args:
        event_type: 要监听的事件类型
        condition: 条件过滤器函数，接收事件对象，返回bool
        topic: 事件主题/通道，用于事件路由

    Note:
        支持任何类或顶层函数使用此装饰器，不再强制要求@Component或@Plugin标记

    Example:
        class ExitHandler:
            @OnSingleEvent(ButtonClickEvent, condition=lambda e: e.button_id == "exit_btn")
            def handle_exit_button(self, event: ButtonClickEvent):
                # 只处理退出按钮
                pass
    """

    def decorator(func: Callable) -> Callable:
        # 使用统一的元数据属性名 _decorator_metadata
        if not hasattr(func, "_decorator_metadata"):
            setattr(func, "_decorator_metadata", [])

        event_metadata = {
            "type": "event",
            "event_type": event_type,
            "condition": condition,
            "topic": topic,
            "handler_type": "single",  # 单线处理器
        }
        getattr(func, "_decorator_metadata").append(event_metadata)

        # 保持向后兼容性：同时设置旧的 _event_metadata 属性
        if not hasattr(func, "_event_metadata"):
            setattr(func, "_event_metadata", [])

        old_metadata = {
            "event_type": event_type,
            "condition": condition,
            "topic": topic,
            "handler_type": "single",
        }
        getattr(func, "_event_metadata").append(old_metadata)

        # 直接注册事件处理器（保持向后兼容性）
        _event_bus.subscribe_single(event_type, func, condition, topic)
        return func

    return decorator


def EventInterceptor(event_type: Type[Event]):
    """
    事件拦截器装饰器

    Args:
        event_type: 要拦截的事件类型

    Returns:
        bool: True继续传播事件，False阻止事件传播

    Example:
        @EventInterceptor(ButtonClickEvent)
        def intercept_old_ui(event: ButtonClickEvent):
            # 阻止老UI处理事件
            return False
    """

    def decorator(func: Callable) -> Callable:
        # 使用统一的元数据属性名 _decorator_metadata
        if not hasattr(func, "_decorator_metadata"):
            setattr(func, "_decorator_metadata", [])

        event_metadata = {
            "type": "event",
            "event_type": event_type,
            "handler_type": "interceptor",  # 拦截器
        }
        getattr(func, "_decorator_metadata").append(event_metadata)

        # 保持向后兼容性：同时设置旧的 _event_metadata 属性
        if not hasattr(func, "_event_metadata"):
            setattr(func, "_event_metadata", [])

        old_metadata = {"event_type": event_type, "handler_type": "interceptor"}
        getattr(func, "_event_metadata").append(old_metadata)

        # 直接注册事件拦截器（保持向后兼容性）
        _event_bus.register_interceptor(event_type, func)
        return func

    return decorator


def publish_event(event: Event):
    """
    发布事件的便捷函数

    同步发布事件，触发所有匹配的事件处理器。
    如果有拦截器，拦截器会先执行，可以阻止事件传播到多线处理器。

    Args:
        event: 事件对象（继承自Event的类实例）

    Returns:
        None

    Example:
        from LStartlet import publish_event, Event

        class ButtonClickEvent(Event):
            button_id: str

        # 发布事件
        event = ButtonClickEvent(button_id="save_btn")
        publish_event(event)
    """
    _event_bus.publish(event)


def publish_event_async(event: Event):
    """
    异步发布事件的便捷函数

    异步发布事件，触发所有匹配的事件处理器。
    异步处理器会在事件循环中执行，同步处理器会立即执行。

    Args:
        event: 事件对象（继承自Event的类实例）

    Returns:
        Coroutine: 异步协程对象

    Example:
        import asyncio
        from LStartlet import publish_event_async, Event

        class ButtonClickEvent(Event):
            button_id: str

        # 异步发布事件
        async def main():
            event = ButtonClickEvent(button_id="save_btn")
            await publish_event_async(event)

        asyncio.run(main())
    """
    return _event_bus.publish_async(event)


def replace_event_handler(
    old_handler: Callable, new_handler: Callable, event_type: Type[Event]
):
    """
    替换事件处理器（用于动态替换）

    动态替换已注册的事件处理器，适用于运行时需要改变处理逻辑的场景。

    Args:
        old_handler: 要替换的旧处理器函数
        new_handler: 新的处理器函数
        event_type: 事件类型

    Returns:
        None

    Example:
        from LStartlet import replace_event_handler, subscribe_event, publish_event, Event

        class ButtonClickEvent(Event):
            button_id: str

        # 初始处理器
        def old_handler(event: ButtonClickEvent):
            print("旧处理器")

        # 新处理器
        def new_handler(event: ButtonClickEvent):
            print("新处理器")

        # 订阅初始处理器
        subscribe_event(ButtonClickEvent, old_handler)

        # 替换处理器
        replace_event_handler(old_handler, new_handler, ButtonClickEvent)

        # 发布事件（会使用新处理器）
        event = ButtonClickEvent(button_id="save_btn")
        publish_event(event)
    """

    _event_bus.unsubscribe(event_type, old_handler)
    _event_bus.subscribe(event_type, new_handler)


# 兼容性别名
def get_event_bus() -> EventBus:
    """
    获取全局事件总线实例

    返回框架的全局事件总线，用于管理所有事件处理器和事件发布。
    通常情况下，用户不需要直接调用此函数，而是使用便捷函数。

    Returns:
        EventBus: 全局事件总线实例

    Example:
        from LStartlet import get_event_bus, Event

        # 获取事件总线
        bus = get_event_bus()

        # 定义事件
        class MyEvent(Event):
            data: str

        # 订阅事件
        def handler(event: MyEvent):
            print(f"处理事件: {event.data}")

        bus.subscribe(MyEvent, handler)

        # 发布事件
        event = MyEvent(data="test")
        bus.publish(event)
    """
    return _event_bus
