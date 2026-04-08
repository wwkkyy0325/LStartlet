"""
插件自动化测试
"""

import pytest
import tempfile
import os
from LStartlet import (
    PluginBase,
    Plugin,
    PluginDependency,
    get_plugin_auto_manager,
    get_plugin_lifecycle_integration,
    enable_plugin_automation,
    disable_plugin_automation,
    auto_start_plugins,
    auto_stop_plugins,
    integrate_plugins_with_framework,
    register_plugin_auto_start_hook,
    register_plugin_auto_stop_hook,
    register_plugin_error_handler,
    get_plugin_automation_status,
)


@pytest.fixture(autouse=True)
def setup_test_env():
    """为每个测试设置环境"""
    # 重置插件管理器
    import LStartlet._plugin_manager as pm_module
    import LStartlet._plugin_automation as pa_module

    # 重新创建插件管理器
    from LStartlet._plugin_manager import PluginManager

    pm_module._plugin_manager = PluginManager()

    # 重新创建自动化管理器
    pa_module._plugin_auto_manager = None
    pa_module._plugin_lifecycle_integration = None

    yield


class TestPluginAutomation:
    """测试插件自动化"""

    def test_enable_auto_discovery(self):
        """测试启用插件自动发现"""
        auto_manager = get_plugin_auto_manager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 启用自动发现
            auto_manager.enable_auto_discovery([temp_dir])

            assert auto_manager._auto_discovery_enabled is True
            assert temp_dir in auto_manager._plugin_dirs

    def test_disable_auto_discovery(self):
        """测试禁用插件自动发现"""
        auto_manager = get_plugin_auto_manager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 启用自动发现
            auto_manager.enable_auto_discovery([temp_dir])

            # 禁用自动发现
            auto_manager.disable_auto_discovery()

            assert auto_manager._auto_discovery_enabled is False
            assert len(auto_manager._plugin_dirs) == 0

    def test_enable_auto_load(self):
        """测试启用插件自动加载"""
        auto_manager = get_plugin_auto_manager()

        auto_manager.enable_auto_load()
        assert auto_manager._auto_load_enabled is True

    def test_enable_auto_activate(self):
        """测试启用插件自动激活"""
        auto_manager = get_plugin_auto_manager()

        auto_manager.enable_auto_activate()
        assert auto_manager._auto_activate_enabled is True

    def test_enable_full_automation(self):
        """测试启用完整自动化"""
        auto_manager = get_plugin_auto_manager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 启用完整自动化
            auto_manager.enable_full_automation([temp_dir])

            assert auto_manager._auto_discovery_enabled is True
            assert auto_manager._auto_load_enabled is True
            assert auto_manager._auto_activate_enabled is True
            assert temp_dir in auto_manager._plugin_dirs

    def test_disable_full_automation(self):
        """测试禁用完整自动化"""
        auto_manager = get_plugin_auto_manager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 启用完整自动化
            auto_manager.enable_full_automation([temp_dir])

            # 禁用完整自动化
            auto_manager.disable_full_automation()

            assert auto_manager._auto_discovery_enabled is False
            assert auto_manager._auto_load_enabled is False
            assert auto_manager._auto_activate_enabled is False
            assert len(auto_manager._plugin_dirs) == 0

    def test_auto_discover_plugins(self):
        """测试自动发现插件"""
        auto_manager = get_plugin_auto_manager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建临时插件文件
            plugin_file = os.path.join(temp_dir, "test_plugin.py")
            with open(plugin_file, "w", encoding="utf-8") as f:
                f.write("""
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
""")

            # 启用自动发现
            auto_manager.enable_auto_discovery([temp_dir])

            # 自动发现插件
            discovered = auto_manager.auto_discover_plugins()

            assert len(discovered) == 1
            assert discovered[0][0] == "test_plugin"

    def test_auto_start_hooks(self):
        """测试自动启动钩子"""
        auto_manager = get_plugin_auto_manager()

        hook_results = []

        def start_hook(result):
            hook_results.append(("start", result))

        # 注册启动钩子
        auto_manager.register_auto_start_hook(start_hook)

        assert len(auto_manager._auto_start_hooks) == 1

    def test_auto_stop_hooks(self):
        """测试自动停止钩子"""
        auto_manager = get_plugin_auto_manager()

        hook_results = []

        def stop_hook(result):
            hook_results.append(("stop", result))

        # 注册停止钩子
        auto_manager.register_auto_stop_hook(stop_hook)

        assert len(auto_manager._auto_stop_hooks) == 1

    def test_error_handlers(self):
        """测试错误处理器"""
        auto_manager = get_plugin_auto_manager()

        error_results = []

        def error_handler(error_info):
            error_results.append(error_info)

        # 注册错误处理器
        auto_manager.register_error_handler(error_handler)

        assert len(auto_manager._error_handlers) == 1

    def test_get_automation_status(self):
        """测试获取自动化状态"""
        auto_manager = get_plugin_auto_manager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 启用完整自动化
            auto_manager.enable_full_automation([temp_dir])

            # 注册钩子
            def hook(result):
                pass

            auto_manager.register_auto_start_hook(hook)
            auto_manager.register_auto_stop_hook(hook)

            # 获取状态
            status = auto_manager.get_automation_status()

            assert status["auto_discovery_enabled"] is True
            assert status["auto_load_enabled"] is True
            assert status["auto_activate_enabled"] is True
            assert temp_dir in status["plugin_dirs"]
            assert status["auto_start_hooks_count"] == 1
            assert status["auto_stop_hooks_count"] == 1


class TestPluginLifecycleIntegration:
    """测试插件生命周期集成"""

    def test_integrate_with_framework(self):
        """测试集成到框架"""
        integration = get_plugin_lifecycle_integration()

        # 集成到框架
        integration.integrate_with_framework()

        assert integration._integrated is True

    def test_get_integration_status(self):
        """测试获取集成状态"""
        integration = get_plugin_lifecycle_integration()

        # 未集成时
        assert integration.get_integration_status() is False

        # 集成后
        integration.integrate_with_framework()
        assert integration.get_integration_status() is True


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_enable_plugin_automation(self):
        """测试启用插件自动化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 启用插件自动化
            enable_plugin_automation([temp_dir])

            auto_manager = get_plugin_auto_manager()
            assert auto_manager._auto_discovery_enabled is True
            assert auto_manager._auto_load_enabled is True
            assert auto_manager._auto_activate_enabled is True

    def test_disable_plugin_automation(self):
        """测试禁用插件自动化"""
        # 启用插件自动化
        with tempfile.TemporaryDirectory() as temp_dir:
            enable_plugin_automation([temp_dir])

            # 禁用插件自动化
            disable_plugin_automation()

            auto_manager = get_plugin_auto_manager()
            assert auto_manager._auto_discovery_enabled is False
            assert auto_manager._auto_load_enabled is False
            assert auto_manager._auto_activate_enabled is False

    def test_get_plugin_automation_status(self):
        """测试获取插件自动化状态"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 启用插件自动化
            enable_plugin_automation([temp_dir])

            # 获取状态
            status = get_plugin_automation_status()

            assert status["auto_discovery_enabled"] is True
            assert status["auto_load_enabled"] is True
            assert status["auto_activate_enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
