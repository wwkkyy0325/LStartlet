"""
插件加载器测试
"""

import os
import sys
import tempfile
import shutil
import unittest
import json
from typing import Dict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin.manager.plugin_loader import PluginLoader
from plugin.base.plugin_base import PluginBase


class MockPluginForLoader(PluginBase):
    """用于加载器测试的模拟插件"""

    def __init__(
        self,
        plugin_id: str = "mock_plugin_for_loader",
        name: str = "Mock Plugin for Loader",
        version: str = "1.0.0",
        description: str = "Mock plugin for loader testing",
    ):
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

    def create_test_plugin_file(self, content: str) -> str:
        """创建测试插件文件"""
        # 创建插件目录结构
        plugin_dir = os.path.join(self.test_dir, "simple_test_plugin")
        os.makedirs(plugin_dir, exist_ok=True)

        # 创建 plugin.json
        plugin_json = {
            "namespace": "com.test.simple_test",
            "name": "Simple Test Plugin",
            "version": "1.0.0",
            "author": "Test Author",
            "description": "Simple test plugin",
            "compatibility": {"min_version": "1.0.0", "max_version": "2.0.0"},
            "entry_point": {"module": "simple_test", "class": "SimpleTestPlugin"},
            "dependencies": {},
            "permissions": [],
        }
        plugin_json_path = os.path.join(plugin_dir, "plugin.json")
        with open(plugin_json_path, "w", encoding="utf-8") as f:
            json.dump(plugin_json, f, indent=2)

        # 创建插件模块文件
        plugin_file_path = os.path.join(plugin_dir, "simple_test.py")
        with open(plugin_file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return plugin_dir

    def test_load_plugin_from_directory_empty(self):
        """测试从空目录加载插件"""
        plugins = self.loader.load_plugin_from_directory(self.test_dir)
        self.assertEqual(len(plugins), 0)

    def test_load_plugin_from_directory_with_file(self):
        """测试从目录加载插件文件"""
        # 创建一个简单的插件文件，确保继承PluginBase
        plugin_content = """
from plugin.base.plugin_base import PluginBase

class SimpleTestPlugin(PluginBase):
    def __init__(self):
        super().__init__("simple_test", "Simple Test", "1.0.0", "Simple test plugin")
    
    def get_dependencies(self):
        return {}
    
    def get_provided_services(self):
        return {"simple_service": self}
    
    def _on_initialize(self):
        return True
    
    def _on_start(self):
        return True
    
    def _on_stop(self):
        return True
    
    def _on_cleanup(self):
        return True
"""
        self.create_test_plugin_file(plugin_content)

        # 加载插件
        plugins = self.loader.load_plugin_from_directory(self.test_dir)
        self.assertEqual(len(plugins), 1)
        self.assertIn("com.test.simple_test", plugins)
