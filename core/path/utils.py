"""
路径工具函数
提供路径操作的实用工具函数，确保路径操作的安全性和一致性
"""

import os
from pathlib import Path
from typing import Optional


class PathUtils:
    """路径工具类 - 提供安全的路径操作方法"""

    @staticmethod
    def join_paths(*paths: str) -> str:
        """
        安全地拼接路径

        Args:
            *paths: 要拼接的路径片段

        Returns:
            拼接后的标准化路径
        """
        if not paths:
            return ""

        # 使用pathlib进行跨平台路径拼接
        result = Path(paths[0])
        for path in paths[1:]:
            if path:
                result = result / path

        return str(result.resolve())

    @staticmethod
    def normalize_path(path: str) -> str:
        """
        标准化路径格式

        Args:
            path: 要标准化的路径

        Returns:
            标准化后的路径
        """
        if not path:
            return ""

        # 使用pathlib进行路径标准化
        return str(Path(path).resolve())

    @staticmethod
    def is_valid_path(path: Optional[str]) -> bool:
        """
        校验路径是否有效

        Args:
            path: 要校验的路径

        Returns:
            路径是否有效
        """
        if path is None:
            return False

        try:
            # 尝试创建Path对象
            Path(path)
            return True
        except (OSError, ValueError):
            return False

    @staticmethod
    def ensure_directory_exists(path: str) -> str:
        """
        确保目录存在，不存在则创建

        Args:
            path: 目录路径

        Returns:
            标准化后的目录路径
        """
        if not path:
            return ""

        normalized_path = PathUtils.normalize_path(path)
        path_obj = Path(normalized_path)

        try:
            # 创建目录（包括父目录）
            path_obj.mkdir(parents=True, exist_ok=True)
            return normalized_path
        except OSError as e:
            # 如果创建失败，尝试使用当前工作目录
            from core.logger import warning

            warning(f"Failed to create directory {normalized_path}: {e}")
            return os.getcwd()

    @staticmethod
    def get_file_size(path: str) -> int:
        """
        获取文件大小（字节）

        Args:
            path: 文件路径

        Returns:
            文件大小（字节），如果文件不存在返回0
        """
        if not path or not os.path.exists(path):
            return 0

        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    @staticmethod
    def path_exists(path: str) -> bool:
        """
        检查路径是否存在

        Args:
            path: 要检查的路径

        Returns:
            路径是否存在
        """
        if not path:
            return False

        return os.path.exists(path)

    @staticmethod
    def get_file_extension(path: str) -> str:
        """
        获取文件扩展名

        Args:
            path: 文件路径

        Returns:
            文件扩展名（包含点号，如 '.txt'）
        """
        if not path:
            return ""
        return Path(path).suffix.lower()

    @staticmethod
    def get_filename_without_extension(path: str) -> str:
        """
        获取不包含扩展名的文件名

        Args:
            path: 文件路径

        Returns:
            不包含扩展名的文件名
        """
        if not path:
            return ""
        return Path(path).stem

    @staticmethod
    def is_subpath(child_path: str, parent_path: str) -> bool:
        """
        检查 child_path 是否是 parent_path 的子路径

        Args:
            child_path: 子路径
            parent_path: 父路径

        Returns:
            是否为子路径
        """
        try:
            child = Path(child_path).resolve()
            parent = Path(parent_path).resolve()
            return str(child).startswith(str(parent))
        except (OSError, ValueError):
            return False

    @staticmethod
    def make_relative_path(target_path: str, base_path: str) -> str:
        """
        获取相对于基准路径的相对路径

        Args:
            target_path: 目标路径
            base_path: 基准路径

        Returns:
            相对路径
        """
        try:
            target = Path(target_path).resolve()
            base = Path(base_path).resolve()
            return str(target.relative_to(base))
        except (OSError, ValueError, RuntimeError):
            # 如果无法计算相对路径，返回目标路径的绝对路径
            return str(Path(target_path).resolve())
