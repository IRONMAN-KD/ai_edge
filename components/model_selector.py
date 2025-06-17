#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型选择器
提供交互式模型和配置选择功能
"""

import sys
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from .model_manager import ModelManager
from utils.logging import get_logger

logger = get_logger(__name__)


class ModelSelector:
    """模型选择器"""
    
    def __init__(self, models_config_path: str = "config/models.yml"):
        """
        初始化模型选择器
        
        Args:
            models_config_path: 模型配置文件路径
        """
        self.model_manager = ModelManager(models_config_path)
        logger.info("模型选择器初始化完成")
    
    def interactive_select(self) -> Optional[Dict[str, Any]]:
        """
        交互式选择模型和配置
        
        Returns:
            选择的配置信息
        """
        print("\n" + "="*60)
        print("华为 AI Edge 智能小站 - 算法模型选择器")
        print("="*60)
        
        # 选择模式
        mode = self._select_mode()
        
        if mode == "scenario":
            return self._select_scenario()
        elif mode == "model":
            return self._select_model()
        else:
            return None
    
    def _select_mode(self) -> str:
        """选择模式"""
        print("\n请选择配置模式:")
        print("1. 场景模式 - 根据应用场景自动选择模型和配置")
        print("2. 自定义模式 - 手动选择模型和配置")
        
        while True:
            try:
                choice = input("\n请输入选择 (1/2): ").strip()
                if choice == "1":
                    return "scenario"
                elif choice == "2":
                    return "model"
                else:
                    print("无效选择，请输入 1 或 2")
            except KeyboardInterrupt:
                print("\n\n用户取消选择")
                return "cancel"
    
    def _select_scenario(self) -> Optional[Dict[str, Any]]:
        """选择场景"""
        scenarios = self.model_manager.get_available_scenarios()
        
        if not scenarios:
            print("没有可用的场景配置")
            return None
        
        print("\n可用场景:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario['id']}")
            print(f"   推荐模型: {', '.join(scenario['recommended_models'])}")
            print(f"   预设配置: {scenario['preset']}")
            print(f"   告警规则: {len(scenario['alert_rules'])} 条")
            print()
        
        while True:
            try:
                choice = input(f"请选择场景 (1-{len(scenarios)}): ").strip()
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(scenarios):
                    selected_scenario = scenarios[choice_idx]
                    scenario_id = selected_scenario['id']
                    
                    # 加载场景
                    if self.model_manager.load_scenario(scenario_id):
                        print(f"\n✓ 成功加载场景: {scenario_id}")
                        
                        # 获取当前模型信息
                        model_info = self.model_manager.get_current_model_info()
                        alert_rules = self.model_manager.get_scenario_alert_rules(scenario_id)
                        
                        return {
                            'mode': 'scenario',
                            'scenario_id': scenario_id,
                            'model_info': model_info,
                            'alert_rules': alert_rules
                        }
                    else:
                        print(f"✗ 加载场景失败: {scenario_id}")
                        return None
                else:
                    print(f"无效选择，请输入 1-{len(scenarios)}")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n用户取消选择")
                return None
    
    def _select_model(self) -> Optional[Dict[str, Any]]:
        """选择模型"""
        models = self.model_manager.get_available_models()
        
        if not models:
            print("没有可用的模型")
            return None
        
        print("\n可用模型:")
        for i, model in enumerate(models, 1):
            print(f"{i}. {model['name']} ({model['id']})")
            print(f"   类型: {model['type']}")
            print(f"   描述: {model['description']}")
            print(f"   支持类别: {', '.join(model['classes'])}")
            print(f"   输入尺寸: {model['input_size']}")
            print()
        
        # 选择模型
        while True:
            try:
                choice = input(f"请选择模型 (1-{len(models)}): ").strip()
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(models):
                    selected_model = models[choice_idx]
                    model_id = selected_model['id']
                    break
                else:
                    print(f"无效选择，请输入 1-{len(models)}")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n用户取消选择")
                return None
        
        # 选择预设
        preset_id = self._select_preset()
        
        # 加载模型
        if self.model_manager.load_model(model_id, preset_id):
            print(f"\n✓ 成功加载模型: {selected_model['name']}")
            if preset_id:
                print(f"✓ 应用预设: {preset_id}")
            
            # 获取当前模型信息
            model_info = self.model_manager.get_current_model_info()
            
            return {
                'mode': 'model',
                'model_id': model_id,
                'preset_id': preset_id,
                'model_info': model_info
            }
        else:
            print(f"✗ 加载模型失败: {selected_model['name']}")
            return None
    
    def _select_preset(self) -> Optional[str]:
        """选择预设"""
        presets = self.model_manager.get_available_presets()
        
        if not presets:
            print("没有可用的预设配置")
            return None
        
        print("\n可用预设:")
        print("0. 使用模型默认配置")
        for i, preset in enumerate(presets, 1):
            print(f"{i}. {preset['id']}")
            print(f"   描述: {preset['description']}")
            print(f"   置信度阈值: {preset['confidence_threshold']}")
            print(f"   NMS阈值: {preset['nms_threshold']}")
            if preset['input_size']:
                print(f"   输入尺寸: {preset['input_size']}")
            print()
        
        while True:
            try:
                choice = input(f"请选择预设 (0-{len(presets)}): ").strip()
                
                if choice == "0":
                    return None
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(presets):
                    return presets[choice_idx]['id']
                else:
                    print(f"无效选择，请输入 0-{len(presets)}")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n用户取消选择")
                return None
    
    def load_from_config(self, config: Dict[str, Any]) -> bool:
        """
        从配置加载模型
        
        Args:
            config: 配置信息
            
        Returns:
            是否加载成功
        """
        try:
            if config.get('mode') == 'scenario':
                scenario_id = config.get('scenario_id')
                if scenario_id:
                    return self.model_manager.load_scenario(scenario_id)
            elif config.get('mode') == 'model':
                model_id = config.get('model_id')
                preset_id = config.get('preset_id')
                if model_id:
                    return self.model_manager.load_model(model_id, preset_id)
            
            return False
        except Exception as e:
            logger.error(f"从配置加载模型失败: {e}")
            return False
    
    def get_current_model(self):
        """获取当前模型"""
        return self.model_manager.current_model
    
    def get_current_model_info(self):
        """获取当前模型信息"""
        return self.model_manager.get_current_model_info()
    
    def switch_model(self, model_id: str, preset_id: Optional[str] = None) -> bool:
        """
        切换模型
        
        Args:
            model_id: 新模型ID
            preset_id: 新预设ID
            
        Returns:
            是否切换成功
        """
        return self.model_manager.switch_model(model_id, preset_id)
    
    def list_models(self):
        """列出所有可用模型"""
        models = self.model_manager.get_available_models()
        print("\n可用模型列表:")
        for model in models:
            print(f"- {model['name']} ({model['id']})")
            print(f"  类型: {model['type']}")
            print(f"  描述: {model['description']}")
            print()
    
    def list_scenarios(self):
        """列出所有可用场景"""
        scenarios = self.model_manager.get_available_scenarios()
        print("\n可用场景列表:")
        for scenario in scenarios:
            print(f"- {scenario['id']}")
            print(f"  推荐模型: {', '.join(scenario['recommended_models'])}")
            print(f"  预设配置: {scenario['preset']}")
            print()
    
    def list_presets(self):
        """列出所有可用预设"""
        presets = self.model_manager.get_available_presets()
        print("\n可用预设列表:")
        for preset in presets:
            print(f"- {preset['id']}")
            print(f"  描述: {preset['description']}")
            print(f"  置信度阈值: {preset['confidence_threshold']}")
            print(f"  NMS阈值: {preset['nms_threshold']}")
            print()
    
    def release(self):
        """释放资源"""
        self.model_manager.release()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def main():
    """主函数 - 用于测试"""
    selector = ModelSelector()
    
    try:
        # 交互式选择
        config = selector.interactive_select()
        
        if config:
            print("\n选择的配置:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            
            # 获取当前模型
            model = selector.get_current_model()
            if model:
                print(f"\n当前模型: {model}")
        else:
            print("未选择任何配置")
    
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    finally:
        selector.release()


if __name__ == "__main__":
    main() 