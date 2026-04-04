"""
命令系统公共API

提供命令系统的核心抽象接口和数据类型，用户应继承 BaseCommand 
并使用 register_command 装饰器来定义和注册自定义命令。
"""

from .command_base import BaseCommand, CommandResult, CommandMetadata, CommandParameter

# 定义公共API - 仅暴露抽象接口、数据类型
__all__ = [
    "BaseCommand",
    "CommandResult", 
    "CommandMetadata",
    "CommandParameter",
]