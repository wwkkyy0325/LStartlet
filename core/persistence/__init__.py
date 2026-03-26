"""
持久化系统初始化模块
"""

from core.persistence.persistence_manager import PersistenceManager
from core.di import ServiceContainer
from core.di.service_descriptor import ServiceLifetime

__all__ = [
    'initialize_persistence_system',
    'PersistenceManager'
]


def initialize_persistence_system(container: ServiceContainer, data_dir: str = "data") -> PersistenceManager:
    """
    初始化持久化系统
    
    Args:
        container: 依赖注入容器
        data_dir: 数据目录路径
        
    Returns:
        持久化管理器实例
    """
    from core.logger import info
    
    info("正在初始化持久化系统...")
    
    # 创建持久化管理器
    persistence_manager = PersistenceManager(data_dir)
    if not persistence_manager.initialize():
        raise RuntimeError("持久化系统初始化失败")
    
    # 注册到依赖注入容器
    container.register(PersistenceManager, instance=persistence_manager, lifetime=ServiceLifetime.SINGLETON)
    
    info("持久化系统初始化完成")
    return persistence_manager
