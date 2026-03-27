"""
数据持久层模型定义
"""

from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StorageItem:
    """存储项模型"""

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)  # type: ignore

    def update_value(self, new_value: Any) -> None:
        """更新值并更新时间戳"""
        self.value = new_value
        self.updated_at = datetime.now()


@dataclass
class StorageConfig:
    """存储配置模型"""

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
    """事务记录模型"""

    transaction_id: str
    operations: Any = field(default_factory=list)  # type: ignore
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # "pending", "committed", "rolled_back"
