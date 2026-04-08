"""
测试全局上下文管理器功能
"""

import pytest
from typing import Any
from LStartlet import (
    register_context_variable,
    get_context_value,
    set_context_value,
    reset_context_value,
    reset_all_context,
    get_global_context,
)


def test_basic_context_operations():
    """测试基本的上下文操作"""
    # 注册变量
    register_context_variable("app_name", "LStartlet", str, "应用名称")
    register_context_variable("debug_mode", False, bool, "调试模式")
    register_context_variable("max_workers", 4, int, "最大工作线程数")

    # 获取默认值
    assert get_context_value("app_name") == "LStartlet"
    assert get_context_value("debug_mode") is False
    assert get_context_value("max_workers") == 4

    # 设置新值
    set_context_value("app_name", "TestApp")
    set_context_value("debug_mode", True)
    set_context_value("max_workers", 8)

    # 验证新值
    assert get_context_value("app_name") == "TestApp"
    assert get_context_value("debug_mode") is True
    assert get_context_value("max_workers") == 8

    # 重置单个变量
    reset_context_value("app_name")
    assert get_context_value("app_name") == "LStartlet"

    # 重置所有变量
    reset_all_context()
    assert get_context_value("debug_mode") is False
    assert get_context_value("max_workers") == 4


def test_type_validation():
    """测试类型验证"""
    register_context_variable("strict_int", 0, int, "严格整数")

    # 正确类型
    set_context_value("strict_int", 42)
    assert get_context_value("strict_int") == 42

    # 错误类型
    with pytest.raises(TypeError):
        set_context_value("strict_int", "not_an_int")


def test_custom_validator():
    """测试自定义验证器"""

    def positive_validator(value: int) -> bool:
        return value > 0

    register_context_variable(
        "positive_number", 1, int, "正数", validator=positive_validator
    )

    # 有效值
    set_context_value("positive_number", 5)
    assert get_context_value("positive_number") == 5

    # 无效值
    with pytest.raises(ValueError):
        set_context_value("positive_number", -1)


def test_readonly_variable():
    """测试只读变量"""
    register_context_variable("version", "1.0.0", str, "版本号", readonly=True)

    # 只读变量不能修改
    with pytest.raises(ValueError):
        set_context_value("version", "2.0.0")

    # 只读变量不能重置
    with pytest.raises(ValueError):
        reset_context_value("version")

    # 获取值正常工作
    assert get_context_value("version") == "1.0.0"


def test_temporary_context():
    """测试临时上下文"""
    register_context_variable("temp_var", "original", str, "临时变量测试")

    # 原始值
    assert get_context_value("temp_var") == "original"

    # 临时上下文
    with get_global_context().temporary_context(temp_var="temporary", new_var="new"):
        assert get_context_value("temp_var") == "temporary"
        assert get_context_value("new_var") == "new"

        # 在临时上下文中修改
        set_context_value("temp_var", "modified_in_temp")
        assert get_context_value("temp_var") == "modified_in_temp"

    # 退出后恢复原始值，新变量被删除
    assert get_context_value("temp_var") == "original"
    assert get_context_value("new_var") is None


def test_context_metadata():
    """测试上下文元数据"""
    register_context_variable(
        "metadata_test", "test", str, "元数据测试", readonly=False
    )

    context_manager = get_global_context()
    metadata = context_manager.get_metadata("metadata_test")

    assert metadata is not None
    assert metadata.key == "metadata_test"
    assert metadata.default_value == "test"
    assert metadata.value_type == str
    assert metadata.description == "元数据测试"
    assert metadata.readonly is False


def test_nonexistent_key():
    """测试不存在的键"""
    context_manager = get_global_context()

    # 获取不存在的键返回默认值
    assert get_context_value("nonexistent", "default") == "default"

    # 设置不存在的键抛出异常
    with pytest.raises(ValueError):
        set_context_value("nonexistent", "value")

    # 重置不存在的键抛出异常
    with pytest.raises(ValueError):
        reset_context_value("nonexistent")

    # 检查键存在性
    assert not context_manager.has_key("nonexistent")
    assert "nonexistent" not in context_manager.get_all_keys()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
