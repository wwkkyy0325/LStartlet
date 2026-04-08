"""
按钮事件处理测试 - 验证条件过滤和主题路由功能
"""

import sys
from pathlib import Path
from dataclasses import dataclass

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from LStartlet import Event, OnEvent, OnSingleEvent, Component, publish_event


@dataclass
class _TestButtonEvent(Event):
    button_id: str
    topic: str = "default"


@Component
class _TestButtonHandler:
    """测试按钮事件处理器"""

    def __init__(self):
        self.save_calls = []
        self.cancel_calls = []
        self.generic_calls = []
        self.toolbar_calls = []
        self.dialog_calls = []
        self.all_calls = []
        self.single_calls = []
        self.multi_calls = []

        # 手动注册实例方法
        from LStartlet._event_decorator import _event_bus

        # 条件过滤器处理器
        _event_bus.subscribe(
            _TestButtonEvent,
            self.handle_save,
            condition=lambda e: e.button_id == "save",
        )
        _event_bus.subscribe(
            _TestButtonEvent,
            self.handle_cancel,
            condition=lambda e: e.button_id == "cancel",
        )
        _event_bus.subscribe(_TestButtonEvent, self.handle_generic)

        # 主题路由处理器
        _event_bus.subscribe(_TestButtonEvent, self.handle_toolbar, topic="toolbar")
        _event_bus.subscribe(_TestButtonEvent, self.handle_dialog, topic="dialog")
        _event_bus.subscribe(_TestButtonEvent, self.handle_all)

        # 单线和多线处理器
        _event_bus.subscribe_single(
            _TestButtonEvent,
            self.handle_special_single,
            condition=lambda e: e.button_id == "special",
        )
        _event_bus.subscribe(
            _TestButtonEvent,
            self.handle_special_multi,
            condition=lambda e: e.button_id == "special",
        )

    def handle_save(self, event: _TestButtonEvent):
        self.save_calls.append(event.button_id)

    def handle_cancel(self, event: _TestButtonEvent):
        self.cancel_calls.append(event.button_id)

    def handle_generic(self, event: _TestButtonEvent):
        self.generic_calls.append(event.button_id)

    def handle_toolbar(self, event: _TestButtonEvent):
        self.toolbar_calls.append(event.button_id)

    def handle_dialog(self, event: _TestButtonEvent):
        self.dialog_calls.append(event.button_id)

    def handle_all(self, event: _TestButtonEvent):
        self.all_calls.append(event.button_id)

    def handle_special_single(self, event: _TestButtonEvent):
        self.single_calls.append(f"single:{event.button_id}")

    def handle_special_multi(self, event: _TestButtonEvent):
        self.multi_calls.append(f"multi:{event.button_id}")


def test_condition_filtering():
    """测试条件过滤器"""
    handler = _TestButtonHandler()

    # 发布保存按钮事件
    save_event = _TestButtonEvent("save", "toolbar")
    publish_event(save_event)

    # 发布取消按钮事件
    cancel_event = _TestButtonEvent("cancel", "dialog")
    publish_event(cancel_event)

    # 发布其他按钮事件
    other_event = _TestButtonEvent("other", "menu")
    publish_event(other_event)

    # 验证条件过滤器工作正常
    assert len(handler.save_calls) == 1
    assert handler.save_calls[0] == "save"

    assert len(handler.cancel_calls) == 1
    assert handler.cancel_calls[0] == "cancel"

    # 通用处理器应该处理所有事件
    assert len(handler.generic_calls) == 3
    assert handler.generic_calls == ["save", "cancel", "other"]


def test_topic_routing():
    """测试主题路由"""
    handler = _TestButtonHandler()

    # 发布工具栏事件
    toolbar_event = _TestButtonEvent("btn1", "toolbar")
    publish_event(toolbar_event)

    # 发布对话框事件
    dialog_event = _TestButtonEvent("btn2", "dialog")
    publish_event(dialog_event)

    # 发布其他主题事件
    menu_event = _TestButtonEvent("btn3", "menu")
    publish_event(menu_event)

    # 验证主题路由工作正常
    assert len(handler.toolbar_calls) == 1
    assert handler.toolbar_calls[0] == "btn1"

    assert len(handler.dialog_calls) == 1
    assert handler.dialog_calls[0] == "btn2"

    # 通用处理器处理所有事件
    assert len(handler.all_calls) == 3


def test_single_event_with_condition():
    """测试带条件的单线事件"""
    handler = _TestButtonHandler()

    # 发布特殊按钮事件
    special_event = _TestButtonEvent("special", "default")
    publish_event(special_event)

    # 发布普通按钮事件
    normal_event = _TestButtonEvent("normal", "default")
    publish_event(normal_event)

    # 单线处理器只处理符合条件的事件
    assert len(handler.single_calls) == 1
    assert handler.single_calls[0] == "single:special"

    # 多线处理器也只处理符合条件的事件
    assert len(handler.multi_calls) == 1
    assert handler.multi_calls[0] == "multi:special"
