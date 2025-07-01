from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List, Any, Dict, Union
from datetime import datetime, time, timedelta
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

class ModelInfo(BaseModel):
    name: str = "N/A"
    version: str = "N/A"

    class Config:
        from_attributes = True

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
    is_enabled: bool = True
    schedule_type: str = 'continuous'
    schedule_days: List[str] = []
    start_time: str = '00:00:00'
    end_time: str = '23:59:59'
    confidence_threshold: float = 0.8
    alert_debounce_interval: int = 60
    inference_interval: float = 1.0
    alert_message: str = "在任务'{task_name}'中，于{time}检测到{class_name}，置信度为{confidence:.2f}%。"

    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def format_time(cls, value: Any) -> str:
        """Ensure time values are strings in HH:MM:SS format."""
        if isinstance(value, time):
            return value.strftime('%H:%M:%S')
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        
        # 处理字符串格式的时间
        if isinstance(value, str):
            # 移除时区信息和毫秒
            time_str = value.strip()
            
            # 移除时区标识符（Z, +XX:XX, -XX:XX等）
            if 'Z' in time_str:
                time_str = time_str.split('Z')[0]
            elif '+' in time_str:
                time_str = time_str.split('+')[0]
            elif time_str.count('-') > 2:  # 避免影响日期中的-
                parts = time_str.split('-')
                if len(parts) > 3:  # 说明有时区信息
                    time_str = '-'.join(parts[:-1])
            
            # 移除毫秒部分
            if '.' in time_str:
                time_str = time_str.split('.')[0]
            
            # 验证和格式化时间
            try:
                # 尝试解析时间
                from datetime import datetime
                if 'T' in time_str:
                    # ISO格式：2023-01-01T16:00:00
                    dt = datetime.fromisoformat(time_str)
                    return dt.strftime('%H:%M:%S')
                else:
                    # 只有时间部分：16:00:00
                    time_parts = time_str.split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(time_parts[2]) if len(time_parts) > 2 else 0
                        
                        # 验证时间范围
                        if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                            return f"{hour:02d}:{minute:02d}:{second:02d}"
            except (ValueError, IndexError):
                pass
            
            # 如果解析失败，返回默认时间
            return '00:00:00'
        
        return str(value)

    @field_validator('video_sources', 'schedule_days', mode='before')
    @classmethod
    def parse_json(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    status: Optional[str] = None
    create_time: datetime
    update_time: datetime
    model: Optional[ModelInfo] = None

    class Config:
        from_attributes = True

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

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int

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
    task_id: Optional[int] = None
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

class TaskPaginatedResponse(PaginatedResponse):
    items: List[Task] 