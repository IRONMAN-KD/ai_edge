package services

import (
	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"

	"gorm.io/gorm"
)

// AlertService 告警服务接口
type AlertService interface {
	Create(alert *models.Alert) error
	GetByID(id uint) (*models.Alert, error)
	Update(alert *models.Alert) error
	Delete(id uint) error
	List(offset, limit int, taskID uint, isRead *bool) ([]*models.Alert, int64, error)
	MarkAsRead(id uint) error
	MarkAsResolved(id uint) error
	GetUnreadCount(taskID uint) (int64, error)
	GetStatistics(taskID uint) (map[string]interface{}, error)
}

type alertService struct {
	db *gorm.DB
}

// NewAlertService 创建告警服务实例
func NewAlertService(db *gorm.DB) AlertService {
	return &alertService{db: db}
}

// Create 创建告警
func (s *alertService) Create(alert *models.Alert) error {
	return s.db.Create(alert).Error
}

// GetByID 根据ID获取告警
func (s *alertService) GetByID(id uint) (*models.Alert, error) {
	var alert models.Alert
	if err := s.db.Preload("Task").Preload("Record").First(&alert, id).Error; err != nil {
		return nil, err
	}
	return &alert, nil
}

// Update 更新告警
func (s *alertService) Update(alert *models.Alert) error {
	return s.db.Save(alert).Error
}

// Delete 删除告警
func (s *alertService) Delete(id uint) error {
	return s.db.Delete(&models.Alert{}, id).Error
}

// List 获取告警列表
func (s *alertService) List(offset, limit int, taskID uint, isRead *bool) ([]*models.Alert, int64, error) {
	var alerts []*models.Alert
	var total int64

	query := s.db.Model(&models.Alert{})
	if taskID > 0 {
		query = query.Where("task_id = ?", taskID)
	}
	if isRead != nil {
		query = query.Where("is_read = ?", *isRead)
	}

	// 获取总数
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// 获取分页数据
	if err := query.Preload("Task").Preload("Record").Offset(offset).Limit(limit).Order("created_at DESC").Find(&alerts).Error; err != nil {
		return nil, 0, err
	}

	return alerts, total, nil
}

// MarkAsRead 标记为已读
func (s *alertService) MarkAsRead(id uint) error {
	return s.db.Model(&models.Alert{}).Where("id = ?", id).Update("is_read", true).Error
}

// MarkAsResolved 标记为已解决
func (s *alertService) MarkAsResolved(id uint) error {
	return s.db.Model(&models.Alert{}).Where("id = ?", id).Updates(map[string]interface{}{
		"is_resolved": true,
		"is_read":     true,
	}).Error
}

// GetUnreadCount 获取未读告警数量
func (s *alertService) GetUnreadCount(taskID uint) (int64, error) {
	var count int64
	query := s.db.Model(&models.Alert{}).Where("is_read = ?", false)
	if taskID > 0 {
		query = query.Where("task_id = ?", taskID)
	}
	return count, query.Count(&count).Error
}

// GetStatistics 获取告警统计信息
func (s *alertService) GetStatistics(taskID uint) (map[string]interface{}, error) {
	var stats map[string]interface{} = make(map[string]interface{})

	query := s.db.Model(&models.Alert{})
	if taskID > 0 {
		query = query.Where("task_id = ?", taskID)
	}

	// 总告警数
	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, err
	}
	stats["total"] = total

	// 未读告警数
	var unread int64
	if err := query.Where("is_read = ?", false).Count(&unread).Error; err != nil {
		return nil, err
	}
	stats["unread"] = unread

	// 未解决告警数
	var unresolved int64
	if err := query.Where("is_resolved = ?", false).Count(&unresolved).Error; err != nil {
		return nil, err
	}
	stats["unresolved"] = unresolved

	// 按严重程度统计
	var severityStats []struct {
		Severity string
		Count    int64
	}
	if err := query.Select("severity, count(*) as count").Group("severity").Scan(&severityStats).Error; err != nil {
		return nil, err
	}
	stats["severity_stats"] = severityStats

	// 按类型统计
	var typeStats []struct {
		AlertType string
		Count     int64
	}
	if err := query.Select("alert_type, count(*) as count").Group("alert_type").Scan(&typeStats).Error; err != nil {
		return nil, err
	}
	stats["type_stats"] = typeStats

	return stats, nil
}