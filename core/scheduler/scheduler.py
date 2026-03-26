"""
调度系统核心调度器
整合进程管理、配置管理和任务分发的核心调度组件
"""

import asyncio
from typing import Optional, Dict, Any, Callable, TypeVar, Awaitable, Union
# 使用项目自定义日志管理器
from core.logger import info, warning, error
# 使用项目自定义错误处理系统
from core.error import handle_error
from core.error.exceptions import ProcessingError, ConfigError
# 导入装饰器
from core.decorators import with_error_handling, with_logging, monitor_metrics, monitor_metrics_async
# 使用事件系统 - 只导入需要的事件
from core.event.events.scheduler_events import (
    SchedulerStatusEvent, TaskSubmittedEvent
)
from core.event.event_bus import EventBus
from .config_manager import SchedulerConfig  # 只导入SchedulerConfig
from .process_manager import ProcessManager
from .task_dispatcher import TaskDispatcher, TaskPriority
from .tick import TickComponent, TickConfig

# 依赖注入容器
from core.di.app_container import get_app_container # type: ignore
from core.config.config_manager import ConfigManager as CoreConfigManager  # 重命名导入

# 类型变量定义
T = TypeVar('T')


class Scheduler:
    """核心调度器"""
    
    # 属性类型声明
    _config: SchedulerConfig
    _config_manager: CoreConfigManager
    _process_manager: ProcessManager
    _task_dispatcher: TaskDispatcher
    _tick_component: TickComponent
    _event_bus: EventBus
    _is_running: bool
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        """
        初始化调度器
        
        Args:
            config: 调度器配置，如果为None则使用默认配置
        """
        self._config = config or SchedulerConfig()
        
        # 初始化ConfigManager
        from core.di.app_container import get_app_container
        self._config_manager = get_app_container().resolve(CoreConfigManager)
        
        # 获取调度器配置 - 使用"scheduler"作为key
        scheduler_config_dict = self._config_manager.get_config("scheduler")
        if scheduler_config_dict is None:
            # 如果没有scheduler配置，使用默认值
            max_processes = 4
            process_timeout = 30.0
            max_concurrent_tasks = 10
            scheduling_strategy = "round_robin"
        else:
            # scheduler_config_dict 是一个字典，不是对象
            max_processes = scheduler_config_dict.get('max_processes', 4)
            process_timeout = scheduler_config_dict.get('process_timeout', 30.0)
            max_concurrent_tasks = scheduler_config_dict.get('max_concurrent_tasks', 10)
            scheduling_strategy = scheduler_config_dict.get('scheduling_strategy', "round_robin")
        
        # 初始化所有组件
        self._process_manager = ProcessManager(
            max_processes=max_processes,
            process_timeout=process_timeout
        )
        self._task_dispatcher = TaskDispatcher(
            max_concurrent_tasks=max_concurrent_tasks,
            strategy=scheduling_strategy
        )
        self._tick_component = TickComponent(TickConfig(interval=1.0, auto_start=False))
        self._event_bus = get_app_container().resolve(EventBus)
        
        self._is_running = False

    @property
    def config(self) -> SchedulerConfig:
        """获取当前配置"""
        # 获取scheduler配置，如果没有则返回默认配置
        scheduler_config_dict = self._config_manager.get_config("scheduler")
        if scheduler_config_dict is None:
            return self._config
        
        # 创建一个新的SchedulerConfig对象
        config = SchedulerConfig()
        config.max_processes = scheduler_config_dict.get('max_processes', 4)
        config.process_timeout = scheduler_config_dict.get('process_timeout', 30.0)
        config.max_concurrent_tasks = scheduler_config_dict.get('max_concurrent_tasks', 10)
        config.scheduling_strategy = scheduler_config_dict.get('scheduling_strategy', "round_robin")
        return config

    @property
    def is_running(self) -> bool:
        """检查调度器是否正在运行"""
        return self._is_running
    
    @property
    def tick_component(self) -> TickComponent:
        """获取tick组件"""
        return self._tick_component  # type: ignore
    
    @property
    def event_bus(self) -> EventBus:
        """获取事件总线实例"""
        return self._event_bus  # type: ignore
    
    def get_config_manager(self) -> CoreConfigManager:
        """获取配置管理器实例"""
        return self._config_manager

    @monitor_metrics("scheduler_start", include_labels=True)
    @with_error_handling(error_code="SCHEDULER_START_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    def start(self) -> None:
        """Start scheduler"""
        if self._is_running:
            warning("Scheduler is already running")
            return
        
        try:
            # Start all components
            self._process_manager.start()
            # TaskDispatcher doesn't need explicit startup, it works automatically when needed
            
            # Start tick component only if there's a running event loop
            try:
                asyncio.get_running_loop()
                # Only start tick component if we're in an async context with running loop
                self._tick_component.start()
            except RuntimeError:
                # In synchronous context without event loop, skip tick component
                warning("No running event loop detected, skipping tick component startup")
            
            self._is_running = True
            
            # Publish start event
            self._event_bus.publish(SchedulerStatusEvent("started"))
            info("Scheduler started successfully")
            
        except Exception as e:
            error(f"Scheduler failed to start: {e}")
            self._is_running = False
            raise

    @monitor_metrics("scheduler_stop", include_labels=True)
    @with_error_handling(error_code="SCHEDULER_STOP_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    def stop(self) -> None:
        """Stop scheduler"""
        if not self._is_running:
            warning("Scheduler is not running")
            return
        
        try:
            # Stop all components (reverse order)
            self._tick_component.stop()
            # TaskDispatcher doesn't need explicit shutdown
            self._process_manager.stop()
            
            self._is_running = False
            
            # Publish stop event
            self._event_bus.publish(SchedulerStatusEvent("stopped"))
            info("Scheduler stopped successfully")
            
        except Exception as e:
            error(f"Scheduler failed to stop: {e}")
            raise
    
    def update_config(self, **kwargs: Any) -> None:
        """
        更新调度器配置
        
        Args:
            **kwargs: 配置项键值对
        """
        try:
            if self._is_running:
                warning("Updating configuration while scheduler is running")
            
            # Update config manager
            for key, value in kwargs.items():
                self._config_manager.set_config(key, value)
            
            # Update related component configs - re-fetch from config manager
            config_dict = self._config_manager.get_config("scheduler")
            if config_dict is not None:
                # Note: ProcessManager and TaskDispatcher properties may need setter methods
                # If no setter, we may need to recreate these components
                if hasattr(self._process_manager, 'max_processes'):
                    self._process_manager.max_processes = config_dict.get('max_processes', 4)
                if hasattr(self._process_manager, 'process_timeout'):
                    self._process_manager.process_timeout = config_dict.get('process_timeout', 30.0)
                if hasattr(self._task_dispatcher, 'max_concurrent_tasks'):
                    self._task_dispatcher.max_concurrent_tasks = config_dict.get('max_concurrent_tasks', 10)
            
            # Publish config update event
            self.event_bus.publish(SchedulerStatusEvent("config_updated", {
                "updated_config": kwargs,
                "current_config": config_dict or {}
            }))
        except Exception as e:
            error_msg = f"更新调度器配置失败: {e}"
            handle_error(ConfigError(error_msg, context=kwargs))
            raise
    
    @monitor_metrics("scheduler_submit_task", include_labels=True)
    async def submit_task(
        self,
        task_id: str,
        func: Callable[..., Union[T, Awaitable[T]]],
        *args: Any,
        priority: Union[TaskPriority, str] = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        **kwargs: Any
    ) -> Optional[T]:
        """
        提交任务到调度器
        
        Args:
            task_id: 任务ID
            func: 任务函数
            *args: 函数参数
            priority: 任务优先级
            timeout: 任务超时时间
            max_retries: 最大重试次数
            **kwargs: 函数关键字参数
            
        Returns:
            任务执行结果
        """
        try:
            if not self._is_running:
                error_msg = "Scheduler is not running. Call start() first."
                handle_error(ProcessingError(error_msg))
                raise RuntimeError(error_msg)
            
            # Handle priority parameter
            if isinstance(priority, str):
                try:
                    priority = TaskPriority[priority.upper()]
                except KeyError:
                    error_msg = f"Invalid priority: {priority}"
                    handle_error(ConfigError(error_msg))
                    raise ValueError(error_msg)
            
            # Use defaults from config
            actual_timeout = timeout
            actual_max_retries = max_retries
            
            config_dict = self._config_manager.get_config("scheduler")
            if config_dict is not None:
                actual_timeout = timeout or config_dict.get('task_timeout', 60.0)
                actual_max_retries = max_retries or config_dict.get('retry_count', 3)
            else:
                actual_timeout = timeout or 60.0
                actual_max_retries = max_retries or 3
            
            # Submit task to dispatcher
            self._task_dispatcher.submit_task(
                task_id=task_id,
                func=func,
                priority=priority,
                timeout=actual_timeout,
                max_retries=actual_max_retries,
                *args,
                **kwargs
            )
            
            # Publish task submitted event
            task_data: Dict[str, Any] = {
                "func_name": getattr(func, "__name__", str(func)),
                "priority": priority.name if hasattr(priority, "name") else str(priority),
                "timeout": actual_timeout,
                "max_retries": actual_max_retries,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
            self.event_bus.publish(TaskSubmittedEvent(task_id, task_data))
            
            # Immediately dispatch task
            await self._task_dispatcher.dispatch_next_task()
            
            # Note: Current design cannot directly return task result
            # Need to use other mechanisms (like callbacks or Future) to get result
            warning("submit_task result handling needs refinement in current design")
            return None
        except Exception as e:
            error_msg = f"提交任务失败: {e}"
            handle_error(ProcessingError(error_msg, context={"task_id": task_id, "priority": priority}))
            raise

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        try:
            config_dict = self._config_manager.get_config("scheduler")
            
            return {
                'is_running': self._is_running,
                'active_processes': self._process_manager.get_active_process_count(),
                'active_tasks': self._task_dispatcher.get_active_task_count(),
                'completed_tasks': self._task_dispatcher.get_completed_task_count(),
                'failed_tasks': self._task_dispatcher.get_failed_task_count(),
                'queue_size': self._task_dispatcher.get_queue_size(),
                'tick_stats': self._tick_component.get_stats(),
                'config': config_dict or {}
            }
        except Exception as e:
            error_msg = f"获取调度器状态失败: {e}"
            handle_error(ProcessingError(error_msg))
            return {}

    @monitor_metrics_async("scheduler_run_loop", include_labels=True)
    async def run_scheduler_loop(self) -> None:
        """运行调度器主循环"""
        try:
            if not self._is_running:
                error_msg = "Scheduler is not running. Call start() first."
                handle_error(ProcessingError(error_msg))
                raise RuntimeError(error_msg)
            
            info("Starting scheduler main loop")
            
            while self._is_running:
                # Dispatch tasks
                while (self._task_dispatcher.get_queue_size() > 0 and 
                       self._task_dispatcher.get_active_task_count() < self._task_dispatcher.max_concurrent_tasks):
                    await self._task_dispatcher.dispatch_next_task()
                
                # Short sleep to avoid high CPU usage
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            info("Scheduler loop cancelled")
        except Exception as e:
            error_msg = f"Error in scheduler loop: {e}"
            handle_error(ProcessingError(error_msg))
            raise
        finally:
            info("Scheduler loop ended")
    
    @monitor_metrics_async("scheduler_wait_completion", include_labels=True)
    async def wait_for_completion(self) -> None:
        """等待所有任务完成"""
        try:
            await self._task_dispatcher.wait_for_completion()
        except Exception as e:
            error_msg = f"等待任务完成失败: {e}"
            handle_error(ProcessingError(error_msg))
            raise