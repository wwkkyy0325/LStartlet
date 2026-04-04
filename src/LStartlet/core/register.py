"""
统一注册装饰器系统

提供统一的装饰器接口用于自动注册服务、插件和命令。
"""

from typing import Type, TypeVar, Optional, Dict, Any, Callable, Union, List
from LStartlet.core.di import get_default_container, ServiceLifetime
from LStartlet.core.di.exceptions import ServiceRegistrationError
from LStartlet.plugin.base.plugin_base import PluginBase
from LStartlet.core.command.command_base import BaseCommand, CommandMetadata, CommandParameter
from LStartlet.core.command.command_registry import command_registry

T = TypeVar('T')
C = TypeVar('C', bound=BaseCommand)


def register_service(
    service_type: Optional[Union[Type[T], str]] = None,
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    implementation_type: Optional[Type[T]] = None
) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """
    服务自动注册装饰器
    
    Args:
        service_type (Optional[Union[Type[T], str]]): 服务类型（接口），如果为None则使用实现类型；如果是字符串则表示无参数调用
        lifetime (ServiceLifetime): 服务生命周期，默认为TRANSIENT
        implementation_type (Optional[Type[T]]): 实现类型，如果为None则使用被装饰的类
        
    Returns:
        Union[Type[T], Callable[[Type[T]], Type[T]]]: 装饰器函数或直接返回类
        
    Example:
        >>> @register_service()
        ... class MyService:
        ...     pass
        
        >>> class IService:
        ...     pass
        ... 
        >>> @register_service(service_type=IService, lifetime=ServiceLifetime.SINGLETON)
        ... class MyServiceImpl(IService):
        ...     pass
    """
    def wrapper(cls: Type[T]) -> Type[T]:
        nonlocal implementation_type
        if implementation_type is None:
            implementation_type = cls
        
        actual_service_type = service_type if isinstance(service_type, type) else implementation_type
        
        try:
            container = get_default_container()
            container.register(
                service_type=actual_service_type,
                implementation_type=implementation_type,
                lifetime=lifetime
            )
        except Exception as e:
            raise ServiceRegistrationError(actual_service_type, f"Failed to register service {cls.__name__}: {str(e)}")
        
        return cls
    
    # 支持无参数调用 @register_service()
    if callable(service_type) and not isinstance(service_type, type):
        # 这是 @register_service() 的情况，service_type 实际上是被装饰的类
        cls = service_type
        return wrapper(cls)
    
    return wrapper


def register_plugin(
    plugin_id: Optional[Union[str, Type]] = None,
    name: Optional[str] = None,
    version: Optional[str] = None,
    description: str = "",
    order: int = 0,
    dependencies: Optional[Dict[str, str]] = None,
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
) -> Union[Type, Callable[[Type], Type]]:
    """
    插件自动注册装饰器
    
    支持两种使用模式：
    1. 完整参数模式：@register_plugin(plugin_id="...", name="...", version="...")
    2. 无参数模式：@register_plugin() - 从插件类的 __init__ 参数或类属性推断元数据
    
    Args:
        plugin_id (Optional[Union[str, Type]]): 插件唯一标识符，如果为None则尝试从类推断；如果是类则表示无参数调用
        name (Optional[str]): 插件名称，如果为None则尝试从类推断  
        version (Optional[str]): 插件版本，如果为None则尝试从类推断
        description (str): 插件描述，默认为空字符串
        order (int): 插件加载顺序，默认为0
        dependencies (Optional[Dict[str, str]]): 插件依赖，默认为None
        lifetime (ServiceLifetime): 插件服务生命周期，默认为SINGLETON
        
    Returns:
        Union[Type, Callable[[Type], Type]]: 装饰器函数或直接返回类
        
    Example:
        # 完整参数模式
        >>> @register_plugin(
        ...     plugin_id="com.example.myplugin",
        ...     name="My Plugin",
        ...     version="1.0.0",
        ...     description="A sample plugin"
        ... )
        ... class MyPlugin(PluginBase):
        ...     def __init__(self):
        ...         super().__init__("com.example.myplugin", "My Plugin", "1.0.0", "A sample plugin")
        ...     
        ...     def initialize(self) -> bool:
        ...         return True
        
        # 无参数模式  
        >>> @register_plugin()
        ... class MyPlugin(PluginBase):
        ...     def __init__(self):
        ...         super().__init__("com.example.myplugin", "My Plugin", "1.0.0")
        ...     
        ...     def initialize(self) -> bool:
        ...         return True
    """
    def wrapper(cls: Type) -> Type:
        # 验证类是否继承自 PluginBase
        if not issubclass(cls, PluginBase):
            raise TypeError(f"Class {cls.__name__} must inherit from PluginBase to be registered as a plugin")
        
        # 如果提供了所有必需参数，直接使用
        if isinstance(plugin_id, str) and name is not None and version is not None:
            metadata = {
                'plugin_id': plugin_id,
                'name': name,
                'version': version,
                'description': description,
                'order': order,
                'dependencies': dependencies or {}
            }
        else:
            # 无参数模式：尝试从类推断元数据
            # 检查类是否已经有 _plugin_metadata 属性（可能是继承或其他装饰器设置的）
            if hasattr(cls, '_plugin_metadata') and cls._plugin_metadata is not None:
                metadata = dict(cls._plugin_metadata)  # 使用dict()而不是copy()
                # 更新可选参数
                if description:
                    metadata['description'] = description
                if dependencies is not None:
                    metadata['dependencies'] = dependencies
                metadata['order'] = order
            else:
                # 尝试从类名生成默认元数据
                default_plugin_id = f"{cls.__module__}.{cls.__name__}".lower().replace("_", ".")
                metadata = {
                    'plugin_id': default_plugin_id,
                    'name': cls.__name__,
                    'version': "1.0.0",  # 默认版本
                    'description': description,
                    'order': order,
                    'dependencies': dependencies or {}
                }
        
        # 设置插件元数据作为类属性
        cls._plugin_metadata = metadata
        
        # 设置 PLUGIN_DEPENDENCIES 类属性（动态设置）
        if metadata['dependencies']:
            setattr(cls, 'PLUGIN_DEPENDENCIES', metadata['dependencies'])
        
        # 同时注册为服务
        try:
            container = get_default_container()
            container.register(
                service_type=cls,
                implementation_type=cls,
                lifetime=lifetime
            )
        except Exception as e:
            raise ServiceRegistrationError(cls, f"Failed to register plugin {cls.__name__} as service: {str(e)}")
        
        return cls
    
    # 支持无参数调用 @register_plugin()
    if callable(plugin_id) and not isinstance(plugin_id, str):
        # 这是 @register_plugin() 的情况，plugin_id 实际上是被装饰的类
        cls = plugin_id
        return wrapper(cls)
    
    return wrapper


def register_command(
    name: Optional[Union[str, Type[C]]] = None,
    description: str = "",
    category: str = "general",
    timeout: float = 30.0,
    version: str = "1.0.0",
    author: str = "",
    parameters: Optional[List[Dict[str, Any]]] = None,
    requires_confirmation: bool = False
) -> Union[Type[C], Callable[[Type[C]], Type[C]]]:
    """
    命令自动注册装饰器
    
    提供更简洁的命令注册方式，自动处理元数据创建和实例化。
    
    Args:
        name (Optional[Union[str, Type[C]]]): 命令名称，如果为None则使用类名（去除Command后缀）；如果是类则表示无参数调用
        description (str): 命令描述，默认为空字符串
        category (str): 命令分类，默认为"general"
        timeout (float): 命令执行超时时间（秒），默认为30.0
        version (str): 命令版本，默认为"1.0.0"
        author (str): 命令作者，默认为空字符串
        parameters (Optional[List[Dict[str, Any]]]): 命令参数定义列表，默认为None
        requires_confirmation (bool): 是否需要用户确认，默认为False
        
    Returns:
        Union[Type[C], Callable[[Type[C]], Type[C]]]: 装饰器函数或直接返回类
        
    Example:
        # 简单用法 - 只需实现execute方法
        >>> @register_command(name="my_cmd", description="My custom command")
        ... class MyCommand(BaseCommand):
        ...     def execute(self, **kwargs) -> CommandResult:
        ...         return CommandResult.success("executed")
        
        # 带参数定义的用法
        >>> @register_command(
        ...     name="backup",
        ...     description="Create backup",
        ...     parameters=[
        ...         {"name": "path", "required": True, "type_hint": str},
        ...         {"name": "compress", "required": False, "default": True}
        ...     ]
        ... )
        ... class BackupCommand(BaseCommand):
        ...     def execute(self, **kwargs) -> CommandResult:
        ...         path = kwargs.get("path")
        ...         compress = kwargs.get("compress", True)
        ...         return CommandResult.success(f"Backup created at {path}")
        
        # 无参数调用
        >>> @register_command()
        ... class SimpleCommand(BaseCommand):
        ...     def execute(self, **kwargs) -> CommandResult:
        ...         return CommandResult.success("Simple command executed")
    """
    def wrapper(cls: Type[C]) -> Type[C]:
        # 验证类是否继承自 BaseCommand
        if not issubclass(cls, BaseCommand):
            raise TypeError(f"Class {cls.__name__} must inherit from BaseCommand to be registered as a command")
        
        # 创建命令元数据
        cmd_name = name if isinstance(name, str) else cls.__name__.lower().replace("command", "")
        
        # 转换参数定义
        command_parameters = []
        if parameters:
            for param_def in parameters:
                command_parameters.append(CommandParameter(**param_def))
        
        metadata = CommandMetadata(
            name=cmd_name,
            description=description,
            category=category,
            version=version,
            author=author,
            parameters=command_parameters,
            requires_confirmation=requires_confirmation,
            timeout=timeout
        )
        
        # 设置命令元数据作为类属性
        cls._command_metadata = metadata
        
        # 立即注册命令实例
        try:
            # 创建命令实例并注册（现在不需要用户手动调用super().__init__）
            cmd_instance = cls()
            command_registry.register_command(cmd_instance)
        except Exception as e:
            raise RuntimeError(f"Failed to register command {cmd_name}: {str(e)}")
        
        return cls
    
    # 支持无参数调用 @register_command()
    if callable(name) and not isinstance(name, str):
        # 这是 @register_command() 的情况，name 实际上是被装饰的类
        cls = name
        return wrapper(cls)
    
    return wrapper