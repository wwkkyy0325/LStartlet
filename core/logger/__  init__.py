# 设置默认配置 - 使用项目根目录下的logs目录
# configure_logger()  # 移除这行，避免在导入时就初始化日志

# 注册退出清理
import atexit


def _cleanup():
    """清理资源"""
    global _logger_manager
    _logger_manager = None

atexit.register(_cleanup)