"""
日志管理模块
支持结构化日志输出，适配容器化环境
"""

import logging
import sys
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger
from typing import Optional


class AtlasLogger:
    """AI Edge 系统日志管理器"""
    
    def __init__(self, name: str = "atlas_vision", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # 检查是否为容器环境
        if os.environ.get('CONTAINER_ENV') == 'true':
            # 容器环境使用JSON格式
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s',
                timestamp=True
            )
        else:
            # 本地环境使用普通格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件输出
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"vision_system_{datetime.now().strftime('%Y%m%d')}.log")
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """错误日志"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self.logger.critical(message, extra=kwargs)
    
    def log_inference(self, model_name: str, inference_time: float, 
                     confidence: float, class_name: str):
        """记录推理性能日志"""
        self.info("推理完成", 
                 model=model_name,
                 inference_time_ms=inference_time * 1000,
                 confidence=confidence,
                 class_name=class_name)
    
    def log_alert(self, alert_type: str, confidence: float, 
                  class_name: str, image_path: Optional[str] = None):
        """记录告警日志"""
        self.warning("告警触发",
                    alert_type=alert_type,
                    confidence=confidence,
                    class_name=class_name,
                    image_path=image_path)
    
    def log_push(self, protocol: str, success: bool, 
                 message: str, response_time: float = None):
        """记录推送日志"""
        self.info("推送完成",
                 protocol=protocol,
                 success=success,
                 message=message,
                 response_time_ms=response_time * 1000 if response_time else None)


# 全局日志实例
logger = AtlasLogger() 


def get_logger(name: str = None):
    """获取日志实例"""
    if name:
        return AtlasLogger(name)
    return logger


def setup_logging(level: str = "INFO"):
    """设置日志级别"""
    logger.logger.setLevel(getattr(logging, level.upper())) 