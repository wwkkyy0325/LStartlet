#!/usr/bin/env python3
"""
统一缓存清理工具

提供简单直观的缓存清理功能，支持清理Python缓存文件和目录。
遵循"约定优于配置"原则，提供合理的默认行为。
"""

import os
import shutil
import sys
from pathlib import Path


def _remove_pycache_items(root_path: Path) -> tuple[int, int]:
    """删除__pycache__目录和.pyc文件，返回删除的目录数和文件数"""
    pycache_dirs = []
    pyc_files = []

    # 收集所有需要删除的项目
    for item in root_path.rglob("*"):
        if item.is_dir() and item.name == "__pycache__":
            pycache_dirs.append(item)
        elif item.is_file() and item.suffix == ".pyc":
            pyc_files.append(item)

    # 删除目录
    removed_dirs = 0
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            removed_dirs += 1
        except Exception as e:
            print(f"警告: 无法删除目录 {pycache_dir}: {e}", file=sys.stderr)

    # 删除文件
    removed_files = 0
    for pyc_file in pyc_files:
        try:
            pyc_file.unlink()
            removed_files += 1
        except Exception as e:
            print(f"警告: 无法删除文件 {pyc_file}: {e}", file=sys.stderr)

    return removed_dirs, removed_files


def clean_cache(root_dir: str = ".") -> None:
    """
    清理指定目录下的Python缓存文件

    Args:
        root_dir: 要清理的根目录，默认为当前目录

    这是主要的公共接口，简单直观，符合框架API设计规范
    """
    root_path = Path(root_dir).resolve()
    print(f"清理缓存: {root_path}")

    removed_dirs, removed_files = _remove_pycache_items(root_path)
    total_removed = removed_dirs + removed_files

    if total_removed == 0:
        print("未找到缓存文件")
    else:
        print(
            f"清理完成! 删除了 {total_removed} 个项目 "
            f"({removed_dirs} 个 __pycache__ 目录, {removed_files} 个 .pyc 文件)"
        )


def main() -> None:
    """命令行入口点"""
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    clean_cache(target_dir)


if __name__ == "__main__":
    main()
