#!/usr/bin/env python3
"""
TickComponent and TickConfig Unit Tests
"""

import sys
import unittest
import asyncio
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scheduler.tick import TickComponent, TickConfig, TickState


class TestTickConfig(unittest.TestCase):
    """TickConfig类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = TickConfig()

        self.assertEqual(config.interval, 1.0)
        self.assertEqual(config.max_ticks, -1)
        self.assertFalse(config.auto_start)
        self.assertTrue(config.enable_logging)

    def test_custom_config(self):
        """测试自定义配置"""
        config = TickConfig(
            interval=0.5, max_ticks=10, auto_start=True, enable_logging=False
        )

        self.assertEqual(config.interval, 0.5)
        self.assertEqual(config.max_ticks, 10)
        self.assertTrue(config.auto_start)
        self.assertFalse(config.enable_logging)


class TestTickComponent(unittest.TestCase):
    """TickComponent类测试"""

    def setUp(self):
        """测试前准备"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """测试后清理"""
        # 确保所有任务都被清理
        pending = asyncio.all_tasks(self.loop)
        for task in pending:
            task.cancel()
        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        self.loop.close()
        asyncio.set_event_loop(None)

    def test_initialization(self):
        """测试初始化"""
        config = TickConfig(interval=0.1, max_ticks=5)
        tick_component = TickComponent(config)

        self.assertEqual(tick_component.config, config)
        self.assertEqual(tick_component.state, TickState.STOPPED)
        self.assertEqual(tick_component.current_tick, 0)
        self.assertEqual(tick_component.elapsed_time, 0.0)

    def test_add_remove_callbacks(self):
        """测试添加和移除回调函数"""
        tick_component = TickComponent()

        # 定义带类型注解的回调函数
        def sync_callback(tick_count: int, elapsed_time: float) -> None:
            pass

        async def async_callback(tick_count: int, elapsed_time: float) -> None:
            pass

        # 添加回调
        tick_component.add_tick_callback(sync_callback)
        tick_component.add_async_tick_callback(async_callback)

        # 验证回调已添加（使用公共方法获取统计信息）
        stats = tick_component.get_stats()
        self.assertEqual(stats["callback_count"], 2)
        self.assertEqual(stats["sync_callbacks"], 1)
        self.assertEqual(stats["async_callbacks"], 1)

        # 移除回调
        removed = tick_component.remove_tick_callback(sync_callback)
        self.assertTrue(removed)

        removed = tick_component.remove_tick_callback(async_callback)
        self.assertTrue(removed)

        # 验证回调已移除
        stats_after_removal = tick_component.get_stats()
        self.assertEqual(stats_after_removal["callback_count"], 0)

    def test_state_transitions(self):
        """测试状态转换（不实际运行tick循环）"""
        tick_component = TickComponent(TickConfig(interval=1.0, max_ticks=2))

        # 初始状态
        self.assertEqual(tick_component.state, TickState.STOPPED)

        # 启动（但不实际运行）
        with patch("asyncio.create_task") as mock_create_task:
            tick_component.start()
            self.assertEqual(tick_component.state, TickState.RUNNING)
            mock_create_task.assert_called_once()

        # 暂停
        tick_component.pause()
        self.assertEqual(tick_component.state, TickState.PAUSED)

        # 恢复
        with patch("asyncio.create_task"):
            tick_component.start()
            self.assertEqual(tick_component.state, TickState.RUNNING)

        # 停止
        tick_component.stop()
        self.assertEqual(tick_component.state, TickState.STOPPED)

    def test_get_stats(self):
        """测试获取统计信息"""
        config = TickConfig(interval=0.1, max_ticks=5, enable_logging=False)
        tick_component = TickComponent(config)

        stats = tick_component.get_stats()

        self.assertEqual(stats["state"], "stopped")
        self.assertEqual(stats["current_tick"], 0)
        self.assertEqual(stats["interval"], 0.1)
        self.assertEqual(stats["max_ticks"], 5)
        self.assertEqual(stats["callback_count"], 0)

    def test_reset(self):
        """测试重置功能"""
        tick_component = TickComponent(TickConfig(interval=0.1, max_ticks=2))

        # 重置
        tick_component.reset()

        self.assertEqual(tick_component.state, TickState.STOPPED)
        self.assertEqual(tick_component.current_tick, 0)
        self.assertEqual(tick_component.elapsed_time, 0.0)


if __name__ == "__main__":
    unittest.main()
