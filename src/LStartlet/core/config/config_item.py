"""
配置项定义
"""

from typing import Any, Type, Optional, Callable


class ConfigItem:
    """配置项类"""

    def __init__(
        self,
        key: str,
        default_value: Any,
        current_value: Any,
        value_type: Type[Any],
        description: str = "",
        validator: Optional[Callable[[Any], bool]] = None,
    ):
        """
        初始化配置项

        Args:
            key: 配置项键名
            default_value: 配置项默认值
            current_value: 配置项当前值
            value_type: 配置项值类型
            description: 配置项描述
            validator: 验证函数
        """
        self.key = key
        self.default_value = default_value
        self.current_value = current_value
        self.value_type = value_type
        self.description = description
        self.validator = validator

    def validate(self, value: Any) -> bool:
        """
        验证配置项值

        Args:
            value: 要验证的值

        Returns:
            验证是否通过
        """
        if self.validator is not None:
            return self.validator(value)
        # 基本类型检查
        if self.value_type is type(None):
            return value is None
        return isinstance(value, self.value_type)
