package services

import (
	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"

	"gorm.io/gorm"
)

// ModelService 模型服务接口
type ModelService interface {
	Create(model *models.Model) error
	GetByID(id uint) (*models.Model, error)
	Update(model *models.Model) error
	Delete(id uint) error
	List(offset, limit int, platform string) ([]*models.Model, int64, error)
	GetActiveModels(platform string) ([]*models.Model, error)
	ActivateModel(id uint) error
	DeactivateModel(id uint) error
	GetByNameAndVersion(name, version string) (*models.Model, error)
}

type modelService struct {
	db *gorm.DB
}

// NewModelService 创建模型服务实例
func NewModelService(db *gorm.DB) ModelService {
	return &modelService{db: db}
}

// Create 创建模型
func (s *modelService) Create(model *models.Model) error {
	return s.db.Create(model).Error
}

// GetByID 根据ID获取模型
func (s *modelService) GetByID(id uint) (*models.Model, error) {
	var model models.Model
	if err := s.db.First(&model, id).Error; err != nil {
		return nil, err
	}
	return &model, nil
}

// Update 更新模型
func (s *modelService) Update(model *models.Model) error {
	return s.db.Save(model).Error
}

// Delete 删除模型
func (s *modelService) Delete(id uint) error {
	return s.db.Delete(&models.Model{}, id).Error
}

// List 获取模型列表
func (s *modelService) List(offset, limit int, platform string) ([]*models.Model, int64, error) {
	var models []*models.Model
	var total int64

	query := s.db.Model(&models.Model{})
	if platform != "" {
		query = query.Where("platform = ?", platform)
	}

	// 获取总数
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// 获取分页数据
	if err := query.Offset(offset).Limit(limit).Order("created_at DESC").Find(&models).Error; err != nil {
		return nil, 0, err
	}

	return models, total, nil
}

// GetActiveModels 获取激活的模型列表
func (s *modelService) GetActiveModels(platform string) ([]*models.Model, error) {
	var models []*models.Model
	query := s.db.Where("status = ? AND is_active = ?", models.ModelStatusActive, true)
	if platform != "" {
		query = query.Where("platform = ?", platform)
	}

	if err := query.Find(&models).Error; err != nil {
		return nil, err
	}
	return models, nil
}

// ActivateModel 激活模型
func (s *modelService) ActivateModel(id uint) error {
	return s.db.Model(&models.Model{}).Where("id = ?", id).Updates(map[string]interface{}{
		"status":    models.ModelStatusActive,
		"is_active": true,
	}).Error
}

// DeactivateModel 停用模型
func (s *modelService) DeactivateModel(id uint) error {
	return s.db.Model(&models.Model{}).Where("id = ?", id).Updates(map[string]interface{}{
		"status":    models.ModelStatusInactive,
		"is_active": false,
	}).Error
}

// GetByNameAndVersion 根据名称和版本获取模型
func (s *modelService) GetByNameAndVersion(name, version string) (*models.Model, error) {
	var model models.Model
	if err := s.db.Where("name = ? AND version = ?", name, version).First(&model).Error; err != nil {
		return nil, err
	}
	return &model, nil
}