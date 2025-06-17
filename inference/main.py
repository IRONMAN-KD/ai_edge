from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
from typing import Optional
import cv2
import numpy as np
from datetime import datetime, timedelta
from database.database import DatabaseManager
from database.models import InferenceRecordCreate, AlertCreate
from database.repositories import ModelRepository, InferenceRepository, TaskRepository, AlertRepository
from models.factory import ModelFactory
from utils.logger import Logger
from utils.exceptions import (
    InferenceError, ModelNotFoundError, ModelLoadError, ModelInferenceError,
    FileNotFoundError, FileUploadError, RecordNotFoundError, DatabaseOperationError
)

app = FastAPI(title="AI Edge Inference Service")

# 初始化日志记录器
logger = Logger()

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
@app.exception_handler(InferenceError)
async def inference_exception_handler(request, exc: InferenceError):
    """处理自定义异常"""
    logger.error(f"推理服务错误: {exc.message}", extra={
        "error_code": exc.error_code,
        "path": request.url.path,
        "method": request.method
    })
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "error_code": exc.error_code
        }
    )

# 依赖注入
def get_model_repository():
    return ModelRepository()

def get_inference_repository():
    return InferenceRepository()

def get_task_repository():
    return TaskRepository()

def get_alert_repository():
    return AlertRepository()

# 工具函数
def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """保存上传的文件"""
    try:
        with open(destination, "wb") as buffer:
            content = upload_file.file.read()
            buffer.write(content)
        return destination
    except Exception as e:
        raise FileUploadError(upload_file.filename, str(e))
    finally:
        upload_file.file.close()

# 路由
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    try:
        # 创建上传目录
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成文件路径
        file_path = os.path.join(upload_dir, file.filename)
        
        # 保存文件
        save_upload_file(file, file_path)
        
        logger.info(f"文件上传成功: {file.filename}")
        
        return {
            "path": file_path,
            "url": f"/uploads/{file.filename}"
        }
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise

@app.post("/inference/{task_id}")
async def run_inference(
    task_id: int,
    image_path: str,
    user_id: int,
    background_tasks: BackgroundTasks,
    model_repo: ModelRepository = Depends(get_model_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
    inference_repo: InferenceRepository = Depends(get_inference_repository),
    alert_repo: AlertRepository = Depends(get_alert_repository)
):
    """执行推理并根据任务配置创建告警"""
    try:
        # 检查输入文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)
        
        # 获取任务信息
        task_info = task_repo.get_task_by_id(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        
        model_id = task_info.model_id
        # 获取模型信息
        model_info = model_repo.get_model_by_id(model_id)
        if not model_info:
            raise ModelNotFoundError(model_id)
        
        # 创建推理记录
        try:
            record = InferenceRecordCreate(
                model_id=model_id,
                user_id=user_id,
                input_path=image_path,
                output_path="",  # 将在后台任务中更新
                status="processing"
            )
            inference_record = inference_repo.create_record(record)
        except Exception as e:
            raise DatabaseOperationError("创建推理记录", str(e))
        
        # 在后台执行推理
        async def process_inference():
            try:
                # 创建模型实例
                model = ModelFactory.create_model(
                    model_type=model_info.type,
                    model_path=model_info.file_path,
                )

                # 读取图像
                image = cv2.imread(image_path)
                if image is None:
                    raise FileNotFoundError(f"Failed to read image at {image_path}")
                
                # 执行推理
                result, inference_time = model.inference(image)
                
                # 保存结果图像
                output_dir = "alert_images"
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"alert_{task_id}_{timestamp}.jpg"
                output_path = os.path.join(output_dir, output_filename)
                
                # 读取原始图像并绘制结果
                output_image = model.draw_result(image, result)
                cv2.imwrite(output_path, output_image)
                
                # 更新推理记录
                inference_repo.update_record(
                    inference_record.id,
                    output_path=output_path,
                    inference_time=inference_time,
                    status="completed"
                )

                # 告警检查和创建
                detections = result.get("detections", [])
                for detection in detections:
                    confidence = detection.get('score', 0)
                    class_name = detection.get('label', 'unknown')

                    if confidence >= task_info.confidence_threshold:
                        # Check for debouncing
                        latest_alert = alert_repo.get_latest_alert_for_task(task_id, class_name)
                        
                        can_create_alert = True
                        if latest_alert:
                            time_since_last_alert = datetime.now() - latest_alert.created_at
                            if time_since_last_alert < timedelta(seconds=task_info.alert_debounce_interval):
                                can_create_alert = False
                        
                        if can_create_alert:
                            alert_repo.create_alert(AlertCreate(
                                title=f"检测到: {class_name}",
                                description=f"在任务 '{task_info.name}' 中检测到高置信度的 '{class_name}'.",
                                confidence=confidence,
                                task_id=task_id,
                                task_name=task_info.name,
                                model_name=model_info.name,
                                alert_image=output_path,
                                detection_class=class_name
                            ))

            except Exception as e:
                # 更新推理记录为失败状态
                inference_repo.update_record(
                    inference_record.id,
                    status="failed"
                )
                logger.error(f"Inference processing failed for task {task_id}: {str(e)}")
                raise
        
        background_tasks.add_task(process_inference)
        return {"message": "推理任务已开始", "record_id": inference_record.id}
        
    except Exception as e:
        logger.error(f"启动推理任务失败: {str(e)}")
        raise

@app.get("/inference/status/{record_id}")
async def get_inference_status(
    record_id: int,
    inference_repo: InferenceRepository = Depends(get_inference_repository)
):
    """获取推理状态"""
    try:
        record = inference_repo.get_record_by_id(record_id)
        if not record:
            raise RecordNotFoundError(record_id)
        return record
    except Exception as e:
        logger.error(f"获取推理状态失败: {str(e)}")
        raise 