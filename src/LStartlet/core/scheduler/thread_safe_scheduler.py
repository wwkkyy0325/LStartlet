import asyncio
import threading
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import queue
import time

from .task_dispatcher import TaskPriority
from LStartlet.core.event.event_bus import EventBus


class ThreadSafeScheduler:
    """线程安全的任务调度器"""

    def __init__(self, max_workers: int = 4):
        self._main_thread_id = threading.current_thread().ident
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._main_thread_queue: queue.Queue[Any] = queue.Queue()
        self._event_bus = EventBus()
        self._running = True
        self._lock = threading.Lock()

        # 启动主线程任务处理线程
        self._processor_thread = threading.Thread(
            target=self._process_main_thread_tasks, daemon=True
        )
        self._processor_thread.start()

    def _process_main_thread_tasks(self):
        """处理主线程队列中的任务"""
        while self._running:
            try:
                # 等待任务，超时避免永久阻塞
                task_item = self._main_thread_queue.get(timeout=0.1)
                if task_item is None:
                    break

                func, args, kwargs, callback = task_item
                try:
                    result = func(*args, **kwargs)
                    if callback:
                        callback(result, None)
                except Exception as e:
                    if callback:
                        callback(None, e)
                finally:
                    self._main_thread_queue.task_done()

            except queue.Empty:
                # 超时，继续检查是否还在运行
                continue
            except Exception as e:
                from LStartlet.core.logger import error

                error(f"主线程任务处理器错误: {e}")

    def is_main_thread(self) -> bool:
        """检查当前是否为主线程"""
        return threading.current_thread().ident == self._main_thread_id

    def run_on_main_thread(
        self,
        func: Callable[..., Any],
        *args: Any,
        callback: Optional[Callable[[Any, Optional[Exception]], None]] = None,
        **kwargs: Any,
    ) -> None:
        """
        在主线程中执行任务

        Args:
            func: 要执行的函数
            *args: 函数参数
            callback: 完成回调 (result, exception)
            **kwargs: 函数关键字参数
        """
        if self.is_main_thread():
            # 如果已经在主线程，直接执行
            try:
                result = func(*args, **kwargs)
                if callback:
                    callback(result, None)
            except Exception as e:
                if callback:
                    callback(None, e)
        else:
            # 放入主线程队列
            self._main_thread_queue.put((func, args, kwargs, callback))

    def submit_async_task(
        self,
        func: Callable[..., Any],
        *args: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> asyncio.Future[Any]:
        """
        提交异步任务到线程池

        Args:
            func: 任务函数
            *args: 函数参数
            priority: 任务优先级（用于日志和监控）
            timeout: 任务超时时间
            max_retries: 最大重试次数
            **kwargs: 函数关键字参数

        Returns:
            asyncio.Future 对象
        """
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def execute_task():
            try:
                if asyncio.iscoroutinefunction(func):
                    # 协程函数需要在事件循环中执行
                    coro = func(*args, **kwargs)
                    if timeout:
                        coro = asyncio.wait_for(coro, timeout=timeout)
                    result = asyncio.run_coroutine_threadsafe(coro, loop).result()
                else:
                    # 普通函数直接执行
                    if timeout:
                        result = self._executor.submit(func, *args, **kwargs).result(
                            timeout=timeout
                        )
                    else:
                        result = func(*args, **kwargs)

                loop.call_soon_threadsafe(future.set_result, result)

            except Exception as e:
                loop.call_soon_threadsafe(future.set_exception, e)

        # 提交到线程池
        self._executor.submit(execute_task)
        return future

    def publish_event_thread_safe(self, event: Any) -> bool:
        """
        线程安全地发布事件

        Args:
            event: 要发布的事件

        Returns:
            发布是否成功
        """
        if self.is_main_thread():
            return self._event_bus.publish(event)
        else:
            # 在主线程中发布事件
            result = [False]

            def publish_in_main():
                result[0] = self._event_bus.publish(event)

            self.run_on_main_thread(publish_in_main)

            # 简单等待结果（实际应用中可能需要更好的同步机制）
            start_time = time.time()
            while not result[0] and time.time() - start_time < 1.0:
                time.sleep(0.01)
            return result[0]

    def shutdown(self, wait: bool = True) -> None:
        """关闭调度器"""
        self._running = False
        if wait:
            # 发送终止信号
            self._main_thread_queue.put(None)
            self._main_thread_queue.join()
        self._executor.shutdown(wait=wait)
