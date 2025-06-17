"""
图像处理工具模块
支持图像预处理、后处理和格式转换
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional
from utils.logging import logger


class ImageProcessor:
    """图像处理器"""
    
    def __init__(self, target_width: int = 640, target_height: int = 640):
        self.target_width = target_width
        self.target_height = target_height
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        包括尺寸调整、归一化等
        """
        try:
            # 获取原始尺寸
            h, w = image.shape[:2]
            
            # 计算缩放比例
            scale = min(self.target_width / w, self.target_height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            # 缩放图像
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # 创建目标尺寸的画布
            canvas = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
            
            # 计算居中位置
            x_offset = (self.target_width - new_w) // 2
            y_offset = (self.target_height - new_h) // 2
            
            # 将缩放后的图像放到画布中心
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            
            # 转换为RGB格式（如果需要）
            canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
            
            # 归一化到[0,1]
            normalized = canvas_rgb.astype(np.float32) / 255.0
            
            # 转换为NCHW格式
            nchw = np.transpose(normalized, (2, 0, 1))
            
            # 添加batch维度
            batched = np.expand_dims(nchw, axis=0)
            
            return batched
            
        except Exception as e:
            logger.error(f"图像预处理失败: {e}")
            raise
    
    def postprocess_detections(self, detections: np.ndarray, 
                              original_shape: Tuple[int, int],
                              confidence_threshold: float = 0.5,
                              nms_threshold: float = 0.4) -> List[dict]:
        """
        检测结果后处理
        包括置信度过滤、NMS等
        """
        try:
            results = []
            h, w = original_shape[:2]
            
            # 解析检测结果
            for detection in detections[0]:  # 取第一个batch
                confidence = float(detection[4])
                
                if confidence < confidence_threshold:
                    continue
                
                # 获取类别和边界框
                class_scores = detection[5:]
                class_id = np.argmax(class_scores)
                class_confidence = float(class_scores[class_id])
                
                if class_confidence < confidence_threshold:
                    continue
                
                # 边界框坐标（相对于模型输入尺寸）
                x1, y1, x2, y2 = detection[:4]
                
                # 转换到原始图像尺寸
                scale_x = w / self.target_width
                scale_y = h / self.target_height
                
                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)
                
                # 确保坐标在图像范围内
                x1 = max(0, min(x1, w))
                y1 = max(0, min(y1, h))
                x2 = max(0, min(x2, w))
                y2 = max(0, min(y2, h))
                
                results.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': class_confidence,
                    'class_id': int(class_id),
                    'area': (x2 - x1) * (y2 - y1)
                })
            
            # 应用NMS
            if results:
                results = self._apply_nms(results, nms_threshold)
            
            return results
            
        except Exception as e:
            logger.error(f"检测结果后处理失败: {e}")
            return []
    
    def _apply_nms(self, detections: List[dict], threshold: float) -> List[dict]:
        """应用非极大值抑制"""
        if not detections:
            return []
        
        # 按置信度排序
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        keep = []
        while detections:
            # 保留置信度最高的检测
            current = detections.pop(0)
            keep.append(current)
            
            # 计算与其他检测的IoU
            remaining = []
            for detection in detections:
                iou = self._calculate_iou(current['bbox'], detection['bbox'])
                if iou < threshold:
                    remaining.append(detection)
            
            detections = remaining
        
        return keep
    
    def _calculate_iou(self, bbox1: List[int], bbox2: List[int]) -> float:
        """计算两个边界框的IoU"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # 计算交集
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # 计算并集
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def draw_detections(self, image: np.ndarray, detections: List[dict], 
                       class_names: List[str], colors: List[List[int]]) -> np.ndarray:
        """在图像上绘制检测结果"""
        try:
            result_image = image.copy()
            
            for detection in detections:
                bbox = detection['bbox']
                confidence = detection['confidence']
                class_id = detection['class_id']
                
                # 获取类别名称和颜色
                class_name = class_names[class_id] if class_id < len(class_names) else f"class_{class_id}"
                color = colors[class_id % len(colors)] if colors else [0, 255, 0]
                
                # 绘制边界框
                x1, y1, x2, y2 = bbox
                cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
                
                # 绘制标签
                label = f"{class_name}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                
                # 标签背景
                cv2.rectangle(result_image, 
                            (x1, y1 - label_size[1] - 10),
                            (x1 + label_size[0], y1),
                            color, -1)
                
                # 标签文字
                cv2.putText(result_image, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            return result_image
            
        except Exception as e:
            logger.error(f"绘制检测结果失败: {e}")
            return image
    
    def save_image(self, image: np.ndarray, path: str, quality: int = 95) -> bool:
        """保存图像"""
        try:
            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 保存图像
            cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            logger.info(f"图像保存成功: {path}")
            return True
            
        except Exception as e:
            logger.error(f"图像保存失败: {e}")
            return False
    
    def add_fps_info(self, image: np.ndarray, fps: float) -> np.ndarray:
        """在图像上添加FPS信息"""
        try:
            result_image = image.copy()
            fps_text = f"FPS: {fps:.1f}"
            
            cv2.putText(result_image, fps_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            return result_image
            
        except Exception as e:
            logger.error(f"添加FPS信息失败: {e}")
            return image 