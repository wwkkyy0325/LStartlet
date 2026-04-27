"""
日志系统实现 - 完整的日志管理功能
包括日志格式化器、日志函数和错误处理装饰器
完全自动化：自动写入终端和文件，自动按天拆分日志
支持多应用日志和框架日志分离
"""

import logging
import logging.handlers
import sys
from functools import wraps
from pathlib import Path
from typing import Optional, Dict, Any, Callable


# ==================== 日志格式化器 ====================


class _LogFormatter(logging.Formatter):
    """彩色日志格式化器（内部实现）"""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "RESET": "\033[0m",
    }

    def __init__(
        self,
        use_color: bool = True,
        logger_name: str = "LStartlet",
        project_root_path: Optional[Path] = None,
    ):
        self.use_color = use_color
        self.logger_name = logger_name
        self.project_root_path = project_root_path
        super().__init__("", datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record):
        """格式化日志记录"""
        full_path = Path(record.pathname)

        if self.project_root_path is None:
            path_str = str(full_path).replace("\\", ".").replace("/", ".")
        else:
            try:
                relative_path = full_path.relative_to(self.project_root_path)
                path_str = str(relative_path).replace("\\", ".").replace("/", ".")
            except ValueError:
                path_str = str(full_path).replace("\\", ".").replace("/", ".")

        log_format = f"%(asctime)s - {self.logger_name} - %(levelname)s - {path_str}:%(lineno)d - %(funcName)s() - %(message)s"
        self._style._fmt = log_format

        log_message = super().format(record)

        if self.use_color:
            level_color = self.COLORS.get(record.levelname, "")
            reset_color = self.COLORS["RESET"]
            log_message = f"{level_color}{log_message}{reset_color}"

        return log_message


# ==================== 日志函数 ====================

# 全局配置参数
_loggers: Dict[str, logging.Logger] = {}  # 存储所有日志器
_framework_logger: Optional[logging.Logger] = None  # 框架日志器

# 从 _application_info 导入统一的 _get_current_app_name 函数
# 注意：这个导入放在这里是为了避免循环导入
_get_current_app_name = None


def _ensure_get_current_app_name():
    """确保 _get_current_app_name 函数已导入"""
    global _get_current_app_name
    if _get_current_app_name is None:
        from ._application_info import _get_current_app_name as _get_app_name

        _get_current_app_name = _get_app_name


def _get_framework_log_directory() -> str:
    """获取框架日志目录路径"""
    from ._path_manager import _get_user_config_root

    return str(Path(_get_user_config_root()) / "logs")


def _get_app_log_directory(app_name: str) -> str:
    """获取应用日志目录路径"""
    from ._path_manager import _get_user_config_root

    return str(Path(_get_user_config_root()) / app_name / "logs")


def _setup_logger(
    logger_name: str,
    console_level: int = logging.INFO,
    file_level: int = logging.INFO,
    log_directory: Optional[str] = None,
) -> logging.Logger:
    """设置并返回日志实例"""
    global _loggers

    if logger_name in _loggers:
        return _loggers[logger_name]

    logger = logging.getLogger(logger_name)
    logger.setLevel(min(console_level, file_level))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = _LogFormatter(
        use_color=True,
        logger_name=logger_name,
        project_root_path=None,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_directory is None:
        if logger_name == "LStartlet":
            log_directory = _get_framework_log_directory()
        else:
            log_directory = _get_app_log_directory(logger_name)

    Path(log_directory).mkdir(parents=True, exist_ok=True)

    log_file = Path(log_directory) / f"{logger_name.lower()}.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_formatter = _LogFormatter(
        use_color=False,
        logger_name=logger_name,
        project_root_path=None,
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    _loggers[logger_name] = logger
    return logger


def _configure_logging(
    console_level: str = "INFO",
    file_level: str = "DEBUG",
) -> None:
    """配置日志系统（内部函数）"""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    console_log_level = level_map.get(console_level.upper(), logging.INFO)
    file_log_level = level_map.get(file_level.upper(), logging.DEBUG)

    _setup_logger("LStartlet", console_log_level, file_log_level)

    _ensure_get_current_app_name()
    assert (
        _get_current_app_name is not None
    ), "_get_current_app_name should be imported by _ensure_get_current_app_name"
    app_name = _get_current_app_name()
    if app_name:
        _setup_logger(app_name, console_log_level, file_log_level)


def _get_framework_logger() -> logging.Logger:
    """获取框架日志实例"""
    global _framework_logger
    if _framework_logger is None:
        _framework_logger = _setup_logger("LStartlet")
    return _framework_logger


def _get_app_logger() -> logging.Logger:
    """获取应用日志实例"""
    _ensure_get_current_app_name()
    assert (
        _get_current_app_name is not None
    ), "_get_current_app_name should be imported by _ensure_get_current_app_name"
    app_name = _get_current_app_name()
    if app_name is None:
        return _get_framework_logger()

    if app_name not in _loggers:
        _setup_logger(app_name)

    return _loggers[app_name]


def _log_framework_debug(message: str) -> None:
    """框架调试级别日志（内部方法）"""
    _get_framework_logger().debug(message, stacklevel=2)


def _log_framework_info(message: str) -> None:
    """框架信息级别日志（内部方法）"""
    _get_framework_logger().info(message, stacklevel=2)


def _log_framework_warning(message: str) -> None:
    """框架警告级别日志（内部方法）"""
    _get_framework_logger().warning(message, stacklevel=2)


def _log_framework_error(message: str) -> None:
    """框架错误级别日志（内部方法）"""
    _get_framework_logger().error(message, stacklevel=2)


def _log_framework_critical(message: str) -> None:
    """框架严重错误级别日志（内部方法）"""
    _get_framework_logger().critical(message, stacklevel=2)


# 应用日志函数（标准API）
def debug(message: str) -> None:
    """
    调试级别日志 - 记录详细的调试信息

    Args:
        message: 日志消息

    Example:
        from LStartlet import debug

        debug("初始化数据库连接")
        debug(f"用户ID: {user_id}")

    Note:
        - DEBUG 级别日志通常只在开发和调试时使用
        - 日志会同时输出到终端和文件
        - 终端使用彩色输出，文件使用纯文本
        - 日志文件按天自动拆分，保留30天
    """
    _get_app_logger().debug(message, stacklevel=2)


def info(message: str) -> None:
    """
    信息级别日志 - 记录一般信息

    Args:
        message: 日志消息

    Example:
        from LStartlet import info

        info("应用启动")
        info("处理用户请求")

    Note:
        - INFO 级别日志用于记录正常运行状态
        - 日志会同时输出到终端和文件
        - 终端使用彩色输出，文件使用纯文本
        - 日志文件按天自动拆分，保留30天
    """
    _get_app_logger().info(message, stacklevel=2)


def warning(message: str) -> None:
    """
    警告级别日志 - 记录警告信息

    Args:
        message: 日志消息

    Example:
        from LStartlet import warning

        warning("配置文件使用默认值")
        warning("连接池接近上限")

    Note:
        - WARNING 级别日志用于记录潜在问题
        - 日志会同时输出到终端和文件
        - 终端使用彩色输出，文件使用纯文本
        - 日志文件按天自动拆分，保留30天
    """
    _get_app_logger().warning(message, stacklevel=2)


def error(message: str) -> None:
    """
    错误级别日志 - 记录错误信息

    Args:
        message: 日志消息

    Example:
        from LStartlet import error

        error("数据库连接失败")
        error(f"处理请求失败: {error_message}")

    Note:
        - ERROR 级别日志用于记录错误但程序仍可继续运行
        - 日志会同时输出到终端和文件
        - 终端使用彩色输出，文件使用纯文本
        - 日志文件按天自动拆分，保留30天
    """
    _get_app_logger().error(message, stacklevel=2)


def critical(message: str) -> None:
    """
    严重错误级别日志 - 记录严重错误

    Args:
        message: 日志消息

    Example:
        from LStartlet import critical

        critical("系统崩溃")
        critical("无法恢复的严重错误")

    Note:
        - CRITICAL 级别日志用于记录严重错误，可能导致程序终止
        - 日志会同时输出到终端和文件
        - 终端使用彩色输出，文件使用纯文本
        - 日志文件按天自动拆分，保留30天
    """
    _get_app_logger().critical(message, stacklevel=2)
