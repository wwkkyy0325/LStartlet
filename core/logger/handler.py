import sys
import shutil
import os
from datetime import datetime, timedelta
from .level import LogRecord, LogLevel
# 导入路径管理器
from core.path import ensure_directory_exists, normalize_path


class BaseHandler:
    """日志处理器基类"""
    
    def __init__(self, level: LogLevel = LogLevel.DEBUG):
        self.level = level
    
    def emit(self, record: LogRecord) -> None:
        """输出日志记录"""
        raise NotImplementedError
    
    def should_emit(self, record: LogRecord) -> bool:
        """判断是否应该输出该日志记录"""
        return record.level >= self.level
    
    def close(self) -> None:
        """关闭处理器，释放资源"""
        pass


class ConsoleHandler(BaseHandler):
    """控制台日志处理器"""
    
    def __init__(self, level: LogLevel = LogLevel.DEBUG, use_color: bool = True):
        super().__init__(level)
        self.use_color = use_color
        self._colors = {
            LogLevel.DEBUG: '\033[36m',    # 青色
            LogLevel.INFO: '\033[32m',     # 绿色
            LogLevel.WARNING: '\033[33m',  # 黄色
            LogLevel.ERROR: '\033[31m',    # 红色
            LogLevel.CRITICAL: '\033[35m', # 紫色
        }
        self._reset_color = '\033[0m'
        # 中文日志级别映射
        self._level_names = {
            LogLevel.DEBUG: '调试',
            LogLevel.INFO: '信息',
            LogLevel.WARNING: '警告',
            LogLevel.ERROR: '错误',
            LogLevel.CRITICAL: '严重',
        }
    
    def emit(self, record: LogRecord) -> None:
        if not self.should_emit(record):
            return
        
        message = self.format_record(record)
        if self.use_color and sys.stdout.isatty():
            color = self._colors.get(record.level, '')
            message = f"{color}{message}{self._reset_color}"
        
        print(message, file=sys.stdout if record.level < LogLevel.ERROR else sys.stderr)
    
    def format_record(self, record: LogRecord) -> str:
        """格式化日志记录"""
        timestamp = record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        level_name = self._level_names.get(record.level, record.level.name)
        return f"[{timestamp}] {level_name:6} | {record.module}:{record.function}:{record.line_number} | {record.message}"


class RotatingFileHandler(BaseHandler):
    """增强的文件日志处理器，支持多进程隔离、按大小和按日期轮转"""
    
    def __init__(
        self, 
        filename: str, 
        process_type: str = "main",  # "main", "renderer", "extension"
        level: LogLevel = LogLevel.DEBUG, 
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 7,  # 保留7天
        rotate_by_date: bool = True
    ):
        super().__init__(level)
        self.process_type = process_type
        # 使用路径管理器标准化路径
        self.base_filename = normalize_path(filename)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.rotate_by_date = rotate_by_date
        # 使用路径管理器确保目录存在
        log_dir = os.path.dirname(self.base_filename) or '.'
        ensure_directory_exists(log_dir)
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 为不同进程类型创建不同的日志文件
        self.filename = self._get_process_specific_filename()
        # 中文日志级别映射
        self._level_names = {
            LogLevel.DEBUG: '调试',
            LogLevel.INFO: '信息',
            LogLevel.WARNING: '警告',
            LogLevel.ERROR: '错误',
            LogLevel.CRITICAL: '严重',
        }
        # 进程类型中文映射
        self._process_names = {
            "main": "主进程",
            "renderer": "渲染进程", 
            "extension": "扩展进程"
        }
    
    def _get_process_specific_filename(self) -> str:
        """根据进程类型获取特定的日志文件名"""
        if self.process_type == "main":
            return self.base_filename
        elif self.process_type == "renderer":
            if self.base_filename.endswith('.log'):
                return self.base_filename[:-4] + '_renderer.log'
            else:
                return self.base_filename + '_renderer'
        elif self.process_type == "extension":
            if self.base_filename.endswith('.log'):
                return self.base_filename[:-4] + '_extension.log'
            else:
                return self.base_filename + '_extension'
        else:
            if self.base_filename.endswith('.log'):
                return self.base_filename[:-4] + f'_{self.process_type}.log'
            else:
                return self.base_filename + f'_{self.process_type}'
    
    def emit(self, record: LogRecord) -> None:
        if not self.should_emit(record):
            return
        
        # 检查是否需要按日期轮转
        if self.rotate_by_date:
            current_date = datetime.now().strftime('%Y-%m-%d')
            if current_date != self.current_date:
                self._rotate_by_date()
                self.current_date = current_date
                self.filename = self._get_process_specific_filename()
        
        message = self.format_record(record)
        self._write_to_file(message)
    
    def format_record(self, record: LogRecord) -> str:
        """格式化日志记录"""
        timestamp = record.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level_name = self._level_names.get(record.level, record.level.name)
        process_name = self._process_names.get(self.process_type, self.process_type)
        process_info = f"[{process_name}]"
        return f"[{timestamp}] {process_info} {level_name:6} | {record.module}:{record.function}:{record.line_number} | {record.message}"
    
    def _write_to_file(self, message: str) -> None:
        """写入文件，支持轮转"""
        try:
            # 检查文件大小是否超过限制
            if os.path.exists(self.filename) and os.path.getsize(self.filename) >= self.max_bytes:
                self._rotate_by_size()
            
            # 使用路径管理器确保目录存在
            log_dir = os.path.dirname(self.filename) or '.'
            ensure_directory_exists(log_dir)
            
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
                
        except Exception as e:
            # 记录到stderr，避免影响主程序
            print(f"文件处理器写入错误: {e}", file=sys.stderr)
    
    
    def _rotate_by_size(self) -> None:
        """按大小轮转日志文件"""
        # 创建带时间戳的备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if self.filename.endswith('.log'):
            backup_name = self.filename[:-4] + f'_{timestamp}.log'
        else:
            backup_name = self.filename + f'_{timestamp}'
        
        try:
            if os.path.exists(self.filename):
                shutil.move(self.filename, backup_name)
        except Exception as e:
            print(f"文件轮转错误: {e}", file=sys.stderr)
        
        # 清理旧的备份文件
        self._cleanup_old_files()
    
    def _rotate_by_date(self) -> None:
        """按日期轮转日志文件"""
        if os.path.exists(self.filename):
            # 创建带日期的备份文件名
            date_str = self.current_date.replace('-', '')
            if self.filename.endswith('.log'):
                backup_name = self.filename[:-4] + f'_{date_str}.log'
            else:
                backup_name = self.filename + f'_{date_str}'
            
            try:
                shutil.move(self.filename, backup_name)
            except Exception as e:
                print(f"日期轮转错误: {e}", file=sys.stderr)
        
        # 清理旧的备份文件
        self._cleanup_old_files()
    
    def _cleanup_old_files(self) -> None:
        """清理超过保留天数的日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.backup_count)
            log_dir = os.path.dirname(self.filename) or '.'
            base_name = os.path.basename(self.filename)
            if base_name.endswith('.log'):
                base_stem = base_name[:-4]
            else:
                base_stem = base_name
                
            # 获取所有可能的备份文件
            for filename in os.listdir(log_dir):
                if filename.startswith(base_stem + '_') and filename.endswith('.log'):
                    # 尝试解析文件名中的日期
                    suffix = filename[len(base_stem)+1:-4]  # 移除基础名和.log
                    if '_' in suffix:
                        # 时间戳格式 YYYYMMDD_HHMMSS
                        date_part = suffix.split('_')[0]
                    else:
                        # 日期格式 YYYYMMDD
                        date_part = suffix
                        
                    if len(date_part) == 8 and date_part.isdigit():
                        try:
                            file_date = datetime.strptime(date_part, '%Y%m%d')
                            if file_date < cutoff_date:
                                os.remove(os.path.join(log_dir, filename))
                        except ValueError:
                            continue
        except Exception as e:
            print(f"清理错误: {e}", file=sys.stderr)