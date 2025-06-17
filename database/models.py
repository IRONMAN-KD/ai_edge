from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
import json

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModelBase(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    file_path: str
    type: str
    labels: Optional[List[str]] = None

class ModelCreate(ModelBase):
    file_path: str

class ModelUpdate(ModelBase):
    file_path: Optional[str] = None

class Model(ModelBase):
    id: int
    status: str
    upload_time: datetime
    update_time: datetime
    file_path: str

    class Config:
        from_attributes = True

from enum import Enum
class ModelStatus(str, Enum):
    active = "active"
    inactive = "inactive"

class ModelStatusUpdate(BaseModel):
    status: ModelStatus

class InferenceRecordBase(BaseModel):
    model_id: int
    user_id: int
    input_path: str
    output_path: str
    inference_time: Optional[float] = None
    status: str

class InferenceRecordCreate(InferenceRecordBase):
    pass

class InferenceRecord(InferenceRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ScheduleType(str, Enum):
    CONTINUOUS = "continuous" # 持续运行
    DAILY = "daily"           # 每天
    WEEKLY = "weekly"         # 每周
    MONTHLY = "monthly"       # 每月

class DayOfWeek(str, Enum):
    MONDAY = "1"
    TUESDAY = "2"
    WEDNESDAY = "3"
    THURSDAY = "4"
    FRIDAY = "5"
    SATURDAY = "6"
    SUNDAY = "7"

class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_id: int
    video_sources: List[Dict[str, Any]]
    status: Optional[str] = 'stopped'
    # Scheduling fields
    is_enabled: Optional[bool] = True
    schedule_type: Optional[ScheduleType] = ScheduleType.CONTINUOUS
    schedule_days: Optional[List[str]] = None
    start_time: Optional[str] = "00:00:00"
    end_time: Optional[str] = "23:59:59"
    # Alerting fields
    confidence_threshold: Optional[float] = 0.8
    alert_debounce_interval: Optional[int] = 60 # seconds
    alert_message: Optional[str] = "在任务'{task_name}'中，于{time}检测到{class_name}，置信度为{confidence:.2f}%。"
    # Execution control
    inference_interval: Optional[float] = 1.0 # seconds between inferences

    @field_validator('video_sources')
    @classmethod
    def validate_video_sources(cls, v):
        if not isinstance(v, list):
            raise TypeError('video_sources must be a list')
        for item in v:
            if not isinstance(item, dict) or 'url' not in item:
                raise ValueError('Each item in video_sources must be a dict with a "url" key')
        return v

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    video_sources: List[Dict[str, Any]]
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    model_name: Optional[str] = None

    @field_validator('video_sources', mode='before')
    @classmethod
    def parse_video_sources(cls, v: Any) -> List[Dict[str, Any]]:
        if v is None:
            return []
        
        loaded = None
        if isinstance(v, str):
            try:
                loaded = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                # Case 1: Plain string URL (very old format)
                return [{'url': v, 'roi': None}]
        elif isinstance(v, list):
            loaded = v
        else:
            return []

        if isinstance(loaded, list):
            migrated_list = []
            for item in loaded:
                if isinstance(item, str):
                    # Case 2: Item is a string URL (from JSON array of strings)
                    migrated_list.append({'url': item, 'roi': None})
                elif isinstance(item, dict) and 'url' in item:
                    # Case 3: Item is already in the new dict format
                    migrated_list.append(item)
            return migrated_list
            
        return []

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    total: int
    items: List

class PaginatedModelResponse(PaginatedResponse):
    items: List[Model]

class PaginatedTaskResponse(PaginatedResponse):
    items: List[Task]

# ----------------- Alert Models -----------------

class AlertLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AlertStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"

class AlertBase(BaseModel):
    title: str
    description: Optional[str] = None
    level: AlertLevel = AlertLevel.MEDIUM
    status: AlertStatus = AlertStatus.PENDING
    confidence: float
    task_id: int
    task_name: Optional[str] = None
    model_name: Optional[str] = None
    alert_image: Optional[str] = None
    # For debouncing purposes
    detection_class: Optional[str] = None

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedAlertResponse(PaginatedResponse):
    items: List[Alert] 