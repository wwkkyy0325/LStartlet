#!/usr/bin/env python3
"""
CICD Controller Unit Tests
Test the CICDController class functionality
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cicd.cicd_controller import CICDController
from core.cicd.pipeline import Pipeline, Stage, Step


class TestCICDController(unittest.TestCase):
    """测试 CICDController 类"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = str(Path(__file__).parent.parent)
        # 重置配置管理器状态
        from core.config import reset_all_configs
        reset_all_configs()
    
    def tearDown(self):
        """测试后清理"""
        from core.config import reset_all_configs
        reset_all_configs()
    
    @patch('core.cicd.cicd_controller.VersionController')
    @patch('core.cicd.cicd_controller.Builder')
    @patch('core.cicd.cicd_controller.Tester')
    @patch('core.cicd.cicd_controller.Deployer')
    def test_controller_initialization(self, mock_deployer, mock_tester, mock_builder, mock_version_controller):
        """测试控制器初始化"""
        controller = CICDController(self.project_root)
        
        # 验证所有组件都被正确初始化
        mock_version_controller.assert_called_once_with(self.project_root)
        mock_builder.assert_called_once_with(self.project_root)
        mock_tester.assert_called_once_with(self.project_root)
        mock_deployer.assert_called_once_with(self.project_root)
        
        # 验证配置项被正确注册
        from core.config import has_config
        self.assertTrue(has_config("cicd.pipeline.timeout"))
        self.assertTrue(has_config("cicd.build.output_dir"))
        self.assertTrue(has_config("cicd.test.report_dir"))
    
    @patch('core.cicd.cicd_controller.VersionController')
    @patch('core.cicd.cicd_controller.Builder')
    @patch('core.cicd.cicd_controller.Tester')
    @patch('core.cicd.cicd_controller.Deployer')
    def test_run_pipeline_success(self, mock_deployer, mock_tester, mock_builder, mock_version_controller):
        """测试成功运行流水线"""
        controller = CICDController(self.project_root)
        
        # 设置模拟对象的行为
        mock_version_controller.return_value.create_tag.return_value = True
        mock_builder.return_value.get_build_artifacts.return_value = ["./build/artifact.zip"]
        mock_deployer.return_value.deploy.return_value = True

        # 创建测试流水线
        step = Step("test_step", lambda: True)
        stage = Stage("test_stage")
        stage.add_step(step)
        pipeline = Pipeline("test_pipeline")
        pipeline.add_stage(stage)
        
        # 执行流水线
        result = controller.run_pipeline(pipeline, "v1.0.0", "staging")
        
        self.assertTrue(result)
        mock_version_controller.return_value.create_tag.assert_called_once_with("v1.0.0", "Auto-build v1.0.0")
        mock_deployer.return_value.deploy.assert_called_once()
    
    @patch('core.cicd.cicd_controller.VersionController')
    @patch('core.cicd.cicd_controller.Builder')
    @patch('core.cicd.cicd_controller.Tester')
    @patch('core.cicd.cicd_controller.Deployer')

    def test_run_pipeline_failure_in_step(self, mock_deployer, mock_tester, mock_builder, mock_version_controller):
        """测试流水线步骤执行失败（抛出异常）"""
        controller = CICDController(self.project_root)
        
        # 设置版本控制器成功
        mock_version_controller.return_value.create_tag.return_value = True

        # 创建抛出异常的步骤
        def failing_step():
            raise RuntimeError("Step failed")
        
        step = Step("failing_step", failing_step)
        stage = Stage("test_stage")
        stage.add_step(step)
        pipeline = Pipeline("test_pipeline")
        pipeline.add_stage(stage)
        
        # 执行流水线
        result = controller.run_pipeline(pipeline)
        
        self.assertFalse(result)
        # 部署不应该被调用
        mock_deployer.return_value.deploy.assert_not_called()
    
    @patch('core.cicd.cicd_controller.VersionController')
    @patch('core.cicd.cicd_controller.Builder')
    @patch('core.cicd.cicd_controller.Tester')
    @patch('core.cicd.cicd_controller.Deployer')
    def test_run_pipeline_version_tag_failure(self, mock_deployer, mock_tester, mock_builder, mock_version_controller):
        """测试版本标签创建失败"""
        controller = CICDController(self.project_root)
        
        # 设置版本控制器失败
        mock_version_controller.return_value.create_tag.return_value = False
        step = Step("test_step", lambda: True)
        stage = Stage("test_stage")
        stage.add_step(step)
        pipeline = Pipeline("test_pipeline")
        pipeline.add_stage(stage)
        
        # 执行流水线
        result = controller.run_pipeline(pipeline, "v1.0.0")
        
        self.assertFalse(result)
        # 部署不应该被调用
        mock_deployer.return_value.deploy.assert_not_called()
    
    @patch('core.cicd.cicd_controller.VersionController')
    @patch('core.cicd.cicd_controller.Builder')
    @patch('core.cicd.cicd_controller.Tester')
    @patch('core.cicd.cicd_controller.Deployer')
    def test_run_build(self, mock_deployer, mock_tester, mock_builder, mock_version_controller):
        """测试仅运行构建阶段"""
        controller = CICDController(self.project_root)
        
        # 设置构建器成功
        mock_builder.return_value.build.return_value = True
        
        result = controller.run_build(["target1", "target2"])
        
        self.assertTrue(result)
        mock_builder.return_value.build.assert_called_once_with(["target1", "target2"])
    
    @patch('core.cicd.cicd_controller.VersionController')
    @patch('core.cicd.cicd_controller.Builder')
    @patch('core.cicd.cicd_controller.Tester')
    @patch('core.cicd.cicd_controller.Deployer')
    def test_run_tests(self, mock_deployer, mock_tester, mock_builder, mock_version_controller):
        """测试运行测试"""
        controller = CICDController(self.project_root)
        
        # 设置测试器返回结果
        expected_result = {"passed": 10, "failed": 0, "total": 10}
        mock_tester.return_value.run_tests.return_value = expected_result
        
        result = controller.run_tests("unit_tests")
        
        self.assertEqual(result, expected_result)
        mock_tester.return_value.run_tests.assert_called_once_with("unit_tests")


if __name__ == '__main__':
    unittest.main()