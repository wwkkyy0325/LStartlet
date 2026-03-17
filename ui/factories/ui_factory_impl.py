"""
UI工厂实现模块
基于DI容器的UI工厂具体实现
"""

import sys
from typing import Optional, Dict, Any, Callable, List

from PySide6.QtWidgets import QApplication, QWidget

from core.logger import info, error
from core.event.event_bus import EventBus
from core.scheduler.tick import TickComponent
from ui.factories.ui_factory_interface import IUIFactory
from ui.core.standard_window_manager import StandardWindowManager
from ui.core.custom_window_manager import CustomWindowManager
from ui.components.frosted_glass_window import FrostedGlassWindow
from ui.config.ui_config import UIConfig
from ui.factories.component_factory_interface import IComponentFactory
from ui.factories.component_factory_impl import ComponentFactoryImpl


class UIFactoryImpl(IUIFactory):
    """UI工厂具体实现类"""
    
    def __init__(
        self,
        event_bus: EventBus,
        tick_component: TickComponent,
        component_factory: Optional[IComponentFactory] = None,
        on_close_callback: Optional[Callable[[], None]] = None
    ):
        """
        初始化UI工厂
        
        Args:
            event_bus: 事件总线实例（通过DI注入）
            tick_component: Tick组件实例（通过DI注入）
            component_factory: 组件工厂实例（通过DI注入，可选）
            on_close_callback: 窗口关闭回调函数
        """
        self.event_bus = event_bus
        self.tick_component = tick_component
        self.component_factory = component_factory or ComponentFactoryImpl()
        self.on_close_callback = on_close_callback
        self.qt_app: Optional[QApplication] = None
        self.current_ui: Optional[QWidget] = None
        
        # 确保TickComponent有事件总线 - 使用安全的方式检查并设置
        if not self.tick_component.has_event_bus:
            self.tick_component.set_event_bus(self.event_bus)
        
    def create_qt_application(self, argv: Optional[List[str]] = None) -> QApplication:
        """创建Qt应用程序实例"""
        if self.qt_app is not None:
            return self.qt_app
            
        # 检查是否已经存在QApplication实例
        existing_app = QApplication.instance()
        if existing_app is not None:
            # 确保existing_app是QApplication类型
            assert isinstance(existing_app, QApplication)
            self.qt_app = existing_app
            return self.qt_app
            
        if argv is None:
            argv = sys.argv
            
        self.qt_app = QApplication(argv)
        info("Qt应用程序实例创建成功")
        return self.qt_app
    
    def create_standard_ui(self, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """创建标准UI（带系统边框）"""
        try:
            info("创建标准UI...")
            
            # 创建UI配置 - 直接使用字典初始化，而不是from_dict
            ui_config = UIConfig()
            if config:
                # 更新配置字段
                for key, value in config.items():
                    if hasattr(ui_config, key):
                        setattr(ui_config, key, value)
            
            # 创建标准窗口管理器
            window_manager = StandardWindowManager(ui_config)
            
            # 设置组件工厂
            window_manager.set_component_factory(self._create_component_wrapper)
            
            main_window = window_manager.get_main_window()
            
            if main_window is None:
                raise RuntimeError("标准UI创建失败：主窗口为空")
                
            self.current_ui = main_window
            main_window.show()
            
            # 注册tick回调
            if self.tick_component:
                self.tick_component.add_tick_callback(self._on_mouse_position_tick)
                info("标准UI的tick回调已注册")
            
            info("标准UI创建成功")
            return main_window
            
        except Exception as e:
            error(f"标准UI创建失败：{e}")
            raise
    
    def create_custom_ui(self, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """创建自定义UI（无边框磨砂玻璃效果）"""
        try:
            info("创建自定义UI...")
            
            # 创建UI配置 - 直接使用字典初始化，而不是from_dict
            ui_config = UIConfig()
            if config:
                # 更新配置字段
                for key, value in config.items():
                    if hasattr(ui_config, key):
                        setattr(ui_config, key, value)
            
            # 创建自定义窗口管理器
            window_manager = CustomWindowManager(ui_config)
            
            # 设置组件工厂
            window_manager.set_component_factory(self._create_component_wrapper)
            
            main_window = window_manager.get_main_window()
            
            if main_window is None:
                raise RuntimeError("自定义UI创建失败：主窗口为空")
                
            self.current_ui = main_window
            main_window.show()
            
            # 注册tick回调
            if self.tick_component:
                self.tick_component.add_tick_callback(self._on_mouse_position_tick)
                info("自定义UI的tick回调已注册")
            
            info("自定义UI创建成功")
            return main_window
            
        except Exception as e:
            error(f"自定义UI创建失败：{e}")
            raise
    
    def create_frosted_glass_ui(self, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """创建磨砂玻璃效果UI"""
        try:
            info("创建磨砂玻璃效果UI...")
            
            # 创建磨砂玻璃窗口
            window = FrostedGlassWindow(
                on_close_callback=self.cleanup_resources if self.on_close_callback is None else self.on_close_callback
            )
            
            # 应用配置（如果有）
            if config:
                ui_config = UIConfig()
                # 更新配置字段
                for key, value in config.items():
                    if hasattr(ui_config, key):
                        setattr(ui_config, key, value)
                # 检查window是否有update_config方法
                if hasattr(window, 'update_config'):
                    window.update_config(ui_config)
            
            # 如果窗口有挂载区域，设置组件工厂
            if hasattr(window, 'mount_area_manager') and getattr(window, 'mount_area_manager', None):
                mount_area_manager = getattr(window, 'mount_area_manager')
                if hasattr(mount_area_manager, 'set_component_factory'):
                    mount_area_manager.set_component_factory(self._create_component_wrapper)
            
            self.current_ui = window
            window.show()
            
            # 写入文件确认窗口创建
            with open("window_created.txt", "w") as f:
                f.write("Window created at startup\n")
            
            # 注册tick回调
            if self.tick_component:
                self.tick_component.add_tick_callback(self._on_mouse_position_tick)
                info("磨砂玻璃UI的tick回调已注册")
            
            info("磨砂玻璃UI创建成功")
            return window
            
        except Exception as e:
            error(f"磨砂玻璃UI创建失败：{e}")
            raise
    
    def _create_component_wrapper(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """组件工厂包装函数，适配AbstractUIManager的接口"""
        return self.component_factory.create_component(component_type, config)
    
    def _on_mouse_position_tick(self, tick_count: int, elapsed_time: float) -> None:
        """鼠标位置监听tick回调"""
        try:
            # 如果UI存在且可见，更新鼠标相关状态
            if self.current_ui and self.current_ui.isVisible():
                # 检查是否是FrostedGlassWindow类型
                if isinstance(self.current_ui, FrostedGlassWindow):
                    if hasattr(self.current_ui, 'update_mouse_state_via_tick'):
                        self.current_ui.update_mouse_state_via_tick()
                # 其他类型的UI可能需要不同的处理方式
                
        except Exception as e:
            # 记录异常但不中断主程序
            error(f"鼠标位置tick回调异常：{e}")
    
    def cleanup_resources(self) -> None:
        """清理UI相关资源"""
        try:
            info("开始清理UI资源...")
            
            # 从tick组件中移除回调
            if self.tick_component:
                self.tick_component.remove_tick_callback(self._on_mouse_position_tick)
            
            # 清理当前UI
            if self.current_ui:
                self.current_ui.close()
                self.current_ui = None
            
            info("UI资源清理完成")
            
        except Exception as e:
            error(f"UI资源清理过程中发生错误：{e}")
    
    def get_qt_app(self) -> Optional[QApplication]:
        """获取Qt应用程序实例"""
        return self.qt_app
    
    def get_component_factory(self) -> IComponentFactory:
        """获取组件工厂实例"""
        return self.component_factory