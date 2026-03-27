"""
依赖解析器 - 分析项目依赖关系
"""

import ast
import os
import subprocess
import sys
from typing import Dict, Set, Optional

from LStartlet.core.logger import info, warning, error
from LStartlet.core.path import get_project_root


class DependencyResolver:
    """依赖解析器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()

        # Python标准库模块
        stdlib_names = getattr(sys, "stdlib_module_names", None)
        if stdlib_names is not None:
            self.stdlib_modules = set(stdlib_names)
        else:
            self.stdlib_modules = self._get_stdlib_modules()

    def _get_stdlib_modules(self) -> Set[str]:
        """获取Python标准库模块列表"""
        stdlib_modules: Set[str] = set()
        try:
            # 尝试导入所有可能的标准库模块
            for module_name in sys.builtin_module_names:
                stdlib_modules.add(module_name)

            # 添加常见的标准库模块
            common_stdlib = {
                "os",
                "sys",
                "pathlib",
                "json",
                "yaml",
                "re",
                "datetime",
                "collections",
                "itertools",
                "functools",
                "typing",
                "abc",
                "logging",
                "subprocess",
                "threading",
                "multiprocessing",
                "unittest",
                "pytest",
                "argparse",
                "configparser",
                "shutil",
                "tempfile",
                "glob",
                "fnmatch",
                "hashlib",
                "base64",
                "uuid",
                "inspect",
                "ast",
                "tokenize",
                "dis",
                "pickle",
                "csv",
                "xml",
                "html",
                "urllib",
                "http",
                "email",
                "ssl",
                "socket",
                "select",
                "asyncio",
                "queue",
                "heapq",
                "bisect",
                "copy",
                "pprint",
                "textwrap",
            }
            stdlib_modules.update(common_stdlib)
        except Exception as e:
            warning(f"获取标准库模块时出错: {e}")

        return stdlib_modules

    def analyze_dependencies(
        self, directory: Optional[str] = None
    ) -> Dict[str, Set[str]]:
        """
        分析项目依赖

        Args:
            directory: 要分析的目录路径，默认为项目根目录

        Returns:
            依赖关系字典，键为依赖类型，值为包名集合
        """
        directory = directory or self.project_root

        external_deps: Set[str] = set()
        project_deps: Set[str] = set()

        for root, dirs, files in os.walk(directory):
            # 跳过某些目录
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in {"__pycache__", "venv", "env", "node_modules"}
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        file_deps = self._extract_imports(file_path)

                        for dep in file_deps:
                            # 移除包名中的子模块部分（如将 sklearn.preprocessing 改为 sklearn）
                            main_package = dep.split(".")[0]

                            if main_package in self.stdlib_modules:
                                continue  # 标准库模块
                            else:
                                # 检查是否是项目内部模块
                                project_module_path = os.path.join(
                                    self.project_root, *dep.split(".")
                                )
                                init_path = os.path.join(
                                    project_module_path, "__init__.py"
                                )

                                if os.path.exists(
                                    project_module_path
                                ) or os.path.exists(init_path):
                                    project_deps.add(dep)
                                else:
                                    external_deps.add(main_package)
                    except Exception as e:
                        warning(f"分析文件 {file_path} 时出错: {e}")

        info(
            f"分析完成 - 外部依赖: {len(external_deps)}, 项目依赖: {len(project_deps)}"
        )

        return {"external": external_deps, "project": project_deps}

    def _extract_imports(self, file_path: str) -> Set[str]:
        """从Python文件中提取导入的模块"""
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                warning(f"无法解析文件 {file_path}，跳过")
                return set()

        imports: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if (
                    node.module
                ):  # 检查是否有模块名（例如，from . import xxx 没有模块名）
                    imports.add(node.module)

        return imports

    def get_external_dependencies(self) -> Set[str]:
        """
        获取外部依赖列表

        Returns:
            外部依赖包名集合
        """
        analysis_result = self.analyze_dependencies()
        return analysis_result["external"]

    def generate_requirements_txt(self, output_file: str = "requirements.txt") -> bool:
        """
        基于当前环境生成requirements.txt文件

        Args:
            output_file: 输出文件路径

        Returns:
            是否生成成功
        """
        try:
            # 获取当前环境的包列表
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True
            )

            if result.returncode != 0:
                error(f"获取包列表失败: {result.stderr}")
                return False

            all_packages = result.stdout.strip().split("\n")

            # 获取项目依赖
            project_deps = self.analyze_dependencies()
            required_packages: Set[str] = project_deps["external"]

            # 过滤出项目实际使用的包
            filtered_packages: list[str] = []
            for pkg in all_packages:
                # 处理包名（去掉版本号部分）
                pkg_name = (
                    pkg.split("==")[0]
                    .split(">=")[0]
                    .split("<=")[0]
                    .split(">")[0]
                    .split("<")[0]
                    .split("~=")[0]
                )
                # 处理一些特殊情况
                pkg_name = pkg_name.replace("_", "-").lower()

                for req_pkg in required_packages:
                    req_normalized = req_pkg.replace("_", "-").lower()
                    if pkg_name == req_normalized or pkg_name.startswith(
                        req_normalized + "-"
                    ):
                        filtered_packages.append(pkg)
                        break

            # 写入文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# 项目依赖列表\n")
                f.write("# 由依赖解析器自动生成\n\n")

                for package in filtered_packages:
                    f.write(package + "\n")

            info(f"requirements.txt 已生成: {output_file}")
            return True

        except Exception as e:
            error(f"生成 requirements.txt 时出错: {e}")
            return False

    def compare_with_requirements(
        self, requirements_file: str = "requirements.txt"
    ) -> Dict[str, Set[str]]:
        """
        比较项目实际依赖与requirements.txt文件的差异

        Args:
            requirements_file: requirements文件路径

        Returns:
            比较结果字典
        """
        # 获取当前项目依赖
        current_deps = self.get_external_dependencies()

        # 读取requirements文件
        required_deps: Set[str] = set()
        if os.path.exists(requirements_file):
            with open(requirements_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # 提取包名（去掉版本号）
                        pkg_name = (
                            line.split("==")[0]
                            .split(">=")[0]
                            .split("<=")[0]
                            .split(">")[0]
                            .split("<")[0]
                            .split("~=")[0]
                        )
                        required_deps.add(pkg_name)

        return {
            "in_project_not_in_req": current_deps
            - required_deps,  # 在项目中但不在req文件中的
            "in_req_not_in_project": required_deps
            - current_deps,  # 在req文件中但不在项目中的
            "common": current_deps & required_deps,  # 共同的
        }
