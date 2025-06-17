from typing import Dict, Type
from .base import BaseModel
from .classification import ClassificationModel
from .detection import DetectionModel

class ModelFactory:
    _models: Dict[str, Type[BaseModel]] = {
        'classification': ClassificationModel,
        'detection': DetectionModel,
    }

    @classmethod
    def create_model(cls, model_type: str, model_path: str, labels_path: str = None, **kwargs) -> BaseModel:
        """
        创建模型实例
        
        Args:
            model_type: 模型类型 ('classification' 或 'detection')
            model_path: 模型文件路径
            labels_path: 标签文件路径（对于分类和检测模型必需）
            **kwargs: 其他模型参数
        
        Returns:
            BaseModel: 模型实例
        """
        if model_type not in cls._models:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        model_class = cls._models[model_type]
        
        if model_type in ['classification', 'detection']:
            if not labels_path:
                raise ValueError(f"{model_type} 模型需要标签文件")
            return model_class(model_path, labels_path, **kwargs)
        
        return model_class(model_path, **kwargs)

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