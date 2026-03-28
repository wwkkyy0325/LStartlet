"""
数据持久层模型定义
"""

from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StorageItem:
    """
    存储项模型
    
    表示键值存储中的单个存储项，包含键、值、时间戳和元数据。
    
    Attributes:
        key (str): 存储项的键
        value (Any): 存储项的值
        created_at (datetime): 创建时间戳，默认为当前时间
        updated_at (datetime): 最后更新时间戳，默认为当前时间
        metadata (Dict[str, Any]): 存储项的元数据字典，默认为空字典
        
    Example:
        >>> item = StorageItem("user_preferences", {"theme": "dark"})
        >>> print(item.key)
        user_preferences
    """

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)  # type: ignore

    def update_value(self, new_value: Any) -> None:
        """
        更新值并更新时间戳
        
        Args:
            new_value (Any): 新的值
            
        Example:
            >>> item = StorageItem("config", "old_value")
            >>> old_time = item.updated_at
            >>> item.update_value("new_value")
            >>> assert item.value == "new_value"
            >>> assert item.updated_at > old_time
        """
        self.value = new_value
        self.updated_at = datetime.now()


@dataclass
class StorageConfig:
    """
    存储配置模型
    
    定义键值存储的配置参数，包括存储类型、路径、大小限制等。
    
    Attributes:
        name (str): 存储配置名称
        storage_type (str): 存储类型，可选值: "file", "memory", "database"。默认为 "file"。
        path (str): 存储路径（对于文件存储），默认为空字符串
        max_size_mb (int): 最大大小（MB），默认为 100
        auto_compact (bool): 是否自动压缩， 默认为 True
        backup_count (int): 备份数量， 默认为 7
        encryption_enabled (bool): 是否启用加密， 默认为 False
        compression_enabled (bool): 是否启用压缩， 默认为 True
        
    Example:
        >>> config = StorageConfig("app_cache", storage_type="memory", max_size_mb=50)
    """

    name: str
    storage_type: str = "file"  # "file", "memory", "database"
    path: str = ""
    max_size_mb: int = 100
    auto_compact: bool = True
    backup_count: int = 7
    encryption_enabled: bool = False
    compression_enabled: bool = True


@dataclass
class TransactionRecord:
    """
    事务记录模型
    
    记录存储操作的事务信息，用于事务回滚和审计。
    
    Attributes:
        transaction_id (str): 事务ID
        operations (Any): 操作列表，默认为空列表
        timestamp (datetime): 事务时间戳，默认为当前时间
        status (str): 事务状态，可选值: "pending", "committed", "rolled_back"。默认为 "pending"。
        
    Example:
        >>> record = TransactionRecord("tx_123", [{"op": "set", "key": "test"}])
    """

    transaction_id: str
    operations: Any = field(default_factory=list)  # type: ignore
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # "pending", "committed", "rolled_back"