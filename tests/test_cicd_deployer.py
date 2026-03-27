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

    @patch("core.cicd.deployer.Deployer._get_deployment_config")
    def test_deploy_success(self, mock_get_config):
        """测试部署成功"""
        deployer = Deployer()

        # 设置模拟对象
        mock_get_config.return_value = {"host": "localhost", "port": 8080}

        with patch.object(deployer, "_execute_deployment") as mock_deploy:
            mock_deploy.return_value = True

            result = deployer.deploy("dev", "/fake/artifact")

            self.assertTrue(result)
            mock_get_config.assert_called_once_with("dev")
            mock_deploy.assert_called_once_with(
                "dev", "/fake/artifact", {"host": "localhost", "port": 8080}
            )

    @patch("core.cicd.deployer.Deployer._get_deployment_config")
    def test_deploy_failure(self, mock_get_config):
        """测试部署失败"""
        deployer = Deployer()

        # 设置模拟对象
        mock_get_config.return_value = {"host": "localhost", "port": 8080}

        with patch.object(deployer, "_execute_deployment") as mock_deploy:
            mock_deploy.return_value = False

            result = deployer.deploy("dev", "/fake/artifact")

            self.assertFalse(result)
            mock_get_config.assert_called_once_with("dev")
            mock_deploy.assert_called_once_with(
                "dev", "/fake/artifact", {"host": "localhost", "port": 8080}
            )

    @patch("core.cicd.deployer.Deployer._get_deployment_config")
    def test_deploy_with_models(self, mock_get_config):
        """测试包含模型文件的部署"""
        deployer = Deployer()

        # 设置模拟对象
        mock_get_config.return_value = {"host": "localhost", "port": 8080}

        with patch.object(deployer, "_execute_deployment") as mock_deploy:
            mock_deploy.return_value = True

            result = deployer.deploy("prod", "/fake/artifact")

            self.assertTrue(result)
            mock_get_config.assert_called_once_with("prod")
            mock_deploy.assert_called_once_with(
                "prod", "/fake/artifact", {"host": "localhost", "port": 8080}
            )

    @patch("core.cicd.deployer.Deployer._get_deployment_config")
    def test_deploy_exception(self, mock_get_config):
        """测试部署异常"""
        deployer = Deployer()

        # 设置模拟对象
        mock_get_config.return_value = {"host": "localhost", "port": 8080}

        with patch.object(deployer, "_execute_deployment") as mock_deploy:
            mock_deploy.side_effect = Exception("Deployment failed")

            result = deployer.deploy("dev", "/fake/artifact")

            self.assertFalse(result)
            mock_get_config.assert_called_once_with("dev")
            mock_deploy.assert_called_once_with(
                "dev", "/fake/artifact", {"host": "localhost", "port": 8080}
            )


if __name__ == "__main__":
    unittest.main()
