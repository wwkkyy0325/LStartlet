"""
插件加载器测试
"""

import os
import sys
import tempfile
import shutil
import unittest
from typing import Dict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin.manager.plugin_loader import PluginLoader
from plugin.base.plugin_base import PluginBase


class MockPluginForLoader(PluginBase):
    """用于加载器测试的模拟插件"""
    
    def __init__(self, plugin_id: str = "mock_plugin_for_loader", name: str = "Mock Plugin for Loader", 
                 version: str = "1.0.0", description: str = "Mock plugin for loader testing"):
        super().__init__(plugin_id, name, version, description)
    
    def get_dependencies(self) -> Dict[str, str]:
        return {}
    
    def get_provided_services(self) -> Dict[str, str]:
        return {}
    
    def _on_initialize(self) -> bool:
        return True
    
    def _on_start(self) -> bool:
        return True
    
    def _on_stop(self) -> bool:
        return True
    
    def _on_cleanup(self) -> bool:
        return True


class TestPluginLoader(unittest.TestCase):
    """插件加载器测试"""
    
    def setUp(self):
        """测试方法前的设置"""
        self.loader = PluginLoader()
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试方法后的清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """测试插件加载器初始化"""
        self.assertEqual(len(self.loader._loaded_modules), 0)  # type: ignore
    
    def test_load_plugin_from_nonexistent_file(self):
        """测试加载不存在的插件文件"""
        with self.assertRaises(Exception):
            self.loader.load_plugin_from_file("nonexistent.py")
    
    def create_test_plugin_file(self, content: str) -> str:
        """创建测试插件文件"""
        plugin_file_path = os.path.join(self.test_dir, "test_plugin.py")
        with open(plugin_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return plugin_file_path
    
    
    def test_load_plugin_from_directory_empty(self):
        """测试从空目录加载插件"""
        plugins = self.loader.load_plugin_from_directory(self.test_dir)
        self.assertEqual(len(plugins), 0)
    
    def test_load_plugin_from_directory_with_file(self):
        """测试从目录加载插件文件"""
        # 创建一个简单的插件文件，确保继承PluginBase
        plugin_content = '''
from plugin.base.plugin_base import PluginBase

class SimpleTestPlugin(PluginBase):
    def __init__(self, plugin_id="simple_test", name="Simple Test", version="1.0.0", description="Simple test plugin"):
        super().__init__(plugin_id, name, version, description)
    
    def get_dependencies(self):
        return {}
    
    def get_provided_services(self):
        return {}
    
    def _on_initialize(self):
        return True
    
    def _on_start(self):
        return True
    
    def _on_stop(self):
        return True
    
    def _on_cleanup(self):
        return True
'''
        self.create_test_plugin_file(plugin_content)
        
        # 加载插件
        plugins = self.loader.load_plugin_from_directory(self.test_dir)
        self.assertEqual(len(plugins), 1)
        self.assertIn("SimpleTestPlugin", plugins)