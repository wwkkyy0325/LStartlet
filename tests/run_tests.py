#!/usr/bin/env python3
"""
测试运行器
使用unittest自动发现并运行所有测试用例
"""

import sys
import os
import unittest


def run_all_tests():
    """运行所有测试"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 添加项目根目录到Python路径
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 创建测试加载器
    loader = unittest.TestLoader()
    
    # 自动发现所有测试
    suite = loader.discover(
        start_dir='tests',
        pattern="test_*.py"
    )
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)