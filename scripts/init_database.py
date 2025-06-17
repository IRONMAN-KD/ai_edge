#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import os
import sys
import pymysql
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def init_database():
    """初始化数据库"""
    # 数据库连接配置
    host = os.getenv('DB_HOST', '117.72.37.51')
    port = int(os.getenv('DB_PORT', 3306))
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'Lkd@2025')
    database = os.getenv('DB_NAME', 'ai_edge_hw')
    
    print(f"正在连接数据库: {host}:{port}/{database}")
    
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建数据库（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 {database} 创建成功")
            
            # 选择数据库
            cursor.execute(f"USE {database}")
            
            # 读取并执行SQL脚本
            schema_file = project_root / 'database' / 'schema.sql'
            if schema_file.exists():
                print("正在执行数据库表结构脚本...")
                with open(schema_file, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                
                # 分割SQL语句并执行
                statements = []
                current_statement = ""
                
                for line in sql_script.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('--'):
                        current_statement += line + " "
                        if line.endswith(';'):
                            statements.append(current_statement.strip())
                            current_statement = ""
                
                # 按顺序执行语句
                for statement in statements:
                    if statement:
                        try:
                            cursor.execute(statement)
                            print(f"执行SQL: {statement[:50]}...")
                        except Exception as e:
                            print(f"执行SQL失败: {e}")
                            print(f"SQL语句: {statement}")
                
                connection.commit()
                print("数据库表结构创建完成")
            else:
                print(f"警告: 未找到数据库脚本文件 {schema_file}")
        
        connection.close()
        print("数据库初始化完成！")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_database() 