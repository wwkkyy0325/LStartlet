#!/usr/bin/env python3
"""
CICD Pipeline Unit Tests
Test the Pipeline, Stage, and Step classes functionality
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cicd.pipeline import Pipeline, Stage, Step


class TestStep(unittest.TestCase):
    """测试 Step 类"""
    
    def test_step_initialization(self):
        """测试步骤初始化"""
        def test_action():
            return True
        
        step = Step("test_step", test_action)
        
        self.assertEqual(step.name, "test_step")
        self.assertEqual(step.execute_func, test_action)
        self.assertEqual(step.status, "pending")
    
    def test_step_execute_success_true(self):
        """测试步骤执行成功（返回 True）"""
        def success_action():
            return True
        
        step = Step("success_step", success_action)
        result = step.execute()
        
        self.assertTrue(result)  # execute() 成功执行返回 True
        self.assertEqual(step.status, "success")
    
    def test_step_execute_success_none(self):
        """测试步骤执行成功（返回 None）"""
        def success_action():
            return None
        
        step = Step("success_step", success_action)
        result = step.execute()
        
        self.assertTrue(result)  # execute() 成功执行返回 True
        self.assertEqual(step.status, "success")
    
    def test_step_execute_failure_return_false(self):
        """测试步骤执行失败（返回 False）"""
        def failure_action():
            return False
        
        step = Step("failure_step", failure_action)
        result = step.execute()
        
        self.assertTrue(result)  # execute() 成功执行（即使函数返回 False）仍然返回 True
        self.assertEqual(step.status, "failure")  # 但状态为 failure
    
    def test_step_execute_exception(self):
        """测试步骤执行异常"""
        def exception_action():
            raise ValueError("Test exception")
        
        step = Step("exception_step", exception_action)
        result = step.execute()
        
        self.assertFalse(result)  # execute() 在异常时返回 False
        self.assertEqual(step.status, "failure")


class TestStage(unittest.TestCase):
    """测试 Stage 类"""
    
    def test_stage_initialization(self):
        """测试阶段初始化"""
        stage = Stage("test_stage")
        
        self.assertEqual(stage.name, "test_stage")
        self.assertEqual(len(stage.steps), 0)
    
    def test_stage_add_step(self):
        """测试添加单个步骤"""
        def step1_action():
            return True
        
        step1 = Step("step1", step1_action)
        stage = Stage("test_stage")
        stage.add_step(step1)
        
        self.assertEqual(len(stage.steps), 1)
        self.assertEqual(stage.steps[0], step1)
    
    def test_stage_add_steps(self):
        """测试批量添加步骤"""
        def step1_action():
            return True
        
        def step2_action():
            return True
        
        step1 = Step("step1", step1_action)
        step2 = Step("step2", step2_action)
        stage = Stage("test_stage")
        stage.add_steps([step1, step2])
        
        self.assertEqual(len(stage.steps), 2)
        self.assertEqual(stage.steps[0], step1)
        self.assertEqual(stage.steps[1], step2)


class TestPipeline(unittest.TestCase):
    """测试 Pipeline 类"""
    
    def test_pipeline_initialization(self):
        """测试流水线初始化"""
        pipeline = Pipeline("test_pipeline")
        
        self.assertEqual(pipeline.name, "test_pipeline")
        self.assertEqual(len(pipeline.stages), 0)
    
    def test_pipeline_add_stage(self):
        """测试添加单个阶段"""
        stage = Stage("stage1")
        pipeline = Pipeline("test_pipeline")
        pipeline.add_stage(stage)
        
        self.assertEqual(len(pipeline.stages), 1)
        self.assertEqual(pipeline.stages[0], stage)
    
    def test_pipeline_add_stages(self):
        """测试批量添加阶段"""
        stage1 = Stage("stage1")
        stage2 = Stage("stage2")
        pipeline = Pipeline("test_pipeline")
        pipeline.add_stages([stage1, stage2])
        
        self.assertEqual(len(pipeline.stages), 2)
        self.assertEqual(pipeline.stages[0], stage1)
        self.assertEqual(pipeline.stages[1], stage2)
    
    def test_pipeline_get_step_by_name(self):
        """测试根据名称获取步骤"""
        def step1_action():
            return True
        
        step1 = Step("target_step", step1_action)
        stage = Stage("stage1")
        stage.add_step(step1)
        pipeline = Pipeline("test_pipeline")
        pipeline.add_stage(stage)
        
        found_step = pipeline.get_step_by_name("target_step")
        self.assertEqual(found_step, step1)
        
        not_found_step = pipeline.get_step_by_name("non_existent")
        self.assertIsNone(not_found_step)
    
    def test_pipeline_get_stage_by_name(self):
        """测试根据名称获取阶段"""
        stage = Stage("target_stage")
        pipeline = Pipeline("test_pipeline")
        pipeline.add_stage(stage)
        
        found_stage = pipeline.get_stage_by_name("target_stage")
        self.assertEqual(found_stage, stage)
        
        not_found_stage = pipeline.get_stage_by_name("non_existent")
        self.assertIsNone(not_found_stage)
    
    def test_pipeline_get_status_summary(self):
        """测试获取状态摘要"""
        def step1_action():
            return True
        
        def step2_action():
            return False
        
        step1 = Step("step1", step1_action)
        step2 = Step("step2", step2_action)
        stage = Stage("stage1")
        stage.add_steps([step1, step2])
        pipeline = Pipeline("test_pipeline")
        pipeline.add_stage(stage)
        
        # 执行步骤
        step1.execute()
        step2.execute()
        
        summary = pipeline.get_status_summary()
        self.assertEqual(summary["total_steps"], 2)
        self.assertEqual(summary["successful_steps"], 1)
        self.assertEqual(summary["failed_steps"], 1)
        self.assertEqual(summary["pending_steps"], 0)
        self.assertEqual(summary["running_steps"], 0)


if __name__ == '__main__':
    unittest.main()