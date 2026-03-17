# -*- coding: utf-8 -*-
"""
OCR项目主入口文件
负责初始化配置、注册核心工具、启动主进程和渲染进程
"""

# =============== 日志级别配置 ===============
# 可选值: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
# 修改此处即可改变日志输出级别
LOG_LEVEL = "DEBUG"
# =========================================

from logging import warning
import os
import sys
import time
from typing import cast, Optional
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QStackedWidget, QFrame, QScrollArea
)
from PySide6.QtGui import QAction

# 核心模块导入
from core.config.config_manager import ConfigManager
from core.logger import configure_logger, info, error, set_process_type
from core.logger.level import LogLevel  # 添加LogLevel导入
from core.error import handle_error, register_global_error_handler  # 添加register_global_error_handler导入
from core.path import get_project_root, join_paths
from core.event.event_bus import EventBus
from core.event.events.ui_events import RenderProcessReadyEvent
from core.event.events.scheduler_events import ApplicationLifecycleEvent
from core.scheduler.tick import TickComponent, TickConfig
from ui.factories.ui_factory_interface import IUIFactory  # 使用新的UI工厂接口

# 新增模块导入
from plugin import initialize_plugin_system
from core.persistence import initialize_persistence_system

# 依赖注入容器（延迟导入）
from core.di import ServiceContainer, ServiceLifetime
from core.di.app_container import get_app_container


class MainApplication:
    """主应用程序类"""
    
    def __init__(self):
        self.container: ServiceContainer = get_app_container()  # 使用全局应用容器
        self.config_manager = None
        self.event_bus = None
        self.render_process_ready = False
        self.custom_ui_callback = None
        self.render_process_thread = None
        self.qt_app = None
        self.tick_component = None  # 添加tick组件引用
        self.plugin_manager = None  # 插件管理器
        self.persistence_manager = None  # 持久化管理器
        self.ui_factory: Optional[IUIFactory] = None  # 使用新的UI工厂接口
        
    def initialize(self) -> bool:
        """初始化应用程序"""
        try:
            # 注册全局错误处理器（在日志配置之前）
            register_global_error_handler()
            
            # 设置当前进程类型为主进程
            set_process_type("main")
            
            # 配置日志系统 - 使用入口处定义的日志级别
            log_level_map = {
                "DEBUG": LogLevel.DEBUG,
                "INFO": LogLevel.INFO,
                "WARNING": LogLevel.WARNING,
                "ERROR": LogLevel.ERROR,
                "CRITICAL": LogLevel.CRITICAL
            }
            actual_log_level = log_level_map.get(LOG_LEVEL.upper(), LogLevel.DEBUG)
            configure_logger(level=actual_log_level)
            
            info("开始初始化OCR主应用程序...")
            
            # 1. 初始化持久化系统
            if not self._initialize_persistence_system():
                error("持久化系统初始化失败")
                return False
            
            # 2. 检查并初始化配置文件
            if not self._initialize_config():
                error("配置初始化失败")
                return False
            
            # 3. 获取事件总线实例（从DI容器）
            self.event_bus = self.container.resolve(EventBus)
            
            # 4. 初始化20Hz的tick系统 (每50ms一个tick)
            if not self._initialize_tick_system():
                error("Tick系统初始化失败")
                return False
            
            # 5. 初始化插件系统
            if not self._initialize_plugin_system():
                error("插件系统初始化失败")
                return False
            
            # 6. 初始化UI工厂（从DI容器获取）
            self.ui_factory = self.container.resolve(IUIFactory)
            
            info("主应用程序初始化完成")
            return True
            
        except Exception as e:
            error(f"应用程序初始化异常: {e}")
            handle_error(e)
            return False
    
    def _initialize_config(self) -> bool:
        """初始化配置管理器"""
        try:
            project_root = get_project_root()
            config_file = join_paths(project_root, "config.json")
            
            # 检查配置文件是否存在
            if not os.path.exists(config_file):
                info("配置文件不存在，创建默认配置文件...")
                self.config_manager = self.container.resolve(ConfigManager)
                # 保存默认配置到文件
                self.config_manager.save_to_file(config_file)
                info(f"默认配置文件已创建: {config_file}")
            else:
                info(f"加载现有配置文件: {config_file}")
                self.config_manager = self.container.resolve(ConfigManager)
            
            return True
            
        except Exception as e:
            error(f"配置初始化失败: {e}")
            handle_error(e)
            return False
    
    def _initialize_tick_system(self) -> bool:
        """初始化20Hz的tick系统"""
        try:
            # 创建20Hz的tick配置 (50ms间隔)
            tick_config = TickConfig(
                interval=0.05,  # 50ms = 20Hz
                auto_start=True,
                enable_logging=False
            )
            
            self.tick_component = TickComponent(tick_config)
            
            # 将 TickComponent 注册到容器中
            self.container.register(TickComponent, instance=self.tick_component, lifetime=ServiceLifetime.SINGLETON)
            
            info("20Hz Tick系统初始化完成")
            return True
            
        except Exception as e:
            error(f"Tick系统初始化失败: {e}")
            handle_error(e)
            return False
    
    def _initialize_persistence_system(self) -> bool:
        """初始化持久化系统"""
        try:
            project_root = get_project_root()
            data_dir = join_paths(project_root, "data")
            
            self.persistence_manager = initialize_persistence_system(self.container, data_dir)
            
            info("持久化系统初始化完成")
            return True
            
        except Exception as e:
            error(f"持久化系统初始化失败: {e}")
            handle_error(e)
            return False
    
    def _initialize_plugin_system(self) -> bool:
        """初始化插件系统"""
        try:
            assert self.event_bus is not None
            
            self.plugin_manager = initialize_plugin_system(self.container, self.event_bus)
            
            # 暂时不自动加载插件目录中的插件
            # project_root = get_project_root()
            # plugin_dir = join_paths(project_root, "plugins")
            # 
            # if os.path.exists(plugin_dir):
            #     self.plugin_manager.load_plugins([plugin_dir])
            #     info(f"加载插件目录: {plugin_dir}")
            # else:
            #     info("插件目录不存在，跳过插件加载")
            
            # 初始化所有插件（目前为空）
            if not self.plugin_manager.initialize_all_plugins():
                warning("部分插件初始化失败，但继续启动应用")
            
            info("插件系统初始化完成")
            return True
            
        except Exception as e:
            error(f"插件系统初始化失败: {e}")
            handle_error(e)
            return False
    
    def _register_event_listeners(self) -> None:
        """注册事件监听器"""
        try:
            assert self.event_bus is not None
            
            # 监听渲染进程准备就绪事件
            self.event_bus.subscribe_lambda(
                RenderProcessReadyEvent.EVENT_TYPE,
                lambda event: self._on_render_process_ready(cast(RenderProcessReadyEvent, event)),
                "render_process_ready_handler"
            )
            
            info("事件监听器注册完成")
            
        except Exception as e:
            error(f"事件监听器注册失败: {e}")
            handle_error(e)
    
    def _on_render_process_ready(self, event: RenderProcessReadyEvent) -> bool:
        """处理渲染进程准备就绪事件"""
        try:
            self.render_process_ready = True
            # 直接赋值，类型已经正确
            self.custom_ui_callback = event.custom_ui_callback
            
            info(f"接收到渲染进程准备就绪事件，进程ID: {event.process_id}")
            
            if event.custom_ui_callback:
                info("检测到自定义UI回调，将使用自定义UI")
            else:
                info("未检测到自定义UI回调，将使用默认UI")
            
            return True
            
        except Exception as e:
            error(f"处理渲染进程准备就绪事件失败: {e}")
            handle_error(e)
            return False
    
    def start_render_process(self, timeout: float = 5.0) -> bool:
        """启动渲染进程"""
        try:
            assert self.ui_factory is not None
            
            # 创建Qt应用程序
            self.qt_app = self.ui_factory.create_qt_application(sys.argv)
            
            # 创建默认UI（磨砂玻璃效果）
            self._create_default_ui()
            
            return True
            
        except Exception as e:
            error(f"启动渲染进程失败: {e}")
            handle_error(e)
            return False
    
    def _run_render_process(self) -> None:
        """运行渲染进程"""
        try:
            # 设置渲染进程类型
            set_process_type("renderer")
            
            # 发布渲染进程准备就绪事件
            render_ready_event = RenderProcessReadyEvent(
                process_id="renderer_1",
                custom_ui_callback=None  # 默认没有自定义UI
            )
            assert self.event_bus is not None
            self.event_bus.publish(render_ready_event)
            
            info("渲染进程初始化完成")
            
        except Exception as e:
            error(f"渲染进程运行失败: {e}")
            handle_error(e)
    
    def _create_default_ui(self) -> None:
        """创建默认UI - 强制使用磨砂玻璃效果"""
        try:
            info("创建磨砂玻璃效果 UI...")
            if not self.ui_factory:
                error("UI工厂未初始化，无法创建磨砂玻璃 UI")
                raise RuntimeError("UI工厂未初始化")
            
            # 强制使用 UI工厂类创建磨砂玻璃窗口
            window = self.ui_factory.create_frosted_glass_ui()
            info(f"磨砂玻璃 UI 创建成功：{window}")
            
            # 创建简单的文件菜单
            if hasattr(window, 'create_simple_file_menu'):
                window.create_simple_file_menu()
                info("简单文件菜单创建成功")
            
            # 挂载左侧栏组件到左侧专用区域
            from ui.components import SidebarWidget, CentralContentManager
            sidebar = SidebarWidget()
            
            # 将侧边栏设置为左侧区域的子组件
            if hasattr(window, '_left_sidebar_area') and window._left_sidebar_area:
                # 检查是否已有布局
                existing_layout = window._left_sidebar_area.layout()
                if existing_layout is None:
                    layout = QVBoxLayout()
                    layout.setContentsMargins(0, 0, 0, 0)
                    window._left_sidebar_area.setLayout(layout)
                else:
                    layout = existing_layout
                layout.addWidget(sidebar)
                window._left_sidebar_area.show()  # 显示左侧区域
                info("左侧栏组件挂载到左侧专用区域成功")
            
            # 创建中央内容管理器并挂载到中央挂载区域
            central_manager = CentralContentManager()
            central_manager.create_default_contents()
            
            # 挂载到中央挂载区域
            if hasattr(window, '_mount_area') and window._mount_area:
                success = window._mount_area.mount_component(central_manager)
                if success:
                    info("中央内容管理器挂载成功")
                else:
                    error("中央内容管理器挂载失败")
            
            # 建立信号连接：侧边栏的选择事件连接到中央内容管理器的显示/隐藏方法
            sidebar.view_selected.connect(central_manager.show_content)
            sidebar.view_deselected.connect(central_manager.hide_content)
            
        except Exception as e:
            error(f"磨砂玻璃 UI 创建失败，程序退出：{e}")
            handle_error(e)
            raise  # 重新抛出异常，让程序退出
    
    def _cleanup_resources(self) -> None:
        """清理资源"""
        try:
            info("开始清理应用程序资源...")
            
            # 清理插件系统
            if self.plugin_manager:
                self.plugin_manager.cleanup_all_plugins()
            
            # 清理持久化系统
            if self.persistence_manager:
                self.persistence_manager.close_all_storages()
            
            # 清理UI资源
            if self.ui_factory:
                self.ui_factory.cleanup_resources()
            
            if self.event_bus is not None:
                # 发布应用程序停止事件
                app_stopping_event = ApplicationLifecycleEvent("stopping", "user_requested")
                self.event_bus.publish(app_stopping_event)
                
                # 等待一段时间让其他组件完成清理
                time.sleep(0.1)
                
                # 发布应用程序已停止事件
                app_stopped_event = ApplicationLifecycleEvent("stopped", "user_requested")
                self.event_bus.publish(app_stopped_event)
            
            # 全局进程管理器会在程序退出时自动清理
            info("应用程序资源清理完成")
            
        except Exception as e:
            error(f"资源清理过程中发生错误: {e}")
            handle_error(e)
    
    def run(self) -> int:
        """运行主应用程序"""
        try:
            if not self.initialize():
                return 1
            
            # 启动渲染进程
            if not self.start_render_process():
                return 1
            
            info("OCR应用程序启动成功！")
            
            # 运行Qt应用
            qt_app = self.ui_factory.get_qt_app() if self.ui_factory else None
            if qt_app:
                # 连接Qt应用的aboutToQuit信号到清理函数
                qt_app.aboutToQuit.connect(self._cleanup_resources)
                exit_code = qt_app.exec()
                return exit_code
            else:
                # 保持主进程运行（如果没有UI）
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    info("接收到中断信号，正在关闭应用程序...")
                    self._cleanup_resources()
                    return 0
                
        except Exception as e:
            error(f"应用程序运行异常: {e}")
            handle_error(e)
            return 1


def main():
    """主函数入口"""
    app = MainApplication()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()