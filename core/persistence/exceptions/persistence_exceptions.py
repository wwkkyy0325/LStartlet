"""
数据持久层异常定义
"""

from typing import Optional


class PersistenceError(Exception):
    """持久化系统基础异常"""
    
    def __init__(self, operation: str, message: str, inner_exception: Optional[Exception] = None):
        self.operation = operation
        self.inner_exception = inner_exception
        super().__init__(f"持久化操作 '{operation}' 失败: {message}")


class StorageNotFoundError(PersistenceError):
    """存储未找到错误"""
    
    def __init__(self, storage_name: str):
        super().__init__("get_storage", f"存储 '{storage_name}' 未找到")


class TransactionError(PersistenceError):
    """事务错误"""
    
    def __init__(self, message: str, inner_exception: Optional[Exception] = None):
        super().__init__("transaction", message, inner_exception)


class DataSerializationError(PersistenceError):
    """数据序列化错误"""
    
    def __init__(self, data_type: str, message: str, inner_exception: Optional[Exception] = None):
        super().__init__("serialize", f"数据类型 '{data_type}' 序列化失败: {message}", inner_exception)