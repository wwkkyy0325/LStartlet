"""
插件基类
定义所有插件必须实现的标准接口和生命周期方法
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, ClassVar
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
        _plugin_metadata (ClassVar[Optional[Dict[str, Any]]]): 装饰器设置的元数据
        
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
    """
    
    # 类级别属性声明，用于装饰器设置
    _plugin_metadata: ClassVar[Optional[Dict[str, Any]]] = None

    def __init__(
        self,
        plugin_id: str,
        name: str,
        version: str,
        description: str = "",
    ) -> None:
        """
        初始化插件基类
        
        Args:
            plugin_id (str): 插件唯一标识符
            name (str): 插件显示名称  
            version (str): 插件版本号
            description (str): 插件描述，默认为空字符串
            
        Example:
            >>> plugin = PluginBase("com.example.test", "Test Plugin", "1.0.0")
        """
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self._container: Optional[ServiceContainer] = None
        self._is_initialized = False
        self._is_started = False

    @property
    def container(self) -> ServiceContainer:
        """
        获取依赖注入容器
        
        Returns:
            ServiceContainer: 依赖注入容器实例
            
        Raises:
            RuntimeError: 如果容器未设置
            
        Example:
            >>> plugin = MyPlugin()
            >>> # container must be set before accessing
            >>> plugin.container.get(MyService)
        """
        if self._container is None:
            raise RuntimeError(f"Plugin {self.name} container not set")
        return self._container

    @container.setter
    def container(self, container: ServiceContainer) -> None:
        """
        设置依赖注入容器
        
        Args:
            container (ServiceContainer): 依赖注入容器实例
            
        Example:
            >>> plugin = MyPlugin()
            >>> plugin.container = my_container
        """
        self._container = container

    @abstractmethod
    def initialize(self) -> bool:
        """
        插件初始化
        
        在依赖注入完成后调用，用于执行插件的初始化逻辑。
        此方法应在子类中实现。
        
        Returns:
            bool: 初始化是否成功
            
        Example:
            >>> class MyPlugin(PluginBase):
            ...     def initialize(self) -> bool:
            ...         # 初始化逻辑
            ...         return True
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """
        插件启动
        
        在应用完全启动后调用，用于启动插件的主要功能。
        此方法应在子类中实现。
        
        Example:
            >>> class MyPlugin(PluginBase):
            ...     def start(self) -> None:
            ...         # 启动逻辑
            ...         pass
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        插件停止
        
        在应用关闭前调用，用于停止插件的功能并释放资源。
        此方法应在子类中实现。
        
        Example:
            >>> class MyPlugin(PluginBase):
            ...     def stop(self) -> None:
            ...         # 停止逻辑
            ...         pass
        """
        pass

    def cleanup(self) -> None:
        """
        插件清理
        
        在插件生命周期结束时调用，用于执行最终的清理工作。
        默认实现为空，子类可选择性重写。
        
        Example:
            >>> class MyPlugin(PluginBase):
            ...     def cleanup(self) -> None:
            ...         # 清理逻辑
            ...         pass
        """
        pass

    def __str__(self) -> str:
        """
        返回插件的字符串表示
        
        Returns:
            str: 插件的字符串表示
            
        Example:
            >>> plugin = MyPlugin()
            >>> assert str(plugin) == "Plugin(com.example.myplugin)"
        """
        return f"Plugin({self.plugin_id})"

    def __repr__(self) -> str:
        """
        返回插件的详细字符串表示
        
        Returns:
            str: 插件的详细字符串表示
            
        Example:
            >>> plugin = MyPlugin()
            >>> assert "Plugin(id='com.example.myplugin', name='My Plugin')" in repr(plugin)
        """
        return f"Plugin(id='{self.plugin_id}', name='{self.name}')"
