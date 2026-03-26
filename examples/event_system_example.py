"""
事件系统增强功能示例
演示事件拦截、修改和插件事件处理器的使用
"""

from core.event.event_bus import EventBus
from core.event.base_event import BaseEvent, EventMetadata
from core.event.event_handler import EventHandler
from core.event.event_interceptor import EventInterceptor
from core.decorators import plugin_event_handler
from typing import Optional


# 示例事件类
class UserLoginEvent(BaseEvent):
    """用户登录事件"""
    
    def __init__(self, username: str, ip_address: str):
        payload = {
            "username": username,
            "ip_address": ip_address,
            "login_time": None,
            "is_admin": False
        }
        super().__init__("user.login", payload)


# 示例事件处理器
class LoginEventHandler(EventHandler):
    """登录事件处理器"""
    
    def handle(self, event: BaseEvent) -> bool:
        if event.event_type == "user.login":
            print(f"处理登录事件: {event.payload['username']} from {event.payload['ip_address']}")
            
            # 修改事件载荷
            import time
            event.payload["login_time"] = time.time()
            event.payload["is_admin"] = event.payload["username"] == "admin"
            
            event.mark_handled()
            return True
        return False


# 示例事件拦截器
class SecurityInterceptor(EventInterceptor):
    """安全拦截器 - 检查并可能修改登录事件"""
    
    def intercept(self, event: BaseEvent) -> Optional[BaseEvent]:
        if event.event_type == "user.login":
            # 检查IP地址是否在黑名单中
            blacklisted_ips = ["192.168.1.100", "10.0.0.50"]
            if event.payload["ip_address"] in blacklisted_ips:
                print(f"阻止来自黑名单IP的登录: {event.payload['ip_address']}")
                return None  # 返回None取消事件
            
            # 记录安全日志
            print(f"安全检查通过: {event.payload['username']} from {event.payload['ip_address']}")
            
            # 可以修改事件载荷
            event.payload["security_checked"] = True
            
        return event


# 插件风格的事件处理器示例
class PluginStyleHandler:
    """使用装饰器的插件事件处理器"""
    
    @plugin_event_handler("user.login", "plugin_login_handler")
    def handle_user_login(self, event: BaseEvent) -> bool:
        print(f"插件处理器处理登录: {event.payload['username']}")
        
        # 插件也可以修改事件
        event.payload["processed_by_plugin"] = True
        
        return True


def main():
    """主函数 - 演示事件系统功能"""
    event_bus = EventBus()
    
    # 添加拦截器
    security_interceptor = SecurityInterceptor()
    event_bus.add_interceptor(security_interceptor)
    
    # 添加处理器
    login_handler = LoginEventHandler()
    event_bus.subscribe("user.login", login_handler)
    
    # 添加插件风格处理器
    plugin_handler = PluginStyleHandler()
    
    # 手动注册插件处理器（通常由插件管理器自动完成）
    if hasattr(plugin_handler.handle_user_login, '_is_plugin_event_handler'):
        from core.event.event_handler import LambdaEventHandler
        # 使用getattr安全访问动态属性，避免类型检查错误
        handler_name = getattr(plugin_handler.handle_user_login, '_handler_name', 'plugin_login_handler')
        handled_event_type = getattr(plugin_handler.handle_user_login, '_handled_event_type', 'user.login')
        
        lambda_handler = LambdaEventHandler(
            lambda event: plugin_handler.handle_user_login(event),
            handler_name
        )
        event_bus.subscribe(handled_event_type, lambda_handler)
    
    # 发布正常登录事件
    print("=== 正常登录事件 ===")
    normal_event = UserLoginEvent("john_doe", "192.168.1.50")
    event_bus.publish(normal_event)
    print(f"事件载荷: {normal_event.payload}")
    
    print("\n=== 黑名单IP登录事件 ===")
    blocked_event = UserLoginEvent("hacker", "192.168.1.100")
    result = event_bus.publish(blocked_event)
    print(f"事件被处理: {result}")
    
    print("\n=== 管理员登录事件 ===")
    admin_event = UserLoginEvent("admin", "10.0.0.1")
    event_bus.publish(admin_event)
    print(f"事件载荷: {admin_event.payload}")


if __name__ == "__main__":
    main()