"""
插件基类
定义所有插件必须实现的标准接口和生命周期方法
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from LStartlet.core.di import ServiceContainer
from LStartlet.core.logger import info, error


class PluginBase(ABC):
    """
    插件基类 - 所有插件必须继承此类

    插件生命周期：
    1. __init__(): 插件实例化
    2. initialize(): 插件初始化（依赖注入完成后调用）
    3. start(): 插件启动（应用完全启动后调用）
    4. stop(): 插件停止（应用关闭前调用）
    5. cleanup(): 插件清理（最后调用）
    
    Attributes:
        plugin_id (str): 插件唯一标识符
        name (str): 插件显示名称
        version (str): 插件版本号
        description (str): 插件描述
        _container (Optional[ServiceContainer]): 依赖注入容器
        _is_initialized (bool): 插件是否已初始化
        _is_started (bool): 插件是否已启动
        
    Example:
        >>> class MyPlugin(PluginBase):
        ...     def __init__(self):
        ...         super().__init__(
        ...             "com.example.myplugin",
        ...             "My Plugin",
        ...             "1.0.0",
        ...             "A sample plugin"
        ...         )
        ...
        ...     def initialize(self) -> None:
        ...         # 初始化逻辑
        ...         pass
        ...
        ...     def start(self) -> None:
        ...         # 启动逻辑
        ...         pass
        ...
        ...     def stop(self) -> None:
        ...         # 停止逻辑
        ...         pass
        ...
        ...     def cleanup(self) -> None:
        ...         # 清理逻辑
        ...         pass
    """

    PLUGIN_DEPENDENCIES: Dict[str, str] = {}
    """插件依赖信息
    
    子类可以重写此属性来声明依赖的其他插件。
    格式为 {plugin_id: version_requirement}，例如 {"core.logger": ">=1.0.0"}。
    
    Example:
        >>> class MyPlugin(PluginBase):
        ...     PLUGIN_DEPENDENCIES = {"core.logger": ">=1.0.0", "core.config": ">=2.0.0"}
    """

    def __init__(self, plugin_id: str, name: str, version: str, description: str = "") -> None:
        """
        初始化插件基本信息

        Args:
            plugin_id (str): 插件唯一标识符（建议使用反向域名格式，如 com.example.myplugin）
            name (str): 插件显示名称
            version (str): 插件版本号（语义化版本格式）
            description (str): 插件描述，默认为空字符串
            
        Example:
            >>> plugin = PluginBase("com.test.plugin", "Test Plugin", "1.0.0", "Test description")
        """
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self._container: Optional[ServiceContainer] = None
        self._is_initialized = False
        self._is_started = False

    def get_dependencies(self) -> Dict[str, str]:
        """
        获取插件依赖信息
        
        返回插件所依赖的其他插件列表及其版本要求。
        
        Returns:
            Dict[str, str]: 依赖插件字典，格式为 {plugin_id: version_requirement}
            
        Example:
            >>> plugin = PluginBase("test", "Test", "1.0.0")
            >>> deps = plugin.get_dependencies()
            >>> assert deps == {}
        """
        return self.PLUGIN_DEPENDENCIES

    def get_provided_services(self) -> Dict[str, Any]:
        """
        获取插件提供的服务
        
        返回插件向依赖注入容器注册的服务列表。
        子类应该重写此方法来提供具体的服务。
        
        Returns:
            Dict[str, Any]: 提供的服务字典，格式为 {service_name: service_instance_or_factory}
            
        Example:
            >>> plugin = PluginBase("test", "Test", "1.0.0")
            >>> services = plugin.get_provided_services()
            >>> assert services == {}
        """
        return {}

    @property
    def container(self) -> ServiceContainer:
        """
        Get dependency injection container
        
        Returns:
            ServiceContainer: 依赖注入容器实例
            
        Raises:
            RuntimeError: 如果容器未设置
            
        Example:
            >>> plugin = PluginBase("test", "Test", "1.0.0")
            >>> # plugin.container  # 这会抛出 RuntimeError
            >>> # 需要先设置 container 属性
        """
        if self._container is None:
            raise RuntimeError(f"Plugin {self.plugin_id} container not set")
        return self._container

    @container.setter
    def container(self, container: ServiceContainer) -> None:
        """
        Set dependency injection container
        
        Args:
            container (ServiceContainer): 依赖注入容器实例
            
        Example:
            >>> from LStartlet.core.di import ServiceContainer
            >>> plugin = PluginBase("test", "Test", "1.0.0")
            >>> container = ServiceContainer()
            >>> plugin.container = container
        """
        self._container = container

    @abstractmethod
    def initialize(self) -> bool:
        """
        插件初始化方法
        
        在依赖注入完成后调用，用于执行插件的初始化逻辑。
        子类必须实现此方法。
        
        Returns:
            bool: 初始化成功返回 True，失败返回 False
            
        Example:
            >>> class MyPlugin(PluginBase):
            ...     def initialize(self) -> bool:
            ...         # 注册服务、配置等
            ...         self.container.register_instance("my_service", MyService())
            ...         return True
        """
        pass

    @abstractmethod
    def start(self) -> bool:
        """
        插件启动方法
        
        在应用程序完全启动后调用，用于启动插件的主要功能。
        子类必须实现此方法。
        
        Returns:
            bool: 启动成功返回 True，失败返回 False
            
        Example:
            >>> class MyPlugin(PluginBase):
            ...     def start(self) -> bool:
            ...         # 启动后台任务、监听事件等
            ...         print("Plugin started")
            ...         self._is_started = True
            ...         return True
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        插件停止方法
        
        在应用程序关闭前调用，用于优雅地停止插件功能。
        子类必须实现此方法。
        
        Returns:
            bool: 停止成功返回 True，失败返回 False
            
        Example:
            >>> class MyPlugin(PluginBase):
            ...     def stop(self) -> bool:
            ...         # 停止后台任务、保存状态等
            ...         print("Plugin stopped")
            ...         self._is_started = False
            ...         return True
        """
        pass

    @abstractmethod
    def cleanup(self) -> bool:
        """
        插件清理方法
        
        在插件卸载时最后调用，用于释放资源和清理状态。
        子类必须实现此方法。
        
        Returns:
            bool: 清理成功返回 True，失败返回 False
            
        Example:
            >>> class MyPlugin(PluginBase):
            ...     def cleanup(self) -> bool:
            ...         # 释放文件句柄、网络连接等
            ...         print("Plugin cleaned up")
            ...         return True
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        获取插件信息
        
        Returns:
            Dict[str, Any]: 包含插件基本信息的字典
            
        Example:
            >>> plugin = PluginBase("test.id", "Test Plugin", "1.0.0", "Description")
            >>> info = plugin.get_info()
            >>> assert info["name"] == "Test Plugin"
            >>> assert info["version"] == "1.0.0"
        """
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "initialized": self._is_initialized,
            "started": self._is_started,
        }

    def __str__(self) -> str:
        """
        返回插件的字符串表示
        
        Returns:
            str: 插件的字符串表示
            
        Example:
            >>> plugin = PluginBase("test", "Test Plugin", "1.0.0")
            >>> assert str(plugin) == "Plugin(Test Plugin v1.0.0)"
        """
        return f"Plugin({self.name} v{self.version})"

    def __repr__(self) -> str:
        """
        返回插件的详细字符串表示
        
        Returns:
            str: 插件的详细字符串表示
            
        Example:
            >>> plugin = PluginBase("test.id", "Test", "1.0.0")
            >>> repr_str = repr(plugin)
            >>> assert "PluginBase" in repr_str
        """
        return f"PluginBase(plugin_id='{self.plugin_id}', name='{self.name}', version='{self.version}')"

    @property
    def is_started(self) -> bool:
        """
        检查插件是否已启动
        
        Returns:
            bool: 如果插件已启动返回 True，否则返回 False
            
        Example:
            >>> plugin = PluginBase("test", "Test", "1.0.0")
            >>> assert not plugin.is_started
        """
        return self._is_started
