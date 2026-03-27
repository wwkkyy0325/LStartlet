#!/usr/bin/env python3
"""
Configuration Manager Unit Tests
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from LStartlet.core.config import (
    get_config,
    set_config,
    has_config,
    get_all_configs,
    add_config_listener,
    remove_config_listener,
    add_config_key_listener,
    remove_config_key_listener,
    reset_config,
    reset_all_configs,
    get_config_manager,
)


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        # 重置配置管理器状态
        reset_all_configs()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        reset_all_configs()

    def test_basic_config_operations(self):
        """测试基本配置操作"""
        # 测试配置不存在时返回默认值
        self.assertFalse(has_config("log_level"))
        self.assertEqual(get_config("log_level", "DEBUG"), "DEBUG")

        # 测试设置配置
        success: bool = set_config("log_level", "INFO")
        self.assertTrue(success)
        self.assertTrue(has_config("log_level"))
        self.assertEqual(get_config("log_level"), "INFO")

        # 测试重置配置（删除配置项）
        success: bool = reset_config("log_level")
        self.assertTrue(success)
        self.assertFalse(has_config("log_level"))
        self.assertEqual(get_config("log_level", "DEBUG"), "DEBUG")

    def test_config_validation(self):
        """测试配置验证"""
        # 测试有效日志级别
        success: bool = set_config("log_level", "WARNING")
        self.assertTrue(success)

        # 测试无效日志级别
        success: bool = set_config("log_level", "INVALID")
        self.assertFalse(success)
        # 配置应该保持之前的值
        self.assertEqual(get_config("log_level"), "WARNING")

    def test_protected_config(self):
        """测试受保护配置"""
        # 创建系统配置文件来测试受保护配置
        system_config_path = os.path.join(self.temp_dir, "system_config.yaml")
        with open(system_config_path, "w", encoding="utf-8") as f:
            f.write("app_name: TestApp\n")

        # 临时修改项目根目录
        original_root = get_config_manager()._project_root
        get_config_manager()._project_root = self.temp_dir
        get_config_manager()._system_config_path = system_config_path

        try:
            # 重新初始化配置管理器
            reset_all_configs()

            # app_name 应该是受保护的
            self.assertTrue(has_config("app_name"))
            self.assertEqual(get_config("app_name"), "TestApp")

            # 尝试修改受保护配置应该失败
            success: bool = set_config("app_name", "ModifiedApp")
            self.assertFalse(success)
            self.assertEqual(get_config("app_name"), "TestApp")

        finally:
            # 恢复原始项目根目录
            get_config_manager()._project_root = original_root
            get_config_manager()._system_config_path = os.path.join(
                original_root, "system_config.yaml"
            )
            reset_all_configs()

    def test_get_all_configs(self):
        """测试获取所有配置"""
        # 重置配置以确保干净状态
        reset_all_configs()

        # 设置多个配置
        set_config("key1", "value1")
        set_config("key2", 42)
        set_config("key3", True)

        all_configs = get_all_configs()
        # 由于系统配置会自动加载，我们只验证用户设置的配置存在
        self.assertIn("key1", all_configs)
        self.assertIn("key2", all_configs)
        self.assertIn("key3", all_configs)
        self.assertEqual(all_configs["key1"], "value1")
        self.assertEqual(all_configs["key2"], 42)
        self.assertEqual(all_configs["key3"], True)

    def test_config_listeners(self):
        """测试配置监听器"""
        changes = []

        def listener(key, old_value, new_value):
            changes.append((key, old_value, new_value))

        add_config_listener(listener)

        # 设置配置
        set_config("test_key", "test_value")
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], ("test_key", None, "test_value"))

        # 修改配置
        set_config("test_key", "new_value")
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[1], ("test_key", "test_value", "new_value"))

        # 移除监听器
        remove_config_listener(listener)
        set_config("test_key", "final_value")
        self.assertEqual(len(changes), 2)  # 不应该再有变化

        # 测试键特定监听器
        key_changes = []

        def key_listener(key, old_value, new_value):
            key_changes.append((key, old_value, new_value))

        add_config_key_listener("specific_key", key_listener)
        set_config("other_key", "other_value")  # 不应该触发
        set_config("specific_key", "specific_value")  # 应该触发

        self.assertEqual(len(key_changes), 1)
        self.assertEqual(key_changes[0], ("specific_key", None, "specific_value"))

        remove_config_key_listener("specific_key", key_listener)


if __name__ == "__main__":
    unittest.main()
