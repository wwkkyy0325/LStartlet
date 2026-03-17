"""
UI工厂实现模块
基于DI容器的UI工厂具体实现
"""

import sys
from typing import Optional, Dict, Any, Callable, List

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
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
            
            # 创建示例UI内容
            self._create_example_ui_content(window)
            
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
    
    def _create_example_ui_content(self, window: FrostedGlassWindow):
        """创建示例UI内容"""
        try:
            # 创建左侧菜单栏内容
            self._create_left_menu_content(window)
            
            # 创建左侧挂载区内容（资源管理器）
            from ui.components.directory_viewer import DirectoryViewerComponent
            directory_viewer = DirectoryViewerComponent()
            directory_widget = directory_viewer.create_widget()
            window.mount_to_left_mount_area(directory_widget)
            
            # 创建中央上挂载区内容（搜索面板）
            self._create_central_top_content(window)
            
            # 创建中央下挂载区内容（图片查看器）
            from ui.components.image_viewer import ImageViewerComponent
            image_viewer = ImageViewerComponent()
            image_widget = image_viewer.create_widget()
            window.mount_to_central_bottom_mount_area(image_widget)
            
            # 创建右侧挂载区内容（属性面板）
            self._create_right_panel_content(window)
            
            # 建立组件间的信号连接
            self._setup_component_connections(window, directory_widget, image_widget)
            
            info("示例UI内容创建成功")
            
        except Exception as e:
            error(f"创建示例UI内容失败: {e}")
    
    def _create_central_top_content(self, window: FrostedGlassWindow):
        """创建中央上挂载区内容"""
        try:
            top_content = QWidget()
            top_layout = QVBoxLayout(top_content)
            top_layout.setContentsMargins(20, 20, 20, 20)
            top_layout.setSpacing(10)
            
            # 标题
            title_label = QLabel("🔍 搜索")
            title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
            top_layout.addWidget(title_label)
            
            # 搜索功能描述
            search_desc = QLabel("""
- 全局搜索
- 文件搜索  
- 符号搜索
- OCR文本搜索
            """)
            search_desc.setStyleSheet("color: white; font-size: 12px;")
            top_layout.addWidget(search_desc)
            
            top_layout.addStretch()
            
            # 挂载到中央上挂载区
            window.mount_to_central_top_mount_area(top_content)
            
        except Exception as e:
            error(f"创建中央上挂载区内容失败: {e}")
    
    def _setup_component_connections(self, window: FrostedGlassWindow, directory_widget, image_widget):
        """建立组件间的信号连接"""
        try:
            # 连接目录查看器的点击事件到图片查看器
            if hasattr(directory_widget, '_tree_widget'):
                directory_widget._tree_widget.itemClicked.connect(
                    lambda item, column: self._on_directory_item_clicked(item, image_widget)
                )
            
        except Exception as e:
            error(f"建立组件连接失败: {e}")
    
    def _on_directory_item_clicked(self, item, image_widget):
        """处理目录项点击事件"""
        try:
            from PySide6.QtCore import Qt
            from pathlib import Path
            
            # 获取点击的文件路径
            path_str = item.data(0, Qt.ItemDataRole.UserRole)
            if not path_str:
                return
                
            path = Path(path_str)
            
            # 检查是否是支持的文件类型（图片或PDF）
            if path.is_file():
                suffix = path.suffix.lower()
                if suffix in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.pdf'}:
                    # 显示点击的文件
                    image_widget.set_image(str(path))
                else:
                    # 如果不是支持的文件类型，清空图片查看器
                    if hasattr(image_widget, 'clear'):
                        image_widget.clear()
            else:
                # 如果是目录，清空图片查看器
                if hasattr(image_widget, 'clear'):
                    image_widget.clear()
                    
        except Exception as e:
            pass  # 静默处理错误
    
    def _create_left_menu_content(self, window: FrostedGlassWindow):
        """创建左侧菜单栏内容"""
        try:
            # 在左侧菜单栏区域添加菜单按钮
            left_menu_layout = QVBoxLayout(window._left_menu_area)
            left_menu_layout.setContentsMargins(0, 10, 0, 10)
            left_menu_layout.setSpacing(10)
            
            # 资源管理器按钮
            explorer_btn = QLabel("📁")
            explorer_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            explorer_btn.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: rgba(255, 255, 255, 20);
                }
                QLabel:hover {
                    background-color: rgba(255, 255, 255, 40);
                }
            """)
            left_menu_layout.addWidget(explorer_btn)
            
            # 搜索按钮
            search_btn = QLabel("🔍")
            search_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            search_btn.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: rgba(255, 255, 255, 20);
                }
                QLabel:hover {
                    background-color: rgba(255, 255, 255, 40);
                }
            """)
            left_menu_layout.addWidget(search_btn)
            
            # 扩展按钮
            extensions_btn = QLabel("🧩")
            extensions_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            extensions_btn.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: rgba(255, 255, 255, 20);
                }
                QLabel:hover {
                    background-color: rgba(255, 255, 255, 40);
                }
            """)
            left_menu_layout.addWidget(extensions_btn)
            
            left_menu_layout.addStretch()
            
        except Exception as e:
            error(f"创建左侧菜单内容失败: {e}")
    
    def _create_right_panel_content(self, window: FrostedGlassWindow):
        """创建右侧面板内容"""
        try:
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(10, 10, 10, 10)
            right_layout.setSpacing(10)
            
            # 标题
            title_label = QLabel("属性面板")
            title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
            right_layout.addWidget(title_label)
            
            # 属性列表
            properties_text = QLabel("""
文件信息:
- 类型: 图片
- 尺寸: 1920x1080
- 大小: 2.3 MB
- 修改时间: 2026-03-17

OCR结果:
- 置信度: 95%
- 识别文字: 128字
- 语言: 中文
            """)
            properties_text.setStyleSheet("color: white; font-size: 12px;")
            right_layout.addWidget(properties_text)
            
            right_layout.addStretch()
            
            # 挂载到右侧区域
            window.mount_to_right_mount_area(right_panel)
            
        except Exception as e:
            error(f"创建右侧面板内容失败: {e}")
    
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