#!/usr/bin/env python3
"""
API初始化测试脚本
直接测试API服务的初始化过程
"""

import os
import sys
import asyncio

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_api_initialization():
    """测试API初始化"""
    print("🔍 测试API服务初始化...")
    
    try:
        # 导入API模块
        import api.main as api_main
        
        # 执行初始化
        print("🔄 执行服务初始化...")
        await api_main.initialize_services()
        
        # 检查初始化结果
        if api_main.inference_engine is not None:
            print("✅ 推理引擎初始化成功")
            print(f"📊 推理引擎类型: {type(api_main.inference_engine).__name__}")
            print(f"📊 模型是否加载: {api_main.inference_engine.is_loaded}")
            print(f"📊 性能统计: {api_main.inference_engine.get_performance_stats()}")
            return True
        else:
            print("❌ 推理引擎初始化失败")
            return False
            
    except Exception as e:
        print(f"❌ API初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 AI Edge API初始化测试")
    print("=" * 50)
    
    # 设置平台环境变量
    os.environ['PLATFORM'] = 'cpu_arm'
    
    # 运行异步测试
    result = asyncio.run(test_api_initialization())
    
    if result:
        print("✅ API初始化测试通过!")
    else:
        print("❌ API初始化测试失败!")
        sys.exit(1) 