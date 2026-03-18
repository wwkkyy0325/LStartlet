import traceback
from typing import Dict, Any
from datetime import datetime


class ErrorFormatter:
    """错误格式化器 - 负责将异常转换为结构化信息"""
    
    @staticmethod
    def format_error(exception: Exception, include_traceback: bool = True) -> str:
        """
        格式化错误信息
        
        Args:
            exception: 异常对象
            include_traceback: 是否包含完整的堆栈跟踪
            
        Returns:
            格式化的错误字符串
        """
        error_info = ErrorFormatter.get_error_info(exception)
        
        formatted = f"[{error_info['timestamp']}] {error_info['error_type']}: {error_info['message']}"
        
        if error_info.get('error_code'):
            formatted += f" (Error Code: {error_info['error_code']})"
        
        if include_traceback and error_info.get('traceback'):
            formatted += f"\nTraceback:\n{error_info['traceback']}"
        
        return formatted
    
    @staticmethod
    def get_error_info(exception: Exception) -> Dict[str, Any]:
        """
        获取错误详细信息
        
        Args:
            exception: 异常对象
            
        Returns:
            包含错误详细信息的字典
        """
        error_info: Dict[str, Any] = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_type': type(exception).__name__,
            'message': str(exception),
            'traceback': ''.join(traceback.format_tb(exception.__traceback__)) if exception.__traceback__ else '',
        }
        
        # 如果是自定义OCR异常，提取额外信息
        if hasattr(exception, 'error_code'):
            error_info['error_code'] = getattr(exception, 'error_code', None)
        
        if hasattr(exception, 'context'):
            error_info['context'] = getattr(exception, 'context', {})
        
        return error_info
    
    @staticmethod
    def get_simple_error_message(exception: Exception) -> str:
        """
        获取简化的错误消息
        
        Args:
            exception: 异常对象
            
        Returns:
            简化的错误消息字符串
        """
        if hasattr(exception, 'message'):
            return str(getattr(exception, 'message', str(exception)))
        return str(exception)