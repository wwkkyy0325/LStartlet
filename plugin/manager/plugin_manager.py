"""
插件管理器
负责插件的加载、卸载、生命周期管理和依赖解析
"""

import os
from typing import Dict, List, Optional, Type, Tuple, Set
from threading import Lock

from plugin.base.plugin_base import PluginBase
from plugin.base.plugin_interface import IPluginManager, IPlugin
from plugin.manager.plugin_loader import PluginLoader
from plugin.manager.dependency_manager import PluginDependencyManager
from plugin.exceptions.plugin_exceptions import PluginLoadError
from plugin.events.plugin_events import PluginLoadedEvent, PluginUnloadedEvent
from plugin.metadata import (
    PluginMetadata,
    PluginCompatibilityChecker,
    PluginAvailabilityChecker,
)
from core.di import ServiceContainer
from core.event.event_bus import EventBus
from core.logger import info, error, warning
from core.decorators import with_error_handling, with_logging, monitor_metrics


class PluginManager(IPluginManager):
    """插件管理器 - 实现插件的完整生命周期管理"""

    def __init__(
        self,
        container: ServiceContainer,
        event_bus: EventBus,
        app_version: str = "1.0.0",
    ):
        """
        初始化插件管理器

        Args:
            container: 依赖注入容器
            event_bus: 事件总线
            app_version: 当前应用程序版本
        """
        self._container = container
        self._event_bus = event_bus
        self._app_version = app_version
        self._plugins: Dict[str, PluginBase] = {}
        self._plugin_metadata: Dict[str, PluginMetadata] = {}
        self._plugin_classes: Dict[str, Type[PluginBase]] = {}
        self._loader = PluginLoader()
        self._dependency_manager = PluginDependencyManager()
        self._availability_checker = PluginAvailabilityChecker(self._dependency_manager)
        self._compatibility_checker = PluginCompatibilityChecker(app_version)
        self._lock = Lock()
        self._is_initialized = False

    @with_error_handling(error_code="PLUGIN_LOAD_ERROR", default_return=None)
    @with_logging(level="info", measure_time=True)
    @monitor_metrics("plugin_load_plugins", include_labels=True)
    def load_plugins(self, plugin_paths: List[str]) -> None:
        """
        加载插件

        Args:
            plugin_paths: 插件路径列表（可以是文件或目录）
        """
        with self._lock:
            for path in plugin_paths:
                if os.path.isfile(path) and path.endswith(".whl"):
                    self._load_plugin_from_wheel(path)
                elif os.path.isdir(path):
                    self._load_plugins_from_directory(path)
                else:
                    warning(f"Plugin path does not exist or is invalid: {path}")

    def _load_plugin_from_wheel(self, plugin_wheel: str) -> None:
        """Load single plugin from wheel file"""
        try:
            result = self._loader.load_plugin_from_wheel(plugin_wheel)
            if result is not None:
                metadata, plugin_class = result
                self._register_plugin(metadata, plugin_class)

        except PluginLoadError as e:
            error(f"Failed to load plugin wheel: {plugin_wheel}, error: {e}")
        except Exception as e:
            error(f"Unexpected error loading plugin wheel: {plugin_wheel}, error: {e}")

    def _topological_sort_plugins(
        self, plugins: Dict[str, PluginMetadata]
    ) -> List[str]:
        """
        对插件进行拓扑排序，确保依赖的插件先加载

        Args:
            plugins: 插件元数据字典

        Returns:
            按依赖顺序排列的插件命名空间列表

        Raises:
            PluginLoadError: 如果存在循环依赖
        """
        # 构建依赖图
        graph: Dict[str, Set[str]] = {}
        all_plugins = set(plugins.keys())

        for namespace, metadata in plugins.items():
            graph[namespace] = set()
            for dep in metadata.plugin_dependencies:
                if dep in all_plugins:
                    graph[namespace].add(dep)
                else:
                    warning(
                        f"Plugin {namespace} depends on {dep}, but {dep} is not available"
                    )

        # 拓扑排序（Kahn算法）
        in_degree: Dict[str, int] = {node: 0 for node in all_plugins}
        for node in all_plugins:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1

        # 找到入度为0的节点
        queue: List[str] = [node for node, degree in in_degree.items() if degree == 0]
        result: List[str] = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # 移除当前节点的所有出边
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(all_plugins):
            # 存在循环依赖
            cycle_nodes = [node for node, degree in in_degree.items() if degree > 0]
            raise PluginLoadError(
                "dependency",
                f"Circular dependency detected among plugins: {', '.join(cycle_nodes)}",
            )

        return result

    def _register_plugins_with_dependencies(
        self, plugins: Dict[str, Tuple[PluginMetadata, Type[PluginBase]]]
    ) -> None:
        """注册插件并处理依赖关系"""
        # 先收集所有元数据用于依赖解析
        metadata_dict: Dict[str, PluginMetadata] = {}
        class_dict: Dict[str, Type[PluginBase]] = {}

        for namespace, (metadata, plugin_class) in plugins.items():
            # 检查版本兼容性
            if not self._compatibility_checker.is_compatible(metadata):
                warning(
                    f"Plugin {namespace} is not compatible with current app version {self._app_version}"
                )
                continue

            # 检查插件可用性（依赖完整性）
            availability = self._availability_checker.check_availability(metadata)
            if not availability["available"]:
                warning(
                    f"Plugin {namespace} is not available: {', '.join(availability['reasons'])}"
                )
                continue

            metadata_dict[namespace] = metadata
            class_dict[namespace] = plugin_class

        if not metadata_dict:
            return

        # 进行拓扑排序
        try:
            sorted_namespaces = self._topological_sort_plugins(metadata_dict)
        except PluginLoadError as e:
            error(f"Failed to sort plugins by dependency: {e}")
            return

        # 按依赖顺序注册插件
        for namespace in sorted_namespaces:
            if namespace in self._plugin_classes:
                warning(f"Plugin {namespace} already loaded, skipping duplicate load")
                continue

            metadata = metadata_dict[namespace]
            plugin_class = class_dict[namespace]

            self._plugin_metadata[namespace] = metadata
            self._plugin_classes[namespace] = plugin_class
            info(
                f"Successfully loaded plugin: {namespace} ({metadata.name} v{metadata.version})"
            )

            # 发布插件加载事件
            self._event_bus.publish(
                PluginLoadedEvent(
                    plugin_id=namespace,
                    plugin_name=metadata.name,
                    version=metadata.version,
                )
            )

    def _load_plugins_from_directory(self, plugin_dir: str) -> None:
        """Load all plugins from directory"""
        try:
            plugins = self._loader.load_plugin_from_directory(plugin_dir)
            self._register_plugins_with_dependencies(plugins)

        except Exception as e:
            error(f"Failed to load plugins from directory: {plugin_dir}, error: {e}")

    def _register_plugin(
        self, metadata: PluginMetadata, plugin_class: Type[PluginBase]
    ) -> None:
        """注册插件到管理器"""
        namespace = metadata.namespace

        # 检查命名空间冲突
        if namespace in self._plugin_classes:
            warning(f"Plugin {namespace} already loaded, skipping duplicate load")
            return

        # 检查版本兼容性
        if not self._compatibility_checker.is_compatible(metadata):
            warning(
                f"Plugin {namespace} is not compatible with current app version {self._app_version}"
            )
            return

        # 检查插件可用性（依赖完整性）
        availability = self._availability_checker.check_availability(metadata)
        if not availability["available"]:
            warning(
                f"Plugin {namespace} is not available: {', '.join(availability['reasons'])}"
            )
            return

        # 注册插件
        self._plugin_metadata[namespace] = metadata
        self._plugin_classes[namespace] = plugin_class
        info(
            f"Successfully loaded plugin: {namespace} ({metadata.name} v{metadata.version})"
        )

        # 发布插件加载事件
        self._event_bus.publish(
            PluginLoadedEvent(
                plugin_id=namespace, plugin_name=metadata.name, version=metadata.version
            )
        )

    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload plugin

        Args:
            plugin_id: Plugin ID (namespace)

        Returns:
            Whether unload was successful
        """
        with self._lock:
            if plugin_id not in self._plugins:
                warning(f"Plugin {plugin_id} not loaded, cannot unload")
                return False

            try:
                plugin = self._plugins[plugin_id]

                # If plugin is running, stop it first
                if plugin.is_started:
                    plugin.stop()

                # Clean up plugin
                plugin.cleanup()

                # Remove from manager
                del self._plugins[plugin_id]
                if plugin_id in self._plugin_classes:
                    del self._plugin_classes[plugin_id]
                if plugin_id in self._plugin_metadata:
                    del self._plugin_metadata[plugin_id]

                # Publish plugin unloaded event
                metadata = self._plugin_metadata.get(plugin_id)
                plugin_name = metadata.name if metadata else plugin_id
                self._event_bus.publish(
                    PluginUnloadedEvent(plugin_id=plugin_id, plugin_name=plugin_name)
                )

                info(f"Successfully unloaded plugin: {plugin_id}")
                return True

            except Exception as e:
                error(f"Failed to unload plugin {plugin_id}: {e}")
                return False

    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """
        Get specified plugin

        Args:
            plugin_id: Plugin ID (namespace)

        Returns:
            Plugin instance or None
        """
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> List[IPlugin]:
        """Get all plugins"""
        return list(self._plugins.values())

    def is_plugin_loaded(self, plugin_id: str) -> bool:
        """Check if plugin is loaded"""
        return plugin_id in self._plugins

    def get_plugin_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get plugin metadata"""
        return self._plugin_metadata.get(plugin_id)

    def get_all_plugin_metadata(self) -> Dict[str, PluginMetadata]:
        """Get all plugin metadata"""
        return self._plugin_metadata.copy()

    @with_error_handling(error_code="PLUGIN_INIT_ALL_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    @monitor_metrics("plugin_initialize_all", include_labels=True)
    def initialize_all_plugins(self) -> bool:
        """初始化所有已加载的插件"""
        with self._lock:
            if self._is_initialized:
                return True

            info("Starting initialization of all plugins...")

            success = True
            for plugin_id, plugin_class in self._plugin_classes.items():
                if plugin_id in self._plugins:
                    # 插件已经初始化
                    continue

                try:
                    # 获取插件元数据
                    metadata = self._plugin_metadata[plugin_id]

                    # 创建插件实例
                    plugin = plugin_class(
                        plugin_id=plugin_id,
                        name=metadata.name,
                        version=metadata.version,
                        description=metadata.description,
                    )

                    # 设置依赖注入容器
                    plugin.container = self._container

                    # 初始化插件
                    if plugin.initialize():
                        self._plugins[plugin_id] = plugin
                        info(f"Plugin {plugin_id} initialized successfully")
                    else:
                        warning(f"Plugin {plugin_id} initialization failed")
                        success = False

                except Exception as e:
                    error(f"Error initializing plugin {plugin_id}: {e}")
                    success = False

            self._is_initialized = True
            return success

    @with_error_handling(error_code="PLUGIN_START_ALL_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    @monitor_metrics("plugin_start_all", include_labels=True)
    def start_all_plugins(self) -> bool:
        """启动所有已初始化的插件"""
        if not self._is_initialized:
            # 如果还没有初始化，先初始化
            if not self.initialize_all_plugins():
                return False

        with self._lock:
            success = True
            for plugin_id, plugin in self._plugins.items():
                if not plugin.is_started:
                    if not plugin.start():
                        warning(f"Plugin {plugin_id} start failed")
                        success = False
                    else:
                        info(f"Plugin {plugin_id} started successfully")

            return success

    @with_error_handling(error_code="PLUGIN_STOP_ALL_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    @monitor_metrics("plugin_stop_all", include_labels=True)
    def stop_all_plugins(self) -> bool:
        """停止所有已启动的插件"""
        with self._lock:
            success = True
            # 按相反顺序停止插件（后启动的先停止）
            for plugin_id in reversed(list(self._plugins.keys())):
                plugin = self._plugins[plugin_id]
                if plugin.is_started:
                    if not plugin.stop():
                        warning(f"Plugin {plugin_id} stop failed")
                        success = False
                    else:
                        info(f"Plugin {plugin_id} stopped successfully")

            return success

    def cleanup_all_plugins(self) -> bool:
        """
        Cleanup all plugins

        Returns:
            Whether all plugins cleaned up successfully
        """
        if not self._plugins:
            return True

        success = True
        with self._lock:
            for plugin_id, plugin in self._plugins.items():
                try:
                    if plugin.cleanup():
                        info(f"Plugin {plugin_id} cleaned up successfully")
                    else:
                        error(f"Plugin {plugin_id} failed to cleanup")
                        success = False
                except Exception as e:
                    error(f"Unexpected error cleaning up plugin {plugin_id}: {e}")
                    success = False

        # 清空插件列表
        self._plugins.clear()
        self._plugin_classes.clear()
        self._plugin_metadata.clear()
        self._is_initialized = False

        if success:
            info("All plugins cleaned up successfully")
        else:
            warning("Some plugins failed to cleanup")

        return success
