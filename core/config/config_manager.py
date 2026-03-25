"""
配置管理器核心实现
提供配置注册、获取、验证、监听等功能
"""

import yaml
import os
import json
from typing import Any, Dict, Optional, Callable, List, Type, cast
# 使用项目自定义日志管理器
from core.logger import info, warning, error, debug
# 使用项目自定义错误处理系统
from core.error import handle_error
from core.error.exceptions import OCRConfigError
from .config_item import ConfigItem
from core.decorators import with_error_handling, with_logging, monitor_metrics


class ConfigManager:
    """配置管理器"""
    
    def _validate_log_level(self, value: Any) -> bool:
        """验证日志级别配置值"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        return isinstance(value, str) and value.upper() in valid_levels

    def _validate_positive_int(self, value: Any) -> bool:
        """验证正整数配置值"""
        return isinstance(value, int) and value > 0

    def _validate_positive_float(self, value: Any) -> bool:
        """验证正浮点数配置值"""
        return isinstance(value, (int, float)) and value > 0

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager
        
        Args:
            config_file: Configuration file path, if None use default configuration
        """
        self._config_file = config_file or "config.yaml"
        self._config_items: Dict[str, ConfigItem] = {}
        self._config_sources: Dict[str, str] = {}  # 记录每个配置项的来源
        self._listeners: List[Callable[[str, Any, Any], None]] = []
        self._key_listeners: Dict[str, List[Callable[[str, Any, Any], None]]] = {}
        
        # 注册默认配置项
        self._register_default_configs()
        
    @monitor_metrics("config_save", include_labels=True)
    @with_error_handling(error_code="CONFIG_SAVE_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
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
                        "app_name": "Infrastructure Framework",
                        "app_version": "1.0.0",
                        "debug_mode": False,
                        "log_level": "DEBUG",
                        "log_console_enabled": True,
                        "log_file_enabled": True,
                        "log_max_size_mb": 100,
                        "log_backup_count": 7,
                        "data_dir": "data",
                        "output_dir": "output",
                        "temp_dir": "temp",
                        "max_workers": 4,
                        "timeout": 30.0,
                        "auto_save_config": True
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
                yaml.dump(config_data, f, allow_unicode=True, indent=2, sort_keys=False)
            
            info(f"Configuration saved by category to: {save_path}")
            return True
        except Exception as e:
            error_msg = f"Failed to save configuration: {e}"
            handle_error(OCRConfigError(error_msg, context={"file_path": filepath}))
            return False

    @monitor_metrics("config_load", include_labels=True)
    @with_error_handling(error_code="CONFIG_LOAD_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    def load(self, filepath: Optional[str] = None) -> bool:
        """加载配置文件"""
        try:
            load_path = filepath or self._config_file
            if os.path.exists(load_path):
                with open(load_path, 'r', encoding='utf-8') as f:
                    if load_path.endswith('.yaml'):
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                
                # 处理分类格式的配置数据
                flat_config = {}
                if isinstance(config_data, dict):
                    # 检查是否是分类格式（包含 system 或 external 键）
                    if "system" in config_data or "external" in config_data:
                        # 分类格式
                        for category, configs in config_data.items():
                            if isinstance(configs, dict):
                                flat_config.update(configs)
                    else:
                        # 扁平格式
                        flat_config = config_data
                
                # 更新配置项
                for key, value in flat_config.items():
                    if key not in self._config_items:
                        self._config_items[key] = ConfigItem(key, value, value, type(value), "")
                    else:
                        self._config_items[key].current_value = value
                        self._config_sources[key] = "file"
                
                info(f"Configuration loaded from {load_path}")
                return True
            else:
                warning(f"Configuration file {load_path} does not exist")
                return False
        except Exception as e:
            error(f"Failed to load configuration: {e}")
            return False
    
    def _register_default_configs(self) -> None:
        """Register default configuration items (marked as system source)"""
        try:
            # Application configuration
            self.register_config_with_source("app_name", "Infrastructure Framework", str, "Application name", plugin_name="system")
            self.register_config_with_source("app_version", "1.0.0", str, "Application version", plugin_name="system")
            self.register_config_with_source("debug_mode", False, bool, "Debug mode switch", plugin_name="system")
            
            # Logging configuration
            self.register_config_with_source("log_level", "DEBUG", str, "Log level (DEBUG/INFO/WARNING/ERROR)", 
                                           validator=self._validate_log_level, plugin_name="system")
            self.register_config_with_source("log_console_enabled", True, bool, "Enable console logging", plugin_name="system")
            self.register_config_with_source("log_file_enabled", True, bool, "Enable file logging", plugin_name="system")
            self.register_config_with_source("log_max_size_mb", 100, int, "Maximum log file size (MB)", plugin_name="system")
            self.register_config_with_source("log_backup_count", 7, int, "Number of log file backups", plugin_name="system")
            
            # Path configuration
            self.register_config_with_source("data_dir", "data", str, "Data directory path", plugin_name="system")
            self.register_config_with_source("output_dir", "output", str, "Output directory path", plugin_name="system")
            self.register_config_with_source("temp_dir", "temp", str, "Temporary directory path", plugin_name="system")
            
            # System behavior configuration
            self.register_config_with_source("auto_save_config", True, bool, "Automatically save configuration", plugin_name="system")
        except Exception as e:
            error_msg = f"Failed to register default configuration items: {e}"
            handle_error(OCRConfigError(error_msg))
            raise
    
    def _publish_config_registration_event(self) -> None:
        """发布配置项注册事件，允许外部模块注册自定义配置项"""
        try:
            from core.event.event_bus import EventBus
            from core.event.events.scheduler_events import ConfigItemRegisteredEvent
            
            event_bus = EventBus()
            config_register_event = ConfigItemRegisteredEvent(self, plugin_name="external")
            event_bus.publish(config_register_event)
            
            debug("Published configuration item registration event, allowing external modules to register custom configuration items")
        except ImportError:
            # 如果事件系统不可用，跳过事件发布（保持向后兼容）
            debug("Event system unavailable, skipping configuration item registration event publication")
        except Exception as e:
            error(f"Failed to publish configuration item registration event: {e}")
            # 不抛出异常，确保配置管理器仍能正常初始化
            pass
    
    def _register_app_lifecycle_listeners(self) -> None:
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
            
            debug("Configuration manager has registered application lifecycle event listeners")
        except ImportError:
            # 如果事件系统不可用，跳过事件监听器注册
            debug("Event system unavailable, skipping configuration manager lifecycle event listener registration")
        except Exception as e:
            error(f"Failed to register configuration manager lifecycle event listener: {e}")
            # 不抛出异常，确保配置管理器仍能正常初始化
            pass
    
    def _on_application_lifecycle_event(self, event: Any) -> bool:
        """处理应用程序生命周期事件"""
        try:
            if hasattr(event, 'lifecycle_stage'):
                if event.lifecycle_stage == "stopping":
                    # 应用程序正在停止，保存当前配置
                    self.save_to_file()
                    info("Configuration manager: application stopping, current configuration saved")
                elif event.lifecycle_stage == "stopped":
                    # 应用程序已停止，清理资源
                    self._config_items.clear()
                    self._config_sources.clear()
                    self._listeners.clear()
                    self._key_listeners.clear()
                    info("Configuration manager: resource cleanup completed")
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
                config_data: Dict[str, Any] = yaml.safe_load(f) or {}
            
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
            error(f"Failed to load existing configuration file: {e}")
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
        Register a configuration item with specified source
        
        Args:
            key: Configuration item key name
            default_value: Default value
            value_type: Value type
            description: Description information
            validator: Custom validator function
            plugin_name: Plugin name (source identifier), None means system default
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
            error_msg = f"Failed to register configuration item '{key}': {e}"
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
        Register configuration item (compatible with old interface, default source is external)
        
        Args:
            key: Configuration item key name
            default_value: Default value
            value_type: Value type
            description: Description information
            validator: Custom validator function
        """
        self.register_config_with_source(key, default_value, value_type, description, validator, "external")
    
    def get_config_source(self, key: str) -> Optional[str]:
        """
        Get the source of a configuration item
        
        Args:
            key: Configuration item key name
            
        Returns:
            Configuration item source ("system", "external", or plugin name)
        """
        return self._config_sources.get(key)
    
    def get_all_configs_by_source(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configuration items categorized by source
        
        Returns:
            Configuration dictionary categorized by source
        """
        configs_by_source: Dict[str, Dict[str, Any]] = {}
        for key, config_item in self._config_items.items():
            source = self._config_sources.get(key, "unknown")
            if source not in configs_by_source:
                configs_by_source[source] = {}
            configs_by_source[source][key] = config_item.current_value
        return configs_by_source
    
    @monitor_metrics("config_set", include_labels=True)
    @with_error_handling(error_code="CONFIG_SET_ERROR", default_return=False)
    @with_logging(level="debug", include_args=True, measure_time=True)
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
                error_msg = f"Configuration item '{key}' not registered, cannot set"
                handle_error(OCRConfigError(error_msg, context={"key": key, "attempted_value": value}))
                return False
            
            config_item = self._config_items[key]
            if not config_item.validate(value):
                error_msg = f"Value '{value}' for configuration item '{key}' failed validation"
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
            
            debug(f"Configuration item '{key}' updated: {old_value} -> {value}")
            return True
        except Exception as e:
            error_msg = f"Failed to set configuration item '{key}': {e}"
            handle_error(OCRConfigError(error_msg, context={"key": key, "value": value}))
            return False
    
    @monitor_metrics("config_get", include_labels=True)
    @with_error_handling(error_code="CONFIG_GET_ERROR", default_return=None)
    @with_logging(level="debug", include_args=True)
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration item value
        
        Args:
            key: Configuration item key name
            default: Default value
            
        Returns:
            Configuration item value
        """
        if key in self._config_items:
            return self._config_items[key].current_value
        return default
    
    @monitor_metrics("config_has", include_labels=True)
    @with_error_handling(error_code="CONFIG_HAS_ERROR", default_return=False)
    @with_logging(level="debug", include_args=True)
    def has_config(self, key: str) -> bool:
        """
        Check if configuration item exists
        
        Args:
            key: Configuration item key name
            
        Returns:
            Whether it exists
        """
        return key in self._config_items
    
    @monitor_metrics("config_get_all", include_labels=True)
    @with_error_handling(error_code="CONFIG_GET_ALL_ERROR", default_return={})
    @with_logging(level="debug", measure_time=True)
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置项"""
        return {key: item.current_value for key, item in self._config_items.items()}
    
    @monitor_metrics("config_add_listener", include_labels=True)
    @with_error_handling(error_code="CONFIG_ADD_LISTENER_ERROR")
    @with_logging(level="debug", include_args=True)
    def add_listener(self, listener: Callable[[str, Any, Any], None]) -> None:
        """
        Add configuration change listener
        
        Args:
            listener: Listener function that receives (key name, old value, new value) parameters
        """
        self._listeners.append(listener)
    
    @monitor_metrics("config_add_key_listener", include_labels=True)
    @with_error_handling(error_code="CONFIG_ADD_KEY_LISTENER_ERROR")
    @with_logging(level="debug", include_args=True)
    def add_key_listener(self, key: str, listener: Callable[[str, Any, Any], None]) -> None:
        """
        Add listener for specific configuration item
        
        Args:
            key: Configuration item key name
            listener: Listener function that receives (key name, old value, new value) parameters
        """
        if key not in self._key_listeners:
            self._key_listeners[key] = []
        self._key_listeners[key].append(listener)
    
    @monitor_metrics("config_remove_listener", include_labels=True)
    @with_error_handling(error_code="CONFIG_REMOVE_LISTENER_ERROR", default_return=False)
    @with_logging(level="debug", include_args=True)
    def remove_listener(self, listener: Callable[[str, Any, Any], None]) -> bool:
        """
        Remove configuration change listener
        
        Args:
            listener: Listener function
            
        Returns:
            Whether removal was successful
        """
        try:
            self._listeners.remove(listener)
            return True
        except ValueError:
            return False
    
    @monitor_metrics("config_remove_key_listener", include_labels=True)
    @with_error_handling(error_code="CONFIG_REMOVE_KEY_LISTENER_ERROR", default_return=False)
    @with_logging(level="debug", include_args=True)
    def remove_key_listener(self, key: str, listener: Callable[[str, Any, Any], None]) -> bool:
        """
        Remove listener for specific configuration item
        
        Args:
            key: Configuration item key name
            listener: Listener function
            
        Returns:
            Whether removal was successful
        """
        if key in self._key_listeners:
            try:
                self._key_listeners[key].remove(listener)
                return True
            except ValueError:
                return False
        return False
    
    @monitor_metrics("config_validate_all", include_labels=True)
    @with_error_handling(error_code="CONFIG_VALIDATE_ALL_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    def validate_all_configs(self) -> bool:
        """
        Validate all configuration items
        
        Returns:
            Whether all validations passed
        """
        for config_item in self._config_items.values():
            if not config_item.validate(config_item.current_value):
                return False
        return True
    
    @monitor_metrics("config_reset_all", include_labels=True)
    @with_error_handling(error_code="CONFIG_RESET_ALL_ERROR")
    @with_logging(level="info", measure_time=True)
    def reset_to_defaults(self) -> None:
        """重置所有配置项为默认值"""
        for config_item in self._config_items.values():
            config_item.current_value = config_item.default_value

    def reset_config(self, key: str) -> bool:
        """
        Reset single configuration item to default value
        
        Args:
            key: Configuration item key name
            
        Returns:
            Whether reset was successful
        """
        try:
            if key not in self._config_items:
                error_msg = f"Configuration item '{key}' not registered, cannot reset"
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
            
            debug(f"Configuration item '{key}' reset to default value: {old_value} -> {config_item.default_value}")
            return True
        except Exception as e:
            error_msg = f"Failed to reset configuration item '{key}': {e}"
            handle_error(OCRConfigError(error_msg, context={"key": key}))
            return False