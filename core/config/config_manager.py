"""
配置管理器核心实现
提供配置注册、获取、验证、监听等功能
"""

import json
import os
from typing import Any, Dict, Optional, Callable, List, Type
# 使用项目自定义日志管理器
from core.logger import info, warning, error, debug
from .config_item import ConfigItem


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        self._config_file = config_file or "config.json"
        self._config_items: Dict[str, ConfigItem] = {}
        self._listeners: List[Callable[[str, Any, Any], None]] = []
        
        # 注册默认配置项
        self._register_default_configs()
        
        # 从文件加载配置（如果存在）
        if os.path.exists(self._config_file):
            self.load_from_file()
        
        info("配置管理器初始化完成")
    
    def _register_default_configs(self) -> None:
        """注册默认配置项"""
        # OCR相关配置
        self.register_config("ocr_engine", "paddle", str, "OCR引擎类型 (paddle/tesseract)")
        self.register_config("language", "ch", str, "识别语言 (ch/en/...)")
        self.register_config("use_gpu", False, bool, "是否使用GPU加速")
        self.register_config("gpu_id", 0, int, "GPU设备ID")
        
        # 图像预处理配置
        self.register_config("preprocess_enabled", True, bool, "是否启用图像预处理")
        self.register_config("denoise_enabled", True, bool, "是否启用降噪")
        self.register_config("binarize_enabled", True, bool, "是否启用二值化")
        self.register_config("deskew_enabled", True, bool, "是否启用倾斜校正")
        
        # 性能配置
        self.register_config("max_workers", 4, int, "最大工作线程数")
        self.register_config("batch_size", 1, int, "批处理大小")
        self.register_config("timeout", 30.0, float, "处理超时时间（秒）")
        
        # 输出配置
        self.register_config("output_format", "text", str, "输出格式 (text/json)")
        self.register_config("confidence_threshold", 0.5, float, "置信度阈值")
        self.register_config("save_debug_images", False, bool, "是否保存调试图像")
    
    def register_config(
        self, 
        key: str, 
        default_value: Any, 
        value_type: Type[Any], 
        description: str = ""
    ) -> None:
        """
        注册配置项
        
        Args:
            key: 配置项键名
            default_value: 默认值
            value_type: 值类型
            description: 描述信息
        """
        if key in self._config_items:
            warning(f"配置项 '{key}' 已存在，将被覆盖")
        
        self._config_items[key] = ConfigItem(
            key=key,
            default_value=default_value,
            current_value=default_value,
            value_type=value_type,
            description=description
        )
        debug(f"注册配置项: {key} = {default_value}")
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置项值
        
        Args:
            key: 配置项键名
            value: 配置项值
            
        Returns:
            是否设置成功
        """
        if key not in self._config_items:
            error(f"配置项 '{key}' 未注册，无法设置")
            return False
        
        config_item = self._config_items[key]
        if not config_item.validate(value):
            error(f"配置项 '{key}' 的值 '{value}' 验证失败")
            return False
        
        old_value = config_item.current_value
        config_item.current_value = value
        
        # 触发监听器
        for listener in self._listeners:
            try:
                listener(key, old_value, value)
            except Exception as e:
                error(f"配置监听器执行失败: {e}")
        
        debug(f"配置项 '{key}' 已更新: {old_value} -> {value}")
        return True
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项值
        
        Args:
            key: 配置项键名
            default: 默认值
            
        Returns:
            配置项值
        """
        if key in self._config_items:
            return self._config_items[key].current_value
        return default
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置项"""
        return {key: item.current_value for key, item in self._config_items.items()}
    
    def add_listener(self, listener: Callable[[str, Any, Any], None]) -> None:
        """
        添加配置变更监听器
        
        Args:
            listener: 监听器函数，接收(键名, 旧值, 新值)参数
        """
        self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[str, Any, Any], None]) -> bool:
        """
        移除配置变更监听器
        
        Args:
            listener: 监听器函数
            
        Returns:
            是否成功移除
        """
        try:
            self._listeners.remove(listener)
            return True
        except ValueError:
            return False
    
    def save_to_file(self, filepath: Optional[str] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            filepath: 文件路径，如果为None则使用初始化时的路径
            
        Returns:
            是否保存成功
        """
        try:
            save_path = filepath or self._config_file
            config_data = self.get_all_configs()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            info(f"配置已保存到: {filepath}")
            return True
        except Exception as e:
            error(f"保存配置失败: {e}")
            return False
    
    def load_from_file(self, filepath: Optional[str] = None) -> bool:
        """
        从文件加载配置
        
        Args:
            filepath: 文件路径，如果为None则使用初始化时的路径
            
        Returns:
            是否加载成功
        """
        try:
            load_path = filepath or self._config_file
            if not os.path.exists(load_path):
                warning(f"配置文件不存在: {filepath}")
                return False
            
            with open(load_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            success_count = 0
            for key, value in config_data.items():
                if key in self._config_items:
                    if self.set_config(key, value):
                        success_count += 1
                else:
                    warning(f"忽略未注册的配置项: {key}")
            
            info(f"从文件加载了 {success_count} 个配置项")
            return True
        except Exception as e:
            error(f"加载配置失败: {e}")
            return False
    
    def validate_all_configs(self) -> bool:
        """
        验证所有配置项
        
        Returns:
            是否全部验证通过
        """
        try:
            for config_item in self._config_items.values():
                if not config_item.validate(config_item.current_value):
                    return False
            return True
        except Exception as e:
            error(f"配置验证异常: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """重置所有配置项为默认值"""
        for config_item in self._config_items.values():
            config_item.current_value = config_item.default_value
