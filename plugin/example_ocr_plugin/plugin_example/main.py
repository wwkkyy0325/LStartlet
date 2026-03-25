"""
示例OCR插件主类 - 演示插件系统的所有基础功能
"""

import os
import json
from typing import Dict, Any
from plugin.base.plugin_base import PluginBase
from core.logger import info, warning, error
from core.decorators import with_error_handling, with_logging


class ExampleOCRPlugin(PluginBase):
    """
    示例OCR插件 - 演示完整的插件生命周期和功能集成
    """
    
    def __init__(self, plugin_id: str, name: str, version: str, description: str = ""):
        super().__init__(plugin_id, name, version, description)
        self._config_dir = None
        self._data_dir = None
        
    def get_dependencies(self) -> Dict[str, str]:
        """获取插件依赖（向后兼容）"""
        return {
            "requests": ">=2.25.0",
            "pillow": ">=8.0.0"
        }
    
    def get_provided_services(self) -> Dict[str, Any]:
        """提供服务给其他插件或主程序使用"""
        return {
            "ocr_processor": self.process_image,
            "text_analyzer": self.analyze_text
        }
    
    @with_error_handling(error_code="PLUGIN_INIT_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    def _on_initialize(self) -> bool:
        """插件初始化逻辑"""
        try:
            # 1. 创建插件专用目录
            plugin_data_dir = os.path.join("data", "plugins", self.plugin_id)
            os.makedirs(plugin_data_dir, exist_ok=True)
            self._data_dir = plugin_data_dir
            
            # 2. 加载插件配置
            config_file = os.path.join(plugin_data_dir, "config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                info(f"Loaded plugin configuration from {config_file}")
            else:
                # 创建默认配置
                default_config = {
                    "confidence_threshold": 0.8,
                    "enable_logging": True,
                    "max_workers": 2
                }
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                info(f"Created default configuration at {config_file}")
            
            # 3. 初始化内部状态
            self._initialized_components = {
                'processor': False,
                'analyzer': False,
                'logger': True
            }
            
            info(f"Example OCR Plugin initialized successfully")
            return True
            
        except Exception as e:
            error(f"Failed to initialize Example OCR Plugin: {e}")
            return False
    
    @with_error_handling(error_code="PLUGIN_START_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    def _on_start(self) -> bool:
        """插件启动逻辑"""
        try:
            # 1. 启动后台服务（如果有）
            info("Starting OCR processing service...")
            
            # 2. 验证所有组件都已正确初始化
            if not all(self._initialized_components.values()):
                warning("Some components may not be fully initialized")
            
            info("Example OCR Plugin started successfully")
            return True
            
        except Exception as e:
            error(f"Failed to start Example OCR Plugin: {e}")
            return False
    
    @with_error_handling(error_code="PLUGIN_STOP_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    def _on_stop(self) -> bool:
        """插件停止逻辑"""
        try:
            # 1. 停止后台服务
            info("Stopping OCR processing service...")
            
            # 2. 保存当前状态
            if self._data_dir is not None:
                state_file = os.path.join(self._data_dir, "plugin_state.json")
                state = {
                    "last_active": "2026-03-25T18:28:00",
                    "processed_images": 42,
                    "active_config": "default"
                }
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
            
            info("Example OCR Plugin stopped successfully")
            return True
            
        except Exception as e:
            error(f"Failed to stop Example OCR Plugin: {e}")
            return False
    
    @with_error_handling(error_code="PLUGIN_CLEANUP_ERROR", default_return=False)
    @with_logging(level="info", measure_time=True)
    def _on_cleanup(self) -> bool:
        """插件清理逻辑"""
        try:
            # 1. 释放所有资源
            if hasattr(self, '_initialized_components'):
                self._initialized_components.clear()
            
            # 2. 清理临时文件（保留配置和状态文件）
            if self._data_dir is not None:
                temp_dir = os.path.join(self._data_dir, "temp")
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
                    info(f"Cleaned up temporary directory: {temp_dir}")
            
            info("Example OCR Plugin cleaned up successfully")
            return True
            
        except Exception as e:
            error(f"Failed to cleanup Example OCR Plugin: {e}")
            return False
    
    def process_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        处理图像进行OCR识别
        
        Args:
            image_path: 图像文件路径
            **kwargs: 额外参数
            
        Returns:
            OCR结果字典
        """
        if not self._is_started:
            raise RuntimeError("Plugin is not started")
        
        confidence_threshold = kwargs.get('confidence_threshold', 0.8)
        
        # 模拟OCR处理
        result = {
            "text": "Hello World! This is a sample OCR result.",
            "confidence": 0.95,
            "bounding_boxes": [
                {"x": 10, "y": 20, "width": 100, "height": 30},
                {"x": 120, "y": 20, "width": 150, "height": 30}
            ],
            "language": "en",
            "processing_time_ms": 125
        }
        
        # 应用置信度阈值
        if result["confidence"] < confidence_threshold:
            result["text"] = ""
            result["warning"] = f"Confidence below threshold ({confidence_threshold})"
        
        # 记录处理日志
        if hasattr(self, '_initialized_components') and self._initialized_components.get('logger', False):
            info(f"Processed image: {image_path}, confidence: {result['confidence']}")
        
        return result
    
    def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        分析文本内容
        
        Args:
            text: 要分析的文本
            **kwargs: 额外参数
            
        Returns:
            文本分析结果
        """
        if not self._is_started:
            raise RuntimeError("Plugin is not started")
        
        # 模拟文本分析
        words = text.split()
        analysis = {
            "word_count": len(words),
            "character_count": len(text),
            "language_detected": "en",
            "sentiment": "neutral",
            "keywords": ["hello", "world", "sample", "ocr"],
            "entities": []
        }
        
        return analysis
    
    def _on_image_processed(self, event_data: Dict[str, Any]) -> bool:
        """
        处理图像处理完成事件
        
        Args:
            event_data: 事件数据
            
        Returns:
            处理是否成功
        """
        try:
            image_path = event_data.get('image_path')
            if image_path:
                # 对已处理的图像进行二次分析
                result = self.process_image(image_path)
                info(f"Secondary analysis completed for {image_path}")
            return True
        except Exception as e:
            error(f"Failed to handle image processed event: {e}")
            return False