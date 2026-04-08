"""
系统配置函数测试 - 验证简化的系统配置功能
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import register_config, get_system_config


def test_system_config_function():
    """测试系统配置函数"""
    # 注册系统配置项
    register_config(
        "system.monitoring.enabled", True, bool, "System monitoring enabled"
    )
    register_config(
        "system.cleanup.threshold_days", 30, int, "Cleanup threshold in days"
    )

    # 测试获取系统配置
    monitoring_enabled = get_system_config("monitoring.enabled", False)
    assert monitoring_enabled is True

    cleanup_threshold = get_system_config("cleanup.threshold_days", 7)
    assert cleanup_threshold == 30

    # 测试默认值
    non_existent = get_system_config("nonexistent.setting", "default_value")
    assert non_existent == "default_value"


if __name__ == "__main__":
    print("Testing system config function...")

    test_system_config_function()
    print("✓ System config function test passed")

    print("\n✅ All tests passed!")
