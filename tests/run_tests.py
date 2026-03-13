#!/usr/bin/env python3
"""
运行所有单元测试的脚本
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def discover_and_run_tests():
    """发现并运行所有测试"""
    # 获取tests目录
    tests_dir = Path(__file__).parent
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 发现所有测试文件
    for test_file in tests_dir.glob("test_*.py"):
        if test_file.name == "run_tests.py":
            continue
        
        # 导入测试模块
        module_name = test_file.stem
        try:
            module = __import__(f"tests.{module_name}", fromlist=[''])
            # 加载测试用例
            module_suite = loader.loadTestsFromModule(module)
            suite.addTests(module_suite)
            from core.logger import info
            info(f"已加载测试模块: {module_name}")
        except Exception as e:
            from core.logger import error
            error(f"加载测试模块失败 {module_name}: {e}")
    
    # 运行测试
    if suite.countTestCases() > 0:
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # 返回测试结果
        return result.wasSuccessful()
    else:
        from core.logger import warning
        warning("未找到任何测试用例")
        return False

if __name__ == '__main__':
    success = discover_and_run_tests()
    sys.exit(0 if success else 1)