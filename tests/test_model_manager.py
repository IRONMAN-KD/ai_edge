#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器单元测试
"""

import unittest
import tempfile
import yaml
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from components.model_manager import ModelManager, ModelConfig, ModelPreset, AlertRule, Scenario


class TestModelManager(unittest.TestCase):
    """模型管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_models.yml")
        
        # 创建测试配置
        self.test_config = {
            'models': {
                'yolov5': {
                    'name': 'YOLOv5 Object Detection',
                    'type': 'object_detection',
                    'model_path': '/opt/models/yolov5s.om',
                    'input_size': [640, 640],
                    'confidence_threshold': 0.5,
                    'nms_threshold': 0.4,
                    'classes': ['person', 'car'],
                    'description': 'YOLOv5目标检测模型'
                },
                'face_detection': {
                    'name': 'Face Detection',
                    'type': 'face_detection',
                    'model_path': '/opt/models/face_detection.om',
                    'input_size': [320, 320],
                    'confidence_threshold': 0.7,
                    'nms_threshold': 0.3,
                    'classes': ['face'],
                    'description': '人脸检测模型'
                }
            },
            'model_presets': {
                'high_accuracy': {
                    'confidence_threshold': 0.8,
                    'nms_threshold': 0.3,
                    'description': '高精度模式'
                },
                'balanced': {
                    'confidence_threshold': 0.6,
                    'nms_threshold': 0.4,
                    'description': '平衡模式'
                }
            },
            'scenarios': {
                'security_monitoring': {
                    'recommended_models': ['yolov5', 'face_detection'],
                    'preset': 'balanced',
                    'alert_rules': [
                        {
                            'target_class': 'person',
                            'min_confidence': 0.6,
                            'alert_message': '检测到人员活动'
                        }
                    ]
                }
            }
        }
        
        # 写入配置文件
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.test_config, f, default_flow_style=False, allow_unicode=True)
        
        # 创建模型管理器实例
        self.model_manager = ModelManager(self.config_path)
    
    def tearDown(self):
        """测试后清理"""
        # 释放资源
        if hasattr(self, 'model_manager'):
            self.model_manager.release()
        
        # 删除临时文件
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_load_config(self):
        """测试配置加载"""
        # 验证模型配置
        self.assertIn('yolov5', self.model_manager.models)
        self.assertIn('face_detection', self.model_manager.models)
        
        yolov5_config = self.model_manager.models['yolov5']
        self.assertEqual(yolov5_config.name, 'YOLOv5 Object Detection')
        self.assertEqual(yolov5_config.type, 'object_detection')
        self.assertEqual(yolov5_config.input_size, [640, 640])
        self.assertEqual(yolov5_config.confidence_threshold, 0.5)
        self.assertEqual(yolov5_config.classes, ['person', 'car'])
        
        # 验证预设配置
        self.assertIn('high_accuracy', self.model_manager.presets)
        self.assertIn('balanced', self.model_manager.presets)
        
        high_acc_preset = self.model_manager.presets['high_accuracy']
        self.assertEqual(high_acc_preset.confidence_threshold, 0.8)
        self.assertEqual(high_acc_preset.nms_threshold, 0.3)
        
        # 验证场景配置
        self.assertIn('security_monitoring', self.model_manager.scenarios)
        
        security_scenario = self.model_manager.scenarios['security_monitoring']
        self.assertEqual(security_scenario.recommended_models, ['yolov5', 'face_detection'])
        self.assertEqual(security_scenario.preset, 'balanced')
        self.assertEqual(len(security_scenario.alert_rules), 1)
        
        alert_rule = security_scenario.alert_rules[0]
        self.assertEqual(alert_rule.target_class, 'person')
        self.assertEqual(alert_rule.min_confidence, 0.6)
        self.assertEqual(alert_rule.alert_message, '检测到人员活动')
    
    def test_get_available_models(self):
        """测试获取可用模型列表"""
        models = self.model_manager.get_available_models()
        
        self.assertEqual(len(models), 2)
        
        # 验证YOLOv5模型信息
        yolov5_info = next(m for m in models if m['id'] == 'yolov5')
        self.assertEqual(yolov5_info['name'], 'YOLOv5 Object Detection')
        self.assertEqual(yolov5_info['type'], 'object_detection')
        self.assertEqual(yolov5_info['input_size'], [640, 640])
        self.assertEqual(yolov5_info['classes'], ['person', 'car'])
        
        # 验证人脸检测模型信息
        face_info = next(m for m in models if m['id'] == 'face_detection')
        self.assertEqual(face_info['name'], 'Face Detection')
        self.assertEqual(face_info['type'], 'face_detection')
        self.assertEqual(face_info['input_size'], [320, 320])
        self.assertEqual(face_info['classes'], ['face'])
    
    def test_get_available_presets(self):
        """测试获取可用预设列表"""
        presets = self.model_manager.get_available_presets()
        
        self.assertEqual(len(presets), 2)
        
        # 验证高精度预设
        high_acc_info = next(p for p in presets if p['id'] == 'high_accuracy')
        self.assertEqual(high_acc_info['confidence_threshold'], 0.8)
        self.assertEqual(high_acc_info['nms_threshold'], 0.3)
        self.assertEqual(high_acc_info['description'], '高精度模式')
        
        # 验证平衡预设
        balanced_info = next(p for p in presets if p['id'] == 'balanced')
        self.assertEqual(balanced_info['confidence_threshold'], 0.6)
        self.assertEqual(balanced_info['nms_threshold'], 0.4)
        self.assertEqual(balanced_info['description'], '平衡模式')
    
    def test_get_available_scenarios(self):
        """测试获取可用场景列表"""
        scenarios = self.model_manager.get_available_scenarios()
        
        self.assertEqual(len(scenarios), 1)
        
        # 验证安防监控场景
        security_info = scenarios[0]
        self.assertEqual(security_info['id'], 'security_monitoring')
        self.assertEqual(security_info['recommended_models'], ['yolov5', 'face_detection'])
        self.assertEqual(security_info['preset'], 'balanced')
        self.assertEqual(len(security_info['alert_rules']), 1)
        
        alert_rule = security_info['alert_rules'][0]
        self.assertEqual(alert_rule['target_class'], 'person')
        self.assertEqual(alert_rule['min_confidence'], 0.6)
        self.assertEqual(alert_rule['alert_message'], '检测到人员活动')
    
    def test_load_model(self):
        """测试加载模型"""
        # 测试加载YOLOv5模型
        success = self.model_manager.load_model('yolov5')
        self.assertTrue(success)
        self.assertIsNotNone(self.model_manager.current_model)
        self.assertEqual(self.model_manager.current_model_name, 'yolov5')
        self.assertIsNone(self.model_manager.current_preset)
        
        # 测试加载不存在的模型
        success = self.model_manager.load_model('nonexistent_model')
        self.assertFalse(success)
    
    def test_load_model_with_preset(self):
        """测试加载模型并应用预设"""
        # 测试加载YOLOv5模型并应用高精度预设
        success = self.model_manager.load_model('yolov5', 'high_accuracy')
        self.assertTrue(success)
        self.assertIsNotNone(self.model_manager.current_model)
        self.assertEqual(self.model_manager.current_model_name, 'yolov5')
        self.assertEqual(self.model_manager.current_preset, 'high_accuracy')
        
        # 验证预设配置已应用
        model_info = self.model_manager.get_current_model_info()
        self.assertEqual(model_info['preset_id'], 'high_accuracy')
    
    def test_load_scenario(self):
        """测试加载场景"""
        # 测试加载安防监控场景
        success = self.model_manager.load_scenario('security_monitoring')
        self.assertTrue(success)
        self.assertIsNotNone(self.model_manager.current_model)
        self.assertEqual(self.model_manager.current_model_name, 'yolov5')  # 第一个推荐模型
        self.assertEqual(self.model_manager.current_preset, 'balanced')
        
        # 测试加载不存在的场景
        success = self.model_manager.load_scenario('nonexistent_scenario')
        self.assertFalse(success)
    
    def test_get_current_model_info(self):
        """测试获取当前模型信息"""
        # 先加载模型
        self.model_manager.load_model('yolov5', 'high_accuracy')
        
        # 获取模型信息
        model_info = self.model_manager.get_current_model_info()
        
        self.assertIsNotNone(model_info)
        self.assertEqual(model_info['model_id'], 'yolov5')
        self.assertEqual(model_info['model_name'], 'YOLOv5 Object Detection')
        self.assertEqual(model_info['model_type'], 'object_detection')
        self.assertEqual(model_info['preset_id'], 'high_accuracy')
        self.assertEqual(model_info['input_size'], [640, 640])
        self.assertEqual(model_info['confidence_threshold'], 0.8)  # 应用了高精度预设
        self.assertEqual(model_info['nms_threshold'], 0.3)  # 应用了高精度预设
        self.assertEqual(model_info['classes'], ['person', 'car'])
    
    def test_get_scenario_alert_rules(self):
        """测试获取场景告警规则"""
        # 获取安防监控场景的告警规则
        alert_rules = self.model_manager.get_scenario_alert_rules('security_monitoring')
        
        self.assertEqual(len(alert_rules), 1)
        
        rule = alert_rules[0]
        self.assertEqual(rule.target_class, 'person')
        self.assertEqual(rule.min_confidence, 0.6)
        self.assertEqual(rule.alert_message, '检测到人员活动')
        
        # 测试不存在的场景
        alert_rules = self.model_manager.get_scenario_alert_rules('nonexistent_scenario')
        self.assertEqual(len(alert_rules), 0)
    
    def test_switch_model(self):
        """测试切换模型"""
        # 先加载YOLOv5模型
        self.model_manager.load_model('yolov5', 'balanced')
        self.assertEqual(self.model_manager.current_model_name, 'yolov5')
        self.assertEqual(self.model_manager.current_preset, 'balanced')
        
        # 切换到人脸检测模型
        success = self.model_manager.switch_model('face_detection', 'high_accuracy')
        self.assertTrue(success)
        self.assertEqual(self.model_manager.current_model_name, 'face_detection')
        self.assertEqual(self.model_manager.current_preset, 'high_accuracy')
        
        # 验证模型信息
        model_info = self.model_manager.get_current_model_info()
        self.assertEqual(model_info['model_id'], 'face_detection')
        self.assertEqual(model_info['model_name'], 'Face Detection')
        self.assertEqual(model_info['input_size'], [320, 320])
        self.assertEqual(model_info['confidence_threshold'], 0.8)  # 应用了高精度预设
        self.assertEqual(model_info['nms_threshold'], 0.3)  # 应用了高精度预设
    
    def test_apply_preset(self):
        """测试应用预设配置"""
        # 获取原始模型配置
        original_config = self.model_manager.models['yolov5']
        
        # 应用高精度预设
        modified_config = self.model_manager._apply_preset(original_config, 'high_accuracy')
        
        # 验证预设配置已应用
        self.assertEqual(modified_config.confidence_threshold, 0.8)  # 来自预设
        self.assertEqual(modified_config.nms_threshold, 0.3)  # 来自预设
        self.assertEqual(modified_config.input_size, [640, 640])  # 保持原始值
        self.assertEqual(modified_config.classes, ['person', 'car'])  # 保持原始值
        
        # 测试应用不存在的预设
        unchanged_config = self.model_manager._apply_preset(original_config, 'nonexistent_preset')
        self.assertEqual(unchanged_config.confidence_threshold, original_config.confidence_threshold)
        self.assertEqual(unchanged_config.nms_threshold, original_config.nms_threshold)
    
    def test_release(self):
        """测试释放资源"""
        # 先加载模型
        self.model_manager.load_model('yolov5')
        self.assertIsNotNone(self.model_manager.current_model)
        
        # 释放资源
        self.model_manager.release()
        
        # 验证资源已释放
        self.assertIsNone(self.model_manager.current_model)
        self.assertIsNone(self.model_manager.current_model_name)
        self.assertIsNone(self.model_manager.current_preset)


if __name__ == '__main__':
    unittest.main() 