"""
插件系统增强实现
"""

import os
import sys
import importlib
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Any, Optional, List, Set, Type, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from weakref import WeakSet

if TYPE_CHECKING:
    from ._plugin_base import PluginBase
else:
    # 在运行时导入 PluginBase 用于 isinstance/issubclass 检查
    from ._plugin_base import PluginBase


class PluginState(Enum):
    """插件状态"""

    UNLOADED = "unloaded"  # 未加载
    LOADED = "loaded"  # 已加载
    INITIALIZED = "initialized"  # 已初始化
    ACTIVATED = "activated"  # 已激活
    DEACTIVATED = "deactivated"  # 已停用
    ERROR = "error"  # 错误状态


@dataclass
class PluginDependency:
    """插件依赖"""

    plugin_name: str
    namespace: Optional[str] = None
    min_version: Optional[str] = None
    max_version: Optional[str] = None

    def is_satisfied(self, plugin_info: "PluginInfo") -> bool:
        """检查依赖是否满足"""
        if plugin_info.name != self.plugin_name:
            return False

        if self.namespace and plugin_info.namespace != self.namespace:
            return False

        if self.min_version and plugin_info.version < self.min_version:
            return False

        if self.max_version and plugin_info.version > self.max_version:
            return False

        return True


@dataclass
class PluginInfo:
    """插件信息"""

    name: str
    plugin_class: Type["PluginBase"]
    namespace: str
    version: str
    description: str
    author: str
    dependencies: List[PluginDependency]
    state: PluginState = PluginState.UNLOADED
    instance: Optional["PluginBase"] = None
    is_framework_plugin: bool = False
    load_time: Optional[datetime] = None
    activate_time: Optional[datetime] = None
    error_message: Optional[str] = None

    def reload_class(self):
        """重新加载插件类"""
        module_name = self.plugin_class.__module__
        importlib.reload(importlib.import_module(module_name))

        # 重新获取类
        module = sys.modules[module_name]
        self.plugin_class = getattr(module, self.plugin_class.__name__)


class PluginNamespace:
    """插件命名空间"""

    def __init__(self, name: str, parent: Optional["PluginNamespace"] = None):
        self.name = name
        self.parent = parent
        self.children: Dict[str, "PluginNamespace"] = {}
        self.plugins: Dict[str, PluginInfo] = {}

    def add_plugin(self, plugin_info: PluginInfo):
        """添加插件到命名空间"""
        self.plugins[plugin_info.name] = plugin_info

    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """获取插件"""
        return self.plugins.get(name)

    def get_all_plugins(self) -> List[PluginInfo]:
        """获取所有插件"""
        return list(self.plugins.values())

    def add_child(self, namespace: "PluginNamespace"):
        """添加子命名空间"""
        self.children[namespace.name] = namespace

    def get_child(self, name: str) -> Optional["PluginNamespace"]:
        """获取子命名空间"""
        return self.children.get(name)

    def get_all_children(self) -> List["PluginNamespace"]:
        """获取所有子命名空间"""
        return list(self.children.values())


class DependencyResolver:
    """依赖解析器"""

    def __init__(self, plugin_manager: "PluginManager"):
        self.plugin_manager = plugin_manager

    def resolve_dependencies(self, plugin_name: str) -> List[PluginInfo]:
        """解析插件依赖"""
        dependencies = []
        visited = set()

        def _resolve(name: str):
            if name in visited:
                return

            visited.add(name)
            plugin_info = self.plugin_manager.get_plugin_info(name)

            if not plugin_info:
                raise DependencyError(f"插件 {name} 不存在")

            dependencies.append(plugin_info)

            for dep in plugin_info.dependencies:
                _resolve(dep.plugin_name)

        _resolve(plugin_name)
        return dependencies

    def check_circular_dependencies(self, plugin_name: str) -> bool:
        """检查循环依赖"""
        visited = set()
        recursion_stack = set()

        def _check(name: str) -> bool:
            if name in recursion_stack:
                return True

            if name in visited:
                return False

            visited.add(name)
            recursion_stack.add(name)

            plugin_info = self.plugin_manager.get_plugin_info(name)

            if not plugin_info:
                recursion_stack.remove(name)
                return False

            for dep in plugin_info.dependencies:
                if _check(dep.plugin_name):
                    return True

            recursion_stack.remove(name)
            return False

        return _check(plugin_name)

    def get_load_order(self, plugin_names: List[str]) -> List[str]:
        """获取插件加载顺序（拓扑排序）"""
        # 构建依赖图
        from typing import Dict, List

        graph: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {}

        for plugin_name in plugin_names:
            graph[plugin_name] = []
            in_degree[plugin_name] = 0

        for plugin_name in plugin_names:
            plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
            if plugin_info:
                for dep in plugin_info.dependencies:
                    if dep.plugin_name in graph:
                        graph[dep.plugin_name].append(plugin_name)
                        in_degree[plugin_name] += 1

        # 拓扑排序
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result: List[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(plugin_names):
            raise DependencyError("存在循环依赖")

        return result


class PluginLifecycleManager:
    """插件生命周期管理器"""

    def __init__(self, plugin_manager: "PluginManager"):
        self.plugin_manager = plugin_manager
        self._state_transitions: Dict[str, List[PluginState]] = {}

    def transition_state(
        self, plugin_name: str, from_state: PluginState, to_state: PluginState
    ) -> bool:
        """状态转换"""
        plugin_info = self.plugin_manager.get_plugin_info(plugin_name)

        if not plugin_info:
            return False

        if plugin_info.state != from_state:
            return False

        # 记录状态转换
        if plugin_name not in self._state_transitions:
            self._state_transitions[plugin_name] = []

        self._state_transitions[plugin_name].append(to_state)
        plugin_info.state = to_state

        return True

    def get_state_history(self, plugin_name: str) -> List[PluginState]:
        """获取状态历史"""
        return self._state_transitions.get(plugin_name, [])

    def can_transition(self, from_state: PluginState, to_state: PluginState) -> bool:
        """检查状态转换是否允许"""
        allowed_transitions = {
            PluginState.UNLOADED: [PluginState.LOADED],
            PluginState.LOADED: [PluginState.INITIALIZED, PluginState.ERROR],
            PluginState.INITIALIZED: [PluginState.ACTIVATED, PluginState.ERROR],
            PluginState.ACTIVATED: [PluginState.DEACTIVATED, PluginState.ERROR],
            PluginState.DEACTIVATED: [PluginState.INITIALIZED, PluginState.ERROR],
            PluginState.ERROR: [PluginState.LOADED, PluginState.UNLOADED],
        }

        return to_state in allowed_transitions.get(from_state, [])


class PluginManager:
    """插件管理器"""

    # 实例变量类型注解
    root_namespace: "PluginNamespace"
    namespaces: Dict[str, "PluginNamespace"]
    plugins: Dict[str, PluginInfo]
    lifecycle_manager: PluginLifecycleManager
    dependency_resolver: DependencyResolver
    framework_plugins: Set[str]
    user_plugins: Set[str]
    _all_instances: WeakSet[Any]

    def __init__(self):
        # 命名空间管理
        self.root_namespace = PluginNamespace("root")
        self.namespaces: Dict[str, PluginNamespace] = {
            "root": self.root_namespace,
            "framework": PluginNamespace("framework", self.root_namespace),
            "user": PluginNamespace("user", self.root_namespace),
            "external": PluginNamespace("external", self.root_namespace),
        }

        # 添加子命名空间
        self.root_namespace.add_child(self.namespaces["framework"])
        self.root_namespace.add_child(self.namespaces["user"])
        self.root_namespace.add_child(self.namespaces["external"])

        # 插件信息
        self.plugins: Dict[str, PluginInfo] = {}

        # 生命周期管理
        self.lifecycle_manager = PluginLifecycleManager(self)

        # 依赖解析器
        self.dependency_resolver = DependencyResolver(self)

        # 插件类型
        self.framework_plugins: Set[str] = set()
        self.user_plugins: Set[str] = set()

        # 所有实例跟踪
        self._all_instances: WeakSet[Any] = WeakSet()

    def register_plugin(
        self,
        plugin_class: Type["PluginBase"],
        namespace: str = "user",
        is_framework_plugin: bool = False,
    ) -> bool:
        """注册插件"""
        # 获取插件元数据
        plugin_name = getattr(plugin_class, "name", plugin_class.__name__)

        # 确保 plugin_name 是有效的字符串
        if not plugin_name or not isinstance(plugin_name, str):
            plugin_name = plugin_class.__name__

        version = getattr(plugin_class, "version", "1.0.0")
        description = getattr(plugin_class, "description", "")
        author = getattr(plugin_class, "author", "")

        # 解析依赖
        dependencies = []
        for dep in getattr(plugin_class, "dependencies", []):
            if isinstance(dep, PluginDependency):
                # 已经是 PluginDependency 对象，直接使用
                dependencies.append(dep)
            elif isinstance(dep, str):
                dependencies.append(PluginDependency(dep))
            elif isinstance(dep, dict):
                dep_plugin_name = dep.get("plugin_name") or dep.get("name")
                if dep_plugin_name:
                    dependencies.append(
                        PluginDependency(
                            plugin_name=dep_plugin_name,
                            namespace=dep.get("namespace"),
                            min_version=dep.get("min_version"),
                            max_version=dep.get("max_version"),
                        )
                    )

        # 创建插件信息
        plugin_info = PluginInfo(
            name=plugin_name,
            plugin_class=plugin_class,
            namespace=namespace,
            version=version,
            description=description,
            author=author,
            dependencies=dependencies,
            is_framework_plugin=is_framework_plugin,
        )

        # 先添加到插件字典中（用于循环依赖检测）
        self.plugins[plugin_name] = plugin_info

        # 检查循环依赖
        if self.dependency_resolver.check_circular_dependencies(plugin_name):
            # 如果存在循环依赖，从字典中移除并抛出异常
            del self.plugins[plugin_name]
            raise PluginError(f"插件 {plugin_name} 存在循环依赖")

        # 添加到命名空间
        ns = self.namespaces.get(namespace, self.root_namespace)
        ns.add_plugin(plugin_info)

        # 分类插件
        if is_framework_plugin:
            self.framework_plugins.add(plugin_name)
        else:
            self.user_plugins.add(plugin_name)

        # 初始状态
        plugin_info.state = PluginState.LOADED
        plugin_info.load_time = datetime.now()

        return True

    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        plugin_info = self.plugins.get(plugin_name)

        if not plugin_info:
            return False

        # 解析依赖
        dependencies = self.dependency_resolver.resolve_dependencies(plugin_name)

        # 加载依赖
        for dep in dependencies:
            if dep.state == PluginState.UNLOADED:
                self.load_plugin(dep.name)

        # 初始化插件
        if plugin_info.state == PluginState.LOADED:
            try:
                instance = plugin_info.plugin_class()
                plugin_info.instance = instance
                self._all_instances.add(instance)

                # 调用 initialize 方法
                if not instance.initialize():
                    plugin_info.error_message = "initialize 方法返回 False"
                    self.lifecycle_manager.transition_state(
                        plugin_name, PluginState.LOADED, PluginState.ERROR
                    )
                    return False

                self.lifecycle_manager.transition_state(
                    plugin_name, PluginState.LOADED, PluginState.INITIALIZED
                )
            except Exception as e:
                plugin_info.error_message = str(e)
                self.lifecycle_manager.transition_state(
                    plugin_name, PluginState.LOADED, PluginState.ERROR
                )
                return False

        return True

    def activate_plugin(self, plugin_name: str) -> bool:
        """激活插件"""
        plugin_info = self.plugins.get(plugin_name)

        if not plugin_info:
            return False

        # 确保插件已加载
        if plugin_info.state == PluginState.LOADED:
            if not self.load_plugin(plugin_name):
                return False

        if plugin_info.state != PluginState.INITIALIZED:
            return False

        # 激活插件
        try:
            if plugin_info.instance and plugin_info.instance.activate():
                self.lifecycle_manager.transition_state(
                    plugin_name, PluginState.INITIALIZED, PluginState.ACTIVATED
                )
                plugin_info.activate_time = datetime.now()
                return True
        except Exception as e:
            plugin_info.error_message = str(e)
            self.lifecycle_manager.transition_state(
                plugin_name, PluginState.INITIALIZED, PluginState.ERROR
            )

        return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """停用插件"""
        plugin_info = self.plugins.get(plugin_name)

        if not plugin_info or plugin_info.state != PluginState.ACTIVATED:
            return False

        # 停用插件
        try:
            if plugin_info.instance:
                plugin_info.instance.deactivate()
            self.lifecycle_manager.transition_state(
                plugin_name, PluginState.ACTIVATED, PluginState.DEACTIVATED
            )
            return True
        except Exception as e:
            plugin_info.error_message = str(e)
            self.lifecycle_manager.transition_state(
                plugin_name, PluginState.ACTIVATED, PluginState.ERROR
            )
            return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """重载插件"""
        plugin_info = self.plugins.get(plugin_name)

        if not plugin_info:
            return False

        # 停用插件
        if plugin_info.state == PluginState.ACTIVATED:
            self.deactivate_plugin(plugin_name)

        try:
            # 重新加载插件类
            plugin_info.reload_class()

            # 重新初始化插件
            instance = plugin_info.plugin_class()
            plugin_info.instance = instance
            self._all_instances.add(instance)

            # 调用 initialize 方法
            if not instance.initialize():
                plugin_info.error_message = "initialize 方法返回 False"
                self.lifecycle_manager.transition_state(
                    plugin_name, PluginState.DEACTIVATED, PluginState.ERROR
                )
                return False

            # 重新激活插件
            self.lifecycle_manager.transition_state(
                plugin_name, PluginState.DEACTIVATED, PluginState.INITIALIZED
            )

            if plugin_info.instance and plugin_info.instance.activate():
                self.lifecycle_manager.transition_state(
                    plugin_name, PluginState.INITIALIZED, PluginState.ACTIVATED
                )
                plugin_info.activate_time = datetime.now()
                return True
        except Exception as e:
            plugin_info.error_message = str(e)
            self.lifecycle_manager.transition_state(
                plugin_name, PluginState.DEACTIVATED, PluginState.ERROR
            )

        return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        plugin_info = self.plugins.get(plugin_name)

        if not plugin_info:
            return False

        # 停用插件
        if plugin_info.state == PluginState.ACTIVATED:
            self.deactivate_plugin(plugin_name)

        # 清理插件
        if plugin_info.instance:
            try:
                plugin_info.instance.cleanup()
            except Exception as e:
                plugin_info.error_message = str(e)

        plugin_info.instance = None
        self.lifecycle_manager.transition_state(
            plugin_name, PluginState.DEACTIVATED, PluginState.UNLOADED
        )

        return True

    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self.plugins.get(name)

    def get_plugins_by_namespace(self, namespace: str) -> List[PluginInfo]:
        """按命名空间获取插件"""
        ns = self.namespaces.get(namespace)
        if not ns:
            return []
        return ns.get_all_plugins()

    def get_framework_plugins(self) -> List[PluginInfo]:
        """获取框架插件"""
        return [self.plugins[name] for name in self.framework_plugins]

    def get_user_plugins(self) -> List[PluginInfo]:
        """获取用户插件"""
        return [self.plugins[name] for name in self.user_plugins]

    def get_all_plugins(self) -> List[PluginInfo]:
        """获取所有插件"""
        return list(self.plugins.values())

    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """分析插件依赖关系"""
        dependency_graph = {}

        for plugin_name, plugin_info in self.plugins.items():
            dependencies = [dep.plugin_name for dep in plugin_info.dependencies]
            dependency_graph[plugin_name] = dependencies

        return dependency_graph

    def get_load_order(self) -> List[str]:
        """获取所有插件的加载顺序"""
        plugin_names = list(self.plugins.keys())
        return self.dependency_resolver.get_load_order(plugin_names)

    def get_all_instances(self) -> List[Any]:
        """获取所有插件实例"""
        return list(self._all_instances)

    def get_instance_count(self) -> int:
        """获取插件实例总数"""
        return len(self._all_instances)


class PluginDiscovery:
    """插件发现器"""

    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager

    def discover_plugins(self, plugin_dirs: List[str]) -> List[str]:
        """发现插件"""
        discovered_plugins = []

        for plugin_dir in plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue

            for filename in os.listdir(plugin_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    module_name = filename[:-3]
                    discovered_plugins.append(module_name)

        return discovered_plugins

    def load_plugins_from_dirs(
        self,
        plugin_dirs: List[str],
        namespace: str = "user",
        is_framework_plugin: bool = False,
    ) -> int:
        """从目录加载插件"""
        discovered = self.discover_plugins(plugin_dirs)
        loaded_count = 0

        for module_name in discovered:
            try:
                # 导入插件模块
                module = importlib.import_module(module_name)

                # 查找插件类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)

                    if (
                        isinstance(attr, type)
                        and issubclass(attr, PluginBase)
                        and attr != PluginBase
                    ):

                        # 注册插件
                        self.plugin_manager.register_plugin(
                            attr,
                            namespace=namespace,
                            is_framework_plugin=is_framework_plugin,
                        )
                        loaded_count += 1

            except Exception as e:
                print(f"加载插件 {module_name} 失败: {e}")

        return loaded_count


class PluginError(Exception):
    """插件错误"""

    pass


class DependencyError(Exception):
    """依赖错误"""

    pass


# 全局插件管理器实例
_plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """
    获取全局插件管理器实例

    返回框架的全局插件管理器，用于管理所有插件的生命周期。
    通常情况下，用户不需要直接调用此函数，而是使用便捷函数。

    Returns:
        PluginManager: 全局插件管理器实例

    Example:
        from LStartlet import get_plugin_manager

        manager = get_plugin_manager()
        plugins = manager.get_all_plugins()
    """
    return _plugin_manager


def register_plugin(
    plugin_class: Type["PluginBase"],
    namespace: str = "user",
    is_framework_plugin: bool = False,
) -> bool:
    """
    注册插件到插件管理器

    将插件类注册到插件管理器中，使其可以被加载和激活。
    注册后插件处于已注册状态，需要调用 load_plugin 和 activate_plugin 才能使用。

    Args:
        plugin_class: 插件类，必须继承自 PluginBase
        namespace: 命名空间，用于区分不同来源的插件，默认为"user"
                  常用值："user"（用户插件）、"framework"（框架插件）
        is_framework_plugin: 是否为框架插件，默认为 False
                              框架插件具有更高的优先级

    Returns:
        bool: 注册成功返回 True，失败返回 False

    Raises:
        PluginError: 插件注册失败时抛出

    Example:
        from LStartlet import Plugin, register_plugin

        @Plugin("my_plugin")
        class MyPlugin(PluginBase):
            def __init__(self):
                super().__init__("my_plugin")

        # 注册插件
        success = register_plugin(MyPlugin, namespace="user")
        if success:
            print("插件注册成功")
    """
    return _plugin_manager.register_plugin(
        plugin_class, namespace=namespace, is_framework_plugin=is_framework_plugin
    )


def load_plugin(plugin_name: str) -> bool:
    """
    加载插件

    加载已注册的插件，解析其依赖关系，但不会激活插件。
    加载成功后插件处于已加载状态，需要调用 activate_plugin 才能使用。

    Args:
        plugin_name: 插件名称，必须与 @Plugin 装饰器中指定的名称一致

    Returns:
        bool: 加载成功返回 True，失败返回 False

    Raises:
        PluginError: 插件未注册或加载失败时抛出
        DependencyError: 插件依赖解析失败时抛出

    Example:
        from LStartlet import load_plugin, activate_plugin

        # 加载插件
        if load_plugin("my_plugin"):
            print("插件加载成功")
            # 激活插件
            activate_plugin("my_plugin")
    """
    return _plugin_manager.load_plugin(plugin_name)


def activate_plugin(plugin_name: str) -> bool:
    """
    激活插件

    激活已加载的插件，使其开始工作。
    激活过程包括：检查依赖、创建实例、调用生命周期方法。

    Args:
        plugin_name: 插件名称，必须与 @Plugin 装饰器中指定的名称一致

    Returns:
        bool: 激活成功返回 True，失败返回 False

    Raises:
        PluginError: 插件未加载或激活失败时抛出
        DependencyError: 插件依赖未满足时抛出

    Example:
        from LStartlet import activate_plugin

        # 激活插件
        if activate_plugin("my_plugin"):
            print("插件激活成功")
    """
    return _plugin_manager.activate_plugin(plugin_name)


def deactivate_plugin(plugin_name: str) -> bool:
    """
    停用插件

    停用已激活的插件，使其停止工作。
    停用过程包括：调用销毁方法、释放资源、更新状态。
    停用后插件仍处于已加载状态，可以重新激活。

    Args:
        plugin_name: 插件名称，必须与 @Plugin 装饰器中指定的名称一致

    Returns:
        bool: 停用成功返回 True，失败返回 False

    Raises:
        PluginError: 插件未激活或停用失败时抛出

    Example:
        from LStartlet import deactivate_plugin, activate_plugin

        # 停用插件
        if deactivate_plugin("my_plugin"):
            print("插件已停用")
            # 重新激活
            activate_plugin("my_plugin")
    """
    return _plugin_manager.deactivate_plugin(plugin_name)


def reload_plugin(plugin_name: str) -> bool:
    """
    重载插件

    重新加载并激活插件，适用于插件代码更新后的热重载场景。
    重载过程包括：停用插件、卸载插件、重新加载、重新激活。

    Args:
        plugin_name: 插件名称，必须与 @Plugin 装饰器中指定的名称一致

    Returns:
        bool: 重载成功返回 True，失败返回 False

    Raises:
        PluginError: 插件重载失败时抛出

    Example:
        from LStartlet import reload_plugin

        # 重载插件（用于开发调试）
        if reload_plugin("my_plugin"):
            print("插件重载成功")
    """
    return _plugin_manager.reload_plugin(plugin_name)


def unload_plugin(plugin_name: str) -> bool:
    """
    卸载插件

    完全卸载插件，释放所有资源。
    卸载过程包括：停用插件、清理依赖、释放资源。
    卸载后插件需要重新注册才能使用。

    Args:
        plugin_name: 插件名称，必须与 @Plugin 装饰器中指定的名称一致

    Returns:
        bool: 卸载成功返回 True，失败返回 False

    Raises:
        PluginError: 插件卸载失败时抛出

    Example:
        from LStartlet import unload_plugin

        # 卸载插件
        if unload_plugin("my_plugin"):
            print("插件已卸载")
    """
    return _plugin_manager.unload_plugin(plugin_name)


def get_plugin_info(name: str) -> Optional[PluginInfo]:
    """
    获取插件信息

    获取指定插件的详细信息，包括状态、依赖、实例等。

    Args:
        name: 插件名称，必须与 @Plugin 装饰器中指定的名称一致

    Returns:
        Optional[PluginInfo]: 插件信息对象，如果插件不存在则返回 None

    Example:
        from LStartlet import get_plugin_info

        # 获取插件信息
        info = get_plugin_info("my_plugin")
        if info:
            print(f"插件状态: {info.state}")
            print(f"插件版本: {info.version}")
            print(f"插件依赖: {info.dependencies}")
    """
    return _plugin_manager.get_plugin_info(name)


def get_plugins_by_namespace(namespace: str) -> List[PluginInfo]:
    """
    按命名空间获取插件列表

    获取指定命名空间下的所有插件信息。
    常用命名空间："user"（用户插件）、"framework"（框架插件）

    Args:
        namespace: 命名空间名称

    Returns:
        List[PluginInfo]: 插件信息列表

    Example:
        from LStartlet import get_plugins_by_namespace

        # 获取所有用户插件
        user_plugins = get_plugins_by_namespace("user")
        for plugin_info in user_plugins:
            print(f"插件: {plugin_info.name}, 状态: {plugin_info.state}")

        # 获取所有框架插件
        framework_plugins = get_plugins_by_namespace("framework")
        for plugin_info in framework_plugins:
            print(f"框架插件: {plugin_info.name}")
    """
    return _plugin_manager.get_plugins_by_namespace(namespace)


def get_framework_plugins() -> List[PluginInfo]:
    """
    获取所有框架插件

    获取所有标记为框架插件的插件信息列表。
    框架插件具有更高的优先级，通常在用户插件之前加载。

    Returns:
        List[PluginInfo]: 框架插件信息列表

    Example:
        from LStartlet import get_framework_plugins

        # 获取所有框架插件
        framework_plugins = get_framework_plugins()
        print(f"框架插件数量: {len(framework_plugins)}")
        for plugin_info in framework_plugins:
            print(f"  - {plugin_info.name}: {plugin_info.state}")
    """
    return _plugin_manager.get_framework_plugins()


def get_user_plugins() -> List[PluginInfo]:
    """
    获取所有用户插件

    获取所有标记为用户插件的插件信息列表。
    用户插件通常由用户自己开发和管理。

    Returns:
        List[PluginInfo]: 用户插件信息列表

    Example:
        from LStartlet import get_user_plugins

        # 获取所有用户插件
        user_plugins = get_user_plugins()
        print(f"用户插件数量: {len(user_plugins)}")
        for plugin_info in user_plugins:
            print(f"  - {plugin_info.name}: {plugin_info.state}")
    """
    return _plugin_manager.get_user_plugins()


def get_all_plugins() -> List[PluginInfo]:
    """
    获取所有插件

    获取所有已注册的插件信息列表，包括框架插件和用户插件。

    Returns:
        List[PluginInfo]: 所有插件信息列表

    Example:
        from LStartlet import get_all_plugins

        # 获取所有插件
        all_plugins = get_all_plugins()
        print(f"总插件数量: {len(all_plugins)}")
        for plugin_info in all_plugins:
            print(f"  - {plugin_info.name}: {plugin_info.state}")
    """
    return _plugin_manager.get_all_plugins()


def analyze_dependencies() -> Dict[str, List[str]]:
    """
    分析插件依赖关系

    分析所有插件的依赖关系，返回每个插件的依赖列表。
    可以用于检查依赖冲突和循环依赖。

    Returns:
        Dict[str, List[str]]: 插件名称到依赖列表的映射

    Example:
        from LStartlet import analyze_dependencies

        # 分析依赖关系
        dependencies = analyze_dependencies()
        for plugin_name, deps in dependencies.items():
            print(f"{plugin_name} 依赖于: {', '.join(deps) if deps else '无'}")
    """
    return _plugin_manager.analyze_dependencies()


def get_load_order() -> List[str]:
    """获取插件加载顺序"""
    return _plugin_manager.get_load_order()
