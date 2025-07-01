"""
配置解析模块
支持YAML配置文件和容器化环境变量
"""

import yaml
import os
from typing import Dict, Any, Optional
from utils.logging import logger


class ContainerConfig:
    """容器化配置管理"""
    
    def __init__(self):
        self.container_env = os.environ.get('CONTAINER_ENV', 'false').lower() == 'true'
        self.device_id = int(os.environ.get('ASCEND_DEVICE_ID', '0'))
        
    def get_model_volume_path(self) -> str:
        """获取容器内模型文件路径"""
        return os.environ.get('MODEL_VOLUME_PATH', '/app/models')
    
    def get_alert_image_volume_path(self) -> str:
        """获取容器内告警图片存储路径"""
        return os.environ.get('ALERT_IMAGE_VOLUME_PATH', '/app/alert_images')
    
    def get_config_volume_path(self) -> str:
        """获取容器内配置文件路径"""
        return os.environ.get('CONFIG_VOLUME_PATH', '/app/config')
    
    def get_compatible_path(self, container_path: str) -> str:
        """获取兼容本地和容器环境的路径
        
        Args:
            container_path: 容器内路径，如 /app/models/person.onnx
            
        Returns:
            str: 根据当前环境返回兼容的路径
        """
        if not self.container_env and container_path.startswith('/app/'):
            # 本地环境，将 /app/ 替换为当前目录
            relative_path = container_path.replace('/app/', '')
            return os.path.join(os.getcwd(), relative_path)
        return container_path
    
    def ensure_directory_exists(self, path: str) -> str:
        """确保目录存在，如果不存在则创建
        
        Args:
            path: 目录路径
            
        Returns:
            str: 创建后的目录路径
        """
        # 如果是容器路径，先转换为兼容路径
        compatible_path = self.get_compatible_path(path)
        
        # 确保目录存在
        if not os.path.exists(compatible_path):
            try:
                os.makedirs(compatible_path, exist_ok=True)
                logger.info(f"创建目录: {compatible_path}")
            except Exception as e:
                logger.error(f"创建目录失败: {compatible_path}, 错误: {e}")
        
        return compatible_path


class ConfigParser:
    """配置解析器"""
    
    def __init__(self, config_path: str = None):
        self.container_config = ContainerConfig()
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self._validate_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        if self.container_config.container_env:
            return "/app/config/config.yml"
        else:
            return "config/config.yml"
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 应用容器化配置覆盖
            config = self._apply_container_overrides(config)
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            return config
            
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式错误: {e}，使用默认配置")
            return self._get_default_config()
    
    def _apply_container_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用容器化环境变量覆盖"""
        if not self.container_config.container_env:
            return config
        
        # 设备ID覆盖
        if 'system' in config:
            config['system']['device_id'] = self.container_config.device_id
        
        # 模型路径覆盖
        if 'model' in config:
            model_volume = self.container_config.get_model_volume_path()
            if os.path.exists(model_volume):
                config['model']['path'] = os.path.join(model_volume, 'model.om')
        
        # 告警图片路径覆盖
        if 'alert' in config:
            alert_volume = self.container_config.get_alert_image_volume_path()
            config['alert']['image_path'] = alert_volume
        
        logger.info("容器化配置覆盖已应用")
        return config
    
    def _validate_config(self):
        """验证配置有效性"""
        required_sections = ['system', 'model', 'video', 'alert']
        for section in required_sections:
            if section not in self.config:
                logger.warning(f"缺少配置节: {section}，将使用默认值")
        
        # 验证模型路径
        if 'model' in self.config and 'path' in self.config['model']:
            model_path = self.config['model']['path']
            if not os.path.exists(model_path):
                logger.warning(f"模型文件不存在: {model_path}")
        
        # 验证视频源
        if 'video' in self.config and 'source' in self.config['video']:
            video_source = self.config['video']['source']
            if video_source.startswith('/dev/') and not os.path.exists(video_source):
                logger.warning(f"视频设备不存在: {video_source}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self.config.get('system', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.config.get('model', {})
    
    def get_video_config(self) -> Dict[str, Any]:
        """获取视频配置"""
        return self.config.get('video', {})
    
    def get_alert_config(self) -> Dict[str, Any]:
        """获取告警配置"""
        return self.config.get('alert', {})
    
    def get_classes_config(self) -> list:
        """获取目标类别配置"""
        return self.config.get('classes', [])
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """获取MQTT配置"""
        return self.config.get('mqtt', {})
    
    def get_http_config(self) -> Dict[str, Any]:
        """获取HTTP配置"""
        return self.config.get('http', {})
    
    def get_rabbitmq_config(self) -> Dict[str, Any]:
        """获取RabbitMQ配置"""
        return self.config.get('rabbitmq', {})
    
    def get_kafka_config(self) -> Dict[str, Any]:
        """获取Kafka配置"""
        return self.config.get('kafka', {})
    
    def get_visualization_config(self) -> Dict[str, Any]:
        """获取可视化配置"""
        return self.config.get('visualization', {})
    
    def get_section(self, section_name: str) -> Optional[Dict[str, Any]]:
        """获取配置节"""
        return self.config.get(section_name)
    
    def get_compatible_model_path(self, model_path: str) -> str:
        """获取兼容本地和容器环境的模型路径
        
        Args:
            model_path: 原始模型路径
            
        Returns:
            str: 兼容的模型路径
        """
        return self.container_config.get_compatible_path(model_path)
    
    def get_alert_image_path(self) -> str:
        """获取告警图片保存路径，并确保目录存在
        
        Returns:
            str: 告警图片保存路径
        """
        # 获取配置中的告警图片路径
        alert_config = self.get_alert_config()
        alert_image_path = alert_config.get('image_path', '/app/alert_images')
        
        # 转换为兼容路径并确保目录存在
        compatible_path = self.container_config.get_compatible_path(alert_image_path)
        self.container_config.ensure_directory_exists(compatible_path)
        
        return compatible_path
    
    def is_container_env(self) -> bool:
        """是否为容器环境"""
        return self.container_config.container_env
    
    def get_device_id(self) -> int:
        """获取设备ID"""
        return self.container_config.device_id
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'system': {
                'device_id': 0,
                'log_level': 'INFO'
            },
            'model': {
                'path': 'models/default.om'
            },
            'video': {
                'source': '/dev/video0'
            },
            'alert': {
                'image_path': 'alert_images'
            }
        } 