"""
系统信息检测器 - 检测用户的操作系统、硬件配置等信息
"""

import platform
import psutil
import subprocess
from typing import Dict, List, Optional, Any

from core.logger import info, warning, error
from core.config import get_config, register_config
from core.path import get_project_root


class SystemDetector:
    """系统信息检测器"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        
        # 注册系统检测相关配置
        register_config("system_detector.auto_detect", True, bool, "是否自动检测系统信息")
        register_config("system_detector.min_ram_gb", 2, int, "最小内存要求（GB）")
        register_config("system_detector.min_storage_gb", 1, int, "最小存储空间要求（GB）")
        register_config("system_detector.gpu_required", False, bool, "是否需要GPU")
        
    def detect_system_info(self) -> Dict[str, Any]:
        """
        检测系统信息
        
        Returns:
            系统信息字典
        """
        system_info: Dict[str, Any] = {
            "os": self._detect_os(),
            "hardware": self._detect_hardware(),
            "cpu": self._detect_cpu(),
            "memory": self._detect_memory(),
            "storage": self._detect_storage(),
            "gpu": self._detect_gpu(),
            "network": self._detect_network(),
            "deep_learning": self._detect_deep_learning_frameworks()
        }
        
        info("系统信息检测完成")
        return system_info
    
    def _detect_os(self) -> Dict[str, str]:
        """检测操作系统信息"""
        arch_info: tuple[str, str] = platform.architecture()
        
        os_info: Dict[str, str] = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor() or "Unknown",
            "architecture": arch_info[0]
        }
        
        return os_info
    
    def _detect_hardware(self) -> Dict[str, str]:
        """检测硬件信息"""
        try:
            # 尝试使用wmic（Windows）或lshw（Linux）获取硬件信息
            system = platform.system().lower()
            
            hardware_info: Dict[str, str] = {
                "manufacturer": "Unknown",
                "model": "Unknown",
                "serial_number": "Unknown"
            }
            
            if system == "windows":
                try:
                    result = subprocess.run(
                        ["wmic", "computersystem", "get", "manufacturer,model"], 
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            values = lines[1].strip().split()
                            if len(values) >= 2:
                                hardware_info["manufacturer"] = values[0]
                                hardware_info["model"] = values[1]
                except Exception as e:
                    warning(f"获取Windows硬件信息失败: {e}")
                    
            elif system == "linux":
                try:
                    result = subprocess.run(
                        ["sudo", "dmidecode", "-s", "system-manufacturer"], 
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        hardware_info["manufacturer"] = result.stdout.strip()
                    
                    result = subprocess.run(
                        ["sudo", "dmidecode", "-s", "system-product-name"], 
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        hardware_info["model"] = result.stdout.strip()
                except Exception as e:
                    warning(f"获取Linux硬件信息失败: {e}")
                    
            elif system == "darwin":  # macOS
                try:
                    result = subprocess.run(
                        ["system_profiler", "SPHardwareDataType"], 
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'Chip' in line or 'Processor' in line:
                                hardware_info["model"] = line.split(':')[-1].strip()
                                break
                except Exception as e:
                    warning(f"获取macOS硬件信息失败: {e}")
                    
            return hardware_info
        except Exception as e:
            error(f"检测硬件信息时出错: {e}")
            return {
                "manufacturer": "Unknown",
                "model": "Unknown",
                "serial_number": "Unknown"
            }
    
    def _detect_cpu(self) -> Dict[str, Any]:
        """检测CPU信息"""
        physical_cores: int = psutil.cpu_count(logical=False) or 0
        total_cores: int = psutil.cpu_count(logical=True) or 0
        
        cpu_freq = psutil.cpu_freq()
        max_frequency: float = cpu_freq.max if cpu_freq else 0.0
        current_frequency: float = cpu_freq.current if cpu_freq else 0.0
        
        usage_per_core: List[float] = psutil.cpu_percent(percpu=True)
        total_usage: float = psutil.cpu_percent()
        
        cpu_info: Dict[str, Any] = {
            "physical_cores": physical_cores,
            "total_cores": total_cores,
            "max_frequency": max_frequency,
            "current_frequency": current_frequency,
            "usage_per_core": usage_per_core,
            "total_usage": total_usage,
            "name": "Unknown"
        }
        
        # 检测CPU特性
        try:
            if platform.system().lower() == "windows":
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"], 
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        cpu_info["name"] = lines[1].strip()
            else:
                # Linux/macOS
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if line.startswith('model name'):
                                cpu_info["name"] = line.split(':', 1)[1].strip()
                                break
                except FileNotFoundError:
                    # macOS 或其他系统
                    result = subprocess.run(
                        ["sysctl", "-n", "machdep.cpu.brand_string"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        cpu_info["name"] = result.stdout.strip()
        except Exception as e:
            warning(f"获取CPU名称失败: {e}")
        
        return cpu_info
    
    def _detect_memory(self) -> Dict[str, float]:
        """检测内存信息"""
        svmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        memory_info: Dict[str, float] = {
            "total": float(svmem.total) / (1024 ** 3),  # GB
            "available": float(svmem.available) / (1024 ** 3),  # GB
            "used": float(svmem.used) / (1024 ** 3),  # GB
            "percentage": float(svmem.percent),
            "swap_total": float(swap.total) / (1024 ** 3),  # GB
            "swap_used": float(swap.used) / (1024 ** 3),  # GB
            "swap_percentage": float(swap.percent)
        }
        
        return memory_info
    
    def _detect_storage(self) -> Dict[str, float]:
        """检测存储信息"""
        partition_usage = psutil.disk_usage(str(self.project_root))
        
        total_gb: float = float(partition_usage.total) / (1024 ** 3)
        used_gb: float = float(partition_usage.used) / (1024 ** 3)
        free_gb: float = float(partition_usage.free) / (1024 ** 3)
        
        percentage: float = (partition_usage.used / partition_usage.total) * 100 if partition_usage.total > 0 else 0.0
        
        storage_info: Dict[str, float] = {
            "total": total_gb,
            "used": used_gb,
            "free": free_gb,
            "percentage": percentage
        }
        
        return storage_info
    
    def _detect_gpu(self) -> List[Dict[str, Any]]:
        """检测GPU信息"""
        gpus: List[Dict[str, Any]] = []
        
        # 检测NVIDIA GPU
        nvidia_gpus: List[Dict[str, Any]] = self._detect_nvidia_gpu()
        gpus.extend(nvidia_gpus)
        
        # 检测AMD GPU
        amd_gpus: List[Dict[str, Any]] = self._detect_amd_gpu()
        gpus.extend(amd_gpus)
        
        # 检测Intel GPU
        intel_gpus: List[Dict[str, Any]] = self._detect_intel_gpu()
        gpus.extend(intel_gpus)
        
        # 检测Apple Silicon
        apple_gpus: List[Dict[str, Any]] = self._detect_apple_gpu()
        gpus.extend(apple_gpus)
        
        return gpus
    
    def _detect_nvidia_gpu(self) -> List[Dict[str, Any]]:
        """检测NVIDIA GPU"""
        gpus: List[Dict[str, Any]] = []
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,driver_version", 
                 "--format=csv,noheader,nounits"], 
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts: List[str] = [part.strip() for part in line.split(',')]
                        if len(parts) >= 4:
                            gpu_info: Dict[str, Any] = {
                                "vendor": "NVIDIA",
                                "name": parts[0],
                                "memory_total": int(parts[1]),  # MB
                                "memory_used": int(parts[2]),   # MB
                                "memory_free": int(parts[3]),   # MB
                                "driver_version": parts[4] if len(parts) > 4 else "Unknown",
                                "cuda_supported": self._check_cuda_support()
                            }
                            gpus.append(gpu_info)
        except FileNotFoundError:
            # nvidia-smi not found
            pass
        except Exception as e:
            warning(f"检测NVIDIA GPU失败: {e}")
        
        return gpus
    
    def _check_cuda_support(self) -> bool:
        """检查 CUDA 支持"""
        try:
            import torch # type: ignore
            return bool(torch.cuda.is_available())
        except ImportError:
            pass
        
        try:
            # 尝试使用 nvidia-ml-py3
            import pynvml # type: ignore
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            return device_count > 0
        except Exception:
            return False
    
    def _detect_amd_gpu(self) -> List[Dict[str, Any]]:
        """检测AMD GPU"""
        gpus: List[Dict[str, Any]] = []
        
        try:
            # 尝试使用rocm-smi（如果安装了ROCm）
            result = subprocess.run(
                ["rocm-smi", "--showproductname"], 
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Card' in line and 'Name:' in line:
                        gpu_info: Dict[str, Any] = {
                            "vendor": "AMD",
                            "name": line.split('Name:')[-1].strip(),
                            "memory_total": "Unknown",  # ROCm可能不直接提供内存大小
                            "memory_used": "Unknown",
                            "memory_free": "Unknown",
                            "driver_version": "Unknown",
                            "cuda_supported": False  # AMD不支持CUDA
                        }
                        gpus.append(gpu_info)
        except FileNotFoundError:
            # rocm-smi not found
            pass
        except Exception as e:
            warning(f"检测AMD GPU失败: {e}")
        
        return gpus
    
    def _detect_intel_gpu(self) -> List[Dict[str, Any]]:
        """检测Intel GPU"""
        gpus: List[Dict[str, Any]] = []
        
        try:
            # Windows
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "path", "win32_videocontroller", "get", "name,adapterram"], 
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # Skip header
                        if line.strip():
                            parts: List[str] = line.strip().split()
                            if parts and 'intel' in parts[0].lower():
                                memory_total: Any = int(parts[-1]) / (1024**2) if parts[-1].isdigit() else "Unknown"
                                gpu_info: Dict[str, Any] = {
                                    "vendor": "Intel",
                                    "name": ' '.join(parts[:-1]) if len(parts) > 1 else parts[0],
                                    "memory_total": memory_total,
                                    "memory_used": "Unknown",
                                    "memory_free": "Unknown",
                                    "driver_version": "Unknown",
                                    "cuda_supported": False  # Intel不支持CUDA
                                }
                                gpus.append(gpu_info)
        except Exception as e:
            warning(f"检测Intel GPU失败: {e}")
        
        return gpus
    
    def _detect_apple_gpu(self) -> List[Dict[str, Any]]:
        """检测Apple GPU"""
        gpus: List[Dict[str, Any]] = []
        
        if platform.system() == "Darwin":  # macOS
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"], 
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    # 解析输出获取GPU信息
                    lines = result.stdout.split('\n')
                    for i, line in enumerate(lines):
                        if 'Chip:' in line or 'Processor:' in line:
                            gpu_name: str = line.split(':')[-1].strip()
                            gpu_info: Dict[str, Any] = {
                                "vendor": "Apple",
                                "name": gpu_name,
                                "memory_total": "Unknown",
                                "memory_used": "Unknown",
                                "memory_free": "Unknown",
                                "driver_version": "Unknown",
                                "cuda_supported": False,  # Apple不支持CUDA，但支持Metal
                                "metal_supported": True
                            }
                            gpus.append(gpu_info)
            except Exception as e:
                warning(f"检测Apple GPU失败: {e}")
        
        return gpus
    
    def _detect_deep_learning_frameworks(self) -> Dict[str, Any]:
        """检测深度学习框架"""
        frameworks: Dict[str, Any] = {}
        
        # 检测 PaddlePaddle
        try:
            import paddle
            paddle_version: str = getattr(paddle, '__version__', 'unknown')
            paddle_gpu_available: bool = False
            try:
                paddle_gpu_available = paddle.device.is_compiled_with_cuda()
            except AttributeError:
                # 旧版本可能没有这个方法
                pass
            
            paddle_info: Dict[str, Any] = {
                "version": paddle_version,
                "gpu_available": paddle_gpu_available,
                "backend": "paddle"
            }
            frameworks["paddle"] = paddle_info
            
            info(f"检测到 PaddlePaddle: {paddle_version}, GPU支持: {paddle_gpu_available}")
        except ImportError:
            frameworks["paddle"] = {
                "version": "not installed",
                "gpu_available": False,
                "backend": "paddle"
            }
            info("PaddlePaddle 未安装")
        except Exception as e:
            error(f"检测 PaddlePaddle 时出错: {e}")
            frameworks["paddle"] = {
                "version": f"error: {str(e)}",
                "gpu_available": False,
                "backend": "paddle"
            }
        
        # 检测 PyTorch
        try:
            import torch # type: ignore
            torch_version: str = getattr(torch, '__version__', 'unknown')
            torch_gpu_available: bool = False
            try:
                torch_gpu_available = torch.cuda.is_available()
            except AttributeError:
                # 旧版本可能没有这个方法
                pass
            
            pytorch_info: Dict[str, Any] = {
                "version": torch_version,
                "gpu_available": torch_gpu_available,
                "backend": "pytorch"
            }
            frameworks["pytorch"] = pytorch_info
            
            info(f"检测到 PyTorch: {torch_version}, GPU支持: {torch_gpu_available}")
        except ImportError:
            frameworks["pytorch"] = {
                "version": "not installed",
                "gpu_available": False,
                "backend": "pytorch"
            }
            info("PyTorch 未安装")
        except Exception as e:
            error(f"检测 PyTorch 时出错: {e}")
            frameworks["pytorch"] = {
                "version": f"error: {str(e)}",
                "gpu_available": False,
                "backend": "pytorch"
            }
        
        # 检测 TensorFlow
        try:
            import tensorflow as tf # type: ignore
            tf_version: str = getattr(tf, '__version__', 'unknown')
            tf_gpu_available: bool = False
            try:
                tf_gpu_available = len(tf.config.experimental.list_physical_devices('GPU')) > 0
            except AttributeError:
                # 旧版本可能没有这个方法
                pass
            
            tf_info: Dict[str, Any] = {
                "version": tf_version,
                "gpu_available": tf_gpu_available,
                "backend": "tensorflow"
            }
            frameworks["tensorflow"] = tf_info
            
            info(f"检测到 TensorFlow: {tf_version}, GPU支持: {tf_gpu_available}")
        except ImportError:
            frameworks["tensorflow"] = {
                "version": "not installed",
                "gpu_available": False,
                "backend": "tensorflow"
            }
            info("TensorFlow 未安装")
        except Exception as e:
            error(f"检测 TensorFlow 时出错: {e}")
            frameworks["tensorflow"] = {
                "version": f"error: {str(e)}",
                "gpu_available": False,
                "backend": "tensorflow"
            }
        
        return frameworks
    
    def _detect_network(self) -> Dict[str, Any]:
        """检测网络信息"""
        net_io = psutil.net_io_counters()
        
        network_info: Dict[str, Any] = {
            "bytes_sent": int(net_io.bytes_sent),
            "bytes_recv": int(net_io.bytes_recv),
            "packets_sent": int(net_io.packets_sent),
            "packets_recv": int(net_io.packets_recv),
            "interfaces": len(psutil.net_if_addrs())
        }
        
        return network_info
    
    def validate_system_requirements(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证系统是否满足最低要求
        
        Args:
            system_info: 系统信息字典
            
        Returns:
            验证结果
        """
        min_ram_gb = get_config("system_detector.min_ram_gb", 2)
        min_storage_gb = get_config("system_detector.min_storage_gb", 1)
        gpu_required = get_config("system_detector.gpu_required", False)
        
        validation_result: Dict[str, Any] = {
            "valid": True,
            "issues": [],
            "recommendations": []
        }
        
        # 检查内存
        if system_info["memory"]["total"] < min_ram_gb:
            validation_result["valid"] = False
            validation_result["issues"].append(
                f"内存不足: 需要至少 {min_ram_gb}GB，当前 {system_info['memory']['total']:.2f}GB"
            )
        elif system_info["memory"]["available"] < min_ram_gb * 0.8:
            validation_result["recommendations"].append(
                f"可用内存较低: 建议保留至少 {min_ram_gb * 0.8}GB 可用内存"
            )
        
        # 检查存储
        if system_info["storage"]["free"] < min_storage_gb:
            validation_result["valid"] = False
            validation_result["issues"].append(
                f"存储空间不足: 需要至少 {min_storage_gb}GB，当前 {system_info['storage']['free']:.2f}GB"
            )
        
        # 检查GPU
        if gpu_required and not system_info["gpu"]:
            validation_result["valid"] = False
            validation_result["issues"].append("需要GPU但未检测到")
        elif gpu_required and system_info["gpu"]:
            # 检查是否有支持CUDA的GPU
            cuda_gpus = [gpu for gpu in system_info["gpu"] if gpu.get("cuda_supported", False)]
            if not cuda_gpus:
                # 检查是否支持PaddlePaddle的GPU
                paddle_gpu = system_info.get("deep_learning", {}).get("paddle", {}).get("gpu_available", False)
                if not cuda_gpus and not paddle_gpu:
                    validation_result["valid"] = False
                    validation_result["issues"].append("需要CUDA或PaddlePaddle GPU支持，但未检测到")
        
        # 检查CPU核心数
        if system_info["cpu"]["physical_cores"] < 2:
            validation_result["recommendations"].append(
                "CPU核心数较少，可能影响性能"
            )
        
        return validation_result
    
    def generate_config_from_system(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据系统信息生成配置
        
        Args:
            system_info: 系统信息字典
            
        Returns:
            生成的配置
        """
        config: Dict[str, Any] = {}
        
        # 根据CPU核心数设置工作进程数
        cpu_cores = system_info["cpu"]["physical_cores"]
        config["num_workers"] = min(cpu_cores, 8)  # 最多8个工作进程
        
        # 根据内存设置批处理大小
        total_memory_gb = system_info["memory"]["total"]
        if total_memory_gb >= 16:
            config["batch_size"] = 32
        elif total_memory_gb >= 8:
            config["batch_size"] = 16
        elif total_memory_gb >= 4:
            config["batch_size"] = 8
        else:
            config["batch_size"] = 4
        
        # 根据深度学习框架设置后端
        dl_frameworks = system_info.get("deep_learning", {})
        paddle_info = dl_frameworks.get("paddle", {})
        pytorch_info = dl_frameworks.get("pytorch", {})
        tf_info = dl_frameworks.get("tensorflow", {})
        
        # 优先级：如果有PaddlePaddle则优先使用
        if paddle_info.get("version") and "not installed" not in str(paddle_info["version"]):
            config["dl_backend"] = "paddle"
            config["use_gpu"] = paddle_info.get("gpu_available", False)
        elif pytorch_info.get("version") and "not installed" not in str(pytorch_info["version"]):
            config["dl_backend"] = "pytorch"
            config["use_gpu"] = pytorch_info.get("gpu_available", False)
        elif tf_info.get("version") and "not installed" not in str(tf_info["version"]):
            config["dl_backend"] = "tensorflow"
            config["use_gpu"] = tf_info.get("gpu_available", False)
        else:
            config["dl_backend"] = "none"
            config["use_gpu"] = False
        
        # 根据GPU设置GPU数量
        if config["use_gpu"]:
            if config["dl_backend"] == "paddle":
                try:
                    import paddle
                    config["gpu_count"] = len(paddle.device.get_available_device()) if paddle_info.get("gpu_available") else 0
                except Exception:
                    config["gpu_count"] = 0
            elif config["dl_backend"] == "pytorch":
                try:
                    import torch # type: ignore
                    config["gpu_count"] = torch.cuda.device_count() if pytorch_info.get("gpu_available") else 0
                except Exception:
                    config["gpu_count"] = 0
            elif config["dl_backend"] == "tensorflow":
                try:
                    import tensorflow as tf # type: ignore
                    config["gpu_count"] = len(tf.config.experimental.list_physical_devices('GPU'))
                except Exception:
                    config["gpu_count"] = 0
        else:
            config["gpu_count"] = 0
        
        # 根据存储空间设置缓存大小
        free_storage_gb = system_info["storage"]["free"]
        if free_storage_gb >= 10:
            config["cache_size"] = "large"
        elif free_storage_gb >= 5:
            config["cache_size"] = "medium"
        else:
            config["cache_size"] = "small"
        
        return config