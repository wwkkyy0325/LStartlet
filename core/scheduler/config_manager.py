"""
调度系统配置管理器
负责配置项的存储、传递和验证
"""

from typing import Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field
import yaml
from pathlib import Path
from typing import Union, Dict, Any


@dataclass
class SchedulerConfig:
    """调度器配置数据类"""
    # 进程相关配置
    max_processes: int = 4
    process_timeout: float = 30.0
    restart_on_failure: bool = True
    
    # 任务相关配置  
    max_concurrent_tasks: int = 10
    task_timeout: float = 60.0
    retry_count: int = 3
    retry_delay: float = 1.0
    
    # 调度策略配置
    scheduling_strategy: str = "round_robin"  # round_robin, priority, fifo
    enable_load_balancing: bool = True
    
    # 日志和监控配置
    enable_logging: bool = True
    log_level: str = "INFO"
    
    # 自定义配置扩展
    custom_config: Dict[str, Any] = field(default_factory=lambda: {})
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'max_processes': self.max_processes,
            'process_timeout': self.process_timeout,
            'restart_on_failure': self.restart_on_failure,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'task_timeout': self.task_timeout,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
            'scheduling_strategy': self.scheduling_strategy,
            'enable_load_balancing': self.enable_load_balancing,
            'enable_logging': self.enable_logging,
            'log_level': self.log_level,
            'custom_config': self.custom_config
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SchedulerConfig':
        """从字典创建配置实例"""
        return cls(**config_dict)
    
    @classmethod
    def from_yaml_file(cls, file_path: Union[str, Path]) -> 'SchedulerConfig':
        """从YAML文件加载配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict: Dict[str, Any] = yaml.safe_load(f) or {}
        return cls.from_dict(config_dict)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        """
        初始化配置管理器
        
        Args:
            config: 调度器配置，如果为None则使用默认配置
        """
        self._config = config or SchedulerConfig()
        self._validators: Dict[str, Callable[[Any], bool]] = {}
        self._setup_validators()
    
    def _setup_validators(self) -> None:
        """设置配置验证器"""
        self._validators.update({
            'max_processes': lambda x: isinstance(x, int) and x > 0,
            'process_timeout': lambda x: isinstance(x, (int, float)) and x > 0,
            'max_concurrent_tasks': lambda x: isinstance(x, int) and x > 0,
            'task_timeout': lambda x: isinstance(x, (int, float)) and x > 0,
            'retry_count': lambda x: isinstance(x, int) and x >= 0,
            'retry_delay': lambda x: isinstance(x, (int, float)) and x >= 0,
            'scheduling_strategy': lambda x: x in ['round_robin', 'priority', 'fifo']
        })
    
    def get_config(self) -> SchedulerConfig:
        """获取当前配置"""
        return self._config
    
    def update_config(self, **kwargs: Any) -> None:
        """
        更新配置
        
        Args:
            **kwargs: 配置项键值对
        """
        for key, value in kwargs.items():
            if not hasattr(self._config, key):
                raise ValueError(f"Unknown configuration key: {key}")
            
            # 验证配置值
            if key in self._validators:
                if not self._validators[key](value):
                    raise ValueError(f"Invalid value for {key}: {value}")
            
            setattr(self._config, key, value)
    
    def validate_config(self) -> bool:
        """验证当前配置的有效性"""
        try:
            for key, validator in self._validators.items():
                value = getattr(self._config, key)
                if not validator(value):
                    return False
            return True
        except Exception:
            return False
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """保存配置到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config.to_dict(), f, allow_unicode=True, indent=2, sort_keys=False)
