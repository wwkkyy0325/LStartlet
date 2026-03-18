"""
插件加载器
负责动态加载和验证插件模块
"""

import importlib
import importlib.util
import os
import sys
from typing import Dict, Any, List, Optional, Type

from plugin.base.plugin_base import PluginBase
from plugin.exceptions.plugin_exceptions import PluginLoadError


class PluginLoader:
    """插件加载器 - 负责动态加载插件模块"""
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
    
    def load_plugin_from_file(self, plugin_file_path: str) -> Optional[Type[PluginBase]]:
        """
        从文件加载插件类
        
        Args:
            plugin_file_path: 插件文件路径
            
        Returns:
            插件类或 None（如果加载失败）
        """
        try:
            if not os.path.exists(plugin_file_path):
                raise PluginLoadError("unknown", f"Plugin file does not exist: {plugin_file_path}")
            
            # Get plugin module name
            plugin_dir = os.path.dirname(plugin_file_path)
            plugin_filename = os.path.basename(plugin_file_path)
            if not plugin_filename.endswith('.py'):
                raise PluginLoadError("unknown", f"Plugin file must be a .py file: {plugin_file_path}")
            
            module_name = plugin_filename[:-3]  # Remove .py extension
            
            # Add plugin directory to Python path (if not already added)
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            # Check if module is already loaded
            if module_name in self._loaded_modules:
                return self._get_plugin_class_from_module(self._loaded_modules[module_name])
            
            # Dynamically load module
            spec = importlib.util.spec_from_file_location(module_name, plugin_file_path)
            if spec is None or spec.loader is None:
                raise PluginLoadError("unknown", f"Unable to load plugin module: {plugin_file_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Cache loaded module
            self._loaded_modules[module_name] = module
            
            # Get plugin class from module
            plugin_class = self._get_plugin_class_from_module(module)
            if plugin_class is None:
                raise PluginLoadError("unknown", f"Plugin module {plugin_file_path} does not contain a valid plugin class")
            
            return plugin_class
            
        except Exception as e:
            raise PluginLoadError("unknown", f"Failed to load plugin file: {plugin_file_path}, Error: {e}", e)
    
    def _get_plugin_class_from_module(self, module: Any) -> Optional[Type[PluginBase]]:
        """
        从模块中提取插件类
        
        Args:
            module: 已加载的模块
            
        Returns:
            插件类或 None
        """
        # Find all classes that inherit from PluginBase
        plugin_classes: List[Type[PluginBase]] = []
        for attr_name in dir(module):
            # Skip private attributes and special methods
            if attr_name.startswith('_'):
                continue
                
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, PluginBase) and 
                attr != PluginBase):
                # Additional check: Ensure class is defined in the current module (avoid imported classes)
                if hasattr(attr, '__module__') and attr.__module__ == module.__name__:
                    print(f"DEBUG: Found plugin class: {attr_name}, module: {attr.__module__}")
                    plugin_classes.append(attr)
        
        if len(plugin_classes) == 0:
            print(f"DEBUG: No plugin classes found in module {module.__name__}")
            return None
        elif len(plugin_classes) > 1:
            # If multiple plugin classes are found, select the first one
            print(f"DEBUG: Multiple plugin classes found, selecting first: {plugin_classes[0].__name__}")
            return plugin_classes[0]
        else:
            print(f"DEBUG: Single plugin class found: {plugin_classes[0].__name__}")
            return plugin_classes[0]
    
    def load_plugin_from_directory(self, plugin_dir: str) -> Dict[str, Type[PluginBase]]:
        """
        从目录加载所有插件
        
        Args:
            plugin_dir: 插件目录路径
            
        Returns:
            插件ID到插件类的映射
        """
        plugin_classes: Dict[str, Type[PluginBase]] = {}
        
        if not os.path.exists(plugin_dir):
            return plugin_classes
        
        # Traverse all .py files in the directory
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                file_path = os.path.join(plugin_dir, filename)
                try:
                    plugin_class = self.load_plugin_from_file(file_path)
                    if plugin_class is not None:
                        # Directly use class name as plugin ID (temporary solution)
                        # In a real project, plugins should define a static attribute or method to get plugin_id
                        plugin_id = plugin_class.__name__
                        plugin_classes[plugin_id] = plugin_class
                except Exception as e:
                    # Log error but continue loading other plugins
                    print(f"警告: 加载插件 {filename} 失败: {e}")
                    continue
        
        return plugin_classes