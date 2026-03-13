#!/usr/bin/env python3
"""
错误处理模块单元测试
测试exceptions、formatter、error_handler等核心功能
"""

import sys
import unittest
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.error import (
    handle_error, format_error, log_error, get_error_info
)
from core.error.exceptions import (
    OCRError, OCRInitializationError, OCRProcessingError,
    OCRFileError, OCRConfigError, OCRNetworkError
)
from core.error.formatter import ErrorFormatter
from core.error.error_handler import ErrorHandler


class TestOCRExceptions(unittest.TestCase):
    """测试OCR自定义异常"""
    
    def test_ocr_error(self):
        """测试基础OCR异常"""
        exc = OCRError("测试错误消息", "TEST_ERROR", {"key": "value"})
        
        self.assertEqual(str(exc), "测试错误消息")
        self.assertEqual(exc.message, "测试错误消息")
        self.assertEqual(exc.error_code, "TEST_ERROR")
        self.assertEqual(exc.context, {"key": "value"})
    
    def test_specific_exceptions(self):
        """测试特定类型的OCR异常"""
        init_error = OCRInitializationError("初始化错误", {"component": "logger"})
        proc_error = OCRProcessingError("处理错误", {"step": "recognition"})
        file_error = OCRFileError("文件错误", {"filename": "test.txt"})
        config_error = OCRConfigError("配置错误", {"setting": "timeout"})
        network_error = OCRNetworkError("网络错误", {"url": "http://example.com"})
        
        self.assertEqual(init_error.error_code, "OCR_INIT_ERROR")
        self.assertEqual(proc_error.error_code, "OCR_PROCESS_ERROR")
        self.assertEqual(file_error.error_code, "OCR_FILE_ERROR")
        self.assertEqual(config_error.error_code, "OCR_CONFIG_ERROR")
        self.assertEqual(network_error.error_code, "OCR_NETWORK_ERROR")


class TestErrorFormatter(unittest.TestCase):
    """测试错误格式化器"""
    
    def test_format_error_with_ocr_exception(self):
        """测试OCR异常的错误格式化"""
        exc = OCRError("测试OCR错误", "TEST_CODE")
        formatted = format_error(exc, include_traceback=False)
        
        # OCR异常应该包含错误码
        self.assertIn("TEST_CODE", formatted)
        self.assertIn("错误码", formatted)
    
    def test_format_error_with_regular_exception(self):
        """测试普通异常的错误格式化"""
        try:
            raise ValueError("测试值错误")
        except ValueError as e:
            formatted = format_error(e, include_traceback=False)
            
            # 普通异常不应该包含"错误码"
            self.assertIn("ValueError", formatted)
            self.assertIn("测试值错误", formatted)
            self.assertNotIn("错误码", formatted)
    
    def test_get_error_info(self):
        """测试获取错误信息"""
        try:
            raise ValueError("测试错误")
        except ValueError as e:
            info = get_error_info(e)
            
            self.assertIn('timestamp', info)
            self.assertIn('error_type', info)
            self.assertIn('message', info)
            self.assertEqual(info['error_type'], 'ValueError')
            self.assertEqual(info['message'], '测试错误')
    
    def test_get_simple_error_message(self):
        """测试获取简化错误消息"""
        exc = OCRError("简化测试消息")
        simple_msg = ErrorFormatter.get_simple_error_message(exc)
        self.assertEqual(simple_msg, "简化测试消息")
        
        # 测试普通异常
        regular_exc = ValueError("普通错误")
        simple_msg = ErrorFormatter.get_simple_error_message(regular_exc)
        self.assertEqual(simple_msg, "普通错误")


class TestErrorHandler(unittest.TestCase):
    """测试错误处理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.handler = ErrorHandler()
    
    def test_handler_initialization(self):
        """测试错误处理器初始化"""
        self.assertEqual(self.handler.get_handler_count(), 0)
        self.assertEqual(self.handler.get_default_context(), {})
    
    def test_add_remove_handler(self):
        """测试添加和移除错误处理回调"""
        def dummy_handler(exception: Exception, context: Optional[Dict[str, Any]]) -> bool:
            return True
        
        self.handler.add_handler(dummy_handler)
        self.assertEqual(self.handler.get_handler_count(), 1)
        
        self.handler.remove_handler(dummy_handler)
        self.assertEqual(self.handler.get_handler_count(), 0)
    
    def test_set_default_context(self):
        """测试设置默认上下文"""
        context = {"app": "ocr", "version": "1.0"}
        self.handler.set_default_context(context)
        self.assertEqual(self.handler.get_default_context(), context)
    
    def test_handle_error(self):
        """测试处理错误"""
        exc = ValueError("处理测试错误")
        result = self.handler.handle_error(exc, {"test": True})
        
        # 应该返回True表示已处理
        self.assertTrue(result)
    
    def test_log_error(self):
        """测试记录错误日志"""
        # 这个方法主要是调用日志系统，不应该抛出异常
        exc = ValueError("日志测试错误")
        self.handler.log_error(exc, {"source": "test"})


class TestGlobalErrorFunctions(unittest.TestCase):
    """测试全局错误处理函数"""
    
    def test_global_functions(self):
        """测试全局错误处理函数"""
        exc = ValueError("全局测试错误")
        
        # 这些函数不应该抛出异常
        formatted = format_error(exc)
        info = get_error_info(exc)
        log_error(exc, {"context": "global_test"})
        handled = handle_error(exc, {"context": "global_test"})
        
        # 验证返回值类型
        self.assertIsInstance(formatted, str)
        self.assertIsInstance(info, dict)
        self.assertIsInstance(handled, bool)


class TestErrorHandlerIntegration(unittest.TestCase):
    """测试错误处理器集成"""
    
    def test_ocr_error_handling(self):
        """测试OCR异常处理"""
        exc = OCRProcessingError("OCR处理失败", {"image": "test.jpg"})
        result = handle_error(exc, {"module": "recognizer"})
        
        self.assertTrue(result)
    
    def test_regular_exception_handling(self):
        """测试普通异常处理"""
        exc = RuntimeError("运行时错误")
        result = handle_error(exc, {"location": "main"})
        
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()