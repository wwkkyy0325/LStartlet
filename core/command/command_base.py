from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from core.logger import error


@dataclass
class CommandMetadata:
    """命令元数据"""

    name: str
    description: str = ""
    category: str = "general"
    version: str = "1.0.0"
    author: str = ""
    parameters: Dict[str, Any] = field(default_factory=lambda: {})
    requires_confirmation: bool = False
    timeout: float = 30.0  # 默认30秒超时


class CommandResult:
    """命令执行结果"""

    def __init__(
        self,
        is_success: bool,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ):
        self.is_success = is_success
        self.message = message
        self.data = data
        self.error = error

    @classmethod
    def success(
        cls,
        message: str = "Command executed successfully",
        data: Optional[Dict[str, Any]] = None,
    ) -> "CommandResult":
        return cls(is_success=True, message=message, data=data)

    @classmethod
    def failure(
        cls, message: str, error: Optional[Exception] = None
    ) -> "CommandResult":
        return cls(is_success=False, message=message, error=error)


class BaseCommand(ABC):
    """命令基类"""

    def __init__(self, metadata: CommandMetadata):
        self.metadata = metadata
        self._is_executing = False

    @property
    def name(self) -> str:
        """获取命令名称"""
        return self.metadata.name

    @property
    def is_executing(self) -> bool:
        """检查命令是否正在执行"""
        return self._is_executing

    def set_executing(self, executing: bool) -> None:
        """设置命令执行状态"""
        self._is_executing = executing

    @abstractmethod
    def execute(self, **kwargs: Any) -> CommandResult:
        """
        执行命令

        Args:
            **kwargs: 命令参数 (Dict[str, Any])

        Returns:
            CommandResult: 命令执行结果
        """
        pass

    def validate_parameters(self, **kwargs: Any) -> bool:
        """
        验证命令参数

        Args:
            **kwargs: 命令参数 (Dict[str, Any])

        Returns:
            bool: 参数是否有效
        """
        # 基础参数验证逻辑
        required_params = self.metadata.parameters.get("required", [])
        for param in required_params:
            if param not in kwargs:
                error(f"Missing required parameter: {param} for command {self.name}")
                return False
        return True

    def __str__(self) -> str:
        return f"Command({self.name})"

    def __repr__(self) -> str:
        return f"Command(name='{self.name}', category='{self.metadata.category}')"
