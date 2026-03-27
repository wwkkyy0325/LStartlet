"""
配置管理器核心实现
提供配置注册、获取、验证、监听等功能
"""

import os
import yaml
from typing import Any, Dict, Optional, Set, List, Callable, Type
from pathlib import Path

from LStartlet.core.logger import info, error, warning
from LStartlet.core.path import get_project_root
from LStartlet.core.error.exceptions import ConfigError


class ConfigManager:
    """配置管理器 - 管理应用程序配置"""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_sources: Dict[str, str] = {}  # 配置项来源追踪
        self._protected_keys: Set[str] = set()  # 受保护的配置项（来自system_config）
        self._plugin_namespaces: Set[str] = set()  # 已注册的插件命名空间
        self._project_root = get_project_root()

        # 监听器
        self._listeners: List[Callable[[str, Any, Any], None]] = []
        self._key_listeners: Dict[str, List[Callable[[str, Any, Any], None]]] = {}

        # 配置文件路径
        self._user_config_path = os.path.join(self._project_root, "config.yaml")
        self._system_config_path = os.path.join(
            self._project_root, "system_config.yaml"
        )

        self._initialize_config()

    def _initialize_config(self):
        """初始化配置 - 按优先级加载配置文件"""
        # 1. 首先加载系统配置（受保护，用户不能修改）
        if os.path.exists(self._system_config_path):
            system_config = self._load_yaml_config(self._system_config_path)
            if system_config:
                self._flatten_and_merge_config(
                    system_config, source="system", protected=True
                )
                info(f"系统配置已从 {self._system_config_path} 加载")

        # 2. 然后加载用户配置（可覆盖默认值，但不能覆盖系统配置）
        if os.path.exists(self._user_config_path):
            user_config = self._load_yaml_config(self._user_config_path)
            if user_config:
                self._flatten_and_merge_config(
                    user_config, source="user", protected=False
                )
                info(f"用户配置已从 {self._user_config_path} 加载")

    def _load_yaml_config(self, file_path: str) -> Optional[Dict[str, Any]]:
        """安全加载YAML配置文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            warning(f"配置文件 {file_path} 不存在")
            return {}
        except yaml.YAMLError as e:
            error(f"YAML解析错误 in {file_path}: {e}")
            raise ConfigError(f"配置文件格式错误: {e}")
        except Exception as e:
            error(f"读取配置文件失败 {file_path}: {e}")
            raise ConfigError(f"无法读取配置文件: {e}")

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """将嵌套字典扁平化为点号分隔的键"""
        items: List[tuple[str, Any]] = []
        for k, v in d.items():
            new_key: str = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _flatten_and_merge_config(
        self, new_config: Dict[str, Any], source: str, protected: bool = False
    ) -> None:
        """扁平化并合并配置字典"""
        flat_config: Dict[str, Any] = self._flatten_dict(new_config)

        for key, value in flat_config.items():
            old_value: Any = self._config.get(key)
            if key in self._config_sources:
                # 配置项已存在
                if protected and not self._is_protected(key):
                    # 新配置是受保护的，但现有配置不是，可以覆盖
                    self._config[key] = value
                    self._config_sources[key] = source
                    if protected:
                        self._protected_keys.add(key)
                    self._notify_listeners(key, old_value, value)
                elif not protected and not self._is_protected(key):
                    # 都不受保护，可以覆盖
                    self._config[key] = value
                    self._config_sources[key] = source
                    self._notify_listeners(key, old_value, value)
                else:
                    # 其他情况（尝试覆盖受保护配置）发出警告但不覆盖
                    if protected != self._is_protected(key):
                        warning(f"配置项 {key} 的保护状态冲突，保持现有值")
            else:
                # 配置项不存在，直接添加
                self._config[key] = value
                self._config_sources[key] = source
                if protected:
                    self._protected_keys.add(key)
                self._notify_listeners(key, None, value)

    def _notify_listeners(self, key: str, old_value: Any, new_value: Any):
        """通知所有监听器配置变更"""
        # 通知全局监听器
        for listener in self._listeners:
            try:
                listener(key, old_value, new_value)
            except Exception as e:
                error(f"配置监听器执行失败: {e}")

        # 通知特定键的监听器
        if key in self._key_listeners:
            for listener in self._key_listeners[key]:
                try:
                    listener(key, old_value, new_value)
                except Exception as e:
                    error(f"配置监听器执行失败: {e}")

    def _is_protected(self, key: str) -> bool:
        """检查配置项是否受保护"""
        return key in self._protected_keys

    # ==================== 公共接口方法 ====================

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项的值"""
        return self._config.get(key, default)

    def has_config(self, key: str) -> bool:
        """检查配置项是否存在"""
        return key in self._config

    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置项"""
        return self._config.copy()

    def set_config(self, key: str, value: Any) -> bool:
        """设置配置项的值"""
        if key in self._protected_keys:
            error(f"无法修改受保护的配置项: {key}")
            return False

        # 验证特定配置项的值
        if key == "log_level":
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if value not in valid_levels:
                error(f"无效的日志级别: {value}")
                return False

        old_value = self._config.get(key)
        self._config[key] = value
        self._config_sources[key] = "external"
        self._notify_listeners(key, old_value, value)
        return True

    def reset_config(self, key: str) -> bool:
        """重置配置项 - 由于遵循零默认配置原则，直接删除配置项"""
        if key in self._protected_keys:
            error(f"无法重置受保护的配置项: {key}")
            return False

        if key in self._config:
            # 删除配置项
            old_value = self._config.pop(key)
            self._config_sources.pop(key, None)
            self._protected_keys.discard(key)
            self._notify_listeners(key, old_value, None)
            return True
        else:
            return False

    def reset_all_configs(self) -> None:
        """重置所有配置到默认状态"""
        self._config.clear()
        self._config_sources.clear()
        self._protected_keys.clear()
        self._plugin_namespaces.clear()
        self._initialize_config()

    def reset_to_defaults(self) -> None:
        """重置到系统默认配置（兼容旧接口）"""
        self.reset_all_configs()

    # ==================== 配置注册与管理 ====================

    def register_config(
        self,
        key: str,
        default_value: Any,
        value_type: Type,
        description: str = "",
        plugin_name: Optional[str] = None,
    ) -> bool:
        """注册新的配置项"""
        if self.has_config(key):
            warning(f"配置项 {key} 已存在，跳过注册")
            return False

        # 类型验证
        if not isinstance(default_value, value_type):
            error(
                f"配置项 {key} 的默认值类型不匹配: 期望 {value_type}, 实际 {type(default_value)}"
            )
            return False

        self._config[key] = default_value
        self._config_sources[key] = "external"
        return True

    def register_config_with_source(
        self,
        key: str,
        default_value: Any,
        value_type: Type,
        description: str = "",
        source: str = "external",
        plugin_name: Optional[str] = None,
    ) -> bool:
        """注册新的配置项并指定来源"""
        if self.has_config(key):
            warning(f"配置项 {key} 已存在，跳过注册")
            return False

        # 类型验证
        if not isinstance(default_value, value_type):
            error(
                f"配置项 {key} 的默认值类型不匹配: 期望 {value_type}, 实际 {type(default_value)}"
            )
            return False

        # 如果提供了plugin_name，使用它作为source
        actual_source = plugin_name if plugin_name is not None else source

        self._config[key] = default_value
        self._config_sources[key] = actual_source
        return True

    def add_key_listener(self, key: str, listener: Callable[[str, Any, Any], None]):
        """为特定配置键添加监听器"""
        if key not in self._key_listeners:
            self._key_listeners[key] = []
        self._key_listeners[key].append(listener)

    def add_global_listener(self, listener: Callable[[str, Any, Any], None]):
        """添加全局配置监听器"""
        self._listeners.append(listener)

    def remove_key_listener(self, key: str, listener: Callable[[str, Any, Any], None]):
        """移除特定配置键的监听器"""
        if key in self._key_listeners:
            if listener in self._key_listeners[key]:
                self._key_listeners[key].remove(listener)
                if not self._key_listeners[key]:
                    del self._key_listeners[key]
                return True
        return False

    def remove_global_listener(self, listener: Callable[[str, Any, Any], None]):
        """移除全局配置监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def list_namespaces(self) -> Set[str]:
        """获取所有已注册的命名空间"""
        return self._plugin_namespaces.copy()

    def get_config_source(self, key: str) -> Optional[str]:
        """获取配置项的来源"""
        return self._config_sources.get(key)

    def get_all_configs_by_source(self) -> Dict[str, Dict[str, Any]]:
        """按来源分组获取所有配置"""
        result: Dict[str, Dict[str, Any]] = {}
        for key, value in self._config.items():
            source: str = self._config_sources.get(key, "unknown")
            if source not in result:
                result[source] = {}
            result[source][key] = value
        return result

    # ==================== 文件操作 ====================

    def load(self, filename: str) -> bool:
        """加载配置文件（兼容旧接口）"""
        return self.load_from_file(filename)

    def save_to_file(self, filename: str) -> bool:
        """保存配置到文件"""
        try:
            # 只保存非系统保护的配置（user和external来源）
            user_config = {}
            for key, value in self._config.items():
                source = self._config_sources.get(key, "unknown")
                if source in ["user", "external"]:
                    user_config[key] = value

            # 将扁平化配置转换回嵌套结构
            nested_config = self._unflatten_dict(user_config)

            with open(filename, "w", encoding="utf-8") as f:
                yaml.dump(
                    nested_config, f, default_flow_style=False, allow_unicode=True
                )
            return True
        except Exception as e:
            error(f"保存配置文件失败 {filename}: {e}")
            return False

    def load_from_file(self, filename: str) -> bool:
        """从文件加载配置"""
        try:
            config_data = self._read_config_file(filename)
            if config_data:
                self._flatten_and_merge_config(
                    config_data, source="user", protected=False
                )
                return True
            return False
        except Exception as e:
            error(f"加载配置文件失败 {filename}: {e}")
            return False

    def load_plugin_config(self, namespace: str, config_path: str) -> None:
        """加载插件配置文件"""
        try:
            config_data: Dict[str, Any] = self._read_config_file(config_path)
            if config_data:
                # 为插件配置添加命名空间前缀
                namespaced_config: Dict[str, Any] = {}
                for key, value in config_data.items():
                    namespaced_key: str = f"{namespace}.{key}"
                    namespaced_config[namespaced_key] = value

                self._flatten_and_merge_config(
                    namespaced_config, source=f"plugin:{namespace}", protected=False
                )
                self._plugin_namespaces.add(namespace)
                info(f"插件 {namespace} 配置已加载")
            else:
                # 如果没有配置文件，创建空配置字典
                empty_config: Dict[str, Any] = {}
                # 扁平化嵌套配置
                flat_config: Dict[str, Any] = self._flatten_dict(empty_config)
                for key, value in flat_config.items():
                    self._config[key] = value
                    self._config_sources[key] = f"plugin:{namespace}"
                self._plugin_namespaces.add(namespace)
        except Exception as e:
            error(f"加载插件配置失败 {config_path}: {e}")

    def _read_config_file(self, file_path: str) -> Dict[str, Any]:
        """读取配置文件"""
        if not os.path.exists(file_path):
            warning(f"配置文件 {file_path} 不存在")
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            error(f"YAML解析错误 in {file_path}: {e}")
            raise ConfigError(f"配置文件格式错误: {e}")
        except Exception as e:
            error(f"读取配置文件失败 {file_path}: {e}")
            raise ConfigError(f"无法读取配置文件: {e}")

    def _unflatten_dict(self, flat_dict: Dict[str, Any]) -> Dict[str, Any]:
        """将扁平化的字典转换回嵌套结构"""
        nested: Dict[str, Any] = {}
        for key, value in flat_dict.items():
            parts: List[str] = key.split(".")
            current: Dict[str, Any] = nested
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return nested
