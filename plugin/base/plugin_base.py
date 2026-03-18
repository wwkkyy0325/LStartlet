"""
插件基类
定义所有插件必须实现的标准接口和生命周期方法
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.di import ServiceContainer
from core.logger import info, error


class PluginBase(ABC):
    """
    插件基类 - 所有插件必须继承此类
    
    插件生命周期：
    1. __init__(): 插件实例化
    2. initialize(): 插件初始化（依赖注入完成后调用）
    3. start(): 插件启动（应用完全启动后调用）
    4. stop(): 插件停止（应用关闭前调用）
    5. cleanup(): 插件清理（最后调用）
    """
    
    def __init__(self, plugin_id: str, name: str, version: str, description: str = ""):
        """
        初始化插件基本信息
        
        Args:
            plugin_id: 插件唯一标识符（建议使用反向域名格式，如 com.example.myplugin）
            name: 插件显示名称
            version: 插件版本号（语义化版本格式）
            description: 插件描述
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
        """Get dependency injection container"""
        if self._container is None:
            raise RuntimeError(f"Plugin {self.plugin_id} container not set")
        return self._container
    
    @container.setter
    def container(self, container: ServiceContainer) -> None:
        """Set dependency injection container"""
        if self._is_initialized:
            raise RuntimeError(f"插件 {self.plugin_id} 已经初始化，不能重新设置容器")
        self._container = container
    
    @property
    def is_started(self) -> bool:
        """检查插件是否已启动"""
        return self._is_started
    
    @abstractmethod
    def get_dependencies(self) -> Dict[str, str]:
        """
        获取插件依赖信息
        
        Returns:
            依赖字典，格式: {"dependency_name": "version_requirement"}
            例如: {"core": ">=1.0.0", "ui": ">=1.0.0"}
            
        Note:
            推荐使用类属性 PLUGIN_DEPENDENCIES 进行静态依赖声明，
            这样可以在不实例化插件的情况下解析依赖。
        """
        pass
    
    @abstractmethod
    def get_provided_services(self) -> Dict[str, Any]:
        """
        获取插件提供的服务
        
        Returns:
            服务字典，格式: {"service_name": service_class_or_instance}
        """
        pass
    
    def initialize(self) -> bool:
        """
        插件初始化 - 在依赖注入完成后调用
        
        Returns:
            初始化是否成功
        """
        try:
            if self._is_initialized:
                info(f"插件 {self.plugin_id} 已经初始化，跳过重复初始化")
                return True
                
            info(f"开始初始化插件: {self.name} ({self.plugin_id} v{self.version})")
            
            # 验证容器是否已设置
            if self._container is None:
                error(f"插件 {self.plugin_id} 的容器未设置，无法初始化")
                return False
            
            # 调用具体的初始化逻辑
            success = self._on_initialize()
            if success:
                self._is_initialized = True
                info(f"插件 {self.name} 初始化成功")
            else:
                error(f"插件 {self.name} 初始化失败")
                
            return success
            
        except Exception as e:
            error(f"插件 {self.name} 初始化异常: {e}")
            return False
    
    def start(self) -> bool:
        """
        插件启动 - 在应用完全启动后调用
        
        Returns:
            启动是否成功
        """
        try:
            if not self._is_initialized:
                error(f"插件 {self.name} 未初始化，无法启动")
                return False
                
            if self._is_started:
                info(f"插件 {self.name} 已经启动，跳过重复启动")
                return True
                
            info(f"开始启动插件: {self.name}")
            success = self._on_start()
            if success:
                self._is_started = True
                info(f"插件 {self.name} 启动成功")
            else:
                error(f"插件 {self.name} 启动失败")
                
            return success
            
        except Exception as e:
            error(f"插件 {self.name} 启动异常: {e}")
            return False
    
    def stop(self) -> bool:
        """
        插件停止 - 在应用关闭前调用
        
        Returns:
            停止是否成功
        """
        try:
            if not self._is_started:
                info(f"插件 {self.name} 未启动或已停止，跳过停止操作")
                return True
                
            info(f"开始停止插件: {self.name}")
            success = self._on_stop()
            if success:
                self._is_started = False
                info(f"插件 {self.name} 停止成功")
            else:
                error(f"插件 {self.name} 停止失败")
                
            return success
            
        except Exception as e:
            error(f"插件 {self.name} 停止异常: {e}")
            return False
    
    def cleanup(self) -> bool:
        """
        插件清理 - 最后调用，释放所有资源
        
        Returns:
            清理是否成功
        """
        try:
            if self._is_started:
                # 如果插件还在运行，先停止它
                self.stop()
                
            if not self._is_initialized:
                info(f"插件 {self.name} 未初始化，跳过清理操作")
                return True
                
            info(f"开始清理插件: {self.name}")
            success = self._on_cleanup()
            if success:
                self._is_initialized = False
                self._container = None
                info(f"插件 {self.name} 清理成功")
            else:
                error(f"插件 {self.name} 清理失败")
                
            return success
            
        except Exception as e:
            error(f"插件 {self.name} 清理异常: {e}")
            return False
    
    @abstractmethod
    def _on_initialize(self) -> bool:
        """具体的初始化逻辑，子类必须实现"""
        pass
    
    @abstractmethod
    def _on_start(self) -> bool:
        """具体的启动逻辑，子类必须实现"""
        pass
    
    @abstractmethod
    def _on_stop(self) -> bool:
        """具体的停止逻辑，子类必须实现"""
        pass
    
    @abstractmethod
    def _on_cleanup(self) -> bool:
        """具体的清理逻辑，子类必须实现"""
        pass