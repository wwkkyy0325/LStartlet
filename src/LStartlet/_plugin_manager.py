"""
LStartlet 插件系统 - 框架定义钩子，插件订阅钩子

插件系统特点：
1. 框架定义钩子点
2. 插件订阅框架的钩子
3. 插件管理器只负责加载/卸载插件
4. 类似 Minecraft/VSCode 的插件管理方式
5. 插件基于应用，默认从 .lstartlet/{app_name}/plugins 目录加载
6. 只支持 wheel 包格式
7. 支持插件依赖声明和自动补全
"""

import importlib
import importlib.util
import sys
import os
import zipfile
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from ._logging import (
    _log_framework_info,
    _log_framework_warning,
    _log_framework_error,
    _log_framework_debug,
)
from ._application_info import _get_application_info


@dataclass
class _PluginInfo:
    """插件信息（内部实现）"""

    name: str
    path: str
    module: Any = None
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    enabled: bool = True
    loaded: bool = False
    dependencies: List[str] = field(default_factory=list)
    is_wheel: bool = False
    wheel_path: Optional[str] = None


class _PluginManager:
    """插件管理器（内部实现）"""

    def __init__(self, app_name: Optional[str] = None, framework: Optional[Any] = None):
        self._plugins: Dict[str, _PluginInfo] = {}
        self._plugin_dirs: List[str] = []
        self._framework = framework
        self._app_name = app_name

        if self._app_name is None:
            metadata = _get_application_info()
            if metadata:
                self._app_name = metadata.display_name or metadata.directory_name
                _log_framework_info(f"自动获取应用名称: {self._app_name}")

        if self._app_name:
            default_plugin_dir = self._get_default_plugin_dir()
            if default_plugin_dir:
                self.add_plugin_dir(default_plugin_dir)

        if self._plugin_dirs:
            _log_framework_info("自动加载插件...")
            self._auto_load()

    def _get_default_plugin_dir(self) -> Optional[str]:
        """获取默认插件目录"""
        if not self._app_name:
            return None

        from ._path_manager import _get_app_path

        plugin_dir = _get_app_path(self._app_name, "plugins")
        return plugin_dir

    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """检查依赖是否满足"""
        missing = []
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)
        return missing

    def _install_dependencies(self, dependencies: List[str]) -> bool:
        """安装缺失的依赖"""
        if not dependencies:
            return True

        try:
            _log_framework_info(f"正在安装依赖: {', '.join(dependencies)}")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + dependencies
            )
            _log_framework_info(f"依赖安装成功: {', '.join(dependencies)}")
            return True
        except subprocess.CalledProcessError as e:
            _log_framework_error(f"依赖安装失败: {e}")
            return False

    def _extract_wheel(self, wheel_path: str) -> Optional[str]:
        """解压 wheel 包"""
        try:
            temp_dir = tempfile.mkdtemp(prefix="lstartlet_plugin_")

            with zipfile.ZipFile(wheel_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            _log_framework_info(f"wheel 包解压成功: {wheel_path} -> {temp_dir}")
            return temp_dir
        except Exception as e:
            _log_framework_error(f"wheel 包解压失败: {wheel_path}, 错误: {e}")
            return None

    def add_plugin_dir(self, plugin_dir: str):
        """添加插件目录"""
        if plugin_dir not in self._plugin_dirs:
            self._plugin_dirs.append(plugin_dir)
            _log_framework_info(f"添加插件目录: {plugin_dir}")

    def load_plugin(
        self, plugin_path: str, plugin_name: Optional[str] = None
    ) -> Optional[Any]:
        """加载单个插件"""
        try:
            is_wheel = plugin_path.endswith(".whl")

            if is_wheel:
                _log_framework_info(f"检测到 wheel 包: {plugin_path}")

                extracted_dir = self._extract_wheel(plugin_path)
                if not extracted_dir:
                    _log_framework_error(f"wheel 包解压失败: {plugin_path}")
                    return None

                module_dir = None
                for item in os.listdir(extracted_dir):
                    item_path = os.path.join(extracted_dir, item)
                    if os.path.isdir(item_path) and not item.startswith("_"):
                        module_dir = item_path
                        break

                if not module_dir:
                    _log_framework_error(f"无法在 wheel 包中找到主模块: {plugin_path}")
                    shutil.rmtree(extracted_dir, ignore_errors=True)
                    return None

                if plugin_name is None:
                    plugin_name = os.path.basename(module_dir)

                if plugin_name in self._plugins:
                    _log_framework_warning(f"插件已加载: {plugin_name}")
                    shutil.rmtree(extracted_dir, ignore_errors=True)
                    return None

                sys.path.insert(0, extracted_dir)

                module = importlib.import_module(plugin_name)

                plugin_info = _PluginInfo(
                    name=plugin_name,
                    path=plugin_path,
                    module=module,
                    enabled=True,
                    loaded=True,
                    is_wheel=True,
                    wheel_path=plugin_path,
                )

            else:
                if plugin_name is None:
                    if os.path.isfile(plugin_path):
                        plugin_name = Path(plugin_path).stem
                    else:
                        plugin_name = os.path.basename(plugin_path.rstrip(os.sep))

                if plugin_name in self._plugins:
                    _log_framework_warning(f"插件已加载: {plugin_name}")
                    return None

                if os.path.isfile(plugin_path):
                    spec = importlib.util.spec_from_file_location(
                        plugin_name, plugin_path
                    )
                    if spec is None:
                        _log_framework_error(f"无法创建模块规范: {plugin_path}")
                        return None
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[plugin_name] = module
                    if spec.loader:
                        spec.loader.exec_module(module)
                    else:
                        _log_framework_error(f"模块加载器为空: {plugin_path}")
                        return None
                else:
                    parent_dir = os.path.dirname(plugin_path)
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    module = importlib.import_module(plugin_name)

                plugin_info = _PluginInfo(
                    name=plugin_name,
                    path=plugin_path,
                    module=module,
                    enabled=True,
                    loaded=True,
                    is_wheel=False,
                )

            if hasattr(module, "__version__"):
                plugin_info.version = module.__version__
            if hasattr(module, "__description__"):
                plugin_info.description = module.__description__
            if hasattr(module, "__author__"):
                plugin_info.author = module.__author__

            plugin_dependencies = []
            if hasattr(module, "__dependencies__"):
                plugin_dependencies = module.__dependencies__
                plugin_info.dependencies = plugin_dependencies

            if plugin_dependencies:
                missing_deps = self._check_dependencies(plugin_dependencies)
                if missing_deps:
                    _log_framework_warning(
                        f"插件 '{plugin_name}' 缺失依赖: {', '.join(missing_deps)}"
                    )

                    if hasattr(module, "install_dependencies"):
                        _log_framework_info(f"尝试使用插件自带的依赖补全方法")
                        try:
                            install_result = module.install_dependencies()
                            if install_result:
                                _log_framework_info(f"插件依赖补全成功")
                            else:
                                _log_framework_error(f"插件依赖补全失败")
                                return None
                        except Exception as e:
                            _log_framework_error(f"插件依赖补全方法执行失败: {e}")
                            return None
                    else:
                        _log_framework_info(f"尝试自动安装缺失的依赖")
                        if not self._install_dependencies(missing_deps):
                            _log_framework_error(f"自动安装依赖失败")
                            return None

            self._plugins[plugin_name] = plugin_info

            _log_framework_info(f"插件加载成功: {plugin_name} v{plugin_info.version}")

            if self._framework and hasattr(module, "register"):
                try:
                    module.register(self._framework)
                    _log_framework_info(f"插件 {plugin_name} 已自动注册到框架")
                except Exception as e:
                    _log_framework_error(f"插件 {plugin_name} 自动注册失败: {e}")

            return module

        except Exception as e:
            _log_framework_error(f"插件加载失败: {plugin_path}, 错误: {e}")
            return None

    def load_plugins_from_dir(self, plugin_dir: str) -> List[Any]:
        """从目录加载所有插件"""
        _log_framework_info(f"从目录加载插件: {plugin_dir}")

        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            _log_framework_warning(f"插件目录不存在: {plugin_dir}")
            return []

        modules = []

        for wheel_file in plugin_path.glob("*.whl"):
            module = self.load_plugin(str(wheel_file))
            if module:
                modules.append(module)

        return modules

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self._plugins:
            _log_framework_warning(f"插件未加载: {plugin_name}")
            return False

        plugin_info = self._plugins[plugin_name]

        if self._framework and hasattr(plugin_info.module, "unregister"):
            try:
                plugin_info.module.unregister(self._framework)
                _log_framework_info(f"插件 {plugin_name} 已自动从框架注销")
            except Exception as e:
                _log_framework_error(f"插件 {plugin_name} 自动注销失败: {e}")

        if plugin_name in sys.modules:
            del sys.modules[plugin_name]

        del self._plugins[plugin_name]

        _log_framework_info(f"插件卸载成功: {plugin_name}")

        return True

    def reload_plugin(self, plugin_name: str) -> Optional[Any]:
        """重新加载插件"""
        if plugin_name not in self._plugins:
            _log_framework_warning(f"插件未加载: {plugin_name}")
            return None

        plugin_info = self._plugins[plugin_name]
        plugin_path = plugin_info.path

        self.unload_plugin(plugin_name)

        return self.load_plugin(plugin_path, plugin_name)

    def get_plugin(self, plugin_name: str) -> Optional[_PluginInfo]:
        """获取插件信息"""
        return self._plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, _PluginInfo]:
        """获取所有插件信息"""
        return self._plugins.copy()

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        if plugin_name not in self._plugins:
            _log_framework_warning(f"插件不存在: {plugin_name}")
            return False

        self._plugins[plugin_name].enabled = True
        _log_framework_info(f"插件已启用: {plugin_name}")
        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        if plugin_name not in self._plugins:
            _log_framework_warning(f"插件不存在: {plugin_name}")
            return False

        self._plugins[plugin_name].enabled = False
        _log_framework_info(f"插件已禁用: {plugin_name}")
        return True

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        return [
            {
                "name": info.name,
                "path": info.path,
                "version": info.version,
                "description": info.description,
                "author": info.author,
                "enabled": info.enabled,
                "loaded": info.loaded,
            }
            for info in self._plugins.values()
        ]

    def _auto_load(self) -> List[Any]:
        """自动加载所有插件目录中的插件"""
        modules = []
        for plugin_dir in self._plugin_dirs:
            dir_modules = self.load_plugins_from_dir(plugin_dir)
            modules.extend(dir_modules)

        _log_framework_info(f"自动加载完成，共加载 {len(modules)} 个插件")
        return modules

    def _auto_unload_all(self) -> bool:
        """自动卸载所有插件"""
        plugin_names = list(self._plugins.keys())
        success = True

        for plugin_name in plugin_names:
            if not self.unload_plugin(plugin_name):
                success = False

        if success:
            _log_framework_info(f"自动卸载完成，共卸载 {len(plugin_names)} 个插件")
        else:
            _log_framework_warning(f"部分插件卸载失败")

        return success

    def _set_framework(self, framework: Any) -> None:
        """设置框架实例"""
        self._framework = framework
        _log_framework_info("已设置框架实例，插件将自动注册/注销")


# 全局插件管理器实例
_plugin_manager = None


def _get_plugin_manager(
    app_name: Optional[str] = None, framework: Optional[Any] = None
) -> _PluginManager:
    """获取插件管理器实例（内部实现）"""
    global _plugin_manager

    if _plugin_manager is None:
        _plugin_manager = _PluginManager(app_name, framework)
    elif app_name is not None and _plugin_manager._app_name != app_name:
        _plugin_manager = _PluginManager(app_name, framework)
    elif framework is not None and _plugin_manager._framework is None:
        _plugin_manager._set_framework(framework)

    return _plugin_manager


def _load_plugin(plugin_path: str, plugin_name: Optional[str] = None) -> Optional[Any]:
    """加载插件（便捷函数，内部实现）"""
    return _get_plugin_manager().load_plugin(plugin_path, plugin_name)


def _unload_plugin(plugin_name: str) -> bool:
    """卸载插件（便捷函数，内部实现）"""
    return _get_plugin_manager().unload_plugin(plugin_name)


def _reload_plugin(plugin_name: str) -> Optional[Any]:
    """重新加载插件（便捷函数，内部实现）"""
    return _get_plugin_manager().reload_plugin(plugin_name)


def _load_plugins_from_dir(plugin_dir: str) -> List[Any]:
    """从目录加载插件（便捷函数，内部实现）"""
    return _get_plugin_manager().load_plugins_from_dir(plugin_dir)


def _list_plugins() -> List[Dict[str, Any]]:
    """列出所有插件（便捷函数，内部实现）"""
    return _get_plugin_manager().list_plugins()
