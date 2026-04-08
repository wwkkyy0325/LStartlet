import pytest
from LStartlet import LogFormatter, set_project_root, configure_logger
import logging
import tempfile
import os


@pytest.fixture(autouse=True)
def setup_test_env():
    """为每个测试设置临时项目根目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_root = set_project_root(temp_dir)
        yield temp_dir
        if original_root:
            set_project_root(original_root)


@pytest.mark.logging
class TestLogFormatter:
    """测试LogFormatter功能"""

    def test_log_formatter_creation(self):
        """测试LogFormatter创建"""
        formatter = LogFormatter()
        assert isinstance(formatter, logging.Formatter)

    def test_log_formatter_format(self):
        """测试日志格式化"""
        formatter = LogFormatter()

        # 创建一个模拟的日志记录
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        # 验证格式包含必要元素
        assert "INFO" in formatted
        assert "Test message" in formatted
        assert "test.py" in formatted

    def test_configure_logger_with_formatter(self):
        """测试使用LogFormatter配置logger"""
        from LStartlet import get_project_root

        project_root = get_project_root()  # 获取当前项目根目录
        log_file = os.path.join(project_root, "test.log")
        configure_logger(log_file=log_file, level="DEBUG")

        logger = logging.getLogger("LStartlet")
        assert len(logger.handlers) > 0

        # 检查handler是否使用了LogFormatter
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, LogFormatter)

        # 清理：先关闭所有handler再删除文件
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        # 确保文件可以被删除
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except PermissionError:
                # 在Windows上可能需要稍等一下
                import time

                time.sleep(0.1)
                os.remove(log_file)
