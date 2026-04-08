"""
全局上下文管理器 - 统一管理应用级别的上下文变量

提供线程安全的全局上下文存储，避免零散的全局变量。
支持类型验证、默认值、生命周期管理和事件通知。
"""

import threading
from typing import Any, Dict, Optional, Type, TypeVar, Generic, Callable
from dataclasses import dataclass
from contextlib import contextmanager

# 延迟导入以避免循环依赖
_event_bus = None


@dataclass
class ContextVariable:
    """上下文变量定义"""

    key: str
    value: Any = None
    default_value: Any = None
    value_type: Optional[Type] = None
    description: str = ""
    readonly: bool = False
    validator: Optional[Callable[[Any], bool]] = None


class GlobalContextManager:
    """全局上下文管理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化上下文管理器"""
        self._context: Dict[str, ContextVariable] = {}
        self._thread_local = threading.local()
        self._readonly_keys: set = set()

    def register_variable(
        self,
        key: str,
        default_value: Any = None,
        value_type: Optional[Type] = None,
        description: str = "",
        readonly: bool = False,
        validator: Optional[Callable[[Any], bool]] = None,
    ) -> None:
        """
        注册上下文变量

        Args:
            key: 变量键名
            default_value: 默认值
            value_type: 期望的值类型（用于类型检查）
            description: 变量描述
            readonly: 是否只读
            validator: 自定义验证函数
        """
        if key in self._context:
            # 允许重复注册（幂等性）
            existing = self._context[key]
            if existing.readonly and readonly != existing.readonly:
                raise ValueError(
                    f"Cannot change readonly status of existing variable: {key}"
                )
            return

        variable = ContextVariable(
            key=key,
            value=default_value,
            default_value=default_value,
            value_type=value_type,
            description=description,
            readonly=readonly,
            validator=validator,
        )

        self._context[key] = variable

        if readonly:
            self._readonly_keys.add(key)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取上下文变量值

        Args:
            key: 变量键名
            default: 默认值（如果变量未注册或值为None）

        Returns:
            变量值或默认值
        """
        if key not in self._context:
            return default

        variable = self._context[key]
        return variable.value if variable.value is not None else variable.default_value

    def set(self, key: str, value: Any) -> None:
        """
        设置上下文变量值

        Args:
            key: 变量键名
            value: 新值

        Raises:
            ValueError: 如果变量不存在、只读或验证失败
        """
        if key not in self._context:
            raise ValueError(f"Context variable '{key}' not registered")

        if key in self._readonly_keys:
            raise ValueError(f"Cannot modify readonly context variable: {key}")

        variable = self._context[key]

        # 类型验证
        if variable.value_type is not None and not isinstance(
            value, variable.value_type
        ):
            raise TypeError(
                f"Expected type {variable.value_type.__name__} for '{key}', "
                f"got {type(value).__name__}"
            )

        # 自定义验证
        if variable.validator is not None and not variable.validator(value):
            raise ValueError(f"Validation failed for context variable '{key}'")

        old_value = variable.value
        variable.value = value

        # 触发上下文变更事件
        self._notify_context_change(key, old_value, value)

    def reset(self, key: str) -> None:
        """
        重置上下文变量到默认值

        Args:
            key: 变量键名

        Raises:
            ValueError: 如果变量不存在或只读
        """
        if key not in self._context:
            raise ValueError(f"Context variable '{key}' not registered")

        if key in self._readonly_keys:
            raise ValueError(f"Cannot reset readonly context variable: {key}")

        variable = self._context[key]
        old_value = variable.value
        variable.value = variable.default_value

        self._notify_context_change(key, old_value, variable.default_value)

    def reset_all(self) -> None:
        """重置所有可写上下文变量到默认值"""
        for key in list(self._context.keys()):
            if key not in self._readonly_keys:
                self.reset(key)

    def has_key(self, key: str) -> bool:
        """检查是否存在指定的上下文变量"""
        return key in self._context

    def get_all_keys(self) -> list:
        """获取所有上下文变量键名"""
        return list(self._context.keys())

    def get_metadata(self, key: str) -> Optional[ContextVariable]:
        """获取上下文变量的元数据"""
        return self._context.get(key)

    def clear(self) -> None:
        """清除所有上下文变量（谨慎使用）"""
        self._context.clear()
        self._readonly_keys.clear()

    def _notify_context_change(self, key: str, old_value: Any, new_value: Any):
        """通知上下文变更事件"""
        global _event_bus
        if _event_bus is None:
            try:
                from ._event_decorator import get_event_bus

                _event_bus = get_event_bus()
            except ImportError:
                return

        # 发布上下文变更事件
        try:
            from dataclasses import dataclass
            from ._event_decorator import Event

            @dataclass
            class ContextChangeEvent(Event):
                key: str
                old_value: Any
                new_value: Any

            _event_bus.publish(ContextChangeEvent(key, old_value, new_value))
        except Exception:
            # 事件发布失败不影响主逻辑
            pass

    @contextmanager
    def temporary_context(self, **kwargs):
        """
        临时上下文管理器

        在with块内临时修改上下文变量，退出时自动恢复

        Example:
            with global_context.temporary_context(debug_mode=True, user_id="test"):
                # 在此块内使用临时值
                pass
        """
        original_values = {}

        try:
            # 保存原始值并设置临时值
            for key, temp_value in kwargs.items():
                if key in self._context:
                    original_values[key] = self.get(key)
                    self.set(key, temp_value)
                else:
                    # 临时注册新变量
                    self.register_variable(key, temp_value)
                    original_values[key] = None

            yield self

        finally:
            # 恢复原始值
            for key, original_value in original_values.items():
                if original_value is None:
                    # 删除临时注册的变量
                    if key in self._context:
                        del self._context[key]
                        if key in self._readonly_keys:
                            self._readonly_keys.remove(key)
                else:
                    self.set(key, original_value)


# 全局上下文管理器实例
_global_context_manager = GlobalContextManager()


def get_global_context() -> GlobalContextManager:
    """获取全局上下文管理器实例"""
    return _global_context_manager


# 便捷函数
def register_context_variable(
    key: str,
    default_value: Any = None,
    value_type: Optional[Type] = None,
    description: str = "",
    readonly: bool = False,
    validator: Optional[Callable[[Any], bool]] = None,
) -> None:
    """注册上下文变量的便捷函数"""
    get_global_context().register_variable(
        key, default_value, value_type, description, readonly, validator
    )


def get_context_value(key: str, default: Any = None) -> Any:
    """获取上下文变量值的便捷函数"""
    return get_global_context().get(key, default)


def set_context_value(key: str, value: Any) -> None:
    """设置上下文变量值的便捷函数"""
    get_global_context().set(key, value)


def reset_context_value(key: str) -> None:
    """重置上下文变量的便捷函数"""
    get_global_context().reset(key)


def reset_all_context() -> None:
    """重置所有上下文变量的便捷函数"""
    get_global_context().reset_all()
