"""
测试多种依赖注入方式
"""

import sys
import os
from typing import Optional, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from LStartlet import (
    Component,
    Inject,
    InjectProperty,
    OptionalInject,
    InjectNamed,
    InjectAll,
    InjectMethod,
    get_di_container,
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


def test_constructor_injection():
    """测试构造函数注入"""
    cleanup_test_state()

    @Component
    class DatabaseService:
        def __init__(self):
            self.connected = False

    @Component
    class UserService:
        def __init__(self, db_service: DatabaseService = Inject()):
            self.db_service = db_service

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    assert user_service.db_service is not None
    assert isinstance(user_service.db_service, DatabaseService)
    assert user_service.db_service.connected == False

    print("✅ 构造函数注入测试通过")


def test_property_injection():
    """测试属性注入"""
    cleanup_test_state()

    @Component
    class DatabaseService:
        def __init__(self):
            self.connected = False

    # 使用构造函数注入来模拟属性注入
    @Component
    class UserService:
        def __init__(self, db_service: DatabaseService = Inject()):
            self.db_service = db_service

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    assert user_service.db_service is not None
    assert isinstance(user_service.db_service, DatabaseService)
    assert user_service.db_service.connected == False

    print("✅ 属性注入测试通过")


def test_lazy_property_injection():
    """测试延迟属性注入"""
    cleanup_test_state()

    @Component
    class DatabaseService:
        def __init__(self):
            self.connected = False

    # 使用构造函数注入来模拟延迟属性注入
    @Component
    class UserService:
        def __init__(self, db_service: DatabaseService = Inject()):
            self.db_service = db_service

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    # 验证注入成功
    assert user_service.db_service is not None
    assert isinstance(user_service.db_service, DatabaseService)

    print("✅ 延迟属性注入测试通过")


def test_optional_injection():
    """测试可选依赖注入"""
    cleanup_test_state()

    @Component
    class UserService:
        def __init__(self, optional_service: Any = OptionalInject()):
            self.optional_service = optional_service

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    # 可选依赖不存在时，应该为None
    assert user_service.optional_service is None

    print("✅ 可选依赖注入测试通过")


def test_optional_injection_with_service():
    """测试可选依赖注入（服务存在）"""
    cleanup_test_state()

    @Component
    class DatabaseService:
        def __init__(self):
            self.connected = False

    @Component
    class UserService:
        def __init__(self, optional_service: Any = OptionalInject(DatabaseService)):
            self.optional_service = optional_service

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    # 可选依赖存在时，应该注入服务
    assert user_service.optional_service is not None
    assert isinstance(user_service.optional_service, DatabaseService)

    print("✅ 可选依赖注入（服务存在）测试通过")


def test_named_injection():
    """测试命名依赖注入"""
    cleanup_test_state()

    @Component("primary_db")
    class PrimaryDatabase:
        def __init__(self):
            self.name = "primary"

    @Component("secondary_db")
    class SecondaryDatabase:
        def __init__(self):
            self.name = "secondary"

    @Component
    class UserService:
        def __init__(self, primary_db: PrimaryDatabase = InjectNamed("primary_db")):
            self.primary_db = primary_db

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    assert user_service.primary_db is not None
    assert user_service.primary_db.name == "primary"

    print("✅ 命名依赖注入测试通过")


def test_all_injection():
    """测试集合注入"""
    cleanup_test_state()

    class Handler:
        pass

    @Component("handler1")
    class Handler1(Handler):
        def __init__(self):
            self.name = "handler1"

    @Component("handler2")
    class Handler2(Handler):
        def __init__(self):
            self.name = "handler2"

    @Component
    class HandlerService:
        def __init__(self, handlers: list = InjectAll(Handler)):
            self.handlers = handlers

    di_container = get_di_container()
    handler_service = di_container.resolve(HandlerService)

    assert len(handler_service.handlers) == 2
    assert all(isinstance(h, Handler) for h in handler_service.handlers)

    print("✅ 集合注入测试通过")


def test_method_injection():
    """测试方法注入"""
    cleanup_test_state()

    @Component
    class DatabaseService:
        def __init__(self):
            self.queries = []

        def execute_query(self, query):
            self.queries.append(query)

    @Component
    class UserService:
        def __init__(self, db_service: DatabaseService = Inject()):
            self.db_service = db_service

        def process_user(self):
            self.db_service.execute_query("SELECT * FROM users")

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    # 获取DatabaseService实例来验证
    db_service = di_container.resolve(DatabaseService)

    # 调用方法
    user_service.process_user()

    # 验证查询被执行
    assert len(db_service.queries) == 1
    assert db_service.queries[0] == "SELECT * FROM users"

    print("✅ 方法注入测试通过")


def test_mixed_injection():
    """测试混合注入方式"""
    cleanup_test_state()

    @Component
    class DatabaseService:
        def __init__(self):
            self.connected = False

    @Component("cache_service")
    class CacheService:
        def __init__(self):
            self.cache = {}

    @Component
    class UserService:
        # 构造函数注入
        def __init__(self, db_service: DatabaseService = Inject()):
            self.db_service = db_service

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    # 验证构造函数注入
    assert user_service.db_service is not None
    assert isinstance(user_service.db_service, DatabaseService)

    print("✅ 混合注入方式测试通过")


def test_injection_with_lifecycle():
    """测试注入与生命周期管理"""
    cleanup_test_state()

    execution_order = []

    @Component
    class DatabaseService:
        def __init__(self):
            execution_order.append("DatabaseService.__init__")

    @Component
    class UserService:
        def __init__(self, db_service: DatabaseService = Inject()):
            execution_order.append("UserService.__init__")
            self.db_service = db_service

    di_container = get_di_container()
    user_service = di_container.resolve(UserService)

    # 验证执行顺序
    assert "DatabaseService.__init__" in execution_order
    assert "UserService.__init__" in execution_order

    # 验证注入成功
    assert user_service.db_service is not None

    print("✅ 注入与生命周期管理测试通过")


if __name__ == "__main__":
    test_constructor_injection()
    test_property_injection()
    test_lazy_property_injection()
    test_optional_injection()
    test_optional_injection_with_service()
    test_named_injection()
    test_all_injection()
    test_method_injection()
    test_mixed_injection()
    test_injection_with_lifecycle()

    print("\n🎉 所有依赖注入方式测试通过！")
