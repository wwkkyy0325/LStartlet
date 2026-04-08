"""
日志函数实现 - 提供具体的日志记录函数
"""

import logging
import sys
from typing import Optional
from pathlib import Path
from ._log_formatter import LogFormatter


# 全局配置参数
_logger: Optional[logging.Logger] = None
_logger_name: str = "LStartlet"
_project_root_path: Optional[Path] = None  # None表示使用绝对路径


def _setup_logger(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_color: bool = True,
    logger_name: Optional[str] = None,
    project_root_path: Optional[str] = None,
) -> logging.Logger:
    """设置并返回日志实例"""
    global _logger, _logger_name, _project_root_path

    if logger_name is not None:
        _logger_name = logger_name
    _project_root_path = Path(project_root_path) if project_root_path else None

    if _logger is not None:
        # 如果已经配置过，先清理现有的处理器
        _logger.handlers.clear()

    logger = logging.getLogger(_logger_name)
    logger.setLevel(level)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = LogFormatter(
        use_color=use_color,
        logger_name=_logger_name,
        project_root_path=_project_root_path,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        # 使用无颜色但带相对路径的格式化器
        file_formatter = LogFormatter(
            use_color=False,
            logger_name=_logger_name,
            project_root_path=_project_root_path,
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def configure_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_color: bool = True,
    logger_name: Optional[str] = None,
    project_root_path: Optional[str] = None,
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别 ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        log_file: 日志文件路径，如果为None则只输出到控制台
        use_color: 是否启用彩色输出（仅在终端支持时生效）
        logger_name: 自定义日志器名称，默认为"LStartlet"
        project_root_path: 项目根目录的绝对路径，如果为None则使用绝对路径显示
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    log_level = level_map.get(level.upper(), logging.INFO)
    _setup_logger(log_level, log_file, use_color, logger_name, project_root_path)


def _get_logger() -> logging.Logger:
    """获取日志实例，如果未配置则使用默认配置"""
    global _logger
    if _logger is None:
        _logger = _setup_logger()
    return _logger


def log_debug(message: str) -> None:
    """调试级别日志"""
    _get_logger().debug(message, stacklevel=2)


def log_info(message: str) -> None:
    """信息级别日志"""
    _get_logger().info(message, stacklevel=2)


def log_warning(message: str) -> None:
    """警告级别日志"""
    _get_logger().warning(message, stacklevel=2)


def log_error(message: str) -> None:
    """错误级别日志"""
    _get_logger().error(message, stacklevel=2)


def log_critical(message: str) -> None:
    """严重错误级别日志"""
    _get_logger().critical(message, stacklevel=2)


# 兼容性导出（符合测试期望的名称）
debug = log_debug
info = log_info
warning = log_warning
error = log_error
critical = log_critical
configure_logger = configure_logging
