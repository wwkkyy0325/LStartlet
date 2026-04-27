"""
框架启动和停止管理

提供统一的框架启动和停止命令，自动管理所有框架组件的生命周期。
"""

from typing import Optional, List, Type, Any
from functools import wraps
from ._di_decorator import _start_framework, _stop_framework, _activate_framework
from ._plugin_manager import _get_plugin_manager, _PluginManager
from ._logging import _log_framework_info, _log_framework_error, _log_framework_warning


# ============================================================================
# 主框架类 - 内部实现
# ============================================================================


class _Framework:
    """框架类 - 统一的框架启动和停止管理"""

    def __init__(
        self,
        app_info: Optional[Any] = None,
        services: Optional[List[Type]] = None,
        framework_instance: Optional[Any] = None,
        console_log_level: str = "INFO",
        file_log_level: str = "DEBUG",
    ):
        self._app_info = app_info
        self._services = services or []
        self._framework_instance = framework_instance
        self._plugin_manager: Optional[_PluginManager] = None
        self._started = False
        self._console_log_level = console_log_level
        self._file_log_level = file_log_level
        self._auto_start_services: List[Type] = []

    def _register_component(self, component: Any) -> None:
        """注册组件（内部方法）"""
        _log_framework_info(f"已注册组件: {component.__class__.__name__}")

    def _register_service(self, service_class: Type) -> None:
        """注册服务（内部方法）"""
        if hasattr(service_class, "_is_service"):
            if (
                hasattr(service_class, "_service_auto_start")
                and service_class._service_auto_start
            ):
                self._auto_start_services.append(service_class)
                _log_framework_info(f"已注册服务（自动启动）: {service_class.__name__}")
            else:
                _log_framework_info(
                    f"已注册服务（已自动注册到DI容器）: {service_class.__name__}"
                )
        else:
            self._services.append(service_class)
            _log_framework_info(f"已注册服务: {service_class.__name__}")

    def _start(self) -> None:
        """启动框架（内部方法）"""
        if self._started:
            _log_framework_warning("框架已经启动，无需重复启动")
            return

        _log_framework_info("正在启动框架...")

        try:
            from ._logging import _configure_logging

            _configure_logging(
                console_level=self._console_log_level, file_level=self._file_log_level
            )
            _log_framework_info(
                f"日志系统已配置（终端: {self._console_log_level}, 文件: {self._file_log_level}）"
            )

            _activate_framework(
                app_info_class=self._app_info,
                services=self._services,
                auto_register=True,
            )

            if self._framework_instance is not None:
                self._plugin_manager = _get_plugin_manager(
                    framework=self._framework_instance
                )
                _log_framework_info("插件管理器已初始化")

            self._auto_start_all()

            self._started = True
            _log_framework_info("框架启动成功")

        except Exception as e:
            _log_framework_error(f"框架启动失败: {e}")
            raise

    def _auto_start_all(self):
        """自动启动所有标记的服务（内部方法）"""
        for service_class in self._auto_start_services:
            try:
                from ._di_decorator import _resolve_service

                service = _resolve_service(service_class)
                _log_framework_info(f"自动启动服务: {service_class.__name__}")
            except Exception as e:
                _log_framework_error(f"自动启动服务失败: {e}")

    def _stop(self) -> None:
        """停止框架（内部方法）"""
        if not self._started:
            _log_framework_warning("框架未启动，无需停止")
            return

        _log_framework_info("正在停止框架...")

        try:
            if self._plugin_manager is not None:
                self._plugin_manager._auto_unload_all()
                _log_framework_info("所有插件已卸载")

            _stop_framework()

            self._started = False
            _log_framework_info("框架停止成功")

        except Exception as e:
            _log_framework_error(f"框架停止失败: {e}")
            raise

    def _is_started(self) -> bool:
        """检查框架是否已启动（内部方法）"""
        return self._started


# 便捷函数
def start_framework(
    app_info: Optional[Any] = None,
    services: Optional[List[Type]] = None,
    framework_instance: Optional[Any] = None,
) -> None:
    """
    启动框架 - 一行代码启动框架，自动处理所有复杂操作

    Args:
        app_info: 应用程序信息类或实例（可选）
        services: 需要注册的服务类列表（可选，已废弃，使用 @Service 装饰器）
        framework_instance: 框架实例（可选，用于插件系统）

    Raises:
        ValueError: 如果应用程序信息无效
        RuntimeError: 如果健康检查失败

    Example:
        from LStartlet import start_framework, ApplicationInfo, Service, Start

        @ApplicationInfo
        class MyApp:
            def get_directory_name(self) -> str:
                return "MyApp"

        @Service(singleton=True, auto_start=True)
        class MyService:
            @Start()
            def on_start(self):
                print("服务已启动")

        # 一行启动框架
        start_framework(app_info=MyApp)

    Note:
        - 自动创建应用程序目录（~/.lstartlet/{app_name}）
        - 自动配置日志系统（终端和文件输出）
        - 自动注册所有 @Service 装饰的服务
        - 自动启动所有标记为 auto_start 的服务
        - 自动加载插件（如果提供了 framework_instance）
        - 自动触发所有 @Init 和 @Start 装饰的方法
        - 支持 console_log_level 和 file_log_level 参数配置日志级别
    """
    global _framework_instance
    framework = _Framework(
        app_info=app_info,
        services=services,
        framework_instance=framework_instance,
    )
    _framework_instance = framework
    framework._start()


# 全局框架实例
_framework_instance: Optional[_Framework] = None


def stop_framework() -> None:
    """
    停止框架 - 停止当前运行的框架实例

    Example:
        from LStartlet import start_framework, stop_framework

        # 启动框架
        start_framework()

        # 停止框架
        stop_framework()

    Note:
        - 自动触发所有 @Stop 和 @Destroy 装饰的方法
        - 按照优先级顺序执行（数值越小优先级越高）
        - 清理所有已注册的服务
        - 释放所有占用的资源
        - 关闭日志系统
        - 可以多次调用，不会报错
    """
    global _framework_instance
    if _framework_instance:
        _framework_instance._stop()
        _framework_instance = None
