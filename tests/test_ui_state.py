#!/usr/bin/env python3
"""
UI状态管理器单元测试
"""

import sys
import unittest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.state.ui_state_manager import UIStateManager
from ui.state.ui_state import UIState
from core.event.event_type_registry import EventTypeRegistry


class TestUIState(unittest.TestCase):
    """UIState类测试"""
    
    def test_ui_state_initialization(self):
        """测试UIState初始化"""
        state = UIState()
        self.assertEqual(state.message, "")
        self.assertEqual(state.state_type, "normal")
        self.assertEqual(state.progress, 0.0)
        self.assertEqual(state.data, {})
        # timestamp在__post_init__中设置，可能为0，所以不测试大于0
    
    def test_ui_state_with_initial_values(self):
        """测试UIState带初始值"""
        data: Dict[str, Any] = {"key": "value"}
        state = UIState(
            message="test message",
            state_type="test_type",
            progress=0.5,
            data=data
        )
        self.assertEqual(state.message, "test message")
        self.assertEqual(state.state_type, "test_type")
        self.assertEqual(state.progress, 0.5)
        self.assertEqual(state.data, data)


class TestUIStateManager(unittest.TestCase):
    """UIStateManager类测试"""
    
    def setUp(self):
        """测试前准备"""
        # 确保UI事件类型被注册
        from core.event.events.ui_events import UIStateChangeEvent
        registry = EventTypeRegistry()
        if not registry.is_registered(UIStateChangeEvent.EVENT_TYPE):
            registry.register_event_type(UIStateChangeEvent.EVENT_TYPE, UIStateChangeEvent, "ui")
        
        self.manager = UIStateManager()
    
    def test_initialization(self):
        """测试UIStateManager初始化"""
        self.assertIsInstance(self.manager.get_current_state(), UIState)
        # 使用公共API进行测试而不是直接访问私有属性
    
    def test_get_current_state(self):
        """测试获取当前状态"""
        state = self.manager.get_current_state()
        self.assertIsInstance(state, UIState)
        # 验证多次调用返回的是同一个实例
        state2 = self.manager.get_current_state()
        self.assertIs(state, state2)
    
    def test_update_state_message(self):
        """测试更新消息"""
        self.manager.update_state(message="test message")
        current_state = self.manager.get_current_state()
        self.assertEqual(current_state.message, "test message")
        self.assertGreaterEqual(current_state.timestamp, 0)
    
    def test_update_state_type(self):
        """测试更新状态类型"""
        self.manager.update_state(state_type="processing")
        current_state = self.manager.get_current_state()
        self.assertEqual(current_state.state_type, "processing")
    
    def test_update_state_progress(self):
        """测试更新进度"""
        self.manager.update_state(progress=0.75)
        current_state = self.manager.get_current_state()
        self.assertEqual(current_state.progress, 0.75)
    
    def test_update_state_progress_clamping(self):
        """测试进度值的边界限制"""
        # 测试超过1.0的情况
        self.manager.update_state(progress=1.5)
        current_state = self.manager.get_current_state()
        self.assertEqual(current_state.progress, 1.0)
        
        # 重置状态
        self.manager.update_state(progress=0.5)
        
        # 测试低于0.0的情况（注意：progress=-1.0 表示不更新）
        self.manager.update_state(progress=-0.5)
        current_state = self.manager.get_current_state()
        # 由于-0.5 >= 0.0 为 False，所以不会更新progress，保持0.5
        self.assertEqual(current_state.progress, 0.5)
    
    def test_update_state_data(self):
        """测试更新数据"""
        test_data: Dict[str, Any] = {"result": "success", "count": 42}
        self.manager.update_state(data=test_data)
        current_state = self.manager.get_current_state()
        self.assertEqual(current_state.data, test_data)
    
    def test_update_state_data_merge(self):
        """测试数据合并"""
        # 先设置一些数据
        initial_data: Dict[str, Any] = {"existing": "value"}
        self.manager.update_state(data=initial_data)
        
        # 再更新部分数据
        new_data: Dict[str, Any] = {"new_key": "new_value"}
        self.manager.update_state(data=new_data)
        
        current_state = self.manager.get_current_state()
        expected_data = {"existing": "value", "new_key": "new_value"}
        self.assertEqual(current_state.data, expected_data)
    
    def test_update_state_multiple_fields(self):
        """测试同时更新多个字段"""
        test_data: Dict[str, Any] = {"key": "value"}
        self.manager.update_state(
            message="multi update",
            state_type="multi_type",
            progress=0.3,
            data=test_data
        )
        current_state = self.manager.get_current_state()
        self.assertEqual(current_state.message, "multi update")
        self.assertEqual(current_state.state_type, "multi_type")
        self.assertEqual(current_state.progress, 0.3)
        self.assertEqual(current_state.data, test_data)
    
    def test_add_remove_observer(self):
        """测试添加和移除同步观察者"""
        observer = Mock()
        
        # 添加观察者
        self.manager.add_observer(observer)
        # 验证观察者被添加（通过更新状态来触发）
        self.manager.update_state(message="test")
        observer.assert_called_once()
        
        # 移除观察者
        self.manager.remove_observer(observer)
        # 再次更新状态，观察者不应被调用
        observer.reset_mock()
        self.manager.update_state(message="test2")
        observer.assert_not_called()
    
    def test_add_remove_async_observer(self):
        """测试添加和移除异步观察者"""
        async_observer = Mock()
        
        # 添加异步观察者
        self.manager.add_async_observer(async_observer)
        # 验证观察者被添加（通过更新状态来触发）
        self.manager.update_state(message="test")
        async_observer.assert_called_once()
        
        # 移除异步观察者
        self.manager.remove_async_observer(async_observer)
        # 再次更新状态，观察者不应被调用
        async_observer.reset_mock()
        self.manager.update_state(message="test2")
        async_observer.assert_not_called()
    
    def test_observer_notification_on_update(self):
        """测试状态更新时通知观察者"""
        observer = Mock()
        async_observer = Mock()
        
        self.manager.add_observer(observer)
        self.manager.add_async_observer(async_observer)
        
        # 更新状态
        self.manager.update_state(message="test notification")
        
        # 验证观察者被调用
        observer.assert_called_once()
        async_observer.assert_called_once()
        
        # 验证传入的状态参数
        called_state = observer.call_args[0][0]
        self.assertIsInstance(called_state, UIState)
        self.assertEqual(called_state.message, "test notification")
    
    def test_observer_exception_handling(self):
        """测试观察者异常处理"""
        def failing_observer(state: UIState) -> None:
            raise Exception("Observer failed")
        
        # 添加会抛出异常的观察者
        self.manager.add_observer(failing_observer)
        
        # 更新状态不应该抛出异常
        try:
            self.manager.update_state(message="should not fail")
            success = True
        except Exception:
            success = False
        
        self.assertTrue(success, "观察者异常不应影响状态管理器")


if __name__ == '__main__':
    unittest.main()