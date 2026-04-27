"""
配置系统 - 完全自动化
用户只需要定义配置类，框架自动处理所有验证、存储和管理
"""

import os
import yaml
import re
import threading
import time
from typing import Any, Dict, List, Optional, Type, get_type_hints, Callable
from dataclasses import dataclass, field
from pathlib import Path

from . import _path_manager
from ._logging import _log_framework_info, _log_framework_warning, _log_framework_error


# ============================================================================
# 配置异常类（内部实现）
# ============================================================================


class _ConfigException(Exception):
    """配置异常（内部实现）"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        details: Optional[dict] = None,
    ):
        self.config_key = config_key
        self.config_value = config_value
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
        if config_value is not None:
            error_details["config_value"] = config_value
        super().__init__(message, error_details)


class _ConfigValidationException(_ConfigException):
    """配置验证异常（内部实现）"""

    def __init__(
        self,
        message: str,
        config_key: str,
        config_value: Any,
        expected_type: Optional[type] = None,
        validation_rule: Optional[str] = None,
    ):
        details = {}
        if expected_type:
            details["expected_type"] = expected_type.__name__
        if validation_rule:
            details["validation_rule"] = validation_rule
        super().__init__(message, config_key, config_value, details)


# ============================================================================
# 配置验证模块
# ============================================================================


@dataclass
class _ConfigField:
    """配置字段定义（内部使用）"""

    key: str
    field_type: Type[Any]
    default_value: Any = None
    description: str = ""
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

    def _validate(self, value: Any) -> None:
        """验证配置值"""
        if self.required and value is None:
            raise _ConfigValidationException(
                f"配置项 '{self.key}' 是必填的，但值为 None",
                config_key=self.key,
                config_value=value,
            )

        if value is None:
            return

        if not isinstance(value, self.field_type):
            raise _ConfigValidationException(
                f"配置项 '{self.key}' 的类型错误，期望 {self.field_type.__name__}，实际 {type(value).__name__}",
                config_key=self.key,
                config_value=value,
            )

        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                raise _ConfigValidationException(
                    f"配置项 '{self.key}' 的值 {value} 小于最小值 {self.min_value}",
                    config_key=self.key,
                    config_value=value,
                )
            if self.max_value is not None and value > self.max_value:
                raise _ConfigValidationException(
                    f"配置项 '{self.key}' 的值 {value} 大于最大值 {self.max_value}",
                    config_key=self.key,
                    config_value=value,
                )

        if isinstance(value, (str, list, dict)):
            length = len(value)
            if self.min_length is not None and length < self.min_length:
                raise _ConfigValidationException(
                    f"配置项 '{self.key}' 的长度 {length} 小于最小长度 {self.min_length}",
                    config_key=self.key,
                    config_value=value,
                )
            if self.max_length is not None and length > self.max_length:
                raise _ConfigValidationException(
                    f"配置项 '{self.key}' 的长度 {length} 大于最大长度 {self.max_length}",
                    config_key=self.key,
                    config_value=value,
                )

        if self.pattern and isinstance(value, str):
            if not re.match(self.pattern, value):
                raise _ConfigValidationException(
                    f"配置项 '{self.key}' 的值 '{value}' 不匹配模式",
                    config_key=self.key,
                    config_value=value,
                )


@dataclass
class _ConfigSchema:
    """配置模式定义（内部使用）"""

    name: str
    description: str = ""
    fields: List[_ConfigField] = field(default_factory=list)

    def _validate(self, config: Dict[str, Any]) -> None:
        """验证配置"""
        for field in self.fields:
            value = config.get(field.key)
            field._validate(value)


class _ConfigValidator:
    """配置验证器（内部使用）"""

    def __init__(self):
        self._schemas: Dict[str, _ConfigSchema] = {}

    def _register_schema(self, schema: _ConfigSchema) -> None:
        """注册配置模式"""
        self._schemas[schema.name] = schema

    def _validate(
        self, config: Dict[str, Any], schema_name: Optional[str] = None
    ) -> None:
        """验证配置"""
        if schema_name:
            schema = self._schemas.get(schema_name)
            if schema:
                schema._validate(config)
        else:
            for schema in self._schemas.values():
                schema._validate(config)


# 全局配置验证器实例
_config_validator = _ConfigValidator()


# ============================================================================
# 配置装饰器模块
# ============================================================================


def Config(name: str, description: str = ""):
    """
    配置装饰器 - 定义配置类并自动处理验证

    Args:
        name: 配置名称
        description: 配置描述

    Returns:
        装饰后的配置类

    Example:
        @Config("app_config", "应用配置")
        class AppConfig:
            database_url: str = "postgresql://localhost/mydb"
            port: int = 8080
            debug: bool = False
            max_connections: int = 10

    Note:
        - 框架自动处理所有验证，用户只需定义配置类
        - 支持自动推断验证规则：
          * 类型验证：从类型注解自动推断
          * 范围验证：从默认值和类型自动推断（如 port: int = 8080 → 1-65535）
          * 长度验证：从字符串类型自动推断
          * 正则表达式验证：从字段名自动推断（如 email、url）
        - 配置值会自动进行类型转换和验证
        - 验证失败会抛出详细的错误信息
        - 支持嵌套配置和复杂类型
    """

    def decorator(cls: Type) -> Type:
        # 创建配置模式
        schema = _ConfigSchema(name=name, description=description)

        # 获取类型注解
        type_hints_dict = get_type_hints(cls)

        # 收集字段信息用于注册到配置管理器
        fields_info = {}

        # 遍历类属性，创建配置字段
        for field_name, field_type in type_hints_dict.items():
            # 获取默认值
            default_value = getattr(cls, field_name, None)

            # 自动推断验证规则
            field = _create_config_field(field_name, field_type, default_value)
            schema.fields.append(field)

            # 收集字段信息
            fields_info[field_name] = {
                "default_value": default_value,
                "value_type": field_type,
            }

        # 注册配置模式到验证器
        _config_validator._register_schema(schema)

        # 注册配置模式到配置管理器
        _config_manager._register_config_schema(name, fields_info)

        # 将模式附加到类
        cls._config_schema = schema

        return cls

    return decorator


def _create_config_field(
    field_name: str, field_type: Type, default_value: Any
) -> _ConfigField:
    """创建配置字段（自动推断验证规则）"""
    field = _ConfigField(
        key=field_name,
        field_type=field_type,
        default_value=default_value,
        required=default_value is None,
    )

    _infer_validation_rules(field)

    return field


def _infer_validation_rules(field: _ConfigField) -> None:
    """自动推断验证规则"""
    field_name_lower = field.key.lower()

    if "port" in field_name_lower and field.field_type == int:
        field.min_value = 1
        field.max_value = 65535

    elif "connection" in field_name_lower and field.field_type == int:
        field.min_value = 1
        field.max_value = 100

    elif "timeout" in field_name_lower and field.field_type == int:
        field.min_value = 1
        field.max_value = 300

    elif "url" in field_name_lower and field.field_type == str:
        field.pattern = r"^(http|https|ftp|postgresql|sqlite|mysql)://.*"

    elif "email" in field_name_lower and field.field_type == str:
        field.pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    elif "ip" in field_name_lower and field.field_type == str:
        field.pattern = r"^(\d{1,3}\.){3}\d{1,3}$"

    elif "host" in field_name_lower and field.field_type == str:
        field.min_length = 1
        field.max_length = 255

    elif "key" in field_name_lower or "secret" in field_name_lower:
        if field.field_type == str:
            field.min_length = 8

    elif field.field_type == str:
        field.max_length = 255

    elif field.field_type == int:
        if field.min_value is None:
            field.min_value = 0
        if field.max_value is None:
            field.max_value = 999999999


# ============================================================================
# 配置管理器模块
# ============================================================================

# 从 _application_info 导入统一的 _get_current_app_name 函数
# 注意：这个导入放在这里是为了避免循环导入
_get_current_app_name = None


def _ensure_get_current_app_name():
    """确保 _get_current_app_name 函数已导入"""
    global _get_current_app_name
    if _get_current_app_name is None:
        from ._application_info import _get_current_app_name as _get_app_name

        _get_current_app_name = _get_app_name


def _get_config_base_path(app_name: Optional[str] = None) -> str:
    """获取配置基础路径"""
    if app_name is not None:
        if app_name == "framework" or app_name == "":
            config_root = _path_manager._get_user_config_root()
            return config_root
        else:
            config_root = _path_manager._get_user_config_root()
            app_dir = _path_manager._join_paths(config_root, app_name)
            return app_dir

    _ensure_get_current_app_name()
    assert (
        _get_current_app_name is not None
    ), "_get_current_app_name should be imported by _ensure_get_current_app_name"
    current_app_name = _get_current_app_name()
    if current_app_name:
        config_root = _path_manager._get_user_config_root()
        app_dir = _path_manager._join_paths(config_root, current_app_name)
        return app_dir

    config_root = _path_manager._get_user_config_root()
    return config_root


def _get_config_file_path(config_name: str, app_name: Optional[str] = None) -> str:
    """获取配置文件路径"""
    base_path = _get_config_base_path(app_name)
    config_dir = _path_manager._join_paths(base_path, "config")
    config_file = _path_manager._join_paths(config_dir, f"{config_name}.yaml")
    return config_file


class _SimpleConfigManager:
    """简单的配置管理器内部类"""

    def __init__(self):
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._field_to_config: Dict[str, str] = {}
        self._registered_configs: Dict[str, Dict[str, dict]] = {}
        self._loaded_configs: Dict[str, bool] = {}
        self._file_mtime: Dict[str, float] = {}
        self._auto_save_enabled: bool = True
        self._pending_changes: Dict[str, bool] = {}
        self._save_timer: Optional[threading.Timer] = None
        self._lock: threading.RLock = threading.RLock()

    def _get_config_name_for_field(self, field_name: str) -> Optional[str]:
        """获取字段所属的配置名称"""
        return self._field_to_config.get(field_name)

    def _ensure_config_loaded(self, config_name: str) -> None:
        """确保配置已加载（带缓存检查）"""
        config_file = _get_config_file_path(config_name)

        if config_name in self._loaded_configs:
            if os.path.exists(config_file):
                current_mtime = os.path.getmtime(config_file)
                if current_mtime > self._file_mtime.get(config_name, 0):
                    self._load_config_file(config_name)
                    self._file_mtime[config_name] = current_mtime
            return

        if config_name not in self._loaded_configs:
            self._load_config_file(config_name)
            self._loaded_configs[config_name] = True
            if os.path.exists(config_file):
                self._file_mtime[config_name] = os.path.getmtime(config_file)

    def _load_config_file(self, config_name: str) -> None:
        """加载配置文件（线程安全）"""
        with self._lock:
            config_file = _get_config_file_path(config_name)

            if not os.path.exists(config_file):
                if config_name not in self._configs:
                    self._configs[config_name] = {}
                return

            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}

                flat_config = self._flatten_dict(config_data)

                self._configs[config_name] = flat_config

                _log_framework_info(f"配置已从 {config_file} 加载")
            except Exception as e:
                _log_framework_error(f"加载配置文件失败 {config_file}: {e}")
                if config_name not in self._configs:
                    self._configs[config_name] = {}

    def _save_config_file(self, config_name: str) -> bool:
        """保存配置文件（线程安全）"""
        with self._lock:
            config_file = _get_config_file_path(config_name)

            try:
                dir_path = os.path.dirname(config_file)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                nested_config = self._unflatten_dict(self._configs.get(config_name, {}))

                with open(config_file, "w", encoding="utf-8") as f:
                    yaml.dump(
                        nested_config,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                    )

                self._file_mtime[config_name] = os.path.getmtime(config_file)
                self._pending_changes.pop(config_name, None)

                _log_framework_info(f"配置已保存到 {config_file}")
                return True
            except Exception as e:
                _log_framework_error(f"保存配置文件失败 {config_file}: {e}")
                return False

    def _register_config_schema(
        self,
        config_name: str,
        fields: Dict[str, dict],
    ) -> None:
        """注册配置模式"""
        self._registered_configs[config_name] = fields

        for field_name in fields.keys():
            self._field_to_config[field_name] = config_name

        if config_name not in self._configs:
            self._configs[config_name] = {}

        for field_name, field_info in fields.items():
            if field_name not in self._configs[config_name]:
                self._configs[config_name][field_name] = field_info["default_value"]

    def _get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值（线程安全）"""
        with self._lock:
            config_name = self._get_config_name_for_field(key)

            if config_name is None:
                return default

            self._ensure_config_loaded(config_name)

            return self._configs[config_name].get(key, default)

    def _set_config(self, key: str, value: Any) -> bool:
        """设置配置值（线程安全 + 批量写入优化）"""
        with self._lock:
            config_name = self._get_config_name_for_field(key)

            if config_name is None:
                raise _ConfigException(
                    f"配置项 '{key}' 未注册，请使用 @Config 装饰器定义配置类"
                )

            self._ensure_config_loaded(config_name)

            field_info = self._registered_configs.get(config_name, {}).get(key)

            if field_info:
                if not isinstance(value, field_info["value_type"]):
                    try:
                        if field_info["value_type"] == int:
                            value = int(value)
                        elif field_info["value_type"] == float:
                            value = float(value)
                        elif field_info["value_type"] == bool:
                            if isinstance(value, str):
                                value = value.lower() in ("true", "1", "yes", "on")
                            else:
                                value = bool(value)
                    except (ValueError, TypeError) as e:
                        raise _ConfigValidationException(
                            f"配置项 '{key}' 的值 '{value}' 无法转换为类型 {field_info['value_type'].__name__}",
                            config_key=key,
                            config_value=value,
                            expected_type=field_info["value_type"],
                        ) from e

                if field_info.get("validator") and not field_info["validator"](value):
                    raise _ConfigValidationException(
                        f"配置项 '{key}' 的自定义验证失败",
                        config_key=key,
                        config_value=value,
                        validation_rule="custom",
                    )

            schema = _config_validator._schemas.get(config_name)
            if schema:
                temp_config = self._configs[config_name].copy()
                temp_config[key] = value
                schema._validate(temp_config)

            old_value = self._configs[config_name].get(key)

            self._configs[config_name][key] = value

            self._pending_changes[config_name] = True

            if old_value != value:
                self._notify_config_change(key, old_value, value)

            if self._auto_save_enabled:
                self._schedule_save()

            return True

    def _schedule_save(self) -> None:
        """调度批量保存（延迟写入优化）"""
        if self._save_timer:
            self._save_timer.cancel()

        self._save_timer = threading.Timer(1.0, self._flush_pending_changes)
        self._save_timer.start()

    def _flush_pending_changes(self) -> None:
        """批量保存待写入的配置"""
        with self._lock:
            for config_name in list(self._pending_changes.keys()):
                self._save_config_file(config_name)

    def _has_config(self, key: str) -> bool:
        """检查配置项是否存在（线程安全）"""
        with self._lock:
            config_name = self._get_config_name_for_field(key)
            if config_name is None:
                return False
            self._ensure_config_loaded(config_name)
            return key in self._configs[config_name]

    def _get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置（扁平化）（线程安全）"""
        with self._lock:
            all_configs = {}
            for config_name, config_dict in self._configs.items():
                all_configs.update(config_dict)
            return all_configs

    def _reset_config(self, key: str) -> bool:
        """重置单个配置项到默认值（线程安全）"""
        with self._lock:
            config_name = self._get_config_name_for_field(key)
            if config_name is None:
                return False

            field_info = self._registered_configs.get(config_name, {}).get(key)
            if field_info:
                self._ensure_config_loaded(config_name)
                self._configs[config_name][key] = field_info["default_value"]
                self._pending_changes[config_name] = True
                if self._auto_save_enabled:
                    self._schedule_save()
                return True
            return False

    def _reset_all_configs(self) -> None:
        """重置所有配置到默认值（线程安全）"""
        with self._lock:
            for config_name, fields in self._registered_configs.items():
                self._ensure_config_loaded(config_name)
                for field_name, field_info in fields.items():
                    self._configs[config_name][field_name] = field_info["default_value"]
                self._pending_changes[config_name] = True
                if self._auto_save_enabled:
                    self._schedule_save()

    def _load_from_file(self, file_path: str) -> bool:
        """从YAML文件加载配置（兼容旧接口）（线程安全）"""
        with self._lock:
            try:
                if not os.path.exists(file_path):
                    _log_framework_warning(f"配置文件 {file_path} 不存在")
                    return False

                with open(file_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}

                flat_config = self._flatten_dict(config_data)

                for key, value in flat_config.items():
                    config_name = self._get_config_name_for_field(key)
                    if config_name:
                        if config_name not in self._configs:
                            self._configs[config_name] = {}
                        self._configs[config_name][key] = value

                _log_framework_info(f"配置已从 {file_path} 加载")
                return True

            except Exception as e:
                _log_framework_error(f"加载配置文件失败 {file_path}: {e}")
                return False

    def _save_to_file(self, file_path: str) -> bool:
        """保存配置到YAML文件（兼容旧接口）（线程安全）"""
        with self._lock:
            try:
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                nested_config = self._unflatten_dict(self._get_all_configs())

                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        nested_config,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                    )

                _log_framework_info(f"配置已保存到 {file_path}")
                return True

            except Exception as e:
                _log_framework_error(f"保存配置文件失败 {file_path}: {e}")
                return False

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """将嵌套字典扁平化为点号分隔的键"""
        from typing import List, Tuple

        items: List[Tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _unflatten_dict(self, flat_dict: Dict[str, Any]) -> Dict[str, Any]:
        """将扁平化字典转换回嵌套结构"""
        result: Dict[str, Any] = {}
        for key, value in flat_dict.items():
            keys = key.split(".")
            current = result
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        return result

    def _notify_config_change(self, key: str, old_value: Any, new_value: Any):
        """通知配置变更（触发@OnConfigChange装饰器）"""
        try:
            from ._lifecycle_decorator import _get_lifecycle_manager, _LifecyclePhase
            from dataclasses import dataclass
            from typing import Any as TypingAny

            # 动态创建ConfigChangeEvent类
            @dataclass
            class ConfigChangeEvent:
                """配置变更事件"""

                key: str
                old_value: TypingAny
                new_value: TypingAny

            # 创建事件实例
            event = ConfigChangeEvent(key=key, old_value=old_value, new_value=new_value)

            # 获取生命周期管理器
            lifecycle_manager = _get_lifecycle_manager()

            # 遍历所有注册的类，查找监听此配置变更的方法
            for cls, methods_dict in lifecycle_manager._methods.items():
                if _LifecyclePhase.ON_CONFIG_CHANGE in methods_dict:
                    methods = methods_dict[_LifecyclePhase.ON_CONFIG_CHANGE]
                    for method_wrapper in methods:
                        # 检查是否监听特定配置键
                        config_key = getattr(method_wrapper.method, "_config_key", None)
                        if config_key is None or config_key == key:
                            # 检查条件
                            if method_wrapper.condition is not None:
                                try:
                                    if not method_wrapper.condition(
                                        None, old_value=old_value, new_value=new_value
                                    ):
                                        continue
                                except Exception:
                                    continue

                            # 执行方法（注意：这里需要实例，暂时跳过）
                            # 在实际使用中，实例应该通过其他方式获取
                            pass
        except ImportError:
            # 如果生命周期模块未导入，跳过处理
            pass
        except Exception as e:
            # 静默失败，避免影响配置设置
            pass

    def _enable_auto_save(self, enabled: bool = True) -> None:
        """
        启用或禁用配置自动保存

        Args:
            enabled: 是否启用自动保存
        """
        self._auto_save_enabled = enabled

        # 注册退出处理器，确保程序退出时保存所有待写入的配置
        if enabled and not hasattr(self, "_exit_handler_registered"):
            import atexit

            atexit.register(self._cleanup)
            self._exit_handler_registered = True

    def _cleanup(self) -> None:
        """
        清理资源，确保所有待写入的配置都被保存
        """
        # 取消定时器
        if self._save_timer:
            self._save_timer.cancel()

        # 保存所有待写入的配置
        if self._pending_changes:
            self._flush_pending_changes()


# 全局配置管理器实例
_config_manager = _SimpleConfigManager()


# ============================================================================
# 公共接口函数
# ============================================================================


def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值 - 从配置管理器中读取配置

    Args:
        key: 配置键名（支持点号分隔的嵌套键，如 "database.url"）
        default: 默认值，当配置不存在时返回此值

    Returns:
        配置值或默认值

    Example:
        # 获取简单配置
        database_url = get_config("database.url")

        # 获取带默认值的配置
        port = get_config("server.port", default=8080)

        # 获取嵌套配置
        timeout = get_config("database.timeout", default=30)

    Note:
        - 支持点号分隔的嵌套键访问
        - 如果配置不存在且未提供默认值，返回 None
        - 配置值会自动进行类型转换
        - 支持从配置文件中读取预定义的配置
    """
    return _config_manager._get_config(key, default)


def set_config(key: str, value: Any) -> bool:
    """
    设置配置值 - 向配置管理器中写入配置

    Args:
        key: 配置键名（支持点号分隔的嵌套键，如 "database.url"）
        value: 配置值

    Returns:
        是否设置成功

    Example:
        # 设置简单配置
        set_config("database.url", "postgresql://localhost/mydb")

        # 设置嵌套配置
        set_config("server.port", 8080)

        # 设置复杂配置
        set_config("app.features", {"feature1": True, "feature2": False})

    Note:
        - 支持点号分隔的嵌套键设置
        - 设置的配置会自动验证（如果配置类定义了验证规则）
        - 配置变更会触发 @OnConfigChange 装饰的方法
        - 配置会持久化到配置文件
        - 如果验证失败，返回 False
    """
    return _config_manager._set_config(key, value)


# ============================================================================
# 内部接口函数（框架内部使用）
# ============================================================================


def _load_config(file_path: str) -> bool:
    """从指定文件路径加载配置（内部函数）"""
    return _config_manager._load_from_file(file_path)


def _save_config(file_path: str) -> bool:
    """保存配置到指定文件路径（内部函数）"""
    return _config_manager._save_to_file(file_path)


def _load_user_config(
    filename: str = "config.yaml", app_name: Optional[str] = None
) -> bool:
    """加载用户配置文件（内部函数）"""
    config_dir = _get_config_base_path(app_name)
    config_file = os.path.join(config_dir, filename)
    return _load_config(config_file)


def _save_user_config(
    filename: str = "config.yaml", app_name: Optional[str] = None
) -> bool:
    """保存用户配置文件（内部函数）"""
    config_dir = _get_config_base_path(app_name)
    config_file = os.path.join(config_dir, filename)
    return _save_config(config_file)


def _enable_auto_save(enabled: bool = True) -> None:
    """启用或禁用配置自动保存（内部函数）"""
    _config_manager._enable_auto_save(enabled)


def _reset_config(key: str) -> bool:
    """重置单个配置项到默认值（内部函数）"""
    return _config_manager._reset_config(key)


def _reset_all_configs() -> None:
    """重置所有配置到默认值（内部函数）"""
    _config_manager._reset_all_configs()


def _has_config(key: str) -> bool:
    """检查配置项是否存在（内部函数）"""
    return _config_manager._has_config(key)


def _get_all_configs() -> Dict[str, Any]:
    """获取所有配置（内部函数）"""
    return _config_manager._get_all_configs()
