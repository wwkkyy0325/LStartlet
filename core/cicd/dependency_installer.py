"""
依赖安装器 - 自动检测并安装缺失的依赖
"""

import subprocess
import sys
import os
import importlib.util
from typing import Dict, Optional

from core.logger import info, warning, error
from core.config import get_config, register_config
from core.path import get_project_root


class DependencyInstaller:
    """依赖安装器"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        
        # 注册依赖安装相关配置
        register_config("dependency_installer.auto_install", True, bool, "是否自动安装缺失的依赖")
        register_config("dependency_installer.pip_index_url", "https://pypi.org/simple/", str, "pip索引URL")
        register_config("dependency_installer.pip_trusted_host", "", str, "pip信任主机")
        register_config("dependency_installer.requirements_file", "requirements.txt", str, "requirements文件路径")
        
    def check_and_install_missing(self, required_packages: Optional[Dict[str, str]] = None) -> bool:
        """
        检查并安装缺失的依赖
        
        Args:
            required_packages: 需要检查的包字典，键为包名，值为版本要求
            
        Returns:
            是否成功安装所有缺失的依赖
        """
        auto_install = get_config("dependency_installer.auto_install", True)
        
        if required_packages is None:
            # 从requirements文件读取依赖
            requirements_file = get_config("dependency_installer.requirements_file", "requirements.txt")
            required_packages = self._load_requirements(requirements_file)
        
        missing_packages = self._find_missing_packages(required_packages)
        
        if not missing_packages:
            info("所有依赖均已安装")
            return True
        
        info(f"发现 {len(missing_packages)} 个缺失的依赖: {list(missing_packages.keys())}")
        
        if not auto_install:
            warning("自动安装已禁用，跳过依赖安装")
            return False
        
        # 安装缺失的依赖
        return self.install_packages(missing_packages)
    
    def _load_requirements(self, requirements_file: str) -> Dict[str, str]:
        """
        从requirements文件加载依赖列表
        
        Args:
            requirements_file: requirements文件路径
            
        Returns:
            包名到版本要求的映射
        """
        packages: Dict[str, str] = {}
        
        if not os.path.exists(requirements_file):
            warning(f"requirements文件不存在: {requirements_file}")
            return packages
        
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 解析包名和版本要求
                        if '==' in line:
                            name, version = line.split('==', 1)
                            packages[name.strip()] = f"=={version.strip()}"
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                            packages[name.strip()] = f">={version.strip()}"
                        elif '<=' in line:
                            name, version = line.split('<=', 1)
                            packages[name.strip()] = f"<={version.strip()}"
                        elif '>' in line:
                            name, version = line.split('>', 1)
                            packages[name.strip()] = f">{version.strip()}"
                        elif '<' in line:
                            name, version = line.split('<', 1)
                            packages[name.strip()] = f"<{version.strip()}"
                        elif '~=' in line:
                            name, version = line.split('~=', 1)
                            packages[name.strip()] = f"~={version.strip()}"
                        else:
                            packages[line] = ""  # 无版本要求
        except Exception as e:
            error(f"读取requirements文件失败: {e}")
        
        return packages
    
    def _find_missing_packages(self, required_packages: Dict[str, str]) -> Dict[str, str]:
        """
        查找缺失的包
        
        Args:
            required_packages: 需要的包字典
            
        Returns:
            缺失的包字典
        """
        missing: Dict[str, str] = {}
        
        for package_name, version_req in required_packages.items():
            # 尝试导入包
            if not self._is_package_installed(package_name, version_req):
                missing[package_name] = version_req
        
        return missing
    
    def _is_package_installed(self, package_name: str, version_req: str = "") -> bool:
        """
        检查包是否已安装
        
        Args:
            package_name: 包名
            version_req: 版本要求
            
        Returns:
            是否已安装
        """
        try:
            # 尝试导入包
            if package_name == 'cv2':  # 特殊处理OpenCV
                import cv2
                module = cv2
            else:
                module_spec = importlib.util.find_spec(package_name)
                if module_spec is None:
                    # 尝试用不同格式查找
                    alt_name = package_name.replace('-', '_')
                    module_spec = importlib.util.find_spec(alt_name)
                    if module_spec is None:
                        return False
                    package_name = alt_name
                
                module = importlib.util.module_from_spec(module_spec)
                if module_spec.loader is not None:
                    module_spec.loader.exec_module(module)
                else:
                    return False
            
            # 如果有版本要求，检查版本是否匹配
            if version_req and hasattr(module, '__version__'):
                installed_version = module.__version__
                return self._check_version_match(installed_version, version_req)
            
            return True
        except ImportError:
            return False
        except AttributeError:
            # 某些包可能没有__version__属性
            return True
        except Exception:
            return False
    
    def _check_version_match(self, installed_version: str, version_req: str) -> bool:
        """
        检查安装的版本是否满足要求
        
        Args:
            installed_version: 已安装版本
            version_req: 版本要求
            
        Returns:
            是否满足要求
        """
        try:
            # 解析版本号（简单实现，只比较主要版本号）
            import re
            req_op = version_req[:2] if version_req.startswith(('==', '>=', '<=', '!=', '~=')) else version_req[:1]
            req_ver = version_req[2:] if version_req.startswith(('==', '>=', '<=', '!=', '~=')) else version_req[1:]
            
            # 简单的版本比较
            inst_parts = [int(x) for x in re.split(r'[^\d]', installed_version)[:3] if x.isdigit()]
            req_parts = [int(x) for x in re.split(r'[^\d]', req_ver)[:3] if x.isdigit()]
            
            if len(inst_parts) < 3:
                inst_parts += [0] * (3 - len(inst_parts))
            if len(req_parts) < 3:
                req_parts += [0] * (3 - len(req_parts))
            
            inst_tuple = tuple(inst_parts)
            req_tuple = tuple(req_parts)
            
            if req_op == '==':
                return inst_tuple == req_tuple
            elif req_op == '>=':
                return inst_tuple >= req_tuple
            elif req_op == '<=':
                return inst_tuple <= req_tuple
            elif req_op == '>':
                return inst_tuple > req_tuple
            elif req_op == '<':
                return inst_tuple < req_tuple
            elif req_op == '!=':
                return inst_tuple != req_tuple
            elif req_op == '~=':
                # 兼容版本：主版本号相同，次版本号大于等于
                return inst_tuple[0] == req_tuple[0] and inst_tuple[1] >= req_tuple[1]
            
            return True
        except Exception as e:
            warning(f"版本比较失败: {e}")
            return True  # 如果比较失败，默认认为满足要求
    
    def install_packages(self, packages: Dict[str, str]) -> bool:
        """
        安装包
        
        Args:
            packages: 要安装的包字典
            
        Returns:
            是否安装成功
        """
        if not packages:
            info("没有需要安装的包")
            return True
        
        # 构建pip安装命令
        install_args = [sys.executable, '-m', 'pip', 'install']
        
        index_url = get_config("dependency_installer.pip_index_url", "https://pypi.org/simple/")
        if index_url:
            install_args.extend(['--index-url', index_url])
        
        trusted_host = get_config("dependency_installer.pip_trusted_host", "")
        if trusted_host:
            install_args.extend(['--trusted-host', trusted_host])
        
        # 添加包名和版本要求
        for package_name, version_req in packages.items():
            package_spec = package_name + version_req
            install_args.append(package_spec)
        
        info(f"正在安装依赖: {list(packages.keys())}")
        
        try:
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                check=True
            )
            
            info(f"依赖安装成功: {list(packages.keys())}")
            info(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            error(f"依赖安装失败: {e}")
            error(e.stderr)
            return False
        except Exception as e:
            error(f"执行pip命令时发生错误: {e}")
            return False
    
    def install_from_requirements(self, requirements_file: str) -> bool:
        """
        从requirements文件安装依赖
        
        Args:
            requirements_file: requirements文件路径
            
        Returns:
            是否安装成功
        """
        index_url = get_config("dependency_installer.pip_index_url", "https://pypi.org/simple/")
        trusted_host = get_config("dependency_installer.pip_trusted_host", "")
        
        install_args = [sys.executable, '-m', 'pip', 'install', '-r', requirements_file]
        
        if index_url:
            install_args.extend(['--index-url', index_url])
        
        if trusted_host:
            install_args.extend(['--trusted-host', trusted_host])
        
        try:
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                check=True
            )
            
            info(f"从 {requirements_file} 安装依赖成功")
            info(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            error(f"从 {requirements_file} 安装依赖失败: {e}")
            error(e.stderr)
            return False
        except Exception as e:
            error(f"执行pip命令时发生错误: {e}")
            return False