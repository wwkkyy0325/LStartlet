"""
系统信息检测器 - 检测用户的操作系统、硬件配置等信息
"""

import platform
import sys
import psutil
import subprocess
from typing import Dict, List, Optional, Any

from LStartlet.core.logger import info, warning, error
from LStartlet.core.config import get_config, register_config
from LStartlet.core.path import get_project_root


class SystemDetector:
    """系统信息检测器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()

        # 注册系统检测相关配置
        register_config(
            "system_detector.auto_detect", True, bool, "是否自动检测系统信息"
        )
        register_config("system_detector.min_ram_gb", 2, int, "最小内存要求（GB）")
        register_config(
            "system_detector.min_storage_gb", 1, int, "最小存储空间要求（GB）"
        )
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
            "gpu": self._detect_gpus(),
            "network": self._detect_network(),
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
            "architecture": arch_info[0],
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
                "serial_number": "Unknown",
            }

            if system == "windows":
                try:
                    result = subprocess.run(
                        ["wmic", "computersystem", "get", "manufacturer,model"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split("\n")
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
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        hardware_info["manufacturer"] = result.stdout.strip()

                    result = subprocess.run(
                        ["sudo", "dmidecode", "-s", "system-product-name"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        hardware_info["model"] = result.stdout.strip()
                except Exception as e:
                    warning(f"获取Linux硬件信息失败: {e}")

            elif system == "darwin":  # macOS
                try:
                    result = subprocess.run(
                        ["system_profiler", "SPHardwareDataType"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split("\n"):
                            if "Chip" in line or "Processor" in line:
                                hardware_info["model"] = line.split(":")[-1].strip()
                                break
                except Exception as e:
                    warning(f"获取macOS硬件信息失败: {e}")

            return hardware_info
        except Exception as e:
            error(f"检测硬件信息时出错: {e}")
            return {
                "manufacturer": "Unknown",
                "model": "Unknown",
                "serial_number": "Unknown",
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
            "name": "Unknown",
        }

        # 检测CPU特性
        try:
            if platform.system().lower() == "windows":
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        cpu_info["name"] = lines[1].strip()
            else:
                # Linux/macOS
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if line.startswith("model name"):
                                cpu_info["name"] = line.split(":", 1)[1].strip()
                                break
                except FileNotFoundError:
                    # macOS 或其他系统
                    result = subprocess.run(
                        ["sysctl", "-n", "machdep.cpu.brand_string"],
                        capture_output=True,
                        text=True,
                        timeout=10,
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
            "total": float(svmem.total) / (1024**3),  # GB
            "available": float(svmem.available) / (1024**3),  # GB
            "used": float(svmem.used) / (1024**3),  # GB
            "percentage": float(svmem.percent),
            "swap_total": float(swap.total) / (1024**3),  # GB
            "swap_used": float(swap.used) / (1024**3),  # GB
            "swap_percentage": float(swap.percent),
        }

        return memory_info

    def _detect_storage(self) -> Dict[str, float]:
        """检测存储信息"""
        partition_usage = psutil.disk_usage(str(self.project_root))

        total_gb: float = float(partition_usage.total) / (1024**3)
        used_gb: float = float(partition_usage.used) / (1024**3)
        free_gb: float = float(partition_usage.free) / (1024**3)

        percentage: float = (
            (partition_usage.used / partition_usage.total) * 100
            if partition_usage.total > 0
            else 0.0
        )

        storage_info: Dict[str, float] = {
            "total": total_gb,
            "used": used_gb,
            "free": free_gb,
            "percentage": percentage,
        }

        return storage_info

    def _detect_gpus(self) -> List[Dict[str, Any]]:
        """检测GPU信息"""
        gpus: List[Dict[str, Any]] = []

        if sys.platform == "darwin":  # macOS
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    # 解析输出获取GPU信息
                    lines = result.stdout.split("\n")
                    for i, line in enumerate(lines):
                        if "Chip:" in line or "Processor:" in line:
                            gpu_name: str = line.split(":")[-1].strip()
                            gpu_info: Dict[str, Any] = {
                                "vendor": "Apple",
                                "name": gpu_name,
                                "memory_total": "Unknown",
                                "memory_used": "Unknown",
                                "memory_free": "Unknown",
                                "driver_version": "Unknown",
                                "cuda_supported": False,  # Apple不支持CUDA，但支持Metal
                                "metal_supported": True,
                            }
                            gpus.append(gpu_info)
            except Exception as e:
                warning(f"检测Apple GPU失败: {e}")

        return gpus

    def validate_system_requirements(
        self, system_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证系统要求

        Args:
            system_info: 系统信息字典

        Returns:
            验证结果字典
        """
        validation_result: Dict[str, Any] = {
            "valid": True,
            "issues": [],
            "recommendations": [],
        }

        # 检查CPU核心数
        if system_info["cpu"]["physical_cores"] < 2:
            validation_result["recommendations"].append("CPU核心数较少，可能影响性能")

        return validation_result

    def generate_config_from_system(
        self, system_info: Dict[str, Any]
    ) -> Dict[str, Any]:
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

        # 移除深度学习框架相关的配置生成逻辑
        # 只保留基础配置

        # 根据存储空间设置缓存大小
        free_space_gb = system_info["storage"]["free"]
        if free_space_gb >= 100:
            config["cache_size"] = "large"
        elif free_space_gb >= 50:
            config["cache_size"] = "medium"
        else:
            config["cache_size"] = "small"

        return config

    def _detect_network(self) -> Dict[str, Any]:
        """检测网络信息"""
        net_io = psutil.net_io_counters()

        network_info: Dict[str, Any] = {
            "bytes_sent": int(net_io.bytes_sent),
            "bytes_recv": int(net_io.bytes_recv),
            "packets_sent": int(net_io.packets_sent),
            "packets_recv": int(net_io.packets_recv),
            "interfaces": len(psutil.net_if_addrs()),
        }

        return network_info
