#!/usr/bin/env python3
"""
ConfigManager and SchedulerConfig Unit Tests
"""

import sys
import unittest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scheduler.config_manager import ConfigManager, SchedulerConfig


class TestSchedulerConfig(unittest.TestCase):
    """SchedulerConfig类测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = SchedulerConfig()
        
        # 验证默认值
        self.assertEqual(config.max_processes, 4)
        self.assertEqual(config.process_timeout, 30.0)
        self.assertTrue(config.restart_on_failure)
        self.assertEqual(config.max_concurrent_tasks, 10)
        self.assertEqual(config.task_timeout, 60.0)
        self.assertEqual(config.retry_count, 3)
        self.assertEqual(config.retry_delay, 1.0)
        self.assertEqual(config.scheduling_strategy, "round_robin")
        self.assertTrue(config.enable_load_balancing)
        self.assertTrue(config.enable_logging)
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.custom_config, {})
    
    def test_config_to_dict(self):
        """测试配置转字典"""
        config = SchedulerConfig(
            max_processes=2,
            max_concurrent_tasks=5,
            scheduling_strategy="priority"
        )
        
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict['max_processes'], 2)
        self.assertEqual(config_dict['max_concurrent_tasks'], 5)
        self.assertEqual(config_dict['scheduling_strategy'], "priority")
    
    def test_config_from_dict(self):
        """测试从字典创建配置"""
        config_dict: Dict[str, Any] = {
            'max_processes': 3,
            'process_timeout': 45.0,
            'max_concurrent_tasks': 8,
            'scheduling_strategy': 'fifo'
        }
        
        config = SchedulerConfig.from_dict(config_dict)
        
        self.assertEqual(config.max_processes, 3)
        self.assertEqual(config.process_timeout, 45.0)
        self.assertEqual(config.max_concurrent_tasks, 8)
        self.assertEqual(config.scheduling_strategy, 'fifo')
    
    @unittest.skipIf(sys.platform == "win32", "Windows系统上文件操作可能不稳定")
    def test_config_from_yaml_file(self):
        """测试从YAML文件加载配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_content = """
max_processes: 6
process_timeout: 25.0
max_concurrent_tasks: 15
scheduling_strategy: priority
custom_config:
  custom_key: custom_value
"""
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            config = SchedulerConfig.from_yaml_file(temp_file)
            
            self.assertEqual(config.max_processes, 6)
            self.assertEqual(config.process_timeout, 25.0)
            self.assertEqual(config.max_concurrent_tasks, 15)
            self.assertEqual(config.scheduling_strategy, "priority")
            self.assertEqual(config.custom_config["custom_key"], "custom_value")
        finally:
            os.unlink(temp_file)


class TestConfigManager(unittest.TestCase):
    """ConfigManager类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config_manager = ConfigManager()
    
    def test_get_config(self):
        """测试获取配置"""
        config = self.config_manager.get_config()
        self.assertIsInstance(config, SchedulerConfig)
    
    def test_update_config_valid_values(self):
        """测试更新有效配置值"""
        self.config_manager.update_config(
            max_processes=8,
            max_concurrent_tasks=20,
            scheduling_strategy="priority"
        )
        
        config = self.config_manager.get_config()
        self.assertEqual(config.max_processes, 8)
        self.assertEqual(config.max_concurrent_tasks, 20)
        self.assertEqual(config.scheduling_strategy, "priority")
    
    def test_update_config_invalid_values(self):
        """测试更新无效配置值"""
        # 测试无效的max_processes
        with self.assertRaises(ValueError):
            self.config_manager.update_config(max_processes=-1)
        
        # 测试无效的scheduling_strategy
        with self.assertRaises(ValueError):
            self.config_manager.update_config(scheduling_strategy="invalid_strategy")
        
        # 测试未知配置键
        with self.assertRaises(ValueError):
            self.config_manager.update_config(unknown_key="value")
    
    def test_validate_config(self):
        """测试配置验证"""
        # 验证默认配置是有效的
        self.assertTrue(self.config_manager.validate_config())
    
    @unittest.skipIf(sys.platform == "win32", "Windows系统上文件操作可能不稳定")
    def test_save_to_file(self):
        """测试保存配置到文件"""
        # 修改一些配置
        self.config_manager.update_config(
            max_processes=5,
            max_concurrent_tasks=12,
            custom_config={"test_key": "test_value"}
        )
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            self.config_manager.save_to_file(temp_file)
            
            # 重新加载配置验证
            loaded_config = SchedulerConfig.from_yaml_file(temp_file)
            
            self.assertEqual(loaded_config.max_processes, 5)
            self.assertEqual(loaded_config.max_concurrent_tasks, 12)
            self.assertEqual(loaded_config.custom_config["test_key"], "test_value")
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()