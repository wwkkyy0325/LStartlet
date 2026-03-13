"""
OCR项目主入口文件
负责初始化配置、注册核心工具、启动主进程和渲染进程
"""

import os
import sys
import time
from typing import cast

# 核心模块导入
from core.config.config_manager import ConfigManager
from core.logger import configure_logger, info, error, set_process_type
from core.logger.level import LogLevel  # 添加LogLevel导入
from core.error import handle_error
from core.path import get_project_root, join_paths
from core.event.event_bus import EventBus
from core.event.events.ui_events import RenderProcessReadyEvent
from core.event.events.scheduler_events import ApplicationLifecycleEvent, ProcessStartedEvent

# UI模块导入
from ui import UIFactory
from ui.core.standard_window_manager import StandardWindowManager  # type: ignore


# =============== 日志级别配置 ===============
# 可选值: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
# 修改此处即可改变日志输出级别
LOG_LEVEL = "DEBUG"
# =========================================


class MainApplication:
    """主应用程序类"""
    
    def __init__(self):
        self.config_manager = None
        self.event_bus = None
        self.render_process_ready = False
        self.custom_ui_callback = None
        self.render_process_thread = None
        self.qt_app = None
        
    def initialize(self) -> bool:
        """初始化应用程序"""
        try:
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
            
            # 1. 检查并初始化配置文件
            if not self._initialize_config():
                error("配置初始化失败")
                return False
            
            # 2. 初始化事件总线
            self.event_bus = EventBus()
            
            # 3. 注册核心工具和组件
            if not self._register_core_components():
                error("核心组件注册失败")
                return False
            
            # 4. 初始化UI工厂（在核心组件注册完成后）
            self.ui_factory = UIFactory(self.event_bus)
            self.ui_factory.register_event_listeners()
            
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
                self.config_manager = ConfigManager(config_file)
                # 保存默认配置到文件
                self.config_manager.save_to_file(config_file)
                info(f"默认配置文件已创建: {config_file}")
            else:
                info(f"加载现有配置文件: {config_file}")
                self.config_manager = ConfigManager(config_file)
            
            return True
            
        except Exception as e:
            error(f"配置初始化失败: {e}")
            handle_error(e)
            return False
    
    def _register_core_components(self) -> bool:
        """注册核心组件"""
        try:
            # 注册事件监听器
            self._register_event_listeners()
            
            # 发布应用程序启动事件
            app_start_event = ApplicationLifecycleEvent("starting")
            assert self.event_bus is not None
            self.event_bus.publish(app_start_event)
            
            # 主进程已经在GlobalProcessManager初始化时自动注册
            main_pid = os.getpid()
            info(f"主进程PID: {main_pid}")
            
            # 发布主进程启动事件
            main_process_event = ProcessStartedEvent(
                process_id=main_pid, 
                process_data={"process_type": "main", "pid": main_pid}
            )
            self.event_bus.publish(main_process_event)
            
            # 发布应用程序已启动事件
            app_started_event = ApplicationLifecycleEvent("started")
            self.event_bus.publish(app_started_event)
            
            info("核心组件注册完成")
            return True
            
        except Exception as e:
            error(f"核心组件注册失败: {e}")
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
            return self.ui_factory.start_render_process(timeout)
            
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
            
        except Exception as e:
            error(f"磨砂玻璃 UI 创建失败，程序退出：{e}")
            handle_error(e)
            raise  # 重新抛出异常，让程序退出
    
    def _cleanup_resources(self) -> None:
        """清理资源"""
        try:
            info("开始清理应用程序资源...")
            
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