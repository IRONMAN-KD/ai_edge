#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兆慧 AI Edge 智能小站 - 视觉识别算法系统
主程序入口
"""

import os
import sys
import signal
import argparse
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, setup_logging
from utils.config_parser import ConfigParser
from components.video_input import VideoInput
from components.model_inference import ModelInference
from components.alert_manager import AlertManager
from components.push_notification import PushNotification
from components.visualization import Visualization
from components.model_selector import ModelSelector

logger = get_logger(__name__)


class VisionSystem:
    """视觉识别系统主类"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        """
        初始化视觉识别系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = None
        self.video_input = None
        self.model_selector = None
        self.alert_manager = None
        self.push_notification = None
        self.visualization = None
        self.running = False
        
        # 初始化日志
        setup_logging()
        logger.info("视觉识别系统初始化开始")
        
        # 加载配置
        self._load_config()
        
        # 初始化组件
        self._init_components()
        
        logger.info("视觉识别系统初始化完成")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            self.config = ConfigParser(self.config_path)
            logger.info(f"成功加载配置文件: {self.config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def _init_components(self):
        """初始化系统组件"""
        try:
            # 初始化模型选择器
            self.model_selector = ModelSelector()
            
            # 初始化视频输入
            video_config = self.config.get('video_input', {})
            self.video_input = VideoInput(
                source=video_config.get('source', 'rtsp://localhost:554/stream'),
                fps=video_config.get('fps', 30),
                resolution=video_config.get('resolution', (1920, 1080))
            )
            
            # 初始化告警管理器
            alert_config = self.config.get('alert', {})
            self.alert_manager = AlertManager(
                confidence_threshold=alert_config.get('confidence_threshold', 0.5),
                debounce_time=alert_config.get('debounce_time', 5),
                save_images=alert_config.get('save_images', True),
                image_save_path=alert_config.get('image_save_path', 'alerts')
            )
            
            # 初始化推送通知
            push_config = self.config.get('push_notification', {})
            self.push_notification = PushNotification(
                mqtt_config=push_config.get('mqtt', {}),
                http_config=push_config.get('http', {}),
                rabbitmq_config=push_config.get('rabbitmq', {}),
                kafka_config=push_config.get('kafka', {})
            )
            
            # 初始化可视化
            vis_config = self.config.get('visualization', {})
            self.visualization = Visualization(
                enabled=vis_config.get('enabled', True),
                window_name=vis_config.get('window_name', 'Vision System'),
                show_fps=vis_config.get('show_fps', True),
                show_confidence=vis_config.get('show_confidence', True)
            )
            
            logger.info("所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            raise
    
    def select_model(self, interactive: bool = True) -> bool:
        """
        选择模型
        
        Args:
            interactive: 是否使用交互式选择
            
        Returns:
            是否选择成功
        """
        try:
            if interactive:
                # 交互式选择
                config = self.model_selector.interactive_select()
                if not config:
                    logger.warning("用户取消模型选择")
                    return False
                
                logger.info(f"选择的配置: {config}")
                return True
            else:
                # 从配置文件加载默认模型
                model_config = self.config.get('model', {})
                model_id = model_config.get('model_id', 'yolov5')
                preset_id = model_config.get('preset_id')
                
                if self.model_selector.load_from_config({
                    'mode': 'model',
                    'model_id': model_id,
                    'preset_id': preset_id
                }):
                    logger.info(f"成功加载默认模型: {model_id}")
                    return True
                else:
                    logger.error(f"加载默认模型失败: {model_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"选择模型失败: {e}")
            return False
    
    def run(self):
        """运行系统"""
        try:
            logger.info("开始运行视觉识别系统")
            self.running = True
            
            # 选择模型
            if not self.select_model():
                logger.error("模型选择失败，系统退出")
                return
            
            # 获取当前模型
            model = self.model_selector.get_current_model()
            if not model:
                logger.error("未获取到有效模型，系统退出")
                return
            
            # 获取模型信息
            model_info = self.model_selector.get_current_model_info()
            logger.info(f"当前模型: {model_info}")
            
            # 启动视频输入
            self.video_input.start()
            
            # 主处理循环
            frame_count = 0
            while self.running:
                try:
                    # 获取视频帧
                    frame = self.video_input.get_frame()
                    if frame is None:
                        continue
                    
                    frame_count += 1
                    
                    # 模型推理
                    detections = model.inference(frame)
                    
                    # 处理检测结果
                    if detections:
                        # 告警检查
                        alert_triggered = self.alert_manager.check_alert(
                            detections, frame, frame_count
                        )
                        
                        # 推送通知
                        if alert_triggered:
                            self.push_notification.send_alert(
                                alert_type="object_detection",
                                message=f"检测到 {len(detections)} 个目标",
                                confidence=detections[0].get('confidence', 0),
                                class_name=detections[0].get('class', 'unknown'),
                                frame_count=frame_count
                            )
                    
                    # 可视化
                    if self.visualization.enabled:
                        self.visualization.draw_detections(
                            frame, detections, model_info
                        )
                        self.visualization.show_frame(frame)
                    
                    # 检查退出信号
                    if not self.running:
                        break
                        
                except KeyboardInterrupt:
                    logger.info("收到中断信号，正在停止系统...")
                    break
                except Exception as e:
                    logger.error(f"处理帧时发生错误: {e}")
                    continue
            
            logger.info(f"系统运行结束，共处理 {frame_count} 帧")
            
        except Exception as e:
            logger.error(f"系统运行失败: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止系统"""
        logger.info("正在停止视觉识别系统...")
        self.running = False
        
        try:
            # 停止视频输入
            if self.video_input:
                self.video_input.stop()
            
            # 释放模型资源
            if self.model_selector:
                self.model_selector.release()
            
            # 关闭可视化
            if self.visualization:
                self.visualization.close()
            
            logger.info("视觉识别系统已停止")
            
        except Exception as e:
            logger.error(f"停止系统时发生错误: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在停止系统...")
    if hasattr(signal_handler, 'system'):
        signal_handler.system.stop()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="华为 AI Edge 智能小站 - 视觉识别算法系统")
    parser.add_argument(
        "--config", 
        default="config/config.yml", 
        help="配置文件路径 (默认: config/config.yml)"
    )
    parser.add_argument(
        "--no-interactive", 
        action="store_true", 
        help="禁用交互式模型选择，使用配置文件中的默认模型"
    )
    parser.add_argument(
        "--list-models", 
        action="store_true", 
        help="列出所有可用模型并退出"
    )
    parser.add_argument(
        "--list-scenarios", 
        action="store_true", 
        help="列出所有可用场景并退出"
    )
    parser.add_argument(
        "--list-presets", 
        action="store_true", 
        help="列出所有可用预设并退出"
    )
    
    args = parser.parse_args()
    
    try:
        # 检查配置文件
        if not os.path.exists(args.config):
            logger.error(f"配置文件不存在: {args.config}")
            sys.exit(1)
        
        # 创建系统实例
        system = VisionSystem(args.config)
        
        # 注册信号处理器
        signal_handler.system = system
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 处理列表选项
        if args.list_models:
            system.model_selector.list_models()
            return
        
        if args.list_scenarios:
            system.model_selector.list_scenarios()
            return
        
        if args.list_presets:
            system.model_selector.list_presets()
            return
        
        # 运行系统
        with system:
            system.run()
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 