"""
测试实例管理自动化和错误处理自动化
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from LStartlet import (
    Component,
    Inject,
    get_di_container,
    start_framework,
    stop_framework,
    get_all_instances,
    get_instances_by_type,
    get_instance_count,
    get_instance_count_by_type,
    register_error_handler,
    unregister_error_handler,
    get_lifecycle_errors,
    clear_lifecycle_errors,
    get_lifecycle_manager,
)


def cleanup_test_state():
    """清理测试状态"""
    # 清理DI容器
    di_container = get_di_container()
    di_container._services.clear()
    di_container._components.clear()
    di_container._plugins.clear()
    di_container._all_instances.clear()
    di_container._lifecycle_errors.clear()
    di_container._error_handlers.clear()

    # 清理生命周期管理器
    lifecycle_manager = get_lifecycle_manager()
    lifecycle_manager._methods.clear()


def test_instance_tracking():
    """测试实例跟踪功能"""
    cleanup_test_state()

    @Component
    class ServiceA:
        def __init__(self):
            self.name = "ServiceA"

    @Component
    class ServiceB:
        def __init__(self):
            self.name = "ServiceB"

    di_container = get_di_container()

    # 解析服务
    service_a = di_container.resolve(ServiceA)
    service_b = di_container.resolve(ServiceB)

    # 验证实例被跟踪
    all_instances = get_all_instances()
    assert len(all_instances) >= 2
    assert service_a in all_instances
    assert service_b in all_instances

    # 验证按类型获取实例
    service_a_instances = get_instances_by_type(ServiceA)
    assert len(service_a_instances) >= 1
    assert service_a in service_a_instances

    service_b_instances = get_instances_by_type(ServiceB)
    assert len(service_b_instances) >= 1
    assert service_b in service_b_instances

    # 验证实例计数
    assert get_instance_count() >= 2
    assert get_instance_count_by_type(ServiceA) >= 1
    assert get_instance_count_by_type(ServiceB) >= 1

    print("✅ 实例跟踪测试通过")


def test_singleton_instance_tracking():
    """测试单例实例跟踪"""
    cleanup_test_state()

    @Component
    class SingletonService:
        def __init__(self):
            self.name = "SingletonService"

    di_container = get_di_container()

    # 解析多次单例服务
    instance1 = di_container.resolve(SingletonService)
    instance2 = di_container.resolve(SingletonService)
    instance3 = di_container.resolve(SingletonService)

    # 验证单例特性
    assert instance1 is instance2
    assert instance2 is instance3

    # 验证实例被跟踪（只跟踪一个实例）
    all_instances = get_all_instances()
    assert instance1 in all_instances

    # 验证实例计数
    singleton_count = get_instance_count_by_type(SingletonService)
    assert singleton_count >= 1

    print("✅ 单例实例跟踪测试通过")


def test_transient_instance_tracking():
    """测试瞬态实例跟踪"""
    cleanup_test_state()

    @Component
    class TransientService:
        def __init__(self):
            self.name = "TransientService"

    di_container = get_di_container()

    # 解析多次瞬态服务
    instance1 = di_container.resolve_transient(TransientService)
    instance2 = di_container.resolve_transient(TransientService)
    instance3 = di_container.resolve_transient(TransientService)

    # 验证瞬态特性
    assert instance1 is not instance2
    assert instance2 is not instance3

    # 验证实例被跟踪
    all_instances = get_all_instances()
    assert instance1 in all_instances
    assert instance2 in all_instances
    assert instance3 in all_instances

    # 验证实例计数
    transient_count = get_instance_count_by_type(TransientService)
    assert transient_count >= 3

    print("✅ 瞬态实例跟踪测试通过")


def test_lifecycle_error_handling():
    """测试生命周期错误处理"""
    cleanup_test_state()

    error_count = [0]

    def error_handler(exception, phase, instance):
        error_count[0] += 1

    # 注册错误处理器
    register_error_handler(error_handler)

    @Component
    class ErrorService:
        def __init__(self):
            raise RuntimeError("初始化错误")

    di_container = get_di_container()

    # 尝试解析会出错的服务
    try:
        di_container.resolve(ErrorService)
        assert False, "应该抛出异常"
    except RuntimeError:
        pass

    # 验证错误被捕获
    assert error_count[0] > 0

    # 验证错误被记录
    errors = get_lifecycle_errors()
    assert len(errors) > 0
    assert errors[0]["phase"] == "CREATE_INSTANCE"
    assert isinstance(errors[0]["exception"], RuntimeError)

    # 清除错误
    clear_lifecycle_errors()
    assert len(get_lifecycle_errors()) == 0

    # 取消注册错误处理器
    unregister_error_handler(error_handler)

    print("✅ 生命周期错误处理测试通过")


def test_multiple_error_handlers():
    """测试多个错误处理器"""
    cleanup_test_state()

    handler1_calls = [0]
    handler2_calls = [0]

    def error_handler1(exception, phase, instance):
        handler1_calls[0] += 1

    def error_handler2(exception, phase, instance):
        handler2_calls[0] += 1

    # 注册多个错误处理器
    register_error_handler(error_handler1)
    register_error_handler(error_handler2)

    @Component
    class ErrorService:
        def __init__(self):
            raise RuntimeError("初始化错误")

    di_container = get_di_container()

    # 尝试解析会出错的服务
    try:
        di_container.resolve(ErrorService)
        assert False, "应该抛出异常"
    except RuntimeError:
        pass

    # 验证所有错误处理器都被调用
    assert handler1_calls[0] > 0
    assert handler2_calls[0] > 0

    # 取消注册错误处理器
    unregister_error_handler(error_handler1)
    unregister_error_handler(error_handler2)

    print("✅ 多个错误处理器测试通过")


def test_instance_cleanup_on_error():
    """测试错误时的实例清理"""
    cleanup_test_state()

    @Component
    class ErrorService:
        def __init__(self):
            raise RuntimeError("初始化错误")

    @Component
    class NormalService:
        def __init__(self):
            self.name = "NormalService"

    di_container = get_di_container()

    # 先解析正常服务
    normal_service = di_container.resolve(NormalService)

    # 尝试解析会出错的服务
    try:
        di_container.resolve(ErrorService)
        assert False, "应该抛出异常"
    except RuntimeError:
        pass

    # 验证正常服务仍然被跟踪
    all_instances = get_all_instances()
    assert normal_service in all_instances

    # 验证实例计数
    assert get_instance_count() >= 1

    print("✅ 错误时的实例清理测试通过")


def test_error_handler_exception_safety():
    """测试错误处理器本身的异常处理"""
    cleanup_test_state()

    def safe_error_handler(exception, phase, instance):
        # 正常的错误处理器
        pass

    def unsafe_error_handler(exception, phase, instance):
        # 会抛出异常的错误处理器
        raise ValueError("错误处理器错误")

    # 注册错误处理器
    register_error_handler(safe_error_handler)
    register_error_handler(unsafe_error_handler)

    @Component
    class ErrorService:
        def __init__(self):
            raise RuntimeError("初始化错误")

    di_container = get_di_container()

    # 尝试解析会出错的服务（不应该因为错误处理器出错而崩溃）
    try:
        di_container.resolve(ErrorService)
        assert False, "应该抛出异常"
    except RuntimeError:
        pass

    # 验证错误被记录
    errors = get_lifecycle_errors()
    assert len(errors) > 0

    # 取消注册错误处理器
    unregister_error_handler(safe_error_handler)
    unregister_error_handler(unsafe_error_handler)

    print("✅ 错误处理器异常安全测试通过")


if __name__ == "__main__":
    test_instance_tracking()
    test_singleton_instance_tracking()
    test_transient_instance_tracking()
    test_lifecycle_error_handling()
    test_multiple_error_handlers()
    test_instance_cleanup_on_error()
    test_error_handler_exception_safety()

    print("\n🎉 所有实例管理和错误处理自动化测试通过！")
