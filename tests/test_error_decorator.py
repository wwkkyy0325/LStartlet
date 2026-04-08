"""
错误处理装饰器测试 - 验证最小化错误处理功能
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import skip_on_error
from LStartlet import configure_logger


def test_skip_on_error_default():
    """测试默认行为的skip_on_error装饰器"""

    @skip_on_error(default_return="default_value")
    def failing_function():
        raise ValueError("This function always fails")

    result = failing_function()
    assert result == "default_value"


def test_skip_on_error_with_warning():
    """测试使用warning级别的skip_on_error装饰器"""

    @skip_on_error(default_return=[], log_level="warning")
    def another_failing_function():
        raise RuntimeError("Another failure")

    result = another_failing_function()
    assert result == []


def test_skip_on_error_with_custom_message():
    """测试自定义错误消息的skip_on_error装饰器"""

    @skip_on_error(
        default_return=None, error_message="Custom error in {func_name}: {error}"
    )
    def custom_failing_function():
        raise Exception("Custom failure")

    result = custom_failing_function()
    assert result is None


def test_skip_on_error_success():
    """测试正常执行的函数不受影响"""

    @skip_on_error(default_return="should_not_be_used")
    def successful_function():
        return "success"

    result = successful_function()
    assert result == "success"


if __name__ == "__main__":
    # 配置日志
    configure_logger(level="WARNING")

    print("Testing skip_on_error decorator...")

    test_skip_on_error_default()
    print("✓ Default behavior test passed")

    test_skip_on_error_with_warning()
    print("✓ Warning level test passed")

    test_skip_on_error_with_custom_message()
    print("✓ Custom message test passed")

    test_skip_on_error_success()
    print("✓ Success case test passed")

    print("\n✅ All tests passed!")
