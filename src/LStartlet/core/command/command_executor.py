import asyncio
import time
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from LStartlet.core.logger import debug, info, warning, error
from LStartlet.core.error import log_error, get_error_info
from LStartlet.core.event import event_bus
from .command_base import BaseCommand, CommandResult
from .command_events import (
    CommandExecutionEvent,
    CommandCompletedEvent,
    CommandFailedEvent,
)
from LStartlet.core.decorators import with_error_handling_async, with_logging_async


class CommandExecutor:
    """命令执行器"""

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._active_commands: Dict[str, asyncio.Future[CommandResult]] = {}

    @with_error_handling_async(
        error_code="COMMAND_EXECUTION_ERROR", default_return=None
    )
    @with_logging_async(level="info", measure_time=True, include_args=True)
    async def execute_command(
        self, command: BaseCommand, **kwargs: Any
    ) -> CommandResult:
        """
        异步执行命令

        Args:
            command: 要执行的命令
            **kwargs: 命令参数 (Dict[str, Any])

        Returns:
            CommandResult: 命令执行结果
        """
        command_id = f"{command.name}_{int(time.time() * 1000)}"

        try:
            # 发布命令开始执行事件
            start_event = CommandExecutionEvent(
                command_name=command.name, command_id=command_id, parameters=kwargs
            )
            event_bus.publish(start_event)

            info(f"Starting execution of command: {command.name}")
            debug(f"Command parameters: {kwargs}")

            # 验证参数
            if not command.validate_parameters(**kwargs):
                error_msg = f"Parameter validation failed for command: {command.name}"
                error(error_msg)
                result = CommandResult.failure(error_msg)

                # 发布命令失败事件
                failed_event = CommandFailedEvent(
                    command_name=command.name,
                    command_id=command_id,
                    error_message=error_msg,
                    error_type="ValidationError",
                )
                event_bus.publish(failed_event)

                return result

            # 设置执行状态
            command.set_executing(True)

            # 执行命令（在单独线程中）
            loop = asyncio.get_event_loop()
            timeout_value = kwargs.get("timeout", command.metadata.timeout)
            if not isinstance(timeout_value, (int, float)):
                timeout_value = command.metadata.timeout

            try:
                # 在线程池中执行命令
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self._executor, self._execute_command_sync, command, kwargs
                    ),
                    timeout=timeout_value,
                )

                # 发布命令完成事件
                completed_event = CommandCompletedEvent(
                    command_name=command.name,
                    command_id=command_id,
                    result=result,
                    execution_time=time.time() - start_event.timestamp,
                )
                event_bus.publish(completed_event)

                info(f"Command {command.name} executed successfully")
                return result

            except asyncio.TimeoutError:
                timeout_msg = (
                    f"Command {command.name} timed out after {timeout_value} seconds"
                )
                warning(timeout_msg)
                result = CommandResult.failure(timeout_msg)

                # 发布命令失败事件
                failed_event = CommandFailedEvent(
                    command_name=command.name,
                    command_id=command_id,
                    error_message=timeout_msg,
                    error_type="TimeoutError",
                )
                event_bus.publish(failed_event)

                return result

            except Exception as e:
                error_msg = f"Error executing command {command.name}: {str(e)}"
                error(error_msg)
                log_error(e, {"command": command.name, "parameters": kwargs})

                result = CommandResult.failure(error_msg, e)

                # 发布命令失败事件
                failed_event = CommandFailedEvent(
                    command_name=command.name,
                    command_id=command_id,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    error_details=get_error_info(e),
                )
                event_bus.publish(failed_event)

                return result

        finally:
            # 清理执行状态和活跃命令
            command.set_executing(False)
            if command_id in self._active_commands:
                del self._active_commands[command_id]

    def _execute_command_sync(
        self, command: BaseCommand, kwargs: Dict[str, Any]
    ) -> CommandResult:
        """
        同步执行命令（在线程池中调用）

        Args:
            command: 要执行的命令
            kwargs: 命令参数

        Returns:
            CommandResult: 命令执行结果
        """
        try:
            return command.execute(**kwargs)
        except Exception as e:
            error(f"Exception in synchronous command execution: {str(e)}")
            return CommandResult.failure(f"Command execution failed: {str(e)}", e)

    def cancel_command(self, command_id: str) -> bool:
        """
        取消正在执行的命令

        Args:
            command_id: 命令ID

        Returns:
            bool: 是否成功取消
        """
        if command_id in self._active_commands:
            future: asyncio.Future[CommandResult] = self._active_commands[command_id]
            if not future.done():
                future.cancel()
                info(f"Command {command_id} cancelled")
                return True
        return False

    def get_active_commands(self) -> List[str]:
        """
        获取所有活跃命令的ID

        Returns:
            List[str]: 活跃命令ID列表
        """
        return list(self._active_commands.keys())

    def shutdown(self) -> None:
        """关闭执行器"""
        info("Shutting down command executor")
        self._executor.shutdown(wait=True)
