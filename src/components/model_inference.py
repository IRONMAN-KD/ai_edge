"""
模型推理模块
集成华为 Atlas SDK 进行 NPU 推理
"""

import os
import time
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from utils.logging import logger
from utils.config_parser import ConfigParser

try:
    import acl
    import aclruntime
    ATLAS_AVAILABLE = True
except ImportError:
    ATLAS_AVAILABLE = False
    logger.warning("华为 Atlas SDK 未安装，将使用模拟模式")


class AtlasInference:
    """Atlas NPU 推理引擎"""
    
    def __init__(self, config: ConfigParser = None, model_path: str = None, 
                 input_size: List[int] = None, confidence_threshold: float = 0.5,
                 nms_threshold: float = 0.4, classes: List[str] = None,
                 device_id: int = 0, batch_size: int = 1):
        """
        初始化Atlas推理引擎
        
        Args:
            config: 配置解析器对象（可选）
            model_path: 模型文件路径
            input_size: 输入尺寸 [width, height]
            confidence_threshold: 置信度阈值
            nms_threshold: NMS阈值
            classes: 类别列表
            device_id: 设备ID
            batch_size: 批处理大小
        """
        # 优先使用直接参数，如果没有则从config获取
        if config is not None:
            self.config = config
            self.device_id = config.get_device_id()
            self.model_path = config.get('model.path', model_path)
            self.input_width = config.get('model.input_width', input_size[0] if input_size else 640)
            self.input_height = config.get('model.input_height', input_size[1] if input_size else 640)
            self.batch_size = config.get('model.batch_size', batch_size)
        else:
            self.config = None
            self.device_id = device_id
            self.model_path = model_path or "/opt/models/default.om"
            self.input_width = input_size[0] if input_size else 640
            self.input_height = input_size[1] if input_size else 640
            self.batch_size = batch_size
        
        # 模型参数
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.classes = classes or []
        
        # Atlas 相关资源
        self.context = None
        self.stream = None
        self.model = None
        self.input_buffer = None
        self.output_buffer = None
        
        # 性能统计
        self.inference_count = 0
        self.total_inference_time = 0.0
        
        # 初始化 Atlas 环境
        self._init_atlas()
    
    def _init_atlas(self):
        """初始化 Atlas 环境"""
        if not ATLAS_AVAILABLE:
            logger.warning("使用模拟模式，跳过 Atlas 初始化")
            return
        
        try:
            # 初始化 ACL
            ret = acl.init()
            if ret != 0:
                raise RuntimeError(f"ACL 初始化失败: {ret}")
            
            # 设置设备
            ret = acl.rt.set_device(self.device_id)
            if ret != 0:
                raise RuntimeError(f"设置设备失败: {ret}")
            
            # 创建上下文
            self.context, ret = acl.rt.create_context(self.device_id)
            if ret != 0:
                raise RuntimeError(f"创建上下文失败: {ret}")
            
            # 创建流
            self.stream, ret = acl.rt.create_stream()
            if ret != 0:
                raise RuntimeError(f"创建流失败: {ret}")
            
            # 加载模型
            self._load_model()
            
            logger.info(f"Atlas 环境初始化成功，设备ID: {self.device_id}")
            
        except Exception as e:
            logger.error(f"Atlas 环境初始化失败: {e}")
            raise
    
    def _load_model(self):
        """加载模型"""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
            
            # 创建模型实例
            self.model = aclruntime.InferenceSession(
                self.model_path, 
                self.device_id
            )
            
            # 获取模型输入输出信息
            self.input_info = self.model.get_inputs()
            self.output_info = self.model.get_outputs()
            
            logger.info(f"模型加载成功: {self.model_path}")
            logger.info(f"输入信息: {self.input_info}")
            logger.info(f"输出信息: {self.output_info}")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        try:
            # 确保输入格式正确
            if len(image.shape) != 4:
                image = np.expand_dims(image, axis=0)
            
            # 确保数据类型为 float32
            if image.dtype != np.float32:
                image = image.astype(np.float32)
            
            return image
            
        except Exception as e:
            logger.error(f"预处理失败: {e}")
            raise
    
    def inference(self, image: np.ndarray) -> np.ndarray:
        """执行推理"""
        if not ATLAS_AVAILABLE:
            return self._mock_inference(image)
        
        try:
            start_time = time.time()
            
            # 预处理
            processed_image = self.preprocess(image)
            
            # 执行推理
            outputs = self.model.run([processed_image])
            
            # 获取输出结果
            result = outputs[0]  # 假设只有一个输出
            
            # 计算推理时间
            inference_time = time.time() - start_time
            self._update_stats(inference_time)
            
            logger.debug(f"推理完成，耗时: {inference_time*1000:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"推理失败: {e}")
            raise
    
    def _mock_inference(self, image: np.ndarray) -> np.ndarray:
        """模拟推理（用于测试）"""
        time.sleep(0.01)  # 模拟推理时间
        
        # 生成模拟检测结果
        h, w = image.shape[2:4]
        mock_detections = np.zeros((1, 100, 85))  # 假设输出格式
        
        # 添加一些模拟检测框
        for i in range(3):
            x1 = np.random.randint(0, w//2)
            y1 = np.random.randint(0, h//2)
            x2 = x1 + np.random.randint(50, 200)
            y2 = y1 + np.random.randint(50, 200)
            confidence = np.random.uniform(0.6, 0.9)
            
            mock_detections[0, i, :4] = [x1, y1, x2, y2]
            mock_detections[0, i, 4] = confidence
            mock_detections[0, i, 5 + i % 80] = confidence
        
        return mock_detections
    
    def _update_stats(self, inference_time: float):
        """更新性能统计"""
        self.inference_count += 1
        self.total_inference_time += inference_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if self.inference_count == 0:
            return {
                'total_inferences': 0,
                'avg_inference_time': 0.0,
                'fps': 0.0
            }
        
        avg_time = self.total_inference_time / self.inference_count
        fps = 1.0 / avg_time if avg_time > 0 else 0.0
        
        return {
            'total_inferences': self.inference_count,
            'avg_inference_time': avg_time,
            'fps': fps
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'model_path': self.model_path,
            'input_width': self.input_width,
            'input_height': self.input_height,
            'batch_size': self.batch_size,
            'device_id': self.device_id,
            'atlas_available': ATLAS_AVAILABLE
        }
    
    def cleanup(self):
        """清理资源"""
        try:
            if ATLAS_AVAILABLE and self.model:
                del self.model
                self.model = None
            
            if ATLAS_AVAILABLE and self.stream:
                acl.rt.destroy_stream(self.stream)
                self.stream = None
            
            if ATLAS_AVAILABLE and self.context:
                acl.rt.destroy_context(self.context)
                self.context = None
            
            if ATLAS_AVAILABLE:
                acl.rt.reset_device(self.device_id)
                acl.rt.set_device(self.device_id)
                acl.finalize()
            
            logger.info("Atlas 资源清理完成")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")


class ModelManager:
    """模型管理器"""
    
    def __init__(self, config: ConfigParser):
        self.config = config
        self.inference_engine = None
        self.class_names = []
        self.class_colors = []
        self.class_thresholds = {}
        
        self._load_class_config()
        self._init_inference_engine()
    
    def _load_class_config(self):
        """加载类别配置"""
        classes_config = self.config.get_classes_config()
        
        for class_config in classes_config:
            name = class_config.get('name', 'unknown')
            threshold = class_config.get('threshold', 0.5)
            color = class_config.get('color', [0, 255, 0])
            
            self.class_names.append(name)
            self.class_colors.append(color)
            self.class_thresholds[name] = threshold
        
        logger.info(f"加载了 {len(self.class_names)} 个目标类别")
    
    def _init_inference_engine(self):
        """初始化推理引擎"""
        try:
            self.inference_engine = AtlasInference(self.config)
            logger.info("推理引擎初始化成功")
        except Exception as e:
            logger.error(f"推理引擎初始化失败: {e}")
            raise
    
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """执行目标检测"""
        try:
            # 执行推理
            raw_output = self.inference_engine.inference(image)
            
            # 后处理
            detections = self._postprocess_detections(raw_output, image.shape)
            
            return detections
            
        except Exception as e:
            logger.error(f"目标检测失败: {e}")
            return []
    
    def _postprocess_detections(self, raw_output: np.ndarray, 
                               original_shape: Tuple[int, ...]) -> List[Dict[str, Any]]:
        """后处理检测结果"""
        try:
            from utils.image_utils import ImageProcessor
            
            # 创建图像处理器
            processor = ImageProcessor(
                self.config.get('model.input_width', 640),
                self.config.get('model.input_height', 640)
            )
            
            # 后处理
            detections = processor.postprocess_detections(
                raw_output,
                original_shape,
                self.config.get('model.confidence_threshold', 0.5),
                self.config.get('model.nms_threshold', 0.4)
            )
            
            # 添加类别信息
            for detection in detections:
                class_id = detection['class_id']
                if class_id < len(self.class_names):
                    detection['class_name'] = self.class_names[class_id]
                    detection['threshold'] = self.class_thresholds.get(
                        self.class_names[class_id], 0.5
                    )
                else:
                    detection['class_name'] = f"class_{class_id}"
                    detection['threshold'] = 0.5
            
            return detections
            
        except Exception as e:
            logger.error(f"后处理失败: {e}")
            return []
    
    def get_class_info(self) -> Dict[str, Any]:
        """获取类别信息"""
        return {
            'class_names': self.class_names,
            'class_colors': self.class_colors,
            'class_thresholds': self.class_thresholds
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if self.inference_engine:
            return self.inference_engine.get_performance_stats()
        return {}
    
    def cleanup(self):
        """清理资源"""
        if self.inference_engine:
            self.inference_engine.cleanup() 