from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, ClassVar, Callable
from dataclasses import dataclass, field
from LStartlet.core.logger import error


@dataclass
class CommandParameter:
    """
    命令参数定义
    
    定义单个命令参数的约束和验证规则。
    
    Attributes:
        name (str): 参数名称
        required (bool): 是否必需，默认为False
        type_hint (Optional[type]): 类型提示，默认为None
        default (Any): 默认值，默认为None
        description (str): 参数描述，默认为空字符串
        validator (Optional[Callable]): 自定义验证函数，默认为None
    """
    name: str
    required: bool = False
    type_hint: Optional[type] = None
    default: Any = None
    description: str = ""
    validator: Optional[Callable] = None


@dataclass
class CommandMetadata:
    """
    命令元数据
    
    定义命令的基本信息和执行约束，用于命令注册、验证和管理。
    
    Attributes:
        name (str): 命令名称，必须唯一
        description (str): 命令描述，默认为空字符串
        category (str): 命令分类，默认为 "general"
        version (str): 命令版本号，默认为 "1.0.0"
        author (str): 命令作者，默认为空字符串
        parameters (List[CommandParameter]): 命令参数定义列表，默认为空列表
        requires_confirmation (bool): 是否需要用户确认，默认为 False
        timeout (float): 命令执行超时时间（秒），默认为 30.0
        
    Example:
        >>> metadata = CommandMetadata(
        ...     name="backup",
        ...     description="Create system backup",
        ...     category="system",
        ...     timeout=60.0
        ... )
    """

    name: str
    description: str = ""
    category: str = "general"
    version: str = "1.0.0"
    author: str = ""
    parameters: List[CommandParameter] = field(default_factory=list)
    requires_confirmation: bool = False
    timeout: float = 30.0  # 默认30秒超时


class CommandResult:
    """
    命令执行结果
    
    封装命令执行的结果信息，包括成功/失败状态、消息、数据和错误信息。
    
    Attributes:
        is_success (bool): 命令是否成功执行
        message (str): 执行结果消息
        data (Optional[Dict[str, Any]]): 执行结果数据，默认为 None
        error (Optional[Exception]): 执行过程中发生的错误，默认为 None
        
    Example:
        >>> result = CommandResult.success("Operation completed", {"result": "data"})
        >>> assert result.is_success is True
        >>> assert result.data["result"] == "data"
    """

    def __init__(
        self,
        is_success: bool,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """
        初始化命令执行结果
        
        Args:
            is_success (bool): 命令是否成功执行
            message (str): 执行结果消息，默认为空字符串
            data (Optional[Dict[str, Any]]): 执行结果数据，默认为 None
            error (Optional[Exception]): 执行过程中发生的错误，默认为 None
            
        Example:
            >>> result = CommandResult(True, "Success", {"key": "value"})
        """
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
        """
        创建成功的命令执行结果
        
        Args:
            message (str): 成功消息，默认为 "Command executed successfully"
            data (Optional[Dict[str, Any]]): 成功结果数据，默认为 None
            
        Returns:
            CommandResult: 成功的命令执行结果实例
            
        Example:
            >>> result = CommandResult.success("Backup created", {"path": "/backup/file"})
        """
        return cls(is_success=True, message=message, data=data)

    @classmethod
    def failure(
        cls, message: str, error: Optional[Exception] = None
    ) -> "CommandResult":
        """
        创建失败的命令执行结果
        
        Args:
            message (str): 失败消息
            error (Optional[Exception]): 相关异常，默认为 None
            
        Returns:
            CommandResult: 失败的命令执行结果实例
            
        Example:
            >>> result = CommandResult.failure("File not found", FileNotFoundError())
        """
        return cls(is_success=False, message=message, error=error)


class BaseCommand(ABC):
    """
    命令基类
    
    所有具体命令实现都必须继承此类，提供统一的命令接口和生命周期管理。
    支持自动元数据注入，简化用户实现。
    
    Attributes:
        metadata (CommandMetadata): 命令元数据
        _is_executing (bool): 命令是否正在执行
        _command_metadata (ClassVar[Optional[CommandMetadata]]): 装饰器设置的元数据（类属性）
        
    Lifecycle:
        1. 实例化 (__init__)
        2. 参数验证 (validate_parameters)
        3. 执行 (execute)
        4. 状态查询 (is_executing property)
        
    Example:
        >>> class HelloWorldCommand(BaseCommand):
        ...     def execute(self, **kwargs) -> CommandResult:
        ...         name = kwargs.get("name", "World")
        ...         return CommandResult.success(f"Hello, {name}!")
        ...
        >>> cmd = HelloWorldCommand()
        >>> result = cmd.execute(name="Alice")
    """
    
    # 类级别属性声明，用于装饰器设置
    _command_metadata: ClassVar[Optional[CommandMetadata]] = None

    def __init__(self, metadata: Optional[CommandMetadata] = None) -> None:
        """
        初始化命令基类
        
        Args:
            metadata (Optional[CommandMetadata]): 命令元数据，如果为None则尝试从类属性获取
            
        Example:
            >>> command = BaseCommand()  # 自动使用装饰器设置的元数据
        """
        # 优先使用传入的metadata，否则尝试从类属性获取
        if metadata is not None:
            self.metadata = metadata
        elif self._command_metadata is not None:
            self.metadata = self._command_metadata
        else:
            # 如果都没有，创建默认元数据
            class_name = self.__class__.__name__
            default_name = class_name.lower().replace("command", "")
            self.metadata = CommandMetadata(name=default_name)
        
        self._is_executing = False

    @property
    def name(self) -> str:
        """
        获取命令名称
        
        Returns:
            str: 命令名称
            
        Example:
            >>> metadata = CommandMetadata(name="backup")
            >>> command = BaseCommand(metadata)
            >>> assert command.name == "backup"
        """
        return self.metadata.name

    @property
    def is_executing(self) -> bool:
        """
        检查命令是否正在执行
        
        Returns:
            bool: 如果命令正在执行返回 True，否则返回 False
            
        Example:
            >>> command = BaseCommand(CommandMetadata(name="test"))
            >>> assert not command.is_executing
        """
        return self._is_executing

    def set_executing(self, executing: bool) -> None:
        """
        设置命令执行状态
        
        Args:
            executing (bool): 执行状态，True 表示正在执行
            
        Example:
            >>> command = BaseCommand(CommandMetadata(name="test"))
            >>> command.set_executing(True)
            >>> assert command.is_executing
        """
        self._is_executing = executing

    @abstractmethod
    def execute(self, **kwargs: Any) -> CommandResult:
        """
        执行命令
        
        子类必须实现此方法来定义具体的命令逻辑。
        
        Args:
            **kwargs (Dict[str, Any]): 命令参数
            
        Returns:
            CommandResult: 命令执行结果
            
        Raises:
            NotImplementedError: 如果子类未实现此方法
            
        Example:
            >>> class MyCommand(BaseCommand):
            ...     def execute(self, **kwargs) -> CommandResult:
            ...         return CommandResult.success("Executed")
        """
        pass

    def validate_parameters(self, **kwargs: Any) -> bool:
        """
        验证命令参数
        
        使用CommandParameter定义进行智能参数验证。
        
        Args:
            **kwargs (Dict[str, Any]): 命令参数
            
        Returns:
            bool: 如果所有参数验证通过返回 True，否则返回 False
            
        Example:
            >>> metadata = CommandMetadata(name="test")
            >>> param = CommandParameter(name="name", required=True)
            >>> metadata.parameters = [param]
            >>> command = BaseCommand(metadata)
            >>> assert command.validate_parameters(name="test") is True
            >>> assert command.validate_parameters() is False
        """
        for param_def in self.metadata.parameters:
            param_value = kwargs.get(param_def.name)
            
            # 检查必需参数
            if param_def.required and param_value is None:
                error(f"Missing required parameter: {param_def.name} for command {self.name}")
                return False
            
            # 检查类型（如果指定了类型提示）
            if param_def.type_hint is not None and param_value is not None:
                if not isinstance(param_value, param_def.type_hint):
                    error(f"Parameter {param_def.name} must be of type {param_def.type_hint.__name__}, got {type(param_value).__name__}")
                    return False
            
            # 执行自定义验证器
            if param_def.validator is not None and param_value is not None:
                try:
                    if not param_def.validator(param_value):
                        error(f"Parameter {param_def.name} failed custom validation")
                        return False
                except Exception as e:
                    error(f"Custom validator for parameter {param_def.name} failed: {str(e)}")
                    return False
        
        return True

    def __str__(self) -> str:
        """
        返回命令的字符串表示
        
        Returns:
            str: 命令的字符串表示
            
        Example:
            >>> command = BaseCommand(CommandMetadata(name="test"))
            >>> assert str(command) == "Command(test)"
        """
        return f"Command({self.name})"

    def __repr__(self) -> str:
        """
        返回命令的详细字符串表示
        
        Returns:
            str: 命令的详细字符串表示
            
        Example:
            >>> metadata = CommandMetadata(name="test", category="system")
            >>> command = BaseCommand(metadata)
            >>> assert "Command(name='test', category='system')" in repr(command)
        """
        return f"Command(name='{self.name}', category='{self.metadata.category}')"