package handlers

import (
	"ai-edge/internal/services"
	"ai-edge/pkg/logger"
)

// Handlers 包含所有处理器
type Handlers struct {
	Auth         *AuthHandler
	User         *UserHandler
	Model        *ModelHandler
	Task         *TaskHandler
	Inference    *InferenceHandler
	Alert        *AlertHandler
	Health       *HealthHandler
	Scheduler    *SchedulerHandler
	Manager      *ManagerHandler
	Monitor      *MonitorHandler
	AlertManager *AlertManagerHandler
	HealthChecker *HealthCheckerHandler
	System       *SystemHandler
	File         *FileHandler
	Stats        *StatsHandler
}

// NewHandlers 创建新的处理器集合
func NewHandlers(services *services.Services) *Handlers {
	log := logger.GetLogger()

	return &Handlers{
		Auth:          NewAuthHandler(services.Auth, log),
		User:          NewUserHandler(services.User, log),
		Model:         NewModelHandler(services.Model, log),
		Task:          NewTaskHandler(services.Task, log),
		Inference:     NewInferenceHandler(services.Inference, log),
		Alert:         NewAlertHandler(services.Alert, log),
		Health:        NewHealthHandler(services, log),
		Scheduler:     NewSchedulerHandler(services.Task, log),
		Manager:       NewManagerHandler(services, log),
		Monitor:       NewMonitorHandler(services, log),
		AlertManager:  NewAlertManagerHandler(services.Alert, log),
		HealthChecker: NewHealthCheckerHandler(services, log),
		System:        NewSystemHandler(services, log),
		File:          NewFileHandler(services.File, log),
		Stats:         NewStatsHandler(services, log),
	}
}