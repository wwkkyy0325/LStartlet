"""
持久化管理器
负责管理多个存储实例和提供统一的持久化接口
"""

import os
from typing import Dict, Optional, Any, List
from threading import Lock

from LStartlet.core.persistence.storage.kv_storage import KVStorage
from LStartlet.core.persistence.models.persistence_models import StorageConfig
from LStartlet.core.persistence.exceptions.persistence_exceptions import (
    StorageNotFoundError,
)
from LStartlet.core.logger import info, error
from LStartlet.core.decorators import with_error_handling, with_logging, monitor_metrics


class PersistenceManager:
    """持久化管理器 - 管理多个存储实例"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化持久化管理器

        Args:
            data_dir: 数据目录路径
        """
        self._data_dir = data_dir
        self._storages: Dict[str, KVStorage] = {}
        self._lock = Lock()
        self._is_initialized = False

        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)

    @monitor_metrics("persistence_initialize", include_labels=True)
    @with_error_handling(error_code="PERSISTENCE_INIT_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    def initialize(self) -> bool:
        """
        初始化持久化管理器

        Returns:
            初始化是否成功
        """
        if self._is_initialized:
            return True

        with self._lock:
            # 创建默认存储
            default_config = StorageConfig(
                name="default",
                storage_type="file",
                path=os.path.join(self._data_dir, "default.yaml"),
            )

            default_storage = KVStorage(default_config)
            if not default_storage.initialize():
                error("默认存储初始化失败")
                return False

            self._storages["default"] = default_storage

            # 创建用户偏好存储
            user_prefs_config = StorageConfig(
                name="user_preferences",
                storage_type="file",
                path=os.path.join(self._data_dir, "user_preferences.yaml"),
            )

            user_prefs_storage = KVStorage(user_prefs_config)
            if not user_prefs_storage.initialize():
                error("用户偏好存储初始化失败")
                return False

            self._storages["user_preferences"] = user_prefs_storage

            # 创建窗口状态存储
            window_state_config = StorageConfig(
                name="window_state",
                storage_type="file",
                path=os.path.join(self._data_dir, "window_state.yaml"),
            )

            window_state_storage = KVStorage(window_state_config)
            if not window_state_storage.initialize():
                error("窗口状态存储初始化失败")
                return False

            self._storages["window_state"] = window_state_storage

            self._is_initialized = True
            info("持久化管理器初始化成功")
            return True

    def get_storage(self, storage_name: str = "default") -> KVStorage:
        """
        获取指定存储

        Args:
            storage_name: 存储名称

        Returns:
            存储实例

        Raises:
            StorageNotFoundError: 存储未找到
        """
        if not self._is_initialized:
            raise RuntimeError("持久化管理器未初始化")

        storage = self._storages.get(storage_name)
        if storage is None:
            raise StorageNotFoundError(storage_name)

        return storage

    def create_storage(self, config: StorageConfig) -> KVStorage:
        """
        创建新存储

        Args:
            config: 存储配置

        Returns:
            新创建的存储实例
        """
        if not self._is_initialized:
            raise RuntimeError("持久化管理器未初始化")

        with self._lock:
            if config.name in self._storages:
                return self._storages[config.name]

            storage = KVStorage(config)
            if not storage.initialize():
                raise RuntimeError(f"存储 '{config.name}' 初始化失败")

            self._storages[config.name] = storage
            info(f"创建新存储: {config.name}")
            return storage

    def get_all_storages(self) -> List[str]:
        """获取所有存储名称"""
        if not self._is_initialized:
            raise RuntimeError("持久化管理器未初始化")
        return list(self._storages.keys())

    def close_all_storages(self) -> None:
        """关闭所有存储"""
        if not self._is_initialized:
            return

        with self._lock:
            for storage in self._storages.values():
                storage.close()

            self._storages.clear()
            self._is_initialized = False
            info("所有存储已关闭")

    # 便捷方法 - 直接操作默认存储
    def get(self, key: str, default: Any = None) -> Any:
        """从默认存储获取值"""
        return self.get_storage("default").get(key, default)

    def set(
        self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """向默认存储设置值"""
        return self.get_storage("default").set(key, value, metadata)

    def delete(self, key: str) -> bool:
        """从默认存储删除值"""
        return self.get_storage("default").delete(key)

    def exists(self, key: str) -> bool:
        """检查默认存储中键是否存在"""
        return self.get_storage("default").exists(key)

    # 用户偏好相关方法
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        return self.get_storage("user_preferences").get(key, default)

    def set_user_preference(self, key: str, value: Any) -> bool:
        """设置用户偏好"""
        return self.get_storage("user_preferences").set(key, value)

    # 窗口状态相关方法
    def get_window_state(self, window_id: str, default: Any = None) -> Any:
        """获取窗口状态"""
        return self.get_storage("window_state").get(window_id, default)

    def set_window_state(self, window_id: str, state: Any) -> bool:
        """设置窗口状态"""
        return self.get_storage("window_state").set(window_id, state)
