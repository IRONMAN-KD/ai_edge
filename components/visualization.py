"""
可视化模块
支持实时显示检测结果和性能信息
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Any, Optional
from utils.logging import logger
from utils.config_parser import ConfigParser
from utils.image_utils import ImageProcessor


class VisualizationManager:
    """可视化管理器"""
    
    def __init__(self, config: ConfigParser):
        self.config = config
        self.visualization_config = config.get_visualization_config()
        self.image_processor = ImageProcessor()
        
        # 显示控制
        self.show_window = self.visualization_config.get('enabled', True)
        self.window_name = "Atlas Vision System"
        
        # 性能统计
        self.fps_history = []
        self.max_fps_history = 30  # 保留最近30帧的FPS
        
        # 显示状态
        self.last_frame = None
        self.last_detections = []
        self.last_fps = 0.0
        
        # 初始化显示窗口
        if self.show_window:
            self._init_display()
    
    def _init_display(self):
        """初始化显示窗口"""
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 1280, 720)
            logger.info("可视化窗口初始化成功")
        except Exception as e:
            logger.error(f"可视化窗口初始化失败: {e}")
            self.show_window = False
    
    def update_display(self, frame, detections: List[Dict[str, Any]], 
                      fps: float = 0.0, performance_stats: Dict[str, Any] = None):
        """更新显示内容"""
        try:
            if frame is None:
                return
            
            # 更新性能统计
            self._update_fps_history(fps)
            self.last_frame = frame.copy()
            self.last_detections = detections
            self.last_fps = fps
            
            # 创建显示图像
            display_image = self._create_display_image(frame, detections, fps, performance_stats)
            
            # 显示图像
            if self.show_window:
                cv2.imshow(self.window_name, display_image)
                
                # 处理键盘事件
                key = cv2.waitKey(1) & 0xFF
                self._handle_keyboard_events(key)
            
        except Exception as e:
            logger.error(f"更新显示失败: {e}")
    
    def _create_display_image(self, frame, detections: List[Dict[str, Any]], 
                             fps: float, performance_stats: Dict[str, Any] = None) -> np.ndarray:
        """创建显示图像"""
        try:
            # 复制原始图像
            display_image = frame.copy()
            
            # 获取类别信息
            class_names = []
            class_colors = []
            for detection in detections:
                class_name = detection.get('class_name', 'unknown')
                class_id = detection.get('class_id', 0)
                if class_name not in class_names:
                    class_names.append(class_name)
                    # 根据类别ID生成颜色
                    color = self._get_class_color(class_id)
                    class_colors.append(color)
            
            # 绘制检测结果
            if detections:
                display_image = self.image_processor.draw_detections(
                    display_image, detections, class_names, class_colors
                )
            
            # 添加性能信息
            if self.visualization_config.get('show_fps', True):
                display_image = self._add_performance_info(display_image, fps, performance_stats)
            
            # 添加系统信息
            display_image = self._add_system_info(display_image)
            
            return display_image
            
        except Exception as e:
            logger.error(f"创建显示图像失败: {e}")
            return frame
    
    def _get_class_color(self, class_id: int) -> List[int]:
        """获取类别颜色"""
        # 预定义的颜色列表
        colors = [
            [255, 0, 0],    # 红色
            [0, 255, 0],    # 绿色
            [0, 0, 255],    # 蓝色
            [255, 255, 0],  # 黄色
            [255, 0, 255],  # 紫色
            [0, 255, 255],  # 青色
            [255, 165, 0],  # 橙色
            [128, 0, 128],  # 紫色
        ]
        
        return colors[class_id % len(colors)]
    
    def _add_performance_info(self, image: np.ndarray, fps: float, 
                             performance_stats: Dict[str, Any] = None) -> np.ndarray:
        """添加性能信息到图像"""
        try:
            # 设置字体参数
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = self.visualization_config.get('font_scale', 0.6)
            thickness = self.visualization_config.get('thickness', 2)
            color = (0, 255, 0)  # 绿色
            
            # 起始位置
            y_offset = 30
            line_height = 25
            
            # FPS信息
            fps_text = f"FPS: {fps:.1f}"
            cv2.putText(image, fps_text, (10, y_offset), font, font_scale, color, thickness)
            y_offset += line_height
            
            # 推理性能信息
            if performance_stats:
                inference_time = performance_stats.get('avg_inference_time', 0)
                inference_fps = performance_stats.get('fps', 0)
                
                inference_text = f"Inference: {inference_time*1000:.1f}ms ({inference_fps:.1f}fps)"
                cv2.putText(image, inference_text, (10, y_offset), font, font_scale, color, thickness)
                y_offset += line_height
            
            # 检测结果统计
            detection_count = len(self.last_detections)
            detection_text = f"Detections: {detection_count}"
            cv2.putText(image, detection_text, (10, y_offset), font, font_scale, color, thickness)
            y_offset += line_height
            
            # 平均FPS
            if self.fps_history:
                avg_fps = sum(self.fps_history) / len(self.fps_history)
                avg_fps_text = f"Avg FPS: {avg_fps:.1f}"
                cv2.putText(image, avg_fps_text, (10, y_offset), font, font_scale, color, thickness)
            
            return image
            
        except Exception as e:
            logger.error(f"添加性能信息失败: {e}")
            return image
    
    def _add_system_info(self, image: np.ndarray) -> np.ndarray:
        """添加系统信息到图像"""
        try:
            # 设置字体参数
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            color = (255, 255, 255)  # 白色
            
            # 获取图像尺寸
            height, width = image.shape[:2]
            
            # 系统信息
            system_info = [
                f"Atlas Vision System",
                f"Resolution: {width}x{height}",
                f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            # 在右上角显示
            y_offset = 30
            for info in system_info:
                text_size = cv2.getTextSize(info, font, font_scale, thickness)[0]
                x_pos = width - text_size[0] - 10
                cv2.putText(image, info, (x_pos, y_offset), font, font_scale, color, thickness)
                y_offset += 20
            
            return image
            
        except Exception as e:
            logger.error(f"添加系统信息失败: {e}")
            return image
    
    def _update_fps_history(self, fps: float):
        """更新FPS历史"""
        self.fps_history.append(fps)
        
        # 保持历史记录在指定长度内
        if len(self.fps_history) > self.max_fps_history:
            self.fps_history.pop(0)
    
    def _handle_keyboard_events(self, key: int):
        """处理键盘事件"""
        if key == 27:  # ESC键
            logger.info("用户按下ESC键，退出程序")
            # 这里可以发送退出信号
        elif key == ord('s'):  # S键保存当前帧
            self._save_current_frame()
        elif key == ord('h'):  # H键显示帮助
            self._show_help()
    
    def _save_current_frame(self):
        """保存当前帧"""
        try:
            if self.last_frame is not None:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"capture_{timestamp}.jpg"
                cv2.imwrite(filename, self.last_frame)
                logger.info(f"当前帧已保存: {filename}")
        except Exception as e:
            logger.error(f"保存当前帧失败: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = [
            "Atlas Vision System 快捷键:",
            "ESC - 退出程序",
            "S - 保存当前帧",
            "H - 显示帮助"
        ]
        
        for text in help_text:
            logger.info(text)
    
    def get_display_stats(self) -> Dict[str, Any]:
        """获取显示统计信息"""
        return {
            'show_window': self.show_window,
            'last_fps': self.last_fps,
            'avg_fps': sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0.0,
            'detection_count': len(self.last_detections),
            'fps_history_length': len(self.fps_history)
        }
    
    def set_show_window(self, show: bool):
        """设置是否显示窗口"""
        self.show_window = show
        if show and not cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE):
            self._init_display()
    
    def cleanup(self):
        """清理资源"""
        if self.show_window:
            cv2.destroyAllWindows()
            logger.info("可视化窗口已关闭")


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.frame_count = 0
        self.inference_times = []
        self.processing_times = []
        self.max_history = 100
    
    def record_inference_time(self, inference_time: float):
        """记录推理时间"""
        self.inference_times.append(inference_time)
        if len(self.inference_times) > self.max_history:
            self.inference_times.pop(0)
    
    def record_processing_time(self, processing_time: float):
        """记录处理时间"""
        self.processing_times.append(processing_time)
        if len(self.processing_times) > self.max_history:
            self.processing_times.pop(0)
    
    def increment_frame_count(self):
        """增加帧计数"""
        self.frame_count += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        elapsed_time = time.time() - self.start_time
        
        # 计算平均推理时间
        avg_inference_time = 0.0
        if self.inference_times:
            avg_inference_time = sum(self.inference_times) / len(self.inference_times)
        
        # 计算平均处理时间
        avg_processing_time = 0.0
        if self.processing_times:
            avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        
        # 计算FPS
        fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0.0
        
        # 计算推理FPS
        inference_fps = 1.0 / avg_inference_time if avg_inference_time > 0 else 0.0
        
        return {
            'elapsed_time': elapsed_time,
            'frame_count': self.frame_count,
            'avg_inference_time': avg_inference_time,
            'avg_processing_time': avg_processing_time,
            'fps': fps,
            'inference_fps': inference_fps,
            'inference_times_count': len(self.inference_times),
            'processing_times_count': len(self.processing_times)
        }
    
    def reset(self):
        """重置统计"""
        self.start_time = time.time()
        self.frame_count = 0
        self.inference_times.clear()
        self.processing_times.clear() 