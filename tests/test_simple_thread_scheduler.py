import unittest
from core.scheduler.simple_thread_scheduler import SimpleThreadScheduler


class TestSimpleThreadScheduler(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        self.scheduler = SimpleThreadScheduler(max_workers=2)
    
    def tearDown(self):
        """清理测试环境"""
        self.scheduler.shutdown()
    
    def test_is_main_thread(self):
        """测试主线程检测"""
        self.assertTrue(self.scheduler.is_main_thread())
    
    def test_run_on_main_thread_sync(self):
        """测试在主线程中同步执行"""
        def test_func(x: int, y: int) -> int:
            return x + y
        
        result = self.scheduler.run_on_main_thread(test_func, 3, 4)
        self.assertEqual(result, 7)


if __name__ == '__main__':
    unittest.main()