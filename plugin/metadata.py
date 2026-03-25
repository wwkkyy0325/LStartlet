"""
插件元数据定义和验证
定义 plugin.json 的结构和验证逻辑
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from core.logger import info, warning, error
from plugin.exceptions.plugin_exceptions import PluginLoadError


@dataclass
class PluginMetadata:
    """插件元数据"""
    namespace: str  # 插件命名空间，如 com.company.plugin-name
    name: str       # 插件显示名称
    version: str    # 插件版本
    author: str     # 插件作者
    description: str  # 插件描述
    compatibility: Dict[str, str]  # 主程序版本兼容性
    entry_point: Dict[str, str]    # 入口点配置
    permissions: List[str] = field(default_factory=list)  # 权限列表
    dependencies: Dict[str, str] = field(default_factory=dict)  # Python包依赖列表
    plugin_dependencies: List[str] = field(default_factory=list)  # 插件依赖列表
    
    def __post_init__(self):
        """验证元数据"""
        self._validate()
    
    def _validate(self):
        """验证元数据的完整性"""
        if not self.namespace:
            raise PluginLoadError("metadata", "Plugin namespace is required")
        
        if not self.name:
            raise PluginLoadError("metadata", "Plugin name is required")
            
        if not self.version:
            raise PluginLoadError("metadata", "Plugin version is required")
            
        if not self.author:
            raise PluginLoadError("metadata", "Plugin author is required")
            
        if not self.compatibility or 'min_version' not in self.compatibility:
            raise PluginLoadError("metadata", "Plugin compatibility.min_version is required")
            
        if not self.entry_point or 'module' not in self.entry_point or 'class' not in self.entry_point:
            raise PluginLoadError("metadata", "Plugin entry_point.module and entry_point.class are required")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """从字典创建 PluginMetadata 实例"""
        return cls(
            namespace=data.get('namespace', ''),
            name=data.get('name', ''),
            version=data.get('version', ''),
            author=data.get('author', ''),
            description=data.get('description', ''),
            compatibility=data.get('compatibility', {}),
            entry_point=data.get('entry_point', {}),
            permissions=data.get('permissions', []),
            dependencies=data.get('dependencies', {})
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'PluginMetadata':
        """从 plugin.json 文件加载元数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise PluginLoadError("metadata", f"Invalid JSON in plugin.json: {e}")
        except FileNotFoundError:
            raise PluginLoadError("metadata", f"plugin.json not found at {file_path}")
        except Exception as e:
            raise PluginLoadError("metadata", f"Failed to load plugin.json: {e}")


class PluginCompatibilityChecker:
    """插件兼容性检查器"""
    
    def __init__(self, current_app_version: str):
        self.current_app_version = current_app_version
    
    def is_compatible(self, metadata: PluginMetadata) -> bool:
        """检查插件是否与当前主程序版本兼容"""
        try:
            min_version = metadata.compatibility.get('min_version')
            max_version = metadata.compatibility.get('max_version')
            
            if not min_version:
                return False
                
            # 检查最小版本要求
            if not self._check_version_compatibility(self.current_app_version, f">={min_version}"):
                return False
                
            # 检查最大版本限制（如果有）
            if max_version and not self._check_version_compatibility(self.current_app_version, f"<={max_version}"):
                return False
                
            return True
            
        except Exception as e:
            error(f"Plugin compatibility check failed: {e}")
            return False
    
    def _check_version_compatibility(self, installed_version: str, required_spec: str) -> bool:
        """检查版本兼容性"""
        if not required_spec or required_spec == "*":
            return True
            
        try:
            from packaging import version, specifiers
            installed = version.parse(installed_version)
            specifier = specifiers.SpecifierSet(required_spec)
            return installed in specifier
        except ImportError:
            # 如果没有packaging库，进行简单比较
            return self._simple_version_check(installed_version, required_spec)
        except Exception as e:
            warning(f"Version compatibility check failed, assuming compatible: {e}")
            return True
    
    def _simple_version_check(self, installed_version: str, required_spec: str) -> bool:
        """简单版本检查（当packaging不可用时）"""
        # 移除前缀操作符
        clean_spec = required_spec.lstrip(">=><=!~")
        
        if ">=" in required_spec:
            return self._compare_versions(installed_version, clean_spec) >= 0
        elif ">" in required_spec:
            return self._compare_versions(installed_version, clean_spec) > 0
        elif "<=" in required_spec:
            return self._compare_versions(installed_version, clean_spec) <= 0
        elif "<" in required_spec:
            return self._compare_versions(installed_version, clean_spec) < 0
        elif "==" in required_spec or required_spec == clean_spec:
            return installed_version == clean_spec
        else:
            # 其他情况假设兼容
            return True
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较两个版本字符串"""
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]
            
            # 补齐较短的版本
            max_len = max(len(parts1), len(parts2))
            parts1.extend([0] * (max_len - len(parts1)))
            parts2.extend([0] * (max_len - len(parts2)))
            
            for p1, p2 in zip(parts1, parts2):
                if p1 < p2:
                    return -1
                elif p1 > p2:
                    return 1
            return 0
        except ValueError:
            # 如果版本包含非数字字符，进行字符串比较
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0


class PluginAvailabilityChecker:
    """插件可用性检查器"""
    
    def __init__(self, dependency_manager):
        self.dependency_manager = dependency_manager
    
    def check_availability(self, metadata: PluginMetadata) -> Dict[str, Any]:
        """
        检查插件的可用性
        
        Returns:
            包含可用性信息的字典:
            {
                'available': bool,
                'reasons': List[str],  # 不可用的原因列表
                'missing_dependencies': List[str]  # 缺失的依赖列表
            }
        """
        result = {
            'available': True,
            'reasons': [],
            'missing_dependencies': []
        }
        
        # 检查依赖是否完整
        if metadata.dependencies:
            missing_deps = []
            for dep_name, version_spec in metadata.dependencies.items():
                if not self.dependency_manager.check_dependency_availability(dep_name, version_spec):
                    missing_deps.append(f"{dep_name}{version_spec}")
            
            if missing_deps:
                result['available'] = False
                result['missing_dependencies'] = missing_deps
                result['reasons'].append(f"Missing dependencies: {', '.join(missing_deps)}")
        
        return result