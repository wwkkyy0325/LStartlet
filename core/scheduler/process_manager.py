"""
调度系统进程管理器
负责工作进程的创建、管理和监控
"""

import multiprocessing as mp
import os
import time
from typing import Dict, Any
# 使用项目自定义日志管理器
from core.logger import info, warning, error
from core.event.event_bus import EventBus
from core.event.events.scheduler_events import ProcessCreatedEvent, ProcessStartedEvent, ProcessStoppedEvent
from core.process import GlobalProcessManager


class ProcessManager:
    """进程管理器"""
    
    def __init__(self, max_processes: int = 4, process_timeout: float = 30.0):
        """
        初始化进程管理器
        
        Args:
            max_processes: 最大进程数
            process_timeout: 进程超时时间（秒）
        """
        self.max_processes = max_processes
        self.process_timeout = process_timeout
        self._processes: Dict[str, mp.Process] = {}
        self._active_count = 0
        # 获取事件总线实例
        self._event_bus = EventBus()
    
    def start(self) -> None:
        """启动进程管理器"""
        if self._active_count > 0:
            warning("Process manager is already running")
            return
        
        # 启动工作进程
        for i in range(self.max_processes):
            worker_id = f"worker_{i}"
            process = mp.Process(
                target=self._worker_process,
                args=(worker_id, i),
                daemon=True
            )
            
            self._processes[worker_id] = process
            
            # 发布进程创建事件
            process_data: Dict[str, Any] = {
                "worker_id": worker_id,
                "process_index": i,
                "max_processes": self.max_processes,
                "process_timeout": self.process_timeout
            }
            self._event_bus.publish(ProcessCreatedEvent(i, process_data))
            
            process.start()
            self._active_count += 1
            
            # 注册到全局进程管理器（确保pid不为None）
            if process.pid is not None:
                GlobalProcessManager().register_process(
                    pid=process.pid,
                    process_type="worker",
                    description=f"工作进程 {worker_id}",
                    callback=self._on_worker_process_terminated
                )
            else:
                warning(f"工作进程 {worker_id} 的PID为None，无法注册到全局进程管理器")
        
        info(f"Process manager started with {self.max_processes} workers")
    
    def _worker_process(self, worker_id: str, process_id: int) -> None:
        """工作进程函数"""
        try:
            info(f"Worker {worker_id} started with PID: {os.getpid()}")
            
            # 发布进程启动事件
            process_data: Dict[str, Any] = {
                "worker_id": worker_id,
                "start_time": time.time(),
                "max_processes": self.max_processes,
                "process_timeout": self.process_timeout
            }
            self._event_bus.publish(ProcessStartedEvent(process_id, process_data))
            
            # 工作进程主循环（简化实现）
            while True:
                # 实际应用中这里应该有任务处理逻辑
                time.sleep(1)
                
        except KeyboardInterrupt:
            info(f"Worker {worker_id} received interrupt signal")
        except Exception as e:
            error(f"Error in worker {worker_id}: {e}")
        finally:
            info(f"Worker {worker_id} stopped")
            
            # 发布进程停止事件
            process_data: Dict[str, Any] = {
                "worker_id": worker_id,
                "stop_time": time.time()
            }
            self._event_bus.publish(ProcessStoppedEvent(process_id, process_data=process_data))
    
    def _on_worker_process_terminated(self, pid: int, process_type: str) -> None:
        """工作进程终止回调"""
        info(f"检测到工作进程 {pid} 已终止")
        # 这里可以添加重新启动进程或其他清理逻辑
    
    def stop(self) -> None:
        """停止进程管理器"""
        if self._active_count == 0:
            return
        
        # 停止所有工作进程
        for process in self._processes.values():
            if process.is_alive():
                # 先尝试正常终止
                process.terminate()
                process.join(timeout=self.process_timeout)
                if process.is_alive():
                    # 强制终止
                    process.kill()
                
                # 从全局进程管理器中注销（确保pid不为None）
                if process.pid is not None:
                    GlobalProcessManager().terminate_process(process.pid, force=True)
        
        self._processes.clear()
        self._active_count = 0
        
        info("Process manager stopped successfully")
    
    def get_active_process_count(self) -> int:
        """获取活跃进程数量"""
        return self._active_count
    
    def submit_task(self, task_data: Any) -> bool:
        """
        提交任务到进程池
        
        Args:
            task_data: 任务数据
            
        Returns:
            是否成功提交
        """
        # 这里简化实现，实际应该有更复杂的任务分发逻辑
        return True
    
    def get_all_processes_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有进程的状态"""
        status_dict: Dict[str, Dict[str, Any]] = {}
        for worker_id, process in self._processes.items():
            status_dict[worker_id] = {
                'worker_id': worker_id,
                'is_alive': process.is_alive(),
                'status': 'running' if process.is_alive() else 'stopped',
                'pid': process.pid if process.pid else None
            }
        return status_dict