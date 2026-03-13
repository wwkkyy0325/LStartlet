"""
配置管理器核心实现
提供配置注册、获取、验证、监听等功能
"""

import json
import os
from typing import Any, Dict, Optional, Callable, List, Type, cast
# 使用项目自定义日志管理器
from core.logger import info, warning, error, debug
# 使用项目自定义错误处理系统
from core.error import handle_error
from core.error.exceptions import OCRConfigError
from .config_item import ConfigItem


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        self._config_file = config_file or "config.json"
        self._config_items: Dict[str, ConfigItem] = {}
        self._config_sources: Dict[str, str] = {}  # 记录每个配置项的来源
        self._listeners: List[Callable[[str, Any, Any], None]] = []
        self._key_listeners: Dict[str, List[Callable[[str, Any, Any], None]]] = {}
        
        try:
            # 先检查并加载现有配置文件（如果存在）
            existing_config_by_source = self._load_existing_config()
            
            # 注册默认配置项（标记为系统来源）
            self._register_default_configs()
            
            # 发布配置项注册事件，允许外部模块注册自定义配置项
            self._publish_config_registration_event()
            
            # 如果有现有配置，应用它们的值（但不改变来源分类）
            if existing_config_by_source:
                self._apply_existing_config_values(existing_config_by_source)
            
            # 如果配置文件不存在，保存默认配置
            if not existing_config_by_source and not os.path.exists(self._config_file):
                self.save_to_file()
            
            # 注册应用程序生命周期事件监听器
            self._register_lifecycle_listeners()
            
            info("配置管理器初始化完成")
        except Exception as e:
            error_msg = f"配置管理器初始化失败: {e}"
            handle_error(OCRConfigError(error_msg, context={"config_file": self._config_file}))
            raise
    
    def _register_lifecycle_listeners(self) -> None:
        """注册应用程序生命周期事件监听器"""
        try:
            from core.event.event_bus import EventBus
            from core.event.events.scheduler_events import ApplicationLifecycleEvent
            
            event_bus = EventBus()
            event_bus.subscribe_lambda(
                ApplicationLifecycleEvent.EVENT_TYPE,
                self._on_application_lifecycle_event,
                "config_manager_lifecycle_handler"
            )
            
            debug("配置管理器已注册应用程序生命周期事件监听器")
        except ImportError:
            # 如果事件系统不可用，跳过事件监听器注册
            debug("事件系统不可用，跳过配置管理器生命周期事件监听器注册")
        except Exception as e:
            error(f"注册配置管理器生命周期事件监听器失败: {e}")
            # 不抛出异常，确保配置管理器仍能正常初始化
            pass
    
    def _on_application_lifecycle_event(self, event: Any) -> bool:
        """处理应用程序生命周期事件"""
        try:
            if hasattr(event, 'lifecycle_stage'):
                if event.lifecycle_stage == "stopping":
                    # 应用程序正在停止，保存当前配置
                    self.save_to_file()
                    info("配置管理器：应用程序停止，已保存当前配置")
                elif event.lifecycle_stage == "stopped":
                    # 应用程序已停止，清理资源
                    self._config_items.clear()
                    self._config_sources.clear()
                    self._listeners.clear()
                    self._key_listeners.clear()
                    info("配置管理器：资源清理完成")
            return True
        except Exception as e:
            error(f"处理应用程序生命周期事件失败: {e}")
            return False

    def _load_existing_config(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        加载现有配置文件（如果存在），保持原有的分类结构
        
        Returns:
            按来源分类的配置字典，如果文件不存在则返回None
        """
        try:
            if not os.path.exists(self._config_file):
                return None
            
            with open(self._config_file, 'r', encoding='utf-8') as f:
                config_data: Dict[str, Any] = json.load(f)
            
            # 如果是扁平格式（旧格式），转换为分类格式
            if config_data:
                # 显式检查第一个值是否为字典
                first_key = next(iter(config_data.keys()))
                first_value = config_data[first_key]
                if not isinstance(first_value, dict):
                    # 扁平格式，假设都是system配置
                    return {"system": config_data}
            
            # 已经是分类格式，直接返回
            return config_data
            
        except Exception as e:
            error(f"加载现有配置文件失败: {e}")
            return None
    
    def _apply_existing_config_values(self, existing_config_by_source: Dict[str, Dict[str, Any]]) -> None:
        """
        应用现有配置文件中的值，但保持配置项的来源分类不变
        
        Args:
            existing_config_by_source: 按来源分类的现有配置
        """
        for source, config_dict in existing_config_by_source.items():
            # 直接使用 config_dict，类型注解已经明确了
            for key, value in config_dict.items():
                if key in self._config_items:
                    # 如果配置项已存在，只更新值，不改变来源
                    self._config_items[key].current_value = value
                else:
                    # 如果配置项不存在，创建新的配置项，来源为原文件中的分类
                    value_type = self._infer_value_type(value)
                    self._config_items[key] = ConfigItem(
                        key=key,
                        default_value=value,
                        current_value=value,
                        value_type=value_type,
                        description=f"从配置文件加载的配置项",
                        validator=None
                    )
                    self._config_sources[key] = source
    
    def _infer_value_type(self, value: Any) -> Type[Any]:
        """推断值的类型"""
        if isinstance(value, str):
            return str
        elif isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        elif isinstance(value, bool):
            return bool
        elif value is None:
            return type(None)
        else:
            # 对于其他类型，统一转换为字符串
            return str
    
    def _publish_config_registration_event(self) -> None:
        """发布配置项注册事件，允许外部模块注册自定义配置项"""
        try:
            from core.event.event_bus import EventBus
            from core.event.events.scheduler_events import ConfigItemRegisteredEvent
            
            event_bus = EventBus()
            config_register_event = ConfigItemRegisteredEvent(self, plugin_name="external")
            event_bus.publish(config_register_event)
            
            debug("已发布配置项注册事件，允许外部模块注册自定义配置项")
        except ImportError:
            # 如果事件系统不可用，跳过事件发布（保持向后兼容）
            debug("事件系统不可用，跳过配置项注册事件发布")
        except Exception as e:
            error(f"发布配置项注册事件失败: {e}")
            # 不抛出异常，确保配置管理器仍能正常初始化
            pass
    
    def _register_default_configs(self) -> None:
        """注册默认配置项（标记为系统来源）"""
        try:
            # OCR相关配置
            self.register_config_with_source("ocr_engine", "paddle", str, "OCR引擎类型 (paddle/tesseract)", plugin_name="system")
            self.register_config_with_source("language", "ch", str, "识别语言 (ch/en/...)", plugin_name="system")
            self.register_config_with_source("use_gpu", False, bool, "是否使用GPU加速", plugin_name="system")
            self.register_config_with_source("gpu_id", 0, int, "GPU设备ID", plugin_name="system")
            
            # 图像预处理配置
            self.register_config_with_source("preprocess_enabled", True, bool, "是否启用图像预处理", plugin_name="system")
            self.register_config_with_source("denoise_enabled", True, bool, "是否启用降噪", plugin_name="system")
            self.register_config_with_source("binarize_enabled", True, bool, "是否启用二值化", plugin_name="system")
            self.register_config_with_source("deskew_enabled", True, bool, "是否启用倾斜校正", plugin_name="system")
            
            # 性能配置
            self.register_config_with_source("max_workers", 4, int, "最大工作线程数", plugin_name="system")
            self.register_config_with_source("batch_size", 1, int, "批处理大小", plugin_name="system")
            self.register_config_with_source("timeout", 30.0, float, "处理超时时间（秒）", plugin_name="system")
            
            # 输出配置
            self.register_config_with_source("output_format", "text", str, "输出格式 (text/json)", plugin_name="system")
            self.register_config_with_source("confidence_threshold", 0.5, float, "置信度阈值", plugin_name="system")
            self.register_config_with_source("save_debug_images", False, bool, "是否保存调试图像", plugin_name="system")
        except Exception as e:
            error_msg = f"注册默认配置项失败: {e}"
            handle_error(OCRConfigError(error_msg))
            raise
    
    def register_config_with_source(
        self, 
        key: str, 
        default_value: Any, 
        value_type: Type[Any], 
        description: str = "",
        validator: Optional[Callable[[Any], bool]] = None,
        plugin_name: Optional[str] = None
    ) -> None:
        """
        注册配置项并指定来源
        
        Args:
            key: 配置项键名
            default_value: 默认值
            value_type: 值类型
            description: 描述信息
            validator: 自定义验证器函数
            plugin_name: 插件名称（来源标识），None表示系统默认
        """
        try:
            if key in self._config_items:
                warning(f"配置项 '{key}' 已存在，将被覆盖")
            
            self._config_items[key] = ConfigItem(
                key=key,
                default_value=default_value,
                current_value=default_value,
                value_type=value_type,
                description=description,
                validator=validator
            )
            self._config_sources[key] = plugin_name or "system"
            debug(f"注册配置项: {key} = {default_value} (来源: {plugin_name or 'system'})")
        except Exception as e:
            error_msg = f"注册配置项 '{key}' 失败: {e}"
            handle_error(OCRConfigError(error_msg, context={"key": key, "value": default_value}))
            raise
    
    def register_config(
        self, 
        key: str, 
        default_value: Any, 
        value_type: Type[Any], 
        description: str = "",
        validator: Optional[Callable[[Any], bool]] = None
    ) -> None:
        """
        注册配置项（兼容旧接口，默认来源为外部）
        
        Args:
            key: 配置项键名
            default_value: 默认值
            value_type: 值类型
            description: 描述信息
            validator: 自定义验证器函数
        """
        self.register_config_with_source(key, default_value, value_type, description, validator, "external")
    
    def get_config_source(self, key: str) -> Optional[str]:
        """
        获取配置项的来源
        
        Args:
            key: 配置项键名
            
        Returns:
            配置项来源（"system", "external", 或插件名称）
        """
        return self._config_sources.get(key)
    
    def get_all_configs_by_source(self) -> Dict[str, Dict[str, Any]]:
        """
        按来源分类获取所有配置项
        
        Returns:
            按来源分类的配置字典
        """
        configs_by_source: Dict[str, Dict[str, Any]] = {}
        for key, config_item in self._config_items.items():
            source = self._config_sources.get(key, "unknown")
            if source not in configs_by_source:
                configs_by_source[source] = {}
            configs_by_source[source][key] = config_item.current_value
        return configs_by_source
    
    def save_to_file(self, filepath: Optional[str] = None) -> bool:
        """
        保存配置到文件（按来源分类保存）
        
        Args:
            filepath: 文件路径，如果为None则使用初始化时的路径
            
        Returns:
            是否保存成功
        """
        try:
            save_path = filepath or self._config_file
            config_data: Dict[str, Dict[str, Any]] = {
                "system": {},
                "external": {}
            }
            
            # 按来源分类组织配置
            for key, config_item in self._config_items.items():
                source = self._config_sources.get(key, "external")
                if source == "system":
                    config_data["system"][key] = config_item.current_value
                elif source == "existing":
                    # existing配置项根据其实际值判断应该属于哪个分类
                    # 这里简单处理：如果值与系统默认值相同，则归为system，否则归为external
                    system_defaults: Dict[str, Any] = {
                        "ocr_engine": "paddle",
                        "language": "ch", 
                        "use_gpu": False,
                        "gpu_id": 0,
                        "preprocess_enabled": True,
                        "denoise_enabled": True,
                        "binarize_enabled": True,
                        "deskew_enabled": True,
                        "max_workers": 4,
                        "batch_size": 1,
                        "timeout": 30.0,
                        "output_format": "text",
                        "confidence_threshold": 0.5,
                        "save_debug_images": False
                    }
                    
                    if key in system_defaults and config_item.current_value == system_defaults[key]:
                        config_data["system"][key] = config_item.current_value
                    else:
                        config_data["external"][key] = config_item.current_value
                else:
                    # 其他来源（插件等）
                    if source not in config_data:
                        config_data[source] = {}
                    config_data[source][key] = config_item.current_value
            
            # 确保目录存在
            dir_path = os.path.dirname(save_path)
            if dir_path:  # 只有当目录路径不为空时才创建
                os.makedirs(dir_path, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            info(f"配置已按分类保存到: {save_path}")
            return True
        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            handle_error(OCRConfigError(error_msg, context={"file_path": filepath}))
            return False
    
    def load_from_file(self, filepath: Optional[str] = None) -> bool:
        """
        从文件加载配置（保留原有配置，不覆盖）
        
        Args:
            filepath: 文件路径，如果为None则使用初始化时的路径
            
        Returns:
            是否加载成功
        """
        try:
            load_path = filepath or self._config_file
            if not os.path.exists(load_path):
                warning(f"配置文件不存在: {load_path}")
                return False
            
            with open(load_path, 'r', encoding='utf-8') as f:
                config_data: Dict[str, Any] = json.load(f)
            
            success_count = 0
            
            # 处理分类配置
            for source, source_configs in config_data.items():
                if isinstance(source_configs, dict):
                    # 使用 cast 明确指定类型
                    typed_source_configs = cast(Dict[str, Any], source_configs)
                    for key, value in typed_source_configs.items():
                        if key in self._config_items:
                            # 如果配置项已注册，更新其值但保留来源
                            if self.set_config(key, value):
                                success_count += 1
                        else:
                            # 如果配置项未注册，注册为外部配置
                            # 这里需要推断类型，简单处理为字符串或保持原类型
                            value_type = self._infer_value_type(value)
                            self.register_config_with_source(key, value, value_type, f"从配置文件加载的配置项", plugin_name=source)
                            success_count += 1
                else:
                    # 兼容旧格式（扁平结构）
                    if source in self._config_items:
                        if self.set_config(source, source_configs):
                            success_count += 1
                    else:
                        value_type = self._infer_value_type(source_configs)
                        self.register_config_with_source(source, source_configs, value_type, f"从配置文件加载的配置项", plugin_name="legacy")
                        success_count += 1
            
            info(f"从文件加载了 {success_count} 个配置项")
            return True
        except Exception as e:
            error_msg = f"加载配置失败: {e}"
            handle_error(OCRConfigError(error_msg, context={"file_path": filepath}))
            return False
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置项值
        
        Args:
            key: 配置项键名
            value: 配置项值
            
        Returns:
            是否设置成功
        """
        try:
            if key not in self._config_items:
                error_msg = f"配置项 '{key}' 未注册，无法设置"
                handle_error(OCRConfigError(error_msg, context={"key": key, "attempted_value": value}))
                return False
            
            config_item = self._config_items[key]
            if not config_item.validate(value):
                error_msg = f"配置项 '{key}' 的值 '{value}' 验证失败"
                handle_error(OCRConfigError(error_msg, context={"key": key, "value": value}))
                return False
            
            old_value = config_item.current_value
            config_item.current_value = value
            
            # 触发全局监听器
            for listener in self._listeners:
                try:
                    listener(key, old_value, value)
                except Exception as e:
                    error(f"配置监听器执行失败: {e}")
            
            # 触发特定配置项的监听器
            if key in self._key_listeners:
                for listener in self._key_listeners[key]:
                    try:
                        listener(key, old_value, value)
                    except Exception as e:
                        error(f"配置项监听器执行失败: {e}")
            
            debug(f"配置项 '{key}' 已更新: {old_value} -> {value}")
            return True
        except Exception as e:
            error_msg = f"设置配置项 '{key}' 失败: {e}"
            handle_error(OCRConfigError(error_msg, context={"key": key, "value": value}))
            return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项值
        
        Args:
            key: 配置项键名
            default: 默认值
            
        Returns:
            配置项值
        """
        try:
            if key in self._config_items:
                return self._config_items[key].current_value
            return default
        except Exception as e:
            error_msg = f"获取配置项 '{key}' 失败: {e}"
            handle_error(OCRConfigError(error_msg, context={"key": key}))
            return default
    
    def has_config(self, key: str) -> bool:
        """
        检查配置项是否存在
        
        Args:
            key: 配置项键名
            
        Returns:
            是否存在
        """
        return key in self._config_items
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置项"""
        try:
            return {key: item.current_value for key, item in self._config_items.items()}
        except Exception as e:
            error_msg = f"获取所有配置项失败: {e}"
            handle_error(OCRConfigError(error_msg))
            return {}
    
    def add_listener(self, listener: Callable[[str, Any, Any], None]) -> None:
        """
        添加配置变更监听器
        
        Args:
            listener: 监听器函数，接收(键名, 旧值, 新值)参数
        """
        try:
            self._listeners.append(listener)
        except Exception as e:
            error_msg = f"添加配置监听器失败: {e}"
            handle_error(OCRConfigError(error_msg))
            raise
    
    def add_key_listener(self, key: str, listener: Callable[[str, Any, Any], None]) -> None:
        """
        为特定配置项添加监听器
        
        Args:
            key: 配置项键名
            listener: 监听器函数，接收(键名, 旧值, 新值)参数
        """
        try:
            if key not in self._key_listeners:
                self._key_listeners[key] = []
            self._key_listeners[key].append(listener)
        except Exception as e:
            error_msg = f"添加配置项监听器失败: {e}"
            handle_error(OCRConfigError(error_msg))
            raise
    
    def remove_listener(self, listener: Callable[[str, Any, Any], None]) -> bool:
        """
        移除配置变更监听器
        
        Args:
            listener: 监听器函数
            
        Returns:
            是否成功移除
        """
        try:
            self._listeners.remove(listener)
            return True
        except ValueError:
            return False
        except Exception as e:
            error_msg = f"移除配置监听器失败: {e}"
            handle_error(OCRConfigError(error_msg))
            return False
    
    def remove_key_listener(self, key: str, listener: Callable[[str, Any, Any], None]) -> bool:
        """
        移除特定配置项的监听器
        
        Args:
            key: 配置项键名
            listener: 监听器函数
            
        Returns:
            是否成功移除
        """
        try:
            if key in self._key_listeners:
                self._key_listeners[key].remove(listener)
                return True
            return False
        except ValueError:
            return False
        except Exception as e:
            error_msg = f"移除配置项监听器失败: {e}"
            handle_error(OCRConfigError(error_msg))
            return False
    
    def validate_all_configs(self) -> bool:
        """
        验证所有配置项
        
        Returns:
            是否全部验证通过
        """
        try:
            for config_item in self._config_items.values():
                if not config_item.validate(config_item.current_value):
                    return False
            return True
        except Exception as e:
            error_msg = f"配置验证异常: {e}"
            handle_error(OCRConfigError(error_msg))
            return False
    
    def reset_to_defaults(self) -> None:
        """重置所有配置项为默认值"""
        try:
            for config_item in self._config_items.values():
                config_item.current_value = config_item.default_value
        except Exception as e:
            error_msg = f"重置配置为默认值失败: {e}"
            handle_error(OCRConfigError(error_msg))
            raise

    def reset_config(self, key: str) -> bool:
        """
        重置单个配置项为默认值
        
        Args:
            key: 配置项键名
            
        Returns:
            是否重置成功
        """
        try:
            if key not in self._config_items:
                error_msg = f"配置项 '{key}' 未注册，无法重置"
                handle_error(OCRConfigError(error_msg, context={"key": key}))
                return False
            
            config_item = self._config_items[key]
            old_value = config_item.current_value
            config_item.current_value = config_item.default_value
            
            # 触发监听器
            for listener in self._listeners:
                try:
                    listener(key, old_value, config_item.default_value)
                except Exception as e:
                    error(f"配置监听器执行失败: {e}")
            if key in self._key_listeners:
                for listener in self._key_listeners[key]:
                    try:
                        listener(key, old_value, config_item.default_value)
                    except Exception as e:
                        error(f"配置项监听器执行失败: {e}")
            
            debug(f"配置项 '{key}' 已重置为默认值: {old_value} -> {config_item.default_value}")
            return True
        except Exception as e:
            error_msg = f"重置配置项 '{key}' 失败: {e}"
            handle_error(OCRConfigError(error_msg, context={"key": key}))
            return False