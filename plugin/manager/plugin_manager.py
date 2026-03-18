"""
插件管理器
负责插件的加载、卸载、生命周期管理和依赖解析
"""

import os
from typing import Dict, List, Optional, Type
from threading import Lock

from plugin.base.plugin_base import PluginBase
from plugin.base.plugin_interface import IPluginManager, IPlugin
from plugin.manager.plugin_loader import PluginLoader
from plugin.manager.dependency_manager import PluginDependencyManager
from plugin.exceptions.plugin_exceptions import PluginLoadError
from plugin.events.plugin_events import PluginLoadedEvent, PluginUnloadedEvent
from core.di import ServiceContainer
from core.event.event_bus import EventBus
from core.logger import info, error, warning


class PluginManager(IPluginManager):
    """插件管理器 - 实现插件的完整生命周期管理"""
    
    def __init__(self, container: ServiceContainer, event_bus: EventBus):
        """
        初始化插件管理器
        
        Args:
            container: 依赖注入容器
            event_bus: 事件总线
        """
        self._container = container
        self._event_bus = event_bus
        self._plugins: Dict[str, PluginBase] = {}
        self._plugin_classes: Dict[str, Type[PluginBase]] = {}
        self._loader = PluginLoader()
        self._dependency_manager = PluginDependencyManager()
        self._lock = Lock()
        self._is_initialized = False
        
    def load_plugins(self, plugin_paths: List[str]) -> None:
        """
        加载插件
        
        Args:
            plugin_paths: 插件路径列表（可以是文件或目录）
        """
        with self._lock:
            for path in plugin_paths:
                if os.path.isfile(path):
                    self._load_plugin_from_file(path)
                elif os.path.isdir(path):
                    self._load_plugins_from_directory(path)
                else:
                    warning(f"Plugin path does not exist or is invalid: {path}")
    
    def _load_plugin_from_file(self, plugin_file: str) -> None:
        """Load single plugin from file"""
        try:
            plugin_class = self._loader.load_plugin_from_file(plugin_file)
            if plugin_class is not None:
                # Use class name as plugin ID (safer approach)
                plugin_id = plugin_class.__name__
                
                if plugin_id in self._plugin_classes:
                    warning(f"Plugin {plugin_id} already loaded, skipping duplicate load")
                    return
                
                self._plugin_classes[plugin_id] = plugin_class
                info(f"Successfully loaded plugin class: {plugin_id}")
                
                # Publish plugin loaded event (use class name as name)
                self._event_bus.publish(PluginLoadedEvent(
                    plugin_id=plugin_id,
                    plugin_name=plugin_id,
                    version="unknown"
                ))
                
        except PluginLoadError as e:
            error(f"Failed to load plugin file: {plugin_file}, error: {e}")
        except Exception as e:
            error(f"Unexpected error loading plugin file: {plugin_file}, error: {e}")
    
    def _load_plugins_from_directory(self, plugin_dir: str) -> None:
        """Load all plugins from directory"""
        try:
            plugin_classes = self._loader.load_plugin_from_directory(plugin_dir)
            for plugin_id, plugin_class in plugin_classes.items():
                if plugin_id in self._plugin_classes:
                    warning(f"Plugin {plugin_id} already loaded, skipping duplicate load")
                    continue
                
                self._plugin_classes[plugin_id] = plugin_class
                info(f"Successfully loaded plugin class: {plugin_id}")
                
                # Publish plugin loaded event
                self._event_bus.publish(PluginLoadedEvent(
                    plugin_id=plugin_id,
                    plugin_name=plugin_id,
                    version="unknown"
                ))
                
        except Exception as e:
            error(f"Failed to load plugins from directory: {plugin_dir}, error: {e}")
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload plugin
        
        Args:
            plugin_id: Plugin ID
            
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
                
                # Publish plugin unloaded event
                self._event_bus.publish(PluginUnloadedEvent(
                    plugin_id=plugin_id,
                    plugin_name=plugin.name
                ))
                
                info(f"Successfully unloaded plugin: {plugin_id}")
                return True
                
            except Exception as e:
                error(f"Failed to unload plugin {plugin_id}: {e}")
                return False
    
    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """
        Get specified plugin
        
        Args:
            plugin_id: Plugin ID
            
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
    
    def initialize_all_plugins(self) -> bool:
        """
        Initialize all plugins
        
        Returns:
            Whether all plugins initialized successfully
        """
        if not self._is_initialized:
            info("Starting initialization of all plugins...")
            self._is_initialized = True
        
        # 如果没有插件类，直接返回True
        if not self._plugin_classes:
            return True
            
        success = True
        with self._lock:
            # 按加载顺序初始化插件
            for plugin_id, plugin_class in self._plugin_classes.items():
                if plugin_id in self._plugins:
                    # 插件已经初始化
                    continue
                
                try:
                    # 创建插件实例
                    plugin = plugin_class(plugin_id, plugin_id, "1.0.0")
                    
                    # 设置依赖注入容器
                    plugin.container = self._container
                    
                    # 初始化插件
                    if plugin.initialize():
                        self._plugins[plugin_id] = plugin
                        info(f"Plugin {plugin_id} initialized successfully")
                    else:
                        error(f"Failed to initialize plugin: {plugin_id}")
                        success = False
                        
                except Exception as e:
                    error(f"Exception during plugin initialization: {plugin_id}, error: {e}")
                    success = False
            
            if success:
                info("All plugins initialized successfully")
            else:
                warning("Some plugins failed to initialize")
            
            return success
    
    def start_all_plugins(self) -> bool:
        """
        Start all plugins
        
        Returns:
            Whether all plugins started successfully
        """
        if not self._is_initialized:
            # 如果还没有初始化，先初始化
            if not self.initialize_all_plugins():
                return False
        
        success = True
        with self._lock:
            for plugin_id, plugin in self._plugins.items():
                if not plugin.is_started:
                    try:
                        if plugin.start():
                            info(f"Plugin {plugin_id} started successfully")
                        else:
                            error(f"Failed to start plugin: {plugin_id}")
                            success = False
                    except Exception as e:
                        error(f"Exception during plugin start: {plugin_id}, error: {e}")
                        success = False
            
            if success:
                info("All plugins started successfully")
            else:
                warning("Some plugins failed to start")
            
            return success
    
    def stop_all_plugins(self) -> bool:
        """
        Stop all plugins
        
        Returns:
            Whether all plugins stopped successfully
        """
        success = True
        with self._lock:
            for plugin_id, plugin in self._plugins.items():
                if plugin.is_started:
                    try:
                        if plugin.stop():
                            info(f"Plugin {plugin_id} stopped successfully")
                        else:
                            error(f"Failed to stop plugin: {plugin_id}")
                            success = False
                    except Exception as e:
                        error(f"Exception during plugin stop: {plugin_id}, error: {e}")
                        success = False
            
            if success:
                info("All plugins stopped successfully")
            else:
                warning("Some plugins failed to stop")
            
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
        self._is_initialized = False
        
        if success:
            info("All plugins cleaned up successfully")
        else:
            warning("Some plugins failed to cleanup")
            
        return success
