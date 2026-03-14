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
from plugin.exceptions.plugin_exceptions import PluginLoadError, PluginInitializeError
from plugin.events.plugin_events import (
    PluginLoadedEvent, PluginUnloadedEvent, PluginInitializedEvent,
    PluginStartedEvent, PluginStoppedEvent
)
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
                    warning(f"插件路径不存在或无效: {path}")
    
    def _load_plugin_from_file(self, plugin_file: str) -> None:
        """从文件加载单个插件"""
        try:
            plugin_class = self._loader.load_plugin_from_file(plugin_file)
            if plugin_class is not None:
                # 使用类名作为插件ID（更安全的方式）
                plugin_id = plugin_class.__name__
                
                if plugin_id in self._plugin_classes:
                    warning(f"插件 {plugin_id} 已经加载，跳过重复加载")
                    return
                
                self._plugin_classes[plugin_id] = plugin_class
                info(f"成功加载插件类: {plugin_id}")
                
                # 发布插件加载事件（使用类名作为名称）
                self._event_bus.publish(PluginLoadedEvent(
                    plugin_id=plugin_id,
                    plugin_name=plugin_id,
                    version="unknown"
                ))
                
        except PluginLoadError as e:
            error(f"加载插件文件失败: {plugin_file}, 错误: {e}")
        except Exception as e:
            error(f"加载插件文件时发生未预期错误: {plugin_file}, 错误: {e}")
    
    def _load_plugins_from_directory(self, plugin_dir: str) -> None:
        """从目录加载所有插件"""
        try:
            plugin_classes = self._loader.load_plugin_from_directory(plugin_dir)
            for plugin_id, plugin_class in plugin_classes.items():
                if plugin_id in self._plugin_classes:
                    warning(f"插件 {plugin_id} 已经加载，跳过重复加载")
                    continue
                
                self._plugin_classes[plugin_id] = plugin_class
                info(f"成功加载插件类: {plugin_id}")
                
                # 发布插件加载事件
                self._event_bus.publish(PluginLoadedEvent(
                    plugin_id=plugin_id,
                    plugin_name=plugin_id,
                    version="unknown"
                ))
                
        except Exception as e:
            error(f"从目录加载插件失败: {plugin_dir}, 错误: {e}")
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            卸载是否成功
        """
        with self._lock:
            if plugin_id not in self._plugins:
                warning(f"插件 {plugin_id} 未加载，无法卸载")
                return False
            
            try:
                plugin = self._plugins[plugin_id]
                
                # 如果插件正在运行，先停止它
                if plugin.is_started:
                    plugin.stop()
                
                # 清理插件
                plugin.cleanup()
                
                # 从管理器中移除
                del self._plugins[plugin_id]
                if plugin_id in self._plugin_classes:
                    del self._plugin_classes[plugin_id]
                
                # 发布插件卸载事件
                self._event_bus.publish(PluginUnloadedEvent(
                    plugin_id=plugin_id,
                    plugin_name=plugin.name
                ))
                
                info(f"成功卸载插件: {plugin_id}")
                return True
                
            except Exception as e:
                error(f"卸载插件 {plugin_id} 失败: {e}")
                return False
    
    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """
        获取指定插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            插件实例或 None
        """
        return self._plugins.get(plugin_id)
    
    def get_all_plugins(self) -> List[IPlugin]:
        """获取所有插件"""
        return list(self._plugins.values())
    
    def is_plugin_loaded(self, plugin_id: str) -> bool:
        """检查插件是否已加载"""
        return plugin_id in self._plugins
    
    def initialize_all_plugins(self) -> bool:
        """
        初始化所有插件
        
        Returns:
            所有插件是否初始化成功
        """
        if not self._is_initialized:
            info("开始初始化所有插件...")
            self._is_initialized = True
        
        success = True
        with self._lock:
            # 按依赖顺序初始化插件（简单实现：按加载顺序）
            for plugin_id, plugin_class in self._plugin_classes.items():
                if plugin_id in self._plugins:
                    # 插件已经初始化
                    continue
                
                try:
                    # 创建插件实例
                    plugin = self._create_plugin_instance(plugin_class, plugin_id)
                    if plugin is None:
                        error(f"创建插件实例失败: {plugin_id}")
                        success = False
                        continue
                    
                    # 设置依赖注入容器
                    plugin.container = self._container
                    
                    # 初始化插件
                    if plugin.initialize():
                        self._plugins[plugin_id] = plugin
                        info(f"插件 {plugin_id} 初始化成功")
                        
                        # 发布插件初始化事件
                        self._event_bus.publish(PluginInitializedEvent(
                            plugin_id=plugin_id,
                            plugin_name=plugin.name,
                            success=True
                        ))
                    else:
                        error(f"插件 {plugin_id} 初始化失败")
                        success = False
                        
                        # 发布插件初始化失败事件
                        self._event_bus.publish(PluginInitializedEvent(
                            plugin_id=plugin_id,
                            plugin_name=plugin.name,
                            success=False,
                            error_message="初始化失败"
                        ))
                        
                except PluginInitializeError as e:
                    error(f"插件 {plugin_id} 初始化异常: {e}")
                    success = False
                    
                    # 发布插件初始化失败事件
                    self._event_bus.publish(PluginInitializedEvent(
                        plugin_id=plugin_id,
                        plugin_name=getattr(e, 'plugin_id', 'unknown'),
                        success=False,
                        error_message=str(e)
                    ))
                    
                except Exception as e:
                    error(f"插件 {plugin_id} 初始化时发生未预期错误: {e}")
                    success = False
                    
                    # 发布插件初始化失败事件
                    self._event_bus.publish(PluginInitializedEvent(
                        plugin_id=plugin_id,
                        plugin_name="unknown",
                        success=False,
                        error_message=f"未预期错误: {e}"
                    ))
        
        if success:
            info("所有插件初始化完成")
        else:
            warning("部分插件初始化失败")
            
        return success
    
    def _create_plugin_instance(self, plugin_class: Type[PluginBase], plugin_id: str) -> Optional[PluginBase]:
        """
        创建插件实例
        
        Args:
            plugin_class: 插件类
            plugin_id: 插件ID
            
        Returns:
            插件实例或 None
        """
        try:
            # 尝试获取插件的元数据
            name = getattr(plugin_class, 'PLUGIN_NAME', plugin_id)
            version = getattr(plugin_class, 'PLUGIN_VERSION', '1.0.0')
            description = getattr(plugin_class, 'PLUGIN_DESCRIPTION', '')
            
            # 使用插件元数据创建实例
            plugin = plugin_class(plugin_id, name, version, description)
            return plugin
                
        except Exception as e:
            error(f"创建插件实例时发生错误: {e}")
            return None
    
    def start_all_plugins(self) -> bool:
        """
        启动所有插件
        
        Returns:
            所有插件是否启动成功
        """
        info("开始启动所有插件...")
        success = True
        
        with self._lock:
            for plugin in self._plugins.values():
                try:
                    if plugin.start():
                        info(f"插件 {plugin.plugin_id} 启动成功")
                        
                        # 发布插件启动事件
                        self._event_bus.publish(PluginStartedEvent(
                            plugin_id=plugin.plugin_id,
                            plugin_name=plugin.name,
                            success=True
                        ))
                    else:
                        error(f"插件 {plugin.plugin_id} 启动失败")
                        success = False
                        
                        # 发布插件启动失败事件
                        self._event_bus.publish(PluginStartedEvent(
                            plugin_id=plugin.plugin_id,
                            plugin_name=plugin.name,
                            success=False,
                            error_message="启动失败"
                        ))
                        
                except Exception as e:
                    error(f"插件 {plugin.plugin_id} 启动时发生未预期错误: {e}")
                    success = False
                    
                    # 发布插件启动失败事件
                    self._event_bus.publish(PluginStartedEvent(
                        plugin_id=plugin.plugin_id,
                        plugin_name=plugin.name,
                        success=False,
                        error_message=f"未预期错误: {e}"
                    ))
        
        if success:
            info("所有插件启动完成")
        else:
            warning("部分插件启动失败")
            
        return success
    
    def stop_all_plugins(self) -> bool:
        """
        停止所有插件
        
        Returns:
            所有插件是否停止成功
        """
        info("开始停止所有插件...")
        success = True
        
        with self._lock:
            # 反向停止插件（后启动的先停止）
            for plugin in reversed(list(self._plugins.values())):
                try:
                    if plugin.stop():
                        info(f"插件 {plugin.plugin_id} 停止成功")
                        
                        # 发布插件停止事件
                        self._event_bus.publish(PluginStoppedEvent(
                            plugin_id=plugin.plugin_id,
                            plugin_name=plugin.name,
                            success=True
                        ))
                    else:
                        error(f"插件 {plugin.plugin_id} 停止失败")
                        success = False
                        
                        # 发布插件停止失败事件
                        self._event_bus.publish(PluginStoppedEvent(
                            plugin_id=plugin.plugin_id,
                            plugin_name=plugin.name,
                            success=False,
                            error_message="停止失败"
                        ))
                        
                except Exception as e:
                    error(f"插件 {plugin.plugin_id} 停止时发生未预期错误: {e}")
                    success = False
                    
                    # 发布插件停止失败事件
                    self._event_bus.publish(PluginStoppedEvent(
                        plugin_id=plugin.plugin_id,
                        plugin_name=plugin.name,
                        success=False,
                        error_message=f"未预期错误: {e}"
                    ))
        
        if success:
            info("所有插件停止完成")
        else:
            warning("部分插件停止失败")
            
        return success
    
    def cleanup_all_plugins(self) -> bool:
        """
        清理所有插件
        
        Returns:
            所有插件是否清理成功
        """
        info("开始清理所有插件...")
        success = True
        
        with self._lock:
            # 反向清理插件
            for plugin in reversed(list(self._plugins.values())):
                try:
                    if plugin.cleanup():
                        info(f"插件 {plugin.plugin_id} 清理成功")
                    else:
                        error(f"插件 {plugin.plugin_id} 清理失败")
                        success = False
                        
                except Exception as e:
                    error(f"插件 {plugin.plugin_id} 清理时发生未预期错误: {e}")
                    success = False
        
        # 清空插件列表
        self._plugins.clear()
        self._plugin_classes.clear()
        self._is_initialized = False
        
        if success:
            info("所有插件清理完成")
        else:
            warning("部分插件清理失败")
            
        return success