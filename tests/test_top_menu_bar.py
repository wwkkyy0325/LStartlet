"""
顶部菜单栏组件单元测试
"""

import unittest
from unittest.mock import Mock, patch
from typing import Dict, Any

# 导入PySide6 QApplication
from PySide6.QtWidgets import QApplication
import sys

# 导入被测试的组件
from ui.components.top_menu_bar import TopMenuBar
from core.event.event_bus import EventBus


class TestTopMenuBar(unittest.TestCase):
    """顶部菜单栏组件测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类前置设置 - 创建QApplication"""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前置设置"""
        self.event_bus = Mock(spec=EventBus)
        self.menu_bar = TopMenuBar(event_bus=self.event_bus)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.menu_bar)
        self.assertEqual(len(self.menu_bar._menus), 0)
        self.assertEqual(len(self.menu_bar._menu_items), 0)
    
    def test_configure_menu(self):
        """测试菜单配置"""
        menu_config = {
            "file": {
                "title": "文件",
                "items": [
                    {"id": "new", "text": "新建", "shortcut": "Ctrl+N", "enabled": True},
                    {"id": "open", "text": "打开", "shortcut": "Ctrl+O", "enabled": True},
                    {"id": "separator", "type": "separator"},
                    {"id": "exit", "text": "退出", "shortcut": "Ctrl+Q", "enabled": True}
                ]
            }
        }
        
        self.menu_bar.configure_menu(menu_config)
        
        # 验证菜单创建
        self.assertIn("file", self.menu_bar._menus)
        self.assertIn("file", self.menu_bar._menu_items)
        self.assertIn("new", self.menu_bar._menu_items["file"])
        self.assertIn("open", self.menu_bar._menu_items["file"])
        self.assertIn("exit", self.menu_bar._menu_items["file"])
    
    def test_update_menu_item(self):
        """测试更新菜单项"""
        menu_config = {
            "file": {
                "title": "文件",
                "items": [
                    {"id": "new", "text": "新建", "shortcut": "Ctrl+N", "enabled": True}
                ]
            }
        }
        
        self.menu_bar.configure_menu(menu_config)
        
        # 更新菜单项
        updates = {"text": "新建文件", "enabled": False}
        result = self.menu_bar.update_menu_item("file", "new", updates)
        
        self.assertTrue(result)
        state = self.menu_bar.get_menu_item_state("file", "new")
        self.assertIsNotNone(state)
        if state:
            self.assertEqual(state["text"], "新建文件")
            self.assertFalse(state["enabled"])
    
    def test_menu_item_triggered_event(self):
        """测试菜单项触发事件"""
        menu_config = {
            "file": {
                "title": "文件",
                "items": [
                    {"id": "new", "text": "新建", "shortcut": "Ctrl+N", "enabled": True}
                ]
            }
        }
        
        self.menu_bar.configure_menu(menu_config)
        
        # 触发菜单项
        item_data = {"id": "new", "text": "新建", "shortcut": "Ctrl+N", "enabled": True}
        self.menu_bar._on_menu_item_triggered("file", "new", item_data)
        
        # 验证事件总线调用
        self.event_bus.publish.assert_called_once()
    
    def test_get_menu_item_state(self):
        """测试获取菜单项状态"""
        menu_config = {
            "file": {
                "title": "文件",
                "items": [
                    {"id": "new", "text": "新建", "shortcut": "Ctrl+N", "enabled": True}
                ]
            }
        }
        
        self.menu_bar.configure_menu(menu_config)
        
        state = self.menu_bar.get_menu_item_state("file", "new")
        self.assertIsNotNone(state)
        if state:
            self.assertEqual(state["text"], "新建")
            self.assertTrue(state["enabled"])
            self.assertEqual(state["shortcut"], "Ctrl+N")
    
    def test_nonexistent_menu_item(self):
        """测试不存在的菜单项"""
        result = self.menu_bar.update_menu_item("nonexistent", "item", {})
        self.assertFalse(result)
        
        state = self.menu_bar.get_menu_item_state("nonexistent", "item")
        self.assertIsNone(state)


if __name__ == '__main__':
    unittest.main()