"""
命令系统公共API
"""

from .command_base import BaseCommand, CommandResult, CommandMetadata
from .command_executor import CommandExecutor
from .command_registry import CommandRegistry, command_registry
from .command_events import (
    CommandExecutionEvent, CommandCompletedEvent, 
    CommandFailedEvent, CommandCancelledEvent
)

# 定义公共API
__all__ = [
    'BaseCommand',
    'CommandResult', 
    'CommandMetadata',
    'CommandExecutor',
    'CommandRegistry',
    'command_registry',
    'CommandExecutionEvent',
    'CommandCompletedEvent',
    'CommandFailedEvent',
    'CommandCancelledEvent'
]