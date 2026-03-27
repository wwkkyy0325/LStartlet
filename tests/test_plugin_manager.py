"""
Plugin Manager Tests
"""

import os
import sys
import tempfile
import shutil
import unittest
from typing import Dict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin.manager.plugin_manager import PluginManager
from plugin.base.plugin_base import PluginBase
from core.di import ServiceContainer
from core.event.event_bus import EventBus


class MockPlugin(PluginBase):
    """模拟插件用于测试"""

    PLUGIN_DEPENDENCIES: Dict[str, str] = {}
    PLUGIN_NAME = "Mock Plugin"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "Mock plugin for testing"

    def __init__(
        self,
        plugin_id: str = "mock_plugin",
        name: str = "Mock Plugin",
        version: str = "1.0.0",
        description: str = "Mock plugin for testing",
    ):
        super().__init__(plugin_id, name, version, description)

    def get_dependencies(self) -> Dict[str, str]:
        return self.PLUGIN_DEPENDENCIES

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


class TestPluginManager(unittest.TestCase):
    """插件管理器测试"""

    def setUp(self):
        """测试方法前的设置"""
        self.container = ServiceContainer()
        self.event_bus = EventBus()
        self.plugin_manager = PluginManager(self.container, self.event_bus)
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试方法后的清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        # 清理插件管理器
        self.plugin_manager.cleanup_all_plugins()

    def test_init(self):
        """测试插件管理器初始化"""
        self.assertEqual(self.plugin_manager._container, self.container)  # type: ignore
        self.assertEqual(self.plugin_manager._event_bus, self.event_bus)  # type: ignore
        self.assertEqual(len(self.plugin_manager._plugins), 0)  # type: ignore
        self.assertEqual(len(self.plugin_manager._plugin_classes), 0)  # type: ignore

    def test_get_plugin_not_found(self):
        """测试获取不存在的插件"""
        plugin = self.plugin_manager.get_plugin("nonexistent")
        self.assertIsNone(plugin)

    def test_get_all_plugins_empty(self):
        """测试获取所有插件（空）"""
        plugins = self.plugin_manager.get_all_plugins()
        self.assertEqual(len(plugins), 0)

    def test_is_plugin_loaded_false(self):
        """测试插件未加载状态"""
        self.assertFalse(self.plugin_manager.is_plugin_loaded("nonexistent"))

    def test_initialize_all_plugins_empty(self):
        """测试初始化所有插件（空）"""
        result = self.plugin_manager.initialize_all_plugins()
        self.assertTrue(result)

    def test_start_all_plugins_empty(self):
        """测试启动所有插件（空）"""
        result = self.plugin_manager.start_all_plugins()
        self.assertTrue(result)

    def test_stop_all_plugins_empty(self):
        """测试停止所有插件（空）"""
        result = self.plugin_manager.stop_all_plugins()
        self.assertTrue(result)

    def test_cleanup_all_plugins_empty(self):
        """测试清理所有插件（空）"""
        result = self.plugin_manager.cleanup_all_plugins()
        self.assertTrue(result)

    def test_unload_plugin_success(self):
        """测试成功卸载插件"""
        # 创建模拟插件元数据
        from plugin.manager.plugin_loader import PluginMetadata

        mock_metadata = PluginMetadata(
            namespace="mock_plugin",
            name="Mock Plugin",
            version="1.0.0",
            author="Test",
            description="Mock plugin for testing",
            compatibility={"min_version": "1.0.0", "max_version": "2.0.0"},
            entry_point={"module": "mock", "class": "MockPlugin"},
            dependencies={},
            permissions=[],
        )

        # 直接添加并初始化插件
        self.plugin_manager._plugin_classes["mock_plugin"] = MockPlugin  # type: ignore
        self.plugin_manager._plugin_metadata["mock_plugin"] = mock_metadata
        self.plugin_manager.initialize_all_plugins()

        # 确保插件已加载
        self.assertTrue(self.plugin_manager.is_plugin_loaded("mock_plugin"))

        # 卸载插件
        result = self.plugin_manager.unload_plugin("mock_plugin")
        self.assertTrue(result)
        self.assertFalse(self.plugin_manager.is_plugin_loaded("mock_plugin"))

    def test_unload_plugin_not_found(self):
        """测试卸载不存在的插件"""
        result = self.plugin_manager.unload_plugin("nonexistent")
        self.assertFalse(result)
