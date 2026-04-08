"""
日志格式化器实现 - 处理日志消息的格式化和颜色输出
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class LogFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 洋红色
        "RESET": "\033[0m",  # 重置
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
        """格式化日志记录，根据配置显示绝对路径或相对路径"""
        full_path = Path(record.pathname)

        if self.project_root_path is None:
            # 使用绝对路径
            path_str = str(full_path).replace("\\", ".").replace("/", ".")
        else:
            # 计算相对于指定项目根目录的相对路径
            try:
                relative_path = full_path.relative_to(self.project_root_path)
                path_str = str(relative_path).replace("\\", ".").replace("/", ".")
            except ValueError:
                # 如果无法计算相对路径（文件不在项目根目录下），回退到绝对路径
                path_str = str(full_path).replace("\\", ".").replace("/", ".")

        log_format = f"%(asctime)s - {self.logger_name} - %(levelname)s - {path_str}:%(lineno)d - %(funcName)s() - %(message)s"
        self._style._fmt = log_format

        log_message = super().format(record)

        if self.use_color:
            level_color = self.COLORS.get(record.levelname, "")
            reset_color = self.COLORS["RESET"]
            log_message = f"{level_color}{log_message}{reset_color}"

        return log_message
