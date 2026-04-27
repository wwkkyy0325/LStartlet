"""
pytest fixture配置文件 - 提供共享的测试设置和工具函数
"""

import sys
from pathlib import Path
import pytest

# 添加src目录到Python路径，确保可以导入项目模块
SRC_PATH = Path(__file__).parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    自动应用的fixture - 为每个测试设置基础环境

    这个fixture会自动清理DI容器，确保测试之间的隔离性
    """
    from LStartlet._di_decorator import _get_di_container

    di_container = _get_di_container()
    # 测试前清理
    di_container._services.clear()
    di_container._components.clear()
    di_container._all_instances.clear()

    yield  # 测试执行点

    # 测试后再次清理（双重保险）
    di_container._services.clear()
    di_container._components.clear()
    di_container._all_instances.clear()


@pytest.fixture
def di_container():
    """提供DI容器实例的fixture"""
    from LStartlet._di_decorator import _get_di_container

    return _get_di_container()


@pytest.fixture
def fresh_di_container():
    """
    提供干净的DI容器实例的fixture

    每次调用都会返回一个清空的容器
    """
    from LStartlet._di_decorator import _get_di_container

    di_container = _get_di_container()
    di_container._services.clear()
    di_container._components.clear()
    di_container._all_instances.clear()

    return di_container


@pytest.fixture
def temp_project_dir(tmp_path):
    """
    创建临时项目目录的fixture

    用于需要文件系统操作的测试
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # 创建基本的项目结构
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()

    return project_dir


def pytest_configure(config):
    """
    pytest配置钩子 - 注册自定义标记
    """
    config.addinivalue_line("markers", "unit: 标记单元测试")
    config.addinivalue_line("markers", "integration: 标记集成测试")
    config.addinivalue_line("markers", "slow: 标记慢速测试")
    config.addinivalue_line("markers", "decorator: 标记装饰器相关测试")
    config.addinivalue_line("markers", "di: 标记依赖注入相关测试")
    config.addinivalue_line("markers", "logging: 标记日志相关测试")


def pytest_collection_modifyitems(config, items):
    """
    测试收集修改钩子 - 可以在这里添加额外的过滤逻辑
    """
    # 目前不需要特殊处理，保留扩展点
    pass
