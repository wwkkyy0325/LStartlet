"""
插件加载器
负责动态加载和验证插件模块
"""

import importlib
import importlib.util
import os
import sys
from typing import Dict, Any, List, Optional, Type, Tuple

from core.logger import error
from plugin.base.plugin_base import PluginBase
from plugin.exceptions.plugin_exceptions import PluginLoadError
from plugin.metadata import PluginMetadata


class PluginLoader:
    """插件加载器 - 负责动态加载插件模块"""
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
    
    def load_plugin_from_wheel(self, wheel_path: str) -> Optional[Tuple[PluginMetadata, Type[PluginBase]]]:
        """
        从 wheel 文件加载插件
        
        Args:
            wheel_path: wheel 文件路径
            
        Returns:
            (metadata, plugin_class) 元组或 None（如果加载失败）
        """
        try:
            if not os.path.exists(wheel_path):
                raise PluginLoadError("unknown", f"Plugin wheel file does not exist: {wheel_path}")
            
            if not wheel_path.endswith('.whl'):
                raise PluginLoadError("unknown", f"Plugin file must be a .whl file: {wheel_path}")
            
            # 解压 wheel 文件到临时目录
            import tempfile
            import zipfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(wheel_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # 查找 plugin.json
                plugin_json_path = None
                for root, dirs, files in os.walk(temp_dir):
                    if 'plugin.json' in files:
                        plugin_json_path = os.path.join(root, 'plugin.json')
                        break
                
                if not plugin_json_path:
                    raise PluginLoadError("unknown", f"plugin.json not found in wheel file: {wheel_path}")
                
                # 加载元数据
                metadata = PluginMetadata.from_file(plugin_json_path)
                
                # 获取入口点信息
                module_name = metadata.entry_point['module']
                class_name = metadata.entry_point['class']
                
                # 添加临时目录到 Python 路径
                if temp_dir not in sys.path:
                    sys.path.insert(0, temp_dir)
                
                # 导入模块
                try:
                    module = importlib.import_module(module_name)
                except ImportError as e:
                    raise PluginLoadError(metadata.namespace, f"Failed to import module {module_name}: {e}")
                
                # 获取插件类
                if not hasattr(module, class_name):
                    raise PluginLoadError(metadata.namespace, f"Class {class_name} not found in module {module_name}")
                
                plugin_class = getattr(module, class_name)
                
                # 验证插件类
                if not isinstance(plugin_class, type) or not issubclass(plugin_class, PluginBase):
                    raise PluginLoadError(metadata.namespace, f"{class_name} is not a valid PluginBase subclass")
                
                return metadata, plugin_class
                
        except Exception as e:
            raise PluginLoadError("unknown", f"Failed to load plugin wheel: {wheel_path}, Error: {e}", e)
    
    def load_plugin_from_directory(self, plugin_dir: str) -> Dict[str, Tuple[PluginMetadata, Type[PluginBase]]]:
        """
        从目录加载所有插件（支持 wheel 文件和源码目录）
        
        Args:
            plugin_dir: 插件目录路径
            
        Returns:
            插件命名空间到 (metadata, plugin_class) 元组的映射
        """
        plugins: Dict[str, Tuple[PluginMetadata, Type[PluginBase]]] = {}
        
        if not os.path.exists(plugin_dir):
            return plugins
        
        # 首先处理 wheel 文件
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.whl'):
                file_path = os.path.join(plugin_dir, filename)
                try:
                    result = self.load_plugin_from_wheel(file_path)
                    if result is not None:
                        metadata, plugin_class = result
                        plugins[metadata.namespace] = (metadata, plugin_class)
                except Exception as e:
                    error(f"警告: 加载插件 wheel {filename} 失败: {e}")
                    continue
        
        # 然后处理源码目录（包含 plugin.json 的目录）
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)
            if os.path.isdir(item_path):
                plugin_json_path = os.path.join(item_path, 'plugin.json')
                if os.path.exists(plugin_json_path):
                    try:
                        metadata = PluginMetadata.from_file(plugin_json_path)
                        plugin_class = self._load_plugin_from_source_dir(item_path, metadata)
                        if plugin_class is not None:
                            plugins[metadata.namespace] = (metadata, plugin_class)
                    except Exception as e:
                        error(f"警告: 加载插件源码目录 {item} 失败: {e}")
                        continue
        
        return plugins
    
    def _load_plugin_from_source_dir(self, plugin_dir: str, metadata: PluginMetadata) -> Optional[Type[PluginBase]]:
        """从源码目录加载插件"""
        try:
            # 添加插件目录到 Python 路径
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            # 获取入口点信息
            module_name = metadata.entry_point['module']
            class_name = metadata.entry_point['class']
            
            # 导入模块
            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                raise PluginLoadError(metadata.namespace, f"Failed to import module {module_name}: {e}")
            
            # 获取插件类
            if not hasattr(module, class_name):
                raise PluginLoadError(metadata.namespace, f"Class {class_name} not found in module {module_name}")
            
            plugin_class = getattr(module, class_name)
            
            # 验证插件类
            if not isinstance(plugin_class, type) or not issubclass(plugin_class, PluginBase):
                raise PluginLoadError(metadata.namespace, f"{class_name} is not a valid PluginBase subclass")
            
            return plugin_class
            
        except Exception as e:
            raise PluginLoadError(metadata.namespace, f"Failed to load plugin from source directory: {plugin_dir}, Error: {e}", e)
    
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