#!/usr/bin/env python3
"""
CICD Deep Learning Manager Unit Tests
Test the DeepLearningManager class functionality
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cicd.deep_learning_manager import DeepLearningManager


class TestDeepLearningManager(unittest.TestCase):
    """测试 DeepLearningManager 类"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = str(Path(__file__).parent.parent)
        # 重置配置
        from core.config import reset_all_configs
        reset_all_configs()
    
    def tearDown(self):
        """测试后清理"""
        from core.config import reset_all_configs
        reset_all_configs()
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = DeepLearningManager(self.project_root)
        
        self.assertEqual(manager.project_root, self.project_root)
    
    @patch('core.cicd.deep_learning_manager.sys.modules')
    def test_detect_deep_learning_deps_success(self, mock_modules):
        """测试成功检测深度学习依赖"""
        # 模拟 torch 模块存在
        mock_torch = MagicMock()
        mock_torch.__version__ = "1.9.0"
        mock_modules.__getitem__.return_value = mock_torch
        
        manager = DeepLearningManager(self.project_root)
        deps = manager.detect_deep_learning_deps()
        
        # 应该包含 PyTorch
        self.assertIn("PyTorch", deps)
        self.assertEqual(deps["PyTorch"], "1.9.0")
    
    def test_generate_dl_requirements_success(self):
        """测试生成深度学习依赖文件成功"""
        manager = DeepLearningManager(self.project_root)
        result = manager.generate_dl_requirements("./test_requirements.txt")
        
        # 文件应该被创建
        import os
        self.assertTrue(os.path.exists("./test_requirements.txt"))
        os.remove("./test_requirements.txt")
    
    def test_validate_environment_compatibility_success(self):
        """测试环境兼容性验证成功"""
        manager = DeepLearningManager(self.project_root)
        is_compatible, issues = manager.validate_environment_compatibility()
        
        # 在测试环境中可能不兼容，但不应该抛异常
        self.assertIsInstance(is_compatible, bool)
        self.assertIsInstance(issues, list)
    
    @patch('core.cicd.deep_learning_manager.sys.modules')
    def test_optimize_for_hardware_with_cuda(self, mock_modules):
        """测试带 CUDA 的硬件优化"""
        # 模拟 torch 模块
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "11.1"
        mock_modules.__getitem__.return_value = mock_torch
        
        manager = DeepLearningManager(self.project_root)
        result = manager.optimize_for_hardware()
        
        self.assertTrue(result)
    
    @patch('core.cicd.deep_learning_manager.sys.modules')
    def test_optimize_for_hardware_cpu_only(self, mock_modules):
        """测试仅 CPU 硬件优化"""
        # 模拟 torch 模块
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_modules.__getitem__.return_value = mock_torch
        
        manager = DeepLearningManager(self.project_root)
        result = manager.optimize_for_hardware()
        
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()