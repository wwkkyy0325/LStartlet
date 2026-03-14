"""
UI工厂模块
负责UI的创建、管理和生命周期控制
"""

import sys
from typing import Optional, Callable, cast

from PySide6.QtWidgets import QApplication

from core.logger import info, error
from core.event.event_bus import EventBus
from core.event.events.ui_events import RenderProcessReadyEvent
from core.scheduler.tick import TickComponent
from ui.components import FrostedGlassWindow
from core.di.app_container import get_app_container


class UIFactory:
    """UI工厂类，负责UI的创建和管理"""
    
    def __init__(self):
        # 使用DI容器获取依赖
        self.event_bus = get_app_container().resolve(EventBus)
        self.tick_component = get_app_container().resolve(TickComponent)
        self.custom_ui_callback: Optional[Callable[[], None]] = None
        self.qt_app: Optional[QApplication] = None
        self.frosted_glass_window: Optional[FrostedGlassWindow] = None
        
    def start_render_process(self, timeout: float = 5.0) -> bool:
        """启动 UI 渲染（实际是在主线程中创建 UI）"""
        try:
            info("开始初始化UI...")
            
            # 初始化 Qt 应用
            self.qt_app = QApplication(sys.argv)
            
            # 直接创建磨砂玻璃 UI
            self.frosted_glass_window = self.create_frosted_glass_ui()
            
            # 使用全局tick组件进行鼠标位置监听
            if self.tick_component:
                self.tick_component.add_tick_callback(self._on_mouse_position_tick)
                info("uitick注册到内存")
            
            return True
            
        except Exception as e:
            error(f"UI 初始化失败：{e}")
            return False
    
    def _on_mouse_position_tick(self, tick_count: int, elapsed_time: float):
        """鼠标位置监听tick回调 - 使用系统的tick更新鼠标状态"""
        try:
            # 如果窗口存在且可见，更新鼠标相关状态
            if self.frosted_glass_window and self.frosted_glass_window.isVisible():
                # 触发窗口的鼠标状态更新
                self.frosted_glass_window.update_mouse_state_via_tick()
                
        except Exception:
            # 静默处理异常，避免影响主程序
            pass
    
    def create_frosted_glass_ui(self) -> FrostedGlassWindow:
        """创建磨砂玻璃效果的自定义 UI"""
        try:
            info("创建磨砂玻璃效果 UI...")
            window = FrostedGlassWindow(on_close_callback=self.cleanup_resources)
            window.show()
            info("磨砂玻璃 UI 创建成功")
            
            # 写入文件确认窗口创建
            with open("window_created.txt", "w") as f:
                f.write("Window created at startup\n")
            
            return window
            
        except Exception as e:
            error(f"磨砂玻璃 UI 创建失败：{e}")
            raise
    
    def _on_render_process_ready(self, event: RenderProcessReadyEvent) -> bool:
        """处理渲染进程准备就绪事件 - 此方法已废弃，UI 在 start_render_process 中直接创建"""
        try:
            info(f"接收到渲染进程准备就绪事件（事件监听模式），进程 ID: {event.process_id}")
            # 不再通过事件回调创建 UI，UI 已在 start_render_process 中创建
            return True
            
        except Exception as e:
            error(f"处理渲染进程准备就绪事件失败：{e}")
            return False
    
    def cleanup_resources(self) -> None:
        """清理 UI 相关资源"""
        try:
            info("开始清理 UI 资源...")
            
            # 从全局tick组件中移除回调
            if self.tick_component:
                self.tick_component.remove_tick_callback(self._on_mouse_position_tick)
            
            # Qt 应用会在退出时自动清理
            info("UI 资源清理完成")
            
        except Exception as e:
            error(f"UI 资源清理过程中发生错误：{e}")
    
    def get_qt_app(self) -> Optional[QApplication]:
        """获取 Qt 应用实例"""
        return self.qt_app
        
    def register_event_listeners(self) -> None:
        """注册UI 相关的事件监听器"""
        try:
            # 监听渲染进程准备就绪事件
            self.event_bus.subscribe_lambda(
                RenderProcessReadyEvent.EVENT_TYPE,
                lambda event: self._on_render_process_ready(cast(RenderProcessReadyEvent, event)),
                "render_process_ready_handler"
            )
            
            info("UI事件监听器注册完成")
            
        except Exception as e:
            error(f"UI事件监听器注册失败：{e}")
