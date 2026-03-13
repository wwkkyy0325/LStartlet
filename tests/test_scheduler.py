#!/usr/bin/env python3
"""
调度器模块单元测试
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scheduler.scheduler import Scheduler
from core.scheduler.task_dispatcher import TaskDispatcher, TaskPriority


class TestScheduler(unittest.TestCase):
    """Scheduler类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.scheduler = Scheduler()
    
    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        self.assertFalse(self.scheduler.is_running)
        self.assertIsNotNone(self.scheduler.config)
        self.assertIsNotNone(self.scheduler.tick_component)
    
    def test_scheduler_start_stop(self):
        """测试调度器启动和停止"""
        # 启动调度器
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running)
        
        # 停止调度器
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)
    
    def test_update_config(self):
        """测试更新配置"""
        # 更新配置
        self.scheduler.update_config(max_processes=8)
        
        # 验证配置已更新
        self.assertEqual(self.scheduler.config.max_processes, 8)
    
    def test_get_status(self):
        """测试获取状态"""
        status = self.scheduler.get_status()
        self.assertIsInstance(status, dict)
        self.assertIn('is_running', status)
        self.assertIn('active_processes', status)
        self.assertIn('active_tasks', status)


class TestTaskDispatcher(unittest.TestCase):
    """TaskDispatcher类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.dispatcher = TaskDispatcher()
    
    def test_dispatcher_initialization(self):
        """测试任务分发器初始化"""
        self.assertEqual(self.dispatcher.strategy, "round_robin")
        self.assertEqual(self.dispatcher.max_concurrent_tasks, 10)
        # 使用公共方法而不是直接访问私有属性
        self.assertEqual(self.dispatcher.get_queue_size(), 0)
    
    def test_submit_task(self):
        """测试提交任务"""
        def dummy_task():
            return "task_result"
        
        # 提交任务
        task = self.dispatcher.submit_task(
            task_id="test_task",
            func=dummy_task,
            priority=TaskPriority.NORMAL
        )
        
        # 验证任务已创建
        self.assertEqual(task.task_id, "test_task")
        self.assertEqual(task.func, dummy_task)
        self.assertEqual(task.priority, TaskPriority.NORMAL)
        
        # 验证任务已添加到队列
        self.assertEqual(self.dispatcher.get_queue_size(), 1)


if __name__ == '__main__':
    unittest.main()