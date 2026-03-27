import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from core.di import (
    ServiceContainer,
    ServiceLifetime,
    ServiceResolutionError,
    ServiceRegistrationError,
)
from core.di.service_container import get_default_container


class TestService:
    def __init__(self, name: str = "test"):
        self.name = name


class DependencyService:
    def __init__(self, test_service: TestService):
        self.test_service = test_service


class TestServiceContainer(unittest.TestCase):

    def setUp(self):
        """测试前清理默认容器"""
        default_container = get_default_container()
        default_container.reset()

    def test_register_and_resolve_transient(self):
        """测试注册和解析瞬态服务"""
        container = ServiceContainer()
        container.register(TestService, lifetime=ServiceLifetime.TRANSIENT)

        instance1 = container.resolve(TestService)
        instance2 = container.resolve(TestService)

        self.assertIsInstance(instance1, TestService)
        self.assertIsInstance(instance2, TestService)
        self.assertIsNot(instance1, instance2)  # 瞬态服务应该是不同实例

    def test_register_and_resolve_singleton(self):
        """测试注册和解析单例服务"""
        container = ServiceContainer()
        container.register(TestService, lifetime=ServiceLifetime.SINGLETON)

        instance1 = container.resolve(TestService)
        instance2 = container.resolve(TestService)

        self.assertIs(instance1, instance2)  # 单例服务应该是同一实例

    def test_register_instance_singleton(self):
        """测试注册预创建实例的单例服务"""
        container = ServiceContainer()
        instance = TestService("pre-created")
        container.register(
            TestService, instance=instance, lifetime=ServiceLifetime.SINGLETON
        )

        resolved = container.resolve(TestService)
        self.assertIs(resolved, instance)
        self.assertEqual(resolved.name, "pre-created")

    def test_dependency_injection(self):
        """测试依赖注入"""
        container = ServiceContainer()
        container.register(TestService, lifetime=ServiceLifetime.SINGLETON)
        container.register(DependencyService, lifetime=ServiceLifetime.TRANSIENT)

        dependency_service = container.resolve(DependencyService)
        self.assertIsInstance(dependency_service, DependencyService)
        self.assertIsInstance(dependency_service.test_service, TestService)

    def test_unregistered_service(self):
        """测试未注册服务的解析"""
        container = ServiceContainer()

        with self.assertRaises(ServiceResolutionError):
            container.resolve(TestService)

    def test_invalid_registration(self):
        """测试无效的注册参数"""
        container = ServiceContainer()

        with self.assertRaises(ServiceRegistrationError):
            container.register(
                TestService, factory=lambda c: TestService(), instance=TestService()
            )


if __name__ == "__main__":
    unittest.main()
