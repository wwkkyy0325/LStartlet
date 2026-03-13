"""
自定义异常类定义
为OCR项目提供特定的异常类型，便于错误分类和处理
"""

from typing import Optional, Dict, Any


class OCRError(Exception):
    """OCR基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "OCR_ERROR"
        self.context = context or {}


class OCRInitializationError(OCRError):
    """OCR初始化错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OCR_INIT_ERROR", context)


class OCRProcessingError(OCRError):
    """OCR处理错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OCR_PROCESS_ERROR", context)


class OCRFileError(OCRError):
    """OCR文件操作错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OCR_FILE_ERROR", context)


class OCRConfigError(OCRError):
    """OCR配置错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OCR_CONFIG_ERROR", context)


class OCRNetworkError(OCRError):
    """OCR网络错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OCR_NETWORK_ERROR", context)
