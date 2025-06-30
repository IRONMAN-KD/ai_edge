#!/usr/bin/env python3
"""
AI Edge统一版本本地运行脚本
用于快速启动和测试系统
"""

import os
import sys
import logging
import argparse

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    try:
        import fastapi
        import uvicorn
        import numpy
        import cv2
        import onnxruntime
        print("✅ 基础依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 依赖检查失败: {e}")
        print("请运行: pip install -r requirements/base.txt -r requirements/cpu.txt")
        return False

def check_model():
    """检查模型文件"""
    print("🔍 检查模型文件...")
    
    model_path = "models/onnx/person.onnx"
    if os.path.exists(model_path):
        print(f"✅ 找到模型文件: {model_path}")
        return model_path
    else:
        print(f"❌ 模型文件不存在: {model_path}")
        return None

def test_inference_engine():
    """测试推理引擎"""
    print("🔍 测试推理引擎...")
    
    try:
        from inference.factory import InferenceFactory
        from utils.platform_detector import auto_detect_platform
        
        # 自动检测平台
        platform = auto_detect_platform()
        print(f"✅ 检测到平台: {platform}")
        
        # 检查支持的平台
        supported = InferenceFactory.get_supported_platforms()
        print(f"✅ 支持的平台: {supported}")
        
        return True
        
    except Exception as e:
        print(f"❌ 推理引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI Edge本地运行脚本")
    parser.add_argument("--port", type=int, default=8000, help="API服务端口")
    parser.add_argument("--host", default="0.0.0.0", help="API服务主机")
    parser.add_argument("--platform", help="指定平台 (cpu_x86, cpu_arm, etc.)")
    parser.add_argument("--check-only", action="store_true", help="仅检查环境，不启动服务")
    
    args = parser.parse_args()
    
    setup_logging()
    
    print("🚀 AI Edge统一版本本地运行")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 检查模型
    model_path = check_model()
    if not model_path:
        return 1
    
    # 测试推理引擎
    if not test_inference_engine():
        return 1
    
    if args.check_only:
        print("✅ 环境检查完成，所有组件正常")
        return 0
    
    # 设置环境变量
    if args.platform:
        os.environ['PLATFORM'] = args.platform
    
    # 启动API服务
    print(f"🚀 启动API服务 (http://{args.host}:{args.port})")
    
    try:
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 