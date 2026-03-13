import platform
import psutil
import os
from typing import Any, Dict
from core.logger import info
from ..command_base import BaseCommand, CommandResult, CommandMetadata


class SystemInfoCommand(BaseCommand):
    """系统信息命令"""
    
    def __init__(self):
        metadata = CommandMetadata(
            name="system.info",
            description="获取系统信息",
            category="system",
            version="1.0.0",
            author="OCR System",
            parameters={
                "required": [],
                "optional": ["detail_level"]
            }
        )
        super().__init__(metadata)
    
    def execute(self, **kwargs: Any) -> CommandResult:
        """执行系统信息命令"""
        try:
            detail_level = kwargs.get("detail_level", "basic")
            
            system_info: Dict[str, Any] = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "processor": platform.processor(),
                "machine": platform.machine(),
                "node": platform.node(),
            }
            
            if detail_level == "detailed":
                # 获取详细的系统信息
                detailed_info: Dict[str, Any] = {
                    "cpu_count": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory": dict(psutil.virtual_memory()._asdict()),
                    "disk_usage": dict(psutil.disk_usage('/')._asdict()) if os.name != 'nt' else dict(psutil.disk_usage('C:\\')._asdict()),
                    "boot_time": psutil.boot_time(),
                }
                system_info.update(detailed_info)
            
            info(f"System info command executed with detail level: {detail_level}")
            return CommandResult.success("System information retrieved successfully", system_info)
            
        except Exception as e:
            return CommandResult.failure(f"Failed to retrieve system information: {str(e)}", e)


class EchoCommand(BaseCommand):
    """回显命令"""
    
    def __init__(self):
        metadata = CommandMetadata(
            name="echo",
            description="回显输入的消息",
            category="utility",
            version="1.0.0",
            author="OCR System",
            parameters={
                "required": ["message"],
                "optional": []
            }
        )
        super().__init__(metadata)
    
    def execute(self, **kwargs: Any) -> CommandResult:
        """执行回显命令"""
        try:
            message = kwargs.get("message", "")
            if not message:
                return CommandResult.failure("Message parameter is required")
            
            echo_result = f"Echo: {message}"
            info(f"Echo command executed: {message}")
            return CommandResult.success(echo_result, {"original_message": message, "echoed_message": echo_result})
            
        except Exception as e:
            return CommandResult.failure(f"Echo command failed: {str(e)}", e)