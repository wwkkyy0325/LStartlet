"""
最终UI推动问题修复验证脚本
验证菜单栏和内容区域都不会推动UI
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import Qt
from ui.components.frosted_glass_window import FrostedGlassWindow


def test_final_ui_fix():
    """最终UI推动问题修复验证"""
    app = QApplication(sys.argv)
    
    # 创建磨砂玻璃窗口
    window = FrostedGlassWindow()
    
    # 创建顶部菜单栏（使用配置驱动方式）
    menu_bar = window.create_top_menu_bar()
    
    # 配置复杂的菜单结构
    menu_config = {
        "file": {
            "title": "文件",
            "items": [
                {"id": "new", "text": "新建", "shortcut": "Ctrl+N", "enabled": True},
                {"id": "open", "text": "打开", "shortcut": "Ctrl+O", "enabled": True},
                {"id": "separator1", "type": "separator"},
                {"id": "save", "text": "保存", "shortcut": "Ctrl+S", "enabled": True},
                {"id": "save_as", "text": "另存为", "shortcut": "Ctrl+Shift+S", "enabled": True},
                {"id": "separator2", "type": "separator"},
                {"id": "exit", "text": "退出", "shortcut": "Ctrl+Q", "enabled": True}
            ]
        },
        "edit": {
            "title": "编辑",
            "items": [
                {"id": "undo", "text": "撤销", "shortcut": "Ctrl+Z", "enabled": True},
                {"id": "redo", "text": "重做", "shortcut": "Ctrl+Y", "enabled": True},
                {"id": "separator3", "type": "separator"},
                {"id": "cut", "text": "剪切", "shortcut": "Ctrl+X", "enabled": True},
                {"id": "copy", "text": "复制", "shortcut": "Ctrl+C", "enabled": True},
                {"id": "paste", "text": "粘贴", "shortcut": "Ctrl+V", "enabled": True}
            ]
        },
        "view": {
            "title": "视图",
            "items": [
                {"id": "zoom_in", "text": "放大", "shortcut": "Ctrl++", "enabled": True},
                {"id": "zoom_out", "text": "缩小", "shortcut": "Ctrl+-", "enabled": True},
                {"id": "reset_zoom", "text": "重置缩放", "shortcut": "Ctrl+0", "enabled": True}
            ]
        },
        "help": {
            "title": "帮助",
            "items": [
                {"id": "documentation", "text": "文档", "shortcut": "", "enabled": True},
                {"id": "about", "text": "关于", "shortcut": "", "enabled": True}
            ]
        }
    }
    
    menu_bar.configure_menu(menu_config)
    
    # 创建非常宽的内容来测试 - 这个宽度会超出小窗口，但不应该推动UI
    test_content = QLabel("这是一个非常宽的内容区域，用于测试当内容宽度超过窗口时的行为。在修复前，这种宽内容会强制推动整个UI向右移动，导致布局混乱。现在使用QScrollArea后，内容应该可以正常滚动，而不会影响窗口的整体尺寸和位置。")
    test_content.setStyleSheet("""
        font-size: 16px; 
        color: #333; 
        background-color: rgba(255, 255, 255, 200); 
        padding: 20px;
        min-width: 1200px;  /* 故意设置很宽 */
        min-height: 300px;
    """)
    test_content.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    test_content.setWordWrap(True)
    test_content.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    
    # 挂载到窗口的挂载区域
    if window._mount_area.mount_component(test_content):
        print("✅ 主内容挂载成功")
    else:
        print("❌ 主内容挂载失败")
    
    # 显示窗口 - 初始尺寸较小，应该能看到滚动条而不是UI被推动
    window.show()
    window.resize(600, 400)
    
    print("最终UI修复测试窗口已显示，请检查：")
    print("1. 窗口边框是否有适当的边距保护（左、下、右各10px）")
    print("2. 菜单栏是否在标题栏下方正确显示（完整的文件、编辑、视图、帮助菜单）")
    print("3. 菜单栏是否出现水平滚动条（如果窗口太小）")
    print("4. 内容区域是否出现水平滚动条（因为内容很宽）")
    print("5. 缩小窗口时，UI是否向右移动（绝对不应该移动！）")
    print("6. 光点是否正常跟随鼠标移动")
    print("7. 窗口边缘是否可以正常调整大小")
    print("8. 菜单栏和内容区域的滚动条是否都正常工作")
    print("9. 菜单项点击是否正常工作（会打印日志）")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    test_final_ui_fix()