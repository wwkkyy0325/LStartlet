#!/usr/bin/env python3
"""
配置管理器单元测试
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import Any, List, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import (
    get_config, set_config, has_config, get_all_configs,
    register_config, save_config, load_config, reset_config,
    reset_all_configs
)


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        # 临时修改配置路径（如果需要）
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_config_operations(self):
        """测试基本配置操作"""
        # 测试默认配置
        self.assertTrue(has_config("log_level"))
        self.assertEqual(get_config("log_level"), "DEBUG")
        
        # 测试设置配置
        success: bool = set_config("log_level", "INFO")
        self.assertTrue(success)
        self.assertEqual(get_config("log_level"), "INFO")
        
        # 测试重置配置
        success: bool = reset_config("log_level")
        self.assertTrue(success)
        self.assertEqual(get_config("log_level"), "DEBUG")
    
    def test_register_new_config(self):
        """测试注册新配置"""
        test_key = "test_custom_config_12345"  # 使用唯一键名避免冲突
        test_value = "custom_value"
        
        # 确保配置不存在
        self.assertFalse(has_config(test_key))
        
        # 注册新配置
        register_config(test_key, test_value, type(test_value))
        
        # 验证配置存在且值正确
        self.assertTrue(has_config(test_key))
        self.assertEqual(get_config(test_key), test_value)
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试有效的日志级别
        success: bool = set_config("log_level", "ERROR")
        self.assertTrue(success)
        
        # 测试无效的日志级别
        success: bool = set_config("log_level", "INVALID_LEVEL")
        self.assertFalse(success)
        
        # 测试数值验证
        success: bool = set_config("ocr_confidence_threshold", 0.8)
        self.assertTrue(success)
        
        success: bool = set_config("ocr_confidence_threshold", 1.5)  # 超出范围
        self.assertFalse(success)
    
    def test_get_all_configs(self):
        """测试获取所有配置"""
        all_configs = get_all_configs()
        self.assertIsInstance(all_configs, dict)
        self.assertIn("log_level", all_configs)
        self.assertIn("app_name", all_configs)
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 修改一些配置
        set_config("log_level", "WARNING")
        set_config("debug_mode", True)
        
        # 保存配置到临时目录
        temp_file = os.path.join(self.temp_dir, "test_config.json")
        success = save_config(temp_file)
        self.assertTrue(success)
        
        # 重置配置
        reset_all_configs()
        self.assertEqual(get_config("log_level"), "DEBUG")
        self.assertEqual(get_config("debug_mode"), False)
        
        # 加载配置
        success = load_config(temp_file)
        self.assertTrue(success)
        self.assertEqual(get_config("log_level"), "WARNING")
        self.assertEqual(get_config("debug_mode"), True)
        
        # 不需要额外清理，tearDown会处理temp_dir
    
    def test_config_listeners(self):
        """测试配置监听器"""
        changes: List[Tuple[str, Any, Any]] = []
        
        def listener(key: str, old_value: Any, new_value: Any):
            changes.append((key, old_value, new_value))
        
        # 添加监听器
        from core.config import add_config_key_listener, remove_config_key_listener
        add_config_key_listener("log_level", listener)
        
        # 修改配置
        set_config("log_level", "INFO")
        
        # 验证监听器被调用
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0][0], "log_level")
        self.assertEqual(changes[0][1], "DEBUG")
        self.assertEqual(changes[0][2], "INFO")
        
        # 移除监听器
        success: bool = remove_config_key_listener("log_level", listener)
        self.assertTrue(success)
        
        # 再次修改配置，监听器不应被调用
        set_config("log_level", "ERROR")
        self.assertEqual(len(changes), 1)  # 应该还是1


if __name__ == '__main__':
    unittest.main()