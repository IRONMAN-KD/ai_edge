package handlers

import (
	"net/http"
	"strconv"

	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/services"

	"github.com/gin-gonic/gin"
)

// AlertHandler 告警处理器
type AlertHandler struct {
	alertService services.AlertService
}

// NewAlertHandler 创建告警处理器
func NewAlertHandler(alertService services.AlertService) *AlertHandler {
	return &AlertHandler{
		alertService: alertService,
	}
}

// CreateAlertRequest 创建告警请求
type CreateAlertRequest struct {
	Title       string                `json:"title" binding:"required"`
	Message     string                `json:"message" binding:"required"`
	Severity    models.AlertSeverity  `json:"severity" binding:"required"`
	TaskID      *uint                 `json:"task_id"`
	ModelID     *uint                 `json:"model_id"`
	Source      string                `json:"source"`
}

// UpdateAlertRequest 更新告警请求
type UpdateAlertRequest struct {
	Title       string                `json:"title"`
	Message     string                `json:"message"`
	Severity    models.AlertSeverity  `json:"severity"`
	TaskID      *uint                 `json:"task_id"`
	ModelID     *uint                 `json:"model_id"`
	Source      string                `json:"source"`
	IsRead      *bool                 `json:"is_read"`
	IsResolved  *bool                 `json:"is_resolved"`
}

// List 获取告警列表
func (h *AlertHandler) List(c *gin.Context) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "10"))
	isRead := c.Query("is_read")
	isResolved := c.Query("is_resolved")
	severity := c.Query("severity")

	offset := (page - 1) * pageSize

	// 构建过滤条件
	filters := make(map[string]interface{})
	if isRead != "" {
		if isRead == "true" {
			filters["is_read"] = true
		} else if isRead == "false" {
			filters["is_read"] = false
		}
	}
	if isResolved != "" {
		if isResolved == "true" {
			filters["is_resolved"] = true
		} else if isResolved == "false" {
			filters["is_resolved"] = false
		}
	}
	if severity != "" {
		filters["severity"] = severity
	}

	alerts, total, err := h.alertService.List(offset, pageSize, filters)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":       alerts,
		"total":      total,
		"page":       page,
		"page_size":  pageSize,
		"total_page": (total + int64(pageSize) - 1) / int64(pageSize),
	})
}

// Create 创建告警
func (h *AlertHandler) Create(c *gin.Context) {
	var req CreateAlertRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	alert := &models.Alert{
		Title:      req.Title,
		Message:    req.Message,
		Severity:   req.Severity,
		TaskID:     req.TaskID,
		ModelID:    req.ModelID,
		Source:     req.Source,
		IsRead:     false,
		IsResolved: false,
	}

	if err := h.alertService.Create(alert); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, alert)
}

// GetByID 根据ID获取告警
func (h *AlertHandler) GetByID(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid alert ID"})
		return
	}

	alert, err := h.alertService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Alert not found"})
		return
	}

	c.JSON(http.StatusOK, alert)
}

// Update 更新告警
func (h *AlertHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid alert ID"})
		return
	}

	var req UpdateAlertRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	alert, err := h.alertService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Alert not found"})
		return
	}

	// 更新字段
	if req.Title != "" {
		alert.Title = req.Title
	}
	if req.Message != "" {
		alert.Message = req.Message
	}
	if req.Severity != "" {
		alert.Severity = req.Severity
	}
	if req.TaskID != nil {
		alert.TaskID = req.TaskID
	}
	if req.ModelID != nil {
		alert.ModelID = req.ModelID
	}
	if req.Source != "" {
		alert.Source = req.Source
	}
	if req.IsRead != nil {
		alert.IsRead = *req.IsRead
	}
	if req.IsResolved != nil {
		alert.IsResolved = *req.IsResolved
	}

	if err := h.alertService.Update(alert); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, alert)
}

// Delete 删除告警
func (h *AlertHandler) Delete(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid alert ID"})
		return
	}

	if err := h.alertService.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Alert deleted successfully"})
}

// MarkAsRead 标记告警为已读
func (h *AlertHandler) MarkAsRead(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid alert ID"})
		return
	}

	if err := h.alertService.MarkAsRead(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Alert marked as read"})
}

// MarkAsResolved 标记告警为已解决
func (h *AlertHandler) MarkAsResolved(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid alert ID"})
		return
	}

	if err := h.alertService.MarkAsResolved(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Alert marked as resolved"})
}

// GetUnreadCount 获取未读告警数量
func (h *AlertHandler) GetUnreadCount(c *gin.Context) {
	count, err := h.alertService.GetUnreadCount()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"unread_count": count})
}

// GetStats 获取告警统计信息
func (h *AlertHandler) GetStats(c *gin.Context) {
	stats, err := h.alertService.GetStats()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, stats)
}