import logging
import os
from .base import BaseModel
from .detection import ONNXDetectionModel, AtlasDetectionModel
from .classification import ClassificationModel

logger = logging.getLogger(__name__)

class ModelFactory:
    @staticmethod
    def create_model(model_config: dict) -> BaseModel:
        model_type = model_config.get('type')
        model_path = model_config.get('path', '')
        
        # 检查模型文件是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        if model_type == 'detection' or model_type == 'object_detection':
            # 根据文件扩展名智能判断模型类型
            if model_path.endswith('.onnx'):
                # ONNX模型，直接使用ONNX运行时
                logger.info(f"检测到ONNX模型文件: {model_path}")
                return ONNXDetectionModel(**model_config)
            
            elif model_path.endswith('.om'):
                # Atlas OM模型，尝试使用Atlas运行时
                logger.info(f"检测到Atlas OM模型文件: {model_path}")
                try:
                    return AtlasDetectionModel(**model_config)
                except RuntimeError as e:
                    if "Atlas ACL initialization failed" in str(e):
                        logger.error(f"Atlas ACL初始化失败: {e}")
                        logger.error("======== Atlas设备诊断信息 ========")
                        logger.error("ACL错误507008通常表示以下问题之一:")
                        logger.error("1. Atlas设备驱动未正确加载")
                        logger.error("2. 容器权限配置不足")
                        logger.error("3. 设备文件映射错误")
                        logger.error("4. CANN工具包环境变量配置问题")
                        logger.error("=====================================")
                        
                        # 进行详细的环境诊断
                        ModelFactory._diagnose_atlas_environment()
                        
                        # 对于Atlas设备，不进行ONNX回退，直接抛出错误
                        raise RuntimeError(
                            f"Atlas设备上OM模型加载失败: {e}\n"
                            "请检查:\n"
                            "1. Atlas设备驱动是否正常: lsmod | grep drv_davinci\n"
                            "2. 设备文件权限: ls -la /dev/davinci*\n"
                            "3. CANN工具包安装: ls -la /usr/local/Ascend/\n"
                            "4. 容器是否运行在Atlas设备上\n"
                            "建议: 可以尝试在宿主机直接运行应用以避免容器权限限制"
                        )
                    else:
                        raise e
            
            else:
                # 未知文件格式，尝试根据runtime参数
                runtime = model_config.get('runtime', 'onnx')
                logger.warning(f"未知的模型文件格式: {model_path}，根据runtime参数使用: {runtime}")
                
                if runtime == 'onnx':
                    return ONNXDetectionModel(**model_config)
                elif runtime == 'atlas':
                    try:
                        return AtlasDetectionModel(**model_config)
                    except RuntimeError as e:
                        logger.error(f"Atlas模型初始化失败: {e}")
                        raise RuntimeError(f"Atlas设备上模型初始化失败，无法使用ONNX回退: {e}")
                else:
                    raise ValueError(f"Unsupported runtime: {runtime} for model: {model_path}")

        elif model_type == 'classification':
            # 分类模型暂时使用通用逻辑
            return ClassificationModel(**model_config)
        
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    @staticmethod
    def _diagnose_atlas_environment():
        """诊断Atlas环境"""
        logger.info("======== 开始Atlas环境诊断 ========")
        
        # 检查设备文件
        atlas_devices = ['/dev/davinci0', '/dev/davinci_manager', '/dev/davinci_manager_docker', '/dev/davinci_mdio']
        for device in atlas_devices:
            if os.path.exists(device):
                logger.info(f"✓ 设备文件存在: {device}")
                try:
                    stat_info = os.stat(device)
                    logger.info(f"  权限: {oct(stat_info.st_mode)[-3:]}")
                except Exception as e:
                    logger.warning(f"  无法获取权限信息: {e}")
            else:
                logger.error(f"✗ 设备文件不存在: {device}")
        
        # 检查CANN安装
        cann_paths = [
            '/usr/local/Ascend/ascend-toolkit/latest',
            '/usr/local/Ascend/driver',
            '/usr/local/Ascend/cann/latest'
        ]
        for path in cann_paths:
            if os.path.exists(path):
                logger.info(f"✓ CANN路径存在: {path}")
            else:
                logger.warning(f"✗ CANN路径不存在: {path}")
        
        # 检查关键库文件
        lib_files = [
            '/usr/local/Ascend/ascend-toolkit/latest/lib64/libascend_hal.so',
            '/usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/devlib/libascend_hal.so',
            '/usr/local/Ascend/driver/lib64/driver/libdriver_api.so'
        ]
        for lib_file in lib_files:
            if os.path.exists(lib_file):
                logger.info(f"✓ 关键库文件存在: {lib_file}")
            else:
                logger.warning(f"✗ 关键库文件不存在: {lib_file}")
        
        # 检查环境变量
        env_vars = ['LD_LIBRARY_PATH', 'ASCEND_OPP_PATH', 'ASCEND_AICPU_PATH', 'PYTHONPATH']
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                logger.info(f"✓ 环境变量 {var}: {value}")
            else:
                logger.warning(f"✗ 环境变量 {var} 未设置")
        
        logger.info("======== Atlas环境诊断完成 ========")

    @staticmethod
    def check_atlas_availability() -> bool:
        """检查Atlas设备是否可用"""
        try:
            # 检查设备文件
            if not os.path.exists('/dev/davinci0'):
                logger.warning("Atlas设备文件 /dev/davinci0 不存在")
                return False
                
            if not os.path.exists('/dev/davinci_manager'):
                logger.warning("Atlas设备文件 /dev/davinci_manager 不存在")
                return False
            
            # 检查CANN环境
            if not os.path.exists('/usr/local/Ascend'):
                logger.warning("CANN工具包路径 /usr/local/Ascend 不存在")
                return False
                
            logger.info("Atlas设备环境检查通过")
            return True
            
        except Exception as e:
            logger.error(f"Atlas设备检查失败: {e}")
            return False
