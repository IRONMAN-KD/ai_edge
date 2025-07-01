package services

import (
	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"

	"gorm.io/gorm"
)

// TaskService 任务服务接口
type TaskService interface {
	Create(task *models.Task) error
	GetByID(id uint) (*models.Task, error)
	Update(task *models.Task) error
	Delete(id uint) error
	List(offset, limit int) ([]*models.Task, int64, error)
	GetEnabledTasks() ([]*models.Task, error)
	StartTask(id uint) error
	StopTask(id uint) error
	PauseTask(id uint) error
	ResumeTask(id uint) error
}

type taskService struct {
	db *gorm.DB
}

// NewTaskService 创建任务服务实例
func NewTaskService(db *gorm.DB) TaskService {
	return &taskService{db: db}
}

// Create 创建任务
func (s *taskService) Create(task *models.Task) error {
	return s.db.Create(task).Error
}

// GetByID 根据ID获取任务
func (s *taskService) GetByID(id uint) (*models.Task, error) {
	var task models.Task
	if err := s.db.Preload("Model").First(&task, id).Error; err != nil {
		return nil, err
	}
	return &task, nil
}

// Update 更新任务
func (s *taskService) Update(task *models.Task) error {
	return s.db.Save(task).Error
}

// Delete 删除任务
func (s *taskService) Delete(id uint) error {
	return s.db.Delete(&models.Task{}, id).Error
}

// List 获取任务列表
func (s *taskService) List(offset, limit int) ([]*models.Task, int64, error) {
	var tasks []*models.Task
	var total int64

	// 获取总数
	if err := s.db.Model(&models.Task{}).Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// 获取分页数据
	if err := s.db.Preload("Model").Offset(offset).Limit(limit).Order("created_at DESC").Find(&tasks).Error; err != nil {
		return nil, 0, err
	}

	return tasks, total, nil
}

// GetEnabledTasks 获取启用的任务列表
func (s *taskService) GetEnabledTasks() ([]*models.Task, error) {
	var tasks []*models.Task
	if err := s.db.Preload("Model").Where("is_enabled = ?", true).Find(&tasks).Error; err != nil {
		return nil, err
	}
	return tasks, nil
}

// StartTask 启动任务
func (s *taskService) StartTask(id uint) error {
	return s.db.Model(&models.Task{}).Where("id = ?", id).Updates(map[string]interface{}{
		"status":     models.TaskStatusRunning,
		"is_enabled": true,
	}).Error
}

// StopTask 停止任务
func (s *taskService) StopTask(id uint) error {
	return s.db.Model(&models.Task{}).Where("id = ?", id).Updates(map[string]interface{}{
		"status":     models.TaskStatusStopped,
		"is_enabled": false,
	}).Error
}

// PauseTask 暂停任务
func (s *taskService) PauseTask(id uint) error {
	return s.db.Model(&models.Task{}).Where("id = ?", id).Update("status", models.TaskStatusPaused).Error
}

// ResumeTask 恢复任务
func (s *taskService) ResumeTask(id uint) error {
	return s.db.Model(&models.Task{}).Where("id = ?", id).Update("status", models.TaskStatusRunning).Error
}