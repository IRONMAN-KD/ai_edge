"""
视频输入模块
支持 RTSP/USB 摄像头/本地视频文件等输入源
"""

import cv2
import time
import threading
import queue
from typing import Optional, Callable, Dict, Any
from utils.logging import logger
from utils.config_parser import ConfigParser


class VideoCapture:
    """视频捕获器"""
    
    def __init__(self, source: str, buffer_size: int = 10, reconnect_delay: int = 5, max_reconnect_attempts: int = 10):
        self.source = source
        self.buffer_size = buffer_size
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.cap = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=buffer_size)
        self.thread = None
        self.last_frame = None
        self.last_frame_time = 0
        
        self._init_capture()
    
    def _init_capture(self, is_reconnecting=False):
        """初始化视频捕获"""
        if self.cap:
            self.cap.release()
            self.cap = None

        try:
            # 根据源类型选择不同的初始化方式
            if self.source.startswith('rtsp://'):
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            elif self.source.startswith('/dev/'):
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)
            else:
                self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"无法打开视频源: {self.source}")
            
            if not is_reconnecting:
                logger.info(f"视频源初始化成功: {self.source}")
            else:
                logger.info(f"视频源重连成功: {self.source}")

            return True
            
        except Exception as e:
            if not is_reconnecting:
                logger.error(f"视频源初始化失败: {e}")
            else:
                logger.warning(f"视频源重连尝试失败: {e}")
            self.cap = None
            return False
    
    def start(self):
        """开始捕获"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("视频捕获线程已启动")
    
    def stop(self):
        """停止捕获"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
        
        logger.info("视频捕获已停止")
    
    def _capture_loop(self):
        """捕获循环"""
        reconnect_attempts = 0
        while self.is_running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    raise ConnectionError("视频捕获未打开或已断开")

                ret, frame = self.cap.read()
                if not ret:
                    logger.warning(f"无法从源 {self.source} 读取视频帧，尝试重连...")
                    raise ConnectionError("无法读取视频帧")
                
                # 重置重连计数器
                reconnect_attempts = 0
                
                # 更新最新帧
                self.last_frame = frame
                self.last_frame_time = time.time()
                
                # 添加到队列（非阻塞）
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    # 队列满时，移除最旧的帧
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
                
            except Exception as e:
                logger.error(f"视频捕获错误: {e}")
                
                if isinstance(e, ConnectionError):
                    self.cap.release()
                    self.cap = None
                    
                    while self.is_running and reconnect_attempts < self.max_reconnect_attempts:
                        reconnect_attempts += 1
                        logger.info(f"第 {reconnect_attempts}/{self.max_reconnect_attempts} 次尝试重连至 {self.source}...")
                        time.sleep(self.reconnect_delay)
                        if self._init_capture(is_reconnecting=True):
                            logger.info(f"成功重连至 {self.source}")
                            break
                        else:
                            logger.warning(f"重连失败，将在 {self.reconnect_delay} 秒后重试...")
                    
                    if self.cap is None or not self.cap.isOpened():
                        logger.error(f"重连 {self.max_reconnect_attempts} 次后依然失败，停止捕获线程。")
                        self.is_running = False
                else:
                    # 对于其他类型的错误，短暂休眠后继续
                    time.sleep(0.1)
    
    def get_frame(self) -> Optional[tuple]:
        """获取最新帧"""
        if self.last_frame is not None:
            return self.last_frame, self.last_frame_time
        return None
    
    def get_frame_from_queue(self, timeout: float = 0.1) -> Optional[tuple]:
        """从队列获取帧"""
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return frame, time.time()
        except queue.Empty:
            return None
    
    def get_properties(self) -> Dict[str, Any]:
        """获取视频属性"""
        if not self.cap:
            return {}
        
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'source': self.source
        }


class VideoProcessor:
    """视频处理器"""
    
    def __init__(self, config: ConfigParser):
        self.config = config
        self.video_config = config.get_video_config()
        self.capture = None
        self.is_running = False
        self.processing_thread = None
        self.frame_callback = None
        
        # 性能统计
        self.frame_count = 0
        self.start_time = 0
        self.current_fps = 0.0
        
        self._init_capture()
    
    def _init_capture(self):
        """初始化视频捕获"""
        try:
            source = self.video_config.get('source', '0')
            buffer_size = self.video_config.get('buffer_size', 10)
            reconnect_delay = self.video_config.get('reconnect_delay_seconds', 5)
            max_attempts = self.video_config.get('max_reconnect_attempts', 10)
            
            self.capture = VideoCapture(
                source, 
                buffer_size,
                reconnect_delay=reconnect_delay,
                max_reconnect_attempts=max_attempts
            )
            
            # 设置视频属性
            self._set_video_properties()
            
            logger.info("视频处理器初始化成功")
            
        except Exception as e:
            logger.error(f"视频处理器初始化失败: {e}")
            raise
    
    def _set_video_properties(self):
        """设置视频属性"""
        try:
            cap = self.capture.cap
            if not cap:
                return
            
            # 设置分辨率
            width = self.video_config.get('width', 1920)
            height = self.video_config.get('height', 1080)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # 设置帧率
            target_fps = self.video_config.get('fps', 30)
            cap.set(cv2.CAP_PROP_FPS, target_fps)
            
            # 设置缓冲区大小
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            logger.info(f"视频属性设置完成: {width}x{height} @ {target_fps}fps")
            
        except Exception as e:
            logger.error(f"设置视频属性失败: {e}")
    
    def set_frame_callback(self, callback: Callable):
        """设置帧处理回调"""
        self.frame_callback = callback
    
    def start(self):
        """开始处理"""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = time.time()
        self.frame_count = 0
        
        # 启动视频捕获
        self.capture.start()
        
        # 启动处理线程
        self.processing_thread = threading.Thread(
            target=self._processing_loop, 
            daemon=True
        )
        self.processing_thread.start()
        
        logger.info("视频处理已启动")
    
    def stop(self):
        """停止处理"""
        self.is_running = False
        
        if self.capture:
            self.capture.stop()
        
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        
        logger.info("视频处理已停止")
    
    def _processing_loop(self):
        """处理循环"""
        while self.is_running:
            try:
                # 获取帧
                frame_data = self.capture.get_frame_from_queue(timeout=0.1)
                if frame_data is None:
                    continue
                
                frame, timestamp = frame_data
                
                # 更新统计
                self.frame_count += 1
                elapsed_time = time.time() - self.start_time
                if elapsed_time > 0:
                    self.current_fps = self.frame_count / elapsed_time
                
                # 调用回调函数
                if self.frame_callback:
                    self.frame_callback(frame, timestamp)
                
            except Exception as e:
                logger.error(f"视频处理错误: {e}")
                time.sleep(0.1)
    
    def get_frame(self) -> Optional[tuple]:
        """获取当前帧"""
        if self.capture:
            return self.capture.get_frame()
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        elapsed_time = time.time() - self.start_time
        
        return {
            'frame_count': self.frame_count,
            'elapsed_time': elapsed_time,
            'current_fps': self.current_fps,
            'avg_fps': self.frame_count / elapsed_time if elapsed_time > 0 else 0.0
        }
    
    def get_video_info(self) -> Dict[str, Any]:
        """获取视频信息"""
        if self.capture:
            return self.capture.get_properties()
        return {}
    
    def is_healthy(self) -> bool:
        """检查视频源是否健康"""
        if not self.capture or not self.capture.cap:
            return False
        
        return self.capture.cap.isOpened()


class VideoInputManager:
    """视频输入管理器"""
    
    def __init__(self, config: ConfigParser):
        self.config = config
        self.processor = None
        self.detection_callback = None
        
        self._init_processor()
    
    def _init_processor(self):
        """初始化视频处理器"""
        try:
            self.processor = VideoProcessor(self.config)
            logger.info("视频输入管理器初始化成功")
        except Exception as e:
            logger.error(f"视频输入管理器初始化失败: {e}")
            raise
    
    def set_detection_callback(self, callback: Callable):
        """设置检测回调"""
        self.detection_callback = callback
        if self.processor:
            self.processor.set_frame_callback(callback)
    
    def start(self):
        """开始视频输入"""
        if self.processor:
            self.processor.start()
    
    def stop(self):
        """停止视频输入"""
        if self.processor:
            self.processor.stop()
    
    def get_frame(self) -> Optional[tuple]:
        """获取当前帧"""
        if self.processor:
            return self.processor.get_frame()
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self.processor:
            return {
                'video_info': self.processor.get_video_info(),
                'performance': self.processor.get_performance_stats(),
                'healthy': self.processor.is_healthy()
            }
        return {}
    
    def cleanup(self):
        """清理资源"""
        if self.processor:
            self.processor.stop() 