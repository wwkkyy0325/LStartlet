"""
测试器 - 负责运行各种测试（单元测试、集成测试等）
"""

import os
import subprocess
import unittest
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.logger import info, warning, error
from core.config import get_config
from core.path import get_project_root


class Tester:
    """测试器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        self.report_dir = get_config("cicd.test.report_dir", "./test_reports")

    def run_tests(self, test_suite: Optional[str] = None) -> Dict[str, Any]:
        """
        运行测试

        Args:
            test_suite: 测试套件名称或路径

        Returns:
            测试结果
        """
        info("开始运行测试")

        if test_suite is None:
            # 默认运行所有测试
            test_suite = "tests"

        # 确保报告目录存在
        os.makedirs(self.report_dir, exist_ok=True)

        # 根据测试套件类型选择执行方式
        if os.path.isdir(os.path.join(self.project_root, test_suite)):
            # 如果是目录，运行目录下的所有测试
            return self._run_test_directory(test_suite)
        elif test_suite.endswith(".py"):
            # 如果是Python文件，运行该文件中的测试
            return self._run_test_file(test_suite)
        else:
            # 默认运行tests目录下的所有测试
            return self._run_test_directory("tests")

    def _run_test_directory(self, test_dir: str) -> Dict[str, Any]:
        """运行目录中的测试"""
        info(f"运行测试目录: {test_dir}")

        try:
            # 使用unittest模块发现并运行测试
            loader = unittest.TestLoader()
            suite = loader.discover(
                os.path.join(self.project_root, test_dir),
                pattern="test*.py",
                top_level_dir=self.project_root,
            )

            # 运行测试并生成报告
            start_time = datetime.now()
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            end_time = datetime.now()

            # 计算通过的测试数量（成功 = 总数 - 失败 - 错误 - 跳过）
            passed_tests = (
                result.testsRun
                - len(result.failures)
                - len(result.errors)
                - len(result.skipped)
            )

            # 生成测试报告
            report_data: Dict[str, Any] = {
                "suite": test_dir,
                "ran_at": start_time.isoformat(),
                "duration": (end_time - start_time).total_seconds(),
                "total_tests": result.testsRun,
                "passed": passed_tests,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped),
                "failures_details": [],
                "errors_details": [],
            }

            # 添加失败详情
            for test, trace in result.failures:
                report_data["failures_details"].append(
                    {"test": str(test), "traceback": trace}
                )

            # 添加错误详情
            for test, trace in result.errors:
                report_data["errors_details"].append(
                    {"test": str(test), "traceback": trace}
                )

            # 保存报告
            self._save_test_report(
                report_data,
                f"test_report_{test_dir}_{start_time.strftime('%Y%m%d_%H%M%S')}.json",
            )

            # 生成JUnit格式报告
            self._generate_junit_report(result, test_dir, start_time)

            info(
                f"测试完成: {report_data['total_tests']} 个测试, "
                f"{report_data['passed']} 个通过, "
                f"{report_data['failures']} 个失败, "
                f"{report_data['errors']} 个错误"
            )

            return report_data

        except Exception as e:
            error(f"运行测试目录时出错: {e}")
            return {
                "suite": test_dir,
                "ran_at": datetime.now().isoformat(),
                "error": str(e),
                "total_tests": 0,
                "passed": 0,
                "failures": 0,
                "errors": 1,
                "skipped": 0,
            }

    def _run_test_file(self, test_file: str) -> Dict[str, Any]:
        """运行测试文件"""
        info(f"运行测试文件: {test_file}")

        try:
            # 使用subprocess运行测试文件，以避免导入问题
            test_file_path = os.path.join(self.project_root, test_file)
            result = subprocess.run(
                ["python", test_file_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            # 解析输出结果
            report_data = {
                "suite": test_file,
                "ran_at": datetime.now().isoformat(),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

            # 保存报告
            start_time = datetime.now()
            self._save_test_report(
                report_data,
                f"test_report_{os.path.basename(test_file).replace('.py', '')}_{start_time.strftime('%Y%m%d_%H%M%S')}.json",
            )

            return report_data

        except Exception as e:
            error(f"运行测试文件时出错: {e}")
            return {
                "suite": test_file,
                "ran_at": datetime.now().isoformat(),
                "error": str(e),
                "return_code": -1,
            }

    def _save_test_report(self, report_data: Dict[str, Any], filename: str) -> str:
        """保存测试报告"""
        report_path = os.path.join(self.report_dir, filename)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        info(f"测试报告已保存: {report_path}")
        return report_path

    def _generate_junit_report(
        self, test_result: unittest.TestResult, test_suite: str, start_time: datetime
    ) -> str:
        """生成JUnit格式的测试报告"""
        try:
            # 创建根元素
            root = ET.Element("testsuite")
            root.set("name", test_suite)
            root.set("tests", str(test_result.testsRun))
            root.set("failures", str(len(test_result.failures)))
            root.set("errors", str(len(test_result.errors)))
            root.set("skipped", str(len(test_result.skipped)))
            root.set("timestamp", start_time.isoformat())

            # 添加成功的测试用例
            # 注意：unittest.TestResult 在标准库中没有 successes 属性
            # 我们需要通过其他方式确定成功的测试
            all_tests: List[str] = []

            # 收集所有失败和错误的测试
            failed_or_errored_tests = set()
            for test, _ in test_result.failures + test_result.errors:
                failed_or_errored_tests.add(str(test))

            # 由于我们无法直接获取成功的测试列表，这里跳过添加成功的测试用例
            # JUnit 报告主要关注失败和错误的测试

            for test, trace in test_result.failures:
                testcase = ET.SubElement(root, "testcase")
                testcase.set("name", str(test))
                testcase.set("classname", str(test.__class__.__name__))
                failure = ET.SubElement(testcase, "failure")
                failure.text = trace

            for test, trace in test_result.errors:
                testcase = ET.SubElement(root, "testcase")
                testcase.set("name", str(test))
                testcase.set("classname", str(test.__class__.__name__))
                error_elem = ET.SubElement(testcase, "error")
                error_elem.text = trace

            for test, _ in test_result.skipped:
                testcase = ET.SubElement(root, "testcase")
                testcase.set("name", str(test))
                testcase.set("classname", str(test.__class__.__name__))
                skipped = ET.SubElement(testcase, "skipped")

            # 生成XML字符串
            return ET.tostring(root, encoding="unicode")
        except Exception as e:
            error(f"生成JUnit报告时出错: {e}")
            # 返回简单的错误报告
            root = ET.Element("testsuite")
            root.set("name", test_suite or "unknown")
            root.set("tests", "0")
            root.set("failures", "1")
            root.set("errors", "0")
            root.set("skipped", "0")
            root.set("timestamp", datetime.now().isoformat())
            
            testcase = ET.SubElement(root, "testcase")
            testcase.set("name", "report_generation")
            testcase.set("classname", "Tester")
            failure = ET.SubElement(testcase, "failure")
            failure.text = f"Report generation failed: {str(e)}"
            
            return ET.tostring(root, encoding="unicode")

    def run_performance_tests(
        self, test_targets: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """运行性能测试"""
        info("开始运行性能测试")

        if test_targets is None:
            test_targets = ["tests/test_performance.py"]

        results: Dict[str, Any] = {
            "performance_tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0},
        }

        for target in test_targets:
            try:
                # 运行性能测试
                proc_result = subprocess.run(
                    ["python", target],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

                perf_result: Dict[str, Any] = {
                    "target": target,
                    "return_code": proc_result.returncode,
                    "stdout": proc_result.stdout,
                    "stderr": proc_result.stderr,
                }

                results["performance_tests"].append(perf_result)
                results["summary"]["total"] += 1

                if proc_result.returncode == 0:
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1

            except Exception as e:
                error(f"运行性能测试时出错 {target}: {e}")
                results["summary"]["failed"] += 1

        info(
            f"性能测试完成: {results['summary']['passed']} 通过, {results['summary']['failed']} 失败"
        )
        return results

    def run_security_scan(self) -> Dict[str, Any]:
        """运行安全扫描"""
        info("开始运行安全扫描")

        try:
            # 检查是否安装了bandit
            import importlib.util

            if importlib.util.find_spec("bandit") is None:
                warning("未安装bandit，跳过安全扫描。请安装: pip install bandit")
                return {"skipped": True, "reason": "bandit not installed"}

            # 运行安全扫描
            result = subprocess.run(
                [
                    "bandit",
                    "-r",
                    self.project_root,
                    "-f",
                    "json",
                    "-o",
                    "/tmp/bandit_results.json",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            # 读取结果
            import json as js

            with open("/tmp/bandit_results.json", "r") as f:
                scan_results = js.load(f)

            # 清理临时文件
            os.remove("/tmp/bandit_results.json")

            security_report = {
                "ran_at": datetime.now().isoformat(),
                "issues_found": scan_results.get("metrics", {})
                .get("_totals", {})
                .get("SEVERITY.HIGH", 0),
                "details": scan_results,
            }

            # 保存安全扫描报告
            report_path = os.path.join(
                self.report_dir,
                f"security_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(security_report, f, indent=2, ensure_ascii=False)

            info(f"安全扫描完成，发现 {security_report['issues_found']} 个严重问题")
            return security_report

        except Exception as e:
            error(f"运行安全扫描时出错: {e}")
            return {"error": str(e)}
