"""
测试完整的生命周期自动化
确保系统能够妥善处理部分定义的情况
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
    Init,
    Start,
    Stop,
    Destroy,
    PreInit,
    PreStart,
    PreStop,
    PreDestroy,
    PostStop,
    PostDestroy,
    trigger_lifecycle_phase,
    LifecyclePhase,
    get_lifecycle_manager,
)


def cleanup_test_state():
    """清理测试状态"""
    # 清理DI容器
    di_container = get_di_container()
    di_container._services.clear()
    di_container._components.clear()
    di_container._plugins.clear()

    # 清理生命周期管理器
    lifecycle_manager = get_lifecycle_manager()
    lifecycle_manager._methods.clear()


def test_full_lifecycle_automation():
    """测试完整的生命周期自动化"""
    cleanup_test_state()

    execution_order = []

    @Component
    class FullLifecycleService:
        def __init__(self):
            execution_order.append("__init__")

        @PreInit()
        def pre_init(self):
            execution_order.append("PreInit")

        @Init()
        def init(self):
            execution_order.append("Init")

        @PreStart()
        def pre_start(self):
            execution_order.append("PreStart")

        @Start()
        def start(self):
            execution_order.append("Start")

        @PreStop()
        def pre_stop(self):
            execution_order.append("PreStop")

        @PostStop()
        def post_stop(self):
            execution_order.append("PostStop")

        @PreDestroy()
        def pre_destroy(self):
            execution_order.append("PreDestroy")

        @Destroy()
        def destroy(self):
            execution_order.append("Destroy")

    di_container = get_di_container()

    # 解析组件（应该触发 PreInit 和 Init）
    service = di_container.resolve(FullLifecycleService)
    assert execution_order == [
        "__init__",
        "PreInit",
        "Init",
    ], f"初始化顺序错误: {execution_order}"

    # 启动框架（应该触发 PreStart 和 Start）
    start_framework()
    expected_order = ["__init__", "PreInit", "Init", "PreStart", "Start"]
    assert execution_order == expected_order, f"启动顺序错误: {execution_order}"

    # 停止框架（应该触发 PreStop, PostStop, PreDestroy, Destroy）
    stop_framework()
    expected_order = [
        "__init__",
        "PreInit",
        "Init",
        "PreStart",
        "Start",
        "PreStop",
        "PostStop",
        "PreDestroy",
        "Destroy",
    ]
    assert execution_order == expected_order, f"停止顺序错误: {execution_order}"

    print("✅ 完整生命周期自动化测试通过")


def test_partial_lifecycle_only_main():
    """测试只定义主要生命周期的情况"""
    cleanup_test_state()

    execution_order = []

    @Component
    class MainLifecycleOnlyService:
        def __init__(self):
            execution_order.append("__init__")

        @Init()
        def init(self):
            execution_order.append("Init")

        @Start()
        def start(self):
            execution_order.append("Start")

        @Stop()
        def stop(self):
            execution_order.append("Stop")

        @Destroy()
        def destroy(self):
            execution_order.append("Destroy")

    di_container = get_di_container()

    # 解析组件（应该只触发 Init）
    service = di_container.resolve(MainLifecycleOnlyService)
    assert execution_order == ["__init__", "Init"], f"初始化顺序错误: {execution_order}"

    # 启动框架（应该只触发 Start）
    start_framework()
    expected_order = ["__init__", "Init", "Start"]
    assert execution_order == expected_order, f"启动顺序错误: {execution_order}"

    # 停止框架（应该触发 Stop 和 Destroy）
    stop_framework()
    expected_order = ["__init__", "Init", "Start", "Stop", "Destroy"]
    assert execution_order == expected_order, f"停止顺序错误: {execution_order}"

    print("✅ 主要生命周期测试通过")


def test_partial_lifecycle_mixed():
    """测试混合定义部分生命周期的情况"""
    cleanup_test_state()

    execution_order = []

    @Component
    class MixedLifecycleService:
        def __init__(self):
            execution_order.append("__init__")

        @PreInit()
        def pre_init(self):
            execution_order.append("PreInit")

        @Init()
        def init(self):
            execution_order.append("Init")

        # 没有 PreStart

        @Start()
        def start(self):
            execution_order.append("Start")

        @Stop()
        def stop(self):
            execution_order.append("Stop")

        # 没有 PostStop

        @PreDestroy()
        def pre_destroy(self):
            execution_order.append("PreDestroy")

        @Destroy()
        def destroy(self):
            execution_order.append("Destroy")

    di_container = get_di_container()

    # 解析组件（应该触发 PreInit 和 Init）
    service = di_container.resolve(MixedLifecycleService)
    assert execution_order == [
        "__init__",
        "PreInit",
        "Init",
    ], f"初始化顺序错误: {execution_order}"

    # 启动框架（应该只触发 Start，因为没有 PreStart）
    start_framework()
    expected_order = ["__init__", "PreInit", "Init", "Start"]
    assert execution_order == expected_order, f"启动顺序错误: {execution_order}"

    # 停止框架（应该触发 Stop, PreDestroy, Destroy）
    stop_framework()
    expected_order = [
        "__init__",
        "PreInit",
        "Init",
        "Start",
        "Stop",
        "PreDestroy",
        "Destroy",
    ]
    assert execution_order == expected_order, f"停止顺序错误: {execution_order}"

    print("✅ 混合生命周期测试通过")


def test_no_lifecycle_methods():
    """测试没有定义任何生命周期方法的情况"""
    cleanup_test_state()

    @Component
    class NoLifecycleService:
        def __init__(self):
            self.initialized = False

    di_container = get_di_container()

    # 解析组件（应该正常工作）
    service = di_container.resolve(NoLifecycleService)
    assert service is not None

    # 启动框架（应该正常工作）
    start_framework()

    # 停止框架（应该正常工作）
    stop_framework()

    print("✅ 无生命周期方法测试通过")


def test_transient_lifecycle():
    """测试瞬态实例的生命周期"""
    cleanup_test_state()

    execution_order = []

    @Component(scope="transient")
    class TransientService:
        def __init__(self):
            execution_order.append("__init__")

        @Init()
        def init(self):
            execution_order.append("Init")

        @Start()
        def start(self):
            execution_order.append("Start")

        @Stop()
        def stop(self):
            execution_order.append("Stop")

        @Destroy()
        def destroy(self):
            execution_order.append("Destroy")

    di_container = get_di_container()

    # 解析瞬态实例（应该触发 Init）
    service1 = di_container.resolve(TransientService)
    assert execution_order == ["__init__", "Init"], f"初始化顺序错误: {execution_order}"

    # 手动启动瞬态实例
    from LStartlet import start_transient_instance

    start_transient_instance(service1)
    expected_order = ["__init__", "Init", "Start"]
    assert execution_order == expected_order, f"启动顺序错误: {execution_order}"

    # 手动停止瞬态实例
    from LStartlet import stop_transient_instance

    stop_transient_instance(service1)
    expected_order = ["__init__", "Init", "Start", "Stop", "Destroy"]
    assert execution_order == expected_order, f"停止顺序错误: {execution_order}"

    print("✅ 瞬态实例生命周期测试通过")


def test_multiple_components_lifecycle():
    """测试多个组件的生命周期顺序"""
    cleanup_test_state()

    execution_order = []

    @Component
    class ServiceA:
        @Init()
        def init(self):
            execution_order.append("ServiceA_Init")

        @Start()
        def start(self):
            execution_order.append("ServiceA_Start")

        @Stop()
        def stop(self):
            execution_order.append("ServiceA_Stop")

        @Destroy()
        def destroy(self):
            execution_order.append("ServiceA_Destroy")

    @Component
    class ServiceB:
        @Init()
        def init(self):
            execution_order.append("ServiceB_Init")

        @Start()
        def start(self):
            execution_order.append("ServiceB_Start")

        @Stop()
        def stop(self):
            execution_order.append("ServiceB_Stop")

        @Destroy()
        def destroy(self):
            execution_order.append("ServiceB_Destroy")

    di_container = get_di_container()

    # 解析组件
    service_a = di_container.resolve(ServiceA)
    service_b = di_container.resolve(ServiceB)

    # 启动框架
    start_framework()

    # 停止框架
    stop_framework()

    # 验证所有生命周期都被触发
    assert "ServiceA_Init" in execution_order
    assert "ServiceB_Init" in execution_order
    assert "ServiceA_Start" in execution_order
    assert "ServiceB_Start" in execution_order
    assert "ServiceA_Stop" in execution_order
    assert "ServiceB_Stop" in execution_order
    assert "ServiceA_Destroy" in execution_order
    assert "ServiceB_Destroy" in execution_order

    print("✅ 多组件生命周期测试通过")


if __name__ == "__main__":
    test_full_lifecycle_automation()
    test_partial_lifecycle_only_main()
    test_partial_lifecycle_mixed()
    test_no_lifecycle_methods()
    test_transient_lifecycle()
    test_multiple_components_lifecycle()

    print("\n🎉 所有生命周期自动化测试通过！")
