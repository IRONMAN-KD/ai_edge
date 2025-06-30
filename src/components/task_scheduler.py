"""
任务调度器
负责管理和执行检测任务
"""

import threading
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from database.repositories import TaskRepository, AlertRepository, ModelRepository
from database.models import Task, AlertCreate
from components.video_input import VideoProcessor
from components.alert_manager import AlertManager
from inference.factory import InferenceFactory
from utils.logging import logger
from utils.config_parser import ConfigParser


class TaskExecutor:
    """单个任务执行器"""
    
    def __init__(self, task: Task, config: ConfigParser):
        self.task = task
        self.config = config
        self.is_running = False
        self.video_processors = {}
        self.inference_engine = None
        self.alert_manager = None
        self.last_detection_time = {}
        self.execution_thread = None
        
        self._initialize()
    
    def _initialize(self):
        """初始化任务执行器"""
        try:
            logger.info(f"开始初始化任务执行器: {self.task.name}")
            self.alert_manager = AlertManager(self.config)
            logger.info(f"AlertManager 初始化完成")
            
            # 手动处理video_sources字段，确保它是列表格式
            if isinstance(self.task.video_sources, str):
                import json
                try:
                    self.task.video_sources = json.loads(self.task.video_sources)
                    logger.info(f"已将任务 {self.task.name} 的 video_sources 从字符串转换为列表")
                except json.JSONDecodeError:
                    logger.error(f"任务 {self.task.name} 的 video_sources JSON 解析失败")
                    self.task.video_sources = []
            
            # 调试信息：检查video_sources的数据类型和内容
            logger.info(f"任务 {self.task.name} 的 video_sources 类型: {type(self.task.video_sources)}")
            logger.info(f"任务 {self.task.name} 的 video_sources 内容: {self.task.video_sources}")
            
            logger.info(f"开始获取模型信息")
            model_repo = ModelRepository()
            model = model_repo.get_model_by_id(self.task.model_id)
            if not model:
                raise ValueError(f"模型不存在: {self.task.model_id}")
            logger.info(f"模型获取成功: {model.name}")
            
            # 处理模型路径，确保使用绝对路径
            model_path = model.file_path
            if not os.path.isabs(model_path):
                # 如果是相对路径，添加模型基础目录
                model_path = os.path.join('/app/models', model_path)
            logger.info(f"模型路径: {model_path}")
            
            platform = self.config.get('platform', 'cpu_arm')
            # 如果platform是字典，提取name字段
            if isinstance(platform, dict):
                platform = platform.get('name', 'cpu_arm')
            inference_config = self.config.get_section('inference') or {}
            logger.info(f"开始创建推理引擎，平台: {platform}")
            
            self.inference_engine = InferenceFactory.create_engine(
                platform=platform,
                model_path=model_path,
                config=inference_config
            )
            logger.info(f"推理引擎创建成功")
            
            if not self.inference_engine.load_model(model_path):
                raise ValueError(f"模型加载失败: {model_path}")
            logger.info(f"模型加载成功")
            
            logger.info(f"开始处理视频源，共 {len(self.task.video_sources)} 个")
            for i, video_source in enumerate(self.task.video_sources):
                try:
                    logger.info(f"处理第 {i+1} 个 video_source: {video_source}, 类型: {type(video_source)}")
                    source_url = video_source.get('url')
                    logger.info(f"获取到 source_url: {source_url}, 类型: {type(source_url)}")
                    if source_url:
                        video_config = ConfigParser()
                        video_config.config = {
                            'video': {
                                'source': source_url,
                                'buffer_size': 5,
                                'fps_limit': 30
                            }
                        }
                        
                        logger.info(f"创建 VideoProcessor for {source_url}")
                        processor = VideoProcessor(video_config)
                        logger.info(f"VideoProcessor 创建成功，准备添加到字典")
                        self.video_processors[source_url] = processor
                        logger.info(f"VideoProcessor 已添加到字典，准备设置 last_detection_time")
                        self.last_detection_time[source_url] = 0
                        logger.info(f"last_detection_time 设置完成")
                except Exception as e:
                    logger.error(f"处理 video_source {video_source} 时出错: {e}")
                    import traceback
                    logger.error(f"错误堆栈: {traceback.format_exc()}")
                    raise
            
            logger.info(f"任务执行器初始化成功: {self.task.name}")
            
        except Exception as e:
            logger.error(f"任务执行器初始化失败: {e}")
            import traceback
            logger.error(f"初始化错误堆栈: {traceback.format_exc()}")
            raise
    
    def start(self):
        """启动任务执行"""
        if self.is_running:
            return
        
        self.is_running = True
        
        for processor in self.video_processors.values():
            processor.start()
        
        self.execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
        self.execution_thread.start()
        
        logger.info(f"任务开始执行: {self.task.name}")
    
    def stop(self):
        """停止任务执行"""
        self.is_running = False
        
        for processor in self.video_processors.values():
            processor.stop()
        
        if self.execution_thread:
            self.execution_thread.join(timeout=5.0)
        
        logger.info(f"任务停止执行: {self.task.name}")
    
    def _execution_loop(self):
        """执行循环"""
        while self.is_running:
            try:
                current_time = time.time()
                
                if not self._is_in_execution_time():
                    time.sleep(60)
                    continue
                
                for source_url, processor in self.video_processors.items():
                    if current_time - self.last_detection_time[source_url] < self.task.inference_interval:
                        continue
                    
                    frame_data = processor.get_frame()
                    if not frame_data:
                        continue
                    
                    frame, frame_time = frame_data
                    
                    detections, inference_time = self.inference_engine.detect(frame)
                    
                    # 根据任务的置信度阈值过滤检测结果
                    filtered_detections = [
                        d for d in detections 
                        if d.get('confidence', 0.0) >= self.task.confidence_threshold
                    ]
                    
                    self._process_detections(filtered_detections, source_url, frame, frame_time)
                    self.last_detection_time[source_url] = current_time
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"任务执行错误 {self.task.name}: {e}")
                time.sleep(1.0)
    
    def _is_in_execution_time(self) -> bool:
        """检查是否在执行时间范围内"""
        if self.task.schedule_type == 'continuous':
            return True
        
        now = datetime.now()
        current_time = now.time()
        current_weekday = str(now.isoweekday())
        
        try:
            start_time = datetime.strptime(self.task.start_time, '%H:%M:%S').time()
            end_time = datetime.strptime(self.task.end_time, '%H:%M:%S').time()
        except:
            return True
        
        time_in_range = start_time <= current_time <= end_time
        
        if self.task.schedule_type == 'daily':
            return time_in_range
        elif self.task.schedule_type == 'weekly':
            return time_in_range and current_weekday in self.task.schedule_days
        elif self.task.schedule_type == 'monthly':
            return time_in_range
        
        return True
    
    def _process_detections(self, detections: List[Dict], source_url: str, frame, frame_time):
        """处理检测结果"""
        if not detections:
            return
        
        for detection in detections:
            class_name = detection.get('class_name', 'unknown')
            confidence = detection.get('confidence', 0.0)
            
            # 修复：确保使用任务配置的告警冷却时间
            alert_key = f"{self.task.id}_{source_url}_{class_name}"
            debounce_interval = self.task.alert_debounce_interval
            logger.debug(f"检查告警是否需要防抖: {alert_key}, 冷却时间: {debounce_interval}秒")
            if self.alert_manager.should_debounce_alert(alert_key, debounce_interval):
                logger.debug(f"告警被防抖过滤: {class_name}, 冷却时间: {debounce_interval}秒")
                continue
            
            try:
                alert_image_path = self.alert_manager.save_alert_image(
                    frame, detection, self.task.name, class_name
                )
                
                # 获取video_name，防御式处理
                if self.task.video_sources and isinstance(self.task.video_sources[0], dict):
                    video_name = self.task.video_sources[0].get('name', '未知视频')
                else:
                    video_name = '未知视频'
                
                # 修复：使用北京时间（UTC+8）
                beijing_time = datetime.now() + timedelta(hours=8)
                alert_message = self.task.alert_message.format(
                    task_name=self.task.name,
                    time=beijing_time.strftime('%Y-%m-%d %H:%M:%S'),
                    class_name=class_name,
                    confidence=confidence * 100,
                    video_name=video_name
                )
                
                # 生成告警标题
                alert_title = f"{class_name}检测告警 - {self.task.name}"
                
                alert_create = AlertCreate(
                    title=alert_title,
                    description=alert_message,
                    level="medium",
                    confidence=confidence,
                    task_id=self.task.id,
                    task_name=self.task.name,
                    model_name=self.task.model.name if hasattr(self.task, 'model') and self.task.model else None,
                    alert_image=alert_image_path,
                    detection_class=class_name
                )
                
                alert_repo = AlertRepository()
                alert = alert_repo.create_alert(alert_create)
                
                logger.info(f"创建告警: {alert.id} - {class_name} (置信度: {confidence:.2f})")
                self.alert_manager.record_alert_time(alert_key)
                
            except Exception as e:
                logger.error(f"处理告警失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        return {
            "task_id": self.task.id,
            "task_name": self.task.name,
            "is_running": self.is_running,
            "video_sources": len(self.video_processors),
            "inference_engine_ready": self.inference_engine is not None,
            "last_detection_times": self.last_detection_time
        }


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, config: ConfigParser):
        self.config = config
        self.task_repo = TaskRepository()
        self.executors = {}
        self.is_running = False
        self.scheduler_thread = None
        self.executor_pool = ThreadPoolExecutor(max_workers=10)
        
    def start(self):
        """启动调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.is_running = False
        
        for executor in list(self.executors.values()):
            executor.stop()
        self.executors.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
        
        self.executor_pool.shutdown(wait=True)
        logger.info("任务调度器已停止")
    
    def _scheduler_loop(self):
        """调度循环"""
        while self.is_running:
            try:
                tasks = self.task_repo.get_all_tasks_for_scheduling()
                
                for task in tasks:
                    if task.is_enabled and task.id not in self.executors:
                        self._start_task(task)
                
                running_task_ids = set(self.executors.keys())
                active_task_ids = {task.id for task in tasks if task.is_enabled}
                
                for task_id in running_task_ids - active_task_ids:
                    self._stop_task(task_id)
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"调度器错误: {e}")
                time.sleep(60)
    
    def _start_task(self, task: Task):
        """启动任务"""
        try:
            executor = TaskExecutor(task, self.config)
            executor.start()
            self.executors[task.id] = executor
            
            self.task_repo.update_task_status(task.id, "running")
            logger.info(f"任务启动成功: {task.name}")
            
        except Exception as e:
            logger.error(f"任务启动失败 {task.name}: {e}")
            self.task_repo.update_task_status(task.id, "error")
    
    def _stop_task(self, task_id: int):
        """停止任务"""
        if task_id in self.executors:
            executor = self.executors[task_id]
            executor.stop()
            del self.executors[task_id]
            
            self.task_repo.update_task_status(task_id, "stopped")
            logger.info(f"任务停止: {task_id}")
    
    def start_task_manually(self, task_id: int):
        """手动启动任务"""
        task = self.task_repo.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        if task_id in self.executors:
            logger.warning(f"任务已在运行: {task.name}")
            return
        
        self._start_task(task)
    
    def stop_task_manually(self, task_id: int):
        """手动停止任务"""
        if task_id not in self.executors:
            logger.warning(f"任务未在运行: {task_id}")
            return
        
        self._stop_task(task_id)
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取正在运行的任务状态"""
        return [executor.get_status() for executor in self.executors.values()]
    
    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取指定任务状态"""
        if task_id in self.executors:
            return self.executors[task_id].get_status()
        return None
