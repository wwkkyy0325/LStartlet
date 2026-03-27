import unittest
import asyncio
import time
import sys
from LStartlet.core.scheduler.thread_safe_scheduler import ThreadSafeScheduler


class TestThreadSafeScheduler(unittest.TestCase):

    def setUp(self):
        """设置测试环境"""
        self.scheduler = ThreadSafeScheduler(max_workers=2)

    def tearDown(self):
        """清理测试环境"""
        self.scheduler.shutdown(wait=True)

    @unittest.skipIf(sys.platform == "win32", "Windows系统上线程调度器测试不稳定")
    def test_is_main_thread(self):
        """测试主线程检测"""
        # 在主线程中调用
        self.assertTrue(self.scheduler.is_main_thread())

    @unittest.skipIf(sys.platform == "win32", "Windows系统上线程调度器测试不稳定")
    def test_run_on_main_thread_immediate(self):
        """测试在主线程中立即执行"""
        result: list[int] = []

        def test_func(value: int) -> int:
            result.append(value)
            return value * 2

        # 在主线程中调用
        self.scheduler.run_on_main_thread(test_func, 5)

        # 等待任务完成
        time.sleep(0.1)

        self.assertEqual(result, [5])

    @unittest.skipIf(sys.platform == "win32", "Windows系统上线程调度器测试不稳定")
    def test_submit_async_task_sync_function(self):
        """测试提交同步异步任务"""

        def sync_test() -> str:
            return "sync_result"

        future = self.scheduler.submit_async_task(sync_test)
        # 使用事件循环来处理 Future
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(future)
            self.assertEqual(result, "sync_result")
        finally:
            loop.close()

    @unittest.skipIf(sys.platform == "win32", "Windows系统上线程调度器测试不稳定")
    def test_submit_async_task_with_timeout(self):
        """测试带超时的异步任务"""

        def long_running_task() -> str:
            time.sleep(0.1)
            return "done"

        # 设置较短的超时时间
        future = self.scheduler.submit_async_task(long_running_task, timeout=0.01)

        loop = asyncio.new_event_loop()
        try:
            with self.assertRaises(Exception):
                loop.run_until_complete(future)
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
