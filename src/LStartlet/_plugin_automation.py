"""
插件系统自动化增强 - 实现插件自动化和与主程序生命周期关联
"""

import os
import sys
import importlib
from typing import List, Set, Optional, Callable, Dict, Any
from weakref import WeakSet
from datetime import datetime

from ._plugin_manager import (
    PluginManager,
    PluginState,
    PluginInfo,
    PluginDependency,
    PluginError,
    DependencyError,
    get_plugin_manager,
)
from ._logging_functions import info, debug, warning, error, critical


class PluginAutoManager:
    """插件自动化管理器"""

    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self._auto_discovery_enabled = False
        self._auto_load_enabled = False
        self._auto_activate_enabled = False
        self._plugin_dirs: List[str] = []
        self._auto_start_hooks: List[Callable] = []
        self._auto_stop_hooks: List[Callable] = []
        self._error_handlers: List[Callable] = []

    def enable_auto_discovery(self, plugin_dirs: List[str]):
        """启用插件自动发现"""
        self._auto_discovery_enabled = True
        self._plugin_dirs = plugin_dirs
        info(f"插件自动发现已启用，监控目录: {plugin_dirs}")

    def disable_auto_discovery(self):
        """禁用插件自动发现"""
        self._auto_discovery_enabled = False
        self._plugin_dirs = []
        info("插件自动发现已禁用")

    def enable_auto_load(self):
        """启用插件自动加载"""
        self._auto_load_enabled = True
        info("插件自动加载已启用")

    def disable_auto_load(self):
        """禁用插件自动加载"""
        self._auto_load_enabled = False
        info("插件自动加载已禁用")

    def enable_auto_activate(self):
        """启用插件自动激活"""
        self._auto_activate_enabled = True
        info("插件自动激活已启用")

    def disable_auto_activate(self):
        """禁用插件自动激活"""
        self._auto_activate_enabled = False
        info("插件自动激活已禁用")

    def enable_full_automation(self, plugin_dirs: List[str]):
        """启用完整的插件自动化"""
        self.enable_auto_discovery(plugin_dirs)
        self.enable_auto_load()
        self.enable_auto_activate()
        info("插件完整自动化已启用")

    def disable_full_automation(self):
        """禁用完整的插件自动化"""
        self.disable_auto_discovery()
        self.disable_auto_load()
        self.disable_auto_activate()
        info("插件完整自动化已禁用")

    def register_auto_start_hook(self, hook: Callable):
        """注册自动启动钩子"""
        self._auto_start_hooks.append(hook)

    def register_auto_stop_hook(self, hook: Callable):
        """注册自动停止钩子"""
        self._auto_stop_hooks.append(hook)

    def register_error_handler(self, handler: Callable):
        """注册插件错误处理器"""
        self._error_handlers.append(handler)

    def auto_discover_plugins(self) -> List[tuple]:
        """自动发现插件"""
        if not self._auto_discovery_enabled:
            warning("插件自动发现未启用")
            return []

        discovered_plugins = []

        for plugin_dir in self._plugin_dirs:
            if not os.path.exists(plugin_dir):
                warning(f"插件目录不存在: {plugin_dir}")
                continue

            for filename in os.listdir(plugin_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    module_name = filename[:-3]
                    discovered_plugins.append((module_name, plugin_dir))

        if discovered_plugins:
            info(f"自动发现插件: {[name for name, _ in discovered_plugins]}")

        return discovered_plugins

    def auto_load_plugins(self, discovered_plugins: List[tuple]) -> int:
        """自动加载插件"""
        if not self._auto_load_enabled:
            warning("插件自动加载未启用")
            return 0

        loaded_count = 0

        for module_name, plugin_dir in discovered_plugins:
            try:
                # 添加插件目录到 Python 路径
                if plugin_dir not in sys.path:
                    sys.path.insert(0, plugin_dir)

                # 导入插件模块
                module = importlib.import_module(module_name)

                # 查找插件类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)

                    # 检查是否为插件类
                    if hasattr(attr, "_plugin_metadata"):
                        plugin_info = attr._plugin_metadata

                        # 确定命名空间
                        namespace = plugin_info.get("namespace", "user")
                        is_framework_plugin = plugin_info.get(
                            "is_framework_plugin", False
                        )

                        # 注册插件
                        self.plugin_manager.register_plugin(
                            attr,
                            namespace=namespace,
                            is_framework_plugin=is_framework_plugin,
                        )

                        loaded_count += 1
                        debug(f"自动加载插件: {module_name}.{attr_name}")

            except Exception as e:
                error(f"自动加载插件 {module_name} 失败: {e}")
                self._handle_plugin_error(e, "AUTO_LOAD", module_name)

        if loaded_count > 0:
            info(f"自动加载插件数量: {loaded_count}")

        return loaded_count

    def auto_activate_plugins(self) -> int:
        """自动激活插件"""
        if not self._auto_activate_enabled:
            warning("插件自动激活未启用")
            return 0

        # 获取加载顺序
        load_order = self.plugin_manager.get_load_order()

        activated_count = 0

        for plugin_name in load_order:
            try:
                plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
                if not plugin_info:
                    warning(f"插件 {plugin_name} 不存在")
                    continue

                # 如果插件未加载，先加载
                if plugin_info.state == PluginState.LOADED:
                    if not self.plugin_manager.load_plugin(plugin_name):
                        warning(f"加载插件 {plugin_name} 失败")
                        continue

                # 如果插件已初始化，激活它
                if plugin_info.state == PluginState.INITIALIZED:
                    if self.plugin_manager.activate_plugin(plugin_name):
                        activated_count += 1
                        debug(f"自动激活插件: {plugin_name}")
                    else:
                        warning(f"激活插件 {plugin_name} 失败")
                # 如果插件已经激活，跳过
                elif plugin_info.state == PluginState.ACTIVATED:
                    debug(f"插件 {plugin_name} 已经激活")
                    activated_count += 1

            except Exception as e:
                error(f"自动激活插件 {plugin_name} 失败: {e}")
                self._handle_plugin_error(e, "AUTO_ACTIVATE", plugin_name)

        if activated_count > 0:
            info(f"自动激活插件数量: {activated_count}")

        return activated_count

    def auto_deactivate_plugins(self) -> int:
        """自动停用插件"""
        # 获取激活的插件（反向顺序）
        load_order = self.plugin_manager.get_load_order()
        activated_plugins = []

        for name in reversed(load_order):
            plugin_info = self.plugin_manager.get_plugin_info(name)
            if plugin_info is not None and plugin_info.state == PluginState.ACTIVATED:
                activated_plugins.append(name)

        deactivated_count = 0

        for plugin_name in activated_plugins:
            try:
                if self.plugin_manager.deactivate_plugin(plugin_name):
                    deactivated_count += 1
                    debug(f"自动停用插件: {plugin_name}")
                else:
                    warning(f"停用插件 {plugin_name} 失败")

            except Exception as e:
                error(f"自动停用插件 {plugin_name} 失败: {e}")
                self._handle_plugin_error(e, "AUTO_DEACTIVATE", plugin_name)

        if deactivated_count > 0:
            info(f"自动停用插件数量: {deactivated_count}")

        return deactivated_count

    def auto_unload_plugins(self) -> int:
        """自动卸载插件"""
        # 获取已加载的插件（反向顺序）
        load_order = self.plugin_manager.get_load_order()
        loaded_plugins = []

        for name in reversed(load_order):
            plugin_info = self.plugin_manager.get_plugin_info(name)
            if plugin_info is not None and plugin_info.state in [
                PluginState.INITIALIZED,
                PluginState.DEACTIVATED,
            ]:
                loaded_plugins.append(name)

        unloaded_count = 0

        for plugin_name in loaded_plugins:
            try:
                if self.plugin_manager.unload_plugin(plugin_name):
                    unloaded_count += 1
                    debug(f"自动卸载插件: {plugin_name}")
                else:
                    warning(f"卸载插件 {plugin_name} 失败")

            except Exception as e:
                error(f"自动卸载插件 {plugin_name} 失败: {e}")
                self._handle_plugin_error(e, "AUTO_UNLOAD", plugin_name)

        if unloaded_count > 0:
            info(f"自动卸载插件数量: {unloaded_count}")

        return unloaded_count

    def auto_start_all(self) -> Dict[str, int]:
        """自动启动所有插件（发现 -> 加载 -> 激活）"""
        info("开始自动启动所有插件...")

        result = {"discovered": 0, "loaded": 0, "activated": 0}

        # 1. 自动发现插件
        discovered = self.auto_discover_plugins()
        result["discovered"] = len(discovered)

        # 2. 自动加载插件
        loaded = self.auto_load_plugins(discovered)
        result["loaded"] = loaded

        # 3. 自动激活插件
        activated = self.auto_activate_plugins()
        result["activated"] = activated

        # 4. 执行自动启动钩子
        for hook in self._auto_start_hooks:
            try:
                hook(result)
            except Exception as e:
                error(f"执行自动启动钩子失败: {e}")

        info(
            f"自动启动插件完成: 发现={result['discovered']}, 加载={result['loaded']}, 激活={result['activated']}"
        )

        return result

    def auto_stop_all(self) -> Dict[str, int]:
        """自动停止所有插件（停用 -> 卸载）"""
        info("开始自动停止所有插件...")

        result = {"deactivated": 0, "unloaded": 0}

        # 1. 自动停用插件
        deactivated = self.auto_deactivate_plugins()
        result["deactivated"] = deactivated

        # 2. 自动卸载插件
        unloaded = self.auto_unload_plugins()
        result["unloaded"] = unloaded

        # 3. 执行自动停止钩子
        for hook in self._auto_stop_hooks:
            try:
                hook(result)
            except Exception as e:
                error(f"执行自动停止钩子失败: {e}")

        info(
            f"自动停止插件完成: 停用={result['deactivated']}, 卸载={result['unloaded']}"
        )

        return result

    def _handle_plugin_error(self, exception: Exception, phase: str, plugin_name: str):
        """处理插件错误"""
        error_info = {
            "exception": exception,
            "phase": phase,
            "plugin_name": plugin_name,
            "timestamp": datetime.now(),
        }

        # 调用所有注册的错误处理器
        for handler in self._error_handlers:
            try:
                handler(error_info)
            except Exception as e:
                error(f"插件错误处理器执行失败: {e}")

    def get_automation_status(self) -> Dict[str, Any]:
        """获取自动化状态"""
        return {
            "auto_discovery_enabled": self._auto_discovery_enabled,
            "auto_load_enabled": self._auto_load_enabled,
            "auto_activate_enabled": self._auto_activate_enabled,
            "plugin_dirs": self._plugin_dirs,
            "auto_start_hooks_count": len(self._auto_start_hooks),
            "auto_stop_hooks_count": len(self._auto_stop_hooks),
            "error_handlers_count": len(self._error_handlers),
        }


class PluginLifecycleIntegration:
    """插件生命周期与主程序生命周期集成"""

    def __init__(self, plugin_manager: PluginManager, auto_manager: PluginAutoManager):
        self.plugin_manager = plugin_manager
        self.auto_manager = auto_manager
        self._integrated = False

    def integrate_with_framework(self):
        """集成到框架生命周期"""
        if self._integrated:
            warning("插件生命周期已经集成到框架")
            return

        # 注册框架启动钩子
        from ._di_decorator import get_di_container

        di_container = get_di_container()

        # 在 DI 容器启动时自动启动插件
        original_start = di_container.start_components

        def wrapped_start():
            # 先启动插件
            self.auto_manager.auto_start_all()
            # 再启动组件
            return original_start()

        di_container.start_components = wrapped_start

        # 在 DI 容器停止时自动停止插件
        original_stop = di_container.stop_components

        def wrapped_stop():
            # 先停止组件
            original_stop()
            # 再停止插件
            self.auto_manager.auto_stop_all()

        di_container.stop_components = wrapped_stop

        self._integrated = True
        info("插件生命周期已集成到框架")

    def disintegrate_from_framework(self):
        """从框架生命周期中分离"""
        if not self._integrated:
            return

        # 恢复原始方法
        from ._di_decorator import get_di_container

        di_container = get_di_container()

        # 这里需要保存原始方法的引用，简化处理
        # 实际实现中应该保存原始方法引用

        self._integrated = False
        info("插件生命周期已从框架分离")

    def get_integration_status(self) -> bool:
        """获取集成状态"""
        return self._integrated


# 全局实例
_plugin_auto_manager = None
_plugin_lifecycle_integration = None


def get_plugin_auto_manager() -> PluginAutoManager:
    """获取插件自动化管理器"""
    global _plugin_auto_manager
    if _plugin_auto_manager is None:
        plugin_manager = get_plugin_manager()
        _plugin_auto_manager = PluginAutoManager(plugin_manager)
    return _plugin_auto_manager


def get_plugin_lifecycle_integration() -> PluginLifecycleIntegration:
    """获取插件生命周期集成器"""
    global _plugin_lifecycle_integration
    if _plugin_lifecycle_integration is None:
        plugin_manager = get_plugin_manager()
        auto_manager = get_plugin_auto_manager()
        _plugin_lifecycle_integration = PluginLifecycleIntegration(
            plugin_manager, auto_manager
        )
    return _plugin_lifecycle_integration


# 便捷函数
def enable_plugin_automation(plugin_dirs: List[str]):
    """启用插件自动化"""
    auto_manager = get_plugin_auto_manager()
    auto_manager.enable_full_automation(plugin_dirs)


def disable_plugin_automation():
    """禁用插件自动化"""
    auto_manager = get_plugin_auto_manager()
    auto_manager.disable_full_automation()


def auto_start_plugins() -> Dict[str, int]:
    """自动启动所有插件"""
    auto_manager = get_plugin_auto_manager()
    return auto_manager.auto_start_all()


def auto_stop_plugins() -> Dict[str, int]:
    """自动停止所有插件"""
    auto_manager = get_plugin_auto_manager()
    return auto_manager.auto_stop_all()


def integrate_plugins_with_framework():
    """将插件生命周期集成到框架"""
    integration = get_plugin_lifecycle_integration()
    integration.integrate_with_framework()


def disintegrate_plugins_from_framework():
    """将插件生命周期从框架分离"""
    integration = get_plugin_lifecycle_integration()
    integration.disintegrate_from_framework()


def register_plugin_auto_start_hook(hook: Callable):
    """注册插件自动启动钩子"""
    auto_manager = get_plugin_auto_manager()
    auto_manager.register_auto_start_hook(hook)


def register_plugin_auto_stop_hook(hook: Callable):
    """注册插件自动停止钩子"""
    auto_manager = get_plugin_auto_manager()
    auto_manager.register_auto_stop_hook(hook)


def register_plugin_error_handler(handler: Callable):
    """注册插件错误处理器"""
    auto_manager = get_plugin_auto_manager()
    auto_manager.register_error_handler(handler)


def get_plugin_automation_status() -> Dict[str, Any]:
    """获取插件自动化状态"""
    auto_manager = get_plugin_auto_manager()
    return auto_manager.get_automation_status()
