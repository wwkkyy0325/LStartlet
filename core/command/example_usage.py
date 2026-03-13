"""
命令系统使用示例
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import asyncio
from core.logger import configure_logger, info, error
from core.command import CommandExecutor, command_registry
from core.command.commands.system_commands import SystemInfoCommand, EchoCommand


async def main():
    """主函数示例"""
    # 配置日志
    configure_logger()
    
    # 创建命令执行器
    executor = CommandExecutor()
    
    # 注册命令
    system_info_cmd = SystemInfoCommand()
    echo_cmd = EchoCommand()
    
    command_registry.register_command(system_info_cmd)
    command_registry.register_command(echo_cmd)
    
    info("Starting command system example")
    
    try:
        # 执行系统信息命令
        result1 = await executor.execute_command(system_info_cmd, detail_level="basic")
        if result1.is_success:
            info(f"System info: {result1.data}")
        else:
            error(f"System info failed: {result1.message}")
        
        # 执行回显命令
        result2 = await executor.execute_command(echo_cmd, message="Hello, Command System!")
        if result2.is_success:
            info(f"Echo result: {result2.data}")
        else:
            error(f"Echo failed: {result2.message}")
            
    except Exception as e:
        error(f"Example execution failed: {str(e)}")
    finally:
        # 关闭执行器
        executor.shutdown()
        info("Command system example completed")


if __name__ == "__main__":
    asyncio.run(main())