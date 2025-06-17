import cv2
import numpy as np
import onnxruntime as ort
from typing import Tuple, Dict, Any
from .base import BaseModel

class ClassificationModel(BaseModel):
    def __init__(self, model_path: str, labels_path: str):
        self.labels_path = labels_path
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

    def postprocess(self, output: np.ndarray) -> Dict[str, Any]:
        """结果后处理"""
        # 获取预测结果
        scores = output[0]
        class_id = np.argmax(scores)
        confidence = float(scores[class_id])
        
        # 获取类别标签
        label = self.labels[class_id] if class_id < len(self.labels) else f"未知类别 {class_id}"
        
        return {
            "class_id": int(class_id),
            "label": label,
            "confidence": confidence,
            "scores": scores.tolist()
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
        result = self.postprocess(outputs[0])
        
        return result, inference_time

    def draw_result(self, image: np.ndarray, result: Dict[str, Any]) -> np.ndarray:
        """在图像上绘制结果"""
        # 创建图像副本
        output = image.copy()
        
        # 准备文本
        label = result["label"]
        confidence = result["confidence"]
        text = f"{label}: {confidence:.2f}"
        
        # 设置文本参数
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        color = (0, 255, 0)  # 绿色
        
        # 获取文本大小
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 绘制背景矩形
        cv2.rectangle(
            output,
            (10, 10),
            (10 + text_width + 20, 10 + text_height + 20),
            (0, 0, 0),
            -1
        )
        
        # 绘制文本
        cv2.putText(
            output,
            text,
            (20, 20 + text_height),
            font,
            font_scale,
            color,
            thickness
        )
        
        return output 