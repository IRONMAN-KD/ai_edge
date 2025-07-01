"""
告警管理模块
实现告警触发、防抖机制和图片保存
"""

import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from utils.logging import logger
from utils.config_parser import ConfigParser
from utils.image_utils import ImageProcessor


class AlertInfo:
    """告警信息结构"""
    
    def __init__(self, detection: Dict[str, Any], frame, timestamp: float):
        self.detection = detection
        self.frame = frame
        self.timestamp = timestamp
        self.alert_id = self._generate_alert_id()
        self.image_path = None
        self.image_url = None
    
    def _generate_alert_id(self) -> str:
        """生成告警ID"""
        # 基于检测信息生成唯一ID
        info_str = f"{self.detection.get('class_name', '')}_{self.detection.get('confidence', 0)}_{self.timestamp}"
        return hashlib.md5(info_str.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'class_name': self.detection.get('class_name', ''),
            'class_id': self.detection.get('class_id', -1),
            'confidence': self.detection.get('confidence', 0.0),
            'bbox': self.detection.get('bbox', []),
            'threshold': self.detection.get('threshold', 0.5),
            'image_path': self.image_path,
            'image_url': self.image_url
        }


class DebounceManager:
    """防抖管理器"""
    
    def __init__(self, debounce_time: int = 60):
        self.debounce_time = debounce_time
        self.alert_history = {}  # {alert_key: last_alert_time}
    
    def should_alert(self, detection: Dict[str, Any]) -> bool:
        """判断是否应该触发告警"""
        # 生成告警键（基于类别和位置）
        alert_key = self._generate_alert_key(detection)
        current_time = time.time()
        
        # 检查是否在防抖时间内
        if alert_key in self.alert_history:
            last_alert_time = self.alert_history[alert_key]
            if current_time - last_alert_time < self.debounce_time:
                return False
        
        # 更新告警时间
        self.alert_history[alert_key] = current_time
        
        # 清理过期的告警记录
        self._cleanup_old_alerts(current_time)
        
        return True
    
    def _generate_alert_key(self, detection: Dict[str, Any]) -> str:
        """生成告警键"""
        class_name = detection.get('class_name', '')
        bbox = detection.get('bbox', [])
        
        # 基于类别和边界框中心点生成键
        if len(bbox) >= 4:
            center_x = (bbox[0] + bbox[2]) // 2
            center_y = (bbox[1] + bbox[3]) // 2
            # 将坐标分块，避免过于精确的位置匹配
            grid_x = center_x // 100
            grid_y = center_y // 100
            key = f"{class_name}_{grid_x}_{grid_y}"
        else:
            key = f"{class_name}_unknown"
        
        return key
    
    def _cleanup_old_alerts(self, current_time: float):
        """清理过期的告警记录"""
        expired_keys = []
        for key, alert_time in self.alert_history.items():
            if current_time - alert_time > self.debounce_time * 2:  # 保留2倍防抖时间
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.alert_history[key]
        
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期的告警记录")


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: ConfigParser):
        self.config = config
        self.alert_config = config.get_alert_config()
        self.debounce_manager = DebounceManager(
            self.alert_config.get('debounce_time', 60)
        )
        self.image_processor = ImageProcessor()
        
        # 告警统计
        self.total_alerts = 0
        self.saved_images = 0
        self.failed_saves = 0
        
        # 确保图片保存目录存在
        self._ensure_image_directory()
    
    def _ensure_image_directory(self):
        """确保图片保存目录存在"""
        image_path = self.alert_config.get('image_path', '/app/alert_images')
        # 使用兼容路径
        image_path = self.config.container_config.get_compatible_path(image_path)
        try:
            os.makedirs(image_path, exist_ok=True)
            logger.info(f"告警图片保存目录(兼容模式): {image_path}")
        except Exception as e:
            logger.error(f"创建图片保存目录失败: {e}")
    
    def process_detections(self, detections: List[Dict[str, Any]], 
                          frame, timestamp: float) -> List[AlertInfo]:
        """处理检测结果，生成告警"""
        alerts = []
        
        for detection in detections:
            # 检查置信度是否超过阈值
            confidence = detection.get('confidence', 0.0)
            threshold = detection.get('threshold', 0.5)
            
            if confidence < threshold:
                continue
            
            # 检查防抖
            if not self.debounce_manager.should_alert(detection):
                logger.debug(f"告警被防抖过滤: {detection.get('class_name', '')} "
                           f"置信度: {confidence:.3f}")
                continue
            
            # 创建告警信息
            alert_info = AlertInfo(detection, frame, timestamp)
            
            # 保存告警图片
            if self.alert_config.get('save_images', True):
                self._save_alert_image(alert_info)
            
            alerts.append(alert_info)
            self.total_alerts += 1
            
            # 记录告警日志
            logger.log_alert(
                "目标检测告警",
                confidence,
                detection.get('class_name', ''),
                alert_info.image_path
            )
        
        return alerts
    
    def _save_alert_image(self, alert_info: AlertInfo) -> bool:
        """保存告警图片"""
        try:
            # 生成图片文件名
            timestamp_str = datetime.fromtimestamp(alert_info.timestamp).strftime('%Y%m%d_%H%M%S_%f')[:-3]
            class_name = alert_info.detection.get('class_name', 'unknown')
            filename = f"{class_name}_{timestamp_str}_{alert_info.alert_id}.jpg"
            
            # 构建保存路径
            image_path = self.alert_config.get('image_path', '/app/alert_images')
            # 使用兼容路径
            image_path = self.config.container_config.get_compatible_path(image_path)
            full_path = os.path.join(image_path, filename)
            
            # 在图像上绘制检测结果
            detection_image = self._draw_detection_on_image(alert_info)
            
            # 保存图片
            quality = self.alert_config.get('image_quality', 95)
            success = self.image_processor.save_image(detection_image, full_path, quality)
            
            if success:
                alert_info.image_path = full_path
                alert_info.image_url = self._generate_image_url(filename)
                self.saved_images += 1
                logger.info(f"告警图片保存成功: {filename}")
                return True
            else:
                self.failed_saves += 1
                logger.error(f"告警图片保存失败: {filename}")
                return False
                
        except Exception as e:
            self.failed_saves += 1
            logger.error(f"保存告警图片异常: {e}")
            return False
    
    def _draw_detection_on_image(self, alert_info: AlertInfo):
        """在图像上绘制检测结果"""
        try:
            # 获取类别信息
            class_names = [alert_info.detection.get('class_name', 'unknown')]
            class_colors = [[255, 0, 0]]  # 红色
            
            # 绘制检测结果
            detections = [alert_info.detection]
            result_image = self.image_processor.draw_detections(
                alert_info.frame,
                detections,
                class_names,
                class_colors
            )
            
            # 添加告警信息
            result_image = self._add_alert_info_to_image(result_image, alert_info)
            
            # 绘制ROI区域（如果存在）
            if 'roi' in alert_info.detection:
                roi = alert_info.detection['roi']
                if roi and isinstance(roi, dict) and 'x' in roi and 'y' in roi and 'w' in roi and 'h' in roi:
                    import cv2
                    # 绘制ROI矩形 - 使用LINE_AA替代LINE_DASHED
                    x, y, w, h = roi['x'], roi['y'], roi['w'], roi['h']
                    cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # 添加ROI标签
                    cv2.putText(result_image, "ROI", (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            return result_image
            
        except Exception as e:
            logger.error(f"绘制检测结果失败: {e}")
            return alert_info.frame
    
    def _add_alert_info_to_image(self, image, alert_info: AlertInfo):
        """在图像上添加告警信息"""
        try:
            import cv2
            
            # 添加时间戳
            timestamp_str = datetime.fromtimestamp(alert_info.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            cv2.putText(image, f"Alert Time: {timestamp_str}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 添加告警ID
            cv2.putText(image, f"Alert ID: {alert_info.alert_id}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            return image
            
        except Exception as e:
            logger.error(f"添加告警信息到图像失败: {e}")
            return image
    
    def _generate_image_url(self, filename: str) -> str:
        """生成图片URL"""
        # 这里可以根据实际部署环境生成URL
        # 例如：http://atlas-500:8080/images/alert_images/filename
        base_url = os.environ.get('IMAGE_BASE_URL', 'http://localhost:8080/images')
        return f"{base_url}/alert_images/{filename}"
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """获取告警统计信息"""
        return {
            'total_alerts': self.total_alerts,
            'saved_images': self.saved_images,
            'failed_saves': self.failed_saves,
            'debounce_history_count': len(self.debounce_manager.alert_history)
        }
    
    def should_debounce_alert(self, alert_key: str, debounce_interval: int) -> bool:
        """检查是否应该防抖过滤告警（兼容旧接口）"""
        # 临时创建一个检测对象来使用现有的防抖逻辑
        # 从alert_key中解析信息
        parts = alert_key.split('_', 2)
        if len(parts) >= 3:
            class_name = parts[2]
        else:
            class_name = 'unknown'
        
        # 创建临时检测对象
        temp_detection = {
            'class_name': class_name,
            'bbox': [0, 0, 100, 100]  # 默认边界框
        }
        
        # 临时更新防抖时间
        old_debounce_time = self.debounce_manager.debounce_time
        self.debounce_manager.debounce_time = debounce_interval
        
        # 检查是否应该告警（返回相反值，因为原方法询问是否应该防抖）
        should_alert = self.debounce_manager.should_alert(temp_detection)
        
        # 恢复原防抖时间
        self.debounce_manager.debounce_time = old_debounce_time
        
        # 返回是否应该防抖（与should_alert相反）
        return not should_alert
    
    def record_alert_time(self, alert_key: str):
        """记录告警时间（兼容旧接口）"""
        # 这个方法现在由DebounceManager内部处理，这里只是为了兼容性
        pass
    
    def save_alert_image(self, frame, detection: Dict[str, Any], task_name: str, class_name: str) -> Optional[str]:
        """保存告警图片（兼容旧接口）"""
        try:
            # 创建AlertInfo对象
            alert_info = AlertInfo(detection, frame, time.time())
            
            # 保存图片
            if self._save_alert_image(alert_info):
                return alert_info.image_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"保存告警图片失败: {e}")
            self.failed_saves += 1
            return None

    def reset_stats(self):
        """重置统计信息"""
        self.total_alerts = 0
        self.saved_images = 0
        self.failed_saves = 0
        self.debounce_manager.alert_history.clear()
        logger.info("告警统计已重置") 