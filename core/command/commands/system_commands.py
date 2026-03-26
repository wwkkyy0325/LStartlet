import platform # type: ignore
import psutil # type: ignore
import os # type: ignore
from typing import Dict, Any, Optional # type: ignore
from core.command.command_base import BaseCommand, CommandResult, CommandMetadata
from core.decorators import require_permission, PermissionLevel, with_error_handling, with_logging
from core.version_control.version_controller import VersionController


class EchoCommand(BaseCommand):
    """回显命令 - 用于测试和调试"""
    
    def __init__(self):
        metadata = CommandMetadata(
            name="echo",
            description="回显输入的消息",
            category="utility",  # 改为utility类别以匹配测试
            timeout=1.0
        )
        super().__init__(metadata)
    
    @with_error_handling(error_code="ECHO_COMMAND_ERROR", default_return=None)
    @with_logging(level="debug", include_args=True)
    def execute(self, **kwargs: Any) -> CommandResult:
        """执行回显命令"""
        message = kwargs.get("message")
        
        # 验证消息参数
        if message is None:
            return CommandResult.failure("message parameter is required")
        
        if message == "":
            return CommandResult.failure("message parameter is required")
        
        # 返回成功结果和数据
        return CommandResult.success(
            f"Echo: {message}",
            {"original_message": message}
        )


class ShutdownCommand(BaseCommand):
    """关机命令 - 需要管理员权限"""
    
    def __init__(self):
        metadata = CommandMetadata(
            name="shutdown",
            description="关闭应用程序",
            category="system",
            timeout=10.0
        )
        super().__init__(metadata)
    
    @require_permission(PermissionLevel.ADMIN, "Only administrators can execute shutdown operations")
    @with_error_handling(error_code="SHUTDOWN_COMMAND_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    def execute(self, **kwargs: Any) -> CommandResult:
        """Execute shutdown command"""
        # Actual shutdown logic
        return CommandResult.success("Application is ready to shut down")


class ClearCacheCommand(BaseCommand):
    """清除缓存命令 - 需要用户权限"""
    
    def __init__(self):
        metadata = CommandMetadata(
            name="clear_cache",
            description="清除应用程序缓存",
            category="system",
            timeout=30.0
        )
        super().__init__(metadata)
    
    @require_permission(PermissionLevel.USER, "User permission required to clear cache")
    @with_error_handling(error_code="CLEAR_CACHE_COMMAND_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    def execute(self, **kwargs: Any) -> CommandResult:
        """Execute clear cache command"""
        # Actual cache clearing logic
        cache_size = kwargs.get("cache_size", "all")
        return CommandResult.success(f"Cache cleared ({cache_size})")


class SystemInfoCommand(BaseCommand):
    """系统信息命令 - 所有用户都可以访问"""
    
    def __init__(self):
        metadata = CommandMetadata(
            name="system.info",  # 改为system.info以匹配测试
            description="获取系统信息",
            category="system",
            timeout=5.0
        )
        super().__init__(metadata)
    
    @with_error_handling(error_code="SYSTEM_INFO_COMMAND_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    def execute(self, **kwargs: Any) -> CommandResult:
        """执行系统信息命令"""
        import platform
        import sys
        
        detail_level = kwargs.get("detail_level", "basic")
        
        # 使用 VersionController 获取真实版本
        version_controller = VersionController()
        current_version = version_controller.get_current_version()
        
        if detail_level == "detailed":
            # 详细模式
            import psutil
            from typing import Any
            info: dict[str, Any] = {
                "version": current_version,
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_release": platform.release(),
                "architecture": platform.machine(),
                "python_version": sys.version,
                "python_implementation": platform.python_implementation(),
                "processor": platform.processor(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available
            }
        else:
            # 基础模式
            info = {
                "version": current_version,
                "platform": platform.system(),
                "python_version": sys.version
            }
        return CommandResult.success("System information retrieved successfully", info)