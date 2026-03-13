"""
调度系统进程管理器
负责工作进程的创建、管理和监控
"""

import multiprocessing as mp
from typing import Dict, Any
# 使用项目自定义日志管理器
from core.logger import info, warning


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
    
    def start(self) -> None:
        """启动进程管理器"""
        if self._active_count > 0:
            warning("Process manager is already running")
            return
        
        # 启动工作进程（简化实现，不使用队列）
        for i in range(self.max_processes):
            worker_id = f"worker_{i}"
            # 创建一个简单的进程（实际项目中应该有更复杂的逻辑）
            process = mp.Process(
                target=self._dummy_worker,
                args=(worker_id,),
                daemon=True
            )
            
            self._processes[worker_id] = process
            process.start()
            self._active_count += 1
        
        info(f"Process manager started with {self.max_processes} workers")
    
    @staticmethod
    def _dummy_worker(worker_id: str) -> None:
        """简单的工作者函数（静态方法避免pickle问题）"""
        # 避免在子进程中使用复杂的日志系统
        print(f"Dummy worker {worker_id} started and finished")
    
    def stop(self) -> None:
        """停止进程管理器"""
        if self._active_count == 0:
            return
        
        # 停止所有工作进程
        for process in self._processes.values():
            if process.is_alive():
                process.terminate()
                process.join(timeout=self.process_timeout)
                if process.is_alive():
                    process.kill()
        
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
        # 这里简化实现
        return True
    
    def get_all_processes_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有进程的状态"""
        status_dict: Dict[str, Dict[str, Any]] = {}
        for worker_id, process in self._processes.items():
            status_dict[worker_id] = {
                'worker_id': worker_id,
                'is_alive': process.is_alive(),
                'status': 'running' if process.is_alive() else 'stopped'
            }
        return status_dict