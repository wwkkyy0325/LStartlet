#!/usr/bin/env python3
"""
Logger Module Unit Tests
Test core functionality of logger, handler, level, etc.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import (
    debug,
    info,
    warning,
    error,
    critical,
    configure_logger,
    set_process_type,
)
from core.logger.level import LogLevel, LogRecord
from core.logger.handler import ConsoleHandler, RotatingFileHandler
from core.logger.logger import LoggerCore, MultiProcessLogger


class TestLogLevel(unittest.TestCase):
    """测试日志级别枚举"""

    def test_log_level_values(self):
        """测试日志级别的数值"""
        self.assertEqual(LogLevel.DEBUG, 10)
        self.assertEqual(LogLevel.INFO, 20)
        self.assertEqual(LogLevel.WARNING, 30)
        self.assertEqual(LogLevel.ERROR, 40)
        self.assertEqual(LogLevel.CRITICAL, 50)

    def test_log_level_comparison(self):
        """测试日志级别的比较"""
        self.assertTrue(LogLevel.DEBUG < LogLevel.INFO)
        self.assertTrue(LogLevel.INFO < LogLevel.WARNING)
        self.assertTrue(LogLevel.WARNING < LogLevel.ERROR)
        self.assertTrue(LogLevel.ERROR < LogLevel.CRITICAL)


class TestLogRecord(unittest.TestCase):
    """测试日志记录数据结构"""

    def test_log_record_creation(self):
        """测试日志记录创建"""
        from datetime import datetime

        record = LogRecord(
            level=LogLevel.INFO,
            message="test message",
            timestamp=datetime.now(),
            module="test_module",
            function="test_function",
            line_number=42,
            extra={"key": "value"},
        )

        self.assertEqual(record.level, LogLevel.INFO)
        self.assertEqual(record.message, "test message")
        self.assertEqual(record.module, "test_module")
        self.assertEqual(record.function, "test_function")
        self.assertEqual(record.line_number, 42)
        self.assertEqual(record.extra, {"key": "value"})


class TestConsoleHandler(unittest.TestCase):
    """测试控制台处理器"""

    def setUp(self):
        """设置测试环境"""
        self.handler = ConsoleHandler(level=LogLevel.DEBUG)

    def test_handler_initialization(self):
        """测试处理器初始化"""
        self.assertEqual(self.handler.level, LogLevel.DEBUG)
        self.assertTrue(hasattr(self.handler, "_colors"))
        self.assertTrue(hasattr(self.handler, "_level_names"))

    def test_should_emit(self):
        """测试是否应该输出日志"""
        from datetime import datetime

        record = LogRecord(
            level=LogLevel.INFO,
            message="test",
            timestamp=datetime.now(),
            module="test",
            function="test",
            line_number=1,
            extra={},
        )

        # 测试低于级别的记录
        debug_handler = ConsoleHandler(level=LogLevel.INFO)
        debug_record = LogRecord(
            level=LogLevel.DEBUG,
            message="debug",
            timestamp=datetime.now(),
            module="test",
            function="test",
            line_number=1,
            extra={},
        )
        self.assertFalse(debug_handler.should_emit(debug_record))

        # 测试等于级别的记录
        self.assertTrue(self.handler.should_emit(record))

        # 测试高于级别的记录
        error_record = LogRecord(
            level=LogLevel.ERROR,
            message="error",
            timestamp=datetime.now(),
            module="test",
            function="test",
            line_number=1,
            extra={},
        )
        self.assertTrue(self.handler.should_emit(error_record))

    def test_format_record(self):
        """测试日志格式化"""
        from datetime import datetime

        record = LogRecord(
            level=LogLevel.INFO,
            message="测试消息",
            timestamp=datetime(2026, 3, 12, 18, 43, 30),
            module="test_module",
            function="test_function",
            line_number=42,
            extra={},
        )

        formatted = self.handler.format_record(record)
        expected = (
            "[2026-03-12 18:43:30] INFO   | test_module:test_function:42 | 测试消息"
        )
        self.assertEqual(formatted, expected)


class TestRotatingFileHandler(unittest.TestCase):
    """测试文件处理器"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")
        self.handler = RotatingFileHandler(
            filename=self.log_file,
            process_type="main",
            level=LogLevel.DEBUG,
            max_bytes=1024,  # 1KB for testing
            backup_count=2,
            rotate_by_date=False,
        )

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_handler_initialization(self):
        """测试文件处理器初始化"""
        self.assertEqual(self.handler.level, LogLevel.DEBUG)
        self.assertEqual(self.handler.filename, self.log_file)
        self.assertEqual(self.handler.max_bytes, 1024)
        self.assertEqual(self.handler.backup_count, 2)

    def test_write_to_file(self):
        """测试写入文件"""
        from datetime import datetime

        record = LogRecord(
            level=LogLevel.INFO,
            message="文件测试消息",
            timestamp=datetime(2026, 3, 12, 18, 43, 30),
            module="test_module",
            function="test_function",
            line_number=42,
            extra={},
        )

        self.handler.emit(record)

        # 检查文件是否存在并包含正确内容
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        expected = "[2026-03-12 18:43:30.000] [主进程] INFO   | test_module:test_function:42 | 文件测试消息"
        self.assertEqual(content, expected)


class TestLoggerCore(unittest.TestCase):
    """测试日志核心类"""

    def setUp(self):
        """设置测试环境"""
        self.logger = LoggerCore(name="test_logger", level=LogLevel.DEBUG)

    def test_logger_initialization(self):
        """测试日志器初始化"""
        self.assertEqual(self.logger.name, "test_logger")
        self.assertEqual(self.logger.level, LogLevel.DEBUG)
        self.assertEqual(len(self.logger.handlers), 1)  # 默认有一个控制台处理器

    def test_add_remove_handler(self):
        """测试添加和移除处理器"""
        handler = ConsoleHandler(level=LogLevel.INFO)
        self.logger.add_handler(handler)
        self.assertIn(handler, self.logger.handlers)

        self.logger.remove_handler(handler)
        self.assertNotIn(handler, self.logger.handlers)

    def test_set_level(self):
        """测试设置日志级别"""
        self.logger.set_level(LogLevel.WARNING)
        self.assertEqual(self.logger.level, LogLevel.WARNING)


class TestMultiProcessLogger(unittest.TestCase):
    """测试多进程日志管理器"""

    def setUp(self):
        """设置测试环境"""
        self.manager = MultiProcessLogger()

    def test_get_logger(self):
        """测试获取日志器"""
        main_logger = self.manager.get_logger("main")
        renderer_logger = self.manager.get_logger("renderer")

        self.assertIsInstance(main_logger, LoggerCore)
        self.assertIsInstance(renderer_logger, LoggerCore)
        self.assertNotEqual(main_logger, renderer_logger)

    def test_set_default_process(self):
        """测试设置默认进程类型"""
        # 测试设置默认进程类型不会抛出异常
        self.manager.set_default_process("renderer")
        # 不直接检查私有属性，而是通过行为验证
        logger = self.manager.get_logger()
        self.assertIsInstance(logger, LoggerCore)


class TestGlobalLoggerFunctions(unittest.TestCase):
    """测试全局日志函数"""

    def setUp(self):
        """设置测试环境"""
        # 由于无法直接访问私有管理器，我们通过重新配置来确保测试环境干净
        # 这里不进行重置，而是依赖每个测试方法自己的配置
        pass

    def test_configure_logger(self):
        """测试配置日志器"""
        temp_dir = tempfile.mkdtemp()
        try:
            # 先清除可能的环境变量
            if "LOG_PROCESS_TYPE" in os.environ:
                del os.environ["LOG_PROCESS_TYPE"]

            configure_logger(
                level=LogLevel.WARNING,
                console=True,
                log_dir=temp_dir,
                process_type="main",
            )

            # 验证配置后的日志器行为
            # 通过调用日志函数并检查是否有异常来间接验证
            info("配置测试消息")
            # 如果没有异常，则说明配置成功

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if "LOG_PROCESS_TYPE" in os.environ:
                del os.environ["LOG_PROCESS_TYPE"]

    def test_global_log_functions(self):
        """测试全局日志函数"""
        # 这些函数不应该抛出异常
        debug("调试测试")
        info("信息测试")
        warning("警告测试")
        error("错误测试")
        critical("严重测试")

    def test_set_process_type(self):
        """测试设置进程类型"""
        set_process_type("renderer")
        # 验证环境变量被设置
        self.assertEqual(os.environ.get("LOG_PROCESS_TYPE"), "renderer")


if __name__ == "__main__":
    unittest.main()
