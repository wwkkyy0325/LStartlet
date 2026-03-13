"""
调度系统核心调度器
整合进程管理、配置管理和任务分发的核心调度组件
"""

import asyncio
from typing import Optional, Dict, Any, Callable, TypeVar, Awaitable, Union
# 使用项目自定义日志管理器
from core.logger import info, warning
# 使用项目自定义错误处理系统
from core.error import handle_error
from core.error.exceptions import OCRInitializationError, OCRProcessingError, OCRConfigError
# 使用事件系统 - 只导入需要的事件
from core.event.events.scheduler_events import SchedulerStatusEvent, TaskSubmittedEvent
from core.event.event_bus import EventBus
from .config_manager import SchedulerConfig, ConfigManager
from .process_manager import ProcessManager
from .task_dispatcher import TaskDispatcher, TaskPriority
from .tick import TickComponent, TickConfig

# 类型变量定义
T = TypeVar('T')


class Scheduler:
    """核心调度器"""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        """
        初始化调度器
        
        Args:
            config: 调度器配置，如果为None则使用默认配置
        """
        try:
            self._config_manager = ConfigManager(config)
            self._process_manager = ProcessManager(
                max_processes=self._config_manager.get_config().max_processes,
                process_timeout=self._config_manager.get_config().process_timeout
            )
            self._task_dispatcher = TaskDispatcher(
                strategy=self._config_manager.get_config().scheduling_strategy,
                max_concurrent_tasks=self._config_manager.get_config().max_concurrent_tasks
            )
            
            # 初始化tick组件
            tick_config = TickConfig(
                interval=1.0,  # 默认1秒间隔
                auto_start=False,
                enable_logging=True
            )
            self._tick_component = TickComponent(tick_config)
            
            # 获取事件总线实例
            self._event_bus = EventBus()
            
            self._is_running = False
            info("调度器初始化完成")
        except Exception as e:
            error_msg = f"调度器初始化失败: {e}"
            handle_error(OCRInitializationError(error_msg, context={"config": config}))
            raise
    
    @property
    def config(self) -> SchedulerConfig:
        """获取当前配置"""
        return self._config_manager.get_config()
    
    @property
    def is_running(self) -> bool:
        """检查调度器是否正在运行"""
        return self._is_running
    
    @property
    def tick_component(self) -> TickComponent:
        """获取tick组件"""
        return self._tick_component
    
    @property
    def event_bus(self) -> EventBus:
        """获取事件总线实例"""
        return self._event_bus
    
    def start(self) -> None:
        """启动调度器"""
        try:
            if self._is_running:
                warning("Scheduler is already running")
                return
            
            # 启动进程管理器
            self._process_manager.start()
            
            # 验证配置
            if not self._config_manager.validate_config():
                error_msg = "Invalid scheduler configuration"
                handle_error(OCRConfigError(error_msg))
                raise ValueError(error_msg)
            
            self._is_running = True
            info("Scheduler started successfully")
            
            # 发布调度器启动事件
            self._event_bus.publish(SchedulerStatusEvent("started", {
                "config": self.config.to_dict()
            }))
        except Exception as e:
            error_msg = f"启动调度器失败: {e}"
            handle_error(OCRInitializationError(error_msg))
            raise
    
    def stop(self) -> None:
        """停止调度器"""
        try:
            if not self._is_running:
                return
            
            # 停止tick组件
            self._tick_component.stop()
            
            # 停止任务分发器（等待所有任务完成）
            # 注意：这需要在异步上下文中调用
            info("Stopping scheduler...")
            
            # 停止进程管理器
            self._process_manager.stop()
            
            self._is_running = False
            info("Scheduler stopped successfully")
            
            # 发布调度器停止事件
            self._event_bus.publish(SchedulerStatusEvent("stopped", {
                "status": self.get_status()
            }))
        except Exception as e:
            error_msg = f"停止调度器失败: {e}"
            handle_error(OCRProcessingError(error_msg))
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
            
            # 更新配置管理器
            self._config_manager.update_config(**kwargs)
            
            # 更新相关组件配置
            config = self._config_manager.get_config()
            self._process_manager.max_processes = config.max_processes
            self._process_manager.process_timeout = config.process_timeout
            self._task_dispatcher.max_concurrent_tasks = config.max_concurrent_tasks
            
            # 发布配置更新事件
            self._event_bus.publish(SchedulerStatusEvent("config_updated", {
                "updated_config": kwargs,
                "current_config": config.to_dict()
            }))
        except Exception as e:
            error_msg = f"更新调度器配置失败: {e}"
            handle_error(OCRConfigError(error_msg, context=kwargs))
            raise
    
    async def submit_task(
        self,
        task_id: str,
        func: Callable[..., Union[T, Awaitable[T]]],
        *args: Any,
        priority: Union[TaskPriority, str] = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
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
                handle_error(OCRProcessingError(error_msg))
                raise RuntimeError(error_msg)
            
            # 处理优先级参数
            if isinstance(priority, str):
                try:
                    priority = TaskPriority[priority.upper()]
                except KeyError:
                    error_msg = f"Invalid priority: {priority}"
                    handle_error(OCRConfigError(error_msg))
                    raise ValueError(error_msg)
            
            # 使用配置中的默认值
            config = self._config_manager.get_config()
            actual_timeout = timeout or config.task_timeout
            actual_max_retries = max_retries or config.retry_count
            
            # 提交任务到分发器
            self._task_dispatcher.submit_task(
                task_id=task_id,
                func=func,
                priority=priority,
                timeout=actual_timeout,
                max_retries=actual_max_retries,
                *args,
                **kwargs
            )
            
            # 发布任务提交事件
            task_data: Dict[str, Any] = {
                "func_name": getattr(func, "__name__", str(func)),
                "priority": priority.name if hasattr(priority, "name") else str(priority),
                "timeout": actual_timeout,
                "max_retries": actual_max_retries,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
            self._event_bus.publish(TaskSubmittedEvent(task_id, task_data))
            
            # 立即分发任务
            await self._task_dispatcher.dispatch_next_task()
            
            # 注意：当前设计中无法直接返回任务结果
            # 需要通过其他机制（如回调或Future）来获取结果
            warning("submit_task result handling needs refinement in current design")
            return None
        except Exception as e:
            error_msg = f"提交任务失败: {e}"
            handle_error(OCRProcessingError(error_msg, context={"task_id": task_id, "priority": priority}))
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        try:
            config = self._config_manager.get_config()
            return {
                'is_running': self._is_running,
                'active_processes': self._process_manager.get_active_process_count(),
                'active_tasks': self._task_dispatcher.get_active_task_count(),
                'completed_tasks': self._task_dispatcher.get_completed_task_count(),
                'failed_tasks': self._task_dispatcher.get_failed_task_count(),
                'queue_size': self._task_dispatcher.get_queue_size(),
                'tick_stats': self._tick_component.get_stats(),
                'config': config.to_dict()
            }
        except Exception as e:
            error_msg = f"获取调度器状态失败: {e}"
            handle_error(OCRProcessingError(error_msg))
            return {}
    
    async def run_scheduler_loop(self) -> None:
        """运行调度器主循环"""
        try:
            if not self._is_running:
                error_msg = "Scheduler is not running. Call start() first."
                handle_error(OCRProcessingError(error_msg))
                raise RuntimeError(error_msg)
            
            info("Starting scheduler main loop")
            
            while self._is_running:
                # 分发任务
                while (self._task_dispatcher.get_queue_size() > 0 and 
                       self._task_dispatcher.get_active_task_count() < self._task_dispatcher.max_concurrent_tasks):
                    await self._task_dispatcher.dispatch_next_task()
                
                # 短暂休眠以避免CPU占用过高
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            info("Scheduler loop cancelled")
        except Exception as e:
            error_msg = f"Error in scheduler loop: {e}"
            handle_error(OCRProcessingError(error_msg))
            raise
        finally:
            info("Scheduler loop ended")
    
    async def wait_for_completion(self) -> None:
        """等待所有任务完成"""
        try:
            await self._task_dispatcher.wait_for_completion()
        except Exception as e:
            error_msg = f"等待任务完成失败: {e}"
            handle_error(OCRProcessingError(error_msg))
            raise