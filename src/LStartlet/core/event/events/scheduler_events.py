"""
调度系统事件定义
定义调度器相关的各种事件类型
"""

from typing import Dict, Any, Optional, Type, Callable
from ..base_event import BaseEvent


class SchedulerStatusEvent(BaseEvent):
    """
    调度器状态事件
    
    用于通知调度器状态变更的事件类。当调度器启动、停止、暂停、恢复或配置更新时触发。
    
    Attributes:
        status (str): 状态类型，可选值包括:
            - 'started': 调度器已启动
            - 'stopped': 调度器已停止  
            - 'paused': 调度器已暂停
            - 'resumed': 调度器已恢复
            - 'config_updated': 配置已更新
        details (Dict[str, Any]): 状态详细信息，包含额外的上下文数据
        
    Event Type:
        EVENT_TYPE = "scheduler.status"
        
    Example:
        >>> event = SchedulerStatusEvent("started", {"uptime": 0})
        >>> print(event.status)
        started
    """

    EVENT_TYPE = "scheduler.status"

    def __init__(self, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化调度器状态事件

        Args:
            status (str): 状态类型 ('started', 'stopped', 'paused', 'resumed', 'config_updated')
            details (Optional[Dict[str, Any]]): 状态详细信息，默认为 None
            
        Example:
            >>> event = SchedulerStatusEvent("started", {"version": "1.0.0"})
        """
        super().__init__(self.EVENT_TYPE)
        self.status = status
        self.details = details or {}

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含状态和详细信息的字典
            
        Example:
            >>> event = SchedulerStatusEvent("started")
            >>> payload = event.get_payload()
            >>> assert payload["status"] == "started"
        """
        return {"status": self.status, "details": self.details}


class ApplicationLifecycleEvent(BaseEvent):
    """
    应用程序生命周期事件 - 用于通知应用程序的启动、关闭等生命周期阶段
    
    在应用程序的关键生命周期节点触发，如启动开始、启动完成、关闭开始、关闭完成等。
    
    Attributes:
        lifecycle_stage (str): 生命周期阶段
        reason (Optional[str]): 关闭原因（仅在stopping/stopped时使用）
        
    Event Type:
        EVENT_TYPE = "application.lifecycle"
        
    Example:
        >>> start_event = ApplicationLifecycleEvent("starting")
        >>> stop_event = ApplicationLifecycleEvent("stopping", "user_request")
    """

    EVENT_TYPE = "application.lifecycle"

    def __init__(self, lifecycle_stage: str, reason: Optional[str] = None) -> None:
        """
        初始化应用程序生命周期事件

        Args:
            lifecycle_stage (str): 生命周期阶段 ('starting', 'started', 'stopping', 'stopped')
            reason (Optional[str]): 关闭原因（仅在stopping/stopped时使用），默认为 None
            
        Example:
            >>> event = ApplicationLifecycleEvent("started")
        """
        super().__init__(self.EVENT_TYPE)
        self.lifecycle_stage = lifecycle_stage
        self.reason = reason

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含生命周期阶段和关闭原因的字典
            
        Example:
            >>> event = ApplicationLifecycleEvent("stopping", "maintenance")
            >>> payload = event.get_payload()
            >>> assert payload["lifecycle_stage"] == "stopping"
        """
        return {"lifecycle_stage": self.lifecycle_stage, "reason": self.reason}


class ConfigItemRegisteredEvent(BaseEvent):
    """
    配置项注册事件 - 在配置项读取前触发，允许外部模块注册自定义配置项
    
    允许插件或其他模块在配置系统初始化时动态注册自己的配置项。
    
    Attributes:
        config_manager (Any): 配置管理器实例，用于注册配置项
        plugin_name (Optional[str]): 插件名称，用于标识配置项来源
        
    Event Type:
        EVENT_TYPE = "scheduler.config.item.registered"
    """

    EVENT_TYPE = "scheduler.config.item.registered"

    def __init__(self, config_manager: Any, plugin_name: Optional[str] = None) -> None:
        """
        初始化配置项注册事件

        Args:
            config_manager (Any): 配置管理器实例，用于注册配置项
            plugin_name (Optional[str]): 插件名称，用于标识配置项来源（可选）
            
        Example:
            >>> event = ConfigItemRegisteredEvent(config_manager, "my_plugin")
        """
        super().__init__(self.EVENT_TYPE)
        self.config_manager = config_manager
        self.plugin_name = plugin_name

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含配置管理器和插件名称的字典
            
        Example:
            >>> event = ConfigItemRegisteredEvent(config_mgr, "test_plugin")
            >>> payload = event.get_payload()
            >>> assert payload["plugin_name"] == "test_plugin"
        """
        return {"config_manager": self.config_manager, "plugin_name": self.plugin_name}

    def register_config(
        self,
        key: str,
        default_value: Any,
        value_type: Type[Any],
        description: str = "",
        validator: Optional[Callable[[Any], bool]] = None,
        plugin_name: Optional[str] = None,
    ) -> None:
        """
        便捷方法：通过事件直接注册配置项

        Args:
            key (str): 配置项键名
            default_value (Any): 默认值
            value_type (Type[Any]): 值类型
            description (str): 描述信息，默认为空字符串
            validator (Optional[Callable[[Any], bool]]): 自定义验证器函数，默认为 None
            plugin_name (Optional[str]): 插件名称（如果未提供，则使用事件中的plugin_name），默认为 None
            
        Example:
            >>> event.register_config(
            ...     "max_workers", 
            ...     4, 
            ...     int, 
            ...     "Maximum number of worker threads"
            ... )
        """
        actual_plugin_name = plugin_name or self.plugin_name
        self.config_manager.register_config_with_source(
            key, default_value, value_type, description, validator, actual_plugin_name
        )


class TaskEvent(BaseEvent):
    """
    任务事件基类
    
    所有任务相关事件的基类，提供通用的任务事件属性和方法。
    
    Attributes:
        task_id (str): 任务ID
        event_subtype (str): 事件子类型
        task_data (Dict[str, Any]): 任务相关数据
    """

    def __init__(
        self,
        event_type: str,
        task_id: str,
        event_subtype: str,
        task_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化任务事件

        Args:
            event_type (str): 事件类型
            task_id (str): 任务ID
            event_subtype (str): 事件子类型
            task_data (Optional[Dict[str, Any]]): 任务相关数据，默认为 None
            
        Example:
            >>> event = TaskEvent("task.custom", "task_123", "custom", {"data": "value"})
        """
        super().__init__(event_type)
        self.task_id = task_id
        self.event_subtype = event_subtype
        self.task_data = task_data or {}

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含任务ID、事件子类型和任务数据的字典
            
        Example:
            >>> event = TaskEvent("test", "123", "test", {"key": "value"})
            >>> payload = event.get_payload()
            >>> assert payload["task_id"] == "123"
        """
        return {
            "task_id": self.task_id,
            "event_subtype": self.event_subtype,
            "task_data": self.task_data,
        }


class TaskSubmittedEvent(TaskEvent):
    """
    任务提交事件
    
    当新任务被提交到调度器时触发。
    
    Event Type:
        EVENT_TYPE = "scheduler.task.submitted"
    """

    EVENT_TYPE = "scheduler.task.submitted"

    def __init__(self, task_id: str, task_data: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化任务提交事件
        
        Args:
            task_id (str): 任务ID
            task_data (Optional[Dict[str, Any]]): 任务相关数据，默认为 None
            
        Example:
            >>> event = TaskSubmittedEvent("task_456", {"priority": "high"})
        """
        super().__init__(self.EVENT_TYPE, task_id, "submitted", task_data)


class TaskStartedEvent(TaskEvent):
    """
    任务开始执行事件
    
    当任务开始执行时触发。
    
    Event Type:
        EVENT_TYPE = "scheduler.task.started"
    """

    EVENT_TYPE = "scheduler.task.started"

    def __init__(self, task_id: str, task_data: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化任务开始事件
        
        Args:
            task_id (str): 任务ID
            task_data (Optional[Dict[str, Any]]): 任务相关数据，默认为 None
            
        Example:
            >>> event = TaskStartedEvent("task_789")
        """
        super().__init__(self.EVENT_TYPE, task_id, "started", task_data)


class TaskCompletedEvent(TaskEvent):
    """
    任务完成事件
    
    当任务成功完成时触发，包含任务执行结果。
    
    Attributes:
        result (Any): 任务执行结果
        
    Event Type:
        EVENT_TYPE = "scheduler.task.completed"
    """

    EVENT_TYPE = "scheduler.task.completed"

    def __init__(
        self,
        task_id: str,
        result: Any = None,
        task_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化任务完成事件
        
        Args:
            task_id (str): 任务ID
            result (Any): 任务执行结果，默认为 None
            task_data (Optional[Dict[str, Any]]): 任务相关数据，默认为 None
            
        Example:
            >>> event = TaskCompletedEvent("task_123", "success_result")
        """
        super().__init__(self.EVENT_TYPE, task_id, "completed", task_data)
        self.result = result

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含任务信息和执行结果的字典
            
        Example:
            >>> event = TaskCompletedEvent("task_123", "result_data")
            >>> payload = event.get_payload()
            >>> assert payload["result"] == "result_data"
        """
        payload = super().get_payload()
        payload["result"] = self.result
        return payload


class TaskFailedEvent(TaskEvent):
    """
    任务失败事件
    
    当任务执行失败时触发，包含错误信息。
    
    Attributes:
        error_message (str): 错误消息
        
    Event Type:
        EVENT_TYPE = "scheduler.task.failed"
    """

    EVENT_TYPE = "scheduler.task.failed"

    def __init__(
        self,
        task_id: str,
        error_message: str,
        task_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化任务失败事件
        
        Args:
            task_id (str): 任务ID
            error_message (str): 错误消息
            task_data (Optional[Dict[str, Any]]): 任务相关数据，默认为 None
            
        Example:
            >>> event = TaskFailedEvent("task_456", "Connection timeout")
        """
        super().__init__(self.EVENT_TYPE, task_id, "failed", task_data)
        self.error_message = error_message

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含任务信息和错误消息的字典
            
        Example:
            >>> event = TaskFailedEvent("task_456", "Error occurred")
            >>> payload = event.get_payload()
            >>> assert "Error occurred" in payload["error_message"]
        """
        payload = super().get_payload()
        payload["error_message"] = self.error_message
        return payload


class ProcessEvent(BaseEvent):
    """
    进程事件基类
    
    所有进程相关事件的基类，提供通用的进程事件属性和方法。
    
    Attributes:
        process_id (int): 进程ID
        event_subtype (str): 事件子类型
        process_data (Dict[str, Any]): 进程相关数据
    """

    def __init__(
        self,
        event_type: str,
        process_id: int,
        event_subtype: str,
        process_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化进程事件

        Args:
            event_type (str): 事件类型
            process_id (int): 进程ID
            event_subtype (str): 事件子类型
            process_data (Optional[Dict[str, Any]]): 进程相关数据，默认为 None
            
        Example:
            >>> event = ProcessEvent("process.test", 1234, "test", {"status": "running"})
        """
        super().__init__(event_type)
        self.process_id = process_id
        self.event_subtype = event_subtype
        self.process_data = process_data or {}

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含进程ID、事件子类型和进程数据的字典
            
        Example:
            >>> event = ProcessEvent("test", 1234, "test", {"key": "value"})
            >>> payload = event.get_payload()
            >>> assert payload["process_id"] == 1234
        """
        return {
            "process_id": self.process_id,
            "event_subtype": self.event_subtype,
            "process_data": self.process_data,
        }


class ProcessCreatedEvent(ProcessEvent):
    """
    进程创建事件
    
    当新进程被创建时触发。
    
    Event Type:
        EVENT_TYPE = "scheduler.process.created"
    """

    EVENT_TYPE = "scheduler.process.created"

    def __init__(self, process_id: int, process_data: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化进程创建事件
        
        Args:
            process_id (int): 进程ID
            process_data (Optional[Dict[str, Any]]): 进程相关数据，默认为 None
            
        Example:
            >>> event = ProcessCreatedEvent(5678, {"name": "worker_process"})
        """
        super().__init__(self.EVENT_TYPE, process_id, "created", process_data)


class ProcessStartedEvent(ProcessEvent):
    """
    进程启动事件
    
    当进程开始运行时触发。
    
    Event Type:
        EVENT_TYPE = "scheduler.process.started"
    """

    EVENT_TYPE = "scheduler.process.started"

    def __init__(self, process_id: int, process_data: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化进程启动事件
        
        Args:
            process_id (int): 进程ID
            process_data (Optional[Dict[str, Any]]): 进程相关数据，默认为 None
            
        Example:
            >>> event = ProcessStartedEvent(5678)
        """
        super().__init__(self.EVENT_TYPE, process_id, "started", process_data)


class ProcessStoppedEvent(ProcessEvent):
    """
    进程停止事件
    
    当进程正常停止时触发，包含退出码信息。
    
    Attributes:
        exit_code (Optional[int]): 进程退出码
        
    Event Type:
        EVENT_TYPE = "scheduler.process.stopped"
    """

    EVENT_TYPE = "scheduler.process.stopped"

    def __init__(
        self,
        process_id: int,
        exit_code: Optional[int] = None,
        process_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化进程停止事件
        
        Args:
            process_id (int): 进程ID
            exit_code (Optional[int]): 进程退出码，默认为 None
            process_data (Optional[Dict[str, Any]]): 进程相关数据，默认为 None
            
        Example:
            >>> event = ProcessStoppedEvent(5678, exit_code=0)
        """
        super().__init__(self.EVENT_TYPE, process_id, "stopped", process_data)
        self.exit_code = exit_code

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含进程信息和退出码的字典
            
        Example:
            >>> event = ProcessStoppedEvent(5678, exit_code=0)
            >>> payload = event.get_payload()
            >>> assert payload["exit_code"] == 0
        """
        payload = super().get_payload()
        payload["exit_code"] = self.exit_code
        return payload


class ProcessFailedEvent(ProcessEvent):
    """
    进程失败事件
    
    当进程异常终止时触发，包含错误信息。
    
    Attributes:
        error_message (str): 错误消息
        
    Event Type:
        EVENT_TYPE = "scheduler.process.failed"
    """

    EVENT_TYPE = "scheduler.process.failed"

    def __init__(
        self,
        process_id: int,
        error_message: str,
        process_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化进程失败事件
        
        Args:
            process_id (int): 进程ID
            error_message (str): 错误消息
            process_data (Optional[Dict[str, Any]]): 进程相关数据，默认为 None
            
        Example:
            >>> event = ProcessFailedEvent(5678, "Memory allocation failed")
        """
        super().__init__(self.EVENT_TYPE, process_id, "failed", process_data)
        self.error_message = error_message

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含进程信息和错误消息的字典
            
        Example:
            >>> event = ProcessFailedEvent(5678, "Process crashed")
            >>> payload = event.get_payload()
            >>> assert "Process crashed" in payload["error_message"]
        """
        payload = super().get_payload()
        payload["error_message"] = self.error_message
        return payload


class TickEvent(BaseEvent):
    """
    Tick事件
    
    定期触发的事件，用于调度器的心跳和定时任务。
    
    Attributes:
        tick_count (int): 当前tick计数
        elapsed_time (float): 已运行时间（秒）
        tick_data (Dict[str, Any]): Tick相关数据
        
    Event Type:
        EVENT_TYPE = "scheduler.tick"
    """

    EVENT_TYPE = "scheduler.tick"

    def __init__(
        self,
        tick_count: int,
        elapsed_time: float,
        tick_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化Tick事件

        Args:
            tick_count (int): 当前tick计数
            elapsed_time (float): 已运行时间（秒）
            tick_data (Optional[Dict[str, Any]]): Tick相关数据，默认为 None
            
        Example:
            >>> event = TickEvent(100, 50.5, {"cpu_usage": 0.3})
        """
        super().__init__(self.EVENT_TYPE)
        self.tick_count = tick_count
        self.elapsed_time = elapsed_time
        self.tick_data = tick_data or {}

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷
        
        Returns:
            Dict[str, Any]: 包含tick计数、运行时间和相关数据的字典
            
        Example:
            >>> event = TickEvent(1, 0.1, {"status": "active"})
            >>> payload = event.get_payload()
            >>> assert payload["tick_count"] == 1
        """
        return {
            "tick_count": self.tick_count,
            "elapsed_time": self.elapsed_time,
            "tick_data": self.tick_data,
        }