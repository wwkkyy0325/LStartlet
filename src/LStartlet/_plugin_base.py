from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Any, Optional


class PluginBase(ABC):
    """插件基类 - 所有插件必须继承此类"""

    # 插件元数据
    name: ClassVar[str] = "unnamed_plugin"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = ""
    author: ClassVar[str] = ""
    dependencies: ClassVar[list] = []

    def __init__(self):
        self._is_initialized = False
        self._is_active = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化插件
        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行插件主要功能
        Args:
            **kwargs: 执行参数
        Returns:
            Any: 执行结果
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理插件资源"""
        pass

    def activate(self) -> bool:
        """激活插件"""
        if not self._is_initialized:
            if not self.initialize():
                return False
            self._is_initialized = True

        self._is_active = True
        return True

    def deactivate(self) -> None:
        """停用插件"""
        self._is_active = False
        self.cleanup()

    @property
    def is_active(self) -> bool:
        """插件是否处于激活状态"""
        return self._is_active
