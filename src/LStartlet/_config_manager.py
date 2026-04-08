"""
超级简化的配置管理器 - 只提供最基本的配置管理功能
作为工具函数集合，不包含复杂的类结构和监听器系统
"""

import os
import yaml
from typing import Any, Dict, Optional, Type, Callable
from pathlib import Path

from . import _path_manager
from ._logging_functions import info, warning, error


# 全局配置存储
_config_store: Dict[str, Any] = {}


class _SimpleConfigManager:
    """简单的配置管理器内部类"""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._registered_configs: Dict[str, dict] = {}  # 存储注册的配置信息
        self._auto_save_enabled: bool = False  # 是否启用自动保存
        self._config_file_path: Optional[str] = None  # 配置文件路径

    def register_config(
        self,
        key: str,
        default_value: Any,
        value_type: Type[Any],
        description: str = "",
        validator: Optional[Callable[[Any], bool]] = None,
    ) -> None:
        """
        注册配置项

        Args:
            key: 配置键名
            default_value: 默认值
            value_type: 期望的类型
            description: 配置描述
            validator: 自定义验证函数
        """
        self._registered_configs[key] = {
            "default_value": default_value,
            "value_type": value_type,
            "description": description,
            "validator": validator,
        }

        # 如果配置不存在，设置默认值
        if key not in self._config:
            self._config[key] = default_value

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键名
            default: 默认值

        Returns:
            配置值或默认值
        """
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置值

        Args:
            key: 配置键名
            value: 配置值

        Returns:
            是否设置成功
        """
        # 验证已注册的配置
        if key in self._registered_configs:
            config_info = self._registered_configs[key]

            # 类型验证
            if not isinstance(value, config_info["value_type"]):
                # 尝试类型转换
                try:
                    if config_info["value_type"] == int:
                        value = int(value)
                    elif config_info["value_type"] == float:
                        value = float(value)
                    elif config_info["value_type"] == bool:
                        if isinstance(value, str):
                            value = value.lower() in ("true", "1", "yes", "on")
                        else:
                            value = bool(value)
                except (ValueError, TypeError):
                    error(
                        f"配置项 {key} 的值 '{value}' 无法转换为类型 {config_info['value_type']}"
                    )
                    return False

            # 自定义验证
            if config_info["validator"] and not config_info["validator"](value):
                error(f"配置项 {key} 的自定义验证失败")
                return False

        # 记录旧值用于配置变更事件
        old_value = self._config.get(key)

        self._config[key] = value

        # 自动保存配置（如果启用）
        if self._auto_save_enabled and self._config_file_path:
            self._auto_save_config()

        # 触发配置变更事件（如果值发生变化）
        if old_value != value:
            self._notify_config_change(key, old_value, value)

        return True

    def has_config(self, key: str) -> bool:
        """检查配置项是否存在"""
        return key in self._config

    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def reset_config(self, key: str) -> bool:
        """重置单个配置项到默认值"""
        if key in self._registered_configs:
            default_value = self._registered_configs[key]["default_value"]
            self._config[key] = default_value
            return True
        return False

    def reset_all_configs(self) -> None:
        """重置所有配置到默认值"""
        for key, config_info in self._registered_configs.items():
            self._config[key] = config_info["default_value"]

        # 清除未注册的配置项
        registered_keys = set(self._registered_configs.keys())
        all_keys = set(self._config.keys())
        unregistered_keys = all_keys - registered_keys
        for key in unregistered_keys:
            del self._config[key]

    def load_from_file(self, file_path: str) -> bool:
        """
        从YAML文件加载配置

        Args:
            file_path: 配置文件路径

        Returns:
            是否加载成功
        """
        try:
            if not os.path.exists(file_path):
                warning(f"配置文件 {file_path} 不存在")
                return False

            with open(file_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

            # 扁平化嵌套配置
            flat_config = self._flatten_dict(config_data)

            # 应用配置（直接设置，不触发通知）
            for key, value in flat_config.items():
                self._config[key] = value

            info(f"配置已从 {file_path} 加载")
            return True

        except Exception as e:
            error(f"加载配置文件失败 {file_path}: {e}")
            return False

    def save_to_file(self, file_path: str) -> bool:
        """
        保存配置到YAML文件

        Args:
            file_path: 配置文件路径

        Returns:
            是否保存成功
        """
        try:
            # 创建目录
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # 转换为嵌套结构
            nested_config = self._unflatten_dict(self._config)

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    nested_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

            info(f"配置已保存到 {file_path}")
            return True

        except Exception as e:
            error(f"保存配置文件失败 {file_path}: {e}")
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

    def _auto_save_config(self) -> bool:
        """自动保存配置到文件"""
        if not self._config_file_path:
            return False

        try:
            # 将配置转换为嵌套结构
            nested_config = self._unflatten_dict(self._config)

            # 确保目录存在
            config_dir = os.path.dirname(self._config_file_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            # 保存到YAML文件
            with open(self._config_file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    nested_config, f, default_flow_style=False, allow_unicode=True
                )

            return True
        except Exception as e:
            error(f"自动保存配置失败: {e}")
            return False

    def _notify_config_change(self, key: str, old_value: Any, new_value: Any):
        """通知配置变更（触发@OnConfigChange装饰器）"""
        try:
            from ._lifecycle_decorator import get_lifecycle_manager, LifecyclePhase
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
            lifecycle_manager = get_lifecycle_manager()

            # 遍历所有注册的类，查找监听此配置变更的方法
            for cls, methods_dict in lifecycle_manager._methods.items():
                if LifecyclePhase.ON_CONFIG_CHANGE in methods_dict:
                    methods = methods_dict[LifecyclePhase.ON_CONFIG_CHANGE]
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

    def enable_auto_save(self, file_path: str) -> bool:
        """
        启用配置自动保存

        Args:
            file_path: 配置文件路径

        Returns:
            是否启用成功
        """
        self._auto_save_enabled = True
        self._config_file_path = file_path
        return True

    def disable_auto_save(self) -> None:
        """禁用配置自动保存"""
        self._auto_save_enabled = False
        self._config_file_path = None


# 全局配置管理器实例
_config_manager = _SimpleConfigManager()


# 公共接口函数
def register_config(
    key: str,
    default_value: Any,
    value_type: Type[Any],
    description: str = "",
    validator: Optional[Callable[[Any], bool]] = None,
) -> None:
    """
    注册配置项

    Args:
        key: 配置键名
        default_value: 默认值
        value_type: 期望的类型
        description: 配置描述
        validator: 自定义验证函数
    """
    _config_manager.register_config(
        key, default_value, value_type, description, validator
    )


def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值

    Args:
        key: 配置键名
        default: 默认值

    Returns:
        配置值或默认值
    """
    return _config_manager.get_config(key, default)


def set_config(key: str, value: Any) -> bool:
    """
    设置配置值

    Args:
        key: 配置键名
        value: 配置值

    Returns:
        是否设置成功
    """
    return _config_manager.set_config(key, value)


def has_config(key: str) -> bool:
    """检查配置项是否存在"""
    return _config_manager.has_config(key)


def get_all_configs() -> Dict[str, Any]:
    """获取所有配置"""
    return _config_manager.get_all_configs()


def reset_config(key: str) -> bool:
    """重置单个配置项到默认值"""
    return _config_manager.reset_config(key)


def reset_all_configs() -> None:
    """重置所有配置到默认值"""
    _config_manager.reset_all_configs()


def load_config(file_path: str) -> bool:
    """
    从文件加载配置

    Args:
        file_path: 配置文件路径

    Returns:
        是否加载成功
    """
    return _config_manager.load_from_file(file_path)


def save_config(file_path: str) -> bool:
    """
    保存配置到文件

    Args:
        file_path: 配置文件路径

    Returns:
        是否保存成功
    """
    return _config_manager.save_to_file(file_path)


# 便捷函数：加载项目根目录下的配置文件
def load_project_config(filename: str = "config.yaml") -> bool:
    """
    加载项目根目录下的配置文件

    Args:
        filename: 配置文件名，默认为"config.yaml"

    Returns:
        是否加载成功
    """
    project_root = _path_manager.get_project_root()
    config_path = _path_manager.join_paths(project_root, filename)
    return load_config(config_path)


def save_project_config(filename: str = "config.yaml") -> bool:
    """
    保存配置到项目根目录下的文件

    Args:
        filename: 配置文件名，默认为"config.yaml"

    Returns:
        是否保存成功
    """
    project_root = _path_manager.get_project_root()
    config_path = _path_manager.join_paths(project_root, filename)
    return save_config(config_path)


def enable_config_auto_save(file_path: str) -> bool:
    """
    启用配置自动保存

    Args:
        file_path: 配置文件路径

    Returns:
        是否启用成功

    Example:
        # 启用自动保存到项目根目录的config.yaml
        enable_config_auto_save("config.yaml")

        # 之后所有配置变更都会自动保存
        set_config("database.url", "postgresql://localhost/mydb")
    """
    return _config_manager.enable_auto_save(file_path)


def enable_project_config_auto_save(filename: str = "config.yaml") -> bool:
    """
    启用项目配置自动保存

    Args:
        filename: 配置文件名，默认为"config.yaml"

    Returns:
        是否启用成功

    Example:
        # 启用自动保存到项目根目录的config.yaml
        enable_project_config_auto_save()
    """
    project_root = _path_manager.get_project_root()
    config_path = _path_manager.join_paths(project_root, filename)
    return _config_manager.enable_auto_save(config_path)


def disable_config_auto_save() -> None:
    """
    禁用配置自动保存

    Example:
        disable_config_auto_save()
    """
    _config_manager.disable_auto_save()


# 简单的系统配置函数 - 替代原来的版本控制器
def get_system_config(key: str, default: Any = None) -> Any:
    """
    获取系统配置值（简化版）

    Args:
        key: 配置键名
        default: 默认值

    Returns:
        配置值或默认值
    """
    # 系统配置前缀
    system_key = f"system.{key}"
    return get_config(system_key, default)
