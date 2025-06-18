#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web应用启动脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def start_web_app():
    """启动Web应用"""
    try:
        # 设置环境变量
        os.environ.setdefault('DB_HOST', '117.72.37.51')
        os.environ.setdefault('DB_PORT', '3306')
        os.environ.setdefault('DB_USER', 'root')
        os.environ.setdefault('DB_PASSWORD', 'Lkd@2025')
        os.environ.setdefault('DB_NAME', 'ai_edge_hw')
        os.environ.setdefault('SECRET_KEY', 'your-secret-key-here-change-in-production')
        
        # 确保上传目录存在
        upload_dir = project_root / 'uploads' / 'models'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保静态文件目录存在
        static_dir = project_root / 'web' / 'static'
        static_dir.mkdir(parents=True, exist_ok=True)
        
        print("正在启动兆慧 AI Edge 智能小站管理系统...")
        print(f"项目根目录: {project_root}")
        print(f"上传目录: {upload_dir}")
        print(f"静态文件目录: {static_dir}")
        
        # 导入并启动Flask应用
        from web.app import app
        
        print("Web应用启动成功！")
        print("访问地址: http://localhost:9950")
        print("默认账号: admin / admin123")
        print("按 Ctrl+C 停止服务")
        
        app.run(host='0.0.0.0', port=9050, debug=True)
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_web_app() 
 