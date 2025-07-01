package models

import (
	"time"

	"gorm.io/gorm"
)

// User 用户模型
type User struct {
	ID        uint           `json:"id" gorm:"primaryKey"`
	Username  string         `json:"username" gorm:"uniqueIndex;size:50;not null"`
	Email     string         `json:"email" gorm:"uniqueIndex;size:100"`
	Password  string         `json:"-" gorm:"size:255;not null"`
	Role      string         `json:"role" gorm:"size:20;default:user"`
	IsActive  bool           `json:"is_active" gorm:"default:true"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
	DeletedAt gorm.DeletedAt `json:"-" gorm:"index"`
}

// Model 模型信息
type Model struct {
	ID          uint           `json:"id" gorm:"primaryKey"`
	Name        string         `json:"name" gorm:"size:100;not null"`
	Version     string         `json:"version" gorm:"size:20;not null"`
	Description string         `json:"description" gorm:"type:text"`
	FilePath    string         `json:"file_path" gorm:"size:500;not null"`
	ModelType   string         `json:"model_type" gorm:"size:50;not null"` // onnx, tensorrt, etc.
	Platform    string         `json:"platform" gorm:"size:50;not null"`   // cpu, gpu, npu, etc.
	Labels      string         `json:"labels" gorm:"type:json"`             // JSON格式的标签
	Status      ModelStatus    `json:"status" gorm:"default:inactive"`
	IsActive    bool           `json:"is_active" gorm:"default:true"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
	DeletedAt   gorm.DeletedAt `json:"-" gorm:"index"`
}

// ModelStatus 模型状态枚举
type ModelStatus string

const (
	ModelStatusInactive ModelStatus = "inactive"
	ModelStatusActive   ModelStatus = "active"
	ModelStatusLoading  ModelStatus = "loading"
	ModelStatusError    ModelStatus = "error"
)

// Task 任务模型
type Task struct {
	ID          uint           `json:"id" gorm:"primaryKey"`
	Name        string         `json:"name" gorm:"size:100;not null"`
	Description string         `json:"description" gorm:"type:text"`
	ModelID     uint           `json:"model_id" gorm:"not null"`
	Model       Model          `json:"model" gorm:"foreignKey:ModelID"`
	VideoSource string         `json:"video_source" gorm:"size:500"`
	Regions     string         `json:"regions" gorm:"type:json"` // JSON格式的检测区域
	Schedule    string         `json:"schedule" gorm:"size:100"` // cron表达式
	IsEnabled   bool           `json:"is_enabled" gorm:"default:false"`
	Status      TaskStatus     `json:"status" gorm:"default:stopped"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
	DeletedAt   gorm.DeletedAt `json:"-" gorm:"index"`
}

// TaskStatus 任务状态枚举
type TaskStatus string

const (
	TaskStatusStopped TaskStatus = "stopped"
	TaskStatusRunning TaskStatus = "running"
	TaskStatusPaused  TaskStatus = "paused"
	TaskStatusError   TaskStatus = "error"
)

// InferenceRecord 推理记录
type InferenceRecord struct {
	ID           uint                `json:"id" gorm:"primaryKey"`
	TaskID       uint                `json:"task_id" gorm:"not null"`
	Task         Task                `json:"task" gorm:"foreignKey:TaskID"`
	ModelID      uint                `json:"model_id" gorm:"not null"`
	Model        Model               `json:"model" gorm:"foreignKey:ModelID"`
	InputPath    string              `json:"input_path" gorm:"size:500"`
	OutputPath   string              `json:"output_path" gorm:"size:500"`
	Results      string              `json:"results" gorm:"type:json"` // JSON格式的推理结果
	InferenceTime float64             `json:"inference_time"`           // 推理耗时(秒)
	Status       InferenceStatus     `json:"status" gorm:"default:pending"`
	ErrorMessage string              `json:"error_message" gorm:"type:text"`
	CreatedAt    time.Time           `json:"created_at"`
	UpdatedAt    time.Time           `json:"updated_at"`
	DeletedAt    gorm.DeletedAt      `json:"-" gorm:"index"`
}

// InferenceStatus 推理状态枚举
type InferenceStatus string

const (
	InferenceStatusPending   InferenceStatus = "pending"
	InferenceStatusRunning   InferenceStatus = "running"
	InferenceStatusCompleted InferenceStatus = "completed"
	InferenceStatusFailed    InferenceStatus = "failed"
)

// Alert 告警模型
type Alert struct {
	ID          uint           `json:"id" gorm:"primaryKey"`
	TaskID      uint           `json:"task_id" gorm:"not null"`
	Task        Task           `json:"task" gorm:"foreignKey:TaskID"`
	RecordID    uint           `json:"record_id"`
	Record      InferenceRecord `json:"record" gorm:"foreignKey:RecordID"`
	AlertType   string         `json:"alert_type" gorm:"size:50;not null"`
	Title       string         `json:"title" gorm:"size:200;not null"`
	Message     string         `json:"message" gorm:"type:text"`
	Severity    AlertSeverity  `json:"severity" gorm:"default:medium"`
	ImagePath   string         `json:"image_path" gorm:"size:500"`
	IsRead      bool           `json:"is_read" gorm:"default:false"`
	IsResolved  bool           `json:"is_resolved" gorm:"default:false"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
	DeletedAt   gorm.DeletedAt `json:"-" gorm:"index"`
}

// AlertSeverity 告警严重程度枚举
type AlertSeverity string

const (
	AlertSeverityLow      AlertSeverity = "low"
	AlertSeverityMedium   AlertSeverity = "medium"
	AlertSeverityHigh     AlertSeverity = "high"
	AlertSeverityCritical AlertSeverity = "critical"
)

// TableName 指定表名
func (User) TableName() string {
	return "users"
}

func (Model) TableName() string {
	return "models"
}

func (Task) TableName() string {
	return "tasks"
}

func (InferenceRecord) TableName() string {
	return "inference_records"
}

func (Alert) TableName() string {
	return "alerts"
}