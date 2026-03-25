"""配置管理器工具函数"""

import yaml
import os
from typing import Any, Dict, Union, Tuple, cast
from core.path import ensure_directory_exists
from core.decorators import with_error_handling, monitor_metrics # type: ignore


class ConfigUtils:
    """配置工具类"""
    
    @staticmethod
    @monitor_metrics("config_validate_type", include_labels=True)
    def validate_config_type(value: Any, expected_type: str) -> bool:
        """
        验证配置值的类型
        
        Args:
            value: 要验证的值
            expected_type: 期望的类型
            
        Returns:
            是否类型匹配
        """
        type_mapping: Dict[str, Union[type, Tuple[type, ...]]] = {
            "string": str,
            "integer": int,
            "float": (int, float),
            "boolean": bool,
            "list": list,
            "dict": dict,
            "path": str  # 路径在存储时是字符串
        }
        
        if expected_type not in type_mapping:
            return False
        
        expected_python_type = type_mapping[expected_type]
        return isinstance(value, expected_python_type)
    
    @staticmethod
    @with_error_handling(error_code="CONFIG_GET_NESTED_ERROR", default_return=None)
    @monitor_metrics("config_get_nested", include_labels=True)
    def safe_get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        安全获取嵌套字典中的值
        
        Args:
            data: 数据字典
            key_path: 键路径，使用点号分隔，如 "database.host"
            default: 默认值
            
        Returns:
            获取到的值或默认值
        """
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            return current
        except (TypeError, AttributeError):
            return default
    
    @staticmethod
    @with_error_handling(error_code="CONFIG_SET_NESTED_ERROR", default_return=False)
    @monitor_metrics("config_set_nested", include_labels=True)
    def safe_set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> bool:
        """
        安全设置嵌套字典中的值
        
        Args:
            data: 数据字典
            key_path: 键路径，使用点号分隔，如 "database.host"
            value: 要设置的值
            
        Returns:
            是否设置成功
        """
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys[:-1]:
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
            
            current[keys[-1]] = value
            return True
        except (TypeError, AttributeError):
            return False
    
    @staticmethod
    @monitor_metrics("config_merge", include_labels=True)
    def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并两个配置字典（深度合并）
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            
        Returns:
            合并后的配置
        """
        result = base_config.copy()
        
        for key, value in override_config.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                # 使用 cast 明确指定类型，避免类型检查器报错
                result[key] = ConfigUtils.merge_configs(
                    cast(Dict[str, Any], result[key]), 
                    cast(Dict[str, Any], value)
                )
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    @with_error_handling(error_code="CONFIG_BACKUP_ERROR", default_return=False)
    @monitor_metrics("config_backup", include_labels=True)
    def create_config_backup(config_data: Dict[str, Any], backup_dir: str, max_backups: int = 5) -> bool:
        """
        创建配置备份
        
        Args:
            config_data: 配置数据
            backup_dir: 备份目录
            max_backups: 最大备份数量
            
        Returns:
            是否备份成功
        """
        try:
            ensure_directory_exists(backup_dir)
            
            # 清理旧备份
            backup_files = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith('config_backup_')],
                reverse=True
            )
            
            # 保留最新的 max_backups 个备份
            for old_file in backup_files[max_backups-1:]:
                os.remove(os.path.join(backup_dir, old_file))
            
            # 创建新备份
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'config_backup_{timestamp}.yaml')
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, indent=2, sort_keys=False)
            
            return True
        except Exception:
            return False