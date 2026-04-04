#!/usr/bin/env python3
"""
Dependency Resolver Unit Tests
Test the DependencyResolver class functionality
"""

import sys
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from LStartlet.core.version_control.dependency_resolver import DependencyResolver


class TestDependencyResolver(unittest.TestCase):
    """测试 DependencyResolver 类"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = self.temp_dir
        
        # 创建模拟的Python文件用于测试依赖分析
        test_py_file = os.path.join(self.temp_dir, "test_module.py")
        with open(test_py_file, "w", encoding="utf-8") as f:
            f.write("import os\n")
            f.write("import sys\n")
            f.write("import requests\n")
            f.write("from pathlib import Path\n")
            # 创建一个实际的项目模块文件
            f.write("from .local_module import helper\n")

        # 创建本地模块文件
        local_module_file = os.path.join(self.temp_dir, "local_module.py")
        with open(local_module_file, "w", encoding="utf-8") as f:
            f.write("# Local module\n")
            f.write("def helper():\n")
            f.write("    pass\n")

        # 创建requirements.txt文件
        self.req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(self.req_file, "w", encoding="utf-8") as f:
            f.write("requests>=2.25.1\n")
            f.write("PyYAML>=6.0\n")

        # 重置配置
        from LStartlet.core.config import reset_all_configs
        reset_all_configs()

    def tearDown(self):
        """测试后清理"""
        from LStartlet.core.config import reset_all_configs
        reset_all_configs()
        
        # 清理临时目录
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """测试依赖解析器初始化"""
        resolver = DependencyResolver(self.project_root)
        
        self.assertEqual(resolver.project_root, self.project_root)
        self.assertIsInstance(resolver.stdlib_modules, set)
        self.assertIn("os", resolver.stdlib_modules)
        self.assertIn("sys", resolver.stdlib_modules)

    def test_analyze_dependencies_success(self):
        """测试成功分析依赖"""
        resolver = DependencyResolver(self.project_root)
        
        result = resolver.analyze_dependencies()
        
        self.assertIsInstance(result, dict)
        self.assertIn("external", result)
        self.assertIn("project", result)
        
        external_deps = result["external"]
        project_deps = result["project"]
        
        # requests 应该是外部依赖
        self.assertIn("requests", external_deps)
        # local_module 应该是项目依赖
        self.assertIn("local_module", project_deps)

    def test_analyze_dependencies_empty_directory(self):
        """测试分析空目录"""
        empty_dir = tempfile.mkdtemp()
        resolver = DependencyResolver(empty_dir)
        
        result = resolver.analyze_dependencies()
        
        self.assertEqual(result["external"], set())
        self.assertEqual(result["project"], set())
        
        # 清理
        import shutil
        shutil.rmtree(empty_dir)

    def test_get_external_dependencies(self):
        """测试获取外部依赖列表"""
        resolver = DependencyResolver(self.project_root)
        
        external_deps = resolver.get_external_dependencies()
        
        self.assertIsInstance(external_deps, set)
        self.assertIn("requests", external_deps)

    @patch("LStartlet.core.version_control.dependency_resolver.subprocess.run")
    def test_generate_requirements_txt_success(self, mock_subprocess):
        """测试成功生成requirements.txt"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "requests==2.28.1\nPyYAML==6.0\nos==1.0\n"
        mock_subprocess.return_value = mock_result
        
        resolver = DependencyResolver(self.project_root)
        output_file = os.path.join(self.temp_dir, "generated_req.txt")
        
        result = resolver.generate_requirements_txt(output_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))
        
        # 验证文件内容（使用utf-8编码）
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("requests==2.28.1", content)
            # 只验证项目实际使用的依赖，PyYAML可能不在其中

    @patch("LStartlet.core.version_control.dependency_resolver.subprocess.run")
    def test_generate_requirements_txt_failure(self, mock_subprocess):
        """测试生成requirements.txt失败"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Command failed"
        mock_subprocess.return_value = mock_result
        
        resolver = DependencyResolver(self.project_root)
        output_file = os.path.join(self.temp_dir, "failed_req.txt")
        
        result = resolver.generate_requirements_txt(output_file)
        
        self.assertFalse(result)
        self.assertFalse(os.path.exists(output_file))

    def test_compare_with_requirements_no_differences(self):
        """测试与requirements文件比较无差异"""
        # 创建一个匹配的requirements文件
        req_file = os.path.join(self.temp_dir, "matching_req.txt")
        with open(req_file, "w", encoding="utf-8") as f:
            f.write("requests>=2.25.1\n")
            f.write("# PyYAML is also used\n")
            f.write("PyYAML==6.0\n")
        
        resolver = DependencyResolver(self.project_root)
        result = resolver.compare_with_requirements(req_file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("in_project_not_in_req", result)
        self.assertIn("in_req_not_in_project", result)
        self.assertIn("common", result)
        
        # requests应该在共同部分
        self.assertIn("requests", result["common"])

    def test_compare_with_requirements_with_differences(self):
        """测试与requirements文件比较有差异"""
        # 创建一个不匹配的requirements文件
        req_file = os.path.join(self.temp_dir, "different_req.txt")
        with open(req_file, "w", encoding="utf-8") as f:
            f.write("numpy>=1.21.0\n")  # numpy不在项目中使用
        
        resolver = DependencyResolver(self.project_root)
        result = resolver.compare_with_requirements(req_file)
        
        # requests在项目中但不在req文件中
        self.assertIn("requests", result["in_project_not_in_req"])
        # numpy在req文件中但不在项目中
        self.assertIn("numpy", result["in_req_not_in_project"])

    def test_compare_with_nonexistent_requirements(self):
        """测试与不存在的requirements文件比较"""
        nonexistent_req = os.path.join(self.temp_dir, "nonexistent.txt")
        
        resolver = DependencyResolver(self.project_root)
        result = resolver.compare_with_requirements(nonexistent_req)
        
        # 所有项目依赖都应该在in_project_not_in_req中
        self.assertIn("requests", result["in_project_not_in_req"])
        self.assertEqual(result["in_req_not_in_project"], set())

    def test_extract_imports_from_syntax_error_file(self):
        """测试从语法错误的文件中提取导入"""
        invalid_py_file = os.path.join(self.temp_dir, "invalid.py")
        with open(invalid_py_file, "w", encoding="utf-8") as f:
            f.write("def invalid syntax(\n")  # 语法错误
        
        resolver = DependencyResolver(self.project_root)
        imports = resolver._extract_imports(invalid_py_file)
        
        self.assertEqual(imports, set())

    def test_analyze_dependencies_with_subdirectories(self):
        """测试分析包含子目录的项目"""
        sub_dir = os.path.join(self.temp_dir, "submodule")
        os.makedirs(sub_dir)
        
        sub_py_file = os.path.join(sub_dir, "sub_module.py")
        with open(sub_py_file, "w", encoding="utf-8") as f:
            f.write("import json\n")
            f.write("import pandas\n")
        
        resolver = DependencyResolver(self.project_root)
        result = resolver.analyze_dependencies()
        
        external_deps = result["external"]
        # pandas应该是外部依赖
        self.assertIn("pandas", external_deps)
        # json是标准库，不应该出现在外部依赖中
        self.assertNotIn("json", external_deps)

    @patch("LStartlet.core.version_control.dependency_resolver.os.walk")
    def test_analyze_dependencies_os_walk_exception(self, mock_walk):
        """测试os.walk异常处理"""
        mock_walk.side_effect = Exception("OS error")
        
        resolver = DependencyResolver(self.project_root)
        result = resolver.analyze_dependencies()
        
        self.assertEqual(result["external"], set())
        self.assertEqual(result["project"], set())


if __name__ == "__main__":
    unittest.main()