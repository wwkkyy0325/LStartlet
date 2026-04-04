"""
插件依赖管理器
实现混合依赖管理模式：检查本地依赖→自动安装到专用目录→支持自包含包回退
"""

import yaml
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any  # type: ignore

# 使用项目自定义日志管理器
from LStartlet.core.logger import info, warning, error

# 使用项目自定义错误处理系统
from LStartlet.core.error import handle_error  # type: ignore
from LStartlet.plugin.exceptions.plugin_exceptions import PluginDependencyError


class PluginDependencyManager:
    """插件依赖管理器"""

    def __init__(self, base_dir: str = "plugin_deps"):
        """
        初始化依赖管理器

        Args:
            base_dir: 插件依赖存储目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.installed_deps: Dict[str, str] = self._load_installed_deps()

    def resolve_dependencies(
        self, plugin_id: str, dependencies: Dict[str, str]
    ) -> bool:
        """
        解析并安装插件依赖

        Args:
            plugin_id: 插件ID
            dependencies: 依赖字典 {包名: 版本要求}

        Returns:
            是否成功解析所有依赖
        """
        if not dependencies:
            return True

        info(f"Starting to resolve dependencies for plugin {plugin_id}...")

        plugin_dep_dir = self.base_dir / plugin_id
        plugin_dep_dir.mkdir(exist_ok=True)

        # 添加插件专用依赖目录到Python路径
        if str(plugin_dep_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dep_dir))

        success = True
        for package_name, version_spec in dependencies.items():
            try:
                if self._check_local_dependency(package_name, version_spec):
                    info(f"依赖 {package_name}{version_spec} 已在本地找到")
                    continue

                if self._install_dependency(plugin_id, package_name, version_spec):
                    info(f"成功安装依赖 {package_name}{version_spec}")
                else:
                    warning(
                        f"无法安装依赖 {package_name}{version_spec}，尝试使用自包含包"
                    )
                    # 这里可以添加自包含包的处理逻辑
                    success = False

            except Exception as e:
                error(f"处理依赖 {package_name}{version_spec} 时出错: {e}")
                success = False

        return success

    def _check_local_dependency(self, package_name: str, version_spec: str) -> bool:
        """
        检查本地是否已存在满足版本要求的依赖

        Args:
            package_name: 包名
            version_spec: 版本要求

        Returns:
            是否满足依赖要求
        """
        try:
            # 处理特殊包名映射（包名与导入名不同）
            import_name = self._get_import_name(package_name)

            # 尝试导入包
            module = __import__(import_name)

            # 如果版本规范是 "*"，只要模块存在就认为满足要求
            if version_spec == "*":
                return True

            # 获取版本信息
            version = self._get_package_version(module, package_name)
            if version is None:
                return False

            # 检查版本是否满足要求
            if self._check_version_compatibility(version, version_spec):
                return True

        except ImportError:
            pass
        except Exception as e:
            warning(f"检查本地依赖 {package_name} 时出错: {e}")

        return False

    def _get_import_name(self, package_name: str) -> str:
        """
        获取包的实际导入名称（处理包名与导入名不同的情况）

        Args:
            package_name: 包名

        Returns:
            实际导入名称
        """
        # 特殊包名映射
        package_mapping = {
            "pillow": "PIL",
            "opencv-python": "cv2",
            "pyyaml": "yaml",
            "beautifulsoup4": "bs4",
        }

        return package_mapping.get(package_name.lower(), package_name)

    def _install_dependency(
        self, plugin_id: str, package_name: str, version_spec: str
    ) -> bool:
        """
        安装依赖到插件专用目录

        Args:
            plugin_id: 插件ID
            package_name: 包名
            version_spec: 版本要求

        Returns:
            安装是否成功
        """
        try:
            plugin_dep_dir = self.base_dir / plugin_id

            # 构建pip安装命令
            package_spec = (
                f"{package_name}{version_spec}" if version_spec else package_name
            )
            cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--target",
                str(plugin_dep_dir),
                "--no-user",
                package_spec,
            ]

            info(f"执行安装命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # 记录已安装的依赖
                self.installed_deps[f"{plugin_id}:{package_name}"] = version_spec
                self._save_installed_deps()
                return True
            else:
                error(f"安装依赖失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            error(f"安装依赖超时: {package_name}{version_spec}")
            return False
        except Exception as e:
            error(f"安装依赖时出错: {e}")
            return False

    def _get_package_version(self, module: Any, package_name: str) -> Optional[str]:
        """
        获取包的版本信息

        Args:
            module: 已导入的模块
            package_name: 包名

        Returns:
            版本字符串或None
        """
        # 尝试多种方式获取版本
        version_attrs = ["__version__", "VERSION", "version"]

        for attr in version_attrs:
            if hasattr(module, attr):
                version = getattr(module, attr)
                if isinstance(version, str):
                    return version
                elif hasattr(version, "__str__"):
                    return str(version)

        # 尝试从metadata获取
        try:
            import importlib.metadata

            return importlib.metadata.version(package_name)
        except (ImportError, Exception):
            pass

        return None

    def _check_version_compatibility(
        self, installed_version: str, required_spec: str
    ) -> bool:
        """
        检查版本兼容性

        Args:
            installed_version: 已安装的版本
            required_spec: 版本要求规范

        Returns:
            是否兼容
        """
        if not required_spec or required_spec == "*":
            return True

        try:
            from packaging import version, specifiers

            installed = version.parse(installed_version)
            specifier = specifiers.SpecifierSet(required_spec)
            return installed in specifier
        except ImportError:
            # 如果没有packaging库，进行简单比较
            return self._simple_version_check(installed_version, required_spec)
        except Exception as e:
            warning(f"版本检查失败，假设兼容: {e}")
            return True

    def _simple_version_check(self, installed_version: str, required_spec: str) -> bool:
        """
        简单版本检查（当packaging不可用时）
        """
        # 移除前缀操作符
        clean_spec = required_spec.lstrip(">=><=!~")

        if ">=" in required_spec:
            return self._compare_versions(installed_version, clean_spec) >= 0
        elif ">" in required_spec:
            return self._compare_versions(installed_version, clean_spec) > 0
        elif "<=" in required_spec:
            return self._compare_versions(installed_version, clean_spec) <= 0
        elif "<" in required_spec:
            return self._compare_versions(installed_version, clean_spec) < 0
        elif "==" in required_spec or required_spec == clean_spec:
            return installed_version == clean_spec
        else:
            # 其他情况假设兼容
            return True

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        比较两个版本字符串

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]

            # 补齐较短的版本
            max_len = max(len(parts1), len(parts2))
            parts1.extend([0] * (max_len - len(parts1)))
            parts2.extend([0] * (max_len - len(parts2)))

            for p1, p2 in zip(parts1, parts2):
                if p1 < p2:
                    return -1
                elif p1 > p2:
                    return 1
            return 0
        except ValueError:
            # 如果版本包含非数字字符，进行字符串比较
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0

    def _load_installed_deps(self) -> Dict[str, str]:
        """加载已安装的依赖记录"""
        deps_file = self.base_dir / "installed_deps.yaml"
        if deps_file.exists():
            try:
                with open(deps_file, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                warning(f"加载已安装依赖记录失败: {e}")
        return {}

    def _save_installed_deps(self):
        """保存已安装的依赖记录"""
        deps_file = self.base_dir / "installed_deps.yaml"
        try:
            with open(deps_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.installed_deps,
                    f,
                    allow_unicode=True,
                    indent=2,
                    sort_keys=False,
                )
        except Exception as e:
            error(f"保存已安装依赖记录失败: {e}")

    def cleanup_plugin_dependencies(self, plugin_id: str):
        """
        清理插件的依赖

        Args:
            plugin_id: 插件ID
        """
        plugin_dep_dir = self.base_dir / plugin_id
        if plugin_dep_dir.exists():
            import shutil

            try:
                shutil.rmtree(plugin_dep_dir)
                info(f"已清理插件 {plugin_id} 的依赖目录")
            except Exception as e:
                error(f"清理插件依赖目录失败: {e}")

        # 清理记录
        keys_to_remove = [
            k for k in self.installed_deps.keys() if k.startswith(f"{plugin_id}:")
        ]
        for key in keys_to_remove:
            del self.installed_deps[key]
        self._save_installed_deps()

    def check_dependency_availability(
        self, package_name: str, version_spec: str
    ) -> bool:
        """
        检查依赖是否可用（在主程序环境中）

        Args:
            package_name: 包名
            version_spec: 版本要求

        Returns:
            依赖是否可用
        """
        return self._check_local_dependency(package_name, version_spec)
