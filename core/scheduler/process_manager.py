"""
调度系统进程管理器
负责进程的创建、启停、监控和资源管理
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
# 使用项目自定义日志管理器
from core.logger import info, warning, error
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, Future
import atexit


class ProcessState(Enum):
    """进程状态枚举"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class ProcessInfo:
    """进程信息数据类"""
    process_id: int
    state: ProcessState
    start_time: float
    config: Dict[str, Any]
    exit_code: Optional[int] = None


class ProcessManager:
    """进程管理器"""
    
    def __init__(self, max_processes: int = 4, process_timeout: float = 30.0):
        """
        初始化进程管理器
        
        Args:
            max_processes: 最大并发进程数
            process_timeout: 进程超时时间（秒）
        """
        self.max_processes = max_processes
        self.process_timeout = process_timeout
        self._processes: Dict[int, ProcessInfo] = {}
        self._executor: Optional[ProcessPoolExecutor] = None
        self._cleanup_registered = False
        
        # 注册清理函数
        self._register_cleanup()
    
    def _register_cleanup(self) -> None:
        """注册清理函数"""
        if not self._cleanup_registered:
            atexit.register(self.cleanup)
            self._cleanup_registered = True
    
    def start(self) -> None:
        """启动进程管理器"""
        if self._executor is not None:
            warning("Process manager is already started")
            return
        
        self._executor = ProcessPoolExecutor(max_workers=self.max_processes)
        info(f"Process manager started with {self.max_processes} workers")
    
    def stop(self, timeout: Optional[float] = None) -> None:
        """
        停止进程管理器
        
        Args:
            timeout: 停止超时时间，None表示使用默认超时
        """
        if self._executor is None:
            return
        
        try:
            self._executor.shutdown(wait=True)
            self._executor = None
            info("Process manager stopped successfully")
        except Exception as e:
            error(f"Error stopping process manager: {e}")
            if self._executor is not None:
                self._executor.shutdown(wait=False)
            self._executor = None
    
    def cleanup(self) -> None:
        """清理资源"""
        self.stop()
        self._processes.clear()
    
    async def create_process(
        self, 
        target_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> int:
        """
        创建并启动新进程
        
        Args:
            target_func: 目标函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            进程ID
        """
        if self._executor is None:
            raise RuntimeError("Process manager not started. Call start() first.")
        
        if len(self._processes) >= self.max_processes:
            raise RuntimeError(f"Maximum number of processes ({self.max_processes}) reached")
        
        # 提交任务到进程池
        future: Future[Any] = self._executor.submit(target_func, *args, **kwargs)
        
        # 创建进程信息
        process_id = id(future)
        process_info = ProcessInfo(
            process_id=process_id,
            state=ProcessState.STARTING,
            start_time=asyncio.get_event_loop().time(),
            config={'target_func': target_func.__name__}
        )
        self._processes[process_id] = process_info
        
        # 更新进程状态为运行中
        process_info.state = ProcessState.RUNNING
        
        return process_id
    
    def get_process_info(self, process_id: int) -> Optional[ProcessInfo]:
        """
        获取进程信息
        
        Args:
            process_id: 进程ID
            
        Returns:
            进程信息，如果不存在则返回None
        """
        return self._processes.get(process_id)
    
    def list_processes(self) -> List[ProcessInfo]:
        """获取所有进程信息列表"""
        return list(self._processes.values())
    
    def get_active_process_count(self) -> int:
        """获取活跃进程数量"""
        return len([p for p in self._processes.values() if p.state == ProcessState.RUNNING])
    
    def is_process_running(self, process_id: int) -> bool:
        """
        检查进程是否正在运行
        
        Args:
            process_id: 进程ID
            
        Returns:
            是否正在运行
        """
        process_info = self._processes.get(process_id)
        return process_info is not None and process_info.state == ProcessState.RUNNING
    
    async def wait_for_process(self, process_id: int, timeout: Optional[float] = None) -> Any:
        """
        等待进程完成
        
        Args:
            process_id: 进程ID
            timeout: 等待超时时间
            
        Returns:
            进程执行结果
            
        Raises:
            TimeoutError: 进程超时
            Exception: 进程执行异常
        """
        if process_id not in self._processes:
            raise ValueError(f"Process {process_id} not found")
        
        process_info = self._processes[process_id]
        if process_info.state != ProcessState.RUNNING:
            raise RuntimeError(f"Process {process_id} is not running")
        
        # 这里需要重新设计，因为ProcessPoolExecutor的future无法直接await
        # 在实际实现中，可能需要使用不同的进程管理策略
        warning("wait_for_process is not fully implemented in current design")
        return None
    
    def terminate_process(self, process_id: int) -> bool:
        """
        终止指定进程
        
        Args:
            process_id: 进程ID
            
        Returns:
            是否成功终止
        """
        if process_id not in self._processes:
            return False
        
        process_info = self._processes[process_id]
        if process_info.state != ProcessState.RUNNING:
            return False
        
        # 标记进程为停止中
        process_info.state = ProcessState.STOPPING
        
        # 在ProcessPoolExecutor中，无法直接终止单个进程
        # 需要重新设计进程管理策略
        warning("terminate_process is limited in ProcessPoolExecutor design")
        
        process_info.state = ProcessState.STOPPED
        return True