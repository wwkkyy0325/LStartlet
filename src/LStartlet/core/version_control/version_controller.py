"""
版本控制器 - 管理代码版本、生成增量包和依赖关系
"""

import os
import json
import hashlib
import subprocess
from typing import Dict, List, Optional
from datetime import datetime

from LStartlet.core.logger import info, error
from LStartlet.core.config import get_config, register_config
from LStartlet.core.path import get_project_root


class ChangeAnalyzer:
    """变更分析器 - 分析代码变更情况"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()

    def analyze_changes(
        self, base_commit: str = "HEAD~1", target_commit: str = "HEAD"
    ) -> Dict[str, List[str]]:
        """
        分析两次提交之间的变更

        Args:
            base_commit: 基础提交
            target_commit: 目标提交

        Returns:
            变更详情字典，包含 added, modified, deleted 文件列表
        """
        try:
            # 获取变更文件列表
            diff_cmd = ["git", "diff", "--name-status", base_commit, target_commit]
            result = subprocess.run(
                diff_cmd, cwd=self.project_root, capture_output=True, text=True
            )

            changes: Dict[str, List[str]] = {"added": [], "modified": [], "deleted": []}

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if line:
                        parts = line.split("\t")
                        if len(parts) >= 2:
                            status, filepath = parts[0], parts[1]
                            if status.lower().startswith("a"):
                                changes["added"].append(filepath)
                            elif status.lower().startswith("m"):
                                changes["modified"].append(filepath)
                            elif status.lower().startswith("d"):
                                changes["deleted"].append(filepath)

            info(
                f"分析变更完成: {len(changes['added'])} 个新增, {len(changes['modified'])} 个修改, {len(changes['deleted'])} 个删除"
            )
            return changes
        except Exception as e:
            error(f"分析变更时出错: {e}")
            return {"added": [], "modified": [], "deleted": []}

    def get_file_hash(self, filepath: str) -> str:
        """获取文件的哈希值"""
        full_path = os.path.join(self.project_root, filepath)
        if not os.path.exists(full_path):
            return ""

        hash_sha256 = hashlib.sha256()
        with open(full_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class IncrementalPackageGenerator:
    """增量包生成器 - 根据变更生成增量包"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        self.analyzer = ChangeAnalyzer(project_root)

    def generate_incremental_package(
        self,
        base_commit: str = "HEAD~1",
        target_commit: str = "HEAD",
        output_dir: str = "./incremental_packages",
    ) -> Optional[str]:
        """
        生成增量包

        Args:
            base_commit: 基准提交
            target_commit: 目标提交
            output_dir: 输出目录

        Returns:
            增量包路径，如果失败则返回None
        """
        try:
            # 获取变更文件
            changes = self.analyzer.analyze_changes(base_commit, target_commit)
            if not changes:
                from LStartlet.core.logger import warning

                warning("没有检测到文件变更，跳过增量包生成")
                return None

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            # 生成增量包文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            package_name = f"incremental_{base_commit}_{target_commit}_{timestamp}.zip"
            package_path = os.path.join(output_dir, package_name)

            # 准备要打包的文件
            files_to_pack = changes["added"] + changes["modified"]

            # 使用zip命令打包文件
            import zipfile

            with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_pack:
                    full_path = os.path.join(self.project_root, file_path)
                    if os.path.exists(full_path):
                        zipf.write(full_path, file_path)

                # 创建变更记录文件
                changes_record: Dict[str, object] = {
                    "base_commit": base_commit,
                    "target_commit": target_commit,
                    "generated_at": datetime.now().isoformat(),
                    "changes": changes,
                }

                # 写入变更记录到zip
                zipf.writestr(
                    "changes.json",
                    json.dumps(changes_record, indent=2, ensure_ascii=False),
                )

            info(f"增量包生成成功: {package_path}")
            return package_path

        except Exception as e:
            error(f"生成增量包时出错: {e}")
            return None


class VersionController:
    """版本控制器主类"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        self.change_analyzer = ChangeAnalyzer(project_root)
        self.incremental_generator = IncrementalPackageGenerator(project_root)

        # 注册版本控制器相关的配置
        register_config(
            "version_control.output_dir",
            "./incremental_packages",
            str,
            "增量包输出目录",
        )
        register_config(
            "version_control.include_dependencies",
            True,
            bool,
            "是否包含依赖信息到增量包",
        )

    def get_current_version(self) -> str:
        """获取当前版本"""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
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

    def create_tag(self, tag_name: str, message: str = "") -> bool:
        """创建标签"""
        try:
            cmd = ["git", "tag", "-a", tag_name, "-m", message or f"Release {tag_name}"]
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )
            if result.returncode == 0:
                info(f"标签 {tag_name} 创建成功")
                return True
            else:
                error(f"创建标签失败: {result.stderr}")
                return False
        except Exception as e:
            error(f"创建标签时出错: {e}")
            return False

    def generate_incremental_package(
        self,
        base_version: str,
        target_version: str = "HEAD",
        include_dependencies: bool = True,
    ) -> Optional[str]:
        """
        生成增量包

        Args:
            base_version: 基础版本
            target_version: 目标版本
            include_dependencies: 是否包含依赖信息

        Returns:
            生成的增量包路径
        """
        output_dir = get_config("version_control.output_dir", "./incremental_packages")

        package_path = self.incremental_generator.generate_incremental_package(
            base_version, target_version, output_dir
        )

        if package_path and include_dependencies:
            self._add_dependency_info(package_path)

        return package_path

    def _add_dependency_info(self, package_path: str):
        """向增量包添加依赖信息"""
        try:
            import zipfile
            import tempfile

            # 创建临时文件来存储依赖信息
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as temp_file:
                # 获取当前项目的依赖信息
                dependencies = self.get_dependencies()

                temp_file.write(json.dumps(dependencies, indent=2, ensure_ascii=False))
                temp_file.flush()

                # 将依赖信息添加到zip包
                with zipfile.ZipFile(package_path, "a", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(temp_file.name, "dependencies.json")

                # 删除临时文件
                os.unlink(temp_file.name)

            info(f"已将依赖信息添加到增量包: {package_path}")
        except Exception as e:
            error(f"添加依赖信息到增量包时出错: {e}")

    def get_dependencies(self) -> Dict[str, str]:
        """获取项目依赖信息"""
        dependencies: Dict[str, str] = {}

        # 读取 requirements.txt
        req_file = os.path.join(self.project_root, "requirements.txt")
        if os.path.exists(req_file):
            try:
                with open(req_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "==" in line:
                                pkg, ver = line.split("==", 1)
                                dependencies[pkg.strip()] = ver.strip()
                            elif ">=" in line:
                                pkg, ver = line.split(">=", 1)
                                dependencies[pkg.strip()] = f">={ver.strip()}"
                            elif "<=" in line:
                                pkg, ver = line.split("<=", 1)
                                dependencies[pkg.strip()] = f"<={ver.strip()}"
                            else:
                                dependencies[line] = "*"
            except Exception as e:
                error(f"读取依赖文件时出错: {e}")

        return dependencies
