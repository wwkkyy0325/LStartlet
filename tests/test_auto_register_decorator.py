"""测试自动注册装饰器的功能"""

import unittest
from abc import ABC, abstractmethod
from typing import Type

from LStartlet.core.decorators import auto_register
from LStartlet.core.di import get_default_container, ServiceLifetime


class TestAutoRegisterDecorator(unittest.TestCase):
    """测试自动注册装饰器"""

    def setUp(self):
        """测试前清理默认容器"""
        # 获取默认容器并清空服务注册
        container = get_default_container()
        container._services.clear()
        container._singleton_instances.clear()

    def test_auto_register_without_service_type(self):
        """测试不指定服务类型时的自动注册"""
        
        @auto_register()
        class TestService:
            def __init__(self):
                self.value = "test"
            
            def get_value(self):
                return self.value

        # 验证服务可以被解析
        container = get_default_container()
        service = container.resolve(TestService)
        
        self.assertIsInstance(service, TestService)
        self.assertEqual(service.get_value(), "test")

    def test_auto_register_with_service_type(self):
        """测试指定服务类型时的自动注册"""
        
        class IService(ABC):
            @abstractmethod
            def do_work(self) -> str:
                pass

        @auto_register(service_type=IService, lifetime=ServiceLifetime.SINGLETON)
        class ConcreteService(IService):
            def __init__(self):
                self.work_count = 0
            
            def do_work(self) -> str:
                self.work_count += 1
                return f"work done {self.work_count} times"

        # 验证服务可以被解析
        container = get_default_container()
        service = container.resolve(IService)
        
        self.assertIsInstance(service, ConcreteService)
        self.assertEqual(service.do_work(), "work done 1 times")
        
        # 验证单例生命周期
        service2 = container.resolve(IService)
        self.assertIs(service, service2)
        self.assertEqual(service2.do_work(), "work done 2 times")

    def test_auto_register_with_custom_lifetime(self):
        """测试自定义生命周期"""
        
        @auto_register(lifetime=ServiceLifetime.TRANSIENT)
        class TransientService:
            def __init__(self):
                self.id = id(self)
            
            def get_id(self):
                return self.id

        container = get_default_container()
        service1 = container.resolve(TransientService)
        service2 = container.resolve(TransientService)
        
        # TRANSIENT 生命周期应该创建不同的实例
        self.assertNotEqual(service1.get_id(), service2.get_id())

    def test_auto_register_with_implementation_type(self):
        """测试指定实现类型"""
        
        class BaseService:
            def base_method(self) -> str:
                return "base"

        class DerivedService(BaseService):
            def derived_method(self) -> str:
                return "derived"

        @auto_register(
            service_type=BaseService, 
            implementation_type=DerivedService,
            lifetime=ServiceLifetime.SINGLETON
        )
        class DecoratedClass:
            pass

        # 这个测试实际上不会使用DecoratedClass，因为指定了implementation_type
        # 让我们重新设计一个更合理的测试
        
        # 清理容器
        container = get_default_container()
        container._services.clear()
        container._singleton_instances.clear()
        
        # 重新注册
        @auto_register(service_type=BaseService, implementation_type=DerivedService)
        class AnotherDecoratedClass:
            pass
        
        resolved_service = container.resolve(BaseService)
        self.assertIsInstance(resolved_service, DerivedService)
        self.assertEqual(resolved_service.base_method(), "base")
        self.assertEqual(resolved_service.derived_method(), "derived")


if __name__ == "__main__":
    unittest.main()