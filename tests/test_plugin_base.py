import pytest
from LStartlet import PluginBase, Plugin, set_project_root
import tempfile


@pytest.fixture(autouse=True)
def setup_test_env():
    """为每个测试设置临时项目根目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_root = set_project_root(temp_dir)
        yield temp_dir
        if original_root:
            set_project_root(original_root)


@pytest.mark.plugin
class TestPluginBase:
    """测试PluginBase基类"""

    def test_plugin_base_cannot_instantiate(self):
        """测试PluginBase不能直接实例化"""
        # PluginBase是抽象基类，不能直接实例化
        with pytest.raises(TypeError):
            plugin = PluginBase()  # type: ignore

    def test_plugin_inheritance(self):
        """测试插件继承PluginBase并实现所有抽象方法"""

        @Plugin
        class CustomPlugin(PluginBase):
            def initialize(self) -> bool:
                return True

            def execute(self, **kwargs):
                return "custom execution"

            def cleanup(self) -> None:
                pass

        plugin = CustomPlugin()
        assert plugin.execute() == "custom execution"
        assert isinstance(plugin, PluginBase)
        assert plugin.initialize() is True
        plugin.cleanup()  # 应该正常执行

    def test_plugin_activation(self):
        """测试插件激活和停用"""

        @Plugin
        class ActivationPlugin(PluginBase):
            def __init__(self):
                super().__init__()
                self.initialized = False
                self.cleaned = False

            def initialize(self) -> bool:
                self.initialized = True
                return True

            def execute(self, **kwargs):
                return "activated"

            def cleanup(self) -> None:
                self.cleaned = True

        plugin = ActivationPlugin()
        assert not plugin.is_active

        # 激活插件
        assert plugin.activate() is True
        assert plugin.is_active is True
        assert plugin.initialized is True

        # 停用插件
        plugin.deactivate()
        assert plugin.is_active is False
        assert plugin.cleaned is True
