import sys
import inspect
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime
from .level import LogRecord, LogLevel
from .handler import BaseHandler, ConsoleHandler, RotatingFileHandler
# 导入路径管理器
from core.path import get_project_root


class LoggerCore:
    """日志核心逻辑类"""
    
    def __init__(self, name: str = 'root', level: LogLevel = LogLevel.DEBUG):
        self.name = name
        self.level = level
        self.handlers: List[BaseHandler] = []
        self._add_default_handler()
    
    def _add_default_handler(self) -> None:
        """添加默认的控制台处理器"""
        console_handler = ConsoleHandler(level=self.level)
        self.add_handler(console_handler)
    
    def add_handler(self, handler: BaseHandler) -> None:
        """添加日志处理器"""
        if handler not in self.handlers:
            self.handlers.append(handler)
    
    def remove_handler(self, handler: BaseHandler) -> None:
        """移除日志处理器"""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别"""
        self.level = level
    
    def close_handlers(self) -> None:
        """关闭所有日志处理器"""
        for handler in self.handlers[:]:  # 使用切片复制避免修改过程中迭代
            try:
                if hasattr(handler, 'close'):
                    handler.close()  # type: ignore
                self.remove_handler(handler)
            except Exception as e:
                print(f"Error closing logger handler: {e}", file=sys.stderr)
    
    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录日志的核心方法"""
        if level < self.level:
            return
        
        # 获取调用者信息 - 使用inspect.stack()替代私有API
        try:
            # 获取调用栈，跳过当前方法和_log方法本身
            stack = inspect.stack()
            # stack[0] 是当前方法 (_log)
            # stack[1] 是_log的调用者 (debug/info/warning等)
            # stack[2] 是实际的业务代码调用者
            if len(stack) >= 3:
                caller_frame_info = stack[2]
                filename = caller_frame_info.filename
                module_name = self._get_module_name(filename)
                function_name = caller_frame_info.function
                line_number = caller_frame_info.lineno
            else:
                module_name = 'unknown'
                function_name = 'unknown'
                line_number = 0
        except Exception:
            module_name = 'unknown'
            function_name = 'unknown'
            line_number = 0
        
        extra = extra or {}
        record = LogRecord(
            level=level,
            message=str(message),
            timestamp=datetime.now(),
            module=module_name,
            function=function_name,
            line_number=line_number,
            extra=extra
        )
        
        # 发送到所有处理器
        for handler in self.handlers:
            try:
                handler.emit(record)
            except Exception as e:
                # 避免日志系统自身的问题影响主程序
                print(f"Logger handler error: {e}", file=sys.stderr)
    
    def _get_module_name(self, filepath: str) -> str:
        """从文件路径获取模块名"""
        try:
            path = filepath.replace('\\', '/').replace('/', '.')
            if path.endswith('.py'):
                path = path[:-3]
            # 使用路径管理器获取项目根目录
            project_root = get_project_root().replace('\\', '/')
            if not project_root.endswith('/'):
                project_root += '/'
            if path.startswith(project_root):
                path = path[len(project_root):]
            return path.lstrip('.')
        except Exception:
            return 'unknown'
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """调试级别日志"""
        self._log(LogLevel.DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """信息级别日志"""
        self._log(LogLevel.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """警告级别日志"""
        self._log(LogLevel.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """错误级别日志"""
        self._log(LogLevel.ERROR, message, extra)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """严重错误级别日志"""
        self._log(LogLevel.CRITICAL, message, extra)


class MultiProcessLogger:
    """多进程日志管理器"""
    
    def __init__(self):
        self._loggers: Dict[str, LoggerCore] = {}
        self._lock = threading.Lock()
        self._default_process = "main"
    
    def get_logger(self, process_type: str = "main") -> LoggerCore:
        """获取指定进程类型的日志器"""
        with self._lock:
            if process_type not in self._loggers:
                self._loggers[process_type] = LoggerCore(name=f"{process_type}_logger")
            return self._loggers[process_type]
    
    def get_logger_names(self) -> List[str]:
        """获取所有已注册的日志器名称列表"""
        with self._lock:
            return list(self._loggers.keys())
    
    def get_all_loggers(self) -> Dict[str, LoggerCore]:
        """获取所有已注册的日志器字典"""
        with self._lock:
            return self._loggers.copy()
    
    def set_default_process(self, process_type: str) -> None:
        """设置默认进程类型"""
        self._default_process = process_type
    
    def configure_all_loggers(
        self,
        level: LogLevel = LogLevel.DEBUG,
        console: bool = True,
        log_dir: Optional[str] = None,
    ) -> None:
        """配置所有进程类型的日志器"""
        process_types = ["main", "renderer", "extension"]
        
        for proc_type in process_types:
            logger = self.get_logger(proc_type)
            # 设置日志级别
            logger.set_level(level)
            
            # 清除现有处理器
            logger.handlers.clear()
            
            # 添加控制台处理器
            if console:
                logger.add_handler(ConsoleHandler(level=level))
            
            # 添加文件处理器
            if log_dir:
                # 确保日志目录在项目根目录下
                from core.path import join_paths, get_project_root
                if not log_dir.startswith(get_project_root()):
                    log_path = join_paths(get_project_root(), log_dir, "app.log")
                else:
                    log_path = join_paths(log_dir, "app.log")
                file_handler = RotatingFileHandler(
                    filename=log_path,
                    process_type=proc_type,
                    level=level,
                    max_bytes=100 * 1024 * 1024,  # 100MB
                    backup_count=7,  # 保留7天
                    rotate_by_date=True
                )
                logger.add_handler(file_handler)
