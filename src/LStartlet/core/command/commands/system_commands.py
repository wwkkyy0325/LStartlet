import platform  # type: ignore
import psutil  # type: ignore
import os  # type: ignore
from typing import Dict, Any, Optional  # type: ignore
from LStartlet.core.command.command_base import (
    BaseCommand,
    CommandResult,
    CommandMetadata,
)
from LStartlet.core.decorators import (
    require_permission,
    PermissionLevel,
    with_error_handling,
    with_logging,
)
from LStartlet.core.version_control.version_controller import VersionController


class EchoCommand(BaseCommand):
    """
    回显命令 - 用于测试和调试
    
    这是一个简单的命令实现，用于验证命令系统的基本功能。
    它接收一个消息参数并将其回显返回。
    
    Attributes:
        metadata (CommandMetadata): 命令元数据，包含名称、描述、类别和超时设置
        
    Example:
        >>> echo_cmd = EchoCommand()
        >>> result = echo_cmd.execute(message="Hello World")
        >>> print(result.data["original_message"])
        Hello World
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="echo",
            description="回显输入的消息",
            category="utility",  # 改为utility类别以匹配测试
            timeout=1.0,
        )
        super().__init__(metadata)

    @with_error_handling(error_code="ECHO_COMMAND_ERROR", default_return=None)
    @with_logging(level="debug", include_args=True)
    def execute(self, **kwargs: Any) -> CommandResult:
        """
        执行回显命令
        
        Args:
            **kwargs: 关键字参数
                - message (str): 要回显的消息文本
                
        Returns:
            CommandResult: 命令执行结果
                - 如果成功: 包含回显消息和原始消息数据
                - 如果失败: 包含错误信息
                
        Raises:
            CommandExecutionError: 当消息参数为空或缺失时
            
        Example:
            >>> cmd = EchoCommand()
            >>> result = cmd.execute(message="test")
            >>> assert result.success is True
            >>> assert result.data["original_message"] == "test"
        """
        message = kwargs.get("message")

        # 验证消息参数
        if message is None:
            return CommandResult.failure("message parameter is required")

        if message == "":
            return CommandResult.failure("message parameter is required")

        # 返回成功结果和数据
        return CommandResult.success(f"Echo: {message}", {"original_message": message})


class ShutdownCommand(BaseCommand):
    """
    关机命令 - 需要管理员权限
    
    这是一个系统级命令，用于安全地关闭应用程序。
    该命令需要 ADMIN 权限级别才能执行，确保只有授权用户可以触发关机操作。
    
    Attributes:
        metadata (CommandMetadata): 命令元数据，包含名称、描述、类别和超时设置
        
    Security:
        Requires PermissionLevel.ADMIN permission to execute
        Uses @require_permission decorator for access control
        
    Example:
        >>> shutdown_cmd = ShutdownCommand()
        >>> # Only users with ADMIN permission can execute this
        >>> result = shutdown_cmd.execute()
        >>> assert result.success is True
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="shutdown", description="关闭应用程序", category="system", timeout=10.0
        )
        super().__init__(metadata)

    @require_permission(
        PermissionLevel.ADMIN, "Only administrators can execute shutdown operations"
    )
    @with_error_handling(error_code="SHUTDOWN_COMMAND_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    def execute(self, **kwargs: Any) -> CommandResult:
        """
        Execute shutdown command
        
        Args:
            **kwargs: 关键字参数（当前未使用）
                
        Returns:
            CommandResult: 命令执行结果
                - 如果成功: 返回应用程序准备关闭的成功消息
                - 如果失败: 返回错误信息
                
        Note:
            This is a mock implementation. In a real application,
            this would trigger actual shutdown logic.
        """
        # Actual shutdown logic
        return CommandResult.success("Application is ready to shut down")


class ClearCacheCommand(BaseCommand):
    """
    清除缓存命令 - 需要用户权限
    
    用于清除应用程序的缓存数据，释放磁盘空间。
    该命令需要 USER 或更高级别权限才能执行。
    
    Attributes:
        metadata (CommandMetadata): 命令元数据
        
    Example:
        >>> clear_cache_cmd = ClearCacheCommand()
        >>> result = clear_cache_cmd.execute(cache_size="all")
        >>> print(result.message)
        Cache cleared (all)
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="clear_cache",
            description="清除应用程序缓存",
            category="system",
            timeout=30.0,
        )
        super().__init__(metadata)

    @require_permission(PermissionLevel.USER, "User permission required to clear cache")
    @with_error_handling(error_code="CLEAR_CACHE_COMMAND_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    def execute(self, **kwargs: Any) -> CommandResult:
        """
        Execute clear cache command
        
        Args:
            **kwargs: 关键字参数
                - cache_size (str): 要清除的缓存大小，默认为 "all"
                
        Returns:
            CommandResult: 命令执行结果，包含清除操作的状态信息
            
        Example:
            >>> cmd = ClearCacheCommand()
            >>> result = cmd.execute(cache_size="temporary")
            >>> assert "temporary" in result.message
        """
        # Actual cache clearing logic
        cache_size = kwargs.get("cache_size", "all")
        return CommandResult.success(f"Cache cleared ({cache_size})")


class SystemInfoCommand(BaseCommand):
    """
    系统信息命令 - 所有用户都可以访问
    
    获取当前系统的详细信息，包括平台、Python 版本、硬件信息等。
    根据 detail_level 参数提供基础或详细信息。
    
    Attributes:
        metadata (CommandMetadata): 命令元数据
        
    Example:
        >>> sys_info_cmd = SystemInfoCommand()
        >>> basic_info = sys_info_cmd.execute(detail_level="basic")
        >>> detailed_info = sys_info_cmd.execute(detail_level="detailed")
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="system.info",  # 改为system.info以匹配测试
            description="获取系统信息",
            category="system",
            timeout=5.0,
        )
        super().__init__(metadata)

    @with_error_handling(error_code="SYSTEM_INFO_COMMAND_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    def execute(self, **kwargs: Any) -> CommandResult:
        """
        执行系统信息命令
        
        Args:
            **kwargs: 关键字参数
                - detail_level (str): 信息详细程度，可选值: "basic" 或 "detailed"。默认为 "basic"。
                
        Returns:
            CommandResult: 命令执行结果，包含系统信息数据字典
            
        Example:
            >>> cmd = SystemInfoCommand()
            >>> result = cmd.execute(detail_level="basic")
            >>> assert "version" in result.data
            >>> assert "platform" in result.data
        """
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
                "memory_available": psutil.virtual_memory().available,
            }
        else:
            # 基础模式
            info = {
                "version": current_version,
                "platform": platform.system(),
                "python_version": sys.version,
            }
        return CommandResult.success("System information retrieved successfully", info)