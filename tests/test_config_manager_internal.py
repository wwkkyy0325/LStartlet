#!/usr/bin/env python3
"""
ConfigManager Internal Methods Unit Tests
Test internal methods of ConfigManager that are not exposed in __init__.py
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config.config_manager import ConfigManager


class TestConfigManagerInternalMethods(unittest.TestCase):
    """测试 ConfigManager 的内部方法"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager()
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_register_config_with_source(self):
        """测试 register_config_with_source 方法"""
        # 注册带来源的配置项
        self.config_manager.register_config_with_source(
            key="test_internal_config",
            default_value="internal_value",
            value_type=str,
            description="Internal test config",
            plugin_name="test_plugin"
        )
        
        # 验证配置项存在
        self.assertTrue(self.config_manager.has_config("test_internal_config"))
        self.assertEqual(self.config_manager.get_config("test_internal_config"), "internal_value")
        
        # 验证来源正确
        source = self.config_manager.get_config_source("test_internal_config")
        self.assertEqual(source, "test_plugin")
    
    def test_get_config_source(self):
        """测试 get_config_source 方法"""
        # 系统配置项应该有 "system" 来源
        system_source = self.config_manager.get_config_source("log_level")
        self.assertEqual(system_source, "system")
        
        # 外部配置项应该有 "external" 来源 - 使用一个不会与系统默认值冲突的键名
        self.config_manager.register_config(
            key="unique_external_test_config_12345",
            default_value="external_value_unique",
            value_type=str,
            description="External test config"
        )
        external_source = self.config_manager.get_config_source("unique_external_test_config_12345")
        self.assertEqual(external_source, "external")
        
        # 不存在的配置项应该返回 None
        non_existent_source = self.config_manager.get_config_source("non_existent_config")
        self.assertIsNone(non_existent_source)
    
    def test_get_all_configs_by_source(self):
        """测试 get_all_configs_by_source 方法"""
        # 添加一个插件配置项
        self.config_manager.register_config_with_source(
            key="plugin_test_config",
            default_value="plugin_value",
            value_type=str,
            description="Plugin test config",
            plugin_name="test_plugin"
        )
        
        # 添加一个外部配置项（使用唯一键名避免与系统配置冲突）
        self.config_manager.register_config(
            key="unique_external_test_config_67890",
            default_value="external_value_unique",
            value_type=str,
            description="External test config"
        )
        
        # 获取按来源分类的所有配置
        configs_by_source = self.config_manager.get_all_configs_by_source()
        
        # 验证结构
        self.assertIsInstance(configs_by_source, dict)
        self.assertIn("system", configs_by_source)
        self.assertIn("external", configs_by_source)
        self.assertIn("test_plugin", configs_by_source)
        
        # 验证系统配置存在
        system_configs = configs_by_source["system"]
        self.assertIn("log_level", system_configs)
        self.assertIn("app_name", system_configs)
        
        # 验证外部配置存在
        external_configs = configs_by_source["external"]
        self.assertIn("unique_external_test_config_67890", external_configs)
        
        # 验证插件配置存在
        plugin_configs = configs_by_source["test_plugin"]
        self.assertIn("plugin_test_config", plugin_configs)


if __name__ == '__main__':
    unittest.main()