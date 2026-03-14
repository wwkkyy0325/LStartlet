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
                raise PluginLoadError("unknown", f"插件文件不存在: {plugin_file_path}")
            
            # 获取插件模块名称
            plugin_dir = os.path.dirname(plugin_file_path)
            plugin_filename = os.path.basename(plugin_file_path)
            if not plugin_filename.endswith('.py'):
                raise PluginLoadError("unknown", f"插件文件必须是 .py 文件: {plugin_file_path}")
            
            module_name = plugin_filename[:-3]  # 移除 .py 扩展名
            
            # 添加插件目录到 Python 路径（如果还没有添加）
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            # 检查模块是否已经加载
            if module_name in self._loaded_modules:
                return self._get_plugin_class_from_module(self._loaded_modules[module_name])
            
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(module_name, plugin_file_path)
            if spec is None or spec.loader is None:
                raise PluginLoadError("unknown", f"无法加载插件模块: {plugin_file_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 缓存加载的模块
            self._loaded_modules[module_name] = module
            
            # 从模块中获取插件类
            plugin_class = self._get_plugin_class_from_module(module)
            if plugin_class is None:
                raise PluginLoadError("unknown", f"插件模块 {plugin_file_path} 中未找到有效的插件类")
            
            return plugin_class
            
        except Exception as e:
            raise PluginLoadError("unknown", f"加载插件文件失败: {plugin_file_path}, 错误: {e}", e)
    
    def _get_plugin_class_from_module(self, module: Any) -> Optional[Type[PluginBase]]:
        """
        从模块中提取插件类
        
        Args:
            module: 已加载的模块
            
        Returns:
            插件类或 None
        """
        # 查找所有继承自 PluginBase 的类
        plugin_classes: List[Type[PluginBase]] = []
        for attr_name in dir(module):
            # 跳过私有属性和特殊方法
            if attr_name.startswith('_'):
                continue
                
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, PluginBase) and 
                attr != PluginBase):
                # 额外检查：确保类定义在当前模块中（避免导入的类）
                if hasattr(attr, '__module__') and attr.__module__ == module.__name__:
                    print(f"DEBUG: Found plugin class: {attr_name}, module: {attr.__module__}")
                    plugin_classes.append(attr)
        
        if len(plugin_classes) == 0:
            print(f"DEBUG: No plugin classes found in module {module.__name__}")
            return None
        elif len(plugin_classes) > 1:
            # 如果有多个插件类，选择第一个
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
        
        # 遍历目录中的所有 .py 文件
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                file_path = os.path.join(plugin_dir, filename)
                try:
                    plugin_class = self.load_plugin_from_file(file_path)
                    if plugin_class is not None:
                        # 直接使用类名作为插件ID（临时方案）
                        # 实际项目中应该要求插件类定义静态属性或方法来获取plugin_id
                        plugin_id = plugin_class.__name__
                        plugin_classes[plugin_id] = plugin_class
                except Exception as e:
                    # 记录错误但继续加载其他插件
                    print(f"警告: 加载插件 {filename} 失败: {e}")
                    continue
        
        return plugin_classes