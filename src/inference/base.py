"""
推理引擎基类
定义统一的推理接口，所有平台的推理引擎都需要继承此基类
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class InferenceEngine(ABC):
    """推理引擎基类"""
    
    def __init__(self, model_path: str, config: Dict[str, Any] = None):
        """
        初始化推理引擎
        
        Args:
            model_path: 模型文件路径
            config: 推理配置参数
        """
        # 处理模型路径，确保兼容本地和容器环境
        try:
            from utils.config_parser import ConfigParser
            config_parser = ConfigParser()
            self.model_path = config_parser.get_compatible_model_path(model_path)
            logger.info(f"模型路径(兼容模式): {self.model_path}")
        except ImportError:
            # 如果无法导入ConfigParser，则直接使用原始路径
            self.model_path = model_path
            logger.info(f"模型路径(原始): {self.model_path}")
            
        self.config = config or {}
        self.is_loaded = False
        self.performance_stats = {
            'total_inferences': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'last_inference_time': 0.0
        }
        
        # 从配置中获取参数
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self.nms_threshold = self.config.get('nms_threshold', 0.4)
        self.input_size = self.config.get('input_size', (640, 640))
        self.labels = self.config.get('labels', ['person'])
        
        logger.info(f"初始化推理引擎: {self.__class__.__name__}")
        logger.info(f"配置参数: {self.config}")
    
    @abstractmethod
    def load_model(self, model_path: str = None) -> bool:
        """
        加载模型
        
        Args:
            model_path: 模型文件路径，如果为None则使用初始化时的路径
            
        Returns:
            bool: 加载是否成功
        """
        pass
    
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            np.ndarray: 预处理后的数据
        """
        pass
    
    @abstractmethod
    def infer(self, input_data: np.ndarray) -> List[np.ndarray]:
        """
        模型推理
        
        Args:
            input_data: 预处理后的输入数据
            
        Returns:
            List[np.ndarray]: 推理输出结果
        """
        pass
    
    @abstractmethod
    def postprocess(self, outputs: List[np.ndarray], original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """
        后处理，将模型输出转换为检测结果
        
        Args:
            outputs: 模型推理输出
            original_shape: 原始图像尺寸 (height, width)
            
        Returns:
            List[Dict]: 检测结果列表，每个检测结果包含 bbox, confidence, class_id, label
        """
        pass
    
    def detect(self, image: np.ndarray) -> Tuple[List[Dict[str, Any]], float]:
        """
        完整的检测流程
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            Tuple[List[Dict], float]: (检测结果, 推理耗时)
        """
        if not self.is_loaded:
            raise RuntimeError("模型未加载，请先调用 load_model()")
        
        start_time = time.time()
        
        try:
            # 记录原始图像尺寸
            original_shape = image.shape[:2]  # (height, width)
            
            # 预处理
            input_data = self.preprocess(image)
            
            # 推理
            outputs = self.infer(input_data)
            
            # 后处理
            detections = self.postprocess(outputs, original_shape)
            
            # 更新性能统计
            inference_time = time.time() - start_time
            self._update_performance_stats(inference_time)
            
            logger.debug(f"检测完成，找到 {len(detections)} 个目标，耗时 {inference_time:.4f}s")
            
            return detections, inference_time
            
        except Exception as e:
            logger.error(f"检测过程出错: {e}")
            raise
    
    def _update_performance_stats(self, inference_time: float):
        """更新性能统计"""
        self.performance_stats['total_inferences'] += 1
        self.performance_stats['total_time'] += inference_time
        self.performance_stats['last_inference_time'] = inference_time
        self.performance_stats['avg_time'] = (
            self.performance_stats['total_time'] / 
            self.performance_stats['total_inferences']
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return self.performance_stats.copy()
    
    def release_resources(self):
        """释放资源"""
        logger.info(f"释放推理引擎资源: {self.__class__.__name__}")
        self.is_loaded = False
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release_resources()
