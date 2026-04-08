"""
Tick函数测试 - 验证简化的tick功能
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import get_tick_time, get_tick_ms


def test_tick_functions():
    """测试tick函数"""
    # 测试时间戳函数
    time1 = get_tick_time()
    assert isinstance(time1, float)
    assert time1 > 0

    # 测试毫秒时间戳函数
    ms1 = get_tick_ms()
    assert isinstance(ms1, int)
    assert ms1 > 0

    # 验证毫秒时间戳比秒时间戳更精确
    time2 = get_tick_time()
    ms2 = get_tick_ms()

    # 毫秒时间戳应该大约等于秒时间戳 * 1000
    assert abs(ms2 - int(time2 * 1000)) < 10  # 允许10毫秒的误差


if __name__ == "__main__":
    print("Testing tick functions...")

    test_tick_functions()
    print("✓ Tick functions test passed")

    print("\n✅ All tests passed!")
