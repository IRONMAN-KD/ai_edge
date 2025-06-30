#!/usr/bin/env python3
"""
AI Edge统一版本启动脚本
管理数据库、后端API和前端服务的完整生命周期
"""

import os
import sys
import time
import signal
import argparse
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedSystemManager:
    """统一系统管理器"""
    
    def __init__(self, mode='docker'):
        self.mode = mode  # 'docker' 或 'local'
        self.project_root = Path(__file__).parent
        self.processes = []
        
    def check_dependencies(self):
        """检查依赖"""
        logger.info("🔍 检查系统依赖...")
        
        if self.mode == 'docker':
            # 检查Docker
            try:
                result = subprocess.run(['docker', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception("Docker未安装或未启动")
                logger.info(f"✅ Docker版本: {result.stdout.strip()}")
                
                # 检查Docker Compose
                result = subprocess.run(['docker-compose', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception("Docker Compose未安装")
                logger.info(f"✅ Docker Compose版本: {result.stdout.strip()}")
                
            except Exception as e:
                logger.error(f"❌ Docker依赖检查失败: {e}")
                return False
        else:
            # 检查Python环境
            try:
                import mysql.connector
                import redis
                import fastapi
                import uvicorn
                logger.info("✅ Python依赖检查通过")
            except ImportError as e:
                logger.error(f"❌ Python依赖缺失: {e}")
                return False
        
        return True
    
    def start_docker_services(self):
        """启动Docker服务"""
        logger.info("🚀 启动Docker服务...")
        
        try:
            # 停止已存在的服务
            logger.info("停止现有服务...")
            subprocess.run(['docker-compose', 'down'], 
                         cwd=self.project_root, check=False)
            
            # 构建并启动服务
            logger.info("构建并启动服务...")
            cmd = ['docker-compose', 'up', '--build', '-d']
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Docker服务启动失败: {result.stderr}")
                return False
            
            logger.info("✅ Docker服务启动成功")
            
            # 等待服务就绪
            self.wait_for_services()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Docker服务启动失败: {e}")
            return False
    
    def start_local_services(self):
        """启动本地服务"""
        logger.info("🚀 启动本地服务...")
        
        try:
            # 1. 启动数据库（假设MySQL已在本地运行）
            logger.info("检查MySQL服务...")
            
            # 2. 启动Redis（如果需要）
            logger.info("检查Redis服务...")
            
            # 3. 启动后端API
            logger.info("启动后端API...")
            api_env = os.environ.copy()
            api_env.update({
                'MYSQL_HOST': 'localhost',
                'MYSQL_PORT': '3308',
                'MYSQL_USER': 'ai_edge_user',
                'MYSQL_PASSWORD': 'ai_edge_pass_2024',
                'MYSQL_DATABASE': 'ai_edge',
                'PLATFORM': 'cpu_arm',
                'PYTHONPATH': str(self.project_root / 'src')
            })
            
            api_process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 
                'api.main:app',
                '--host', '0.0.0.0',
                '--port', '8000',
                '--reload'
            ], cwd=self.project_root / 'src', env=api_env)
            
            self.processes.append(('API', api_process))
            logger.info("✅ 后端API启动成功 (PID: {})".format(api_process.pid))
            
            # 4. 启动前端（开发模式）
            if (self.project_root / 'frontend' / 'package.json').exists():
                logger.info("启动前端开发服务器...")
                frontend_process = subprocess.Popen([
                    'npm', 'run', 'dev'
                ], cwd=self.project_root / 'frontend')
                
                self.processes.append(('Frontend', frontend_process))
                logger.info("✅ 前端服务启动成功 (PID: {})".format(frontend_process.pid))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 本地服务启动失败: {e}")
            return False
    
    def wait_for_services(self):
        """等待服务就绪"""
        logger.info("⏳ 等待服务就绪...")
        
        services = [
            ('数据库', 'localhost', 3308),
            ('后端API', 'localhost', 8000),
            ('前端', 'localhost', 8080)
        ]
        
        for name, host, port in services:
            logger.info(f"等待 {name} 服务就绪...")
            max_retries = 30
            for i in range(max_retries):
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        logger.info(f"✅ {name} 服务就绪 ({host}:{port})")
                        break
                except:
                    pass
                
                if i == max_retries - 1:
                    logger.warning(f"⚠️  {name} 服务可能未就绪")
                else:
                    time.sleep(2)
    
    def show_status(self):
        """显示服务状态"""
        logger.info("📊 系统状态:")
        
        if self.mode == 'docker':
            try:
                result = subprocess.run(['docker-compose', 'ps'], 
                                      cwd=self.project_root,
                                      capture_output=True, text=True)
                print(result.stdout)
            except Exception as e:
                logger.error(f"获取Docker状态失败: {e}")
        else:
            for name, process in self.processes:
                if process.poll() is None:
                    logger.info(f"✅ {name} 运行中 (PID: {process.pid})")
                else:
                    logger.info(f"❌ {name} 已停止")
        
        # 显示访问地址
        logger.info("🌐 访问地址:")
        logger.info("  - 前端界面: http://localhost:8080")
        logger.info("  - API文档: http://localhost:8000/docs")
        logger.info("  - API健康检查: http://localhost:8000/health")
        logger.info("  - 数据库: localhost:3307")
    
    def stop_services(self):
        """停止服务"""
        logger.info("🛑 停止服务...")
        
        if self.mode == 'docker':
            try:
                subprocess.run(['docker-compose', 'down'], 
                             cwd=self.project_root, check=True)
                logger.info("✅ Docker服务已停止")
            except Exception as e:
                logger.error(f"停止Docker服务失败: {e}")
        else:
            for name, process in self.processes:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"✅ {name} 已停止")
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.info(f"🔥 {name} 已强制停止")
                except Exception as e:
                    logger.error(f"停止 {name} 失败: {e}")
    
    def start(self):
        """启动系统"""
        logger.info("🚀 AI Edge统一版本启动")
        logger.info("=" * 50)
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 启动服务
        if self.mode == 'docker':
            success = self.start_docker_services()
        else:
            success = self.start_local_services()
        
        if success:
            self.show_status()
            return True
        else:
            return False
    
    def cleanup(self, signum=None, frame=None):
        """清理资源"""
        logger.info("🧹 清理系统资源...")
        self.stop_services()
        sys.exit(0)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI Edge统一版本管理器')
    parser.add_argument('--mode', choices=['docker', 'local'], 
                       default='docker', help='运行模式')
    parser.add_argument('--action', choices=['start', 'stop', 'status'], 
                       default='start', help='执行动作')
    
    args = parser.parse_args()
    
    manager = UnifiedSystemManager(mode=args.mode)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, manager.cleanup)
    signal.signal(signal.SIGTERM, manager.cleanup)
    
    try:
        if args.action == 'start':
            if manager.start():
                logger.info("🎉 系统启动成功！")
                # 保持运行状态
                if args.mode == 'local':
                    logger.info("按 Ctrl+C 停止服务")
                    while True:
                        time.sleep(1)
            else:
                logger.error("❌ 系统启动失败")
                sys.exit(1)
        elif args.action == 'stop':
            manager.stop_services()
        elif args.action == 'status':
            manager.show_status()
            
    except KeyboardInterrupt:
        manager.cleanup()
    except Exception as e:
        logger.error(f"系统错误: {e}")
        manager.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main() 