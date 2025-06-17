import mysql.connector.locales.eng.client_error
import os
import sys
import traceback
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, File, UploadFile, Form, WebSocket, WebSocketDisconnect, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Any, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import cv2
import asyncio
import numpy as np
import base64
from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
import json
import logging
import time
import multiprocessing
import threading
from collections import deque
import weakref
from multiprocessing import Process, Queue
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import uuid

# Add project root to Python path first
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Define absolute path for alert images
ALERT_IMAGE_DIR = os.path.join(project_root, "alert_images")
os.makedirs(ALERT_IMAGE_DIR, exist_ok=True)
TEMP_FRAME_DIR = os.path.join(project_root, "uploads", "temp_frames")
os.makedirs(TEMP_FRAME_DIR, exist_ok=True)

# Now, import project-specific modules
from database.models import (
    User, UserCreate, Model, ModelCreate, ModelUpdate, InferenceRecord, 
    InferenceRecordCreate, Task, TaskCreate, PaginatedModelResponse, PaginatedTaskResponse,
    ModelStatusUpdate, ScheduleType, PaginatedAlertResponse, Alert, AlertStatus, AlertCreate
)
from database.repositories import UserRepository, ModelRepository, InferenceRepository, TaskRepository, AlertRepository
from api.models.factory import ModelFactory

load_dotenv()

app = FastAPI(title="AI Edge API")
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

# IPC Queue for detection results from background processes
detection_queue = Queue()

# Global dictionary to hold running background processes
background_task_processes = {}

# Manager for broadcasting detection results via WebSocket
class DetectionStreamManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, task_id: int, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)

    def disconnect(self, task_id: int, websocket: WebSocket):
        if task_id in self.active_connections:
            self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def broadcast(self, task_id: int, data: Dict):
        if task_id in self.active_connections:
            # Use a copy of the list to avoid issues if a client disconnects during broadcast
            for connection in self.active_connections[task_id][:]:
                try:
                    await connection.send_json(data)
                except (WebSocketDisconnect, ConnectionResetError):
                    self.disconnect(task_id, connection)

detection_manager = DetectionStreamManager()

# Mount static files directory for alert images
app.mount("/alert_images", StaticFiles(directory="alert_images"), name="alert_images")

# Add a middleware to log incoming request headers
@app.middleware("http")
async def log_request_headers(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url.path}")
    print(f"Headers: {request.headers}")
    response = await call_next(request)
    return response

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# 依赖注入
def get_user_repository():
    return UserRepository()

def get_model_repository():
    return ModelRepository()

def get_task_repository():
    return TaskRepository()

def get_inference_repository():
    return InferenceRepository()

def get_alert_repository():
    return AlertRepository()

# 工具函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, user_repo: UserRepository = Depends(get_user_repository)):
    print("--- Backend Auth ---")
    print("Request path:", request.url.path)
    print("Received headers:", dict(request.headers))
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise credentials_exception
        
    try:
        parts = auth_header.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            raise credentials_exception
        token = parts[1]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (JWTError, IndexError):
        raise credentials_exception
    
    user = user_repo.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    print("User authenticated successfully:", user.username)
    print("--------------------")
    return user

async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    if token is None:
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")

    credentials_exception = WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication credentials")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = user_repo.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# 认证路由
@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), user_repo: UserRepository = Depends(get_user_repository)):
    user = user_repo.authenticate_user(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 用户路由
@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, user_repo: UserRepository = Depends(get_user_repository)):
    db_user = user_repo.get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return user_repo.create_user(user)

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# 模型路由
@app.post("/models/", response_model=Model)
async def create_model(
    model: ModelCreate,
    current_user: User = Depends(get_current_user),
    model_repo: ModelRepository = Depends(get_model_repository)
):
    return model_repo.create_model(model)

@app.get("/models", response_model=PaginatedModelResponse)
async def read_models(
    current_user: User = Depends(get_current_user),
    model_repo: ModelRepository = Depends(get_model_repository),
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    status: Optional[str] = 'active',
    type: Optional[str] = None
):
    return model_repo.get_all_models(
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        type=type
    )

@app.get("/models/{model_id}", response_model=Model)
async def read_model_by_id(
    model_id: int,
    current_user: User = Depends(get_current_user),
    model_repo: ModelRepository = Depends(get_model_repository)
):
    model = model_repo.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@app.put("/models/{model_id}", response_model=Model)
async def update_model_details(
    model_id: int,
    model_update: ModelUpdate,
    current_user: User = Depends(get_current_user),
    model_repo: ModelRepository = Depends(get_model_repository)
):
    """Updates a model's editable details."""
    updated_model = model_repo.update_model(model_id, model_update)
    if not updated_model:
        raise HTTPException(status_code=404, detail="Model not found")
    return updated_model

@app.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_by_id(
    model_id: int,
    current_user: User = Depends(get_current_user),
    model_repo: ModelRepository = Depends(get_model_repository)
):
    success = model_repo.delete_model_by_id(model_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete model")
    return None

@app.put("/models/{model_id}/status", response_model=Model)
async def update_model_status_endpoint(
    model_id: int,
    status_update: ModelStatusUpdate,
    current_user: User = Depends(get_current_user),
    model_repo: ModelRepository = Depends(get_model_repository)
):
    """启用或禁用模型"""
    model_repo.update_model_status(model_id, status_update.status.value)
    updated_model = model_repo.get_model_by_id(model_id)
    if not updated_model:
        raise HTTPException(status_code=404, detail="Model not found after update")
    return updated_model

@app.post("/models/upload", response_model=Model)
async def upload_model_file(
    name: str = Form(...),
    version: str = Form("1.0"),
    model_type: str = Form(..., alias="type"),
    description: Optional[str] = Form(None),
    labels: Optional[str] = Form("[]"), # Expect a JSON string for labels
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    model_repo: ModelRepository = Depends(get_model_repository)
):
    upload_dir = "uploads/models"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{name}_{version}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        parsed_labels = json.loads(labels)
        if not isinstance(parsed_labels, list):
            raise ValueError("Labels must be a list.")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid format for labels: {e}")

    model_create = ModelCreate(
        name=name,
        version=version,
        description=description,
        type=model_type,
        file_path=file_path,
        labels=parsed_labels,
    )
    
    created_model = model_repo.create_model(model_create)
    return created_model

# Global reference to the scheduler jobs
task_jobs = {}

# --- Thread-safe, non-blocking frame grabber ---
class VideoCapture:
    def __init__(self, src=0):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.q = deque(maxlen=1)  # Buffer of size 1
        self.running = True
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                # Attempt to reconnect if the stream is lost
                self.cap.release()
                time.sleep(1)
                self.cap = cv2.VideoCapture(self.src)
                continue
            if not self.q: # if queue is empty
                self.q.append(frame)
            else: # if queue is full
                self.q.popleft()
                self.q.append(frame)
            time.sleep(0.01) # Small sleep to prevent high CPU usage

    def read(self):
        try:
            return True, self.q.get_nowait()
        except asyncio.QueueEmpty: # Using asyncio exception type for deque under this name
             return False, None
        except Exception:
             return False, None

    def isOpened(self):
        return self.cap.isOpened()

    def release(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        if self.cap.isOpened():
            self.cap.release()


# --- Background Task Processing ---
async def listen_for_detections():
    """
    Listens for detection results from the queue and broadcasts them.
    This function should run in the main FastAPI process.
    """
    loop = asyncio.get_event_loop()
    while True:
        try:
            # Use run_in_executor for the blocking get() call
            detection_data = await loop.run_in_executor(None, detection_queue.get)
            if detection_data and 'task_id' in detection_data:
                await detection_manager.broadcast(detection_data['task_id'], detection_data)
        except Exception as e:
            print(f"Error in detection listener: {e}")
        await asyncio.sleep(0.1)


def run_task_in_background(task_id: int, q: Queue):
    """
    The actual function that runs in a separate process for a given task.
    Initializes model and video capture, then enters a continuous loop
    to process frames and run inference.
    """
    print(f"[{datetime.now()}] Starting background process for task {task_id}")
    
    # Each process needs its own repository instances
    task_repo = TaskRepository()
    model_repo = ModelRepository()
    alert_repo = AlertRepository()

    try:
        task = task_repo.get_task_by_id(task_id)
        if not task:
            print(f"ERROR: Task {task_id} not found when starting background process.")
            return

        model_details = model_repo.get_model_by_id(task.model_id)
        if not model_details or not model_details.status == 'active':
            print(f"ERROR: Model {task.model_id} for task {task_id} not found or is not active.")
            return
        
        try:
            print(f"Task {task_id}: Loading model {model_details.name} from {model_details.file_path}")
            model = ModelFactory.create_model(
                model_type=model_details.type,
                model_path=model_details.file_path,
                labels=model_details.labels
            )
            print(f"Task {task_id}: Model loaded successfully.")
        except Exception as e:
            print(f"FATAL: Failed to load model for task {task_id}. Error: {e}")
            traceback.print_exc()
            return

        if not task.video_sources:
            print(f"ERROR: Task {task_id} has no video sources configured.")
            return

        # Main loop to process video sources
        while True:
            # Re-fetch task to check status. In a real scenario, a better IPC mechanism would be used.
            current_task_state = task_repo.get_task_by_id(task_id)
            if not current_task_state or not current_task_state.is_enabled or current_task_state.status != 'running':
                print(f"Task {task_id} is disabled or stopped. Exiting process.")
                break

            for source in current_task_state.video_sources:
                source_url = source.get("url")
                if not source_url:
                    continue
                
                cap = None
                try:
                    print(f"Task {task_id}: Opening video source: {source_url}")
                    cap = cv2.VideoCapture(source_url)
                    if not cap.isOpened():
                        print(f"ERROR: Task {task_id} could not open video source: {source_url}. Retrying in 5s.")
                        time.sleep(5)
                        continue

                    ret, frame = cap.read()
                    if not ret:
                        print(f"ERROR: Task {task_id} could not read frame from {source_url}.")
                        time.sleep(current_task_state.inference_interval)
                        continue
                except Exception as e:
                    print(f"ERROR: Failed to read from video source {source_url} for task {task_id}. Error: {e}")
                    time.sleep(5) # Wait before retrying
                    continue
                finally:
                    if cap:
                        cap.release() # Release immediately after one frame

                
                print(f"Task {task_id}: Frame captured from {source_url}. Running inference.")
                try:
                    # The model's `inference` method is expected to be in `api/models/detection.py`
                    detections = model.inference(frame)
                    print(f"Task {task_id}: Inference complete. Found {len(detections)} potential objects.")
                except Exception as e:
                    print(f"ERROR: Inference failed for task {task_id}. Error: {e}")
                    traceback.print_exc()
                    time.sleep(current_task_state.inference_interval)
                    continue

                if detections:
                    # Send raw detections to websocket subscribers
                    q.put({"task_id": task_id, "detections": detections})
                
                    # Process for alerts
                    for detection in detections:
                        confidence = detection.get('score', 0)
                        class_name = detection.get('label', 'unknown')

                        if confidence >= current_task_state.confidence_threshold:
                            can_create_alert = True
                            latest_alert = alert_repo.get_latest_alert_for_task(task.id, class_name)
                            if latest_alert:
                                time_since_last = datetime.now() - latest_alert.created_at
                                if time_since_last < timedelta(seconds=current_task_state.alert_debounce_interval):
                                    can_create_alert = False
                            
                            if can_create_alert:
                                print(f"Task {task_id}: High confidence detection '{class_name}' ({confidence:.2f}). Creating alert.")
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                image_filename = f"alert_{task_id}_{class_name}_{timestamp}.jpg"
                                image_path = os.path.join(ALERT_IMAGE_DIR, image_filename)
                                
                                # Draw result on the frame for the alert image
                                frame_with_dets = model.draw_result(frame.copy(), detections)
                                cv2.imwrite(image_path, frame_with_dets)
                                
                                alert_create = AlertCreate(
                                    task_id=task.id,
                                    task_name=task.name,
                                    model_name=model_details.name,
                                    alert_image=image_path, # Use the absolute path for the alert
                                    confidence=confidence,
                                    detection_class=class_name,
                                    title=f"Detection of {class_name}",
                                    description=task.alert_message.format(task_name=task.name, time=datetime.now().strftime('%H:%M:%S'), class_name=class_name, confidence=confidence*100)
                                )
                                alert_repo.create_alert(alert_create)

                # Wait for the specified interval before processing the next frame
                time.sleep(current_task_state.inference_interval)

    except Exception as e:
        print(f"FATAL ERROR in background process for task {task_id}: {e}")
        traceback.print_exc()
    finally:
        print(f"[{datetime.now()}] Background process for task {task_id} is shutting down.")


def stop_background_task(task_id: int):
    """Stops the background process for a given task."""
    process = background_task_processes.get(task_id)
    if process and process.is_alive():
        print(f"Terminating background process for task {task_id}.")
        process.terminate()
        process.join()
    if task_id in background_task_processes:
        del background_task_processes[task_id]


def start_background_task(task_id: int):
    """Starts a new background process for a given task if not already running."""
    if task_id in background_task_processes and background_task_processes[task_id].is_alive():
        print(f"Task {task_id} is already running.")
        return

    process = Process(target=run_task_in_background, args=(task_id, detection_queue), daemon=True)
    background_task_processes[task_id] = process
    process.start()
    print(f"Started background process for task {task_id} with PID {process.pid}.")


def schedule_task(task: Task, task_repo: TaskRepository):
    """Schedules a task based on its cron settings."""
    job_id_start = f"task_{task.id}_start"
    job_id_stop = f"task_{task.id}_stop"
    
    # Remove existing jobs to prevent duplicates
    if scheduler.get_job(job_id_start):
        scheduler.remove_job(job_id_start)
    if scheduler.get_job(job_id_stop):
        scheduler.remove_job(job_id_stop)

    if not task.is_enabled:
        print(f"Task {task.id} is disabled, not scheduling.")
        return

    def start_job():
        print(f"Scheduler starting task {task.id}...")
        task_repo.update_task_status(task.id, 'running')
        start_background_task(task.id)

    def stop_job():
        print(f"Scheduler stopping task {task.id}...")
        stop_background_task(task.id)
        task_repo.update_task_status(task.id, 'stopped')

    # Add jobs to start and stop the task
    if task.schedule_type == ScheduleType.CONTINUOUS:
        # For continuous tasks, we assume they should be started if enabled.
        # The actual start/stop is handled via API calls, not cron.
        # However, if we want them to start on app startup, we can do this:
        if task.status == 'running':
             print(f"Restarting continuous task {task.id} on scheduler sync.")
             start_background_task(task.id)
        return

    # Logic for scheduled tasks (daily, weekly, monthly)
    start_time_parts = [int(p) for p in task.start_time.split(':')]
    end_time_parts = [int(p) for p in task.end_time.split(':')]
    
    cron_args = {
        'hour': start_time_parts[0],
        'minute': start_time_parts[1],
    }
    
    if task.schedule_type == ScheduleType.WEEKLY:
        cron_args['day_of_week'] = ",".join(task.schedule_days) if task.schedule_days else "0-6"
    elif task.schedule_type == ScheduleType.MONTHLY:
        cron_args['day'] = ",".join(task.schedule_days) if task.schedule_days else "*"
        
    scheduler.add_job(start_job, CronTrigger(**cron_args, timezone='Asia/Shanghai'), id=f"{job_id_start}")
    
    # Schedule stop job
    cron_args['hour'] = end_time_parts[0]
    cron_args['minute'] = end_time_parts[1]
    scheduler.add_job(stop_job, CronTrigger(**cron_args, timezone='Asia/Shanghai'), id=f"{job_id_stop}")

    print(f"Scheduled task {task.id} ({task.schedule_type}) to start at {task.start_time} and stop at {task.end_time}.")


def sync_and_schedule_all_tasks():
    """Fetches all tasks from DB and syncs their schedule and running state."""
    print("--- Syncing and scheduling all tasks from database ---")
    task_repo = TaskRepository()
    all_tasks = task_repo.get_all_tasks_for_scheduling()
    for task in all_tasks:
        # Schedule the task based on its settings
        schedule_task(task, task_repo)
        
        # For tasks that should be running but aren't (e.g., after a server restart)
        # We only handle CONTINUOUS tasks here. Scheduled tasks are handled by the scheduler.
        if task.schedule_type == ScheduleType.CONTINUOUS and task.is_enabled and task.status == 'running':
            print(f"Continuous task {task.id} was running. Restarting background process.")
            start_background_task(task.id)
        elif task.status == 'running': # If a scheduled task was running, stop it. Let the scheduler restart it.
                print(f"Stopping previously running scheduled task {task.id}. Scheduler will handle restart.")
                task_repo.update_task_status(task.id, 'stopped')


@app.on_event("startup")
def start_scheduler():
    """Start the scheduler and the detection listener on app startup."""
    print("--- FastAPI App Startup ---")
    # Start the detection listener in the background
    asyncio.create_task(listen_for_detections())
    
    # Start the APScheduler
    scheduler.start()
    
    # Sync tasks from DB
    sync_and_schedule_all_tasks()
    print("--- Scheduler and services are running ---")

# 任务路由
@app.post("/tasks", response_model=Task)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    created_task = task_repo.create_task(task)
    # Schedule the newly created task
    schedule_task(created_task, task_repo)
    return created_task

@app.get("/tasks", response_model=PaginatedTaskResponse)
async def read_tasks(
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(get_task_repository),
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None
):
    return task_repo.get_all_tasks(page=page, page_size=page_size, keyword=keyword)

@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    task = task_repo.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    task_update: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    updated_task = task_repo.update_task(task_id, task_update)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Reschedule the task with updated settings
    schedule_task(updated_task, task_repo)
    return updated_task

@app.post("/tasks/{task_id}/start", status_code=status.HTTP_204_NO_CONTENT)
async def start_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    # Enable the task and set its status to running
    task_repo.update_task_status_and_enabled_state(task_id, "running", True)
    
    # Reload the task and re-evaluate its schedule
    task = task_repo.get_task_by_id(task_id)
    if task:
        schedule_task(task, task_repo)
    else:
        # This case is unlikely if the task exists, but good practice
        raise HTTPException(status_code=404, detail="Task not found after attempting to start")
        
    return None

@app.post("/tasks/{task_id}/stop", status_code=status.HTTP_204_NO_CONTENT)
async def stop_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    # Disable the task and set its status to stopped
    task_repo.update_task_status_and_enabled_state(task_id, "stopped", False)
    
    # Reload the task and re-evaluate its schedule (which will stop it)
    task = task_repo.get_task_by_id(task_id)
    if task:
        schedule_task(task, task_repo)
    else:
        # This case is unlikely if the task exists, but good practice
        stop_background_task(task_id) # Ensure process is stopped anyway
        
    return None

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    # Stop any running process before deleting
    stop_background_task(task_id)
    success = task_repo.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

async def generate_mjpeg_stream(source: str):
    """生成MJPEG视频流"""
    while True:
        cap = None
        try:
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                error_msg = "Could not open video source."
                # 创建一个包含错误消息的图像
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, error_msg, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                await asyncio.sleep(5) # 等待5秒后重试
                continue

            while True:
                ret, frame = cap.read()
                if not ret:
                    # 如果读取失败，跳出内层循环以尝试重新打开视频源
                    break
                
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                await asyncio.sleep(1/30) # 控制帧率

        except Exception as e:
            logging.error(f"Error in MJPEG stream for {source}: {e}")
            # 创建一个包含错误消息的图像
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f"Error: {e}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            await asyncio.sleep(5) # 发生异常后，等待5秒再重试
        finally:
            if cap:
                cap.release()


@app.get("/tasks/{task_id}/stream")
async def mjpeg_video_stream(
    task_id: int,
    task_repo: TaskRepository = Depends(get_task_repository),
    # Note: No user dependency here to allow direct access from <img> src
    # In a real-world scenario, you'd use a signed URL or token in query param
):
    task = task_repo.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.video_sources:
        raise HTTPException(status_code=404, detail="Task has no video sources")

    # For simplicity, we stream the first video source of the task
    video_source_url = task.video_sources[0]['url']
    
    return StreamingResponse(
        generate_mjpeg_stream(video_source_url),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

class FrameRequest(BaseModel):
    source: str

@app.post("/tasks/frame")
async def get_task_frame(request: FrameRequest, current_user: User = Depends(get_current_user)):
    """
    Retrieves a single frame from a given video source URL.
    Used for ROI selection in the frontend.
    """
    cap = None
    source = request.source
    try:
        source_to_open = int(source) if source.isdigit() else source
        cap = cv2.VideoCapture(source_to_open)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Cannot open video source")
        
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=404, detail="Could not read frame from video source")
            
        # Encode frame to JPEG
        is_success, buffer = cv2.imencode(".jpg", frame)
        if not is_success:
            raise HTTPException(status_code=500, detail="Failed to encode frame")

        # Encode the buffer to base64
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        return JSONResponse(content={"frame": "data:image/jpeg;base64," + jpg_as_text})

    except Exception as e:
        print(f"Error getting frame from source {source}: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    finally:
        if cap:
            cap.release()

# WebSocket 视频流路由
@app.websocket("/ws/tasks/{task_id}/stream")
async def websocket_stream(
    websocket: WebSocket,
    task_id: int,
    token: str = Query(...)
    # No repository dependencies here, as they are not thread-safe and will be created in the process.
):
    # Note: Authentication is simplified here. In a real app, you'd validate the token.
    # For instance, by calling a utility function that decodes the token.
    # We will just accept the connection for now.
    await detection_manager.connect(task_id, websocket)
    try:
        while True:
            # Keep the connection alive, but we don't need to process incoming messages.
            # The manager will push data out.
            await websocket.receive_text()
    except WebSocketDisconnect:
        logging.info(f"Client disconnected from task {task_id} stream.")
    finally:
        detection_manager.disconnect(task_id, websocket)

# 推理路由
@app.post("/inference/", response_model=InferenceRecord)
async def create_inference_record(
    record: InferenceRecordCreate,
    current_user: User = Depends(get_current_user),
    inference_repo: InferenceRepository = Depends(get_inference_repository)
):
    return inference_repo.create_record(record)

@app.get("/inference/", response_model=list[InferenceRecord])
async def read_inference_records(
    current_user: User = Depends(get_current_user),
    inference_repo: InferenceRepository = Depends(get_inference_repository)
):
    return inference_repo.get_user_records(current_user.id)

# Alert Routes
class AlertStatusUpdate(BaseModel):
    status: AlertStatus
    remark: Optional[str] = None

class BatchAlertUpdateRequest(BaseModel):
    ids: List[int]
    status: AlertStatus
    remark: Optional[str] = None

@app.get("/alerts", response_model=PaginatedAlertResponse)
async def read_alerts(
    current_user: User = Depends(get_current_user),
    alert_repo: AlertRepository = Depends(get_alert_repository),
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    return alert_repo.get_all_alerts(
        page=page, page_size=page_size, keyword=keyword, level=level,
        status=status, start_date=start_date, end_date=end_date
    )

@app.get("/alerts/{alert_id}", response_model=Alert)
async def read_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    alert_repo: AlertRepository = Depends(get_alert_repository)
):
    alert = alert_repo.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@app.put("/alerts/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: int,
    alert_update: AlertStatusUpdate,
    current_user: User = Depends(get_current_user),
    alert_repo: AlertRepository = Depends(get_alert_repository)
):
    updated_alert = alert_repo.update_alert_status(
        alert_id, alert_update.status.value, alert_update.remark
    )
    if not updated_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return updated_alert

@app.put("/alerts/batch", status_code=status.HTTP_204_NO_CONTENT)
async def batch_update_alerts(
    update_request: BatchAlertUpdateRequest,
    current_user: User = Depends(get_current_user),
    alert_repo: AlertRepository = Depends(get_alert_repository)
):
    for alert_id in update_request.ids:
        alert_repo.update_alert_status(
            alert_id, update_request.status.value, update_request.remark
        )
    return None

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001) 