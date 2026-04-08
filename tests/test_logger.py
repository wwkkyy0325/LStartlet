"""
极简日志系统测试 - 验证详细信息和彩色输出
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import configure_logger, debug, info, warning, error, critical


def test_default_absolute_path():
    """测试默认绝对路径显示"""
    # 默认使用绝对路径 (project_root_path=None)
    configure_logger(level="INFO", use_color=True)
    info("这应该显示绝对路径")


def test_custom_logger_name():
    """测试自定义logger名称"""
    configure_logger(
        level="INFO", logger_name="MyApp", use_color=True  # 自定义logger名称
    )
    info("这应该显示MyApp作为logger名称")


def test_project_root_path():
    """测试项目根目录路径控制"""
    # 直接传入项目根目录绝对路径
    project_root = str(
        Path(__file__).parent.parent
    )  # f:\workspace-new\python\LStartlet
    configure_logger(
        level="INFO",
        project_root_path=project_root,  # 传入项目根目录绝对路径
        use_color=True,
    )
    info("这应该显示相对于项目根目录的相对路径: tests.test_logger.py")


def test_function_context():
    """测试函数上下文信息"""

    def nested_function():
        info("这条日志应该显示正确的文件名、行号和函数名")

    nested_function()


if __name__ == "__main__":
    print("=== 测试默认绝对路径 ===")
    test_default_absolute_path()

    print("\n=== 测试自定义logger名称 ===")
    test_custom_logger_name()

    print("\n=== 测试项目根目录路径控制 ===")
    test_project_root_path()

    print("\n=== 测试函数上下文 ===")
    test_function_context()

    print("\n✅ 日志系统测试完成！")
    print("💡 使用说明：")
    print("   - project_root_path=None: 显示绝对路径（默认）")
    print("   - project_root_path='/path/to/project': 显示相对于指定根目录的相对路径")
    print("   - logger_name: 自定义日志器名称，默认为'LStartlet'")
