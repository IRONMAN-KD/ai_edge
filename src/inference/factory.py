"""
推理引擎工厂类
负责创建和管理不同平台的推理引擎实例
"""

import logging
from typing import Dict, Type, Optional, Any
from .base import InferenceEngine

logger = logging.getLogger(__name__)


class InferenceFactory:
    """推理引擎工厂类"""
    
    # 注册的推理引擎
    _engines: Dict[str, Type[InferenceEngine]] = {}
    
    @classmethod
    def register_engine(cls, platform: str, engine_class: Type[InferenceEngine]):
        """
        注册推理引擎
        
        Args:
            platform: 平台名称
            engine_class: 推理引擎类
        """
        cls._engines[platform] = engine_class
        logger.info(f"注册推理引擎: {platform} -> {engine_class.__name__}")
    
    @classmethod
    def create_engine(cls, platform: str, model_path: str, config: Dict[str, Any] = None) -> Optional[InferenceEngine]:
        """
        创建推理引擎实例
        
        Args:
            platform: 平台名称
            model_path: 模型文件路径
            config: 推理配置
            
        Returns:
            InferenceEngine: 推理引擎实例，如果平台不支持则返回None
        """
        if platform not in cls._engines:
            logger.error(f"不支持的平台: {platform}")
            logger.info(f"支持的平台: {list(cls._engines.keys())}")
            return None
        
        try:
            engine_class = cls._engines[platform]
            engine = engine_class(model_path, config)
            logger.info(f"创建推理引擎成功: {platform}")
            return engine
        except Exception as e:
            logger.error(f"创建推理引擎失败: {platform}, 错误: {e}")
            return None
    
    @classmethod
    def get_supported_platforms(cls) -> list:
        """
        获取支持的平台列表
        
        Returns:
            list: 支持的平台名称列表
        """
        return list(cls._engines.keys())
    
    @classmethod
    def is_platform_supported(cls, platform: str) -> bool:
        """
        检查平台是否支持
        
        Args:
            platform: 平台名称
            
        Returns:
            bool: 是否支持
        """
        return platform in cls._engines


# 自动导入和注册推理引擎
def _auto_register_engines():
    """自动导入和注册推理引擎"""
    try:
        # CPU推理引擎
        from .cpu_inference import CPUInference
        InferenceFactory.register_engine('cpu_x86', CPUInference)
        InferenceFactory.register_engine('cpu_arm', CPUInference)
        logger.info("CPU推理引擎注册成功")
    except ImportError as e:
        logger.warning(f"CPU推理引擎导入失败: {e}")
    
    try:
        # NVIDIA GPU推理引擎
        from .nvidia_inference import NvidiaInference
        InferenceFactory.register_engine('nvidia_gpu', NvidiaInference)
        logger.info("NVIDIA GPU推理引擎注册成功")
    except ImportError as e:
        logger.warning(f"NVIDIA GPU推理引擎导入失败: {e}")
    
    try:
        # Atlas NPU推理引擎
        from .atlas_inference import AtlasInference
        InferenceFactory.register_engine('atlas_npu', AtlasInference)
        logger.info("Atlas NPU推理引擎注册成功")
    except ImportError as e:
        logger.warning(f"Atlas NPU推理引擎导入失败: {e}")
    
    try:
        # 算能推理引擎
        from .sophon_inference import SophonInference
        InferenceFactory.register_engine('sophon', SophonInference)
        logger.info("算能推理引擎注册成功")
    except ImportError as e:
        logger.warning(f"算能推理引擎导入失败: {e}")


# 模块加载时自动注册
_auto_register_engines()
