"""
超级简化的路径管理器 - 只提供最基本的路径功能
作为工具函数集合，不包含复杂的类结构和自动检测逻辑
"""

import os
from pathlib import Path
from typing import Optional


def _join_paths(*paths: str) -> str:
    """安全地拼接路径（内部方法）"""
    if not paths:
        return ""

    result = Path(paths[0])
    for path in paths[1:]:
        if path:
            result = result / path

    return str(result.resolve())


def _ensure_directory_exists(path: str) -> str:
    """确保目录存在，不存在则创建（内部方法）"""
    if not path:
        return ""

    normalized_path = str(Path(path).resolve())
    Path(normalized_path).mkdir(parents=True, exist_ok=True)
    return normalized_path


def _get_user_config_root() -> str:
    """获取用户.lstartlet配置根目录（内部方法）"""
    home_dir = os.path.expanduser("~")
    config_root = os.path.join(home_dir, ".lstartlet")
    _ensure_directory_exists(config_root)
    return config_root


def _get_app_path(app_name: str, *subpaths: str) -> str:
    """获取应用程序路径（简化版，内部实现）"""
    root = _get_user_config_root()
    app_path = os.path.join(root, app_name)

    if subpaths:
        for subpath in subpaths:
            app_path = os.path.join(app_path, subpath)

    return app_path


def _ensure_app_directory(app_name: str, *subpaths: str) -> str:
    """确保应用程序目录存在（内部实现）"""
    path = _get_app_path(app_name, *subpaths)
    return _ensure_directory_exists(path)


def _write_app_file(app_name: str, filename: str, content: str, mode: str = "w") -> str:
    """写入应用程序文件（内部实现）"""
    file_path = _get_app_path(app_name, filename)

    dir_path = os.path.dirname(file_path)
    _ensure_directory_exists(dir_path)

    with open(file_path, mode, encoding="utf-8") as f:
        f.write(content)

    return file_path


def _read_app_file(app_name: str, filename: str) -> str:
    """读取应用程序文件（内部实现）"""
    file_path = _get_app_path(app_name, filename)

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _app_file_exists(app_name: str, filename: str) -> bool:
    """检查应用程序文件是否存在（内部实现）"""
    file_path = _get_app_path(app_name, filename)
    return os.path.exists(file_path)


def _delete_app_file(app_name: str, filename: str) -> bool:
    """删除应用程序文件（内部实现）"""
    file_path = _get_app_path(app_name, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def _list_app_files(app_name: str, pattern: str = "*") -> list:
    """列出应用程序目录中的文件（内部实现）"""
    app_path = _get_app_path(app_name)
    search_path = os.path.join(app_path, pattern)

    from glob import glob

    return glob(search_path, recursive=True)


class _AppFileManager:
    """统一的应用文件管理器（内部实现）"""

    app_name: Optional[str]
    _base_dir: Optional[str]

    def __init__(self, app_name: Optional[str] = None, base_dir: Optional[str] = None):
        """初始化文件管理器"""
        self._base_dir = base_dir

        if base_dir is None:
            if app_name is None:
                from ._application_info import _get_current_app_name

                app_name = _get_current_app_name()

            if app_name is None:
                raise ValueError("无法确定应用程序名称，请显式提供 app_name 参数")

            self.app_name = app_name
        else:
            self.app_name = None

    def _get_full_path(self, filename: str) -> str:
        """获取文件的完整路径（内部方法）"""
        if self._base_dir:
            return os.path.join(self._base_dir, filename)
        else:
            assert (
                self.app_name is not None
            ), "app_name cannot be None when base_dir is not set"
            return _get_app_path(self.app_name, filename)

    def read(self, filename: str) -> str:
        """读取文件"""
        file_path = self._get_full_path(filename)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def write(self, filename: str, content: str, mode: str = "w") -> str:
        """写入文件"""
        file_path = self._get_full_path(filename)

        dir_path = os.path.dirname(file_path)
        _ensure_directory_exists(dir_path)

        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)

        return file_path

    def exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        file_path = self._get_full_path(filename)
        return os.path.exists(file_path)

    def delete(self, filename: str) -> bool:
        """删除文件"""
        file_path = self._get_full_path(filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def list(self, pattern: str = "*") -> list:
        """列出文件"""
        if self._base_dir:
            search_path = os.path.join(self._base_dir, pattern)
        else:
            assert (
                self.app_name is not None
            ), "app_name cannot be None when base_dir is not set"
            app_path = _get_app_path(self.app_name)
            search_path = os.path.join(app_path, pattern)

        from glob import glob

        return glob(search_path, recursive=True)

    def get_path(self, *subpaths: str) -> str:
        """获取路径"""
        if self._base_dir:
            return os.path.join(self._base_dir, *subpaths)
        else:
            assert (
                self.app_name is not None
            ), "app_name cannot be None when base_dir is not set"
            return _get_app_path(self.app_name, *subpaths)
