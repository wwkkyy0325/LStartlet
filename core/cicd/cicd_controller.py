"""
CI/CD 控制器 - 管理整个持续集成和持续部署流程
"""

import os
import json
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

from core.logger import info, warning, error
from core.config import get_config, register_config
from core.path import get_project_root
from core.version_control import VersionController
from .pipeline import Pipeline
from .builder import Builder
from .tester import Tester
from .deployer import Deployer


if TYPE_CHECKING:
    from core.system.config_manager import SystemConfigManager
    from core.cicd.dependency_installer import DependencyInstaller


class CICDController:
    """CI/CD 控制器主类"""

    system_config_manager: Optional["SystemConfigManager"]
    dependency_installer: Optional["DependencyInstaller"]

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        self.version_controller = VersionController(self.project_root)
        self.builder = Builder(self.project_root)
        self.tester = Tester(self.project_root)
        self.deployer = Deployer(self.project_root)

        # 导入系统检测模块
        try:
            from core.system.config_manager import SystemConfigManager

            self.system_config_manager = SystemConfigManager(self.project_root)
        except ImportError as e:
            error(f"无法导入系统配置管理器: {e}")
            self.system_config_manager = None

        # 导入依赖安装模块
        try:
            from core.cicd.dependency_installer import DependencyInstaller

            self.dependency_installer = DependencyInstaller(self.project_root)
        except ImportError as e:
            error(f"无法导入依赖安装器: {e}")
            self.dependency_installer = None

        # 注册 CI/CD 相关配置
        register_config("cicd.pipeline.timeout", 3600, int, "流水线执行超时时间（秒）")
        register_config("cicd.build.output_dir", "./build", str, "构建输出目录")
        register_config(
            "cicd.test.report_dir", "./test_reports", str, "测试报告输出目录"
        )
        register_config("cicd.deploy.target_env", "staging", str, "部署目标环境")
        register_config("cicd.notify.on_failure", True, bool, "失败时是否发送通知")
        register_config("cicd.notify.on_success", False, bool, "成功时是否发送通知")
        register_config(
            "cicd.system.pre_deploy_detection", True, bool, "部署前是否进行系统检测"
        )
        register_config(
            "cicd.system.post_deploy_validation", True, bool, "部署后是否进行系统验证"
        )
        register_config(
            "cicd.dependencies.install_missing", True, bool, "是否自动安装缺失依赖"
        )

    def run_pipeline(
        self,
        pipeline: Pipeline,
        version_tag: Optional[str] = None,
        deploy_target: Optional[str] = None,
    ) -> bool:
        """
        运行完整的CI/CD流水线

        Args:
            pipeline: 流水线对象
            version_tag: 版本标签
            deploy_target: 部署目标环境

        Returns:
            是否执行成功
        """
        info(f"开始执行CI/CD流水线: {pipeline.name}")

        start_time = datetime.now()

        try:
            # 在部署前进行系统检测（如果启用）
            if (
                get_config("cicd.system.pre_deploy_detection", True)
                and deploy_target
                and self.system_config_manager
            ):
                info("执行部署前系统检测")
                if not self.system_config_manager.setup_optimal_config():
                    warning("系统配置设置存在问题，但仍继续部署")

            # 检查并安装缺失的依赖（如果启用）
            if (
                get_config("cicd.dependencies.install_missing", True)
                and self.dependency_installer
            ):
                info("检查并安装缺失的依赖")
                install_success = self._install_missing_dependencies()
                if not install_success:
                    warning("依赖安装失败，但仍继续部署")

            # 如果提供了版本标签，则创建标签
            if version_tag:
                success = self.version_controller.create_tag(
                    version_tag, f"Auto-build {version_tag}"
                )
                if not success:
                    error(f"创建版本标签失败: {version_tag}")
                    return False

            # 执行流水线中的各个阶段
            for stage in pipeline.stages:
                info(f"执行阶段: {stage.name}")

                for step in stage.steps:
                    info(f"执行步骤: {step.name}")

                    # 执行步骤
                    success = step.execute()
                    if not success:
                        error(f"步骤执行失败: {step.name}")
                        self._send_notification(
                            f"CI/CD流水线失败: {pipeline.name}", "failure"
                        )
                        return False

                    info(f"步骤完成: {step.name}")

                info(f"阶段完成: {stage.name}")

            # 如果需要部署，则执行部署
            if deploy_target:
                info(f"开始部署到: {deploy_target}")

                # 获取构建产物
                artifacts_paths = self.builder.get_build_artifacts()

                # 如果有多个构件，选择第一个或合并路径
                artifacts_path: Optional[str] = None
                if artifacts_paths:
                    # 对于部署，通常使用第一个构件或需要特殊处理
                    artifacts_path = artifacts_paths[0] if artifacts_paths else None

                deploy_success = self.deployer.deploy(
                    deploy_target,
                    artifacts_path,
                )

                if not deploy_success:
                    error(f"部署失败: {deploy_target}")
                    self._send_notification(f"部署失败: {pipeline.name}", "failure")
                    return False
                else:
                    info(f"部署成功: {deploy_target}")

                    # 部署后系统验证（如果启用）
                    if (
                        get_config("cicd.system.post_deploy_validation", True)
                        and self.system_config_manager
                    ):
                        info("执行部署后系统验证")
                        # 这里可以添加健康检查、功能验证等
                        self._post_deploy_validation(deploy_target)

                    self._send_notification(f"部署成功: {pipeline.name}", "success")
            else:
                info("跳过部署阶段")

            end_time = datetime.now()
            duration = end_time - start_time

            info(f"CI/CD流水线执行成功，耗时: {duration}")

            # 根据配置决定是否发送成功通知
            if get_config("cicd.notify.on_success", False):
                self._send_notification(f"CI/CD流水线成功: {pipeline.name}", "success")

            return True

        except Exception as e:
            error(f"CI/CD流水线执行异常: {e}")
            self._send_notification(f"CI/CD流水线失败: {pipeline.name}", "failure")
            return False

    def _install_missing_dependencies(self) -> bool:
        """检查并安装缺失的依赖"""
        try:
            # 检查并安装缺失的依赖
            if self.dependency_installer is not None:
                success = self.dependency_installer.check_and_install_missing()
                if success:
                    info("依赖安装完成")
                else:
                    error("依赖安装失败")
                return success
            else:
                warning("依赖安装器不可用，跳过依赖安装")
                return True
        except Exception as e:
            error(f"依赖安装过程中发生错误: {e}")
            return False

    def _post_deploy_validation(self, target_env: str) -> bool:
        """部署后系统验证"""
        try:
            # 这里可以添加各种验证逻辑
            # 例如：检查服务是否正常运行、执行基本功能测试等
            info(f"对 {target_env} 执行部署后验证")

            # 示例：检查目标目录是否存在
            # 可以扩展为更复杂的验证逻辑
            return True
        except Exception as e:
            error(f"部署后验证失败: {e}")
            return False

    def _should_fail_on_dl_issues(self, issues: List[str]) -> bool:
        """根据问题严重性判断是否应该终止流水线"""
        critical_issues = [
            "可用内存不足",
            "PyTorch 未正确链接 CUDA",
            "CUDA 不可用",  # 取决于项目是否需要GPU
        ]

        for issue in issues:
            for critical in critical_issues:
                if critical in issue:
                    return True
        return False

    def run_build(self, build_targets: Optional[List[str]] = None) -> bool:
        """
        仅运行构建阶段

        Args:
            build_targets: 构建目标列表

        Returns:
            是否构建成功
        """
        info("开始执行构建阶段")
        return self.builder.build(build_targets)

    def run_tests(self, test_suite: Optional[str] = None) -> Dict[str, Any]:
        """
        仅运行测试阶段

        Args:
            test_suite: 测试套件名称

        Returns:
            测试结果
        """
        info("开始执行测试阶段")
        return self.tester.run_tests(test_suite)

    def run_deploy(self, target: str, artifacts_path: Optional[str] = None) -> bool:
        """
        仅运行部署阶段

        Args:
            target: 部署目标
            artifacts_path: 构件路径

        Returns:
            是否部署成功
        """
        info(f"开始部署到: {target}")
        return self.deployer.deploy(target, artifacts_path)

    def _send_notification(self, message: str, status: str) -> None:
        """
        发送通知

        Args:
            message: 通知消息
            status: 状态 ('success' 或 'failure')
        """
        notify_enabled = (
            get_config("cicd.notify.on_failure", True)
            if status == "failure"
            else get_config("cicd.notify.on_success", False)
        )

        if not notify_enabled:
            return

        # 这里可以扩展为发送邮件、Slack消息或其他通知方式
        info(f"发送通知: {message}, 状态: {status}")

        # TODO: 实现具体的通知发送逻辑（如邮件、Webhook等）
        pass

    def generate_pipeline_report(
        self, pipeline: Pipeline, results: Dict[str, Any]
    ) -> str:
        """
        生成流水线执行报告

        Args:
            pipeline: 流水线对象
            results: 执行结果

        Returns:
            报告路径
        """
        report_data: Dict[str, Any] = {
            "pipeline_name": pipeline.name,
            "executed_at": datetime.now().isoformat(),
            "results": results,
            "stages": [],
        }

        # 如果系统配置管理器可用，添加系统信息
        if self.system_config_manager:
            try:
                system_info = (
                    self.system_config_manager.system_detector.detect_system_info()
                )
                report_data["system_info"] = system_info
            except Exception as e:
                error(f"获取系统信息失败: {e}")

        # 如果依赖安装器可用，添加依赖信息
        if self.dependency_installer:
            try:
                from core.version_control.dependency_resolver import DependencyResolver

                resolver = DependencyResolver(self.project_root)
                deps = resolver.analyze_dependencies()
                report_data["dependencies"] = deps
            except Exception as e:
                error(f"获取依赖信息失败: {e}")

        for stage in pipeline.stages:
            stage_data: Dict[str, Any] = {"name": stage.name, "steps": []}

            for step in stage.steps:
                step_data: Dict[str, Any] = {
                    "name": step.name,
                    "status": step.status,
                    "duration": step.duration,
                    "details": step.details,
                }
                stage_data["steps"].append(step_data)

            report_data["stages"].append(stage_data)

        # 确定报告输出路径
        report_dir = get_config("cicd.test.report_dir", "./test_reports")
        os.makedirs(report_dir, exist_ok=True)

        report_filename = f"cicd_report_{pipeline.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(report_dir, report_filename)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        info(f"流水线报告已生成: {report_path}")
        return report_path
