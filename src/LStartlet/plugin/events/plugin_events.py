"""
插件系统相关事件定义
"""

from LStartlet.core.event.base_event import BaseEvent
from typing import Dict, Any, Optional


class PluginLoadedEvent(BaseEvent):
    """插件加载事件"""

    EVENT_TYPE = "LStartlet.plugin.loaded"

    def __init__(
        self,
        plugin_id: str,
        plugin_name: str,
        version: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(self.EVENT_TYPE)
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name
        self.version = version
        self._plugin_metadata = metadata or {}

    def get_payload(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "version": self.version,
            "metadata": self._plugin_metadata,
        }


class PluginUnloadedEvent(BaseEvent):
    """插件卸载事件"""

    EVENT_TYPE = "LStartlet.plugin.unloaded"

    def __init__(self, plugin_id: str, plugin_name: str):
        super().__init__(self.EVENT_TYPE)
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name

    def get_payload(self) -> Dict[str, Any]:
        return {"plugin_id": self.plugin_id, "plugin_name": self.plugin_name}


class PluginInitializedEvent(BaseEvent):
    """插件初始化事件"""

    EVENT_TYPE = "LStartlet.plugin.initialized"

    def __init__(
        self,
        plugin_id: str,
        plugin_name: str,
        success: bool,
        error_message: Optional[str] = None,
    ):
        super().__init__(self.EVENT_TYPE)
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name
        self.success = success
        self.error_message = error_message

    def get_payload(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "success": self.success,
            "error_message": self.error_message,
        }


class PluginStartedEvent(BaseEvent):
    """插件启动事件"""

    EVENT_TYPE = "LStartlet.plugin.started"

    def __init__(
        self,
        plugin_id: str,
        plugin_name: str,
        success: bool,
        error_message: Optional[str] = None,
    ):
        super().__init__(self.EVENT_TYPE)
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name
        self.success = success
        self.error_message = error_message

    def get_payload(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "success": self.success,
            "error_message": self.error_message,
        }


class PluginStoppedEvent(BaseEvent):
    """插件停止事件"""

    EVENT_TYPE = "LStartlet.plugin.stopped"

    def __init__(
        self,
        plugin_id: str,
        plugin_name: str,
        success: bool,
        error_message: Optional[str] = None,
    ):
        super().__init__(self.EVENT_TYPE)
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name
        self.success = success
        self.error_message = error_message

    def get_payload(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "success": self.success,
            "error_message": self.error_message,
        }
