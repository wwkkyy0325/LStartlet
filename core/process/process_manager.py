"""
全局进程管理器
负责管理所有独立进程的PID，提供启动、查询、关闭和清理功能
"""

import os
import signal
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
# 使用项目自定义日志管理器
from core.logger import info, warning, error


@dataclass
class ProcessInfo:
    """进程信息数据类"""
    pid: int
    process_type: str  # 如 "main", "renderer", "worker", "extension" 等
    start_time: datetime
    description: str = ""
    callback: Optional[Callable[[int, str], None]] = None
    is_active: bool = True


class GlobalProcessManager:
    """全局进程管理器单例类"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """初始化进程管理器"""
        self._processes: Dict[int, ProcessInfo] = {}
        self._process_lock = threading.RLock()
        self._cleanup_registered = False
        
        # 注册程序退出时的清理函数
        self._register_cleanup()
        
        # Record main process
        main_pid = os.getpid()
        self.register_process(
            pid=main_pid,
            process_type="main",
            description="Main application process"
        )
        info(f"Main process registered, PID: {main_pid}")
    
    def _register_cleanup(self) -> None:
        """注册清理函数"""
        if not self._cleanup_registered:
            import atexit
            atexit.register(self.cleanup_all_processes)
            self._cleanup_registered = True
    
    def register_process(
        self,
        pid: int,
        process_type: str,
        description: str = "",
        callback: Optional[Callable[[int, str], None]] = None
    ) -> None:
        """
        Register new process
        
        Args:
            pid: Process ID
            process_type: Process type
            description: Process description
            callback: Callback function after process shutdown
        """
        with self._process_lock:
            if pid in self._processes:
                warning(f"Process {pid} already exists, updating information")
            
            process_info = ProcessInfo(
                pid=pid,
                process_type=process_type,
                start_time=datetime.now(),
                description=description,
                callback=callback,
                is_active=True
            )
            self._processes[pid] = process_info
            info(f"Process registered - PID: {pid}, Type: {process_type}, Description: {description}")
    
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """
        获取指定进程的信息
        
        Args:
            pid: 进程ID
            
        Returns:
            进程信息，如果不存在则返回None
        """
        with self._process_lock:
            return self._processes.get(pid)
    
    def get_processes_by_type(self, process_type: str) -> List[ProcessInfo]:
        """
        获取指定类型的进程列表
        
        Args:
            process_type: 进程类型
            
        Returns:
            进程信息列表
        """
        with self._process_lock:
            return [
                info for info in self._processes.values()
                if info.process_type == process_type and info.is_active
            ]
    
    def get_all_processes(self) -> List[ProcessInfo]:
        """获取所有活跃进程的信息"""
        with self._process_lock:
            return [
                info for info in self._processes.values()
                if info.is_active
            ]
    
    def is_process_active(self, pid: int) -> bool:
        """
        检查进程是否仍然活跃
        
        Args:
            pid: 进程ID
            
        Returns:
            进程是否活跃
        """
        try:
            # 在Windows上，os.kill(pid, 0) 会检查进程是否存在
            os.kill(pid, 0)
            return True
        except OSError:
            # 进程不存在
            with self._process_lock:
                if pid in self._processes:
                    self._processes[pid].is_active = False
            return False
    
    def _get_terminate_signal(self, force: bool = False) -> int:
        """
        获取适合当前平台的终止信号
        
        Args:
            force: 是否强制终止
            
        Returns:
            信号值
        """
        if force:
            # 强制终止优先级：SIGTERM -> SIGKILL -> SIGBREAK -> SIGTERM
            if hasattr(signal, 'SIGTERM'):
                return getattr(signal, 'SIGTERM')
            elif hasattr(signal, 'SIGKILL'):
                return getattr(signal, 'SIGKILL')
            elif hasattr(signal, 'SIGBREAK'):
                return getattr(signal, 'SIGBREAK')
            else:
                # 默认返回SIGTERM的值（15）
                return 15
        else:
            # 正常终止优先级：SIGTERM -> SIGBREAK -> SIGTERM
            if hasattr(signal, 'SIGTERM'):
                return getattr(signal, 'SIGTERM')
            elif hasattr(signal, 'SIGBREAK'):
                return getattr(signal, 'SIGBREAK')
            else:
                # 默认返回SIGTERM的值（15）
                return 15
    
    def terminate_process(
        self,
        pid: int,
        force: bool = False,
        timeout: float = 5.0
    ) -> bool:
        """
        终止指定进程
        
        Args:
            pid: 进程ID
            force: 是否强制终止
            timeout: 等待超时时间（秒）
            
        Returns:
            是否成功终止
        """
        with self._process_lock:
            if pid not in self._processes:
                warning(f"尝试终止未注册的进程 {pid}")
                return False
            
            process_info = self._processes[pid]
            if not process_info.is_active:
                info(f"进程 {pid} 已经不活跃")
                return True
        
        # 检查进程是否还存在
        if not self.is_process_active(pid):
            info(f"进程 {pid} 已经退出")
            self._unregister_process(pid)
            return True
        
        try:
            # 获取终止信号
            sig = self._get_terminate_signal(force)
            os.kill(pid, sig)
            action = "强制" if force else "正常"
            info(f"已发送{action}终止信号到进程 {pid}")
            
            # 等待进程退出
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.is_process_active(pid):
                    break
                time.sleep(0.1)
            
            # 如果进程仍然活跃，强制终止
            if self.is_process_active(pid):
                if force:
                    warning(f"进程 {pid} 无法在 {timeout} 秒内终止")
                    return False
                else:
                    info(f"进程 {pid} 未在 {timeout} 秒内退出，尝试强制终止")
                    return self.terminate_process(pid, force=True, timeout=timeout)
            
            # 执行回调
            if process_info.callback:
                try:
                    process_info.callback(pid, process_info.process_type)
                except Exception as e:
                    error(f"进程 {pid} 回调执行失败: {e}")
            
            # 注销进程
            self._unregister_process(pid)
            info(f"进程 {pid} 已成功终止并注销")
            return True
            
        except OSError as e:
            error(f"终止进程 {pid} 失败: {e}")
            # 如果是因为进程不存在，也认为是成功的
            if e.errno == 3:  # No such process
                self._unregister_process(pid)
                return True
            return False
        except Exception as e:
            error(f"终止进程 {pid} 时发生未知错误: {e}")
            return False
    
    def _unregister_process(self, pid: int) -> None:
        """
        内部方法：注销进程
        
        Args:
            pid: 进程ID
        """
        with self._process_lock:
            if pid in self._processes:
                del self._processes[pid]
                info(f"进程 {pid} 已从管理器中注销")
    
    def terminate_processes_by_type(
        self,
        process_type: str,
        force: bool = False,
        timeout: float = 5.0
    ) -> Dict[int, bool]:
        """
        终止指定类型的所有进程
        
        Args:
            process_type: 进程类型
            force: 是否强制终止
            timeout: 等待超时时间（秒）
            
        Returns:
            {pid: success} 的字典
        """
        processes = self.get_processes_by_type(process_type)
        results: Dict[int, bool] = {}
        
        for process_info in processes:
            success = self.terminate_process(process_info.pid, force, timeout)
            results[process_info.pid] = success
        
        return results
    
    def cleanup_all_processes(self) -> None:
        """清理所有进程（程序退出时调用）"""
        info("开始清理所有注册的进程...")
        
        # 获取所有进程的PID副本
        with self._process_lock:
            pids = list(self._processes.keys())
        
        for pid in pids:
            try:
                # 不强制终止，给进程正常退出的机会
                self.terminate_process(pid, force=False, timeout=2.0)
            except Exception as e:
                error(f"清理进程 {pid} 时出错: {e}")
        
        info("所有进程清理完成")
    
    def get_process_count(self) -> int:
        """获取活跃进程数量"""
        return len(self.get_all_processes())
    
    def print_process_status(self) -> Dict[str, Any]:
        """打印所有进程的状态（用于调试），返回状态字典"""
        processes = self.get_all_processes()
        info(f"当前活跃进程数量: {len(processes)}")
        status_dict: Dict[str, Any] = {
            "total_processes": len(processes),
            "processes": []
        }
        for proc in processes:
            status = "活跃" if self.is_process_active(proc.pid) else "不活跃"
            proc_info: Dict[str, Any] = {
                "pid": proc.pid,
                "type": proc.process_type,
                "status": status,
                "start_time": proc.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "description": proc.description
            }
            status_dict["processes"].append(proc_info)
            info(f"  PID: {proc.pid}, 类型: {proc.process_type}, 状态: {status}, "
                 f"启动时间: {proc.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return status_dict