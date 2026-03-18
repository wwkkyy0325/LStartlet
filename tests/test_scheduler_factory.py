#!/usr/bin/env python3
"""
SchedulerFactory Unit Tests
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scheduler.scheduler_factory import SchedulerFactory
from core.scheduler.scheduler import Scheduler
from core.scheduler.config_manager import SchedulerConfig


class TestSchedulerFactory(unittest.TestCase):
    """SchedulerFactory类测试"""
    
    def setUp(self):
        """测试前准备"""
        # Mock ProcessManager以避免多进程问题
        self.mock_process_manager_patch = patch('core.scheduler.scheduler.ProcessManager')
        self.mock_process_manager = self.mock_process_manager_patch.start()
        mock_instance = Mock()
        mock_instance.get_active_process_count.return_value = 0
        mock_instance.start.return_value = None
        mock_instance.stop.return_value = None
        self.mock_process_manager.return_value = mock_instance
    
    def tearDown(self):
        """测试后清理"""
        self.mock_process_manager_patch.stop()
    
    def test_create_default_scheduler(self):
        """测试创建默认调度器"""
        scheduler = SchedulerFactory.create_default_scheduler()
        
        self.assertIsInstance(scheduler, Scheduler)
        config = scheduler.config
        self.assertIsInstance(config, SchedulerConfig)
        # 验证是默认配置
        self.assertEqual(config.max_processes, 4)
        self.assertEqual(config.max_concurrent_tasks, 10)
    
    def test_create_scheduler_with_config(self):
        """测试使用指定配置创建调度器"""
        custom_config = SchedulerConfig(
            max_processes=2,
            max_concurrent_tasks=5,
            scheduling_strategy="priority"
        )
        
        scheduler = SchedulerFactory.create_scheduler_with_config(custom_config)
        
        self.assertIsInstance(scheduler, Scheduler)
        actual_config = scheduler.config
        self.assertEqual(actual_config.max_processes, 2)
        self.assertEqual(actual_config.max_concurrent_tasks, 5)
        self.assertEqual(actual_config.scheduling_strategy, "priority")
    
    def test_create_lightweight_scheduler(self):
        """测试创建轻量级调度器"""
        scheduler = SchedulerFactory.create_lightweight_scheduler()
        
        self.assertIsInstance(scheduler, Scheduler)
        config = scheduler.config
        self.assertEqual(config.max_processes, 1)
        self.assertEqual(config.max_concurrent_tasks, 2)
        self.assertEqual(config.process_timeout, 15.0)
        self.assertEqual(config.task_timeout, 30.0)
        self.assertEqual(config.retry_count, 1)
    
    def test_create_high_performance_scheduler(self):
        """测试创建高性能调度器"""
        scheduler = SchedulerFactory.create_high_performance_scheduler()
        
        self.assertIsInstance(scheduler, Scheduler)
        config = scheduler.config
        self.assertEqual(config.max_processes, 8)
        self.assertEqual(config.max_concurrent_tasks, 50)
        self.assertEqual(config.process_timeout, 60.0)
        self.assertEqual(config.task_timeout, 120.0)
        self.assertEqual(config.retry_count, 5)
        self.assertTrue(config.enable_load_balancing)
    
    def test_create_scheduler_from_dict(self):
        """测试从字典配置创建调度器"""
        config_dict: Dict[str, Any] = {
            'max_processes': 3,
            'max_concurrent_tasks': 8,
            'scheduling_strategy': 'fifo',
            'enable_load_balancing': False
        }
        
        scheduler = SchedulerFactory.create_scheduler_from_dict(config_dict)
        
        self.assertIsInstance(scheduler, Scheduler)
        actual_config = scheduler.config
        self.assertEqual(actual_config.max_processes, 3)
        self.assertEqual(actual_config.max_concurrent_tasks, 8)
        self.assertEqual(actual_config.scheduling_strategy, 'fifo')
        self.assertFalse(actual_config.enable_load_balancing)


if __name__ == '__main__':
    unittest.main()