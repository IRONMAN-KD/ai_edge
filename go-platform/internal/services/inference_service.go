package services

import (
	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"

	"gorm.io/gorm"
)

// InferenceService 推理服务接口
type InferenceService interface {
	Create(record *models.InferenceRecord) error
	GetByID(id uint) (*models.InferenceRecord, error)
	Update(record *models.InferenceRecord) error
	Delete(id uint) error
	List(offset, limit int, taskID uint) ([]*models.InferenceRecord, int64, error)
	GetByTaskID(taskID uint, offset, limit int) ([]*models.InferenceRecord, int64, error)
	GetStatistics(taskID uint) (map[string]interface{}, error)
}

type inferenceService struct {
	db *gorm.DB
}

// NewInferenceService 创建推理服务实例
func NewInferenceService(db *gorm.DB) InferenceService {
	return &inferenceService{db: db}
}

// Create 创建推理记录
func (s *inferenceService) Create(record *models.InferenceRecord) error {
	return s.db.Create(record).Error
}

// GetByID 根据ID获取推理记录
func (s *inferenceService) GetByID(id uint) (*models.InferenceRecord, error) {
	var record models.InferenceRecord
	if err := s.db.Preload("Task").Preload("Model").First(&record, id).Error; err != nil {
		return nil, err
	}
	return &record, nil
}

// Update 更新推理记录
func (s *inferenceService) Update(record *models.InferenceRecord) error {
	return s.db.Save(record).Error
}

// Delete 删除推理记录
func (s *inferenceService) Delete(id uint) error {
	return s.db.Delete(&models.InferenceRecord{}, id).Error
}

// List 获取推理记录列表
func (s *inferenceService) List(offset, limit int, taskID uint) ([]*models.InferenceRecord, int64, error) {
	var records []*models.InferenceRecord
	var total int64

	query := s.db.Model(&models.InferenceRecord{})
	if taskID > 0 {
		query = query.Where("task_id = ?", taskID)
	}

	// 获取总数
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// 获取分页数据
	if err := query.Preload("Task").Preload("Model").Offset(offset).Limit(limit).Order("created_at DESC").Find(&records).Error; err != nil {
		return nil, 0, err
	}

	return records, total, nil
}

// GetByTaskID 根据任务ID获取推理记录
func (s *inferenceService) GetByTaskID(taskID uint, offset, limit int) ([]*models.InferenceRecord, int64, error) {
	return s.List(offset, limit, taskID)
}

// GetStatistics 获取推理统计信息
func (s *inferenceService) GetStatistics(taskID uint) (map[string]interface{}, error) {
	var stats map[string]interface{} = make(map[string]interface{})

	query := s.db.Model(&models.InferenceRecord{})
	if taskID > 0 {
		query = query.Where("task_id = ?", taskID)
	}

	// 总记录数
	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, err
	}
	stats["total"] = total

	// 各状态统计
	var statusStats []struct {
		Status string
		Count  int64
	}
	if err := query.Select("status, count(*) as count").Group("status").Scan(&statusStats).Error; err != nil {
		return nil, err
	}
	stats["status_stats"] = statusStats

	// 平均推理时间
	var avgTime float64
	if err := query.Where("status = ?", models.InferenceStatusCompleted).Select("AVG(inference_time)").Scan(&avgTime).Error; err != nil {
		return nil, err
	}
	stats["avg_inference_time"] = avgTime

	return stats, nil
}