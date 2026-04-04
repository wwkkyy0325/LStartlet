#!/usr/bin/env python3
"""
Persistence Manager Unit Tests
Test the PersistenceManager class functionality
"""

import sys
import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from LStartlet.core.persistence.persistence_manager import PersistenceManager
from LStartlet.core.persistence.models.persistence_models import StorageConfig


class TestPersistenceManager(unittest.TestCase):
    """测试 PersistenceManager 类"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, "test_data")
        
        # 重置配置
        from LStartlet.core.config import reset_all_configs
        reset_all_configs()

    def tearDown(self):
        """测试后清理"""
        from LStartlet.core.config import reset_all_configs
        reset_all_configs()
        
        # 清理临时目录
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """测试持久化管理器初始化"""
        manager = PersistenceManager(self.data_dir)
        
        self.assertEqual(manager._data_dir, self.data_dir)
        self.assertEqual(manager._storages, {})
        self.assertFalse(manager._is_initialized)
        self.assertTrue(os.path.exists(self.data_dir))

    def test_initialize_success(self):
        """测试成功初始化"""
        manager = PersistenceManager(self.data_dir)
        
        result = manager.initialize()
        
        self.assertTrue(result)
        self.assertTrue(manager._is_initialized)
        self.assertIn("default", manager._storages)
        self.assertIn("user_preferences", manager._storages)
        self.assertIn("window_state", manager._storages)

    def test_initialize_already_initialized(self):
        """测试重复初始化"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        # 第二次初始化应该返回True
        result = manager.initialize()
        self.assertTrue(result)

    def test_get_storage_success(self):
        """测试成功获取存储"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        storage = manager.get_storage("default")
        self.assertIsNotNone(storage)

    def test_get_storage_not_found(self):
        """测试获取不存在的存储"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        from LStartlet.core.persistence.exceptions.persistence_exceptions import StorageNotFoundError
        
        with self.assertRaises(StorageNotFoundError):
            manager.get_storage("nonexistent")

    def test_get_storage_uninitialized(self):
        """测试未初始化时获取存储"""
        manager = PersistenceManager(self.data_dir)
        
        with self.assertRaises(RuntimeError):
            manager.get_storage("default")

    def test_create_storage_success(self):
        """测试成功创建存储"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        config = StorageConfig(
            name="test_storage",
            storage_type="file",
            path=os.path.join(self.data_dir, "test_storage.yaml")
        )
        
        storage = manager.create_storage(config)
        self.assertIsNotNone(storage)
        self.assertIn("test_storage", manager._storages)

    def test_create_storage_duplicate(self):
        """测试创建重复存储"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        config = StorageConfig(
            name="test_duplicate",
            storage_type="file",
            path=os.path.join(self.data_dir, "test_duplicate.yaml")
        )
        
        storage1 = manager.create_storage(config)
        storage2 = manager.create_storage(config)
        
        self.assertIs(storage1, storage2)  # 应该返回同一个实例

    def test_create_storage_uninitialized(self):
        """测试未初始化时创建存储"""
        manager = PersistenceManager(self.data_dir)
        
        config = StorageConfig(
            name="test",
            storage_type="file",
            path=os.path.join(self.data_dir, "test.yaml")
        )
        
        with self.assertRaises(RuntimeError):
            manager.create_storage(config)

    def test_get_all_storages(self):
        """测试获取所有存储名称"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        storages = manager.get_all_storages()
        expected = ["default", "user_preferences", "window_state"]
        self.assertEqual(set(storages), set(expected))

    def test_get_all_storages_uninitialized(self):
        """测试未初始化时获取所有存储"""
        manager = PersistenceManager(self.data_dir)
        
        with self.assertRaises(RuntimeError):
            manager.get_all_storages()

    def test_close_all_storages(self):
        """测试关闭所有存储"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        # 验证存储存在
        self.assertTrue(manager._is_initialized)
        self.assertGreater(len(manager._storages), 0)
        
        manager.close_all_storages()
        
        # 验证存储已关闭
        self.assertFalse(manager._is_initialized)
        self.assertEqual(manager._storages, {})

    def test_close_all_storages_uninitialized(self):
        """测试未初始化时关闭所有存储"""
        manager = PersistenceManager(self.data_dir)
        
        # 不应该抛出异常
        manager.close_all_storages()

    def test_convenience_methods(self):
        """测试便捷方法"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        # 测试 get/set/delete/exists
        test_key = "test_key"
        test_value = {"data": "value"}
        
        # 设置值
        result = manager.set(test_key, test_value)
        self.assertTrue(result)
        
        # 获取值
        retrieved = manager.get(test_key)
        self.assertEqual(retrieved, test_value)
        
        # 检查存在
        exists = manager.exists(test_key)
        self.assertTrue(exists)
        
        # 删除值
        deleted = manager.delete(test_key)
        self.assertTrue(deleted)
        
        # 验证已删除
        retrieved_after_delete = manager.get(test_key, "default")
        self.assertEqual(retrieved_after_delete, "default")

    def test_user_preference_methods(self):
        """测试用户偏好方法"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        pref_key = "theme"
        pref_value = "dark"
        
        # 设置用户偏好
        result = manager.set_user_preference(pref_key, pref_value)
        self.assertTrue(result)
        
        # 获取用户偏好
        retrieved = manager.get_user_preference(pref_key)
        self.assertEqual(retrieved, pref_value)

    def test_window_state_methods(self):
        """测试窗口状态方法"""
        manager = PersistenceManager(self.data_dir)
        manager.initialize()
        
        window_id = "main_window"
        window_state = {"width": 800, "height": 600}
        
        # 设置窗口状态
        result = manager.set_window_state(window_id, window_state)
        self.assertTrue(result)
        
        # 获取窗口状态
        retrieved = manager.get_window_state(window_id)
        self.assertEqual(retrieved, window_state)

    @patch('LStartlet.core.persistence.storage.kv_storage.KVStorage.initialize')
    def test_initialize_failure(self, mock_kv_init):
        """测试初始化失败"""
        mock_kv_init.return_value = False
        
        manager = PersistenceManager(self.data_dir)
        result = manager.initialize()
        
        self.assertFalse(result)
        self.assertFalse(manager._is_initialized)


if __name__ == "__main__":
    unittest.main()