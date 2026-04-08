"""
装饰器主入口模块 - 提供@Component和@Plugin装饰器
"""

from typing import Any, Dict, Type, Optional, Callable, TypeVar, overload

T = TypeVar("T")


class ComponentRegistry:
    """组件注册器 - 用于存储和管理被装饰的组件"""

    _components: Dict[str, Type[Any]] = {}
    _plugins: Dict[str, Type[Any]] = {}

    @classmethod
    def register_component(cls, name: str, obj: Any, is_plugin: bool = False):
        """注册组件"""
        if is_plugin:
            cls._plugins[name] = obj
        else:
            cls._components[name] = obj

    @classmethod
    def register_plugin(cls, name: str, obj: Any):
        """注册插件（便捷方法）"""
        cls._plugins[name] = obj

    @classmethod
    def get_component(cls, name: str) -> Optional[Any]:
        """获取组件"""
        return cls._components.get(name)

    @classmethod
    def get_plugin(cls, name: str) -> Optional[Any]:
        """获取插件"""
        return cls._plugins.get(name)

    @classmethod
    def get_components(cls) -> Dict[str, Any]:
        """获取所有组件（兼容性方法）"""
        return cls._components.copy()

    @classmethod
    def get_plugins(cls) -> Dict[str, Any]:
        """获取所有插件（兼容性方法）"""
        return cls._plugins.copy()

    @classmethod
    def clear(cls):
        """清空注册表（用于测试）"""
        cls._components.clear()
        cls._plugins.clear()


def _get_name(obj: Any, provided_name: Optional[str] = None) -> str:
    """获取组件/插件名称"""
    if provided_name is not None:
        return provided_name
    if hasattr(obj, "__name__"):
        return obj.__name__
    return str(obj)


def _validate_inheritance(obj: Any, is_plugin: bool = False):
    """验证继承关系"""
    if is_plugin:
        from ._plugin_base import PluginBase

        if not issubclass(obj, PluginBase):
            raise TypeError(f"Plugin {obj.__name__} 必须继承自 PluginBase")
    # 组件不需要特定基类


@overload
def Component(name_or_cls: type[T]) -> type[T]: ...


@overload
def Component(
    name_or_cls: str,
    *,
    scope: str = "singleton",
    singleton: Optional[bool] = None,
) -> Callable[[type[T]], type[T]]: ...


@overload
def Component(
    *,
    scope: str = "singleton",
    singleton: Optional[bool] = None,
) -> Callable[[type[T]], type[T]]: ...


def Component(
    name_or_cls=None, *, scope: str = "singleton", singleton: Optional[bool] = None
):
    """
    组件装饰器 - 用于标记一个类为可注入的组件

    Args:
        name_or_cls: 组件名称（字符串）或被装饰的类（当直接使用@Component时）
        scope: 实例作用域，'singleton'（单例）或 'transient'（瞬态），默认为'singleton'
        singleton: 已弃用，请使用 scope 参数

    Example:
        @Component("my_service")
        class MyService:
            pass

        @Component  # 使用类名作为组件名，单例
        class AnotherService:
            pass

        @Component(scope='transient')  # 瞬态实例
        class TransientService:
            pass

        @Component("transient_service", scope='transient')  # 命名瞬态实例
        class NamedTransientService:
            pass
    """
    # 处理向后兼容性：如果提供了 singleton 参数且没有提供 scope，则转换为 scope
    if singleton is not None:
        # 只有当 scope 为默认值时才使用 singleton 参数
        # 这样可以确保 scope 参数优先于 singleton 参数
        if scope == "singleton":
            scope = "singleton" if singleton else "transient"

    # 验证 scope 参数
    if scope not in ("singleton", "transient"):
        raise ValueError(f"scope must be 'singleton' or 'transient', got '{scope}'")

    singleton_bool = scope == "singleton"

    if callable(name_or_cls):
        # @Component 用法 - name_or_cls 是类
        cls = name_or_cls
        component_name = cls.__name__
        _register_component(
            cls, component_name, is_plugin=False, singleton=singleton_bool
        )
        return cls
    else:
        # @Component("name") 或 @Component(scope='transient') 用法
        def decorator(cls):
            component_name = name_or_cls if name_or_cls is not None else cls.__name__
            _register_component(
                cls, component_name, is_plugin=False, singleton=singleton_bool
            )
            return cls

        return decorator


@overload
def Plugin(name_or_cls: type[T]) -> type[T]: ...


@overload
def Plugin(
    name_or_cls: str,
    *,
    scope: str = "singleton",
    singleton: Optional[bool] = None,
) -> Callable[[type[T]], type[T]]: ...


@overload
def Plugin(
    *,
    scope: str = "singleton",
    singleton: Optional[bool] = None,
) -> Callable[[type[T]], type[T]]: ...


def Plugin(
    name_or_cls=None, *, scope: str = "singleton", singleton: Optional[bool] = None
):
    """
    插件装饰器 - 用于标记一个类为插件

    Args:
        name_or_cls: 插件名称（字符串）或被装饰的类（当直接使用@Plugin时）
        scope: 实例作用域，'singleton'（单例）或 'transient'（瞬态），默认为'singleton'
        singleton: 已弃用，请使用 scope 参数

    Example:
        @Plugin("my_plugin")
        class MyPlugin(PluginBase):
            pass

        @Plugin  # 使用类名作为插件名，单例
        class AnotherPlugin(PluginBase):
            pass

        @Plugin(scope='transient')  # 瞬态插件
        class TransientPlugin(PluginBase):
            pass

        @Plugin("transient_plugin", scope='transient')  # 命名瞬态插件
        class NamedTransientPlugin(PluginBase):
            pass
    """
    # 处理向后兼容性：如果提供了 singleton 参数且没有提供 scope，则转换为 scope
    if singleton is not None:
        # 只有当 scope 为默认值时才使用 singleton 参数
        # 这样可以确保 scope 参数优先于 singleton 参数
        if scope == "singleton":
            scope = "singleton" if singleton else "transient"

    # 验证 scope 参数
    if scope not in ("singleton", "transient"):
        raise ValueError(f"scope must be 'singleton' or 'transient', got '{scope}'")

    singleton_bool = scope == "singleton"

    if callable(name_or_cls):
        # @Plugin 用法 - name_or_cls 是类
        cls = name_or_cls
        # 验证继承关系
        _validate_inheritance(cls, is_plugin=True)
        plugin_name = cls.__name__
        _register_component(cls, plugin_name, is_plugin=True, singleton=singleton_bool)
        return cls
    else:
        # @Plugin("name") 或 @Plugin(scope='transient') 用法
        def decorator(cls):
            # 验证继承关系
            _validate_inheritance(cls, is_plugin=True)
            plugin_name = name_or_cls if name_or_cls is not None else cls.__name__
            _register_component(
                cls, plugin_name, is_plugin=True, singleton=singleton_bool
            )
            return cls

        return decorator


def _register_component(
    cls: Any, name: str, is_plugin: bool = False, singleton: bool = True
):
    """注册组件或插件的内部函数"""
    # 注册到组件注册器
    if is_plugin:
        ComponentRegistry.register_plugin(name, cls)
    else:
        ComponentRegistry.register_component(name, cls)

    # 延迟导入DI容器以避免循环依赖
    from ._di_decorator import get_di_container

    di_container = get_di_container()
    if is_plugin:
        di_container.register_plugin(name, cls, singleton=singleton)
    else:
        di_container.register_component(name, cls, singleton=singleton)

    # 添加统一的元数据到类（使用列表格式与其他装饰器保持一致）
    if not hasattr(cls, "_decorator_metadata"):
        setattr(cls, "_decorator_metadata", [])

    scope = "singleton" if singleton else "transient"
    decorator_metadata = {
        "type": "plugin" if is_plugin else "component",
        "name": name,
        "scope": scope,
        "singleton": singleton,  # 保持向后兼容性
    }
    getattr(cls, "_decorator_metadata").append(decorator_metadata)

    # 保持向后兼容性：同时设置旧的 _component_metadata 属性
    cls._component_metadata = {
        "name": name,
        "type": "plugin" if is_plugin else "component",
        "is_plugin": is_plugin,
        "singleton": singleton,
        "scope": scope,  # 新增 scope 字段
    }

    # 注册生命周期方法
    try:
        from ._lifecycle_decorator import register_lifecycle_methods_for_class

        register_lifecycle_methods_for_class(cls)
    except ImportError:
        # 如果生命周期模块未导入，跳过处理
        pass
