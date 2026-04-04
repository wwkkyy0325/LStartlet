#!/usr/bin/env python3
"""
Thread Safe Scheduler Unit Tests
Test the ThreadSafeScheduler class functionality
"""

import sys
import unittest
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from LStartlet.core.scheduler.thread_safe_scheduler import ThreadSafeScheduler


class TestThreadSafeScheduler(unittest.TestCase):
    """测试 ThreadSafeScheduler 类"""

    def setUp(self):
        """测试前准备"""
        # 重置配置
        from LStartlet.core.config import reset_all_configs
        reset_all_configs()

    def tearDown(self):
        """测试后清理"""
        from LStartlet.core.config import reset_all_configs
        reset_all_configs()

    def test_basic_initialization_and_shutdown(self):
        """测试基本的初始化和关闭功能"""
        scheduler = ThreadSafeScheduler(max_workers=1)
        
        # 验证基本属性
        self.assertIsNotNone(scheduler._main_thread_id)
        self.assertTrue(scheduler._running)
        
        # 立即关闭，不等待
        scheduler.shutdown(wait=False)
        self.assertFalse(scheduler._running)

    def test_is_main_thread_detection(self):
        """测试主线程检测"""
        scheduler = ThreadSafeScheduler()
        is_main = scheduler.is_main_thread()
        self.assertIsInstance(is_main, bool)
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    unittest.main()