#!/usr/bin/env python3
"""
本地启动后端服务，同时使用容器中的数据库和前端
"""

import os
import sys
import subprocess
import time
import argparse
import logging
import signal
import atexit

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("local_backend")

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_docker_services():
    """检查必要的Docker服务是否运行"""
    required_services = ["ai_edge_unified_db", "ai_edge_unified_redis", "ai_edge_unified_frontend"]
    missing_services = []
    running_services = []
    
    for service in required_services:
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={service}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                running_services.append(service)
            else:
                missing_services.append(service)
        except subprocess.CalledProcessError as e:
            logger.error(f"检查Docker服务时出错: {e}")
            missing_services.append(service)
    
    return missing_services, running_services

def check_service_health(service_name):
    """检查Docker服务的健康状态"""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", service_name],
            capture_output=True,
            text=True,
            check=True
        )
        health_status = result.stdout.strip()
        logger.info(f"服务 {service_name} 健康状态: {health_status}")
        return health_status
    except subprocess.CalledProcessError as e:
        logger.error(f"检查服务健康状态时出错: {e}")
        return "unknown"

def start_service(service_name):
    """启动单个Docker服务"""
    logger.info(f"启动Docker服务: {service_name}...")
    
    try:
        # 先尝试停止可能已经存在但不健康的容器
        try:
            subprocess.run(
                ["docker", "stop", f"ai_edge_unified_{service_name}"],
                check=False,
                capture_output=True
            )
            logger.info(f"已停止现有的 {service_name} 容器")
        except:
            pass
        
        # 启动服务
        subprocess.run(
            ["docker-compose", "up", "-d", service_name],
            check=True
        )
        logger.info(f"Docker服务 {service_name} 启动成功")
        
        # 等待服务健康
        if service_name == "db":
            logger.info("等待数据库服务就绪...")
            for i in range(30):  # 最多等待30*2=60秒
                health = check_service_health(f"ai_edge_unified_{service_name}")
                if health == "healthy":
                    logger.info("数据库服务已就绪")
                    return True
                time.sleep(2)
            logger.warning("数据库服务未能在超时时间内就绪，但将继续尝试")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"启动Docker服务 {service_name} 失败: {e}")
        return False

def start_required_services(services=None):
    """启动必要的Docker服务"""
    if services is None:
        services = ["db", "redis", "frontend"]
    
    logger.info(f"启动Docker服务: {', '.join(services)}...")
    
    success = True
    for service in services:
        if not start_service(service):
            success = False
    
    return success

def setup_environment():
    """设置环境变量"""
    # 数据库配置
    os.environ["MYSQL_HOST"] = "localhost"  # 本地访问容器映射的端口
    os.environ["MYSQL_PORT"] = "3307"       # docker-compose.yml中映射的端口
    os.environ["MYSQL_USER"] = "ai_edge_user"
    os.environ["MYSQL_PASSWORD"] = "ai_edge_pass_2024"
    os.environ["MYSQL_DATABASE"] = "ai_edge"
    
    # Redis配置
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
    
    # 平台配置
    os.environ["PLATFORM"] = "cpu_x86"
    
    # API配置
    os.environ["API_HOST"] = "0.0.0.0"
    os.environ["API_PORT"] = "8000"
    
    # 日志级别
    os.environ["LOG_LEVEL"] = "DEBUG"  # 本地开发使用DEBUG级别
    
    # Python路径
    os.environ["PYTHONPATH"] = f"{os.getcwd()}/src"

def start_backend_service():
    """启动后端服务"""
    logger.info("启动后端服务...")
    
    # 创建必要的目录
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("alert_images", exist_ok=True)
    
    # 启动后端服务
    cmd = [
        "python", "-m", "uvicorn", 
        "src.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"  # 开发模式下自动重载
    ]
    
    backend_process = subprocess.Popen(cmd)
    logger.info(f"后端服务已启动，进程ID: {backend_process.pid}")
    
    return backend_process

def cleanup(process):
    """清理资源"""
    if process and process.poll() is None:
        logger.info(f"停止后端服务进程 (PID: {process.pid})...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        logger.info("后端服务已停止")

def signal_handler(sig, frame, process):
    """信号处理函数"""
    logger.info(f"接收到信号 {sig}，正在停止服务...")
    cleanup(process)
    sys.exit(0)

def show_docker_logs(service_name, lines=50):
    """显示Docker服务的日志"""
    try:
        result = subprocess.run(
            ["docker", "logs", f"ai_edge_unified_{service_name}", "--tail", str(lines)],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"{service_name} 服务的最近 {lines} 行日志:")
        for line in result.stdout.splitlines():
            print(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.error(f"获取 {service_name} 日志失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="本地启动后端服务")
    parser.add_argument("--skip-docker-check", action="store_true", help="跳过Docker服务检查")
    parser.add_argument("--db-only", action="store_true", help="只启动数据库服务")
    parser.add_argument("--show-db-logs", action="store_true", help="显示数据库日志")
    parser.add_argument("--fix-db", action="store_true", help="尝试修复数据库")
    args = parser.parse_args()
    
    if args.show_db_logs:
        show_docker_logs("db")
        return
    
    if args.fix_db:
        logger.info("尝试修复数据库服务...")
        subprocess.run(["docker-compose", "stop", "db"], check=False)
        time.sleep(2)
        start_service("db")
        return
    
    if args.db_only:
        logger.info("只启动数据库服务")
        start_service("db")
        return
    
    if not args.skip_docker_check:
        # 检查必要的Docker服务
        missing_services, running_services = check_docker_services()
        if missing_services:
            logger.warning(f"以下必要的Docker服务未运行: {', '.join(missing_services)}")
            start_choice = input("是否要启动这些服务? (y/n): ").lower()
            if start_choice == 'y':
                if not start_required_services(services=[s.split('_')[-1] for s in missing_services]):
                    logger.error("无法启动必要的Docker服务，退出")
                    return
            else:
                logger.warning("继续运行，但某些功能可能无法正常工作")
        else:
            logger.info("所有必要的Docker服务都在运行")
            
            # 检查数据库健康状态
            db_health = check_service_health("ai_edge_unified_db")
            if db_health != "healthy":
                logger.warning(f"数据库服务状态不健康: {db_health}")
                fix_choice = input("是否要尝试修复数据库服务? (y/n): ").lower()
                if fix_choice == 'y':
                    logger.info("尝试修复数据库服务...")
                    subprocess.run(["docker-compose", "stop", "db"], check=False)
                    time.sleep(2)
                    if not start_service("db"):
                        logger.error("修复数据库服务失败，退出")
                        return
                else:
                    logger.warning("继续运行，但数据库功能可能无法正常工作")
    
    # 设置环境变量
    setup_environment()
    
    # 启动后端服务
    backend_process = start_backend_service()
    
    # 注册清理函数
    atexit.register(cleanup, backend_process)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, backend_process))
    signal.signal(signal.SIGTERM, lambda sig, frame: signal_handler(sig, frame, backend_process))
    
    # 保持脚本运行
    try:
        while backend_process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup(backend_process)

if __name__ == "__main__":
    print("=" * 50)
    print("AI Edge 本地后端启动工具")
    print("=" * 50)
    print("这个脚本将在本地启动后端服务，同时使用Docker容器中的数据库和前端")
    print("确保Docker服务已经启动，并且项目依赖已安装")
    print("=" * 50)
    main() 