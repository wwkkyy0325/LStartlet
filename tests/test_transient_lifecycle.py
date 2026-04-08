"""
瞬态实例生命周期测试
"""

import pytest
from LStartlet import Component, Inject, get_di_container
from LStartlet import Init, Start, Stop, Destroy
from LStartlet import (
    resolve_transient,
    start_transient_instance,
    stop_transient_instance,
)


@Component
class TransientService:
    """用于测试的瞬态服务"""

    def __init__(self):
        self.init_called = False
        self.start_called = False
        self.stop_called = False
        self.destroy_called = False

    @Init()
    def initialize(self):
        self.init_called = True

    @Start()
    def start_service(self):
        self.start_called = True

    @Stop()
    def stop_service(self):
        self.stop_called = True

    @Destroy()
    def destroy_service(self):
        self.destroy_called = True


def test_transient_instance_creation():
    """测试瞬态实例创建和POST_INIT自动触发"""
    # 创建瞬态实例
    instance = resolve_transient(TransientService)

    # 验证Init方法被自动调用
    assert instance.init_called == True
    assert instance.start_called == False
    assert instance.stop_called == False
    assert instance.destroy_called == False


def test_transient_instance_full_lifecycle():
    """测试瞬态实例完整生命周期"""
    # 创建瞬态实例
    instance = resolve_transient(TransientService)

    # 验证Init已触发
    assert instance.init_called == True

    # 手动触发Start
    start_transient_instance(instance)
    assert instance.start_called == True

    # 手动触发Stop和Destroy
    stop_transient_instance(instance)
    assert instance.stop_called == True
    assert instance.destroy_called == True


def test_transient_vs_singleton():
    """测试瞬态实例与单例实例的区别"""
    di_container = get_di_container()

    # 注册为单例的服务
    di_container.register_service(TransientService, TransientService, singleton=True)

    # 获取单例实例
    singleton1 = di_container.resolve(TransientService)
    singleton2 = di_container.resolve(TransientService)

    # 获取瞬态实例
    transient1 = resolve_transient(TransientService)
    transient2 = resolve_transient(TransientService)

    # 验证单例是同一个实例
    assert singleton1 is singleton2

    # 验证瞬态是不同实例
    assert transient1 is not transient2

    # 验证所有实例都正确触发了Init
    assert singleton1.init_called == True
    assert transient1.init_called == True
    assert transient2.init_called == True


def test_unregistered_transient_creation():
    """测试未注册类型的瞬态实例创建"""

    class SimpleClass:
        """简单的未注册类"""

        def __init__(self):
            self.value = "simple"

    # 直接创建未注册类型的瞬态实例
    instance = resolve_transient(SimpleClass)

    # 验证实例创建成功
    assert isinstance(instance, SimpleClass)
    assert instance.value == "simple"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
