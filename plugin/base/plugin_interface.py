"""
插件接口定义
提供插件系统的核心接口和类型定义
"""

from typing import Protocol, Dict, Any, List, Optional


class IPlugin(Protocol):
    """插件接口协议"""
    
    @property
    def plugin_id(self) -> str:
        """插件唯一标识符"""
        ...
    
    @property
    def name(self) -> str:
        """插件显示名称"""
        ...
    
    @property
    def version(self) -> str:
        """插件版本号"""
        ...
    
    @property
    def description(self) -> str:
        """插件描述"""
        ...
    
    def get_dependencies(self) -> Dict[str, str]:
        """获取插件依赖信息"""
        ...
    
    def get_provided_services(self) -> Dict[str, Any]:
        """获取插件提供的服务"""
        ...
    
    def initialize(self) -> bool:
        """插件初始化"""
        ...
    
    def start(self) -> bool:
        """插件启动"""
        ...
    
    def stop(self) -> bool:
        """插件停止"""
        ...
    
    def cleanup(self) -> bool:
        """插件清理"""
        ...


class IPluginManager(Protocol):
    """插件管理器接口协议"""
    
    def load_plugins(self, plugin_paths: List[str]) -> None:
        """加载插件"""
        ...
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        ...
    
    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """获取指定插件"""
        ...
    
    def get_all_plugins(self) -> List[IPlugin]:
        """获取所有插件"""
        ...
    
    def is_plugin_loaded(self, plugin_id: str) -> bool:
        """检查插件是否已加载"""
        ...
    
    def initialize_all_plugins(self) -> bool:
        """初始化所有插件"""
        ...
    
    def start_all_plugins(self) -> bool:
        """启动所有插件"""
        ...
    
    def stop_all_plugins(self) -> bool:
        """停止所有插件"""
        ...
    
    def cleanup_all_plugins(self) -> bool:
        """清理所有插件"""
        ...