"""
部署器 - 负责将构建产物部署到目标环境
"""

import os
import shutil
import subprocess
import yaml
from typing import Dict, Any, Optional, List, cast
from datetime import datetime

from LStartlet.core.logger import info, warning, error
from LStartlet.core.config import get_config
from LStartlet.core.path import get_project_root


class Deployer:
    """部署器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        self.deployment_history: List[Dict[str, Any]] = []

    def deploy(self, target_env: str, artifacts_path: Optional[str] = None) -> bool:
        """
        执行部署

        Args:
            target_env: 目标环境 (dev, staging, prod)
            artifacts_path: 构件路径

        Returns:
            是否部署成功
        """
        info(f"开始部署到环境: {target_env}")

        try:
            # 根据目标环境确定部署配置
            deployment_config = self._get_deployment_config(target_env)
            if not deployment_config:
                error(f"未找到环境 {target_env} 的部署配置")
                return False

            # 确定要部署的构件
            if not artifacts_path:
                # 如果没有指定构件路径，尝试使用最近的构建产物
                artifacts_path = self._get_latest_artifact()

            if not artifacts_path:
                error("未找到要部署的构件")
                return False

            # 执行部署
            success = self._execute_deployment(
                target_env, artifacts_path, deployment_config
            )

            if success:
                # 记录部署历史
                self._record_deployment(target_env, artifacts_path, success)
                info(f"部署到 {target_env} 成功")
            else:
                self._record_deployment(target_env, artifacts_path, success)
                error(f"部署到 {target_env} 失败")

            return success

        except Exception as e:
            error(f"部署过程中发生异常: {e}")
            return False

    def rollback(self, target_env: str, version: Optional[str] = None) -> bool:
        """
        回滚部署

        Args:
            target_env: 目标环境
            version: 版本号，如果为None则回滚到上一个版本

        Returns:
            是否回滚成功
        """
        info(f"开始回滚环境: {target_env}")

        try:
            # 获取部署历史
            history = self._get_deployment_history(target_env)
            if not history:
                error(f"未找到环境 {target_env} 的部署历史")
                return False

            # 确定要回滚到的版本
            if version:
                rollback_deployment = next(
                    (d for d in history if d["version"] == version), None
                )
            else:
                # 回滚到上一个版本
                history_sorted = sorted(
                    history, key=lambda x: x["deployed_at"], reverse=True
                )
                if len(history_sorted) < 2:
                    error("没有足够的部署历史来进行回滚")
                    return False
                rollback_deployment = history_sorted[1]  # 上一个版本

            if not rollback_deployment:
                error(f"未找到版本 {version} 的部署记录")
                return False

            # 执行回滚
            rollback_artifact = rollback_deployment["artifact_path"]
            deployment_config = self._get_deployment_config(target_env)

            if not deployment_config:
                error(f"未找到环境 {target_env} 的部署配置")
                return False

            success = self._execute_deployment(
                target_env, rollback_artifact, deployment_config
            )

            if success:
                # 记录回滚操作
                self._record_rollback(
                    target_env, rollback_deployment["version"], rollback_artifact
                )
                info(f"回滚到版本 {rollback_deployment['version']} 成功")
            else:
                error(f"回滚到版本 {rollback_deployment['version']} 失败")

            return success

        except Exception as e:
            error(f"回滚过程中发生异常: {e}")
            return False

    def _get_deployment_config(self, target_env: str) -> Optional[Dict[str, Any]]:
        """获取部署配置"""
        config_file = os.path.join(
            self.project_root, "deployment", f"{target_env}_config.yaml"
        )

        if not os.path.exists(config_file):
            # 尝试从配置管理器获取
            try:
                env_config = get_config(f"deployment.{target_env}", {})
                if env_config:
                    return env_config
            except Exception:
                pass

            # 如果都没有，返回默认配置
            info(f"未找到环境 {target_env} 的部署配置文件，使用默认配置")
            return self._get_default_deployment_config(target_env)

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            error(f"读取部署配置文件失败: {e}")
            return None

    def _get_default_deployment_config(self, target_env: str) -> Dict[str, Any]:
        """获取默认部署配置"""
        # 根据环境返回不同的默认配置
        if target_env == "prod":
            return {
                "target_path": "/var/www/prod",
                "backup_before_deploy": True,
                "run_health_check": True,
                "notify_on_deploy": True,
                "model_path": "/var/models/prod",
            }
        elif target_env == "staging":
            return {
                "target_path": "/var/www/staging",
                "backup_before_deploy": True,
                "run_health_check": True,
                "notify_on_deploy": False,
                "model_path": "/var/models/staging",
            }
        else:  # dev or other
            return {
                "target_path": "/tmp/dev_deployment",
                "backup_before_deploy": False,
                "run_health_check": False,
                "notify_on_deploy": False,
                "model_path": "/tmp/models_dev",
            }

    def _get_latest_artifact(self) -> Optional[str]:
        """获取最新的构建产物"""
        build_dir = get_config("cicd.build.output_dir", "./build")

        if not os.path.exists(build_dir):
            return None

        # 查找最新的压缩包文件
        artifacts: List[tuple[float, str]] = []
        try:
            items: List[str] = cast(List[str], os.listdir(build_dir))
            for item in items:
                if item.endswith((".tar.gz", ".zip", ".whl")):
                    file_path = os.path.join(build_dir, item)
                    mod_time = os.path.getmtime(file_path)
                    artifacts.append((mod_time, file_path))
        except (OSError, TypeError) as e:
            error(f"读取构建目录失败: {e}")
            return None

        if not artifacts:
            return None

        # 返回最新修改的文件
        artifacts.sort(reverse=True)
        return artifacts[0][1]

    def _execute_deployment(
        self, target_env: str, artifact_path: str, config: Dict[str, Any]
    ) -> bool:
        """执行实际部署"""
        info(f"开始部署构件: {artifact_path} 到环境: {target_env}")

        try:
            target_path = config.get("target_path", f"/var/www/{target_env}")

            # 创建目标目录
            os.makedirs(target_path, exist_ok=True)

            # 如果需要备份，先备份现有文件
            if config.get("backup_before_deploy", False):
                backup_path = (
                    f"{target_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                if os.path.exists(target_path):
                    shutil.copytree(target_path, backup_path)
                    info(f"已创建备份: {backup_path}")

            # 确定目标部署目录（去除版本号等后缀）
            deploy_dir = os.path.join(target_path, "current")

            # 如果目标目录存在，先删除
            if os.path.exists(deploy_dir):
                shutil.rmtree(deploy_dir)

            # 解压或复制构件
            if artifact_path.endswith(".tar.gz"):
                import tarfile

                with tarfile.open(artifact_path, "r:gz") as tar:
                    tar.extractall(path=deploy_dir)
            elif artifact_path.endswith(".zip"):
                import zipfile

                with zipfile.ZipFile(artifact_path, "r") as zip_ref:
                    zip_ref.extractall(deploy_dir)
            else:
                # 假设是目录，直接复制
                shutil.copytree(artifact_path, deploy_dir)

            # 根据目标环境自动判断是否需要部署模型文件
            if target_env in ["prod", "staging"]:
                model_path = config.get("model_path", f"/var/models/{target_env}")
                self._deploy_models(deploy_dir, model_path)

            # 设置适当的权限
            for root, dirs, files in os.walk(deploy_dir):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o755)
                for f in files:
                    file_path = os.path.join(root, f)
                    # 对Python文件和可执行文件设置执行权限
                    if f.endswith(".py") or os.access(file_path, os.X_OK):
                        os.chmod(file_path, 0o755)
                    else:
                        os.chmod(file_path, 0o644)

            # 如果配置中指定了部署后执行的脚本，运行它
            post_deploy_script = config.get("post_deploy_script")
            if post_deploy_script and os.path.exists(post_deploy_script):
                result = subprocess.run(
                    ["bash", post_deploy_script, deploy_dir],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    error(f"执行部署后脚本失败: {result.stderr}")
                    return False

            # 如果需要运行健康检查，执行它
            if config.get("run_health_check", False):
                health_check_passed = self._run_health_check(target_env, deploy_dir)
                if not health_check_passed:
                    error("健康检查失败")
                    return False

            # 如果需要通知，发送通知
            if config.get("notify_on_deploy", False):
                self._send_deploy_notification(
                    target_env, os.path.basename(artifact_path)
                )

            info(f"部署到 {target_env} 成功")
            return True

        except Exception as e:
            error(f"部署执行失败: {e}")
            return False

    def _deploy_models(self, source_dir: str, model_target_path: str) -> bool:
        """部署模型文件"""
        info(f"部署模型文件到: {model_target_path}")

        try:
            # 确保模型目录存在
            os.makedirs(model_target_path, exist_ok=True)

            # 查找源目录中的模型文件
            model_extensions = [".pth", ".pt", ".onnx", ".pb", ".h5", ".joblib", ".pkl"]
            deployed_models: List[str] = []

            for root, _, files in os.walk(source_dir):  # 使用 _ 忽略 dirs 变量
                for file in files:
                    if any(file.endswith(ext) for ext in model_extensions):
                        source_path = os.path.join(root, file)
                        target_path = os.path.join(model_target_path, file)

                        # 复制模型文件
                        shutil.copy2(source_path, target_path)
                        deployed_models.append(file)
                        info(f"已部署模型: {file}")

            info(f"模型部署完成，共部署 {len(deployed_models)} 个模型文件")
            return True

        except Exception as e:
            error(f"模型部署失败: {e}")
            return False

    def _run_health_check(self, target_env: str, deploy_dir: str) -> bool:
        """运行健康检查"""
        info(f"对环境 {target_env} 运行健康检查")

        try:
            # 简单的健康检查：检查主应用文件是否存在并可运行
            main_app_path = os.path.join(deploy_dir, "main.py")
            if not os.path.exists(main_app_path):
                # 尝试其他可能的入口文件
                possible_entries = ["app.py", "server.py", "application.py"]
                for entry in possible_entries:
                    main_app_path = os.path.join(deploy_dir, entry)
                    if os.path.exists(main_app_path):
                        break
                else:
                    error("找不到应用入口文件")
                    return False

            # 尝试导入应用文件，检查是否有语法错误
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "health_check_app", main_app_path
            )
            if spec and spec.loader:
                try:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    error(f"应用健康检查失败: {e}")
                    return False

            # 对于深度学习应用，检查模型文件是否可加载
            model_extensions = [".pth", ".pt", ".onnx", ".pb", ".h5"]
            model_files: List[str] = []

            for root, _, files in os.walk(deploy_dir):  # 使用 _ 忽略 dirs 变量
                for file in files:
                    if any(file.endswith(ext) for ext in model_extensions):
                        model_files.append(os.path.join(root, file))

            if model_files:
                info(f"检测到 {len(model_files)} 个模型文件，执行模型加载测试")

                # 尝试加载第一个模型以验证环境兼容性
                first_model: str = model_files[0]
                if first_model.endswith((".pth", ".pt")):
                    try:
                        import torch  # type: ignore

                        model = torch.load(first_model, map_location="cpu")
                        info("PyTorch 模型加载测试成功")
                    except Exception as e:
                        warning(f"PyTorch 模型加载测试失败: {e}")
                elif first_model.endswith(".onnx"):
                    try:
                        import onnx  # type: ignore

                        model = onnx.load(first_model)
                        onnx.checker.check_model(model)
                        info("ONNX 模型验证成功")
                    except Exception as e:
                        warning(f"ONNX 模型验证失败: {e}")

            info("健康检查通过")
            return True

        except Exception as e:
            error(f"健康检查异常: {e}")
            return False

    def _send_deploy_notification(self, target_env: str, artifact_name: str) -> None:
        """发送部署通知"""
        info(f"发送部署通知到环境: {target_env}")

        # 这里可以实现具体的通知逻辑，如邮件、Slack等
        # 为了简化，这里只是记录日志
        notification_msg = (
            f"部署成功: {artifact_name} -> {target_env} at {datetime.now()}"
        )
        info(notification_msg)

        # TODO: 实现具体的通知发送逻辑（如邮件、Webhook等）

    def _record_deployment(
        self, target_env: str, artifact_path: str, success: bool
    ) -> None:
        """记录部署历史"""
        record: Dict[str, Any] = {
            "environment": target_env,
            "artifact_path": artifact_path,
            "version": (
                os.path.basename(artifact_path).split("_")[1]
                if "_" in os.path.basename(artifact_path)
                else "unknown"
            ),
            "deployed_at": datetime.now().isoformat(),
            "success": success,
        }

        self.deployment_history.append(record)

        # 保存部署历史到文件
        history_file = os.path.join(self.project_root, "deployment", "history.yaml")
        os.makedirs(os.path.dirname(history_file), exist_ok=True)

        # 读取现有历史
        history: List[Dict[str, Any]] = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    loaded_data = yaml.safe_load(f)
                    if isinstance(loaded_data, list):
                        history = cast(List[Dict[str, Any]], loaded_data)
            except Exception:
                history = []

        # 添加新的记录
        history.append(record)

        # 只保留最近的20条记录
        history = history[-20:]

        # 保存历史
        with open(history_file, "w", encoding="utf-8") as f:
            yaml.dump(history, f, indent=2, allow_unicode=True, sort_keys=False)

    def _get_deployment_history(self, target_env: str) -> List[Dict[str, Any]]:
        """获取部署历史"""
        history_file = os.path.join(self.project_root, "deployment", "history.yaml")

        if not os.path.exists(history_file):
            return []

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                loaded_data = yaml.safe_load(f)
                if loaded_data is None:
                    return []
                if isinstance(loaded_data, list):
                    history = cast(List[Dict[str, Any]], loaded_data)
                    return [h for h in history if h.get("environment") == target_env]
                else:
                    return []
        except Exception as e:
            error(f"读取部署历史失败: {e}")
            return []

    def _record_rollback(
        self, target_env: str, version: str, artifact_path: str
    ) -> None:
        """记录回滚操作"""
        info(f"记录回滚操作: {target_env}, version: {version}")

        # 这里可以添加特殊的回滚记录到历史文件
        rollback_record: Dict[str, Any] = {
            "environment": target_env,
            "version": version,
            "artifact_path": artifact_path,
            "rolled_back_at": datetime.now().isoformat(),
            "type": "rollback",
        }

        # 保存到专门的回滚历史文件
        rollback_history_file = os.path.join(
            self.project_root, "deployment", "rollback_history.yaml"
        )
        os.makedirs(os.path.dirname(rollback_history_file), exist_ok=True)

        history: List[Dict[str, Any]] = []
        if os.path.exists(rollback_history_file):
            try:
                with open(rollback_history_file, "r", encoding="utf-8") as f:
                    loaded_data = yaml.safe_load(f)
                    if isinstance(loaded_data, list):
                        history = cast(List[Dict[str, Any]], loaded_data)
            except Exception:
                history = []

        history.append(rollback_record)

        # 只保留最近的10条回滚记录
        history = history[-10:]

        with open(rollback_history_file, "w", encoding="utf-8") as f:
            yaml.dump(history, f, indent=2, allow_unicode=True, sort_keys=False)
