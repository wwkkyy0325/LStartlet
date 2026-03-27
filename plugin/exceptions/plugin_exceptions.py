"""
插件系统异常定义
"""

from typing import Optional


class PluginError(Exception):
    """插件系统基础异常"""

    def __init__(
        self, plugin_id: str, message: str, inner_exception: Optional[Exception] = None
    ):
        self.plugin_id = plugin_id
        self.inner_exception = inner_exception
        super().__init__(f"插件 {plugin_id} 错误: {message}")


class PluginLoadError(PluginError):
    """插件加载错误"""

    def __init__(
        self, plugin_id: str, message: str, inner_exception: Optional[Exception] = None
    ):
        super().__init__(plugin_id, f"加载失败: {message}", inner_exception)


class PluginInitializeError(PluginError):
    """插件初始化错误"""

    def __init__(
        self, plugin_id: str, message: str, inner_exception: Optional[Exception] = None
    ):
        super().__init__(plugin_id, f"初始化失败: {message}", inner_exception)


class PluginDependencyError(PluginError):
    """插件依赖错误"""

    def __init__(
        self, plugin_id: str, dependency_name: str, required_version: str, message: str
    ):
        super().__init__(
            plugin_id,
            f"依赖 {dependency_name} (要求版本: {required_version}) 错误: {message}",
        )


class PluginNotFoundError(PluginError):
    """插件未找到错误"""

    def __init__(self, plugin_id: str):
        super().__init__(plugin_id, "插件未找到")


class PluginAlreadyLoadedError(PluginError):
    """插件已加载错误"""

    def __init__(self, plugin_id: str):
        super().__init__(plugin_id, "插件已加载")
