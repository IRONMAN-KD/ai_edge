"""
视频输入模块
支持 RTSP/USB 摄像头/本地视频文件等输入源
"""

import cv2
import time
import threading
import queue
import subprocess
import tempfile
import os
import atexit
import numpy as np
from typing import Optional, Callable, Dict, Any, Tuple, Union
from utils.logging import logger
from utils.config_parser import ConfigParser
from urllib.parse import urlparse


class EnhancedVideoCapture:
    """增强版视频捕获类，支持多种后备方案"""
    
    def __init__(self, source: Union[str, int]):
        self.source = source
        self.cap = None
        self.is_opened = False
        self.backend = None
        self.temp_file = None
        self.ffmpeg_process = None
        self.use_fallback = False
        
        # 注册清理函数
        atexit.register(self.cleanup)
        
        self._initialize_capture()
    
    def _is_network_stream(self, source: Union[str, int]) -> bool:
        """检查是否为网络流"""
        if isinstance(source, int):
            return False
        
        parsed = urlparse(str(source))
        return parsed.scheme in ['rtsp', 'rtmp', 'http', 'https']
    
    def _try_opencv_optimized(self) -> bool:
        """尝试使用优化参数的OpenCV"""
        try:
            if self._is_network_stream(self.source):
                # 尝试不同的后端
                backends = [
                    cv2.CAP_FFMPEG,
                    cv2.CAP_GSTREAMER,
                    cv2.CAP_ANY
                ]
                
                for backend in backends:
                    logger.info(f"尝试OpenCV后端: {backend}")
                    cap = cv2.VideoCapture(str(self.source), backend)
                    
                    if backend == cv2.CAP_FFMPEG:
                        # 为RTSP优化参数
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        cap.set(cv2.CAP_PROP_FPS, 25)
                        
                        # RTSP特定参数
                        if str(self.source).startswith('rtsp'):
                            # 设置网络超时
                            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
                            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
                    
                    if cap.isOpened():
                        # 测试读取
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            logger.info(f"OpenCV成功，后端: {backend}")
                            self.cap = cap
                            self.backend = f"opencv_{backend}"
                            return True
                        cap.release()
            else:
                # 本地设备或文件
                self.cap = cv2.VideoCapture(self.source)
                if self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        self.backend = "opencv_local"
                        # 重新定位到开始
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        return True
                    self.cap.release()
                    
        except Exception as e:
            logger.error(f"OpenCV初始化失败: {e}")
            
        return False
    
    def _try_imageio_fallback(self) -> bool:
        """尝试使用imageio作为后备方案"""
        try:
            import imageio
            
            if not self._is_network_stream(self.source):
                return False
                
            logger.info("尝试imageio后备方案")
            
            # 创建临时文件用于ffmpeg输出
            self.temp_file = tempfile.NamedTemporaryFile(suffix='.mjpeg', delete=False)
            self.temp_file.close()
            
            # 使用ffmpeg转换流
            cmd = [
                'ffmpeg', '-y',
                '-rtsp_transport', 'tcp',
                '-i', str(self.source),
                '-f', 'mjpeg',
                '-q:v', '5',
                '-r', '10',  # 降低帧率减少负载
                self.temp_file.name
            ]
            
            logger.info(f"启动ffmpeg命令: {' '.join(cmd)}")
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            # 等待一些数据写入
            time.sleep(3)
            
            # 尝试用imageio读取
            try:
                reader = imageio.get_reader(self.temp_file.name, 'ffmpeg')
                # 测试读取第一帧
                frame = reader.get_next_data()
                if frame is not None:
                    logger.info("imageio后备方案成功")
                    self.cap = reader
                    self.backend = "imageio"
                    self.use_fallback = True
                    return True
            except Exception as e:
                logger.error(f"imageio读取失败: {e}")
                
        except ImportError:
            logger.warning("imageio未安装，跳过此后备方案")
        except Exception as e:
            logger.error(f"imageio后备方案失败: {e}")
            
        return False
    
    def _try_av_fallback(self) -> bool:
        """尝试使用PyAV作为后备方案"""
        try:
            import av
            
            if not self._is_network_stream(self.source):
                return False
                
            logger.info("尝试PyAV后备方案")
            
            container = av.open(str(self.source), options={
                'rtsp_transport': 'tcp',
                'stimeout': '10000000',  # 10秒超时
            })
            
            # 测试获取第一帧
            for frame in container.decode(video=0):
                if frame:
                    logger.info("PyAV后备方案成功")
                    self.cap = container
                    self.backend = "pyav"
                    self.use_fallback = True
                    return True
                break
                
        except ImportError:
            logger.warning("PyAV未安装，跳过此后备方案")
        except Exception as e:
            logger.error(f"PyAV后备方案失败: {e}")
            
        return False
    
    def _initialize_capture(self):
        """初始化视频捕获，按优先级尝试不同方案"""
        logger.info(f"初始化视频源: {self.source}")
        
        # 方案1: 优化的OpenCV
        if self._try_opencv_optimized():
            self.is_opened = True
            return
            
        # 方案2: imageio后备
        if self._try_imageio_fallback():
            self.is_opened = True
            return
            
        # 方案3: PyAV后备
        if self._try_av_fallback():
            self.is_opened = True
            return
            
        logger.error("所有视频捕获方案都失败了")
        self.is_opened = False
    
    def isOpened(self) -> bool:
        """检查是否成功打开"""
        return self.is_opened
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取一帧"""
        if not self.is_opened or self.cap is None:
            return False, None
            
        try:
            if self.backend == "imageio":
                try:
                    frame = self.cap.get_next_data()
                    return True, frame
                except Exception:
                    return False, None
                    
            elif self.backend == "pyav":
                try:
                    for frame in self.cap.decode(video=0):
                        return True, frame.to_ndarray(format='bgr24')
                    return False, None
                except Exception:
                    return False, None
                    
            else:  # OpenCV
                return self.cap.read()
                
        except Exception as e:
            logger.error(f"读取帧失败: {e}")
            return False, None
    
    def get(self, prop):
        """获取属性"""
        if not self.is_opened or self.cap is None:
            return 0
            
        if hasattr(self.cap, 'get'):
            return self.cap.get(prop)
        return 0
    
    def set(self, prop, value):
        """设置属性"""
        if not self.is_opened or self.cap is None:
            return False
            
        if hasattr(self.cap, 'set'):
            return self.cap.set(prop, value)
        return False
    
    def cleanup(self):
        """清理资源"""
        if self.cap is not None:
            if hasattr(self.cap, 'release'):
                self.cap.release()
            elif hasattr(self.cap, 'close'):
                self.cap.close()
            self.cap = None
            
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except:
                self.ffmpeg_process.kill()
            self.ffmpeg_process = None
            
        if self.temp_file and os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except:
                pass
            self.temp_file = None
    
    def release(self):
        """释放资源"""
        self.cleanup()
        self.is_opened = False

# 保持原有的VideoCapture类作为旧版兼容，但使用增强版实现
class VideoCapture(EnhancedVideoCapture):
    """原有VideoCapture类的兼容接口"""
    
    def __init__(self, source, threaded=False):
        self.threaded = threaded
        self.last_frame = None
        self.frame_lock = threading.Lock()
        self.thread = None
        self.running = False
        
        super().__init__(source)
        
        if self.threaded and self.is_opened:
            self.start_thread()
    
    def start_thread(self):
        """启动读取线程"""
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._read_thread)
            self.thread.daemon = True
            self.thread.start()
    
    def _read_thread(self):
        """后台读取线程"""
        while self.running and self.is_opened:
            ret, frame = super().read()
            if ret:
                with self.frame_lock:
                    self.last_frame = frame
            time.sleep(0.03)  # ~30fps
    
    def read(self):
        """读取帧（支持线程模式）"""
        if self.threaded:
            with self.frame_lock:
                if self.last_frame is not None:
                    return True, self.last_frame.copy()
                return False, None
        else:
            return super().read()
    
    def stop(self):
        """停止线程和释放资源"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        self.cleanup()

# 向后兼容的工厂函数
def create_video_capture(source, threaded=False):
    """创建视频捕获对象的工厂函数"""
    return VideoCapture(source, threaded=threaded)


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
            
            # 使用兼容的新接口
            self.capture = VideoCapture(source, threaded=True)
            
            # 设置视频属性
            self._set_video_properties()
            
            logger.info("视频处理器初始化成功")
            
        except Exception as e:
            logger.error(f"视频处理器初始化失败: {e}")
            raise
    
    def _set_video_properties(self):
        """设置视频属性"""
        try:
            if not self.capture.isOpened():
                return
            
            # 设置分辨率
            width = self.video_config.get('width', 1920)
            height = self.video_config.get('height', 1080)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # 设置帧率
            target_fps = self.video_config.get('fps', 30)
            self.capture.set(cv2.CAP_PROP_FPS, target_fps)
            
            # 设置缓冲区大小
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
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
                ret, frame = self.capture.read()
                if not ret or frame is None:
                    time.sleep(0.03)  # 短暂等待
                    continue
                
                timestamp = time.time()
                
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
        if not self.capture:
            return None
        
        ret, frame = self.capture.read()
        if ret:
            return frame, time.time()
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
        if not self.capture:
            return {}
        
        return {
            'width': int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.capture.get(cv2.CAP_PROP_FPS),
            'frame_count': int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT)),
            'source': self.video_config.get('source', '0')
        }
    
    def is_healthy(self) -> bool:
        """检查视频源是否健康"""
        if not self.capture:
            return False
        
        return self.capture.isOpened()


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