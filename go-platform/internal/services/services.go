package services

import (
	"ai-edge/ai-edge/ai-edge/go-platform/internal/config"

	"gorm.io/gorm"
)

// Services 服务集合
type Services struct {
	User      UserService
	Model     ModelService
	Task      TaskService
	Inference InferenceService
	Alert     AlertService
	Auth      AuthService
}

// NewServices 创建服务实例
func NewServices(db *gorm.DB, cfg *config.Config) *Services {
	return &Services{
		User:      NewUserService(db),
		Model:     NewModelService(db),
		Task:      NewTaskService(db),
		Inference: NewInferenceService(db),
		Alert:     NewAlertService(db),
		Auth:      NewAuthService(db, cfg.JWT),
	}
}