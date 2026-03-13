"""
调度系统事件定义
定义调度器相关的各种事件类型
"""

from typing import Dict, Any, Optional, Type, Callable
from ..base_event import BaseEvent


class SchedulerStatusEvent(BaseEvent):
    """调度器状态事件"""
    
    EVENT_TYPE = "scheduler.status"
    
    def __init__(self, status: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化调度器状态事件
        
        Args:
            status: 状态类型 ('started', 'stopped', 'paused', 'resumed', 'config_updated')
            details: 状态详细信息
        """
        super().__init__(self.EVENT_TYPE)
        self.status = status
        self.details = details or {}
    
    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷"""
        return {
            "status": self.status,
            "details": self.details
        }


class ApplicationLifecycleEvent(BaseEvent):
    """应用程序生命周期事件 - 用于通知应用程序的启动、关闭等生命周期阶段"""
    
    EVENT_TYPE = "application.lifecycle"
    
    def __init__(self, lifecycle_stage: str, reason: Optional[str] = None):
        """
        初始化应用程序生命周期事件
        
        Args:
            lifecycle_stage: 生命周期阶段 ('starting', 'started', 'stopping', 'stopped')
            reason: 关闭原因（仅在stopping/stopped时使用）
        """
        super().__init__(self.EVENT_TYPE)
        self.lifecycle_stage = lifecycle_stage
        self.reason = reason
    
    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷"""
        return {
            "lifecycle_stage": self.lifecycle_stage,
            "reason": self.reason
        }


class ConfigItemRegisteredEvent(BaseEvent):
    """配置项注册事件 - 在配置项读取前触发，允许外部模块注册自定义配置项"""
    
    EVENT_TYPE = "scheduler.config.item.registered"
    
    def __init__(self, config_manager: Any, plugin_name: Optional[str] = None):
        """
        初始化配置项注册事件
        
        Args:
            config_manager: 配置管理器实例，用于注册配置项
            plugin_name: 插件名称，用于标识配置项来源（可选）
        """
        super().__init__(self.EVENT_TYPE)
        self.config_manager = config_manager
        self.plugin_name = plugin_name
    
    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷"""
        return {
            "config_manager": self.config_manager,
            "plugin_name": self.plugin_name
        }
    
    def register_config(self, key: str, default_value: Any, value_type: Type[Any], 
                      description: str = "", validator: Optional[Callable[[Any], bool]] = None,
                      plugin_name: Optional[str] = None) -> None:
        """
        便捷方法：通过事件直接注册配置项
        
        Args:
            key: 配置项键名
            default_value: 默认值
            value_type: 值类型
            description: 描述信息
            validator: 自定义验证器函数
            plugin_name: 插件名称（如果未提供，则使用事件中的plugin_name）
        """
        actual_plugin_name = plugin_name or self.plugin_name
        self.config_manager.register_config_with_source(
            key, default_value, value_type, description, validator, actual_plugin_name
        )


class TaskEvent(BaseEvent):
    """任务事件基类"""
    
    def __init__(self, event_type: str, task_id: str, event_subtype: str, task_data: Optional[Dict[str, Any]] = None):
        """
        初始化任务事件
        
        Args:
            event_type: 事件类型
            task_id: 任务ID
            event_subtype: 事件子类型
            task_data: 任务相关数据
        """
        super().__init__(event_type)
        self.task_id = task_id
        self.event_subtype = event_subtype
        self.task_data = task_data or {}
    
    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷"""
        return {
            "task_id": self.task_id,
            "event_subtype": self.event_subtype,
            "task_data": self.task_data
        }


class TaskSubmittedEvent(TaskEvent):
    """任务提交事件"""
    
    EVENT_TYPE = "scheduler.task.submitted"
    
    def __init__(self, task_id: str, task_data: Optional[Dict[str, Any]] = None):
        super().__init__(self.EVENT_TYPE, task_id, "submitted", task_data)


class TaskStartedEvent(TaskEvent):
    """任务开始执行事件"""
    
    EVENT_TYPE = "scheduler.task.started"
    
    def __init__(self, task_id: str, task_data: Optional[Dict[str, Any]] = None):
        super().__init__(self.EVENT_TYPE, task_id, "started", task_data)


class TaskCompletedEvent(TaskEvent):
    """任务完成事件"""
    
    EVENT_TYPE = "scheduler.task.completed"
    
    def __init__(self, task_id: str, result: Any = None, task_data: Optional[Dict[str, Any]] = None):
        super().__init__(self.EVENT_TYPE, task_id, "completed", task_data)
        self.result = result
    
    def get_payload(self) -> Dict[str, Any]:
        payload = super().get_payload()
        payload["result"] = self.result
        return payload


class TaskFailedEvent(TaskEvent):
    """任务失败事件"""
    
    EVENT_TYPE = "scheduler.task.failed"
    
    def __init__(self, task_id: str, error_message: str, task_data: Optional[Dict[str, Any]] = None):
        super().__init__(self.EVENT_TYPE, task_id, "failed", task_data)
        self.error_message = error_message
    
    def get_payload(self) -> Dict[str, Any]:
        payload = super().get_payload()
        payload["error_message"] = self.error_message
        return payload


class ProcessEvent(BaseEvent):
    """进程事件基类"""
    
    def __init__(self, event_type: str, process_id: int, event_subtype: str, process_data: Optional[Dict[str, Any]] = None):
        """
        初始化进程事件
        
        Args:
            event_type: 事件类型
            process_id: 进程ID
            event_subtype: 事件子类型
            process_data: 进程相关数据
        """
        super().__init__(event_type)
        self.process_id = process_id
        self.event_subtype = event_subtype
        self.process_data = process_data or {}
    
    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷"""
        return {
            "process_id": self.process_id,
            "event_subtype": self.event_subtype,
            "process_data": self.process_data
        }


class ProcessCreatedEvent(ProcessEvent):
    """进程创建事件"""
    
    EVENT_TYPE = "scheduler.process.created"
    
    def __init__(self, process_id: int, process_data: Optional[Dict[str, Any]] = None):
        super().__init__(self.EVENT_TYPE, process_id, "created", process_data)


class ProcessStartedEvent(ProcessEvent):
    """进程启动事件"""
    
    EVENT_TYPE = "scheduler.process.started"
    
    def __init__(self, process_id: int, process_data: Optional[Dict[str, Any]] = None):
        super().__init__(self.EVENT_TYPE, process_id, "started", process_data)


class ProcessStoppedEvent(ProcessEvent):
    """进程停止事件"""
    
    EVENT_TYPE = "scheduler.process.stopped"
    
    def __init__(self, process_id: int, exit_code: Optional[int] = None, process_data: Optional[Dict[str, Any]] = None):
        super().__init__(self.EVENT_TYPE, process_id, "stopped", process_data)
        self.exit_code = exit_code
    
    def get_payload(self) -> Dict[str, Any]:
        payload = super().get_payload()
        payload["exit_code"] = self.exit_code
        return payload


class ProcessFailedEvent(ProcessEvent):
    """进程失败事件"""
    
    EVENT_TYPE = "scheduler.process.failed"
    
    def __init__(self, process_id: int, error_message: str, process_data: Optional[Dict[str, Any]] = None):
        super().__init__(self.EVENT_TYPE, process_id, "failed", process_data)
        self.error_message = error_message
    
    def get_payload(self) -> Dict[str, Any]:
        payload = super().get_payload()
        payload["error_message"] = self.error_message
        return payload


class TickEvent(BaseEvent):
    """Tick事件"""
    
    EVENT_TYPE = "scheduler.tick"
    
    def __init__(self, tick_count: int, elapsed_time: float, tick_data: Optional[Dict[str, Any]] = None):
        """
        初始化Tick事件
        
        Args:
            tick_count: 当前tick计数
            elapsed_time: 已运行时间
            tick_data: Tick相关数据
        """
        super().__init__(self.EVENT_TYPE)
        self.tick_count = tick_count
        self.elapsed_time = elapsed_time
        self.tick_data = tick_data or {}
    
    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷"""
        return {
            "tick_count": self.tick_count,
            "elapsed_time": self.elapsed_time,
            "tick_data": self.tick_data
        }