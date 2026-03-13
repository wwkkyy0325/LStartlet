from typing import Dict, Optional, List
from core.logger import info, warning
from .command_base import BaseCommand


class CommandRegistry:
    """命令注册表"""
    
    _instance: Optional['CommandRegistry'] = None
    
    def __new__(cls) -> 'CommandRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._commands = {}
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._commands: Dict[str, BaseCommand] = {}
            self._initialized = True
    
    def register_command(self, command: BaseCommand) -> bool:
        """
        注册命令
        
        Args:
            command: 要注册的命令
            
        Returns:
            bool: 是否注册成功
        """
        if command.name in self._commands:
            warning(f"Command {command.name} already registered, overwriting")
        
        self._commands[command.name] = command
        info(f"Registered command: {command.name}")
        return True
    
    def register_commands(self, commands: List[BaseCommand]) -> int:
        """
        批量注册命令
        
        Args:
            commands: 命令列表
            
        Returns:
            int: 成功注册的命令数量
        """
        count = 0
        for command in commands:
            if self.register_command(command):
                count += 1
        return count
    
    def get_command(self, name: str) -> Optional[BaseCommand]:
        """
        获取命令
        
        Args:
            name: 命令名称
            
        Returns:
            Optional[BaseCommand]: 命令实例，如果不存在则返回None
        """
        return self._commands.get(name)
    
    def get_all_commands(self) -> Dict[str, BaseCommand]:
        """
        获取所有注册的命令
        
        Returns:
            Dict[str, BaseCommand]: 所有命令的字典
        """
        return self._commands.copy()
    
    def get_commands_by_category(self, category: str) -> Dict[str, BaseCommand]:
        """
        根据分类获取命令
        
        Args:
            category: 命令分类
            
        Returns:
            Dict[str, BaseCommand]: 指定分类的命令字典
        """
        return {
            name: cmd for name, cmd in self._commands.items() 
            if cmd.metadata.category == category
        }
    
    def unregister_command(self, name: str) -> bool:
        """
        注销命令
        
        Args:
            name: 命令名称
            
        Returns:
            bool: 是否注销成功
        """
        if name in self._commands:
            del self._commands[name]
            info(f"Unregistered command: {name}")
            return True
        return False
    
    def command_exists(self, name: str) -> bool:
        """
        检查命令是否存在
        
        Args:
            name: 命令名称
            
        Returns:
            bool: 命令是否存在
        """
        return name in self._commands
    
    def get_command_names(self) -> List[str]:
        """
        获取所有命令名称
        
        Returns:
            List[str]: 命令名称列表
        """
        return list(self._commands.keys())
    
    def clear(self) -> None:
        """清空所有注册的命令"""
        self._commands.clear()
        info("Cleared all registered commands")


# 全局命令注册表实例
command_registry = CommandRegistry()