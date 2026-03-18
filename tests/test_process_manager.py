#!/usr/bin/env python3
"""
ProcessManager Unit Tests
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scheduler.process_manager import ProcessManager


class TestProcessManager(unittest.TestCase):
    """ProcessManager类测试"""
    
    def setUp(self):
        """测试前准备"""
        # Mock 依赖项以避免实际创建进程
        self.mock_event_bus = Mock()
        self.mock_global_process_manager = Mock()
        
        # Mock get_app_container().resolve(EventBus)
        self.mock_app_container_patch = patch('core.scheduler.process_manager.get_app_container')
        self.mock_app_container = self.mock_app_container_patch.start()
        mock_container_instance = Mock()
        mock_container_instance.resolve.return_value = self.mock_event_bus
        self.mock_app_container.return_value = mock_container_instance
        
        # Mock GlobalProcessManager
        self.mock_global_process_manager_patch = patch('core.scheduler.process_manager.GlobalProcessManager')
        self.mock_global_process_manager_class = self.mock_global_process_manager_patch.start()
        self.mock_global_process_manager_class.return_value = self.mock_global_process_manager
    
    def tearDown(self):
        """测试后清理"""
        self.mock_app_container_patch.stop()
        self.mock_global_process_manager_patch.stop()
    
    @unittest.skipIf(sys.platform == "win32", "Windows系统上多进程测试不稳定")
    def test_initialization(self):
        """测试初始化"""
        process_manager = ProcessManager(max_processes=2, process_timeout=15.0)
        
        # 验证公共属性（如果有的话）
        # 由于ProcessManager没有提供获取内部状态的公共方法，我们只能验证对象创建成功
        self.assertIsNotNone(process_manager)
    
    @unittest.skipIf(sys.platform == "win32", "Windows系统上多进程测试不稳定")
    def test_start_stop(self):
        """测试启动和停止"""
        process_manager = ProcessManager(max_processes=1, process_timeout=5.0)
        
        # 启动
        process_manager.start()
        
        # 验证事件总线调用
        self.assertEqual(self.mock_event_bus.publish.call_count, 2)  # ProcessCreatedEvent + ProcessStartedEvent
        
        # 停止
        process_manager.stop()
        
        # 验证全局进程管理器调用
        self.mock_global_process_manager.terminate_process.assert_called()
    
    @unittest.skipIf(sys.platform == "win32", "Windows系统上多进程测试不稳定")
    def test_get_active_process_count(self):
        """测试获取活跃进程数量"""
        process_manager = ProcessManager(max_processes=2, process_timeout=5.0)
        
        # 未启动时
        self.assertEqual(process_manager.get_active_process_count(), 0)
        
        # 启动后
        process_manager.start()
        # 在mock环境下，我们无法真正测试活跃进程数，但可以验证方法被调用
        self.assertIsInstance(process_manager.get_active_process_count(), int)
        
        process_manager.stop()
    
    @unittest.skipIf(sys.platform == "win32", "Windows系统上多进程测试不稳定")
    def test_submit_task(self):
        """测试提交任务"""
        process_manager = ProcessManager(max_processes=1, process_timeout=5.0)
        
        # 未启动时提交任务
        result = process_manager.submit_task({"task": "test"})
        self.assertTrue(result)
        
        # 启动后提交任务
        process_manager.start()
        result = process_manager.submit_task({"task": "test2"})
        self.assertTrue(result)
        process_manager.stop()
    
    @unittest.skipIf(sys.platform == "win32", "Windows系统上多进程测试不稳定")
    def test_get_all_processes_status(self):
        """测试获取所有进程状态"""
        process_manager = ProcessManager(max_processes=1, process_timeout=5.0)
        
        # 未启动时
        status = process_manager.get_all_processes_status()
        self.assertEqual(len(status), 0)
        
        # 启动后
        process_manager.start()
        status = process_manager.get_all_processes_status()
        self.assertEqual(len(status), 1)
        
        # 验证状态结构
        worker_id = list(status.keys())[0]
        worker_status = status[worker_id]
        self.assertIn('worker_id', worker_status)
        self.assertIn('is_alive', worker_status)
        self.assertIn('status', worker_status)
        self.assertIn('pid', worker_status)
        self.assertIn('start_time', worker_status)
        self.assertIn('last_heartbeat', worker_status)
        self.assertIn('task_count', worker_status)
        self.assertIn('uptime', worker_status)
        
        process_manager.stop()


if __name__ == '__main__':
    unittest.main()