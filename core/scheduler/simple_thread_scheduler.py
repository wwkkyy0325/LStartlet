import asyncio
import threading
from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor

from core.event.event_bus import EventBus


class SimpleThreadScheduler:
    """简化的线程安全任务调度器"""

    def __init__(self, max_workers: int = 4):
        self._main_thread_id = threading.current_thread().ident
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._event_bus = EventBus()

    def is_main_thread(self) -> bool:
        """检查当前是否为主线程"""
        return threading.current_thread().ident == self._main_thread_id

    def run_on_main_thread(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """
        在主线程中同步执行任务

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        if self.is_main_thread():
            return func(*args, **kwargs)
        else:
            # 在非主线程中调用会抛出异常，因为无法真正同步切换到主线程
            # 实际应用中应该使用异步回调模式
            raise RuntimeError(
                "Cannot synchronously execute function on main thread from background thread"
            )

    def run_on_main_thread_async(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> asyncio.Future[Any]:
        """
        异步在主线程中执行任务（实际是提交到线程池）

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            asyncio.Future 对象
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self._executor, func, *args, **kwargs)

    def submit_background_task(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> asyncio.Future[Any]:
        """
        提交后台任务到线程池

        Args:
            func: 任务函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            asyncio.Future 对象
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self._executor, func, *args, **kwargs)

    def publish_event_safely(self, event: Any) -> bool:
        """
        安全地发布事件（线程安全）

        Args:
            event: 要发布的事件

        Returns:
            发布是否成功
        """
        return self._event_bus.publish(event)

    def shutdown(self) -> None:
        """关闭调度器"""
        self._executor.shutdown(wait=True)
