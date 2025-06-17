from .base import BaseModel
from .detection import DetectionModel
from .classification import ClassificationModel
from typing import List, Optional, Type

class ModelFactory:
    _model_classes = {
        'detection': DetectionModel,
        'classification': ClassificationModel
    }

    @staticmethod
    def create_model(model_type: str, model_path: str, labels: Optional[List[str]] = None, **kwargs) -> BaseModel:
        if model_type in ["detection", "object_detection"]:
            return DetectionModel(model_path=model_path, labels=labels, **kwargs)
        elif model_type == "classification":
            return ClassificationModel(model_path=model_path, labels=labels, **kwargs)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    @classmethod
    def register_model(cls, model_type: str, model_class: Type[BaseModel]):
        """
        注册新的模型类型
        
        Args:
            model_type: 模型类型名称
            model_class: 模型类
        """
        if not issubclass(model_class, BaseModel):
            raise ValueError("模型类必须继承自 BaseModel")
        cls._models[model_type] = model_class 