"""
基础功能测试
验证系统核心组件的功能
"""

import unittest
import os
import sys
import tempfile
import yaml
import numpy as np

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_parser import ConfigParser
from utils.logging import AtlasLogger
from utils.image_utils import ImageProcessor
from components.model_inference import ModelManager
from components.alert_manager import AlertManager, AlertInfo
from components.push_notification import PushNotificationManager


class TestConfigParser(unittest.TestCase):
    """配置解析器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yml')
        
        # 创建测试配置
        test_config = {
            'system': {'device_id': 0, 'log_level': 'INFO'},
            'model': {'path': '/test/model.om', 'input_width': 640},
            'video': {'source': 'test.mp4', 'fps': 30},
            'alert': {'debounce_time': 60, 'save_images': True}
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
    
    def test_load_config(self):
        """测试配置加载"""
        config = ConfigParser(self.config_path)
        
        self.assertEqual(config.get('system.device_id'), 0)
        self.assertEqual(config.get('model.input_width'), 640)
        self.assertEqual(config.get('video.fps'), 30)
        self.assertTrue(config.get('alert.save_images'))
    
    def test_container_env(self):
        """测试容器环境检测"""
        config = ConfigParser(self.config_path)
        
        # 测试容器环境检测
        is_container = config.is_container_env()
        self.assertIsInstance(is_container, bool)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)


class TestImageProcessor(unittest.TestCase):
    """图像处理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = ImageProcessor(640, 640)
    
    def test_preprocess_image(self):
        """测试图像预处理"""
        # 创建测试图像
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 预处理
        processed = self.processor.preprocess_image(test_image)
        
        # 验证输出
        self.assertEqual(processed.shape, (1, 3, 640, 640))
        self.assertEqual(processed.dtype, np.float32)
        self.assertTrue(np.all(processed >= 0) and np.all(processed <= 1))
    
    def test_draw_detections(self):
        """测试检测结果绘制"""
        # 创建测试图像
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 创建测试检测结果
        detections = [
            {
                'bbox': [100, 100, 200, 200],
                'confidence': 0.8,
                'class_id': 0
            }
        ]
        
        class_names = ['person']
        class_colors = [[255, 0, 0]]
        
        # 绘制检测结果
        result = self.processor.draw_detections(test_image, detections, class_names, class_colors)
        
        # 验证输出
        self.assertEqual(result.shape, test_image.shape)
        self.assertEqual(result.dtype, test_image.dtype)
    
    def test_save_image(self):
        """测试图像保存"""
        # 创建测试图像
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
        
        try:
            # 保存图像
            success = self.processor.save_image(test_image, temp_path)
            self.assertTrue(success)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(temp_path))
            
        finally:
            # 清理
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestAlertManager(unittest.TestCase):
    """告警管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置
        self.temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(self.temp_dir, 'test_config.yml')
        
        test_config = {
            'alert': {
                'debounce_time': 60,
                'save_images': False,
                'image_path': self.temp_dir
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        self.config = ConfigParser(config_path)
        self.alert_manager = AlertManager(self.config)
    
    def test_process_detections(self):
        """测试检测结果处理"""
        # 创建测试检测结果
        detections = [
            {
                'bbox': [100, 100, 200, 200],
                'confidence': 0.8,
                'class_id': 0,
                'class_name': 'person',
                'threshold': 0.5
            }
        ]
        
        # 创建测试图像
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        timestamp = 1234567890.0
        
        # 处理检测结果
        alerts = self.alert_manager.process_detections(detections, test_image, timestamp)
        
        # 验证结果
        self.assertEqual(len(alerts), 1)
        self.assertIsInstance(alerts[0], AlertInfo)
        self.assertEqual(alerts[0].detection['class_name'], 'person')
        self.assertEqual(alerts[0].detection['confidence'], 0.8)
    
    def test_debounce_mechanism(self):
        """测试防抖机制"""
        # 创建相同位置的检测结果
        detection = {
            'bbox': [100, 100, 200, 200],
            'confidence': 0.8,
            'class_id': 0,
            'class_name': 'person',
            'threshold': 0.5
        }
        
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        timestamp = 1234567890.0
        
        # 第一次处理
        alerts1 = self.alert_manager.process_detections([detection], test_image, timestamp)
        self.assertEqual(len(alerts1), 1)
        
        # 短时间内再次处理（应该被防抖）
        alerts2 = self.alert_manager.process_detections([detection], test_image, timestamp + 1)
        self.assertEqual(len(alerts2), 0)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)


class TestModelManager(unittest.TestCase):
    """模型管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置
        self.temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(self.temp_dir, 'test_config.yml')
        
        test_config = {
            'model': {
                'path': '/test/model.om',
                'input_width': 640,
                'input_height': 640,
                'confidence_threshold': 0.5
            },
            'classes': [
                {'name': 'person', 'threshold': 0.6, 'color': [255, 0, 0]},
                {'name': 'car', 'threshold': 0.5, 'color': [0, 255, 0]}
            ]
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        self.config = ConfigParser(config_path)
    
    def test_model_manager_init(self):
        """测试模型管理器初始化"""
        try:
            model_manager = ModelManager(self.config)
            
            # 验证类别信息
            class_info = model_manager.get_class_info()
            self.assertEqual(len(class_info['class_names']), 2)
            self.assertEqual(class_info['class_names'][0], 'person')
            self.assertEqual(class_info['class_names'][1], 'car')
            
        except Exception as e:
            # 如果没有 Atlas SDK，应该跳过测试
            self.skipTest(f"Atlas SDK 不可用: {e}")
    
    def test_detect(self):
        """测试目标检测"""
        try:
            model_manager = ModelManager(self.config)
            
            # 创建测试图像
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # 执行检测
            detections = model_manager.detect(test_image)
            
            # 验证结果
            self.assertIsInstance(detections, list)
            
        except Exception as e:
            # 如果没有 Atlas SDK，应该跳过测试
            self.skipTest(f"Atlas SDK 不可用: {e}")
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)


class TestPushNotificationManager(unittest.TestCase):
    """推送通知管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置
        self.temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(self.temp_dir, 'test_config.yml')
        
        test_config = {
            'mqtt': {'enabled': False},
            'http': {'enabled': False},
            'rabbitmq': {'enabled': False},
            'kafka': {'enabled': False}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        self.config = ConfigParser(config_path)
        self.push_manager = PushNotificationManager(self.config)
    
    def test_push_manager_init(self):
        """测试推送管理器初始化"""
        # 验证初始化成功
        self.assertIsNotNone(self.push_manager)
        self.assertIsInstance(self.push_manager.pushers, dict)
    
    def test_push_alert(self):
        """测试告警推送"""
        # 创建测试告警信息
        alert_info = {
            'alert_id': 'test_123',
            'timestamp': 1234567890.0,
            'class_name': 'person',
            'confidence': 0.8,
            'bbox': [100, 100, 200, 200]
        }
        
        # 推送告警
        results = self.push_manager.push_alert(alert_info)
        
        # 验证结果
        self.assertIsInstance(results, dict)
    
    def test_get_status(self):
        """测试状态获取"""
        status = self.push_manager.get_status()
        self.assertIsInstance(status, dict)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)


class TestLogger(unittest.TestCase):
    """日志器测试"""
    
    def test_logger_init(self):
        """测试日志器初始化"""
        logger = AtlasLogger("test_logger", "INFO")
        self.assertIsNotNone(logger)
    
    def test_log_functions(self):
        """测试日志函数"""
        logger = AtlasLogger("test_logger", "INFO")
        
        # 测试各种日志级别
        logger.debug("测试调试日志")
        logger.info("测试信息日志")
        logger.warning("测试警告日志")
        logger.error("测试错误日志")
        
        # 测试特殊日志函数
        logger.log_inference("test_model", 0.1, 0.8, "person")
        logger.log_alert("test_alert", 0.8, "person", "/test/image.jpg")
        logger.log_push("test_protocol", True, "推送成功", 0.05)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2) 