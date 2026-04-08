"""
测试 scope 参数替代 singleton 参数
"""

import pytest
from LStartlet import Component, Plugin, PluginBase, get_di_container


def cleanup_test_state():
    """清理测试状态"""
    di_container = get_di_container()
    di_container._services.clear()
    di_container._components.clear()
    di_container._plugins.clear()


def test_scope_parameter_singleton():
    """测试 scope='singleton' 参数"""
    cleanup_test_state()

    @Component(scope="singleton")
    class SingletonService:
        def __init__(self):
            self.value = 0

    di_container = get_di_container()

    # 解析两次，应该是同一个实例
    instance1 = di_container.resolve(SingletonService)
    instance2 = di_container.resolve(SingletonService)

    assert instance1 is instance2
    instance1.value = 42
    assert instance2.value == 42


def test_scope_parameter_transient():
    """测试 scope='transient' 参数"""
    cleanup_test_state()

    @Component(scope="transient")
    class TransientService:
        def __init__(self):
            self.value = 0

    di_container = get_di_container()

    # 解析两次，应该是不同的实例
    instance1 = di_container.resolve(TransientService)
    instance2 = di_container.resolve(TransientService)

    assert instance1 is not instance2
    instance1.value = 42
    assert instance2.value == 0


def test_scope_parameter_with_name():
    """测试带名称的 scope 参数"""
    cleanup_test_state()

    @Component("named_service", scope="transient")
    class NamedService:
        def __init__(self):
            self.value = 0

    di_container = get_di_container()

    # 验证组件已注册
    assert "named_service" in di_container._components

    # 解析两次，应该是不同的实例
    instance1 = di_container.resolve(NamedService)
    instance2 = di_container.resolve(NamedService)

    assert instance1 is not instance2


def test_scope_parameter_invalid():
    """测试无效的 scope 参数"""
    with pytest.raises(ValueError, match="scope must be 'singleton' or 'transient'"):

        @Component(scope="invalid")
        class InvalidService:
            pass


def test_singleton_parameter_backward_compatibility():
    """测试 singleton 参数的向后兼容性"""
    cleanup_test_state()

    @Component(singleton=True)
    class OldSingletonService:
        def __init__(self):
            self.value = 0

    @Component(singleton=False)
    class OldTransientService:
        def __init__(self):
            self.value = 0

    di_container = get_di_container()

    # 测试 singleton=True
    instance1 = di_container.resolve(OldSingletonService)
    instance2 = di_container.resolve(OldSingletonService)
    assert instance1 is instance2

    # 测试 singleton=False
    instance3 = di_container.resolve(OldTransientService)
    instance4 = di_container.resolve(OldTransientService)
    assert instance3 is not instance4


def test_scope_parameter_plugin():
    """测试 Plugin 的 scope 参数"""
    cleanup_test_state()

    @Plugin(scope="transient")
    class TransientPlugin(PluginBase):
        def initialize(self):
            return True

        def execute(self, **kwargs):
            return None

        def cleanup(self):
            pass

    di_container = get_di_container()

    # 解析两次，应该是不同的实例
    instance1 = di_container.resolve(TransientPlugin)
    instance2 = di_container.resolve(TransientPlugin)

    assert instance1 is not instance2


def test_scope_parameter_default():
    """测试 scope 参数的默认值"""
    cleanup_test_state()

    @Component
    class DefaultService:
        def __init__(self):
            self.value = 0

    di_container = get_di_container()

    # 默认应该是 singleton
    instance1 = di_container.resolve(DefaultService)
    instance2 = di_container.resolve(DefaultService)

    assert instance1 is instance2


def test_metadata_contains_scope():
    """测试元数据包含 scope 字段"""
    cleanup_test_state()

    @Component(scope="transient")
    class TransientService:
        pass

    @Component(scope="singleton")
    class SingletonService:
        pass

    # 检查统一元数据
    assert hasattr(TransientService, "_decorator_metadata")
    assert hasattr(SingletonService, "_decorator_metadata")

    transient_metadata = TransientService._decorator_metadata[0]  # type: ignore
    singleton_metadata = SingletonService._decorator_metadata[0]  # type: ignore

    assert transient_metadata["scope"] == "transient"
    assert singleton_metadata["scope"] == "singleton"

    # 检查旧元数据（向后兼容）
    assert hasattr(TransientService, "_component_metadata")
    assert hasattr(SingletonService, "_component_metadata")

    assert TransientService._component_metadata["scope"] == "transient"  # type: ignore
    assert SingletonService._component_metadata["scope"] == "singleton"  # type: ignore


def test_scope_priority_over_singleton():
    """测试 scope 参数优先于 singleton 参数"""
    cleanup_test_state()

    # 如果同时提供 scope 和 singleton，scope 应该优先
    @Component(singleton=True, scope="transient")
    class PriorityService:
        def __init__(self):
            self.value = 0

    di_container = get_di_container()

    # scope='transient' 应该生效
    instance1 = di_container.resolve(PriorityService)
    instance2 = di_container.resolve(PriorityService)

    assert instance1 is not instance2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
