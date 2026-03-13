"""
配置项数据类
用于存储单个配置项的元数据和值
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ConfigItem:
    """配置项数据类"""
    key: str
    default_value: Any
    current_value: Any = field(default_factory=lambda: None)
    value_type: type = str
    description: str = ""
    validator: Optional[Callable[[Any], bool]] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.current_value is None:
            self.current_value = self.default_value
    
    def validate(self, value: Any) -> bool:
        """
        验证配置值
        
        Args:
            value: 要验证的值
            
        Returns:
            是否验证通过
        """
        # 检查类型
        if not isinstance(value, self.value_type):
            return False
        
        # 执行自定义验证器
        if self.validator is not None:
            return self.validator(value)
        
        return True
    
    def reset_to_default(self) -> None:
        """重置为默认值"""
        self.current_value = self.default_value