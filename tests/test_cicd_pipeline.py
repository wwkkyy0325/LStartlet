"""
CI/CD流水线测试 - 验证极简CI/CD功能
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import cicd_step, run_cicd_pipeline


def test_cicd_pipeline():
    """测试CI/CD流水线装饰器和执行"""

    # 重置全局状态（用于测试）
    from LStartlet._cicd_decorator import _cicd_pipeline

    _cicd_pipeline.steps.clear()

    # 定义测试步骤
    step1_executed = False
    step2_executed = False

    @cicd_step("test_step_1", order=1)
    def test_step_1():
        nonlocal step1_executed
        step1_executed = True
        return True

    @cicd_step("test_step_2", order=2)
    def test_step_2():
        nonlocal step2_executed
        step2_executed = True
        return True

    # 验证步骤已注册
    assert len(_cicd_pipeline.steps) == 2
    assert _cicd_pipeline.steps[0].name == "test_step_1"
    assert _cicd_pipeline.steps[1].name == "test_step_2"

    # 执行流水线
    success = run_cicd_pipeline()

    assert success is True
    assert step1_executed is True
    assert step2_executed is True


def test_cicd_pipeline_failure():
    """测试CI/CD流水线失败情况"""

    # 重置全局状态
    from LStartlet._cicd_decorator import _cicd_pipeline

    _cicd_pipeline.steps.clear()

    @cicd_step("failing_step", order=1)
    def failing_step():
        return False  # 模拟失败

    @cicd_step("should_not_run", order=2)
    def should_not_run():
        raise Exception("This should not be executed")

    # 执行流水线
    success = run_cicd_pipeline()

    assert success is False


if __name__ == "__main__":
    print("Testing CI/CD pipeline...")

    test_cicd_pipeline()
    print("✓ CI/CD pipeline basic test passed")

    test_cicd_pipeline_failure()
    print("✓ CI/CD pipeline failure test passed")

    print("\n✅ All tests passed!")
