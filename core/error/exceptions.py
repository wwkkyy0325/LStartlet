"""
自定义异常类定义
为基础设施框架提供特定的异常类型，便于错误分类和处理
"""

from typing import Optional, Dict, Any


class InfrastructureError(Exception):
    """基础设施基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "INFRA_ERROR"
        self.context = context or {}


class InitializationError(InfrastructureError):
    """初始化错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INIT_ERROR", context)


class ProcessingError(InfrastructureError):
    """处理错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PROCESS_ERROR", context)


class FileError(InfrastructureError):
    """文件操作错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "FILE_ERROR", context)


class ConfigError(InfrastructureError):
    """配置错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", context)


class NetworkError(InfrastructureError):
    """网络错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NETWORK_ERROR", context)