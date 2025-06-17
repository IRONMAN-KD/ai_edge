import cv2
import numpy as np
import onnxruntime as ort
from typing import Tuple, Dict, Any, List
from .base import BaseModel

class DetectionModel(BaseModel):
    def __init__(self, model_path: str, labels_path: str, conf_threshold: float = 0.5):
        self.labels_path = labels_path
        self.conf_threshold = conf_threshold
        self.labels = self._load_labels()
        super().__init__(model_path)

    def _load_labels(self) -> list:
        """加载标签文件"""
        try:
            with open(self.labels_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines()]
        except Exception as e:
            print(f"加载标签文件失败: {e}")
            return []

    def load_model(self):
        """加载ONNX模型"""
        try:
            self.model = ort.InferenceSession(
                self.model_path,
                providers=['CPUExecutionProvider']
            )
            # 获取模型输入信息
            self.input_name = self.model.get_inputs()[0].name
            self.input_shape = self.model.get_inputs()[0].shape
            self.input_size = (self.input_shape[2], self.input_shape[3])
        except Exception as e:
            raise RuntimeError(f"加载模型失败: {e}")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        # 保存原始图像尺寸
        self.original_size = image.shape[:2]
        
        # 调整图像大小
        image = cv2.resize(image, self.input_size)
        
        # 转换为RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 归一化
        image = image.astype(np.float32) / 255.0
        
        # 调整维度顺序 (H, W, C) -> (1, C, H, W)
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, axis=0)
        
        return image

    def postprocess(self, outputs: List[np.ndarray]) -> Dict[str, Any]:
        """结果后处理"""
        # 获取检测框、置信度和类别
        boxes = outputs[0]  # [N, 4]
        scores = outputs[1]  # [N]
        class_ids = outputs[2]  # [N]
        
        # 过滤低置信度的检测结果
        mask = scores > self.conf_threshold
        boxes = boxes[mask]
        scores = scores[mask]
        class_ids = class_ids[mask]
        
        # 将检测框坐标转换回原始图像尺寸
        scale_x = self.original_size[1] / self.input_size[0]
        scale_y = self.original_size[0] / self.input_size[1]
        
        detections = []
        for box, score, class_id in zip(boxes, scores, class_ids):
            # 转换坐标
            x1, y1, x2, y2 = box
            x1 = int(x1 * scale_x)
            y1 = int(y1 * scale_y)
            x2 = int(x2 * scale_x)
            y2 = int(y2 * scale_y)
            
            # 获取类别标签
            label = self.labels[int(class_id)] if int(class_id) < len(self.labels) else f"未知类别 {int(class_id)}"
            
            detections.append({
                "box": [x1, y1, x2, y2],
                "score": float(score),
                "class_id": int(class_id),
                "label": label
            })
        
        return {
            "detections": detections,
            "count": len(detections)
        }

    def inference(self, image: np.ndarray) -> Tuple[Dict[str, Any], float]:
        """执行推理"""
        # 预处理
        input_tensor = self.preprocess(image)
        
        # 执行推理
        start_time = cv2.getTickCount()
        outputs = self.model.run(None, {self.input_name: input_tensor})
        end_time = cv2.getTickCount()
        
        # 计算推理时间（毫秒）
        inference_time = (end_time - start_time) * 1000 / cv2.getTickFrequency()
        
        # 后处理
        result = self.postprocess(outputs)
        
        return result, inference_time

    def draw_result(self, image: np.ndarray, result: Dict[str, Any]) -> np.ndarray:
        """在图像上绘制结果"""
        # 创建图像副本
        output = image.copy()
        
        # 设置绘制参数
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2
        
        # 为每个类别生成不同的颜色
        colors = {}
        
        # 绘制每个检测框
        for detection in result["detections"]:
            box = detection["box"]
            score = detection["score"]
            label = detection["label"]
            
            # 获取或生成颜色
            if label not in colors:
                colors[label] = tuple(np.random.randint(0, 255, 3).tolist())
            color = colors[label]
            
            # 绘制边界框
            cv2.rectangle(
                output,
                (box[0], box[1]),
                (box[2], box[3]),
                color,
                thickness
            )
            
            # 准备标签文本
            text = f"{label}: {score:.2f}"
            
            # 获取文本大小
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
            
            # 绘制标签背景
            cv2.rectangle(
                output,
                (box[0], box[1] - text_height - 10),
                (box[0] + text_width + 10, box[1]),
                color,
                -1
            )
            
            # 绘制标签文本
            cv2.putText(
                output,
                text,
                (box[0] + 5, box[1] - 5),
                font,
                font_scale,
                (255, 255, 255),
                thickness
            )
        
        return output 