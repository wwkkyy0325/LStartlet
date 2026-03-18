"""
调度器工厂
用于创建不同配置和策略的调度器实例
"""

from typing import Dict, Any
from .scheduler import Scheduler
from .config_manager import SchedulerConfig


class SchedulerFactory:
    """调度器工厂类"""
    
    @staticmethod
    def create_default_scheduler() -> Scheduler:
        """创建默认调度器"""
        config = SchedulerConfig()
        return Scheduler(config)
    
    @staticmethod
    def create_scheduler_with_config(config: SchedulerConfig) -> Scheduler:
        """
        使用指定配置创建调度器
        
        Args:
            config: 调度器配置
            
        Returns:
            调度器实例
        """
        return Scheduler(config)
    
    @staticmethod
    def create_lightweight_scheduler() -> Scheduler:
        """创建轻量级调度器（适用于资源受限环境）"""
        config = SchedulerConfig(
            max_processes=1,
            max_concurrent_tasks=2,
            process_timeout=15.0,
            task_timeout=30.0,
            retry_count=1
        )
        return Scheduler(config)
    
    @staticmethod
    def create_high_performance_scheduler() -> Scheduler:
        """创建高性能调度器（适用于高负载环境）"""
        config = SchedulerConfig(
            max_processes=8,
            max_concurrent_tasks=50,
            process_timeout=60.0,
            task_timeout=120.0,
            retry_count=5,
            enable_load_balancing=True
        )
        return Scheduler(config)
    
    @staticmethod
    def create_scheduler_from_dict(config_dict: Dict[str, Any]) -> Scheduler:
        """
        从字典配置创建调度器
        
        Args:
            config_dict: 配置字典
            
        Returns:
            调度器实例
        """
        config = SchedulerConfig.from_dict(config_dict)
        return Scheduler(config)
    
    @staticmethod
    def create_scheduler_from_file(file_path: str) -> Scheduler:
        """
        从配置文件创建调度器
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            调度器实例
        """
        config = SchedulerConfig.from_yaml_file(file_path)
        return Scheduler(config)