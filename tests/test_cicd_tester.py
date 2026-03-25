#!/usr/bin/env python3
"""
CICD Tester Unit Tests
Test the Tester class functionality
"""

import sys
import unittest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cicd.tester import Tester


class TestTester(unittest.TestCase):
    """测试 Tester 类"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = str(Path(__file__).parent.parent)
        # 重置配置
        from core.config import reset_all_configs
        reset_all_configs()
        # 确保测试报告目录存在
        self.test_report_dir = "./test_reports"
        os.makedirs(self.test_report_dir, exist_ok=True)
    
    def tearDown(self):
        """测试后清理"""
        from core.config import reset_all_configs
        reset_all_configs()
        # 清理测试报告目录
        if os.path.exists(self.test_report_dir):
            for file in os.listdir(self.test_report_dir):
                os.remove(os.path.join(self.test_report_dir, file))
    
    def test_tester_initialization(self):
        """测试测试器初始化"""
        tester = Tester(self.project_root)
        
        self.assertEqual(tester.project_root, self.project_root)
    
    @patch('core.cicd.tester.unittest.TextTestRunner')
    @patch('core.cicd.tester.unittest.TestLoader')
    def test_run_test_directory_success(self, mock_loader, mock_runner):
        """测试运行测试目录成功"""
        # 模拟测试结果
        mock_result = MagicMock()
        mock_result.testsRun = 15
        mock_result.failures = []
        mock_result.errors = []
        mock_result.skipped = []
        mock_runner.return_value.run.return_value = mock_result
        
        tester = Tester(self.project_root)
        result = tester._run_test_directory("tests")
        
        # 验证返回值结构
        self.assertIn("total_tests", result)
        self.assertIn("passed", result)
        self.assertEqual(result["total_tests"], 15)
        self.assertEqual(result["passed"], 15)
    
    @patch('core.cicd.tester.subprocess.run')
    def test_run_test_file_success(self, mock_subprocess_run):
        """测试运行测试文件成功"""
        # 模拟 subprocess 结果
        mock_process = MagicMock()
        mock_process.stdout = "Test output"
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process
        
        tester = Tester(self.project_root)
        result = tester._run_test_file("test_example.py")
        
        # 验证返回值结构（注意：_run_test_file 不返回 passed 字段）
        self.assertIn("suite", result)
        self.assertIn("return_code", result)
        self.assertEqual(result["return_code"], 0)
        self.assertEqual(result["suite"], "test_example.py")
    
    @patch('core.cicd.tester.unittest.TextTestRunner')
    @patch('core.cicd.tester.unittest.TestLoader')
    def test_run_tests_with_unittest_discovery(self, mock_loader, mock_runner):
        """测试使用 unittest 发现机制运行测试"""
        # 模拟测试结果
        mock_result = MagicMock()
        mock_result.testsRun = 10
        mock_result.failures = []
        mock_result.errors = []
        mock_result.skipped = []
        mock_runner.return_value.run.return_value = mock_result
        
        tester = Tester(self.project_root)
        result = tester.run_tests("tests")
        
        # 验证返回值结构
        self.assertIn("total_tests", result)
        self.assertIn("passed", result)
        self.assertEqual(result["total_tests"], 10)
        self.assertEqual(result["passed"], 10)


if __name__ == '__main__':
    unittest.main()