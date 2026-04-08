import pytest
from LStartlet import (
    Component,
    Inject,
    resolve_service,
    get_di_container,
    set_project_root,
    PluginBase,
)
import os
import tempfile


@pytest.fixture(autouse=True)
def setup_test_env():
    """为每个测试设置临时项目根目录并清理DI容器"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_root = set_project_root(temp_dir)
        # 清理注册表（DI容器会自动清理）
        from LStartlet import ComponentRegistry

        ComponentRegistry.clear()
        yield temp_dir
        if original_root:
            set_project_root(original_root)
        ComponentRegistry.clear()


@pytest.mark.di
class TestDIDecorator:
    """测试依赖注入装饰器和相关功能"""

    def test_component_registration_in_di(self):
        """测试Component装饰器自动注册到DI容器"""

        @Component
        class DatabaseService:
            def connect(self):
                return "connected"

        container = get_di_container()
        assert "DatabaseService" in [
            name for name, cls in container._components.items()
        ]

        # 测试解析服务
        db_service = resolve_service(DatabaseService)
        assert isinstance(db_service, DatabaseService)
        assert db_service.connect() == "connected"


@pytest.mark.di
class TestInjectDecorator:
    """测试Inject装饰器"""

    def test_inject_basic_usage(self):
        """测试基本的Inject装饰器用法"""

        @Component
        class ConfigService:
            def get_config(self, key):
                return f"value_of_{key}"

        @Component
        class UserService:
            def __init__(self, config_service: ConfigService = Inject()):
                self.config = config_service

            def get_user_config(self):
                return self.config.get_config("user")

        user_service = resolve_service(UserService)
        assert user_service.get_user_config() == "value_of_user"

    def test_inject_multiple_services(self):
        """测试注入多个服务"""

        @Component
        class LoggerService:
            def log(self, message):
                return f"LOG: {message}"

        @Component
        class CacheService:
            def get(self, key):
                return f"cached_{key}"

        @Component
        class BusinessService:
            def __init__(
                self, logger: LoggerService = Inject(), cache: CacheService = Inject()
            ):
                self.logger = logger
                self.cache = cache

            def process(self, key):
                cached_value = self.cache.get(key)
                self.logger.log(f"Processing {key}")
                return cached_value

        business_service = resolve_service(BusinessService)
        result = business_service.process("test_key")
        assert result == "cached_test_key"
