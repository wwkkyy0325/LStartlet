import sys # type: ignore
from typing import Optional, Dict, Any
from .logger import MultiProcessLogger, LoggerCore
from .level import LogLevel
from .handler import ConsoleHandler, RotatingFileHandler
import atexit
import os


# 全局多进程logger管理器
_logger_manager: Optional[MultiProcessLogger] = None


def _get_project_root() -> str:
    """获取项目根目录"""
    # 使用当前文件的路径向上查找
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # core/logger/ -> core/ -> project root
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return project_root


def _join_paths(base_path: str, *paths: str) -> str:
    """连接路径"""
    return os.path.join(base_path, *paths)


__all__ = [
    'debug',
    'info', 
    'warning',
    'error',
    'critical',
    'configure_logger',
    'set_process_type',
    'LogLevel',
    'ConsoleHandler',
    'RotatingFileHandler',
    'MultiProcessLogger',
    'LoggerCore'
]


def _get_logger_manager() -> MultiProcessLogger:
    """获取全局logger管理器"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = MultiProcessLogger()
        # 注册应用程序生命周期事件监听器
        _register_lifecycle_listeners()
    return _logger_manager


def _register_lifecycle_listeners() -> None:
    """注册应用程序生命周期事件监听器"""
    try:
        from core.event.event_bus import EventBus
        from core.event.events.scheduler_events import ApplicationLifecycleEvent
        
        def _on_application_lifecycle_event(event: Any) -> bool:
            """处理应用程序生命周期事件"""
            try:
                if hasattr(event, 'lifecycle_stage'):
                    if event.lifecycle_stage in ("stopping", "stopped"):
                        # 关闭所有日志处理器
                        manager = _get_logger_manager()
                        all_loggers = manager.get_all_loggers()
                        for logger in all_loggers.values():
                            logger.close_handlers()
                        info("日志管理器：所有日志处理器已关闭")
                return True
            except Exception as e:
                # 确保sys可用
                import sys
                print(f"Error in logger lifecycle handler: {e}", file=sys.stderr)
                return False
        
        event_bus = EventBus()
        event_bus.subscribe_lambda(
            ApplicationLifecycleEvent.EVENT_TYPE,
            _on_application_lifecycle_event,
            "logger_lifecycle_handler"
        )
        
    except ImportError:
        # 如果事件系统不可用，跳过事件监听器注册
        pass
    except Exception as e:
        # 确保sys可用
        import sys
        print(f"Failed to register logger lifecycle listeners: {e}", file=sys.stderr)


def _get_current_logger() -> LoggerCore:
    """获取当前进程的日志器"""
    try:
        manager = _get_logger_manager()
        # 这里可以根据实际的进程环境自动检测进程类型
        # 为了简化，我们使用环境变量或默认为主进程
        process_type = os.getenv('LOG_PROCESS_TYPE', 'main')
        return manager.get_logger(process_type)
    except Exception as e:
        # 如果获取日志器失败，创建一个简单的备用日志器
        import sys
        print(f"Warning: Failed to get logger, using fallback: {e}", file=sys.stderr)
        # 返回一个简单的日志器实例，避免完全失败
        fallback_logger = LoggerCore(name="fallback", level=LogLevel.WARNING)
        return fallback_logger


def configure_logger(
    level: LogLevel = LogLevel.DEBUG,
    console: bool = True,
    log_dir: Optional[str] = None,
    process_type: Optional[str] = None
) -> None:
    """
    配置logger
    
    Args:
        level: 日志级别
        console: 是否启用控制台输出
        log_dir: 日志目录路径，如果为None则不启用文件输出
        process_type: 进程类型 ("main", "renderer", "extension")，如果为None则配置所有进程类型
    """
    manager = _get_logger_manager()
    
    # 如果没有指定日志目录，使用项目根目录下的logs目录
    if log_dir is None:
        log_dir = _join_paths(_get_project_root(), 'logs')
    
    if process_type is None:
        # 配置所有进程类型
        manager.configure_all_loggers(
            level=level,
            console=console,
            log_dir=log_dir
        )
    else:
        # 配置特定进程类型
        logger = manager.get_logger(process_type)
        logger.set_level(level)
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 添加控制台处理器
        if console:
            logger.add_handler(ConsoleHandler(level=level))
        
        # 添加文件处理器
        if log_dir:
            log_path = _join_paths(log_dir, "app.log")
            file_handler = RotatingFileHandler(
                filename=log_path,
                process_type=process_type,
                level=level,
                max_bytes=100 * 1024 * 1024,  # 100MB
                backup_count=7,  # 保留7天
                rotate_by_date=True
            )
            logger.add_handler(file_handler)


def set_process_type(process_type: str) -> None:
    """
    设置当前进程类型
    
    Args:
        process_type: 进程类型 ("main", "renderer", "extension")
    """
    os.environ['LOG_PROCESS_TYPE'] = process_type
    manager = _get_logger_manager()
    manager.set_default_process(process_type)


# 暴露日志方法（自动根据当前进程类型选择日志器）
def debug(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """调试级别日志"""
    _get_current_logger().debug(message, extra)


def info(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """信息级别日志"""
    _get_current_logger().info(message, extra)


def warning(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """警告级别日志"""
    _get_current_logger().warning(message, extra)


def error(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """错误级别日志"""
    _get_current_logger().error(message, extra)


def critical(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """严重错误级别日志"""
    _get_current_logger().critical(message, extra)


# 移除顶层的configure_logger()调用，避免模块导入时立即执行初始化
# 根据项目规范，日志配置应在主程序入口统一执行

# 注册退出清理
def _cleanup():
    """清理资源"""
    global _logger_manager
    _logger_manager = None

atexit.register(_cleanup)