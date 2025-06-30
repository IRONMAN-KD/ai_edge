from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Time
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Model(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    labels = Column(JSON)
    status = Column(String(20), default='active')
    upload_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = Column(Text)
    
    tasks = relationship("Task", back_populates="model")


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    
    model_id = Column(Integer, ForeignKey('models.id'), nullable=False)
    model = relationship("Model", back_populates="tasks")
    
    video_sources = Column(JSON)
    status = Column(String(20), default='stopped')
    is_enabled = Column(Boolean, default=True)
    
    schedule_type = Column(String(20), default='continuous')
    schedule_days = Column(JSON)
    start_time = Column(Time, default='00:00:00')
    end_time = Column(Time, default='23:59:59')
    
    confidence_threshold = Column(Float, default=0.8)
    alert_debounce_interval = Column(Integer, default=60)
    alert_message = Column(String(255), default="在任务'{task_name}'中，于{time}检测到{class_name}，置信度为{confidence:.2f}%。")
    inference_interval = Column(Float, default=1.0)
    
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 