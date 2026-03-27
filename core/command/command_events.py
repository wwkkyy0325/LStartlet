from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time
from core.event.base_event import BaseEvent


@dataclass
class CommandExecutionEvent(BaseEvent):
    """命令开始执行事件"""

    command_name: str
    command_id: str
    parameters: Dict[str, Any] = field(default_factory=lambda: {})
    timestamp: float = field(default_factory=time.time)

    EVENT_TYPE = "command.execution.start"

    def __post_init__(self):
        super().__init__(self.EVENT_TYPE)

    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷数据"""
        return {
            "command_name": self.command_name,
            "command_id": self.command_id,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
        }


@dataclass
class CommandCompletedEvent(BaseEvent):
    """命令执行完成事件"""

    command_name: str
    command_id: str
    result: Any
    execution_time: float
    timestamp: float = field(default_factory=time.time)

    EVENT_TYPE = "command.execution.completed"

    def __post_init__(self):
        super().__init__(self.EVENT_TYPE)

    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷数据"""
        return {
            "command_name": self.command_name,
            "command_id": self.command_id,
            "result": self.result,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
        }


@dataclass
class CommandFailedEvent(BaseEvent):
    """命令执行失败事件"""

    command_name: str
    command_id: str
    error_message: str
    error_type: str
    error_details: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)

    EVENT_TYPE = "command.execution.failed"

    def __post_init__(self):
        super().__init__(self.EVENT_TYPE)

    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷数据"""
        return {
            "command_name": self.command_name,
            "command_id": self.command_id,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "error_details": self.error_details,
            "timestamp": self.timestamp,
        }


@dataclass
class CommandCancelledEvent(BaseEvent):
    """命令被取消事件"""

    command_name: str
    command_id: str
    reason: str = ""
    timestamp: float = field(default_factory=time.time)

    EVENT_TYPE = "command.execution.cancelled"

    def __post_init__(self):
        super().__init__(self.EVENT_TYPE)

    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷数据"""
        return {
            "command_name": self.command_name,
            "command_id": self.command_id,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }
