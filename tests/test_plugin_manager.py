"""
插件系统测试
"""

import pytest
import tempfile
import os
from LStartlet import (
    PluginBase,
    Plugin,
    PluginManager,
    PluginState,
    PluginDependency,
    get_plugin_manager,
    register_plugin,
    load_plugin,
    activate_plugin,
    deactivate_plugin,
    reload_plugin,
    unload_plugin,
    get_plugin_info,
    get_plugins_by_namespace,
    get_framework_plugins,
    get_user_plugins,
    get_all_plugins,
    analyze_dependencies,
    get_load_order,
    PluginDiscovery,
    PluginError,
    DependencyError,
)


@pytest.fixture(autouse=True)
def setup_test_env():
    """为每个测试设置环境"""
    # 创建新的插件管理器
    import LStartlet._plugin_manager as pm_module

    pm_module._plugin_manager = PluginManager()

    yield

    # 清理
    pm_module._plugin_manager = PluginManager()


class TestPluginManager:
    """测试插件管理器"""

    def test_register_plugin(self):
        """测试注册插件"""

        @Plugin
        class TestPlugin(PluginBase):
            name = "test_plugin"
            version = "1.0.0"
            description = "测试插件"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "test"

            def cleanup(self) -> None:
                pass

        # 注册插件
        result = register_plugin(TestPlugin, namespace="user")
        assert result is True

        # 验证插件已注册
        plugin_info = get_plugin_info("test_plugin")
        assert plugin_info is not None
        assert plugin_info.name == "test_plugin"
        assert plugin_info.namespace == "user"
        assert plugin_info.version == "1.0.0"

    def test_load_plugin(self):
        """测试加载插件"""

        @Plugin
        class LoadTestPlugin(PluginBase):
            name = "load_test_plugin"
            version = "1.0.0"
            description = "加载测试插件"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "load_test"

            def cleanup(self) -> None:
                pass

        # 注册插件
        register_plugin(LoadTestPlugin, namespace="user")

        # 加载插件
        result = load_plugin("load_test_plugin")
        assert result is True

        # 验证插件状态
        plugin_info = get_plugin_info("load_test_plugin")
        assert plugin_info is not None
        assert plugin_info.state == PluginState.INITIALIZED
        assert plugin_info.instance is not None

    def test_activate_plugin(self):
        """测试激活插件"""

        @Plugin
        class ActivateTestPlugin(PluginBase):
            name = "activate_test_plugin"
            version = "1.0.0"
            description = "激活测试插件"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "activate_test"

            def cleanup(self) -> None:
                pass

        # 注册插件
        register_plugin(ActivateTestPlugin, namespace="user")

        # 激活插件
        result = activate_plugin("activate_test_plugin")
        assert result is True

        # 验证插件状态
        plugin_info = get_plugin_info("activate_test_plugin")
        assert plugin_info is not None
        assert plugin_info.state == PluginState.ACTIVATED
        assert plugin_info.instance is not None
        assert plugin_info.instance.is_active is True

    def test_deactivate_plugin(self):
        """测试停用插件"""

        @Plugin
        class DeactivateTestPlugin(PluginBase):
            name = "deactivate_test_plugin"
            version = "1.0.0"
            description = "停用测试插件"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "deactivate_test"

            def cleanup(self) -> None:
                pass

        # 注册并激活插件
        register_plugin(DeactivateTestPlugin, namespace="user")
        activate_plugin("deactivate_test_plugin")

        # 停用插件
        result = deactivate_plugin("deactivate_test_plugin")
        assert result is True

        # 验证插件状态
        plugin_info = get_plugin_info("deactivate_test_plugin")
        assert plugin_info is not None
        assert plugin_info.state == PluginState.DEACTIVATED
        assert plugin_info.instance is not None
        assert plugin_info.instance.is_active is False

    def test_plugin_dependencies(self):
        """测试插件依赖"""

        @Plugin
        class CorePlugin(PluginBase):
            name = "core_plugin"
            version = "1.0.0"
            description = "核心插件"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "core"

            def cleanup(self) -> None:
                pass

        @Plugin
        class DependentPlugin(PluginBase):
            name = "dependent_plugin"
            version = "1.0.0"
            description = "依赖插件"
            author = "Test"
            dependencies = [PluginDependency("core_plugin", min_version="1.0.0")]

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "dependent"

            def cleanup(self) -> None:
                pass

        # 注册插件
        register_plugin(CorePlugin, namespace="framework", is_framework_plugin=True)
        register_plugin(DependentPlugin, namespace="user")

        # 分析依赖关系
        dependencies = analyze_dependencies()
        assert "core_plugin" in dependencies
        assert "dependent_plugin" in dependencies
        assert "core_plugin" in dependencies["dependent_plugin"]

        # 获取加载顺序
        load_order = get_load_order()
        assert load_order.index("core_plugin") < load_order.index("dependent_plugin")

    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""

        @Plugin
        class PluginA(PluginBase):
            name = "plugin_a"
            version = "1.0.0"
            description = "插件A"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "a"

            def cleanup(self) -> None:
                pass

        @Plugin
        class PluginB(PluginBase):
            name = "plugin_b"
            version = "1.0.0"
            description = "插件B"
            author = "Test"
            dependencies = [PluginDependency("plugin_c")]

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "b"

            def cleanup(self) -> None:
                pass

        @Plugin
        class PluginC(PluginBase):
            name = "plugin_c"
            version = "1.0.0"
            description = "插件C"
            author = "Test"
            dependencies = [PluginDependency("plugin_b")]

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "c"

            def cleanup(self) -> None:
                pass

        # 注册插件A和B
        register_plugin(PluginA, namespace="user")
        register_plugin(PluginB, namespace="user")

        # 尝试注册插件C（会形成循环依赖）
        with pytest.raises(PluginError, match="循环依赖"):
            register_plugin(PluginC, namespace="user")

    def test_namespace_management(self):
        """测试命名空间管理"""

        @Plugin
        class FrameworkPlugin(PluginBase):
            name = "framework_plugin"
            version = "1.0.0"
            description = "框架插件"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "framework"

            def cleanup(self) -> None:
                pass

        @Plugin
        class UserPlugin(PluginBase):
            name = "user_plugin"
            version = "1.0.0"
            description = "用户插件"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "user"

            def cleanup(self) -> None:
                pass

        # 注册插件到不同命名空间
        register_plugin(
            FrameworkPlugin, namespace="framework", is_framework_plugin=True
        )
        register_plugin(UserPlugin, namespace="user")

        # 按命名空间获取插件
        framework_plugins = get_plugins_by_namespace("framework")
        user_plugins = get_plugins_by_namespace("user")

        assert len(framework_plugins) == 1
        assert len(user_plugins) == 1
        assert framework_plugins[0].name == "framework_plugin"
        assert user_plugins[0].name == "user_plugin"

        # 获取框架插件和用户插件
        framework_plugins_list = get_framework_plugins()
        user_plugins_list = get_user_plugins()

        assert len(framework_plugins_list) == 1
        assert len(user_plugins_list) == 1

    def test_get_all_plugins(self):
        """测试获取所有插件"""

        @Plugin
        class Plugin1(PluginBase):
            name = "plugin_1"
            version = "1.0.0"
            description = "插件1"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "1"

            def cleanup(self) -> None:
                pass

        @Plugin
        class Plugin2(PluginBase):
            name = "plugin_2"
            version = "1.0.0"
            description = "插件2"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "2"

            def cleanup(self) -> None:
                pass

        # 注册插件
        register_plugin(Plugin1, namespace="user")
        register_plugin(Plugin2, namespace="user")

        # 获取所有插件
        all_plugins = get_all_plugins()
        assert len(all_plugins) == 2
        plugin_names = [p.name for p in all_plugins]
        assert "plugin_1" in plugin_names
        assert "plugin_2" in plugin_names


class TestPluginLifecycle:
    """测试插件生命周期"""

    def test_full_lifecycle(self):
        """测试完整生命周期"""
        lifecycle_states = []

        @Plugin
        class LifecycleTestPlugin(PluginBase):
            name = "lifecycle_test_plugin"
            version = "1.0.0"
            description = "生命周期测试插件"
            author = "Test"
            dependencies = []

            def initialize(self) -> bool:
                lifecycle_states.append("initialize")
                return True

            def execute(self, **kwargs):
                return "lifecycle_test"

            def cleanup(self) -> None:
                lifecycle_states.append("cleanup")

        # 注册插件
        register_plugin(LifecycleTestPlugin, namespace="user")

        # 验证初始状态
        plugin_info = get_plugin_info("lifecycle_test_plugin")
        assert plugin_info is not None
        assert plugin_info.state == PluginState.LOADED

        # 加载插件
        load_plugin("lifecycle_test_plugin")
        assert "initialize" in lifecycle_states
        plugin_info = get_plugin_info("lifecycle_test_plugin")
        assert plugin_info is not None
        assert plugin_info.state == PluginState.INITIALIZED

        # 激活插件
        activate_plugin("lifecycle_test_plugin")
        assert plugin_info.state == PluginState.ACTIVATED

        # 停用插件
        deactivate_plugin("lifecycle_test_plugin")
        assert "cleanup" in lifecycle_states
        assert plugin_info.state == PluginState.DEACTIVATED

        # 卸载插件
        unload_plugin("lifecycle_test_plugin")
        assert plugin_info.state == PluginState.UNLOADED


class TestPluginDiscovery:
    """测试插件发现"""

    def test_discover_plugins(self):
        """测试发现插件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建临时插件文件
            plugin_file = os.path.join(temp_dir, "test_plugin.py")
            with open(plugin_file, "w") as f:
                f.write(
                    """
from LStartlet import PluginBase, Plugin

@Plugin
class DiscoveredPlugin(PluginBase):
    name = "discovered_plugin"
    version = "1.0.0"
    description = "发现的插件"
    author = "Test"
    dependencies = []
    
    def initialize(self) -> bool:
        return True
    
    def execute(self, **kwargs):
        return "discovered"
    
    def cleanup(self) -> None:
        pass
"""
                )

            # 创建插件发现器
            plugin_manager = get_plugin_manager()
            discovery = PluginDiscovery(plugin_manager)

            # 发现插件
            discovered = discovery.discover_plugins([temp_dir])
            assert "test_plugin" in discovered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
