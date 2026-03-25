"""
CI/CD 流水线定义 - 包括阶段、步骤等概念
"""

from typing import List, Callable, Any, Optional, Dict
from datetime import datetime
import time


class Step:
    """流水线步骤"""
    
    def __init__(self, name: str, execute_func: Callable[[], Any], description: str = ""):
        self.name = name
        self.description = description
        self.execute_func = execute_func
        self.status = "pending"  # pending, running, success, failure
        self.duration = 0
        self.details = ""
    
    def execute(self) -> bool:
        """执行步骤"""
        start_time = time.time()
        self.status = "running"
        
        try:
            result = self.execute_func()
            self.status = "success" if result or result is None else "failure"
            self.duration = time.time() - start_time
            self.details = "执行成功" if result or result is None else "执行返回失败值"
            return True
        except Exception as e:
            self.status = "failure"
            self.duration = time.time() - start_time
            self.details = f"执行异常: {str(e)}"
            return False


class Stage:
    """流水线阶段"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: List[Step] = []
    
    def add_step(self, step: Step) -> None:
        """添加步骤到阶段"""
        self.steps.append(step)
    
    def add_steps(self, steps: List[Step]) -> None:
        """批量添加步骤"""
        self.steps.extend(steps)


class Pipeline:
    """CI/CD 流水线"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.stages: List[Stage] = []
        self.created_at = datetime.now()
    
    def add_stage(self, stage: Stage) -> None:
        """添加阶段到流水线"""
        self.stages.append(stage)
    
    def add_stages(self, stages: List[Stage]) -> None:
        """批量添加阶段"""
        self.stages.extend(stages)
    
    def get_step_by_name(self, step_name: str) -> Optional[Step]:
        """根据名称获取步骤"""
        for stage in self.stages:
            for step in stage.steps:
                if step.name == step_name:
                    return step
        return None
    
    def get_stage_by_name(self, stage_name: str) -> Optional[Stage]:
        """根据名称获取阶段"""
        for stage in self.stages:
            if stage.name == stage_name:
                return stage
        return None
    
    def get_total_duration(self) -> float:
        """获取流水线总耗时"""
        total = 0
        for stage in self.stages:
            for step in stage.steps:
                total += step.duration
        return total
    
    def get_status_summary(self) -> Dict[str, int]:
        """获取状态摘要"""
        summary: Dict[str, int] = {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "pending_steps": 0,
            "running_steps": 0
        }
        
        for stage in self.stages:
            for step in stage.steps:
                summary["total_steps"] += 1
                if step.status == "success":
                    summary["successful_steps"] += 1
                elif step.status == "failure":
                    summary["failed_steps"] += 1
                elif step.status == "pending":
                    summary["pending_steps"] += 1
                elif step.status == "running":
                    summary["running_steps"] += 1
        
        return summary