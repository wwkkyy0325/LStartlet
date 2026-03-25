"""
深度学习框架管理器 - 专门处理深度学习相关依赖
"""

import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

from core.logger import info, warning, error
from core.config import get_config, register_config
from core.path import get_project_root


class DeepLearningManager:
    """深度学习框架管理器"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        
        # 注册深度学习相关配置
        register_config("dl_framework.cuda_version", "", str, "CUDA 版本")
        register_config("dl_framework.pytorch_version", "", str, "PyTorch 版本")
        register_config("dl_framework.tensorflow_version", "", str, "TensorFlow 版本")
        register_config("dl_framework.paddle_version", "", str, "PaddlePaddle 版本")
        register_config("dl_framework.onnx_version", "", str, "ONNX 版本")
        register_config("dl_framework.models_dir", "./models", str, "模型文件存储目录")
        register_config("dl_framework.requirements_dl", "requirements-dl.txt", str, "深度学习依赖文件")
    
    def detect_deep_learning_deps(self) -> Dict[str, str]:
        """
        检测项目中的深度学习依赖
        
        Returns:
            深度学习框架及其版本的字典
        """
        deps: Dict[str, str] = {}
        
        # 检测常见的深度学习框架
        frameworks = {
            'torch': 'PyTorch',
            'tensorflow': 'TensorFlow', 
            'keras': 'Keras',
            'paddle': 'PaddlePaddle',
            'onnx': 'ONNX',
            'opencv-python': 'OpenCV',
            'numpy': 'NumPy',
            'pandas': 'Pandas',
            'scipy': 'SciPy',
            'matplotlib': 'Matplotlib',
            'pillow': 'Pillow',
            'scikit-learn': 'Scikit-learn'
        }
        
        for module_name, friendly_name in frameworks.items():
            try:
                # 动态导入模块并获取版本
                __import__(module_name)
                module = sys.modules[module_name]
                
                # 获取版本信息
                if hasattr(module, '__version__'):
                    version = str(module.__version__)
                elif hasattr(module, 'VERSION'):
                    version = str(module.VERSION)
                elif module_name == 'paddle':
                    # PaddlePaddle 特殊处理
                    import paddle
                    version = str(getattr(paddle, '__version__', 'unknown'))
                else:
                    version = "unknown"
                
                deps[friendly_name] = version
                info(f"检测到 {friendly_name}: {version}")
            except ImportError:
                # 模块未安装
                continue
            except Exception as e:
                warning(f"检测 {friendly_name} 时出错: {e}")
        
        return deps
    
    def generate_dl_requirements(self, output_file: Optional[str] = None) -> bool:
        """
        生成深度学习依赖文件
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            是否生成成功
        """
        if output_file is None:
            output_file = get_config("dl_framework.requirements_dl", "requirements-dl.txt")
        
        try:
            # 获取当前环境的包列表
            result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                                    capture_output=True, text=True)
            
            if result.returncode != 0:
                error("获取包列表失败")
                return False
            
            # 过滤出深度学习相关包
            all_packages = result.stdout.strip().split('\n')
            dl_packages: List[str] = []
            
            dl_keywords = ['torch', 'tensorflow', 'keras', 'paddle', 'onnx', 'opencv', 'numpy', 
                          'pandas', 'scipy', 'matplotlib', 'pillow', 'scikit-learn', 
                          'nltk', 'spacy', 'transformers', 'fastai', 'pytorch', 'paddlepaddle']
            
            for package in all_packages:
                if any(keyword in package.lower() for keyword in dl_keywords):
                    dl_packages.append(package)
            
            # 写入文件
            if output_file:  # 确保 output_file 不为 None
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("# 深度学习框架依赖\n")
                    f.write("# 自动生成于 {}\n\n".format(self._get_current_datetime()))
                    
                    for package in dl_packages:
                        f.write(package + "\n")
            
            info(f"深度学习依赖文件已生成: {output_file}")
            return True
            
        except Exception as e:
            error(f"生成深度学习依赖文件时出错: {e}")
            return False
    
    def validate_environment_compatibility(self) -> Tuple[bool, List[str]]:
        """
        验证环境兼容性
        
        Returns:
            (是否兼容, 不兼容的原因列表)
        """
        issues: List[str] = []
        
        # 检查 CUDA 版本兼容性
        try:
            # 检查 PyTorch
            import torch # type: ignore
            if torch.cuda.is_available():
                cuda_version: Optional[str] = getattr(torch.version, 'cuda', None) if hasattr(torch, 'version') else None
                if cuda_version:
                    info(f"PyTorch - CUDA 可用，版本: {cuda_version}")
                else:
                    info("PyTorch - CUDA 可用但版本信息不可用")
                
                # 检查 PyTorch 是否与 CUDA 兼容
                if not cuda_version:
                    issues.append("PyTorch 未正确链接 CUDA")
            else:
                info("PyTorch - CUDA 不可用，将使用 CPU 模式")
        except ImportError:
            info("PyTorch 未安装")
        except Exception as e:
            issues.append(f"检查 PyTorch CUDA 兼容性时出错: {e}")
        
        # 检查 PaddlePaddle
        try:
            import paddle
            paddle_version = str(getattr(paddle, '__version__', 'unknown'))
            info(f"PaddlePaddle 版本：{paddle_version}")
            
            # 尝试初始化 PaddlePaddle 并检查 GPU 支持
            try:
                if hasattr(paddle.utils, 'run_check'):
                    paddle.utils.run_check()  # 运行快速验证
                    info("PaddlePaddle - 安装验证通过")
                else:
                    info("PaddlePaddle - 安装但无法运行验证")
            except:
                info("PaddlePaddle - 安装但验证失败")
        except ImportError:
            info("PaddlePaddle 未安装")
        except Exception as e:
            error(f"检查 PaddlePaddle 时出错：{e}")
        
        # 检查内存是否足够
        try:
            import psutil
            available_gb = psutil.virtual_memory().available / (1024**3)
            if available_gb < 4:  # 少于 4GB
                issues.append(f"可用内存不足: {available_gb:.2f}GB，推荐至少 4GB")
        except ImportError:
            warning("psutil 未安装，无法检查内存")
        
        # 检查磁盘空间
        try:
            free_space_gb = self._get_free_disk_space() / (1024**3)
            if free_space_gb < 2:  # 少于 2GB
                issues.append(f"可用磁盘空间不足: {free_space_gb:.2f}GB，推荐至少 2GB")
        except Exception as e:
            issues.append(f"检查磁盘空间时出错: {e}")
        
        is_compatible = len(issues) == 0
        return is_compatible, issues
    
    def _get_free_disk_space(self) -> float:
        """获取可用磁盘空间（字节）"""
        # 处理 Windows 和 Unix 系统的差异
        if os.name == 'nt':  # Windows
            import shutil
            _, _, free = shutil.disk_usage(self.project_root)  # 只使用 free，忽略 total 和 used
            return free
        else:  # Unix/Linux/Mac
            statvfs = os.statvfs(self.project_root)
            return statvfs.f_frsize * statvfs.f_bavail
    
    def _get_current_datetime(self) -> str:
        """获取当前日期时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def optimize_for_hardware(self) -> bool:
        """
        根据硬件优化配置
        
        Returns:
            是否优化成功
        """
        try:
            import torch # type: ignore
            # 检测硬件配置
            gpu_available: bool = torch.cuda.is_available()
            cpu_count = os.cpu_count() or 1
            
            info(f"检测到硬件: GPU可用={gpu_available}, CPU核心数={cpu_count}")
            
            # 根据GPU可用性调整配置
            if gpu_available:
                device = "cuda"
                info("使用 GPU 加速")
            else:
                device = "cpu"
                info("使用 CPU 计算")
            
            # 注册设备配置
            register_config("dl_framework.device", device, str, "计算设备 (cuda/cpu)")
            register_config("dl_framework.num_workers", min(cpu_count, 8), int, "数据加载工作进程数")
            
            return True
            
        except ImportError:
            warning("PyTorch 未安装，跳过硬件优化")
            return False
        except Exception as e:
            error(f"硬件优化时出错: {e}")
            return False
    
    def manage_model_versions(self) -> Dict[str, str]:
        """
        管理模型版本
        
        Returns:
            模型文件路径字典
        """
        models_dir = get_config("dl_framework.models_dir", "./models")
        model_files: Dict[str, str] = {}
        
        if not os.path.exists(models_dir):
            info(f"模型目录不存在: {models_dir}")
            return model_files
        
        # 遍历模型目录，收集模型文件
        for root, _, files in os.walk(models_dir):  # 使用 _ 忽略 dirs 变量
            for file in files:
                if file.endswith(('.pdparams', '.pdopt', '.pdmodel', '.pth', '.pt', '.onnx', '.pb', '.h5', '.joblib')):
                    from pathlib import Path
                    model_path: str = str(Path(root) / file)
                    model_name = os.path.splitext(file)[0]
                    model_files[model_name] = model_path
        
        info(f"检测到 {len(model_files)} 个模型文件")
        return model_files