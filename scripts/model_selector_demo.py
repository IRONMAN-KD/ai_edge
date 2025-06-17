#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型选择器演示脚本
展示如何使用模型选择功能
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.model_selector import ModelSelector
from utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


def demo_interactive_selection():
    """演示交互式模型选择"""
    print("\n" + "="*60)
    print("模型选择器演示 - 交互式选择")
    print("="*60)
    
    with ModelSelector() as selector:
        # 交互式选择
        config = selector.interactive_select()
        
        if config:
            print("\n✓ 选择成功!")
            print("配置详情:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            
            # 获取当前模型信息
            model_info = selector.get_current_model_info()
            if model_info:
                print(f"\n当前模型信息:")
                print(f"  模型ID: {model_info['model_id']}")
                print(f"  模型名称: {model_info['model_name']}")
                print(f"  模型类型: {model_info['model_type']}")
                print(f"  预设ID: {model_info['preset_id']}")
                print(f"  输入尺寸: {model_info['input_size']}")
                print(f"  置信度阈值: {model_info['confidence_threshold']}")
                print(f"  NMS阈值: {model_info['nms_threshold']}")
                print(f"  支持类别: {model_info['classes']}")
        else:
            print("\n✗ 选择失败或用户取消")


def demo_programmatic_selection():
    """演示程序化模型选择"""
    print("\n" + "="*60)
    print("模型选择器演示 - 程序化选择")
    print("="*60)
    
    with ModelSelector() as selector:
        # 列出可用模型
        print("\n1. 列出所有可用模型:")
        selector.list_models()
        
        # 列出可用场景
        print("\n2. 列出所有可用场景:")
        selector.list_scenarios()
        
        # 列出可用预设
        print("\n3. 列出所有可用预设:")
        selector.list_presets()
        
        # 程序化加载场景
        print("\n4. 程序化加载场景:")
        scenario_config = {
            'mode': 'scenario',
            'scenario_id': 'security_monitoring'
        }
        
        if selector.load_from_config(scenario_config):
            print("✓ 成功加载安防监控场景")
            model_info = selector.get_current_model_info()
            print(f"  使用模型: {model_info['model_name']}")
            print(f"  使用预设: {model_info['preset_id']}")
        else:
            print("✗ 加载场景失败")
        
        # 程序化切换模型
        print("\n5. 程序化切换模型:")
        if selector.switch_model('yolov8', 'high_accuracy'):
            print("✓ 成功切换到YOLOv8高精度模式")
            model_info = selector.get_current_model_info()
            print(f"  当前模型: {model_info['model_name']}")
            print(f"  当前预设: {model_info['preset_id']}")
        else:
            print("✗ 切换模型失败")


def demo_model_comparison():
    """演示模型比较"""
    print("\n" + "="*60)
    print("模型选择器演示 - 模型比较")
    print("="*60)
    
    with ModelSelector() as selector:
        models = selector.model_manager.get_available_models()
        
        print("\n模型对比表:")
        print("-" * 80)
        print(f"{'模型名称':<20} {'类型':<15} {'输入尺寸':<12} {'支持类别数':<10}")
        print("-" * 80)
        
        for model in models:
            class_count = len(model['classes'])
            input_size_str = f"{model['input_size'][0]}x{model['input_size'][1]}"
            print(f"{model['name']:<20} {model['type']:<15} {input_size_str:<12} {class_count:<10}")
        
        print("-" * 80)
        
        # 比较预设配置
        print("\n预设配置对比:")
        print("-" * 60)
        print(f"{'预设名称':<15} {'置信度阈值':<12} {'NMS阈值':<10} {'描述':<20}")
        print("-" * 60)
        
        presets = selector.model_manager.get_available_presets()
        for preset in presets:
            print(f"{preset['id']:<15} {preset['confidence_threshold']:<12.2f} {preset['nms_threshold']:<10.2f} {preset['description']:<20}")
        
        print("-" * 60)


def demo_scenario_analysis():
    """演示场景分析"""
    print("\n" + "="*60)
    print("模型选择器演示 - 场景分析")
    print("="*60)
    
    with ModelSelector() as selector:
        scenarios = selector.model_manager.get_available_scenarios()
        
        for scenario in scenarios:
            scenario_id = scenario['id']
            print(f"\n场景: {scenario_id}")
            print(f"  推荐模型: {', '.join(scenario['recommended_models'])}")
            print(f"  预设配置: {scenario['preset']}")
            print(f"  告警规则:")
            
            for rule in scenario['alert_rules']:
                print(f"    - 目标类别: {rule['target_class']}")
                print(f"      最小置信度: {rule['min_confidence']}")
                print(f"      告警消息: {rule['alert_message']}")
            
            # 加载场景并获取详细信息
            if selector.load_from_config({'mode': 'scenario', 'scenario_id': scenario_id}):
                model_info = selector.get_current_model_info()
                print(f"  当前模型: {model_info['model_name']}")
                print(f"  模型类型: {model_info['model_type']}")
                print(f"  输入尺寸: {model_info['input_size']}")
                print(f"  置信度阈值: {model_info['confidence_threshold']}")
                print(f"  NMS阈值: {model_info['nms_threshold']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="模型选择器演示脚本")
    parser.add_argument(
        "--demo", 
        choices=["interactive", "programmatic", "comparison", "scenario", "all"],
        default="all",
        help="选择演示类型"
    )
    
    args = parser.parse_args()
    
    # 初始化日志
    setup_logging()
    
    try:
        if args.demo == "interactive":
            demo_interactive_selection()
        elif args.demo == "programmatic":
            demo_programmatic_selection()
        elif args.demo == "comparison":
            demo_model_comparison()
        elif args.demo == "scenario":
            demo_scenario_analysis()
        elif args.demo == "all":
            demo_interactive_selection()
            demo_programmatic_selection()
            demo_model_comparison()
            demo_scenario_analysis()
        
        print("\n" + "="*60)
        print("演示完成!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"\n演示失败: {e}")


if __name__ == "__main__":
    main() 