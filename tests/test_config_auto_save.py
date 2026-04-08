"""
测试配置自动保存功能
"""

import sys
import os
import yaml
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from LStartlet import (
    Component,
    get_di_container,
    set_config,
    get_config,
    enable_config_auto_save,
    disable_config_auto_save,
    load_config,
    save_config,
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


def test_config_auto_save():
    """测试配置自动保存功能"""
    cleanup_test_state()

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_config_file = f.name
        f.write('database:\n  url: "postgresql://localhost/test"\n  port: 5432\n')

    try:
        # 加载初始配置
        load_config(temp_config_file)
        assert get_config("database.url") == "postgresql://localhost/test"
        assert get_config("database.port") == 5432

        # 启用自动保存
        enable_config_auto_save(temp_config_file)

        # 修改配置（应该自动保存）
        set_config("database.url", "postgresql://localhost/newdb")
        set_config("database.port", 5433)

        # 验证配置已更新
        assert get_config("database.url") == "postgresql://localhost/newdb"
        assert get_config("database.port") == 5433

        # 验证配置已自动保存到文件
        with open(temp_config_file, "r", encoding="utf-8") as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["database"]["url"] == "postgresql://localhost/newdb"
        assert saved_config["database"]["port"] == 5433

        print("✅ 配置自动保存测试通过")

    finally:
        # 清理临时文件
        if os.path.exists(temp_config_file):
            os.remove(temp_config_file)


def test_config_auto_save_nested():
    """测试嵌套配置的自动保存"""
    cleanup_test_state()

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_config_file = f.name
        f.write(
            'app:\n  name: "MyApp"\n  version: "1.0.0"\n  features:\n    - feature1\n    - feature2\n'
        )

    try:
        # 加载初始配置
        load_config(temp_config_file)
        assert get_config("app.name") == "MyApp"
        assert get_config("app.version") == "1.0.0"

        # 启用自动保存
        enable_config_auto_save(temp_config_file)

        # 修改嵌套配置
        set_config("app.name", "UpdatedApp")
        set_config("app.version", "2.0.0")
        set_config("app.features", ["feature1", "feature2", "feature3"])

        # 验证配置已更新
        assert get_config("app.name") == "UpdatedApp"
        assert get_config("app.version") == "2.0.0"
        assert get_config("app.features") == ["feature1", "feature2", "feature3"]

        # 验证配置已自动保存到文件
        with open(temp_config_file, "r", encoding="utf-8") as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["app"]["name"] == "UpdatedApp"
        assert saved_config["app"]["version"] == "2.0.0"
        assert saved_config["app"]["features"] == ["feature1", "feature2", "feature3"]

        print("✅ 嵌套配置自动保存测试通过")

    finally:
        # 清理临时文件
        if os.path.exists(temp_config_file):
            os.remove(temp_config_file)


def test_disable_config_auto_save():
    """测试禁用配置自动保存"""
    cleanup_test_state()

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_config_file = f.name
        f.write('key1: "value1"\nkey2: "value2"\n')

    try:
        # 加载初始配置
        load_config(temp_config_file)
        assert get_config("key1") == "value1"
        assert get_config("key2") == "value2"

        # 启用自动保存
        enable_config_auto_save(temp_config_file)

        # 修改配置（应该自动保存）
        set_config("key1", "new_value1")
        assert get_config("key1") == "new_value1"

        # 禁用自动保存
        disable_config_auto_save()

        # 修改配置（不应该自动保存）
        set_config("key2", "new_value2")
        assert get_config("key2") == "new_value2"

        # 验证配置文件中的值
        with open(temp_config_file, "r", encoding="utf-8") as f:
            saved_config = yaml.safe_load(f)

        # key1 应该被保存（因为当时启用了自动保存）
        assert saved_config["key1"] == "new_value1"
        # key2 不应该被保存（因为禁用了自动保存）
        assert saved_config["key2"] == "value2"

        print("✅ 禁用配置自动保存测试通过")

    finally:
        # 清理临时文件
        if os.path.exists(temp_config_file):
            os.remove(temp_config_file)


def test_config_auto_save_new_file():
    """测试自动保存到新文件"""
    cleanup_test_state()

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    temp_config_file = os.path.join(temp_dir, "new_config.yaml")

    try:
        # 设置初始配置
        set_config("app.name", "MyApp")
        set_config("app.version", "1.0.0")

        # 启用自动保存到新文件
        enable_config_auto_save(temp_config_file)

        # 修改配置（应该自动保存）
        set_config("app.name", "UpdatedApp")

        # 验证配置文件已创建
        assert os.path.exists(temp_config_file)

        # 验证配置已保存
        with open(temp_config_file, "r", encoding="utf-8") as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["app"]["name"] == "UpdatedApp"
        assert saved_config["app"]["version"] == "1.0.0"

        print("✅ 自动保存到新文件测试通过")

    finally:
        # 清理临时目录
        import shutil

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_config_auto_save_with_components():
    """测试配置自动保存与组件的集成"""
    cleanup_test_state()

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_config_file = f.name
        f.write(
            'database:\n  url: "postgresql://localhost/test"\n  max_connections: 10\n'
        )

    try:
        # 加载初始配置
        load_config(temp_config_file)

        # 启用自动保存
        enable_config_auto_save(temp_config_file)

        # 定义使用配置的组件
        @Component
        class DatabaseService:
            def __init__(self):
                self.url = get_config("database.url")
                self.max_connections = get_config("database.max_connections")

            def update_config(self, new_url, new_max_connections):
                set_config("database.url", new_url)
                set_config("database.max_connections", new_max_connections)
                self.url = new_url
                self.max_connections = new_max_connections

        # 创建组件
        di_container = get_di_container()
        db_service = di_container.resolve(DatabaseService)

        # 验证初始配置
        assert db_service.url == "postgresql://localhost/test"
        assert db_service.max_connections == 10

        # 通过组件更新配置
        db_service.update_config("postgresql://localhost/production", 20)

        # 验证组件配置已更新
        assert db_service.url == "postgresql://localhost/production"
        assert db_service.max_connections == 20

        # 验证配置已自动保存
        with open(temp_config_file, "r", encoding="utf-8") as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["database"]["url"] == "postgresql://localhost/production"
        assert saved_config["database"]["max_connections"] == 20

        print("✅ 配置自动保存与组件集成测试通过")

    finally:
        # 清理临时文件
        if os.path.exists(temp_config_file):
            os.remove(temp_config_file)


if __name__ == "__main__":
    test_config_auto_save()
    test_config_auto_save_nested()
    test_disable_config_auto_save()
    test_config_auto_save_new_file()
    test_config_auto_save_with_components()

    print("\n🎉 所有配置自动保存测试通过！")
