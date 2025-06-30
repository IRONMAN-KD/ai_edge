#!/usr/bin/env python3
"""
测试数据库连接
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
    'MYSQL_DATABASE': 'ai_edge'
})

def test_database_connection():
    """测试数据库连接"""
    try:
        print("🔍 测试数据库连接...")
        
        # 测试mysql.connector
        import mysql.connector
        
        config = {
            'host': os.getenv('MYSQL_HOST'),
            'port': int(os.getenv('MYSQL_PORT')),
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE')
        }
        
        print(f"连接配置: {config}")
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        # 测试查询
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"✅ 数据库连接成功: {result}")
        
        # 测试表是否存在
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✅ 数据库表: {[table['Tables_in_ai_edge'] for table in tables]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_database_manager():
    """测试DatabaseManager类"""
    try:
        print("🔍 测试DatabaseManager...")
        
        from database.database import DatabaseManager
        
        db = DatabaseManager()
        result = db.execute_query("SELECT 1 as test", fetch='one')
        print(f"✅ DatabaseManager测试成功: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ DatabaseManager测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_repository():
    """测试ModelRepository"""
    try:
        print("🔍 测试ModelRepository...")
        
        from database.repositories import ModelRepository
        
        repo = ModelRepository()
        models = repo.get_all_models(page=1, page_size=5)
        print(f"✅ ModelRepository测试成功: 找到 {models['total']} 个模型")
        
        return True
        
    except Exception as e:
        print(f"❌ ModelRepository测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 AI Edge数据库连接测试")
    print("=" * 50)
    
    success = True
    
    # 测试基础连接
    if not test_database_connection():
        success = False
    
    print()
    
    # 测试DatabaseManager
    if not test_database_manager():
        success = False
    
    print()
    
    # 测试ModelRepository
    if not test_model_repository():
        success = False
    
    print()
    print("=" * 50)
    if success:
        print("🎉 所有测试通过！")
    else:
        print("❌ 部分测试失败")
        sys.exit(1) 