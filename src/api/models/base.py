from abc import ABC, abstractmethod
import cv2
import numpy as np
from typing import Tuple, Dict, Any

class BaseModel(ABC):
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.input_size = (224, 224)  # 默认输入大小
        self.load_model()

    @abstractmethod
    def load_model(self):
        """加载模型"""
        pass

    @abstractmethod
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        pass

    @abstractmethod
    def postprocess(self, output: Any) -> Dict[str, Any]:
        """结果后处理"""
        pass

    @abstractmethod
    def inference(self, image: np.ndarray) -> Tuple[Dict[str, Any], float]:
        """执行推理"""
        pass

    def process_image(self, image_path: str) -> Tuple[Dict[str, Any], float]:
        """处理图像并返回结果"""
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")

        # 执行推理
        result, inference_time = self.inference(image)
        return result, inference_time

    def draw_result(self, image: np.ndarray, result: Dict[str, Any]) -> np.ndarray:
        """在图像上绘制结果"""
        return image  # 默认实现，子类可以重写 