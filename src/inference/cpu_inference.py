"""
CPU推理引擎
基于ONNX Runtime实现，支持x86和ARM架构的CPU推理
"""

import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from .base import InferenceEngine

logger = logging.getLogger(__name__)


class CPUInference(InferenceEngine):
    """CPU推理引擎"""
    
    def __init__(self, model_path: str, config: Dict[str, Any] = None):
        """
        初始化CPU推理引擎
        
        Args:
            model_path: ONNX模型文件路径
            config: 推理配置参数
        """
        super().__init__(model_path, config)
        
        if not ONNX_AVAILABLE:
            raise ImportError("ONNX Runtime未安装，请运行: pip install onnxruntime")
        
        self.session = None
        self.input_name = None
        self.output_names = None
        
        # CPU特定配置
        self.num_threads = self.config.get('num_threads', 4)
        self.use_fp16 = self.config.get('use_fp16', False)
        
        logger.info(f"CPU推理引擎配置: threads={self.num_threads}, fp16={self.use_fp16}")
    
    def load_model(self, model_path: str = None) -> bool:
        """
        加载ONNX模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            bool: 加载是否成功
        """
        if model_path:
            self.model_path = model_path
        
        if not os.path.exists(self.model_path):
            logger.error(f"模型文件不存在: {self.model_path}")
            return False
        
        try:
            # 配置ONNX Runtime
            providers = ['CPUExecutionProvider']
            
            # 设置会话选项
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = self.num_threads
            sess_options.inter_op_num_threads = self.num_threads
            
            # 创建推理会话
            self.session = ort.InferenceSession(
                self.model_path,
                sess_options=sess_options,
                providers=providers
            )
            
            # 获取输入输出信息
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            # 获取输入尺寸
            input_shape = self.session.get_inputs()[0].shape
            if len(input_shape) == 4:
                # 处理动态尺寸（可能是字符串）
                try:
                    height = int(input_shape[2]) if isinstance(input_shape[2], (int, float)) else 640
                    width = int(input_shape[3]) if isinstance(input_shape[3], (int, float)) else 640
                    if height > 0 and width > 0:
                        self.input_size = (height, width)
                except (ValueError, TypeError):
                    # 如果无法解析，使用默认尺寸
                    self.input_size = (640, 640)
            
            self.is_loaded = True
            logger.info(f"ONNX模型加载成功: {self.model_path}")
            logger.info(f"输入名称: {self.input_name}")
            logger.info(f"输出名称: {self.output_names}")
            logger.info(f"输入尺寸: {self.input_size}")
            
            return True
            
        except Exception as e:
            logger.error(f"ONNX模型加载失败: {e}")
            return False
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            np.ndarray: 预处理后的数据 (1, C, H, W)
        """
        # 调整尺寸
        resized = cv2.resize(image, self.input_size)
        
        # BGR转RGB
        if len(resized.shape) == 3 and resized.shape[2] == 3:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # 归一化到 [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # 转换为 (C, H, W) 格式
        transposed = np.transpose(normalized, (2, 0, 1))
        
        # 添加batch维度 (1, C, H, W)
        batched = np.expand_dims(transposed, axis=0)
        
        return batched
    
    def infer(self, input_data: np.ndarray) -> List[np.ndarray]:
        """
        模型推理
        
        Args:
            input_data: 预处理后的输入数据
            
        Returns:
            List[np.ndarray]: 推理输出结果
        """
        if not self.is_loaded:
            raise RuntimeError("模型未加载")
        
        try:
            # 执行推理
            outputs = self.session.run(
                self.output_names,
                {self.input_name: input_data}
            )
            
            return outputs
            
        except Exception as e:
            logger.error(f"推理执行失败: {e}")
            raise
    
    def postprocess(self, outputs: List[np.ndarray], original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """
        后处理，将模型输出转换为检测结果
        
        Args:
            outputs: 模型推理输出
            original_shape: 原始图像尺寸 (height, width)
            
        Returns:
            List[Dict]: 检测结果列表
        """
        if not outputs:
            return []
        
        # 假设输出格式为 (1, num_detections, 6) 其中6为 [x1, y1, x2, y2, confidence, class_id]
        # 或者 (1, num_detections, 85) YOLOv5格式 [x, y, w, h, confidence, class_probs...]
        
        detections = []
        output = outputs[0]  # 取第一个输出
        
        if len(output.shape) == 3:
            output = output[0]  # 移除batch维度
        
        # 处理不同的输出格式
        if output.shape[1] == 6:
            # 格式: [x1, y1, x2, y2, confidence, class_id]
            detections = self._process_xyxy_format(output, original_shape)
        elif output.shape[1] >= 85:
            # YOLOv5格式: [x, y, w, h, confidence, class_probs...]
            detections = self._process_yolo_format(output, original_shape)
        else:
            logger.warning(f"未知的输出格式: {output.shape}")
        
        return detections
    
    def _process_xyxy_format(self, output: np.ndarray, original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """处理xyxy格式的输出"""
        detections = []
        orig_h, orig_w = original_shape
        
        for detection in output:
            x1, y1, x2, y2, confidence, class_id = detection
            
            if confidence < self.confidence_threshold:
                continue
            
            # 坐标缩放到原始图像尺寸
            x1 = int(x1 * orig_w / self.input_size[0])
            y1 = int(y1 * orig_h / self.input_size[1])
            x2 = int(x2 * orig_w / self.input_size[0])
            y2 = int(y2 * orig_h / self.input_size[1])
            
            # 确保坐标在有效范围内
            x1 = max(0, min(x1, orig_w))
            y1 = max(0, min(y1, orig_h))
            x2 = max(0, min(x2, orig_w))
            y2 = max(0, min(y2, orig_h))
            
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': float(confidence),
                'class_id': int(class_id),
                'label': self.labels[int(class_id)] if int(class_id) < len(self.labels) else f'class_{int(class_id)}'
            })
        
        return detections
    
    def _process_yolo_format(self, output: np.ndarray, original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """处理YOLO格式的输出"""
        detections = []
        orig_h, orig_w = original_shape
        
        for detection in output:
            # YOLO格式: [x_center, y_center, width, height, confidence, class_probs...]
            x_center, y_center, width, height, obj_conf = detection[:5]
            class_probs = detection[5:]
            
            # 找到最高概率的类别
            class_id = np.argmax(class_probs)
            class_conf = class_probs[class_id]
            confidence = obj_conf * class_conf
            
            if confidence < self.confidence_threshold:
                continue
            
            # 转换为xyxy格式
            x1 = int((x_center - width / 2) * orig_w / self.input_size[0])
            y1 = int((y_center - height / 2) * orig_h / self.input_size[1])
            x2 = int((x_center + width / 2) * orig_w / self.input_size[0])
            y2 = int((y_center + height / 2) * orig_h / self.input_size[1])
            
            # 确保坐标在有效范围内
            x1 = max(0, min(x1, orig_w))
            y1 = max(0, min(y1, orig_h))
            x2 = max(0, min(x2, orig_w))
            y2 = max(0, min(y2, orig_h))
            
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': float(confidence),
                'class_id': int(class_id),
                'label': self.labels[int(class_id)] if int(class_id) < len(self.labels) else f'class_{int(class_id)}'
            })
        
        # 应用NMS
        detections = self._apply_nms(detections)
        
        return detections
    
    def _apply_nms(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用非极大值抑制"""
        if not detections:
            return detections
        
        # 转换为numpy数组进行NMS
        boxes = np.array([det['bbox'] for det in detections])
        scores = np.array([det['confidence'] for det in detections])
        
        # 使用OpenCV的NMS
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(),
            scores.tolist(),
            self.confidence_threshold,
            self.nms_threshold
        )
        
        if len(indices) > 0:
            indices = indices.flatten()
            return [detections[i] for i in indices]
        
        return []
    
    def release_resources(self):
        """释放资源"""
        super().release_resources()
        if self.session:
            self.session = None
        logger.info("CPU推理引擎资源已释放")
