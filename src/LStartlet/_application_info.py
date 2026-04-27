"""
应用程序元数据装饰器 - 强制实现程序基本信息
用于程序识别、依赖管理、目录命名等
"""

from typing import Optional, Dict, Any, Type, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import re

from ._path_manager import (
    _get_app_path,
    _ensure_app_directory,
    _write_app_file,
    _read_app_file,
    _app_file_exists,
    _delete_app_file,
    _list_app_files,
)

from ._logging import (
    _log_framework_info,
    _log_framework_warning,
    _log_framework_error,
)


def _validate_directory_name(name: str) -> bool:
    """验证目录名称是否符合规范"""
    if not name or not isinstance(name, str):
        return False

    # 检查长度
    if len(name) < 3 or len(name) > 50:
        return False

    # 检查是否以字母开头
    if not name[0].isalpha():
        return False

    # 检查是否只包含允许的字符
    pattern = r"^[a-zA-Z][a-zA-Z0-9_-]*$"
    if not re.match(pattern, name):
        return False

    # 检查保留名称
    reserved_names = ["framework", "lstartlet", "system"]
    if name.lower() in reserved_names:
        return False

    return True


@dataclass
class _ApplicationMetadata:
    """应用程序元数据（内部实现）"""

    directory_name: str
    display_name: Optional[str] = None
    author: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    version: Optional[str] = None
    homepage: Optional[str] = None

    def get_config_root(self) -> str:
        """获取配置根目录"""
        return _get_app_path(self.directory_name)

    def get_log_root(self) -> str:
        """获取日志根目录"""
        return _get_app_path(self.directory_name, "logs")

    def get_cache_root(self) -> str:
        """获取缓存根目录"""
        return _get_app_path(self.directory_name, "cache")

    def get_data_root(self) -> str:
        """获取数据根目录"""
        return _get_app_path(self.directory_name, "data")

    def get_plugin_root(self) -> str:
        """获取插件根目录"""
        return _get_app_path(self.directory_name, "plugins")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "directory_name": self.directory_name,
            "display_name": self.display_name,
            "author": self.author,
            "email": self.email,
            "description": self.description,
            "dependencies": self.dependencies,
            "version": self.version,
            "homepage": self.homepage,
        }


class ApplicationInfo:
    """
    应用程序信息装饰器 - 标记应用程序的元数据类

    Args:
        cls: 应用程序信息类

    Returns:
        装饰后的应用程序信息类

    Example:
        @ApplicationInfo
        class MyAppInfo:
            def get_directory_name(self) -> str:
                return "my_app"

            def get_display_name(self) -> Optional[str]:
                return "我的应用"

            def get_author(self) -> Optional[str]:
                return "Author Name"

            def get_email(self) -> Optional[str]:
                return "author@example.com"

            def get_description(self) -> Optional[str]:
                return "My application description"

            def get_dependencies(self) -> Optional[List[str]]:
                return ["OtherApp"]

            def get_version(self) -> Optional[str]:
                return "1.0.0"

    Note:
        - get_directory_name() 是必需的，用于目录命名，必须符合命名规范
        - get_display_name() 是可选的，用于UI显示，可以是中文或特殊字符
        - 如果没有提供 get_display_name()，则使用 get_directory_name() 作为显示名
        - 目录命名规范：字母开头，只能包含字母、数字、下划线、连字符
        - 框架会自动收集和管理这些信息
    """

    _is_application_info = True

    def __init__(self, cls: type):
        self._cls = cls
        self._metadata: Optional[_ApplicationMetadata] = None

        # 立即注册应用程序信息
        self._register()

    def __call__(self, *args, **kwargs):
        """支持类装饰器语法"""
        instance = self._cls(*args, **kwargs)
        return instance

    def _register(self) -> None:
        """自动注册应用程序信息"""
        # 检查是否已注册
        if self._cls in [info._cls for info in _application_info_registry.values()]:
            return  # 避免重复注册

        # 获取元数据
        metadata = self._get_metadata()

        # 检查是否已注册（通过目录名）
        if metadata.directory_name in _application_info_registry:
            return  # 避免重复注册

        # 验证必需字段
        if not metadata.directory_name:
            raise ValueError(f"应用程序信息缺少必需字段: directory_name")

        # 验证目录名格式
        if not _validate_directory_name(metadata.directory_name):
            raise ValueError(
                f"目录名称 '{metadata.directory_name}' 不符合规范。"
                f"规则：字母开头，只能包含字母、数字、下划线、连字符，长度3-50个字符"
            )

        # 注册到注册表
        _application_info_registry[metadata.directory_name] = self

        # 将元数据放入缓存（避免重复调用 _get_metadata）
        _metadata_cache[metadata.directory_name] = metadata

        # 自动创建应用程序目录
        try:
            app_root = _ensure_app_directory(metadata.directory_name)
            _log_framework_info(
                f"已注册应用程序: {metadata.display_name or metadata.directory_name} (目录名: {metadata.directory_name})"
            )
            _log_framework_info(f"已创建应用程序目录: {app_root}")

            # 批量创建标准子目录（优化性能）
            subdirs = ["logs", "cache", "data", "plugins", "config"]
            for subdir in subdirs:
                subdir_path = _ensure_app_directory(metadata.directory_name, subdir)
                _log_framework_info(f"已创建子目录: {subdir_path}")
        except Exception as e:
            _log_framework_warning(f"创建应用程序目录失败: {e}")

        # 验证版本号格式（如果提供）
        if metadata.version:
            try:
                parts = metadata.version.split(".")
                if len(parts) < 2:
                    _log_framework_warning(
                        f"应用程序 '{metadata.display_name or metadata.directory_name}' 的版本号格式不正确: {metadata.version}"
                    )
            except Exception:
                _log_framework_warning(
                    f"应用程序 '{metadata.display_name or metadata.directory_name}' 的版本号格式不正确: {metadata.version}"
                )

        # 检查依赖是否存在
        if metadata.dependencies:
            missing_deps = [
                dep
                for dep in metadata.dependencies
                if dep not in _application_info_registry
            ]
            if missing_deps:
                _log_framework_warning(
                    f"应用程序 '{metadata.display_name or metadata.directory_name}' 的依赖尚未注册: {', '.join(missing_deps)}"
                )

    def _get_metadata(self) -> _ApplicationMetadata:
        """获取应用程序元数据（内部方法）"""
        if self._metadata is None:
            instance = self._cls()
            directory_name = self._call_method(instance, "get_directory_name")

            if not directory_name:
                raise ValueError(f"应用程序信息缺少必需字段: directory_name")

            if not _validate_directory_name(directory_name):
                raise ValueError(
                    f"目录名称 '{directory_name}' 不符合规范。"
                    f"规则：字母开头，只能包含字母、数字、下划线、连字符，长度3-50个字符"
                )

            display_name = self._call_method(instance, "get_display_name")

            self._metadata = _ApplicationMetadata(
                directory_name=directory_name,
                display_name=display_name,
                author=self._call_method(instance, "get_author"),
                email=self._call_method(instance, "get_email"),
                description=self._call_method(instance, "get_description"),
                dependencies=self._call_method(instance, "get_dependencies") or [],
                version=self._call_method(instance, "get_version"),
                homepage=self._call_method(instance, "get_homepage"),
            )
        return self._metadata

    def _call_method(self, instance: Any, method_name: str) -> Any:
        """安全地调用方法"""
        if hasattr(instance, method_name):
            method = getattr(instance, method_name)
            if callable(method):
                return method()
        return None


# 全局应用程序信息注册表
_application_info_registry: Dict[str, ApplicationInfo] = {}
# 元数据缓存（避免重复调用 _get_metadata）
_metadata_cache: Dict[str, _ApplicationMetadata] = {}


def _get_application_info(
    app_name: Optional[str] = None,
) -> Optional[_ApplicationMetadata]:
    """获取应用程序元数据（带缓存优化，内部实现）"""
    if app_name is None:
        if _application_info_registry:
            first_key = next(iter(_application_info_registry))
            if first_key not in _metadata_cache:
                _metadata_cache[first_key] = _application_info_registry[
                    first_key
                ]._get_metadata()
            return _metadata_cache[first_key]
        return None

    if app_name in _application_info_registry:
        if app_name not in _metadata_cache:
            _metadata_cache[app_name] = _application_info_registry[
                app_name
            ]._get_metadata()
        return _metadata_cache[app_name]
    return None


def _get_all_applications() -> Dict[str, _ApplicationMetadata]:
    """获取所有注册的应用程序元数据（内部函数，带缓存优化）"""
    result = {}
    for name in _application_info_registry.keys():
        if name not in _metadata_cache:
            _metadata_cache[name] = _application_info_registry[name]._get_metadata()
        result[name] = _metadata_cache[name]
    return result


def _check_dependencies(app_name: str) -> List[str]:
    """检查应用程序的依赖是否满足（内部函数，性能优化）"""
    metadata = _get_application_info(app_name)
    if not metadata:
        return []

    registered_apps = set(_application_info_registry.keys())
    missing_deps = [dep for dep in metadata.dependencies if dep not in registered_apps]
    return missing_deps


def _list_applications() -> List[str]:
    """列出所有注册的应用程序（内部函数）"""
    return list(_application_info_registry.keys())


@dataclass
class _ApplicationCheckResult:
    """应用程序检查结果（内部使用）"""

    app_name: str
    is_healthy: bool
    missing_dependencies: List[str]
    issues: List[str]
    check_time: datetime = field(default_factory=datetime.now)

    def _to_dict(self) -> Dict[str, Any]:
        """转换为字典（内部方法）"""
        return {
            "app_name": self.app_name,
            "is_healthy": self.is_healthy,
            "missing_dependencies": self.missing_dependencies,
            "issues": self.issues,
            "check_time": self.check_time.isoformat(),
        }


@dataclass
class _FrameworkCheckReport:
    """框架检查报告（内部使用）"""

    total_apps: int
    healthy_apps: int
    unhealthy_apps: int
    app_results: Dict[str, _ApplicationCheckResult]
    check_time: datetime = field(default_factory=datetime.now)

    def _to_dict(self) -> Dict[str, Any]:
        """转换为字典（内部方法）"""
        return {
            "total_apps": self.total_apps,
            "healthy_apps": self.healthy_apps,
            "unhealthy_apps": self.unhealthy_apps,
            "app_results": {
                name: result._to_dict() for name, result in self.app_results.items()
            },
            "check_time": self.check_time.isoformat(),
        }

    def _to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串（内部方法）"""
        return json.dumps(self._to_dict(), indent=indent, ensure_ascii=False)


def _check_application_health(app_name: str) -> _ApplicationCheckResult:
    """检查单个应用程序的健康状态（内部函数）"""
    metadata = _get_application_info(app_name)
    if not metadata:
        return _ApplicationCheckResult(
            app_name=app_name,
            is_healthy=False,
            missing_dependencies=[],
            issues=[f"应用程序未注册: {app_name}"],
        )

    issues = []

    missing_deps = _check_dependencies(app_name)
    if missing_deps:
        issues.append(f"缺失依赖: {', '.join(missing_deps)}")

    try:
        config_root = metadata.get_config_root()
        if not os.path.exists(config_root):
            issues.append(f"配置目录不存在: {config_root}")
    except Exception as e:
        issues.append(f"目录检查失败: {str(e)}")

    if not metadata.directory_name:
        issues.append("缺少必需字段: directory_name")

    if metadata.version:
        try:
            parts = metadata.version.split(".")
            if len(parts) < 2:
                issues.append(f"版本号格式不正确: {metadata.version}")
        except Exception:
            issues.append(f"版本号格式不正确: {metadata.version}")

    is_healthy = len(issues) == 0 and len(missing_deps) == 0

    return _ApplicationCheckResult(
        app_name=app_name,
        is_healthy=is_healthy,
        missing_dependencies=missing_deps,
        issues=issues,
    )


def _check_all_applications() -> _FrameworkCheckReport:
    """检查所有注册的应用程序（内部函数）"""
    app_names = _list_applications()
    app_results = {}

    healthy_count = 0
    unhealthy_count = 0

    for app_name in app_names:
        result = _check_application_health(app_name)
        app_results[app_name] = result

        if result.is_healthy:
            healthy_count += 1
        else:
            unhealthy_count += 1

    return _FrameworkCheckReport(
        total_apps=len(app_names),
        healthy_apps=healthy_count,
        unhealthy_apps=unhealthy_count,
        app_results=app_results,
    )


def _save_check_report(
    report: _FrameworkCheckReport, file_path: Optional[str] = None
) -> str:
    """保存检查报告到文件（内部函数）"""
    if file_path is None:
        from ._path_manager import _get_user_config_root

        reports_dir = os.path.join(_get_user_config_root(), "reports")
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(reports_dir, f"check_report_{timestamp}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report._to_json())

    return file_path


def _load_check_report(file_path: str) -> _FrameworkCheckReport:
    """从文件加载检查报告（内部函数）"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    app_results = {}
    for app_name, result_data in data["app_results"].items():
        app_results[app_name] = _ApplicationCheckResult(
            app_name=result_data["app_name"],
            is_healthy=result_data["is_healthy"],
            missing_dependencies=result_data["missing_dependencies"],
            issues=result_data["issues"],
            check_time=datetime.fromisoformat(result_data["check_time"]),
        )

    return _FrameworkCheckReport(
        total_apps=data["total_apps"],
        healthy_apps=data["healthy_apps"],
        unhealthy_apps=data["unhealthy_apps"],
        app_results=app_results,
        check_time=datetime.fromisoformat(data["check_time"]),
    )


def _print_check_report(report: _FrameworkCheckReport) -> None:
    """打印检查报告（内部函数）"""
    _log_framework_info("=" * 60)
    _log_framework_info(f"框架应用程序检查报告")
    _log_framework_info(f"检查时间: {report.check_time.strftime('%Y-%m-%d %H:%M:%S')}")
    _log_framework_info("=" * 60)
    _log_framework_info(f"总应用程序数: {report.total_apps}")
    _log_framework_info(f"健康应用程序: {report.healthy_apps}")
    _log_framework_info(f"不健康应用程序: {report.unhealthy_apps}")
    _log_framework_info("=" * 60)

    for app_name, result in report.app_results.items():
        status = "[OK] 健康" if result.is_healthy else "[FAIL] 不健康"
        _log_framework_info(f"\n{status} - {app_name}")

        if result.missing_dependencies:
            _log_framework_info(f"  缺失依赖: {', '.join(result.missing_dependencies)}")

        if result.issues:
            _log_framework_info(f"  问题:")
            for issue in result.issues:
                _log_framework_info(f"    - {issue}")

    _log_framework_info("=" * 60)


def _get_dependency_graph() -> Dict[str, List[str]]:
    """获取应用程序依赖图（内部函数）"""
    dependency_graph = {}

    for app_name in _list_applications():
        metadata = _get_application_info(app_name)
        if metadata:
            dependency_graph[app_name] = metadata.dependencies

    return dependency_graph


def _print_dependency_graph() -> None:
    """打印应用程序依赖图（内部函数）"""
    _log_framework_info("=" * 60)
    _log_framework_info("应用程序依赖图")
    _log_framework_info("=" * 60)

    dependency_graph = _get_dependency_graph()

    for app_name, dependencies in dependency_graph.items():
        if dependencies:
            _log_framework_info(f"{app_name} -> {', '.join(dependencies)}")
        else:
            _log_framework_info(f"{app_name} (无依赖)")

    _log_framework_info("=" * 60)


def _check_circular_dependencies() -> List[List[str]]:
    """检查循环依赖（内部函数）"""
    dependency_graph = _get_dependency_graph()
    visited = set()
    recursion_stack = set()
    cycles = []

    def dfs(node: str, path: List[str]) -> None:
        if node in recursion_stack:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return

        if node in visited:
            return

        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        for neighbor in dependency_graph.get(node, []):
            if neighbor in dependency_graph:
                dfs(neighbor, path.copy())

        recursion_stack.remove(node)

    for app_name in _list_applications():
        if app_name not in visited:
            dfs(app_name, [])

    return cycles


def _print_circular_dependencies() -> None:
    """打印循环依赖检查结果（内部函数）"""
    _log_framework_info("=" * 60)
    _log_framework_info("循环依赖检查")
    _log_framework_info("=" * 60)

    cycles = _check_circular_dependencies()

    if cycles:
        _log_framework_info(f"发现 {len(cycles)} 个循环依赖:")
        for i, cycle in enumerate(cycles, 1):
            _log_framework_info(f"{i}. {' -> '.join(cycle)}")
    else:
        _log_framework_info("[OK] 未发现循环依赖")

    _log_framework_info("=" * 60)


def _get_application_summary() -> Dict[str, Any]:
    """获取应用程序摘要信息（内部函数）"""
    apps = _get_all_applications()
    dependency_graph = _get_dependency_graph()

    summary = {
        "total_apps": len(apps),
        "app_names": list(apps.keys()),
        "dependency_graph": dependency_graph,
        "has_circular_dependencies": len(_check_circular_dependencies()) > 0,
        "apps_with_dependencies": [
            name for name, deps in dependency_graph.items() if deps
        ],
        "apps_without_dependencies": [
            name for name, deps in dependency_graph.items() if not deps
        ],
    }

    return summary


def _print_application_summary() -> None:
    """打印应用程序摘要（内部函数）"""
    _log_framework_info("=" * 60)
    _log_framework_info("应用程序摘要")
    _log_framework_info("=" * 60)

    summary = _get_application_summary()

    _log_framework_info(f"总应用程序数: {summary['total_apps']}")
    _log_framework_info(f"有依赖的应用: {len(summary['apps_with_dependencies'])}")
    _log_framework_info(f"无依赖的应用: {len(summary['apps_without_dependencies'])}")
    _log_framework_info(
        f"存在循环依赖: {'是' if summary['has_circular_dependencies'] else '否'}"
    )

    _log_framework_info("\n应用程序列表:")
    for app_name in summary["app_names"]:
        _log_framework_info(f"  - {app_name}")

    _log_framework_info("=" * 60)


def _validate_framework() -> bool:
    """验证框架状态（内部函数）"""
    report = _check_all_applications()
    cycles = _check_circular_dependencies()

    if report.unhealthy_apps > 0:
        return False

    if cycles:
        return False

    return True


def _auto_check_and_report() -> None:
    """自动检查框架并生成报告（内部函数）"""
    if not _list_applications():
        return

    report = _check_all_applications()
    cycles = _check_circular_dependencies()

    if report.unhealthy_apps > 0 or cycles:
        _print_check_report(report)
        _print_circular_dependencies()

        report_path = _save_check_report(report)
        _log_framework_info(f"检查报告已保存到: {report_path}")


# 全局变量用于缓存当前应用名称
_current_app_name: Optional[str] = None


def _get_current_app_name() -> Optional[str]:
    """获取当前应用程序名称"""
    global _current_app_name

    if _current_app_name is not None:
        return _current_app_name

    if _application_info_registry:
        _current_app_name = list(_application_info_registry.keys())[0]
        return _current_app_name

    return None
