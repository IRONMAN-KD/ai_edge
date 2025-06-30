"""
平台自动检测器
用于自动识别当前运行环境的硬件平台
"""

import os
import platform
import subprocess
import logging
from typing import Tuple, Dict, Any, List

logger = logging.getLogger(__name__)


class PlatformDetector:
    """平台检测器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        
    def detect_best_platform(self) -> Tuple[str, float]:
        """
        自动检测最佳平台
        
        Returns:
            Tuple[str, float]: (平台名称, 置信度)
        """
        platforms = self.detect_all_platforms()
        
        if not platforms:
            # 默认使用CPU
            if 'x86' in self.machine or 'amd64' in self.machine:
                return 'cpu_x86', 0.5
            else:
                return 'cpu_arm', 0.5
        
        # 返回置信度最高的平台
        best_platform = max(platforms, key=lambda x: x[1])
        return best_platform[0], best_platform[1]
    
    def detect_all_platforms(self) -> List[Tuple[str, float]]:
        """
        检测所有可用平台
        
        Returns:
            List[Tuple[str, float]]: [(平台名称, 置信度), ...]
        """
        platforms = []
        
        # 检测NVIDIA GPU
        nvidia_score = self._detect_nvidia_gpu()
        if nvidia_score > 0:
            platforms.append(('nvidia_gpu', nvidia_score))
        
        # 检测Atlas NPU
        atlas_score = self._detect_atlas_npu()
        if atlas_score > 0:
            platforms.append(('atlas_npu', atlas_score))
        
        # 检测算能芯片
        sophon_score = self._detect_sophon()
        if sophon_score > 0:
            platforms.append(('sophon', sophon_score))
        
        # 检测CPU
        cpu_score = self._detect_cpu()
        if cpu_score > 0:
            if 'x86' in self.machine or 'amd64' in self.machine:
                platforms.append(('cpu_x86', cpu_score))
            else:
                platforms.append(('cpu_arm', cpu_score))
        
        return platforms
    
    def _detect_nvidia_gpu(self) -> float:
        """检测NVIDIA GPU"""
        try:
            # 检查nvidia-smi命令
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # 检查CUDA环境
                cuda_available = self._check_cuda()
                if cuda_available:
                    return 0.9
                else:
                    return 0.6
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # 检查CUDA环境变量
        if os.environ.get('CUDA_HOME') or os.environ.get('CUDA_PATH'):
            return 0.3
        
        return 0.0
    
    def _detect_atlas_npu(self) -> float:
        """检测Atlas NPU"""
        try:
            # 检查设备文件
            if os.path.exists('/dev/davinci0') or os.path.exists('/dev/davinci_manager'):
                return 0.9
            
            # 检查ACL库
            if self._check_acl_available():
                return 0.8
            
            # 检查环境变量
            if os.environ.get('ASCEND_HOME') or os.environ.get('ASCEND_TOOLKIT_HOME'):
                return 0.5
            
            # 检查SOC版本文件
            if os.path.exists('/proc/driver/hisilicon/soc_version'):
                return 0.7
                
        except Exception as e:
            logger.debug(f"Atlas检测异常: {e}")
        
        return 0.0
    
    def _detect_sophon(self) -> float:
        """检测算能芯片"""
        try:
            # 检查设备文件
            if os.path.exists('/dev/bm-sophon0'):
                return 0.9
            
            # 检查SOPHON SDK
            if self._check_sophon_sdk():
                return 0.8
            
            # 检查环境变量
            if os.environ.get('SOPHON_SDK_HOME'):
                return 0.5
                
        except Exception as e:
            logger.debug(f"算能检测异常: {e}")
        
        return 0.0
    
    def _detect_cpu(self) -> float:
        """检测CPU平台"""
        # CPU总是可用的
        return 0.8
    
    def _check_cuda(self) -> bool:
        """检查CUDA是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            pass
        
        try:
            import tensorflow as tf
            return len(tf.config.list_physical_devices('GPU')) > 0
        except ImportError:
            pass
        
        return False
    
    def _check_acl_available(self) -> bool:
        """检查ACL库是否可用"""
        try:
            import acl
            return True
        except ImportError:
            pass
        
        # 检查库文件
        acl_paths = [
            '/usr/local/Ascend/acllib/lib64/libascendcl.so',
            '/usr/local/Ascend/nnae/latest/acllib/lib64/libascendcl.so'
        ]
        
        for path in acl_paths:
            if os.path.exists(path):
                return True
        
        return False
    
    def _check_sophon_sdk(self) -> bool:
        """检查SOPHON SDK是否可用"""
        try:
            import sophon.sail
            return True
        except ImportError:
            pass
        
        # 检查库文件
        sophon_paths = [
            '/opt/sophon/libsophon-current/lib/libbmrt.so',
            '/opt/sophon/sophon-sail/lib/python3/dist-packages'
        ]
        
        for path in sophon_paths:
            if os.path.exists(path):
                return True
        
        return False
    
    def get_platform_capabilities(self, platform: str) -> Dict[str, Any]:
        """
        获取平台能力信息
        
        Args:
            platform: 平台名称
            
        Returns:
            Dict: 平台能力信息
        """
        capabilities = {
            'cpu_x86': {
                'inference_speed': 'medium',
                'memory_usage': 'low',
                'model_formats': ['onnx'],
                'precision': ['fp32', 'fp16'],
                'max_batch_size': 8
            },
            'cpu_arm': {
                'inference_speed': 'low',
                'memory_usage': 'low',
                'model_formats': ['onnx'],
                'precision': ['fp32'],
                'max_batch_size': 4
            },
            'nvidia_gpu': {
                'inference_speed': 'high',
                'memory_usage': 'high',
                'model_formats': ['onnx', 'tensorrt'],
                'precision': ['fp32', 'fp16', 'int8'],
                'max_batch_size': 32
            },
            'atlas_npu': {
                'inference_speed': 'high',
                'memory_usage': 'medium',
                'model_formats': ['om'],
                'precision': ['fp16', 'int8'],
                'max_batch_size': 16
            },
            'sophon': {
                'inference_speed': 'high',
                'memory_usage': 'medium',
                'model_formats': ['bmodel'],
                'precision': ['fp32', 'fp16', 'int8'],
                'max_batch_size': 16
            }
        }
        
        return capabilities.get(platform, {})
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'system': self.system,
            'machine': self.machine,
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': os.cpu_count()
        }


def auto_detect_platform() -> str:
    """
    自动检测平台的便捷函数
    
    Returns:
        str: 检测到的平台名称
    """
    detector = PlatformDetector()
    platform_name, confidence = detector.detect_best_platform()
    
    logger.info(f"自动检测到平台: {platform_name} (置信度: {confidence:.2f})")
    
    return platform_name
