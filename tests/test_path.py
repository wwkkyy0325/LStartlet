#!/usr/bin/env python3
"""
路径管理模块单元测试
测试path_manager、constants、utils等核心功能
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.path import (
    get_project_root, get_core_path, get_logger_path, get_error_path,
    get_data_path, get_config_path, get_output_path, get_logs_path,
    join_paths, normalize_path, is_valid_path, ensure_directory_exists,
    PATH_CONSTANTS
)
from core.path.path_manager import PathManager
from core.path.constants import PATH_CONSTANTS as CONSTANTS
from core.path.utils import PathUtils


class TestPathConstants(unittest.TestCase):
    """测试路径常量"""
    
    def test_constants_exist(self):
        """测试路径常量存在"""
        self.assertIn('PROJECT_ROOT', CONSTANTS)
        self.assertIn('CORE_PATH', CONSTANTS)
        self.assertIn('LOGGER_PATH', CONSTANTS)
        self.assertIn('ERROR_PATH', CONSTANTS)
        self.assertIn('DATA_PATH', CONSTANTS)
        self.assertIn('CONFIG_PATH', CONSTANTS)
        self.assertIn('OUTPUT_PATH', CONSTANTS)
        self.assertIn('LOGS_PATH', CONSTANTS)


class TestPathUtils(unittest.TestCase):
    """测试路径工具函数"""
    
    def test_join_paths(self):
        """测试路径拼接"""
        result = join_paths("a", "b", "c")
        expected = str(Path("a") / "b" / "c")
        # 转换为绝对路径进行比较
        self.assertEqual(Path(result).resolve(), Path(expected).resolve())
    
    def test_normalize_path(self):
        """测试路径标准化"""
        test_path = "test/../test/./file.txt"
        normalized = normalize_path(test_path)
        expected = str(Path("test/file.txt").resolve())
        self.assertEqual(normalized, expected)
    
    def test_is_valid_path(self):
        """测试路径有效性检查"""
        self.assertTrue(is_valid_path("valid/path"))
        self.assertTrue(is_valid_path(""))  # 空字符串是有效的
        self.assertFalse(is_valid_path(None))
    
    def test_ensure_directory_exists(self):
        """测试确保目录存在"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_subdir = os.path.join(temp_dir, "subdir", "nested")
            result = ensure_directory_exists(test_subdir)
            
            self.assertTrue(os.path.exists(test_subdir))
            self.assertEqual(result, normalize_path(test_subdir))
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_get_file_size(self):
        """测试获取文件大小"""
        # 测试PathUtils的get_file_size方法
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test content")
                temp_file = f.name
            
            size = PathUtils.get_file_size(temp_file)
            self.assertEqual(size, 12)  # "test content" 的字节长度
            
            # 测试不存在的文件
            non_existent = "/non/existent/file.txt"
            size = PathUtils.get_file_size(non_existent)
            self.assertEqual(size, 0)
            
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_path_exists(self):
        """测试路径存在性检查"""
        self.assertTrue(PathUtils.path_exists(os.getcwd()))
        self.assertFalse(PathUtils.path_exists("/non/existent/path"))


class TestPathManager(unittest.TestCase):
    """测试路径管理器 - 简化测试避免全局状态干扰"""
    
    def test_path_manager_creation(self):
        """测试路径管理器创建"""
        manager = PathManager()
        self.assertIsNotNone(manager)
        
        # 验证基本方法不抛出异常
        project_root = manager.get_project_root()
        self.assertIsInstance(project_root, str)
        self.assertTrue(project_root)
    
    def test_get_all_paths(self):
        """测试获取所有路径"""
        manager = PathManager()
        all_paths = manager.get_all_paths()
        
        self.assertIsInstance(all_paths, dict)
        self.assertIn('PROJECT_ROOT', all_paths)
        self.assertIn('CORE_PATH', all_paths)


class TestGlobalPathFunctions(unittest.TestCase):
    """测试全局路径函数"""
    
    def test_global_functions(self):
        """测试全局路径函数"""
        # 这些函数不应该抛出异常
        project_root = get_project_root()
        core_path = get_core_path()
        logger_path = get_logger_path()
        error_path = get_error_path()
        data_path = get_data_path()
        config_path = get_config_path()
        output_path = get_output_path()
        logs_path = get_logs_path()
        
        # 验证返回值是字符串且不为空
        self.assertIsInstance(project_root, str)
        self.assertTrue(project_root)
        self.assertIsInstance(core_path, str)
        self.assertTrue(core_path)
        self.assertIsInstance(logger_path, str)
        self.assertTrue(logger_path)
        self.assertIsInstance(error_path, str)
        self.assertTrue(error_path)
        self.assertIsInstance(data_path, str)
        self.assertTrue(data_path)
        self.assertIsInstance(config_path, str)
        self.assertTrue(config_path)
        self.assertIsInstance(output_path, str)
        self.assertTrue(output_path)
        self.assertIsInstance(logs_path, str)
        self.assertTrue(logs_path)
        
        # 验证路径存在或可以创建
        self.assertTrue(os.path.exists(project_root) or os.path.dirname(project_root))
    
    def test_global_constants(self):
        """测试全局常量"""
        self.assertIsInstance(PATH_CONSTANTS['PROJECT_ROOT'], str)
        self.assertTrue(PATH_CONSTANTS['PROJECT_ROOT'])


if __name__ == '__main__':
    unittest.main()