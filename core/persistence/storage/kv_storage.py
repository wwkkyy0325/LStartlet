"""
键值存储实现
提供轻量级的键值对存储功能
"""

import yaml
import threading
from pathlib import Path
from typing import Any, Dict, Optional, List, cast
from datetime import datetime

from core.persistence.models.persistence_models import StorageItem, StorageConfig
from core.persistence.exceptions.persistence_exceptions import PersistenceError
from core.logger import info, error, debug


class KVStorage:
    """键值存储 - 提供线程安全的键值对存储功能"""

    def __init__(self, config: StorageConfig):
        """
        初始化键值存储

        Args:
            config: 存储配置
        """
        self.config = config
        self._data: Dict[str, StorageItem] = {}
        self._lock = threading.RLock()
        self._is_initialized = False
        self._storage_path: Optional[Path] = None

        if config.path:
            self._storage_path = Path(config.path)
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> bool:
        """
        初始化存储

        Returns:
            初始化是否成功
        """
        with self._lock:
            if self._is_initialized:
                return True

            try:
                if self._storage_path and self._storage_path.exists():
                    # 从文件加载数据
                    self._load_from_file()
                else:
                    # 创建新的存储
                    self._data = {}

                self._is_initialized = True
                info(f"键值存储 '{self.config.name}' 初始化成功")
                return True

            except Exception as e:
                error(f"键值存储 '{self.config.name}' 初始化失败: {e}")
                return False

    def _load_from_file(self) -> None:
        """从文件加载数据"""
        if not self._storage_path or not self._storage_path.exists():
            return

        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                raw_data = cast(Dict[str, Any], yaml.safe_load(f) or {})

            # 转换为 StorageItem 对象
            self._data = {}
            for key, item_data in raw_data.items():
                created_at = datetime.fromisoformat(str(item_data["created_at"]))
                updated_at = datetime.fromisoformat(str(item_data["updated_at"]))
                self._data[key] = StorageItem(
                    key=str(key),
                    value=item_data["value"],
                    created_at=created_at,
                    updated_at=updated_at,
                    metadata=cast(Dict[str, Any], item_data.get("metadata", {})),
                )

            debug(f"从文件加载了 {len(self._data)} 个存储项")

        except Exception as e:
            raise PersistenceError("load", f"从文件加载数据失败: {e}", e)

    def _save_to_file(self) -> None:
        """保存数据到文件"""
        if not self._storage_path:
            return

        try:
            # 准备要保存的数据
            save_data = {}
            for key, item in self._data.items():
                save_data[key] = {
                    "key": item.key,
                    "value": item.value,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                    "metadata": item.metadata,
                }

            # 写入临时文件，然后原子性地替换原文件
            temp_path = self._storage_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.dump(save_data, f, allow_unicode=True, indent=2, sort_keys=False)

            # 原子性替换
            temp_path.replace(self._storage_path)

            debug(f"保存了 {len(self._data)} 个存储项到文件")

        except Exception as e:
            raise PersistenceError("save", f"保存数据到文件失败: {e}", e)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取值

        Args:
            key: 键
            default: 默认值

        Returns:
            值或默认值
        """
        with self._lock:
            if not self._is_initialized:
                raise RuntimeError("存储未初始化")

            item = self._data.get(key)
            return item.value if item is not None else default

    def set(
        self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        设置值

        Args:
            key: 键
            value: 值
            metadata: 元数据

        Returns:
            设置是否成功
        """
        with self._lock:
            if not self._is_initialized:
                raise RuntimeError("存储未初始化")

            try:
                if key in self._data:
                    # 更新现有项
                    self._data[key].update_value(value)
                    if metadata:
                        self._data[key].metadata.update(metadata)
                else:
                    # 创建新项
                    self._data[key] = StorageItem(
                        key=key, value=value, metadata=metadata or {}
                    )

                # 如果配置了自动保存，立即保存到文件
                if self.config.storage_type == "file":
                    self._save_to_file()

                return True

            except Exception as e:
                error(f"设置键值对失败: {key} = {value}, 错误: {e}")
                return False

    def delete(self, key: str) -> bool:
        """
        删除键值对

        Args:
            key: 键

        Returns:
            删除是否成功
        """
        with self._lock:
            if not self._is_initialized:
                raise RuntimeError("存储未初始化")

            if key in self._data:
                del self._data[key]

                # 如果配置了自动保存，立即保存到文件
                if self.config.storage_type == "file":
                    self._save_to_file()

                return True
            return False

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键

        Returns:
            键是否存在
        """
        with self._lock:
            if not self._is_initialized:
                raise RuntimeError("存储未初始化")
            return key in self._data

    def keys(self) -> List[str]:
        """
        获取所有键

        Returns:
            键列表
        """
        with self._lock:
            if not self._is_initialized:
                raise RuntimeError("存储未初始化")
            return list(self._data.keys())

    def clear(self) -> bool:
        """
        清空所有数据

        Returns:
            清空是否成功
        """
        with self._lock:
            if not self._is_initialized:
                raise RuntimeError("存储未初始化")

            self._data.clear()

            # 如果配置了自动保存，立即保存到文件
            if self.config.storage_type == "file":
                self._save_to_file()

            return True

    def size(self) -> int:
        """
        获取存储大小（键值对数量）

        Returns:
            存储大小
        """
        with self._lock:
            if not self._is_initialized:
                raise RuntimeError("存储未初始化")
            return len(self._data)

    def close(self) -> None:
        """关闭存储"""
        with self._lock:
            if self._is_initialized and self.config.storage_type == "file":
                self._save_to_file()
            self._is_initialized = False
            info(f"键值存储 '{self.config.name}' 已关闭")
