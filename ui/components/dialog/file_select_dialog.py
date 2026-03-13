"""
文件选择弹窗UI组件
提供专门的文件和目录选择对话框，支持图片和PDF文件筛选
"""

import os
import sys
from typing import List, Optional, Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog, QWidget
)


class FileSelectDialog:
    """
    文件选择弹窗类
    提供统一的文件和目录选择界面，支持批量选择和文件类型过滤
    直接使用系统原生文件对话框，包含左侧快捷位置（盘符、桌面、文档等）
    """
    
    # 支持的文件扩展名
    IMAGE_EXTENSIONS = [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
        '.webp', '.svg', '.ico', '.raw', '.cr2', '.nef', '.arw'
    ]
    
    DOCUMENT_EXTENSIONS = ['.pdf']
    
    @staticmethod
    def _get_supported_extensions() -> List[str]:
        """获取所有支持的文件扩展名"""
        return FileSelectDialog.IMAGE_EXTENSIONS + FileSelectDialog.DOCUMENT_EXTENSIONS
    
    @staticmethod
    def _create_file_filter() -> str:
        """创建文件过滤器字符串"""
        image_ext_str = " ".join(f"*{ext}" for ext in FileSelectDialog.IMAGE_EXTENSIONS)
        doc_ext_str = " ".join(f"*{ext}" for ext in FileSelectDialog.DOCUMENT_EXTENSIONS)
        all_ext_str = " ".join(f"*{ext}" for ext in FileSelectDialog._get_supported_extensions())
        
        return (
            f"支持的文件 ({all_ext_str});;"
            f"图片文件 ({image_ext_str});;"
            f"PDF文件 ({doc_ext_str});;"
            "所有文件 (*.*)"
        )
    
    @staticmethod
    def select_files(
        parent: Optional[QWidget] = None,
        title: str = "选择图片或PDF文件",
        initial_directory: Optional[str] = None,
        allow_multiple: bool = True,
        custom_filter: Optional[str] = None,
        file_validator: Optional[Callable[[str], bool]] = None
    ) -> List[str]:
        """
        选择一个或多个文件
        
        Args:
            parent: 父窗口部件
            title: 对话框标题
            initial_directory: 初始目录路径
            allow_multiple: 是否允许多选
            custom_filter: 自定义文件过滤器字符串，格式如 "*.txt *.pdf"
            file_validator: 自定义文件验证函数，接收文件路径返回bool
            
        Returns:
            选中的文件路径列表
        """
        if initial_directory is None:
            initial_directory = FileSelectDialog._get_default_directory()
        
        # 确保初始目录存在
        if not os.path.exists(initial_directory):
            initial_directory = str(Path.home())
        
        # 使用系统原生对话框，自动包含左侧快捷位置（盘符、桌面、文档等）
        options = (
            QFileDialog.Option.ReadOnly |
            QFileDialog.Option.HideNameFilterDetails
        )
        
        # 确定使用的过滤器
        if custom_filter is not None:
            # 直接使用自定义过滤器（已假设是有效的字符串）
            file_filter = custom_filter
        else:
            file_filter = FileSelectDialog._create_file_filter()
        
        if allow_multiple:
            files, _ = QFileDialog.getOpenFileNames(
                parent,
                title,
                initial_directory,
                file_filter,
                options=options
            )
        else:
            file, _ = QFileDialog.getOpenFileName(
                parent,
                title,
                initial_directory,
                file_filter,
                options=options
            )
            files = [file] if file else []
        
        # 过滤文件：先按扩展名过滤，再按自定义验证器过滤
        supported_files: List[str] = []
        for file_path in files:
            if file_path:
                # 如果提供了自定义验证器，使用验证器
                if file_validator is not None:
                    if file_validator(file_path):
                        supported_files.append(file_path)
                else:
                    # 否则使用默认的扩展名过滤
                    ext = Path(file_path).suffix.lower()
                    if ext in FileSelectDialog._get_supported_extensions():
                        supported_files.append(file_path)
        
        return supported_files
    
    @staticmethod
    def select_directory(
        parent: Optional[QWidget] = None,
        title: str = "选择包含图片/PDF的目录",
        initial_directory: Optional[str] = None
    ) -> str:
        """
        选择目录
        
        Args:
            parent: 父窗口部件
            title: 对话框标题
            initial_directory: 初始目录路径
            
        Returns:
            选中的目录路径，如果取消则返回空字符串
        """
        if initial_directory is None:
            initial_directory = FileSelectDialog._get_default_directory()
        
        # 确保初始 directory exists
        if not os.path.exists(initial_directory):
            initial_directory = str(Path.home())
        
        # 使用系统原生对话框，自动包含左侧快捷位置
        options = (
            QFileDialog.Option.ShowDirsOnly |
            QFileDialog.Option.ReadOnly |
            QFileDialog.Option.HideNameFilterDetails
        )
        
        directory = QFileDialog.getExistingDirectory(
            parent,
            title,
            initial_directory,
            options
        )
        
        return directory if directory else ""
    
    @staticmethod
    def _get_default_directory() -> str:
        """获取默认的初始目录"""
        # 优先使用图片目录
        if sys.platform == "win32":
            pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
            if os.path.exists(pictures_dir):
                return pictures_dir
        elif sys.platform == "darwin":  # macOS
            pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
            if os.path.exists(pictures_dir):
                return pictures_dir
        else:  # Linux
            pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
            if not os.path.exists(pictures_dir):
                pictures_dir = os.path.join(os.path.expanduser("~"), "图片")
            if os.path.exists(pictures_dir):
                return pictures_dir
        
        # 如果图片目录不存在，使用用户主目录
        return str(Path.home())


# 便捷函数
def select_image_and_pdf_files(
    parent: Optional[QWidget] = None,
    title: str = "选择图片或PDF文件",
    initial_directory: Optional[str] = None,
    allow_multiple: bool = True,
    custom_filter: Optional[str] = None,
    file_validator: Optional[Callable[[str], bool]] = None
) -> List[str]:
    """
    便捷函数：选择图片和PDF文件
    
    Args:
        parent: 父窗口部件
        title: 对话框标题
        initial_directory: 初始目录路径
        allow_multiple: 是否允许多选
        custom_filter: 自定义文件过滤器字符串
        file_validator: 自定义文件验证函数
        
    Returns:
        选中的文件路径列表
    """
    return FileSelectDialog.select_files(
        parent=parent,
        title=title,
        initial_directory=initial_directory,
        allow_multiple=allow_multiple,
        custom_filter=custom_filter,
        file_validator=file_validator
    )


def select_directory_for_ocr(
    parent: Optional[QWidget] = None,
    title: str = "选择OCR处理目录",
    initial_directory: Optional[str] = None
) -> str:
    """
    便捷函数：选择OCR处理目录
    
    Args:
        parent: 父窗口部件
        title: 对话框标题
        initial_directory: 初始目录路径
        
    Returns:
        选中的目录路径
    """
    return FileSelectDialog.select_directory(
        parent=parent,
        title=title,
        initial_directory=initial_directory
    )


# 预定义的常用过滤器
class FileFilters:
    """预定义的常用文件过滤器"""
    
    @staticmethod
    def images_only() -> str:
        """仅图片文件"""
        extensions = FileSelectDialog.IMAGE_EXTENSIONS
        ext_str = " ".join(f"*{ext}" for ext in extensions)
        return f"图片文件 ({ext_str})"
    
    @staticmethod
    def pdf_only() -> str:
        """仅PDF文件"""
        return "PDF文件 (*.pdf)"
    
    @staticmethod
    def documents_only() -> str:
        """文档文件（PDF + 常见文档格式）"""
        doc_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf']
        ext_str = " ".join(f"*{ext}" for ext in doc_extensions)
        return f"文档文件 ({ext_str})"
    
    @staticmethod
    def custom_extensions(extensions: List[str]) -> str:
        """
        自定义扩展名过滤器
        
        Args:
            extensions: 扩展名列表，如 ['.jpg', '.png', '.pdf']
            
        Returns:
            过滤器字符串
        """
        # 确保扩展名以点开头
        normalized_exts: List[str] = []
        ext: str
        for ext in extensions:
            if not ext.startswith('.'):
                normalized_exts.append(f'.{ext}')
            else:
                normalized_exts.append(ext)
        
        ext_str = " ".join(f"*{ext}" for ext in normalized_exts)
        return f"自定义文件 ({ext_str})"
    
    @staticmethod
    def create_custom_filter(
        filter_name: str,
        extensions: List[str]
    ) -> str:
        """
        创建自定义文件过滤器
        
        Args:
            filter_name: 过滤器名称
            extensions: 扩展名列表
            
        Returns:
            过滤器字符串
        """
        # 确保扩展名以点开头
        normalized_exts: List[str] = []
        for ext in extensions:
            if not ext.startswith('.'):
                normalized_exts.append(f'.{ext}')
            else:
                normalized_exts.append(ext)
        
        ext_str = " ".join(f"*{ext}" for ext in normalized_exts)
        return f"{filter_name} ({ext_str})"


# 预定义的常用验证器
class FileValidators:
    """预定义的常用文件验证器"""
    
    @staticmethod
    def by_size(max_size_mb: float = 10.0) -> Callable[[str], bool]:
        """
        按文件大小验证
        
        Args:
            max_size_mb: 最大文件大小（MB）
            
        Returns:
            验证函数
        """
        def validator(file_path: str) -> bool:
            try:
                file_size = os.path.getsize(file_path)
                return file_size <= (max_size_mb * 1024 * 1024)
            except (OSError, ValueError):
                return False
        return validator
    
    @staticmethod
    def by_extension(allowed_extensions: List[str]) -> Callable[[str], bool]:
        """
        按扩展名验证
        
        Args:
            allowed_extensions: 允许的扩展名列表
            
        Returns:
            验证函数
        """
        def validator(file_path: str) -> bool:
            ext = Path(file_path).suffix.lower()
            return ext in allowed_extensions
        return validator
    
    @staticmethod
    def combined(*validators: Callable[[str], bool]) -> Callable[[str], bool]:
        """
        组合多个验证器（逻辑AND）
        
        Args:
            validators: 多个验证函数
            
        Returns:
            组合后的验证函数
        """
        def combined_validator(file_path: str) -> bool:
            return all(validator(file_path) for validator in validators)
        return combined_validator