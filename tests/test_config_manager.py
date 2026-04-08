"""
简化配置管理器测试 - 验证超级简化的配置管理功能
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import (
    register_config,
    get_config,
    set_config,
    has_config,
    get_all_configs,
    reset_config,
    reset_all_configs,
    load_config,
    save_config,
    load_project_config,
    save_project_config,
)


def test_basic_config_operations():
    """测试基本配置操作"""
    # 清理配置状态
    reset_all_configs()

    # 注册配置项
    register_config("app.name", "MyApp", str, "Application name")
    register_config("app.version", "1.0.0", str, "Application version")
    register_config("server.port", 8080, int, "Server port")
    register_config("debug.enabled", False, bool, "Debug mode")

    # 测试获取配置
    assert get_config("app.name") == "MyApp"
    assert get_config("server.port") == 8080
    assert get_config("debug.enabled") is False

    # 测试设置配置
    assert set_config("app.name", "NewApp")
    assert get_config("app.name") == "NewApp"

    # 测试类型转换
    assert set_config("server.port", "9090")  # 字符串转整数
    assert get_config("server.port") == 9090

    assert set_config("debug.enabled", "true")  # 字符串转布尔值
    assert get_config("debug.enabled") is True

    # 测试不存在的配置
    assert get_config("nonexistent", "default") == "default"
    assert not has_config("nonexistent")

    # 测试配置存在性
    assert has_config("app.name")


def test_config_validation():
    """测试配置验证"""

    # 注册带验证器的配置
    def validate_port(port):
        return 1 <= port <= 65535

    register_config("valid.port", 8080, int, "Valid port", validate_port)

    # 有效值
    assert set_config("valid.port", 3000)
    assert get_config("valid.port") == 3000

    # 无效值
    assert not set_config("valid.port", 70000)  # 超出范围

    # 类型错误
    assert not set_config("valid.port", "invalid")  # 无法转换为整数


def test_config_reset():
    """测试配置重置"""
    register_config("test.reset", "original", str, "Test reset")

    # 修改配置
    set_config("test.reset", "modified")
    assert get_config("test.reset") == "modified"

    # 重置单个配置
    reset_config("test.reset")
    assert get_config("test.reset") == "original"

    # 修改多个配置
    set_config("app.name", "TempApp")
    set_config("server.port", 9999)

    # 重置所有配置
    reset_all_configs()
    assert get_config("app.name") == "MyApp"  # 回到注册时的默认值
    assert get_config("server.port") == 8080


def test_file_operations():
    """测试文件操作"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = os.path.join(temp_dir, "test_config.yaml")

        # 注册配置项以便重置
        register_config("file.test", "default_value", str, "Test file config")
        register_config(
            "nested.config.value", "default_nested", str, "Test nested config"
        )

        # 设置一些配置
        set_config("file.test", "value1")
        set_config("nested.config.value", "value2")

        # 保存到文件
        assert save_config(config_file)
        assert os.path.exists(config_file)

        # 重置配置到默认值
        reset_all_configs()
        assert get_config("file.test") == "default_value"

        # 从文件加载
        assert load_config(config_file)
        assert get_config("file.test") == "value1"
        assert get_config("nested.config.value") == "value2"


def test_get_all_configs():
    """测试获取所有配置"""
    all_configs = get_all_configs()
    assert isinstance(all_configs, dict)
    assert "app.name" in all_configs
    assert "server.port" in all_configs


if __name__ == "__main__":
    print("Testing simplified config manager...")

    test_basic_config_operations()
    print("✓ Basic config operations test passed")

    test_config_validation()
    print("✓ Config validation test passed")

    test_config_reset()
    print("✓ Config reset test passed")

    test_file_operations()
    print("✓ File operations test passed")

    test_get_all_configs()
    print("✓ Get all configs test passed")

    print("\n✅ All tests passed!")
