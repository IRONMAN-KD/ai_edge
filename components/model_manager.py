#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器
支持动态加载和切换不同的算法模型
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from .model_inference import AtlasInference
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelConfig:
    """模型配置数据类"""
    name: str
    type: str
    model_path: str
    input_size: List[int]
    confidence_threshold: float
    nms_threshold: float
    classes: List[str]
    description: str


@dataclass
class ModelPreset:
    """模型预设配置数据类"""
    confidence_threshold: float
    nms_threshold: float
    input_size: Optional[List[int]] = None
    description: str = ""


@dataclass
class AlertRule:
    """告警规则数据类"""
    target_class: str
    min_confidence: float
    alert_message: str


@dataclass
class Scenario:
    """场景配置数据类"""
    recommended_models: List[str]
    preset: str
    alert_rules: List[AlertRule]


class ModelManager:
    """模型管理器"""
    
    def __init__(self, models_config_path: str = "config/models.yml"):
        """
        初始化模型管理器
        
        Args:
            models_config_path: 模型配置文件路径
        """
        self.models_config_path = models_config_path
        self.models: Dict[str, ModelConfig] = {}
        self.presets: Dict[str, ModelPreset] = {}
        self.scenarios: Dict[str, Scenario] = {}
        self.current_model: Optional[AtlasInference] = None
        self.current_model_name: Optional[str] = None
        self.current_preset: Optional[str] = None
        
        # 加载配置文件
        self._load_config()
        
        logger.info("模型管理器初始化完成")
    
    def _load_config(self):
        """加载模型配置文件"""
        try:
            if not os.path.exists(self.models_config_path):
                logger.warning(f"模型配置文件不存在: {self.models_config_path}")
                return
            
            with open(self.models_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 加载模型配置
            if 'models' in config:
                for model_id, model_data in config['models'].items():
                    self.models[model_id] = ModelConfig(
                        name=model_data.get('name', model_id),
                        type=model_data.get('type', 'object_detection'),
                        model_path=model_data.get('model_path', ''),
                        input_size=model_data.get('input_size', [640, 640]),
                        confidence_threshold=model_data.get('confidence_threshold', 0.5),
                        nms_threshold=model_data.get('nms_threshold', 0.4),
                        classes=model_data.get('classes', []),
                        description=model_data.get('description', '')
                    )
            
            # 加载预设配置
            if 'model_presets' in config:
                for preset_id, preset_data in config['model_presets'].items():
                    self.presets[preset_id] = ModelPreset(
                        confidence_threshold=preset_data.get('confidence_threshold', 0.5),
                        nms_threshold=preset_data.get('nms_threshold', 0.4),
                        input_size=preset_data.get('input_size'),
                        description=preset_data.get('description', '')
                    )
            
            # 加载场景配置
            if 'scenarios' in config:
                for scenario_id, scenario_data in config['scenarios'].items():
                    alert_rules = []
                    for rule_data in scenario_data.get('alert_rules', []):
                        alert_rules.append(AlertRule(
                            target_class=rule_data.get('target_class', ''),
                            min_confidence=rule_data.get('min_confidence', 0.5),
                            alert_message=rule_data.get('alert_message', '')
                        ))
                    
                    self.scenarios[scenario_id] = Scenario(
                        recommended_models=scenario_data.get('recommended_models', []),
                        preset=scenario_data.get('preset', 'balanced'),
                        alert_rules=alert_rules
                    )
            
            logger.info(f"成功加载 {len(self.models)} 个模型配置")
            logger.info(f"成功加载 {len(self.presets)} 个预设配置")
            logger.info(f"成功加载 {len(self.scenarios)} 个场景配置")
            
        except Exception as e:
            logger.error(f"加载模型配置文件失败: {e}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表
        
        Returns:
            可用模型信息列表
        """
        models_info = []
        for model_id, model_config in self.models.items():
            models_info.append({
                'id': model_id,
                'name': model_config.name,
                'type': model_config.type,
                'description': model_config.description,
                'classes': model_config.classes,
                'input_size': model_config.input_size
            })
        return models_info
    
    def get_available_presets(self) -> List[Dict[str, Any]]:
        """
        获取可用预设列表
        
        Returns:
            可用预设信息列表
        """
        presets_info = []
        for preset_id, preset_config in self.presets.items():
            presets_info.append({
                'id': preset_id,
                'description': preset_config.description,
                'confidence_threshold': preset_config.confidence_threshold,
                'nms_threshold': preset_config.nms_threshold,
                'input_size': preset_config.input_size
            })
        return presets_info
    
    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """
        获取可用场景列表
        
        Returns:
            可用场景信息列表
        """
        scenarios_info = []
        for scenario_id, scenario_config in self.scenarios.items():
            scenarios_info.append({
                'id': scenario_id,
                'recommended_models': scenario_config.recommended_models,
                'preset': scenario_config.preset,
                'alert_rules': [
                    {
                        'target_class': rule.target_class,
                        'min_confidence': rule.min_confidence,
                        'alert_message': rule.alert_message
                    }
                    for rule in scenario_config.alert_rules
                ]
            })
        return scenarios_info
    
    def load_model(self, model_id: str, preset_id: Optional[str] = None) -> bool:
        """
        加载指定模型
        
        Args:
            model_id: 模型ID
            preset_id: 预设ID，可选
            
        Returns:
            是否加载成功
        """
        try:
            if model_id not in self.models:
                logger.error(f"模型不存在: {model_id}")
                return False
            
            model_config = self.models[model_id]
            
            # 检查模型文件是否存在
            if not os.path.exists(model_config.model_path):
                logger.warning(f"模型文件不存在: {model_config.model_path}")
                # 使用模拟模式
                logger.info("使用模拟模式加载模型")
            
            # 应用预设配置
            final_config = self._apply_preset(model_config, preset_id)
            
            # 创建模型推理实例
            self.current_model = AtlasInference(
                model_path=final_config.model_path,
                input_size=final_config.input_size,
                confidence_threshold=final_config.confidence_threshold,
                nms_threshold=final_config.nms_threshold,
                classes=final_config.classes
            )
            
            self.current_model_name = model_id
            self.current_preset = preset_id
            
            logger.info(f"成功加载模型: {model_config.name}")
            if preset_id:
                logger.info(f"应用预设: {preset_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def _apply_preset(self, model_config: ModelConfig, preset_id: Optional[str]) -> ModelConfig:
        """
        应用预设配置到模型配置
        
        Args:
            model_config: 原始模型配置
            preset_id: 预设ID
            
        Returns:
            应用预设后的模型配置
        """
        if not preset_id or preset_id not in self.presets:
            return model_config
        
        preset = self.presets[preset_id]
        
        # 创建新的配置对象
        new_config = ModelConfig(
            name=model_config.name,
            type=model_config.type,
            model_path=model_config.model_path,
            input_size=preset.input_size or model_config.input_size,
            confidence_threshold=preset.confidence_threshold,
            nms_threshold=preset.nms_threshold,
            classes=model_config.classes,
            description=model_config.description
        )
        
        return new_config
    
    def load_scenario(self, scenario_id: str) -> bool:
        """
        加载场景配置
        
        Args:
            scenario_id: 场景ID
            
        Returns:
            是否加载成功
        """
        try:
            if scenario_id not in self.scenarios:
                logger.error(f"场景不存在: {scenario_id}")
                return False
            
            scenario = self.scenarios[scenario_id]
            
            # 加载推荐模型中的第一个
            if not scenario.recommended_models:
                logger.error(f"场景 {scenario_id} 没有推荐模型")
                return False
            
            recommended_model = scenario.recommended_models[0]
            
            # 加载模型和预设
            success = self.load_model(recommended_model, scenario.preset)
            
            if success:
                logger.info(f"成功加载场景: {scenario_id}")
                logger.info(f"使用模型: {recommended_model}")
                logger.info(f"使用预设: {scenario.preset}")
            
            return success
            
        except Exception as e:
            logger.error(f"加载场景失败: {e}")
            return False
    
    def get_current_model_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前模型信息
        
        Returns:
            当前模型信息
        """
        if not self.current_model or not self.current_model_name:
            return None
        
        model_config = self.models[self.current_model_name]
        
        # 应用当前预设配置
        final_config = self._apply_preset(model_config, self.current_preset)
        
        return {
            'model_id': self.current_model_name,
            'model_name': final_config.name,
            'model_type': final_config.type,
            'preset_id': self.current_preset,
            'input_size': final_config.input_size,
            'confidence_threshold': final_config.confidence_threshold,
            'nms_threshold': final_config.nms_threshold,
            'classes': final_config.classes,
            'description': final_config.description
        }
    
    def get_scenario_alert_rules(self, scenario_id: str) -> List[AlertRule]:
        """
        获取场景的告警规则
        
        Args:
            scenario_id: 场景ID
            
        Returns:
            告警规则列表
        """
        if scenario_id not in self.scenarios:
            return []
        
        return self.scenarios[scenario_id].alert_rules
    
    def switch_model(self, model_id: str, preset_id: Optional[str] = None) -> bool:
        """
        切换模型
        
        Args:
            model_id: 新模型ID
            preset_id: 新预设ID，可选
            
        Returns:
            是否切换成功
        """
        # 释放当前模型资源
        if self.current_model:
            try:
                self.current_model.cleanup()
            except:
                pass
        
        # 加载新模型
        return self.load_model(model_id, preset_id)
    
    def release(self):
        """释放资源"""
        if self.current_model:
            try:
                self.current_model.cleanup()
            except:
                pass
        
        self.current_model = None
        self.current_model_name = None
        self.current_preset = None
        
        logger.info("模型管理器资源已释放")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release() 