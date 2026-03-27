"""
UI相关事件类型定义
用于事件系统接管UI组件的样式与实际逻辑连接
"""

from ..base_event import BaseEvent
from typing import Any, Optional, Dict, Callable


class UIComponentEvent(BaseEvent):
    """UI组件事件基类"""

    def __init__(self, event_type: str, component_id: str, data: Optional[Any] = None):
        super().__init__(event_type)
        self.component_id = component_id
        self.data = data

    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷数据"""
        return {"component_id": self.component_id, "data": self.data}


class UIStyleUpdateEvent(UIComponentEvent):
    """UI样式更新事件"""

    EVENT_TYPE = "ui.style.update"

    def __init__(self, component_id: str, style_data: Dict[str, Any]):
        super().__init__(self.EVENT_TYPE, component_id, style_data)


class UIConfigChangeEvent(UIComponentEvent):
    """UI配置变更事件"""

    EVENT_TYPE = "ui.config.change"

    def __init__(self, component_id: str, config_changes: Dict[str, Any]):
        super().__init__(self.EVENT_TYPE, component_id, config_changes)


class UIStateChangeEvent(UIComponentEvent):
    """UI状态变更事件"""

    EVENT_TYPE = "ui.state.change"

    def __init__(self, component_id: str, state_changes: Dict[str, Any]):
        super().__init__(self.EVENT_TYPE, component_id, state_changes)


class UIMountAreaEvent(UIComponentEvent):
    """挂载区域事件"""

    EVENT_TYPE = "ui.mount.area"

    def __init__(self, component_id: str, area_action: str, area_data: Dict[str, Any]):
        super().__init__(
            self.EVENT_TYPE, component_id, {"action": area_action, "data": area_data}
        )


class UIComponentLifecycleEvent(UIComponentEvent):
    """UI组件生命周期事件"""

    EVENT_TYPE = "ui.component.lifecycle"

    def __init__(self, component_id: str, lifecycle_stage: str):
        super().__init__(self.EVENT_TYPE, component_id, {"stage": lifecycle_stage})


class RenderProcessReadyEvent(BaseEvent):
    """渲染进程准备就绪事件 - 用于通知主进程渲染进程已初始化完毕"""

    EVENT_TYPE = "ui.render.process.ready"

    def __init__(
        self, process_id: str, custom_ui_callback: Optional[Callable[[], None]] = None
    ):
        """
        初始化渲染进程准备就绪事件

        Args:
            process_id: 渲染进程ID
            custom_ui_callback: 自定义UI回调函数，如果提供则使用自定义UI，否则使用默认UI
        """
        super().__init__(self.EVENT_TYPE)
        self.process_id = process_id
        self.custom_ui_callback = custom_ui_callback

    def get_payload(self) -> Dict[str, Any]:
        """获取事件载荷数据"""
        return {
            "process_id": self.process_id,
            "has_custom_ui": self.custom_ui_callback is not None,
        }
