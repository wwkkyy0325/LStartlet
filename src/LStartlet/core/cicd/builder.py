"""
构建器 - 负责项目的编译、打包等构建过程
"""

import os
import shutil
import subprocess
import tarfile
from typing import List, Optional
from datetime import datetime

from LStartlet.core.config import get_config
from LStartlet.core.logger import error, info, warning
from LStartlet.core.path import get_project_root


class Builder:
    """构建器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        self.build_dir = get_config("cicd.build.output_dir", "./build")
        self.artifacts: List[str] = []

    def build(self, targets: Optional[List[str]] = None) -> bool:
        """
        执行构建过程

        Args:
            targets: 构建目标列表

        Returns:
            是否构建成功
        """
        info("开始执行构建过程")

        try:
            # 创建构建目录
            os.makedirs(self.build_dir, exist_ok=True)

            # 默认构建目标
            if targets is None:
                targets = ["package"]

            for target in targets:
                if target == "package":
                    success = self._build_package()
                elif target == "docs":
                    success = self._build_docs()
                elif target == "requirements":
                    success = self._build_requirements()
                else:
                    warning(f"未知的构建目标: {target}")
                    continue

                if not success:
                    error(f"构建目标失败: {target}")
                    return False

            info("构建过程完成")
            return True

        except Exception as e:
            error(f"构建过程异常: {e}")
            return False

    def _build_package(self) -> bool:
        """构建项目包"""
        info("开始打包项目")

        try:
            # 创建版本化的目录名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version = self._get_current_version()
            package_name = f"app_{version}_{timestamp}"
            package_dir = os.path.join(self.build_dir, package_name)

            os.makedirs(package_dir, exist_ok=True)

            # 复制项目文件（排除不需要的文件）
            exclude_patterns = [".git", "__pycache__", "*.pyc", ".gitignore", "tests/"]

            for root, dirs, files in os.walk(self.project_root):
                # 过滤不需要的目录
                dirs[:] = [d for d in dirs if d not in exclude_patterns]

                for file in files:
                    if any(
                        pattern in file or file == pattern
                        for pattern in exclude_patterns
                    ):
                        continue

                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, self.project_root)
                    dst_path = os.path.join(package_dir, rel_path)

                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

                    # 复制文件
                    shutil.copy2(src_path, dst_path)

            # 创建压缩包
            archive_path = f"{package_dir}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(package_dir, arcname=os.path.basename(package_dir))

            self.artifacts.append(archive_path)
            info(f"项目包已创建: {archive_path}")

            return True

        except Exception as e:
            error(f"打包项目时出错: {e}")
            return False

    def _build_docs(self) -> bool:
        """构建文档"""
        info("开始构建文档")

        try:
            docs_src = os.path.join(self.project_root, "docs")
            docs_build_dir = os.path.join(self.build_dir, "docs")

            if not os.path.exists(docs_src):
                info("文档源目录不存在，跳过文档构建")
                return True

            # 清理之前的构建
            if os.path.exists(docs_build_dir):
                shutil.rmtree(docs_build_dir)

            # 复制文档
            shutil.copytree(docs_src, docs_build_dir)

            info(f"文档已构建到: {docs_build_dir}")
            return True

        except Exception as e:
            error(f"构建文档时出错: {e}")
            return False

    def _build_requirements(self) -> bool:
        """构建依赖文件"""
        info("开始构建依赖文件")

        try:
            # 检查是否存在requirements.txt
            req_file = os.path.join(self.project_root, "requirements.txt")

            if not os.path.exists(req_file):
                warning("requirements.txt 不存在，跳过依赖构建")
                return True

            # 复制到构建目录
            target_req_file = os.path.join(self.build_dir, "requirements.txt")
            shutil.copy2(req_file, target_req_file)

            # 如果有额外的依赖处理需求，可以在这里添加
            info(f"依赖文件已复制到: {target_req_file}")
            return True

        except Exception as e:
            error(f"构建依赖文件时出错: {e}")
            return False

    def get_build_artifacts(self) -> List[str]:
        """
        获取构建产物列表

        Returns:
            构建产物路径列表
        """
        return self.artifacts

    def clean_build_artifacts(self) -> bool:
        """
        清理构建产物

        Returns:
            是否清理成功
        """
        try:
            for artifact in self.artifacts:
                if os.path.exists(artifact):
                    os.remove(artifact)
                    info(f"已删除构建产物: {artifact}")

            # 清理构建目录
            if os.path.exists(self.build_dir):
                shutil.rmtree(self.build_dir)
                info(f"已删除构建目录: {self.build_dir}")

            self.artifacts = []
            info("构建产物清理完成")
            return True

        except Exception as e:
            error(f"清理构建产物时出错: {e}")
            return False

    def _get_current_version(self) -> str:
        """获取当前版本"""
        try:
            # 尝试从Git获取版本
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip().replace("-", "_").replace(".", "_")
            else:
                # 如果没有标签，使用commit hash
                result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception as e:
            error(f"获取当前版本时出错: {e}")
            return "unknown"
