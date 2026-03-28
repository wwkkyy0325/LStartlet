"""
UI相关事件类型定义
用于事件系统接管UI组件的样式与实际逻辑连接
"""

from ..base_event import BaseEvent
from typing import Any, Optional, Dict, Callable


class UIComponentEvent(BaseEvent):
    """
    UI组件事件基类
    
    所有UI组件相关事件的基类，提供通用的UI事件属性和方法。
    
    Attributes:
        component_id (str): UI组件ID
        data (Optional[Any]): 事件相关数据
        
    Example:
        >>> event = UIComponentEvent("ui.update", "button_1", {"color": "red"})
    """

    def __init__(self, event_type: str, component_id: str, data: Optional[Any] = None) -> None:
        """
        初始化UI组件事件
        
        Args:
            event_type (str): 事件类型
            component_id (str): UI组件ID
            data (Optional[Any]): 事件相关数据，默认为 None
            
        Example:
            >>> event = UIComponentEvent("custom.ui.event", "component_123")
        """
        super().__init__(event_type)
        self.component_id = component_id
        self.data = data

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷数据
        
        Returns:
            Dict[str, Any]: 包含组件ID和事件数据的字典
            
        Example:
            >>> event = UIComponentEvent("test", "comp_1", "test_data")
            >>> payload = event.get_payload()
            >>> assert payload["component_id"] == "comp_1"
        """
        return {"component_id": self.component_id, "data": self.data}


class UIStyleUpdateEvent(UIComponentEvent):
    """
    UI样式更新事件
    
    当UI组件的样式需要更新时触发，包含新的样式数据。
    
    Event Type:
        EVENT_TYPE = "ui.style.update"
        
    Example:
        >>> event = UIStyleUpdateEvent("button_1", {"background": "blue", "color": "white"})
    """

    EVENT_TYPE = "ui.style.update"

    def __init__(self, component_id: str, style_data: Dict[str, Any]) -> None:
        """
        初始化UI样式更新事件
        
        Args:
            component_id (str): UI组件ID
            style_data (Dict[str, Any]): 新的样式数据字典
            
        Example:
            >>> event = UIStyleUpdateEvent("header", {"font_size": "16px", "color": "#333"})
        """
        super().__init__(self.EVENT_TYPE, component_id, style_data)


class UIConfigChangeEvent(UIComponentEvent):
    """
    UI配置变更事件
    
    当UI组件的配置发生变更时触发，包含配置变更信息。
    
    Event Type:
        EVENT_TYPE = "ui.config.change"
        
    Example:
        >>> event = UIConfigChangeEvent("chart_1", {"theme": "dark", "responsive": True})
    """

    EVENT_TYPE = "ui.config.change"

    def __init__(self, component_id: str, config_changes: Dict[str, Any]) -> None:
        """
        初始化UI配置变更事件
        
        Args:
            component_id (str): UI组件ID
            config_changes (Dict[str, Any]): 配置变更字典
            
        Example:
            >>> event = UIConfigChangeEvent("sidebar", {"collapsed": True})
        """
        super().__init__(self.EVENT_TYPE, component_id, config_changes)


class UIStateChangeEvent(UIComponentEvent):
    """
    UI状态变更事件
    
    当UI组件的状态发生变化时触发，包含状态变更信息。
    
    Event Type:
        EVENT_TYPE = "ui.state.change"
        
    Example:
        >>> event = UIStateChangeEvent("modal_1", {"visible": False, "loading": False})
    """

    EVENT_TYPE = "ui.state.change"

    def __init__(self, component_id: str, state_changes: Dict[str, Any]) -> None:
        """
        初始化UI状态变更事件
        
        Args:
            component_id (str): UI组件ID
            state_changes (Dict[str, Any]): 状态变更字典
            
        Example:
            >>> event = UIStateChangeEvent("form_1", {"valid": True, "dirty": False})
        """
        super().__init__(self.EVENT_TYPE, component_id, state_changes)


class UIMountAreaEvent(UIComponentEvent):
    """
    挂载区域事件
    
    当UI组件需要在特定区域挂载或卸载时触发。
    
    Event Type:
        EVENT_TYPE = "ui.mount.area"
        
    Example:
        >>> event = UIMountAreaEvent("widget_1", "mount", {"container": "sidebar"})
    """

    EVENT_TYPE = "ui.mount.area"

    def __init__(self, component_id: str, area_action: str, area_data: Dict[str, Any]) -> None:
        """
        初始化挂载区域事件
        
        Args:
            component_id (str): UI组件ID
            area_action (str): 区域操作类型（如 "mount", "unmount"）
            area_data (Dict[str, Any]): 区域相关数据
            
        Example:
            >>> event = UIMountAreaEvent("toolbar", "mount", {"position": "top"})
        """
        super().__init__(
            self.EVENT_TYPE, component_id, {"action": area_action, "data": area_data}
        )


class UIComponentLifecycleEvent(UIComponentEvent):
    """
    UI组件生命周期事件
    
    在UI组件的生命周期各个阶段触发（创建、挂载、更新、卸载等）。
    
    Event Type:
        EVENT_TYPE = "ui.component.lifecycle"
        
    Example:
        >>> event = UIComponentLifecycleEvent("panel_1", "mounted")
    """

    EVENT_TYPE = "ui.component.lifecycle"

    def __init__(self, component_id: str, lifecycle_stage: str) -> None:
        """
        初始化UI组件生命周期事件
        
        Args:
            component_id (str): UI组件ID
            lifecycle_stage (str): 生命周期阶段（如 "created", "mounted", "updated", "unmounted"）
            
        Example:
            >>> event = UIComponentLifecycleEvent("grid_1", "created")
        """
        super().__init__(self.EVENT_TYPE, component_id, {"stage": lifecycle_stage})


class RenderProcessReadyEvent(BaseEvent):
    """
    渲染进程准备就绪事件 - 用于通知主进程渲染进程已初始化完毕
    
    当渲染进程完成初始化并准备好接收UI指令时触发。
    
    Attributes:
        process_id (str): 渲染进程ID
        custom_ui_callback (Optional[Callable[[], None]]): 自定义UI回调函数
        
    Event Type:
        EVENT_TYPE = "ui.render.process.ready"
        
    Example:
        >>> event = RenderProcessReadyEvent("render_proc_1")
    """

    EVENT_TYPE = "ui.render.process.ready"

    def __init__(
        self, process_id: str, custom_ui_callback: Optional[Callable[[], None]] = None
    ) -> None:
        """
        初始化渲染进程准备就绪事件

        Args:
            process_id (str): 渲染进程ID
            custom_ui_callback (Optional[Callable[[], None]]): 自定义UI回调函数，
                如果提供则使用自定义UI，否则使用默认UI，默认为 None
                
        Example:
            >>> def custom_ui():
            ...     print("Custom UI initialized")
            ...
            >>> event = RenderProcessReadyEvent("renderer_1", custom_ui)
        """
        super().__init__(self.EVENT_TYPE)
        self.process_id = process_id
        self.custom_ui_callback = custom_ui_callback

    def get_payload(self) -> Dict[str, Any]:
        """
        获取事件载荷数据
        
        Returns:
            Dict[str, Any]: 包含进程ID和自定义UI标志的字典
            
        Example:
            >>> event = RenderProcessReadyEvent("proc_1")
            >>> payload = event.get_payload()
            >>> assert payload["process_id"] == "proc_1"
        """
        return {
            "process_id": self.process_id,
            "has_custom_ui": self.custom_ui_callback is not None,
        }