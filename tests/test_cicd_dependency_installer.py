#!/usr/bin/env python3
"""
CICD Dependency Installer Unit Tests
Test the DependencyInstaller class functionality
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cicd.dependency_installer import DependencyInstaller


class TestDependencyInstaller(unittest.TestCase):
    """测试 DependencyInstaller 类"""
    
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
    
    def test_dependency_installer_initialization(self):
        """测试依赖安装器初始化"""
        installer = DependencyInstaller(self.project_root)
        
        self.assertEqual(installer.project_root, self.project_root)
    
    @patch('core.cicd.dependency_installer.os.path.exists', return_value=False)
    def test_check_and_install_missing_no_requirements(self, mock_exists):
        """测试没有 requirements.txt 文件"""
        installer = DependencyInstaller(self.project_root)
        result = installer.check_and_install_missing()
        
        self.assertTrue(result)  # 没有 requirements 文件时返回 True
    
    @patch('core.cicd.dependency_installer.DependencyInstaller._load_requirements')
    @patch('core.cicd.dependency_installer.DependencyInstaller._find_missing_packages')
    @patch('core.cicd.dependency_installer.DependencyInstaller.install_packages')
    def test_check_and_install_missing_success(self, mock_install, mock_find, mock_load):
        """测试依赖安装成功"""
        # 模拟有缺失的依赖但安装成功
        mock_load.return_value = {"requests": ">=2.0"}
        mock_find.return_value = {"requests": ">=2.0"}
        mock_install.return_value = True
        
        installer = DependencyInstaller(self.project_root)
        result = installer.check_and_install_missing()
        
        self.assertTrue(result)
        mock_install.assert_called_once()
    
    @patch('core.cicd.dependency_installer.DependencyInstaller._load_requirements')
    @patch('core.cicd.dependency_installer.DependencyInstaller._find_missing_packages')
    @patch('core.cicd.dependency_installer.DependencyInstaller.install_packages')
    def test_check_and_install_missing_installation_failure(self, mock_install, mock_find, mock_load):
        """测试依赖安装失败"""
        # 模拟有缺失的依赖但安装失败
        mock_load.return_value = {"requests": ">=2.0"}
        mock_find.return_value = {"requests": ">=2.0"}
        mock_install.return_value = False
        
        installer = DependencyInstaller(self.project_root)
        result = installer.check_and_install_missing()
        
        self.assertFalse(result)
        mock_install.assert_called_once()


if __name__ == '__main__':
    unittest.main()