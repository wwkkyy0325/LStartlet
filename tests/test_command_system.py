"""
命令系统单元测试
"""

import asyncio
import unittest
from core.command import CommandExecutor, command_registry
from core.command.commands.system_commands import EchoCommand, SystemInfoCommand


class TestCommandSystem(unittest.TestCase):
    """命令系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 清空命令注册表
        command_registry.clear()
        self.executor = CommandExecutor(max_workers=2)
    
    def tearDown(self):
        """测试后清理"""
        self.executor.shutdown()
    
    def test_echo_command_basic(self):
        """测试回显命令基本功能"""
        echo_cmd = EchoCommand()
        result = echo_cmd.execute(message="test message")
        
        self.assertTrue(result.is_success)
        self.assertIn("Echo: test message", result.message)
        # 使用类型断言
        assert result.data is not None
        self.assertEqual(result.data["original_message"], "test message")
    
    def test_echo_command_empty_message(self):
        """测试回显命令空消息"""
        echo_cmd = EchoCommand()
        result = echo_cmd.execute(message="")
        
        self.assertFalse(result.is_success)
        self.assertIn("required", result.message.lower())
    
    def test_echo_command_missing_message(self):
        """测试回显命令缺少消息参数"""
        echo_cmd = EchoCommand()
        result = echo_cmd.execute()
        
        self.assertFalse(result.is_success)
        self.assertIn("required", result.message.lower())
    
    def test_system_info_command_basic(self):
        """测试系统信息命令基本功能"""
        system_cmd = SystemInfoCommand()
        result = system_cmd.execute()
        
        self.assertTrue(result.is_success)
        # 使用类型断言
        assert result.data is not None
        self.assertIn("platform", result.data)
        self.assertIn("python_version", result.data)
    
    def test_system_info_command_detailed(self):
        """测试系统信息命令详细模式"""
        system_cmd = SystemInfoCommand()
        result = system_cmd.execute(detail_level="detailed")
        
        self.assertTrue(result.is_success)
        # 使用类型断言
        assert result.data is not None
        self.assertIn("cpu_count", result.data)
        self.assertIn("memory", result.data)
    
    def test_command_registry(self):
        """测试命令注册表功能"""
        echo_cmd = EchoCommand()
        system_cmd = SystemInfoCommand()
        
        # 注册命令
        command_registry.register_command(echo_cmd)
        command_registry.register_command(system_cmd)
        
        # 验证注册
        self.assertTrue(command_registry.command_exists("echo"))
        self.assertTrue(command_registry.command_exists("system.info"))
        
        # 获取命令
        retrieved_echo = command_registry.get_command("echo")
        # 使用类型断言确保 retrieved_echo 不为 None
        assert retrieved_echo is not None
        self.assertEqual(retrieved_echo.name, "echo")
        
        # 获取所有命令
        all_commands = command_registry.get_all_commands()
        self.assertEqual(len(all_commands), 2)
        
        # 按分类获取
        utility_commands = command_registry.get_commands_by_category("utility")
        self.assertEqual(len(utility_commands), 1)
        self.assertIn("echo", utility_commands)
    
    async def test_async_command_execution(self):
        """测试异步命令执行"""
        echo_cmd = EchoCommand()
        command_registry.register_command(echo_cmd)
        
        result = await self.executor.execute_command(echo_cmd, message="async test")
        
        self.assertTrue(result.is_success)
        self.assertIn("async test", result.message)
    
    def test_async_command_execution_sync(self):
        """同步方式测试异步命令执行"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            echo_cmd = EchoCommand()
            command_registry.register_command(echo_cmd)
            
            result = loop.run_until_complete(
                self.executor.execute_command(echo_cmd, message="sync async test")
            )
            
            self.assertTrue(result.is_success)
            self.assertIn("sync async test", result.message)
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()