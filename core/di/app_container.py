from typing import Optional
from .service_container import ServiceContainer
from .container_config import configure_default_container
from .service_registry import register_application_services


# 创建全局应用容器实例
app_container: Optional[ServiceContainer] = None


def get_app_container() -> ServiceContainer:
    """获取应用程序容器实例"""
    global app_container
    if app_container is None:
        app_container = configure_default_container(register_application_services)
    return app_container


def reset_app_container() -> None:
    """重置应用程序容器（用于测试）"""
    global app_container
    app_container = None
