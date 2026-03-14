"""
调度系统任务分发器
负责任务的分发、调度策略和负载均衡
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any, Deque
from enum import Enum
from dataclasses import dataclass, field
import heapq
from collections import deque
import time
# 使用事件系统
from core.event.events.scheduler_events import (
    TaskStartedEvent, TaskCompletedEvent, TaskFailedEvent
)
from core.event.event_bus import EventBus
# 依赖注入容器
from core.di.app_container import get_app_container
# 使用项目自定义日志管理器
from core.logger import info


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    func: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=lambda: {})
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=lambda: {})


class TaskQueue:
    """任务队列基类"""
    
    def __init__(self):
        self._tasks: List[Any] = []
    
    def put(self, task: Task) -> None:
        """添加任务到队列"""
        raise NotImplementedError
    
    def get(self) -> Optional[Task]:
        """从队列获取任务"""
        raise NotImplementedError
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return len(self._tasks) == 0
    
    def size(self) -> int:
        """获取队列大小"""
        return len(self._tasks)


class FIFOQueue(TaskQueue):
    """先进先出队列"""
    
    def __init__(self):
        super().__init__()
        self._queue: Deque[Task] = deque()
    
    def put(self, task: Task) -> None:
        self._queue.append(task)
    
    def get(self) -> Optional[Task]:
        if self.empty():
            return None
        return self._queue.popleft()


class PriorityQueue(TaskQueue):
    """优先级队列"""
    
    def put(self, task: Task) -> None:
        # 使用负优先级值，因为heapq是最小堆
        heapq.heappush(self._tasks, (-task.priority.value, task.created_at, task))
    
    def get(self) -> Optional[Task]:
        if self.empty():
            return None
        _, _, task = heapq.heappop(self._tasks)
        return task


class RoundRobinQueue(TaskQueue):
    """轮询队列"""
    
    def __init__(self):
        super().__init__()
        self._queues: Dict[str, Deque[Task]] = {}
        self._current_worker = 0
    
    def put(self, task: Task) -> None:
        worker_id = task.metadata.get('worker_id', 'default')
        if worker_id not in self._queues:
            self._queues[worker_id] = deque()
        self._queues[worker_id].append(task)
    
    def get(self) -> Optional[Task]:
        if not self._queues:
            return None
        
        worker_ids = list(self._queues.keys())
        if not worker_ids:
            return None
        
        # 轮询选择工作者
        self._current_worker = (self._current_worker + 1) % len(worker_ids)
        worker_id = worker_ids[self._current_worker]
        
        if self._queues[worker_id]:
            return self._queues[worker_id].popleft()
        
        # 如果当前工作者队列为空，尝试其他工作者
        for i in range(len(worker_ids)):
            next_worker = (self._current_worker + i + 1) % len(worker_ids)
            if self._queues[worker_ids[next_worker]]:
                self._current_worker = next_worker
                return self._queues[worker_ids[next_worker]].popleft()
        
        return None
    
    def size(self) -> int:
        """获取队列大小"""
        return sum(len(queue) for queue in self._queues.values())
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return all(len(queue) == 0 for queue in self._queues.values())


class TaskDispatcher:
    """任务分发器"""
    
    def __init__(self, strategy: str = "round_robin", max_concurrent_tasks: int = 10):
        """
        初始化任务分发器
        
        Args:
            strategy: 调度策略 ('fifo', 'priority', 'round_robin')
            max_concurrent_tasks: 最大并发任务数
        """
        self.strategy = strategy
        self.max_concurrent_tasks = max_concurrent_tasks
        self._task_queue = self._create_queue(strategy)
        self._active_tasks: Dict[str, asyncio.Task[Any]] = {}
        self._completed_tasks: List[Task] = []
        self._failed_tasks: List[Task] = []
        # 获取事件总线实例
        self._event_bus = get_app_container().resolve(EventBus)
        info(f"任务分发器初始化完成 (策略: {strategy}, 最大并发任务数: {max_concurrent_tasks})")
    
    def _create_queue(self, strategy: str) -> TaskQueue:
        """根据策略创建任务队列"""
        if strategy == "fifo":
            return FIFOQueue()
        elif strategy == "priority":
            return PriorityQueue()
        elif strategy == "round_robin":
            return RoundRobinQueue()
        else:
            raise ValueError(f"Unknown scheduling strategy: {strategy}")
    
    def submit_task(
        self,
        task_id: str,
        func: Callable[..., Any],
        *args: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        **kwargs: Any
    ) -> Task:
        """
        提交任务到分发器
        
        Args:
            task_id: 任务ID
            func: 任务函数
            *args: 函数参数
            priority: 任务优先级
            timeout: 任务超时时间
            max_retries: 最大重试次数
            **kwargs: 函数关键字参数
            
        Returns:
            任务对象
        """
        task = Task(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries
        )
        self._task_queue.put(task)
        return task
    
    async def dispatch_next_task(self) -> Optional[Task]:
        """
        分发下一个任务
        
        Returns:
            分发的任务，如果队列为空则返回None
        """
        if len(self._active_tasks) >= self.max_concurrent_tasks:
            return None
        
        task = self._task_queue.get()
        if task is None:
            return None
        
        # 发布任务开始事件
        task_data: Dict[str, Any] = {
            "func_name": getattr(task.func, "__name__", str(task.func)),
            "priority": task.priority.name,
            "timeout": task.timeout,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "args_count": len(task.args),
            "kwargs_keys": list(task.kwargs.keys())
        }
        self._event_bus.publish(TaskStartedEvent(task.task_id, task_data))
        
        # 创建异步任务
        async_task = asyncio.create_task(self._execute_task(task))
        self._active_tasks[task.task_id] = async_task
        
        return task
    
    async def _execute_task(self, task: Task) -> Any:
        """
        执行任务
        
        Args:
            task: 要执行的任务
            
        Returns:
            任务执行结果
        """
        try:
            # 执行任务
            if asyncio.iscoroutinefunction(task.func):
                result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                # 对于同步函数，使用线程池执行
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, task.func, *task.args, **task.kwargs),
                    timeout=task.timeout
                )
            
            # 任务成功完成
            self._completed_tasks.append(task)
            
            # 发布任务完成事件
            task_data: Dict[str, Any] = {
                "func_name": getattr(task.func, "__name__", str(task.func)),
                "priority": task.priority.name,
                "execution_time": time.time() - task.created_at
            }
            self._event_bus.publish(TaskCompletedEvent(task.task_id, result, task_data))
            
            return result
            
        except asyncio.TimeoutError as e:
            # 任务超时
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                # 重试任务
                self._task_queue.put(task)
            else:
                self._failed_tasks.append(task)
                # 发布任务失败事件
                task_data: Dict[str, Any] = {
                    "func_name": getattr(task.func, "__name__", str(task.func)),
                    "priority": task.priority.name,
                    "error_type": "TimeoutError",
                    "retry_count": task.retry_count
                }
                self._event_bus.publish(TaskFailedEvent(task.task_id, str(e), task_data))
            raise
            
        except Exception as e:
            # 任务执行异常
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                # 重试任务
                self._task_queue.put(task)
            else:
                self._failed_tasks.append(task)
                # 发布任务失败事件
                task_data: Dict[str, Any] = {
                    "func_name": getattr(task.func, "__name__", str(task.func)),
                    "priority": task.priority.name,
                    "error_type": type(e).__name__,
                    "retry_count": task.retry_count
                }
                self._event_bus.publish(TaskFailedEvent(task.task_id, str(e), task_data))
            raise
            
        finally:
            # 清理活跃任务
            if task.task_id in self._active_tasks:
                del self._active_tasks[task.task_id]
    
    def get_active_task_count(self) -> int:
        """获取活跃任务数量"""
        return len(self._active_tasks)
    
    def get_completed_task_count(self) -> int:
        """获取已完成任务数量"""
        return len(self._completed_tasks)
    
    def get_failed_task_count(self) -> int:
        """获取失败任务数量"""
        return len(self._failed_tasks)
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self._task_queue.size()
    
    def is_busy(self) -> bool:
        """检查分发器是否繁忙"""
        return (self.get_active_task_count() >= self.max_concurrent_tasks or 
                self.get_queue_size() > 0)
    
    async def wait_for_completion(self) -> None:
        """等待所有任务完成"""
        while self.is_busy():
            await asyncio.sleep(0.1)
            # 分发剩余任务
            while self.get_queue_size() > 0 and self.get_active_task_count() < self.max_concurrent_tasks:
                await self.dispatch_next_task()
        
        # 等待所有活跃任务完成
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks.values(), return_exceptions=True)