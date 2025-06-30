#!/usr/bin/env python3
"""
简化的API测试脚本
"""

import os
import sys

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 设置环境变量
os.environ.update({
    'MYSQL_HOST': 'localhost',
    'MYSQL_PORT': '3308',
    'MYSQL_USER': 'ai_edge_user',
    'MYSQL_PASSWORD': 'ai_edge_pass_2024',
    'MYSQL_DATABASE': 'ai_edge',
    'PLATFORM': 'cpu_arm'
})

def test_imports():
    """测试导入"""
    try:
        print("🔍 测试导入...")
        
        # 测试基础导入
        from fastapi import FastAPI
        print("✅ FastAPI导入成功")
        
        # 测试数据库导入
        from database.database import DatabaseManager
        print("✅ DatabaseManager导入成功")
        
        from database.repositories import ModelRepository
        print("✅ ModelRepository导入成功")
        
        # 测试推理引擎导入
        from inference.factory import InferenceFactory
        print("✅ InferenceFactory导入成功")
        
        from utils.platform_detector import auto_detect_platform
        print("✅ platform_detector导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_creation():
    """测试API创建"""
    try:
        print("🔍 测试API创建...")
        
        from fastapi import FastAPI
        
        app = FastAPI(title="测试API")
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "测试成功"}
        
        print("✅ API创建成功")
        return True
        
    except Exception as e:
        print(f"❌ API创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services_init():
    """测试服务初始化"""
    try:
        print("🔍 测试服务初始化...")
        
        # 测试数据库
        from database.database import DatabaseManager
        db = DatabaseManager()
        result = db.execute_query("SELECT 1", fetch='one')
        print(f"✅ 数据库初始化成功: {result}")
        
        # 测试平台检测
        from utils.platform_detector import auto_detect_platform
        platform = auto_detect_platform()
        print(f"✅ 平台检测成功: {platform}")
        
        # 测试推理引擎工厂
        from inference.factory import InferenceFactory
        supported = InferenceFactory.get_supported_platforms()
        print(f"✅ 推理引擎工厂成功: {supported}")
        
        return True
        
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 AI Edge API简化测试")
    print("=" * 50)
    
    success = True
    
    # 测试导入
    if not test_imports():
        success = False
    
    print()
    
    # 测试API创建
    if not test_api_creation():
        success = False
    
    print()
    
    # 测试服务初始化
    if not test_services_init():
        success = False
    
    print()
    print("=" * 50)
    if success:
        print("🎉 所有测试通过！可以启动完整API服务")
    else:
        print("❌ 部分测试失败")
        sys.exit(1) 