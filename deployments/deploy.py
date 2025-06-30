#!/usr/bin/env python3
"""
AI Edge 部署管理脚本
支持多平台版本选择和部署
"""

import os
import sys
import yaml
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional

class DeploymentManager:
    """部署管理器"""
    
    def __init__(self, config_path: str = "config.yml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.deployments_dir = Path(__file__).parent
        self.project_root = self.deployments_dir.parent
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        config_file = Path(__file__).parent / self.config_path
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _save_config(self):
        """保存配置文件"""
        config_file = Path(__file__).parent / self.config_path
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    def list_platforms(self) -> List[str]:
        """列出支持的平台"""
        return list(self.config['platforms'].keys())
    
    def get_current_platform(self) -> str:
        """获取当前配置的平台"""
        return self.config['deployment']['platform']
    
    def set_platform(self, platform: str):
        """设置当前平台"""
        if platform not in self.list_platforms():
            raise ValueError(f"不支持的平台: {platform}. 支持的平台: {self.list_platforms()}")
        
        self.config['deployment']['platform'] = platform
        self._save_config()
        print(f"✅ 平台已设置为: {platform}")
    
    def show_platform_info(self, platform: str = None):
        """显示平台信息"""
        if platform is None:
            platform = self.get_current_platform()
            
        if platform not in self.config['platforms']:
            print(f"❌ 未知平台: {platform}")
            return
            
        info = self.config['platforms'][platform]
        print(f"\n📋 平台信息: {platform}")
        print(f"名称: {info['name']}")
        print(f"描述: {info['description']}")
        print(f"Docker Compose: {info['docker_compose']}")
        print(f"要求:")
        for req in info['requirements']:
            print(f"  - {req}")
    
    def check_requirements(self, platform: str = None) -> bool:
        """检查平台要求"""
        if platform is None:
            platform = self.get_current_platform()
            
        print(f"🔍 检查 {platform} 平台要求...")
        
        # 检查Docker
        if not self._check_docker():
            return False
            
        # 检查平台特定要求
        if platform == "nvidia_gpu":
            return self._check_nvidia_requirements()
        elif platform == "atlas_npu":
            return self._check_atlas_requirements()
        elif platform == "cpu":
            return self._check_cpu_requirements()
        
        return True
    
    def _check_docker(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Docker: {result.stdout.strip()}")
            
            # 检查Docker Compose
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Docker Compose: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker或Docker Compose未安装或不可用")
            return False
    
    def _check_nvidia_requirements(self) -> bool:
        """检查NVIDIA GPU要求"""
        try:
            # 检查nvidia-smi
            result = subprocess.run(['nvidia-smi'], 
                                  capture_output=True, text=True, check=True)
            print("✅ NVIDIA GPU驱动可用")
            
            # 检查nvidia-docker
            result = subprocess.run(['docker', 'run', '--rm', '--gpus', 'all', 
                                   'nvidia/cuda:11.8-base-ubuntu20.04', 'nvidia-smi'], 
                                  capture_output=True, text=True, check=True)
            print("✅ NVIDIA Docker运行时可用")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ NVIDIA GPU驱动或Docker运行时不可用")
            return False
    
    def _check_atlas_requirements(self) -> bool:
        """检查Atlas NPU要求"""
        # 检查设备文件
        devices = ['/dev/davinci0', '/dev/davinci_manager']
        for device in devices:
            if not os.path.exists(device):
                print(f"❌ Atlas设备文件不存在: {device}")
                return False
        
        # 检查运行时库
        runtime_path = '/usr/local/Ascend/runtime'
        if not os.path.exists(runtime_path):
            print(f"❌ Atlas运行时不存在: {runtime_path}")
            return False
            
        print("✅ Atlas NPU环境检查通过")
        return True
    
    def _check_cpu_requirements(self) -> bool:
        """检查CPU要求"""
        print("✅ CPU平台无特殊要求")
        return True
    
    def prepare_data_directories(self):
        """准备数据目录"""
        print("📁 创建数据目录...")
        
        data_volumes = self.config['deployment']['data_volumes']
        base_dir = self.deployments_dir / "data"
        
        for volume_name, volume_path in data_volumes.items():
            full_path = base_dir / volume_path.lstrip('./')
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {full_path}")
    
    def deploy(self, platform: str = None, build: bool = False, detached: bool = True):
        """部署指定平台"""
        if platform is None:
            platform = self.get_current_platform()
        
        if platform not in self.list_platforms():
            raise ValueError(f"不支持的平台: {platform}")
        
        print(f"🚀 开始部署 {platform} 平台...")
        
        # 检查要求
        if not self.check_requirements(platform):
            print("❌ 平台要求检查失败，部署终止")
            return False
        
        # 准备数据目录
        self.prepare_data_directories()
        
        # 获取docker-compose文件路径
        compose_file = self.deployments_dir / self.config['platforms'][platform]['docker_compose']
        if not compose_file.exists():
            print(f"❌ Docker Compose文件不存在: {compose_file}")
            return False
        
        # 构建Docker Compose命令
        cmd = ['docker', 'compose', '-f', str(compose_file)]
        
        if build:
            cmd.extend(['up', '--build'])
        else:
            cmd.extend(['up'])
            
        if detached:
            cmd.append('-d')
        
        try:
            print(f"🔨 执行命令: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, cwd=self.deployments_dir)
            print(f"✅ {platform} 平台部署成功!")
            
            # 显示服务信息
            self._show_service_info()
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 部署失败: {e}")
            return False
    
    def stop(self, platform: str = None):
        """停止指定平台"""
        if platform is None:
            platform = self.get_current_platform()
        
        compose_file = self.deployments_dir / self.config['platforms'][platform]['docker_compose']
        if not compose_file.exists():
            print(f"❌ Docker Compose文件不存在: {compose_file}")
            return False
        
        try:
            cmd = ['docker', 'compose', '-f', str(compose_file), 'down']
            subprocess.run(cmd, check=True, cwd=self.deployments_dir)
            print(f"✅ {platform} 平台已停止")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 停止失败: {e}")
            return False
    
    def status(self, platform: str = None):
        """查看服务状态"""
        if platform is None:
            platform = self.get_current_platform()
        
        compose_file = self.deployments_dir / self.config['platforms'][platform]['docker_compose']
        if not compose_file.exists():
            print(f"❌ Docker Compose文件不存在: {compose_file}")
            return
        
        try:
            cmd = ['docker', 'compose', '-f', str(compose_file), 'ps']
            subprocess.run(cmd, check=True, cwd=self.deployments_dir)
        except subprocess.CalledProcessError as e:
            print(f"❌ 状态查询失败: {e}")
    
    def logs(self, platform: str = None, service: str = None, follow: bool = False):
        """查看服务日志"""
        if platform is None:
            platform = self.get_current_platform()
        
        compose_file = self.deployments_dir / self.config['platforms'][platform]['docker_compose']
        if not compose_file.exists():
            print(f"❌ Docker Compose文件不存在: {compose_file}")
            return
        
        try:
            cmd = ['docker', 'compose', '-f', str(compose_file), 'logs']
            if follow:
                cmd.append('-f')
            if service:
                cmd.append(service)
                
            subprocess.run(cmd, check=True, cwd=self.deployments_dir)
        except subprocess.CalledProcessError as e:
            print(f"❌ 日志查询失败: {e}")
    
    def _show_service_info(self):
        """显示服务信息"""
        ports = self.config['deployment']['ports']
        print("\n🌐 服务访问地址:")
        print(f"  前端: http://localhost:{ports['frontend']}")
        print(f"  API: http://localhost:{ports['api']}")
        print(f"  API文档: http://localhost:{ports['api']}/docs")
        print(f"  MySQL: localhost:{ports['mysql']}")
        print(f"  Redis: localhost:{ports['redis']}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI Edge 部署管理工具")
    parser.add_argument('--config', default='config.yml', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出平台
    subparsers.add_parser('list', help='列出支持的平台')
    
    # 显示当前平台
    subparsers.add_parser('current', help='显示当前平台')
    
    # 设置平台
    set_parser = subparsers.add_parser('set', help='设置当前平台')
    set_parser.add_argument('platform', help='平台名称')
    
    # 显示平台信息
    info_parser = subparsers.add_parser('info', help='显示平台信息')
    info_parser.add_argument('--platform', help='平台名称（默认为当前平台）')
    
    # 检查要求
    check_parser = subparsers.add_parser('check', help='检查平台要求')
    check_parser.add_argument('--platform', help='平台名称（默认为当前平台）')
    
    # 部署
    deploy_parser = subparsers.add_parser('deploy', help='部署平台')
    deploy_parser.add_argument('--platform', help='平台名称（默认为当前平台）')
    deploy_parser.add_argument('--build', action='store_true', help='重新构建镜像')
    deploy_parser.add_argument('--foreground', action='store_true', help='前台运行')
    
    # 停止
    stop_parser = subparsers.add_parser('stop', help='停止平台')
    stop_parser.add_argument('--platform', help='平台名称（默认为当前平台）')
    
    # 状态
    status_parser = subparsers.add_parser('status', help='查看服务状态')
    status_parser.add_argument('--platform', help='平台名称（默认为当前平台）')
    
    # 日志
    logs_parser = subparsers.add_parser('logs', help='查看服务日志')
    logs_parser.add_argument('--platform', help='平台名称（默认为当前平台）')
    logs_parser.add_argument('--service', help='指定服务名称')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='跟踪日志')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = DeploymentManager(args.config)
        
        if args.command == 'list':
            platforms = manager.list_platforms()
            current = manager.get_current_platform()
            print("📋 支持的平台:")
            for platform in platforms:
                marker = " (当前)" if platform == current else ""
                print(f"  - {platform}{marker}")
                
        elif args.command == 'current':
            current = manager.get_current_platform()
            print(f"当前平台: {current}")
            manager.show_platform_info(current)
            
        elif args.command == 'set':
            manager.set_platform(args.platform)
            
        elif args.command == 'info':
            manager.show_platform_info(args.platform)
            
        elif args.command == 'check':
            success = manager.check_requirements(args.platform)
            sys.exit(0 if success else 1)
            
        elif args.command == 'deploy':
            success = manager.deploy(
                platform=args.platform,
                build=args.build,
                detached=not args.foreground
            )
            sys.exit(0 if success else 1)
            
        elif args.command == 'stop':
            success = manager.stop(args.platform)
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            manager.status(args.platform)
            
        elif args.command == 'logs':
            manager.logs(args.platform, args.service, args.follow)
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 