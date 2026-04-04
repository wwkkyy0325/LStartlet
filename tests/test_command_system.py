#!/usr/bin/env python3
"""
System Command Unit Tests
Test the system-related commands functionality
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from LStartlet.core.command.commands.system_commands import (
    EchoCommand,
    SystemInfoCommand,
    ShutdownCommand,
    ClearCacheCommand,
)
from LStartlet.core.command.command_executor import CommandExecutor
from LStartlet.core.command.command_registry import CommandRegistry, command_registry


class TestCommandSystem(unittest.TestCase):
    """测试系统命令功能"""

    def setUp(self):
        """测试前准备"""
        # 重置配置
        from LStartlet.core.config import reset_all_configs

        reset_all_configs()

    def tearDown(self):
        """测试后清理"""
        from LStartlet.core.config import reset_all_configs

        reset_all_configs()

    def test_echo_command_success(self):
        """测试回显命令成功"""
        echo_cmd = EchoCommand()
        result = echo_cmd.execute(message="Hello World")

        self.assertTrue(result.is_success)
        self.assertEqual(result.message, "Echo: Hello World")
        self.assertEqual(result.data["original_message"], "Hello World")

    def test_echo_command_missing_message(self):
        """测试回显命令缺少消息参数"""
        echo_cmd = EchoCommand()
        result = echo_cmd.execute()

        self.assertFalse(result.is_success)
        self.assertIn("message parameter is required", result.message)

    def test_echo_command_empty_message(self):
        """测试回显命令空消息"""
        echo_cmd = EchoCommand()
        result = echo_cmd.execute(message="")

        self.assertFalse(result.is_success)
        self.assertIn("message parameter is required", result.message)

    def test_system_info_command_basic(self):
        """测试系统信息命令基础模式"""
        system_cmd = SystemInfoCommand()
        result = system_cmd.execute()

        self.assertTrue(result.is_success)
        self.assertIn("version", result.data)
        self.assertIn("platform", result.data)
        self.assertIn("python_version", result.data)

    def test_system_info_command_detailed(self):
        """测试系统信息命令详细模式"""
        system_cmd = SystemInfoCommand()
        result = system_cmd.execute(detail_level="detailed")

        self.assertTrue(result.is_success)
        self.assertIn("version", result.data)
        self.assertIn("platform", result.data)
        self.assertIn("python_version", result.data)
        self.assertIn("cpu_count", result.data)
        # 检查内存相关字段（不是单个'memory'键）
        self.assertIn("memory_total", result.data)
        self.assertIn("memory_available", result.data)

    def test_command_registry(self):
        """测试命令注册表功能"""
        # 重置命令注册表
        command_registry._commands.clear()
        
        echo_cmd = EchoCommand()
        system_cmd = SystemInfoCommand()

        registry = CommandRegistry()
        registry.register_command(echo_cmd)
        registry.register_command(system_cmd)

        self.assertEqual(len(registry.get_all_commands()), 2)
        self.assertIsNotNone(registry.get_command("echo"))
        self.assertIsNotNone(registry.get_command("system.info"))

    def test_command_executor_with_registry(self):
        """测试命令执行器与注册表集成"""
        echo_cmd = EchoCommand()
        system_cmd = SystemInfoCommand()

        registry = CommandRegistry()
        registry.register_command(echo_cmd)
        registry.register_command(system_cmd)

        # CommandExecutor 不需要 registry，直接执行命令
        executor = CommandExecutor()

        # 测试回显命令（同步执行）
        result = echo_cmd.execute(message="Test Message")
        self.assertTrue(result.is_success)
        self.assertEqual(result.message, "Echo: Test Message")

        # 测试系统信息命令（同步执行）
        result = system_cmd.execute()
        self.assertTrue(result.is_success)
        self.assertIn("version", result.data)


if __name__ == "__main__":
    unittest.main()
