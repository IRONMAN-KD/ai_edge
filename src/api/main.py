"""
AI Edge统一API服务
支持多平台推理引擎，集成数据库管理
"""

import os
import sys
import argparse
import logging
import asyncio
import numpy as np
import cv2
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import time
import concurrent.futures

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, APIRouter, status, WebSocket, WebSocketDisconnect, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference.factory import InferenceFactory
from utils.platform_detector import auto_detect_platform
from utils.config_parser import ConfigParser

# 数据库相关导入
from database.database import DatabaseManager
from database.repositories import ModelRepository, UserRepository, TaskRepository, AlertRepository, SystemConfigRepository
from database.models import (
    Model, ModelCreate, ModelUpdate, ModelStatusUpdate, User, UserCreate, Task, TaskCreate, Alert, AlertCreate,
    PaginatedModelResponse, PaginatedTaskResponse, PaginatedAlertResponse
)

# 组件导入
from components.task_scheduler import TaskScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
inference_engine = None
app_config = None
db_manager = None
model_repository = None
user_repository = None
task_repository = None
alert_repository = None
config_repository = None
current_model = None
task_scheduler = None

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 创建API路由器
api_router = APIRouter(prefix="/api/v1")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 AI Edge API服务启动中...")
    await initialize_services()
    
    yield
    
    # 关闭时清理
    logger.info("🛑 AI Edge API服务关闭中...")
    await cleanup_services()

# 创建FastAPI应用
app = FastAPI(
    title="AI Edge统一API",
    description="支持多平台的AI推理服务",
    version="2.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
ALERT_IMAGE_DIR = "alert_images"
if not os.path.exists(ALERT_IMAGE_DIR):
    os.makedirs(ALERT_IMAGE_DIR)
app.mount("/alert_images", StaticFiles(directory=ALERT_IMAGE_DIR), name="alert_images")

async def initialize_services():
    """初始化服务"""
    global inference_engine, app_config, db_manager, model_repository, user_repository
    global task_repository, alert_repository, config_repository, current_model, task_scheduler
    
    try:
        # 1. 初始化数据库连接（带重试机制）
        logger.info("🔗 初始化数据库连接...")
        
        # 数据库连接重试机制
        max_retries = 30
        retry_interval = 2
        db_connected = False
        
        # 初始化变量
        db_manager = None
        model_repository = None
        user_repository = None
        task_repository = None
        alert_repository = None
        config_repository = None
        
        for attempt in range(1, max_retries + 1):
            try:
                db_manager = DatabaseManager()
                model_repository = ModelRepository()
                user_repository = UserRepository()
                task_repository = TaskRepository()
                alert_repository = AlertRepository()
                config_repository = SystemConfigRepository()
                
                # 测试数据库连接
                test_query = "SELECT 1"
                db_manager.execute_query(test_query, fetch='one')
                logger.info("✅ 数据库连接成功")
                db_connected = True
                break
                
            except Exception as e:
                logger.warning(f"❌ 数据库连接失败 (尝试 {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    logger.info(f"等待 {retry_interval} 秒后重试...")
                    await asyncio.sleep(retry_interval)
                else:
                    logger.error("❌ 数据库连接最终失败，服务将在无数据库模式下启动")
        
        # 2. 获取平台参数
        platform = os.getenv('PLATFORM')
        if not platform:
            platform = auto_detect_platform()
            logger.info(f"自动检测到平台: {platform}")
        else:
            logger.info(f"使用指定平台: {platform}")
        
        # 3. 加载配置
        config_path = f"configs/platforms/{platform}/platform.yml"
        if os.path.exists(config_path):
            app_config = ConfigParser(config_path)
            logger.info(f"加载平台配置: {config_path}")
        else:
            logger.warning(f"平台配置文件不存在: {config_path}")
            app_config = ConfigParser()
        
        # 4. 从数据库获取激活的模型
        model_path = None
        if model_repository:
            active_models = model_repository.get_all_models(page=1, page_size=1, status='active')
        else:
            active_models = {'items': []}
        if active_models['items']:
            current_model = active_models['items'][0]  # 使用第一个激活的模型
            model_path = current_model.file_path
            logger.info(f"从数据库加载模型: {current_model.name} ({model_path})")
        else:
            # 如果数据库中没有模型，尝试从文件系统获取
            model_path = get_model_path(platform)
            if model_path:
                logger.info(f"从文件系统找到模型: {model_path}")
                # 将模型添加到数据库
                if model_repository:
                    try:
                        model_create = ModelCreate(
                            name="person_detection",
                            version="1.0",
                            type="object_detection",
                            file_path=model_path,
                            description="自动导入的人员检测模型"
                        )
                        current_model = model_repository.create_model(model_create)
                        logger.info(f"模型已添加到数据库: {current_model.id}")
                    except Exception as e:
                        logger.warning(f"添加模型到数据库失败: {e}")
                else:
                    logger.warning("数据库不可用，无法添加模型到数据库")
            else:
                logger.warning(f"未找到{platform}平台的模型文件，API服务将在无模型模式下启动")
        
        # 5. 创建推理引擎
        if model_path and os.path.exists(model_path):
            inference_config = app_config.get_section('inference') or {}
            inference_engine = InferenceFactory.create_engine(
                platform=platform,
                model_path=model_path,
                config=inference_config
            )
            
            # 加载模型
            if inference_engine.load_model(model_path):
                logger.info("✅ 推理引擎初始化成功")
            else:
                logger.error("❌ 推理引擎初始化失败")
                inference_engine = None
        else:
            logger.warning(f"模型文件不存在或未指定: {model_path}，推理功能将不可用")
            inference_engine = None
        
        # 6. 创建任务调度器
        task_scheduler = TaskScheduler(app_config)
        task_scheduler.start()
        
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        inference_engine = None

async def cleanup_services():
    """清理服务"""
    global inference_engine, task_scheduler
    
    if task_scheduler:
        try:
            task_scheduler.stop()
            logger.info("任务调度器已停止")
        except Exception as e:
            logger.error(f"任务调度器停止失败: {e}")
    
    if inference_engine:
        try:
            inference_engine.release_resources()
            logger.info("推理引擎资源已释放")
        except Exception as e:
            logger.error(f"资源释放失败: {e}")

def get_model_path(platform: str) -> Optional[str]:
    """获取模型文件路径"""
    model_dir = "models"
    
    if not os.path.exists(model_dir):
        return None
    
    # 平台特定的模型文件扩展名
    model_extensions = {
        'nvidia_gpu': ['.onnx', '.trt', '.engine'],
        'atlas_npu': ['.om'],
        'sophon': ['.bmodel'],
        'cpu_x86': ['.onnx'],
        'cpu_arm': ['.onnx']
    }
    
    extensions = model_extensions.get(platform, ['.onnx'])
    
    # 递归查找模型文件
    for root, dirs, files in os.walk(model_dir):
        for filename in files:
            for ext in extensions:
                if filename.endswith(ext):
                    model_path = os.path.join(root, filename)
                    logger.info(f"找到模型文件: {model_path}")
                    return model_path
    
    return None

# ==================== 基础端点 ====================

@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "AI Edge统一API服务",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    # 测试数据库连接
    db_status = "disconnected"
    if db_manager and model_repository:
        try:
            db_manager.execute_query("SELECT 1", fetch='one')
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "inference_engine": "ready" if inference_engine else "not_ready",
        "current_model": current_model.name if current_model else None
    }

@app.get("/platform/info")
async def get_platform_info():
    """获取平台信息"""
    platform = os.getenv('PLATFORM', auto_detect_platform())
    supported_platforms = InferenceFactory.get_supported_platforms()
    
    return {
        "current_platform": platform,
        "supported_platforms": supported_platforms,
        "inference_engine_status": "ready" if inference_engine else "not_ready",
        "model_loaded": current_model.name if current_model else None
    }

# ==================== 用户认证 ====================

@api_router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    user = user_repository.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 这里应该生成JWT token，简化版本直接返回用户信息
    return {"access_token": f"token_{user.id}", "token_type": "bearer", "user": user}

@api_router.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    """创建用户"""
    return user_repository.create_user(user)

@api_router.get("/users/me/", response_model=User)
async def read_users_me():
    """获取当前用户信息"""
    # 简化版本，实际应该从token中解析用户
    return {"id": 1, "username": "admin", "email": "admin@example.com"}

# ==================== 模型管理 ====================

@api_router.post("/models/", response_model=Model)
async def create_model(model: ModelCreate):
    """创建模型"""
    return model_repository.create_model(model)

@api_router.get("/models", response_model=PaginatedModelResponse)
async def get_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None
):
    """获取模型列表"""
    if not model_repository:
        raise HTTPException(status_code=503, detail="数据库服务不可用")
    
    result = model_repository.get_all_models(
        page=page, page_size=page_size, keyword=keyword, status=status, type=type
    )
    return PaginatedModelResponse(**result)

@api_router.get("/models/{model_id}", response_model=Model)
async def get_model(model_id: int):
    """获取单个模型"""
    model = model_repository.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model

@api_router.put("/models/{model_id}", response_model=Model)
async def update_model(model_id: int, model_update: ModelUpdate):
    """更新模型信息"""
    updated_model = model_repository.update_model(model_id, model_update)
    if not updated_model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return updated_model

@api_router.put("/models/{model_id}/status", response_model=Model)
async def update_model_status(model_id: int, status_data: dict):
    """更新模型状态（启用/禁用）"""
    status = status_data.get("status")
    if status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    model_repository.update_model_status(model_id, status)
    updated_model = model_repository.get_model_by_id(model_id)
    if not updated_model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return updated_model

@api_router.post("/models/upload", response_model=Model)
async def upload_model(
    name: str = Form(...),
    version: str = Form("1.0"),
    model_type: str = Form(..., alias="type"),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """上传模型文件"""
    import os
    import json
    
    # 创建模型目录
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    
    # 安全的文件名处理
    sanitized_filename = os.path.basename(file.filename)
    if not sanitized_filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
        
    file_location = os.path.join(models_dir, sanitized_filename)

    # 保存上传的文件
    try:
        with open(file_location, "wb+") as file_object:
            contents = await file.read()
            file_object.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    # 创建数据库记录
    model_data = ModelCreate(
        name=name,
        version=version,
        type=model_type,
        description=description,
        file_path=sanitized_filename
    )

    try:
        db_model = model_repository.create_model(model_data)
        return db_model
    except Exception as e:
        # 如果数据库操作失败，删除已上传的文件
        try:
            os.remove(file_location)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"模型创建失败: {e}")

@api_router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: int):
    """删除模型（只能删除禁用状态的模型）"""
    model = model_repository.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 检查模型状态，只有禁用状态的模型才能删除
    if model.status == 'active':
        raise HTTPException(status_code=400, detail="无法删除启用状态的模型，请先禁用模型")
    
    success = model_repository.delete_model_by_id(model_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除模型失败")
    
    return None  # 204状态码不需要返回内容，但需要显式返回

# 模型部署
@api_router.post("/models/{model_id}/deploy")
async def deploy_model(model_id: int):
    """部署模型"""
    model = model_repository.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 简化实现，更新状态为active
    updated_model = model_repository.update_model_status(model_id, "active")
    return {"message": "模型部署成功", "model": updated_model}

# 取消部署模型
@api_router.post("/models/{model_id}/undeploy")
async def undeploy_model(model_id: int):
    """取消部署模型"""
    model = model_repository.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 简化实现，更新状态为inactive
    updated_model = model_repository.update_model_status(model_id, "inactive")
    return {"message": "模型取消部署成功", "model": updated_model}

# 获取模型版本列表
@api_router.get("/models/{model_id}/versions")
async def get_model_versions(model_id: int):
    """获取模型版本列表"""
    model = model_repository.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 简化实现，返回当前版本
    versions = [{"version": model.version, "created_at": model.upload_time, "status": model.status}]
    return {"versions": versions}

# 获取模型性能指标
@api_router.get("/models/{model_id}/metrics")
async def get_model_metrics(model_id: int):
    """获取模型性能指标"""
    model = model_repository.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 简化实现，返回模拟指标
    metrics = {
        "accuracy": 0.95,
        "inference_time": 0.05,
        "memory_usage": 512,
        "throughput": 100
    }
    return {"metrics": metrics}

# 批量操作模型
class BatchModelUpdateRequest(BaseModel):
    ids: List[int]
    action: str  # activate, deactivate, delete
    
@api_router.put("/models/batch")
async def batch_update_models(update_request: BatchModelUpdateRequest):
    """批量操作模型"""
    for model_id in update_request.ids:
        if update_request.action == "activate":
            model_repository.update_model_status(model_id, "active")
        elif update_request.action == "deactivate":
            model_repository.update_model_status(model_id, "inactive")
        elif update_request.action == "delete":
            model_repository.delete_model(model_id)
    return {"message": f"批量操作完成: {update_request.action}"}

# 导出模型配置
@api_router.get("/models/{model_id}/export")
async def export_model(model_id: int):
    """导出模型配置"""
    model = model_repository.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 简化实现，返回模型配置
    config = {
        "name": model.name,
        "version": model.version,
        "type": model.type,
        "description": model.description
    }
    return {"config": config}

# 导入模型配置
@api_router.post("/models/import")
async def import_model(file: UploadFile = File(...)):
    """导入模型配置"""
    # 简化实现
    content = await file.read()
    return {"message": "模型配置导入成功", "imported_count": 0}

# ==================== 任务管理 ====================

@api_router.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate):
    """创建新任务"""
    return task_repository.create_task(task)

@api_router.get("/tasks", response_model=PaginatedTaskResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    model_id: Optional[int] = None,
    is_enabled: Optional[bool] = None
):
    """获取任务列表（支持筛选）"""
    return task_repository.get_all_tasks(
        page=page, page_size=page_size, keyword=keyword,
        status=status, model_id=model_id, is_enabled=is_enabled
    )

# 任务统计 - 放在{task_id}路由之前
@api_router.get("/tasks/stats")
async def get_task_stats():
    """获取任务统计信息"""
    counts = task_repository.get_task_counts_by_status()
    total = task_repository.get_total_count()
    return {
        "total": total,
        "counts_by_status": counts,
        "active_tasks": counts.get("running", 0) + counts.get("pending", 0)
    }

# 获取运行中的任务 - 放在{task_id}路由之前
@api_router.get("/tasks/running")
async def get_running_tasks():
    """获取运行中的任务"""
    running_tasks = task_repository.get_tasks_by_status("running")
    return {"tasks": running_tasks, "count": len(running_tasks)}

# 导出任务 - 放在{task_id}路由之前
@api_router.get("/tasks/export")
async def export_tasks():
    """导出任务数据"""
    tasks = task_repository.get_all_tasks()['items']
    return {"data": tasks, "total": len(tasks)}

# 导入任务 - 放在{task_id}路由之前
@api_router.post("/tasks/import")
async def import_tasks(file: UploadFile = File(...)):
    """导入任务数据"""
    # 简化实现
    content = await file.read()
    return {"message": "任务导入成功", "imported_count": 0}

# 获取视频帧用于ROI选择 - 放在{task_id}路由之前
class FrameRequest(BaseModel):
    source: str

@api_router.post("/tasks/frame")
async def get_task_frame(request: FrameRequest):
    """获取视频帧用于ROI选择"""
    import base64
    def read_frame_from_source(source, timeout=5):
        import cv2, time
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            cap.release()
            return None
        start_time = time.time()
        frame = None
        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if ret:
                break
            time.sleep(0.1)
        cap.release()
        return frame if ret else None
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        frame = await loop.run_in_executor(pool, read_frame_from_source, request.source, 5)
    if frame is None:
        raise HTTPException(status_code=404, detail="无法从视频源读取帧（超时）")
    is_success, buffer = cv2.imencode(".jpg", frame)
    if not is_success:
        raise HTTPException(status_code=500, detail="帧编码失败")
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return {"frame": "data:image/jpeg;base64," + jpg_as_text}

# 批量操作任务 - 放在{task_id}路由之前
class BatchTaskUpdateRequest(BaseModel):
    ids: List[int]
    action: str  # start, stop, delete
    
@api_router.put("/tasks/batch")
async def batch_update_tasks(update_request: BatchTaskUpdateRequest):
    """批量操作任务"""
    for task_id in update_request.ids:
        if update_request.action == "start":
            # 启动任务逻辑
            pass
        elif update_request.action == "stop":
            # 停止任务逻辑
            pass
        elif update_request.action == "delete":
            task_repository.delete_task(task_id)
    return {"message": f"批量操作完成: {update_request.action}"}

@api_router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """获取单个任务详情"""
    task = task_repository.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task: TaskCreate):
    """更新任务"""
    updated_task = task_repository.update_task(task_id, task)
    if not updated_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return updated_task

@api_router.post("/tasks/{task_id}/start", status_code=status.HTTP_204_NO_CONTENT)
async def start_task(task_id: int):
    """启动任务"""
    task = task_repository.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新数据库中的任务状态和启用状态
    task_repository.update_task_status_and_enabled_state(task_id, "running", True)
    
    # 调用任务调度器启动任务
    if task_scheduler:
        task_scheduler.start_task_manually(task_id)
    
    logger.info(f"任务 {task_id} 已启动")

@api_router.post("/tasks/{task_id}/stop", status_code=status.HTTP_204_NO_CONTENT)
async def stop_task(task_id: int):
    """停止任务"""
    task = task_repository.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新数据库中的任务状态和启用状态
    task_repository.update_task_status_and_enabled_state(task_id, "stopped", False)
    
    # 调用任务调度器停止任务
    if task_scheduler:
        task_scheduler.stop_task_manually(task_id)
    
    logger.info(f"任务 {task_id} 已停止")

@api_router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    """删除任务"""
    success = task_repository.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")

@api_router.get("/tasks/{task_id}/status")
async def get_task_runtime_status(task_id: int):
    """获取任务运行时状态"""
    task = task_repository.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查任务调度器中的状态
    runtime_status = "unknown"
    if task_scheduler:
        runtime_status = task_scheduler.get_task_status(task_id)
    
    return {
        "task_id": task_id,
        "database_status": task.status,
        "runtime_status": runtime_status,
        "is_enabled": task.is_enabled
    }

# 任务日志
@api_router.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: int, limit: int = Query(100, ge=1, le=1000)):
    """获取任务日志"""
    task = task_repository.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 简化实现，返回模拟日志
    logs = [
        {"timestamp": "2024-01-01T12:00:00Z", "level": "INFO", "message": f"Task {task_id} started"},
        {"timestamp": "2024-01-01T12:01:00Z", "level": "INFO", "message": f"Processing video stream for task {task_id}"},
    ]
    return {"logs": logs[:limit]}

# ==================== 告警管理 ====================

@api_router.get("/alerts", response_model=PaginatedAlertResponse)
async def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取告警列表"""
    return alert_repository.get_all_alerts(
        page=page, page_size=page_size, keyword=keyword, level=level,
        status=status, start_date=start_date, end_date=end_date
    )

# 告警统计 - 放在{alert_id}路由之前
@api_router.get("/alerts/stats")
async def get_alert_stats():
    """获取告警统计"""
    counts_by_status = alert_repository.get_alert_counts_by_status()
    counts_by_day = alert_repository.get_alert_counts_by_day(days=7)
    latest_alerts = alert_repository.get_latest_alerts(limit=5)
    
    return {
        "counts_by_status": counts_by_status,
        "counts_by_day": counts_by_day,
        "latest_alerts": latest_alerts
    }

# 告警趋势 - 放在{alert_id}路由之前
@api_router.get("/alerts/trends")
async def get_alert_trends():
    """获取告警趋势"""
    trends = alert_repository.get_alert_counts_by_day(days=30)
    return {"trends": trends}

# 导出告警 - 放在{alert_id}路由之前
@api_router.get("/alerts/export")
async def export_alerts():
    """导出告警数据"""
    # 简化实现，返回JSON格式
    alerts = alert_repository.get_all_alerts()['items']
    return {"data": alerts, "total": len(alerts)}

# 告警配置 - 放在{alert_id}路由之前
@api_router.get("/alerts/config")
async def get_alert_config():
    """获取告警配置"""
    return config_repository.get_config("alert_settings", {})

@api_router.put("/alerts/config")
async def update_alert_config(config: Dict[str, Any]):
    """更新告警配置"""
    config_repository.update_config("alert_settings", config)
    return {"message": "告警配置更新成功"}

# 批量操作告警 - 放在{alert_id}路由之前
class BatchAlertUpdateRequest(BaseModel):
    ids: List[int]
    status: str
    remark: Optional[str] = None

@api_router.put("/alerts/batch", status_code=status.HTTP_204_NO_CONTENT)
async def batch_update_alerts(update_request: BatchAlertUpdateRequest):
    """批量更新告警状态"""
    for alert_id in update_request.ids:
        alert_repository.update_alert_status(
            alert_id, update_request.status, update_request.remark
        )

@api_router.get("/alerts/{alert_id}")
async def get_alert(alert_id: int):
    """获取单个告警详情"""
    alert = alert_repository.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    return alert

@api_router.put("/alerts/{alert_id}", response_model=Alert)
async def update_alert(alert_id: int, data: dict = Body(...)):
    """
    更新单条告警（兼容前端）
    """
    alert = alert_repository.update_alert_status(
        alert_id, data.get("status"), data.get("remark")
    )
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    return alert

@api_router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(alert_id: int):
    """
    删除单条告警（兼容前端）
    """
    success = alert_repository.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="告警不存在")

# ==================== 推理接口 ====================

@api_router.post("/inference/detect")
async def detect_objects(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(0.5),
    nms_threshold: float = Form(0.4)
):
    """目标检测接口"""
    if not inference_engine:
        raise HTTPException(status_code=503, detail="推理引擎未就绪")
    
    try:
        # 读取图片
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="无效的图片文件")
        
        # 执行推理
        results = inference_engine.detect(
            image, 
            confidence_threshold=confidence_threshold,
            nms_threshold=nms_threshold
        )
        
        return {
            "status": "success",
            "results": results,
            "inference_time": inference_engine.get_performance_stats().get("last_inference_time", 0)
        }
        
    except Exception as e:
        logger.error(f"推理失败: {e}")
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")

# ==================== 系统配置 ====================

@api_router.get("/config")
async def get_system_config():
    """获取系统配置"""
    return config_repository.get_all_configs()

@api_router.put("/config")
async def update_system_config(configs: Dict[str, Any]):
    """更新系统配置"""
    config_repository.update_configs(configs)
    return {"message": "配置更新成功"}

# ==================== 系统统计 ====================

@api_router.get("/system/stats")
async def get_system_stats():
    """获取系统统计信息 - 已修复版本"""
    # 获取任务统计
    task_counts = task_repository.get_task_counts_by_status()
    total_tasks = task_repository.get_total_count()
    
    # 获取模型统计
    model_total = model_repository.get_total_count()
    active_models = len(model_repository.get_all_models(status='active')['items'])
    
    # 获取告警统计
    alert_counts = alert_repository.get_alert_counts_by_status()
    recent_alerts = len(alert_repository.get_latest_alerts(limit=10))
    
    # 扁平结构（向后兼容）
    stats = {
        "total_tasks": total_tasks,
        "pending": task_counts.get("pending", 0),
        "running": task_counts.get("running", 0),
        "completed": task_counts.get("completed", 0),
        "failed": task_counts.get("failed", 0),
        "total_models": model_total,
        "active_models": active_models,
        "total_alerts": recent_alerts,
        "unresolved_alerts": alert_counts.get("unresolved", 0),
        "resolved_alerts": alert_counts.get("resolved", 0),
        "models": {
            "total": model_total,
            "active": active_models
        },
        "tasks": {
            "total": total_tasks,
            "counts_by_status": task_counts
        },
        "alerts": {
            "counts_by_status": alert_counts,
            "recent": recent_alerts
        },
        
        # 前端Dashboard期望的嵌套结构
        "summary": {
            "total_tasks": total_tasks,
            "running_tasks": task_counts.get("running", 0),
            "total_models": model_total,
            "pending_alerts": alert_counts.get("unresolved", 0)
        },
        "alerts_by_status": {
            "pending": alert_counts.get("unresolved", 0),
            "processing": alert_counts.get("processing", 0),
            "resolved": alert_counts.get("resolved", 0)
        },
        "alerts_past_week": [],  # 暂时为空，可以后续实现
        "latest_alerts": []  # 暂时为空，可以后续实现
    }
    
    if inference_engine:
        stats["inference"] = inference_engine.get_performance_stats()
    
    # 强制添加测试字段
    stats["test_summary"] = {
        "total_tasks": total_tasks,
        "running_tasks": task_counts.get("running", 0),
        "total_models": model_total,
        "pending_alerts": alert_counts.get("unresolved", 0)
    }
    
    return stats

@api_router.get("/system/configs")
async def get_system_configs():
    """获取系统配置 (兼容性端点)"""
    return config_repository.get_all_configs()

@api_router.put("/system/configs")
async def update_system_configs(configs: Dict[str, Any]):
    """更新系统配置 (兼容性端点)"""
    config_repository.update_configs(configs)
    return {"message": "System configurations updated successfully."}

# ==================== 视频流支持 ====================

async def generate_mjpeg_stream(video_source_url: str):
    """
    Generates an MJPEG stream from a video source.
    """
    import cv2
    import concurrent.futures
    import asyncio
    cap = None
    loop = asyncio.get_event_loop()
    try:
        logger.info(f"Opening MJPEG stream for: {video_source_url}")
        source_to_open = int(video_source_url) if video_source_url.isdigit() else video_source_url
        cap = cv2.VideoCapture(source_to_open)
        if not cap.isOpened():
            logger.error(f"Cannot open video source: {video_source_url}")
            return
        def read_frame():
            ret, frame = cap.read()
            return ret, frame
        with concurrent.futures.ThreadPoolExecutor() as pool:
            while True:
                ret, frame = await loop.run_in_executor(pool, read_frame)
                if not ret:
                    logger.warning(f"Lost connection to video stream: {video_source_url}. Stopping stream.")
                    break
                _, buffer = cv2.imencode('.jpg', frame)
                frame_data = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
    except Exception as e:
        logger.error(f"An unexpected error occurred in MJPEG stream for {video_source_url}: {e}")
    finally:
        if cap:
            cap.release()
        logger.info(f"Client disconnected from stream: {video_source_url}. Closing resources.")

@api_router.get("/tasks/{task_id}/stream")
async def mjpeg_video_stream(task_id: int):
    """MJPEG视频流端点"""
    task = task_repository.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not task.video_sources:
        raise HTTPException(status_code=404, detail="任务没有视频源")

    # For simplicity, we stream the first video source of the task
    first_source = task.video_sources[0]
    if isinstance(first_source, dict):
        video_source_url = first_source.get('url', first_source.get('source', ''))
    elif isinstance(first_source, str):
        video_source_url = first_source
    else:
        video_source_url = ''
    if not video_source_url:
        raise HTTPException(status_code=400, detail="无效的视频源格式")
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        generate_mjpeg_stream(video_source_url),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

# ==================== WebSocket支持 ====================

@app.websocket("/ws/tasks/{task_id}/stream")
async def websocket_task_stream(websocket: WebSocket, task_id: int):
    """任务实时流WebSocket"""
    await websocket.accept()
    try:
        while True:
            # 这里应该实现实时视频流处理
            # 简化版本只发送心跳
            await websocket.send_json({"type": "heartbeat", "task_id": task_id})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: task_id={task_id}")

# 注册API路由
app.include_router(api_router)

# ==================== 启动配置 ====================

def parse_args():
    parser = argparse.ArgumentParser(description="AI Edge统一API服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式热重载")
    return parser.parse_args()

def main():
    args = parse_args()
    
    logger.info(f"启动AI Edge API服务 - {args.host}:{args.port}")
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
