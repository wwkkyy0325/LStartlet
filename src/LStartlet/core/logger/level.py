from enum import IntEnum
from typing import NamedTuple, Dict, Any
from datetime import datetime


class LogLevel(IntEnum):
    """日志级别枚举"""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogRecord(NamedTuple):
    """日志记录数据结构"""

    level: LogLevel
    message: str
    timestamp: datetime
    module: str
    function: str
    line_number: int
    extra: Dict[str, Any]
