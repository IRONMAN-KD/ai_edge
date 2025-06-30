#!/usr/bin/env python3
"""
推理引擎测试脚本
直接测试推理引擎的初始化和加载过程
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_inference_engine():
    """测试推理引擎"""
    print("🔍 测试推理引擎初始化...")
    
    try:
        from inference.factory import InferenceFactory
        from utils.platform_detector import auto_detect_platform
        
        # 自动检测平台
        platform = auto_detect_platform()
        print(f"✅ 检测到平台: {platform}")
        
        # 查找模型文件
        model_path = None
        for root, dirs, files in os.walk("models"):
            for filename in files:
                if filename.endswith('.onnx'):
                    model_path = os.path.join(root, filename)
                    print(f"✅ 找到模型文件: {model_path}")
                    break
            if model_path:
                break
        
        if not model_path:
            print("❌ 未找到ONNX模型文件")
            return False
        
        # 创建推理引擎
        config = {
            'confidence_threshold': 0.5,
            'nms_threshold': 0.4,
            'input_size': [640, 640],
            'labels': ['person']
        }
        
        print(f"🔄 创建推理引擎: {platform}")
        engine = InferenceFactory.create_engine(
            platform=platform,
            model_path=model_path,
            config=config
        )
        
        if not engine:
            print("❌ 推理引擎创建失败")
            return False
        
        print("✅ 推理引擎创建成功")
        
        # 加载模型
        print("🔄 加载模型...")
        if engine.load_model():
            print("✅ 模型加载成功")
            
            # 测试简单推理
            print("🔄 测试推理...")
            import cv2
            import numpy as np
            
            # 创建测试图像
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            try:
                detections, inference_time = engine.detect(test_image)
                print(f"✅ 推理测试成功! 检测到 {len(detections)} 个目标，耗时 {inference_time:.4f}s")
                
                # 显示性能统计
                stats = engine.get_performance_stats()
                print(f"📊 性能统计: {stats}")
                
                return True
            except Exception as e:
                print(f"❌ 推理测试失败: {e}")
                return False
        else:
            print("❌ 模型加载失败")
            return False
            
    except Exception as e:
        print(f"❌ 推理引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 AI Edge推理引擎测试")
    print("=" * 50)
    
    if test_inference_engine():
        print("✅ 所有测试通过!")
    else:
        print("❌ 测试失败!")
        sys.exit(1) 