"""
CI/CD流水线装饰器实现 - 让用户通过装饰器定义构建步骤
"""

import os
import subprocess
import sys
from typing import List, Callable, Optional
from pathlib import Path

from ._logging_functions import info, warning, error
from ._path_manager import get_project_root


class PipelineStep:
    """流水线步骤定义"""

    def __init__(self, func: Callable, name: str, order: int):
        self.func = func
        self.name = name
        self.order = order

    def execute(self) -> bool:
        """执行步骤"""
        try:
            info(f"执行步骤: {self.name}")
            result = self.func()
            if result is False:
                error(f"步骤 {self.name} 执行失败")
                return False
            info(f"步骤 {self.name} 执行成功")
            return True
        except Exception as e:
            error(f"步骤 {self.name} 执行异常: {e}")
            return False


class SimpleCICDPipeline:
    """简单的CI/CD流水线管理器"""

    def __init__(self):
        self.steps: List[PipelineStep] = []

    def add_step(self, func: Callable, name: Optional[str] = None, order: int = 0):
        """添加步骤到流水线"""
        step_name = name or func.__name__
        step = PipelineStep(func, step_name, order)
        self.steps.append(step)
        # 按顺序排序
        self.steps.sort(key=lambda x: x.order)

    def run(self) -> bool:
        """运行整个流水线"""
        info("开始执行CI/CD流水线")

        for step in self.steps:
            if not step.execute():
                error("CI/CD流水线执行失败")
                return False

        info("CI/CD流水线执行成功")
        return True


# 全局流水线实例
_cicd_pipeline = SimpleCICDPipeline()


def cicd_step(name: Optional[str] = None, order: int = 0):
    """
    CI/CD流水线步骤装饰器

    Args:
        name: 步骤名称，如果不提供则使用函数名
        order: 执行顺序，数字越小越先执行

    Example:
        @cicd_step("run_tests", order=1)
        def run_unit_tests():
            # 运行单元测试
            return True

        @cicd_step("build_package", order=2)
        def build_package():
            # 打包
            return True
    """

    def decorator(func: Callable) -> Callable:
        _cicd_pipeline.add_step(func, name, order)
        return func

    return decorator


def run_cicd_pipeline() -> bool:
    """
    运行CI/CD流水线

    Returns:
        是否成功执行所有步骤
    """
    return _cicd_pipeline.run()


# 预定义的常用步骤函数
def run_tests() -> bool:
    """运行测试"""
    try:
        # 尝试运行pytest
        project_root = get_project_root()
        result = subprocess.run(
            [sys.executable, "-m", "pytest", project_root],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        error(f"运行测试失败: {e}")
        return False


def run_code_quality_check() -> bool:
    """运行代码质量检查"""
    try:
        # 尝试运行flake8或ruff
        project_root = get_project_root()

        # 先尝试 ruff
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "."],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            pass  # ruff 未安装

        # 再尝试 flake8
        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", "."],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            warning("未找到代码质量检查工具 (ruff 或 flake8)")
            return True  # 如果没有安装工具，跳过检查

    except Exception as e:
        error(f"代码质量检查失败: {e}")
        return False


def create_git_tag(tag_name: str, message: str = "") -> bool:
    """创建Git标签"""
    try:
        project_root = get_project_root()
        cmd = ["git", "tag", "-a", tag_name]
        if message:
            cmd.extend(["-m", message])
        else:
            cmd.extend(["-m", f"Release {tag_name}"])

        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        error(f"创建Git标签失败: {e}")
        return False


def build_package() -> bool:
    """构建Python包"""
    try:
        project_root = get_project_root()
        # 使用build工具构建
        result = subprocess.run(
            [sys.executable, "-m", "build"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        error(f"构建包失败: {e}")
        return False


def publish_package() -> bool:
    """发布包到PyPI"""
    try:
        project_root = get_project_root()
        # 使用twine发布
        dist_path = os.path.join(project_root, "dist")
        if not os.path.exists(dist_path):
            error("dist目录不存在，无法发布")
            return False

        result = subprocess.run(
            [sys.executable, "-m", "twine", "upload", "dist/*"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        error(f"发布包失败: {e}")
        return False
