"""
简化路径管理器测试 - 验证超级简化的路径管理功能
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import (
    set_project_root,
    get_project_root,
    join_paths,
    ensure_directory_exists,
    get_core_path,
    get_logger_path,
    get_data_path,
    get_config_path,
    get_logs_path,
)


def test_basic_functionality():
    """测试基本功能"""
    # 设置一个已知存在的目录作为项目根目录进行测试
    test_root = str(Path(__file__).parent)
    original_root = set_project_root(test_root)

    # 现在测试应该通过
    current_root = get_project_root()
    assert os.path.exists(current_root)
    assert current_root == str(Path(test_root).resolve())

    # 测试路径拼接
    config_path = join_paths(get_project_root(), "config", "app.conf")
    expected = str(Path(test_root) / "config" / "app.conf")
    assert config_path == str(Path(expected).resolve())

    # 恢复原始根目录
    if original_root:
        set_project_root(original_root)


def test_ensure_directory_exists():
    """测试目录创建功能"""
    test_dir = str(Path(get_project_root()) / "test_temp_dir")
    result = ensure_directory_exists(test_dir)
    assert os.path.exists(result)
    assert result == str(Path(test_dir).resolve())

    # 清理测试目录
    os.rmdir(test_dir)


def test_get_path_functions():
    """测试各种get_path函数"""
    root = get_project_root()

    # 测试核心路径
    core_path = get_core_path()
    assert "src" in core_path and "LStartlet" in core_path and "core" in core_path

    # 测试日志路径
    logger_path = get_logger_path()
    assert "src" in logger_path and "logger" in logger_path

    # 测试数据、配置、日志目录
    data_path = get_data_path()
    config_path = get_config_path()
    logs_path = get_logs_path()

    assert data_path == str(Path(root) / "data")
    assert config_path == str(Path(root) / "config")
    assert logs_path == str(Path(root) / "logs")


def test_error_handling():
    """测试错误处理"""
    try:
        set_project_root("/nonexistent/path")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "does not exist" in str(e)


if __name__ == "__main__":
    print("Testing simplified path manager...")

    test_basic_functionality()
    print("✓ Basic functionality test passed")

    test_ensure_directory_exists()
    print("✓ Directory creation test passed")

    test_get_path_functions()
    print("✓ Get path functions test passed")

    test_error_handling()
    print("✓ Error handling test passed")

    print("\n✅ All tests passed!")
