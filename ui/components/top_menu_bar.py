"""
顶部菜单栏组件
挂在标题栏下方，根据字体大小自适应高度
支持配置驱动的完整菜单系统
"""

from typing import Optional, List, Dict, Any, Callable
from PySide6.QtWidgets import QWidget, QHBoxLayout, QMenu, QMenuBar, QScrollArea, QApplication
from PySide6.QtGui import QAction, QMouseEvent
from PySide6.QtCore import Qt
from core.event.event_bus import EventBus


class TopMenuBar(QWidget):
    """顶部菜单栏组件 - 完整的菜单系统实现"""
    
    def __init__(self, parent: Optional[QWidget] = None, event_bus: Optional[EventBus] = None, on_menu_item_clicked: Optional[Callable[[str, str, Dict[str, Any]], None]] = None):
        super().__init__(parent)
        self._event_bus = event_bus
        self._on_menu_item_clicked = on_menu_item_clicked
        self._menus: Dict[str, QMenu] = {}  # 菜单映射 {menu_id: QMenu}
        self._menu_items: Dict[str, Dict[str, QAction]] = {}  # 菜单项映射 {menu_id: {item_id: QAction}}
        
        # 创建QMenuBar（使用QScrollArea包装以防止推动UI）
        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("menuBarScroll")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet("""
            QScrollArea#menuBarScroll {
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QScrollArea#menuBarScroll > QWidget {
                background-color: transparent;
            }
            /* 确保滚动条样式透明 */
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 80);
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 120);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                width: 0px;
                height: 0px;
            }
        """)
        
        self._menu_bar = QMenuBar()
        self._menu_bar.setObjectName("topMenuBar")
        self._menu_bar.setStyleSheet("""
            QMenuBar#topMenuBar {
                background-color: rgba(255, 255, 255, 15);
                border-bottom: 1px solid rgba(255, 255, 255, 30);
                color: white;
                font-size: 14px;
                padding: 0px;  /* 完全移除内边距 */
                margin: 0px;
                height: 28px;  /* 固定高度 */
            }
            
            QMenuBar#topMenuBar::item {
                background: transparent;
                padding: 2px 12px;  /* 进一步减少上下内边距 */
                min-width: 60px;  /* 减少最小宽度 */
                margin: 0px;
                height: 24px;  /* 菜单项高度 */
            }
            
            QMenuBar#topMenuBar::item:selected {
                background: rgba(255, 255, 255, 30);
                border-radius: 3px;
            }
            
            QMenuBar#topMenuBar::item:pressed {
                background: rgba(255, 255, 255, 50);
                border-radius: 3px;
            }
        """)
        
        # 设置菜单栏属性 - 菜单栏需要接收点击事件，不能透明给鼠标事件
        self._menu_bar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._scroll_area.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)  # 滚动区域也需要接收事件
        
        self._scroll_area.setWidget(self._menu_bar)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._scroll_area)
        
        # 设置尺寸策略
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)  # 菜单栏本身需要接收事件

    def configure_menu(self, menu_config: Dict[str, Any]) -> None:
        """
        配置菜单
        
        Args:
            menu_config: 菜单配置字典
                {
                    "file": {
                        "title": "文件",
                        "items": [
                            {"id": "new", "text": "新建", "shortcut": "Ctrl+N", "enabled": True},
                            {"id": "separator", "type": "separator"},
                            {"id": "exit", "text": "退出", "shortcut": "Ctrl+Q", "enabled": True}
                        ]
                    }
                }
        """
        # 清除现有菜单
        self._menus.clear()
        self._menu_items.clear()
        self._menu_bar.clear()
        
        for menu_id, menu_data in menu_config.items():
            menu_title = menu_data.get("title", menu_id)
            menu_items = menu_data.get("items", [])
            
            # 创建菜单
            menu = QMenu(menu_title)
            self._menus[menu_id] = menu
            self._menu_items[menu_id] = {}
            
            # 添加菜单项
            for item_data in menu_items:
                if item_data.get("type") == "separator":
                    menu.addSeparator()
                    continue
                
                item_id = item_data["id"]
                text = item_data["text"]
                shortcut = item_data.get("shortcut", "")
                enabled = item_data.get("enabled", True)
                
                # 创建动作
                action = QAction(text, self)
                if shortcut:
                    action.setShortcut(shortcut)
                action.setEnabled(enabled)
                
                # 连接信号
                action.triggered.connect(
                    lambda checked=False, m_id=menu_id, i_id=item_id, data=item_data: 
                    self._on_menu_item_triggered(m_id, i_id, data)
                )
                
                menu.addAction(action)
                self._menu_items[menu_id][item_id] = action
            
            # 将菜单添加到菜单栏
            self._menu_bar.addMenu(menu)
    
    def _on_menu_item_triggered(self, menu_id: str, item_id: str, item_data: Dict[str, Any]) -> None:
        """处理菜单项触发"""
        # 调用回调函数
        if self._on_menu_item_clicked:
            self._on_menu_item_clicked(menu_id, item_id, item_data)