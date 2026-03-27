#!/usr/bin/env python3
"""
CICD Builder Unit Tests
Test the Builder class functionality
"""

import sys
import unittest
import tempfile
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cicd.builder import Builder


class TestBuilder(unittest.TestCase):
    """测试 Builder 类"""

    def setUp(self):
        """测试前准备"""
        self.project_root = str(Path(__file__).parent.parent)
        self.temp_dir = tempfile.mkdtemp()
        # 注册并设置配置
        from core.config import register_config, set_config

        register_config("cicd.build.output_dir", "./build", str, "构建输出目录")
        set_config("cicd.build.output_dir", self.temp_dir)

    def tearDown(self):
        """测试后清理"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # 重置配置
        from core.config import reset_all_configs

        reset_all_configs()

    def test_builder_initialization(self):
        """测试构建器初始化"""
        builder = Builder(self.project_root)

        self.assertEqual(builder.project_root, self.project_root)
        self.assertEqual(builder.build_dir, self.temp_dir)

    def test_build_success(self):
        """测试构建成功"""
        builder = Builder(self.project_root)
        result = builder.build(["package"])

        self.assertTrue(result)

    def test_build_package_success(self):
        """测试包构建成功"""
        builder = Builder(self.project_root)
        result = builder._build_package()

        self.assertTrue(result)
        # 验证 artifacts 被正确添加
        self.assertGreater(len(builder.artifacts), 0)

    def test_build_failure_unknown_target(self):
        """测试未知构建目标"""
        builder = Builder(self.project_root)
        result = builder.build(["unknown_target"])

        self.assertTrue(result)  # 未知目标应该被跳过，不导致失败

    def test_get_build_artifacts_empty(self):
        """测试获取空的构建产物"""
        builder = Builder(self.project_root)
        artifacts = builder.get_build_artifacts()

        # 初始状态下应该没有产物
        self.assertEqual(artifacts, [])

    def test_get_build_artifacts_with_files(self):
        """测试获取包含文件的构建产物"""
        # 创建一些模拟的构建产物文件
        artifact1 = os.path.join(self.temp_dir, "artifact1.tar.gz")
        artifact2 = os.path.join(self.temp_dir, "artifact2.zip")

        with open(artifact1, "w") as f:
            f.write("dummy content")
        with open(artifact2, "w") as f:
            f.write("dummy content")

        builder = Builder(self.project_root)
        # 手动添加 artifacts
        builder.artifacts = [artifact1, artifact2]
        artifacts = builder.get_build_artifacts()

        # 应该返回手动添加的文件
        self.assertEqual(len(artifacts), 2)
        self.assertIn(artifact1, artifacts)
        self.assertIn(artifact2, artifacts)


if __name__ == "__main__":
    unittest.main()
