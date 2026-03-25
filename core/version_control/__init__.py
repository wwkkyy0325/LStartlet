"""
版本控制模块 - 提供增量包生成和依赖管理功能
"""

from .version_controller import VersionController, ChangeAnalyzer, IncrementalPackageGenerator
from .dependency_resolver import DependencyResolver

__all__ = [
    'VersionController',
    'ChangeAnalyzer', 
    'IncrementalPackageGenerator',
    'DependencyResolver'
]