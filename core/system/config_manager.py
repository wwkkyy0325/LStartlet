"""
系统配置管理器 - 根据系统信息生成和管理配置
"""

import os
import platform
import yaml
from typing import Dict, Any, Optional, cast
from datetime import datetime

from core.logger import info, warning, error
from core.config import get_config, register_config
from core.path import get_project_root
from .system_detector import SystemDetector


class SystemConfigManager:
    """系统配置管理器"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or get_project_root()
        self.system_detector = SystemDetector(project_root)
        
        # 注册配置管理相关配置
        register_config("system_config.auto_apply", True, bool, "是否自动应用系统检测配置")
        register_config("system_config.config_file", "./system_config.yaml", str, "系统配置文件路径")
        register_config("system_config.backup_config", True, bool, "是否备份现有配置")
        
    def setup_optimal_config(self) -> bool:
        """
        根据系统信息设置最优配置
        
        Returns:
            是否成功设置配置
        """
        info("开始检测系统信息并设置最优配置")
        
        try:
            # 检测系统信息
            system_info = self.system_detector.detect_system_info()
            
            # 验证系统要求
            validation_result = self.system_detector.validate_system_requirements(system_info)
            
            if not validation_result["valid"]:
                error(f"系统不符合要求: {validation_result['issues']}")
                return False
            
            # 根据系统信息生成配置
            optimal_config = self.system_detector.generate_config_from_system(system_info)
            
            # 应用配置
            self._apply_config(optimal_config)
            
            # 保存配置到文件
            self._save_config_to_file(optimal_config, system_info)
            
            info("系统配置设置完成")
            return True
            
        except Exception as e:
            error(f"设置系统配置时出错: {e}")
            return False
    
    def _apply_config(self, config: Dict[str, Any]) -> None:
        """应用配置到系统"""
        info("应用系统配置")
        
        # 应用配置项
        for key, value in config.items():
            # 添加前缀以区分系统配置
            config_key = f"system.{key}"
            
            # 使用配置管理器设置配置项
            from core.config import get_config_manager
            config_manager = get_config_manager()
            config_manager.set_config(config_key, value)
            
            info(f"设置配置项: {config_key} = {value}")
    
    def _save_config_to_file(self, config: Dict[str, Any], system_info: Dict[str, Any]) -> None:
        """将配置保存到文件"""
        config_file = get_config("system_config.config_file", "./system_config.yaml")
        
        # 确保 config_file 是字符串
        if config_file is None:
            config_file = "./system_config.yaml"
        
        # 准备保存的数据
        data_to_save: Dict[str, Any] = {
            "generated_at": self._get_current_datetime(),
            "system_info": system_info,
            "applied_config": config,
            "platform": platform.platform(),
            "config_sources": {}  # 保存配置项的来源信息
        }
        
        # 获取每个配置项的来源信息
        from core.config import get_config_manager
        config_manager = get_config_manager()
        for key in config.keys():
            full_key = f"system.{key}"
            source = config_manager.get_config_source(full_key)
            if source:
                data_to_save["config_sources"][full_key] = source
        
        # 确保目录存在
        config_dir = os.path.dirname(config_file)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        
        # 如果启用了备份且文件存在，则备份现有文件
        if get_config("system_config.backup_config", True) and os.path.exists(config_file):
            backup_file = f"{config_file}.backup"
            os.rename(config_file, backup_file)
            info(f"备份现有配置文件到: {backup_file}")
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(data_to_save, f, indent=2, allow_unicode=True, sort_keys=False)
        
        info(f"系统配置已保存到: {config_file}")
    
    def _get_current_datetime(self) -> str:
        """获取当前日期时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def load_config_from_file(self, config_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        从文件加载系统配置
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
            
        Returns:
            加载的配置，如果失败返回None
        """
        if not config_file:
            config_file = get_config("system_config.config_file", "./system_config.yaml")
        
        # 确保 config_file 是字符串
        if config_file is None:
            config_file = "./system_config.yaml"
        
        if not os.path.exists(config_file):
            warning(f"配置文件不存在: {config_file}")
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            info(f"从文件加载配置: {config_file}")
            
            # 应用配置到系统
            if "applied_config" in data:
                applied_config = cast(Dict[str, Any], data["applied_config"])
                for key, value in applied_config.items():
                    config_key = f"system.{key}"
                    from core.config import get_config_manager
                    config_manager = get_config_manager()
                    config_manager.set_config(config_key, value)
            
            return data
        except Exception as e:
            error(f"加载配置文件时出错: {e}")
            return None
    
    def get_recommended_config(self) -> Dict[str, Any]:
        """
        获取推荐配置（不应用，只返回）
        
        Returns:
            推荐配置
        """
        info("获取推荐系统配置")
        
        try:
            # 检测系统信息
            system_info = self.system_detector.detect_system_info()
            
            # 验证系统要求
            validation_result = self.system_detector.validate_system_requirements(system_info)
            
            if not validation_result["valid"]:
                warning(f"系统可能不符合要求: {validation_result['issues']}")
            
            # 根据系统信息生成配置
            recommended_config = self.system_detector.generate_config_from_system(system_info)
            
            return recommended_config
            
        except Exception as e:
            error(f"获取推荐配置时出错: {e}")
            return {}
    
    def get_config_tracing_info(self) -> Dict[str, Any]:
        """
        获取配置项的溯源信息
        
        Returns:
            包含配置项溯源信息的字典
        """
        from core.config import get_config_manager
        config_manager = get_config_manager()
        
        tracing_info: Dict[str, Any] = {}
        
        # 获取所有以 system. 开头的配置项
        all_configs = config_manager.get_all_configs()
        for key, value in all_configs.items():
            if key.startswith("system."):
                # ConfigItem 现在没有 get_config_metadata 方法，直接返回基本信息
                tracing_info[key] = {
                    "value": value,
                    "source": config_manager.get_config_source(key) or "unknown"
                }
        
        return tracing_info