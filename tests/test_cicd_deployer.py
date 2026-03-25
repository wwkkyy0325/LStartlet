#!/usr/bin/env python3
"""
CICD Deployer Unit Tests
Test the Deployer class functionality
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cicd.deployer import Deployer


class TestDeployer(unittest.TestCase):
    """测试 Deployer 类"""
    
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
    
    def test_deployer_initialization(self):
        """测试部署器初始化"""
        deployer = Deployer(self.project_root)
        
        self.assertEqual(deployer.project_root, self.project_root)
        self.assertEqual(deployer.deployment_history, [])
    
    @patch('core.cicd.deployer.Deployer._get_deployment_config')
    @patch('core.cicd.deployer.Deployer._execute_deployment')
    def test_deploy_success(self, mock_execute, mock_get_config):
        """测试部署成功"""
        # Mock 部署配置和执行
        mock_get_config.return_value = {
            "target_path": "/fake/target",
            "backup_before_deploy": False,
            "run_health_check": False,
            "notify_on_deploy": False,
            "model_path": "/fake/models"
        }
        mock_execute.return_value = True
        
        deployer = Deployer(self.project_root)
        result = deployer.deploy("dev", "/fake/artifact", False)
        
        self.assertTrue(result)
        mock_get_config.assert_called_with("dev")
        mock_execute.assert_called_once()
    
    @patch('core.cicd.deployer.Deployer._get_deployment_config')
    @patch('core.cicd.deployer.Deployer._execute_deployment')
    def test_deploy_with_models(self, mock_execute, mock_get_config):
        """测试包含模型文件的部署"""
        # Mock 部署配置和执行
        mock_get_config.return_value = {
            "target_path": "/fake/target",
            "backup_before_deploy": False,
            "run_health_check": False,
            "notify_on_deploy": False,
            "model_path": "/fake/models"
        }
        mock_execute.return_value = True
        
        deployer = Deployer(self.project_root)
        result = deployer.deploy("prod", "/fake/artifact", True)
        
        self.assertTrue(result)
        mock_get_config.assert_called_with("prod")
        mock_execute.assert_called_once()
    
    @patch('core.cicd.deployer.Deployer._get_deployment_config')
    @patch('core.cicd.deployer.Deployer._execute_deployment', return_value=False)
    def test_deploy_failure(self, mock_execute, mock_get_config):
        """测试部署失败"""
        # Mock 部署配置
        mock_get_config.return_value = {
            "target_path": "/fake/target",
            "backup_before_deploy": False,
            "run_health_check": False,
            "notify_on_deploy": False,
            "model_path": "/fake/models"
        }
        
        deployer = Deployer(self.project_root)
        result = deployer.deploy("dev", "/fake/artifact", False)
        
        self.assertFalse(result)
        mock_get_config.assert_called_with("dev")
        mock_execute.assert_called_once()
    
    @patch('core.cicd.deployer.Deployer._get_deployment_config')
    @patch('core.cicd.deployer.Deployer._execute_deployment', side_effect=Exception("Unexpected error"))
    def test_deploy_exception(self, mock_execute, mock_get_config):
        """测试部署异常"""
        # Mock 部署配置
        mock_get_config.return_value = {
            "target_path": "/fake/target",
            "backup_before_deploy": False,
            "run_health_check": False,
            "notify_on_deploy": False,
            "model_path": "/fake/models"
        }
        
        deployer = Deployer(self.project_root)
        result = deployer.deploy("dev", "/fake/artifact", False)
        
        self.assertFalse(result)
        mock_get_config.assert_called_with("dev")


if __name__ == '__main__':
    unittest.main()