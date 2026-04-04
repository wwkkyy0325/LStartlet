"""测试命令装饰器的功能"""

import unittest
from LStartlet.core.decorators import command as register_command_decorator
from LStartlet.core.command.command_base import BaseCommand, CommandResult, CommandMetadata
from LStartlet.core.command.command_registry import command_registry


class TestCommandDecorator(unittest.TestCase):
    """测试命令装饰器"""

    def setUp(self):
        """测试前清理命令注册表"""
        command_registry._commands.clear()

    def test_command_registration(self):
        """测试命令自动注册"""
        
        @register_command_decorator(name="test_cmd", description="Test command")
        class TestCommand(BaseCommand):
            def __init__(self):
                super().__init__(self._command_metadata)
            
            def execute(self, *args, **kwargs) -> CommandResult:
                return CommandResult(success=True, data="executed")

        # 检查命令是否已注册
        cmd = command_registry.get_command("test_cmd")
        self.assertIsNotNone(cmd)
        self.assertIsInstance(cmd, TestCommand)
        self.assertEqual(cmd.metadata.description, "Test command")

    def test_command_execution(self):
        """测试命令执行"""
        
        @register_command_decorator(name="exec_cmd")
        class ExecCommand(BaseCommand):
            def __init__(self):
                super().__init__(self._command_metadata)
            
            def execute(self, message: str = "hello") -> CommandResult:
                return CommandResult(is_success=True, data=f"received: {message}")

        # 直接获取命令实例并执行
        cmd_instance = command_registry.get_command("exec_cmd")
        result = cmd_instance.execute(message="world")
        self.assertTrue(result.is_success)
        self.assertEqual(result.data, "received: world")


if __name__ == "__main__":
    unittest.main()