package handlers

import (
	"net/http"
	"strconv"

	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/services"

	"github.com/gin-gonic/gin"
)

// InferenceHandler 推理记录处理器
type InferenceHandler struct {
	inferenceService services.InferenceService
}

// NewInferenceHandler 创建推理记录处理器
func NewInferenceHandler(inferenceService services.InferenceService) *InferenceHandler {
	return &InferenceHandler{
		inferenceService: inferenceService,
	}
}

// CreateInferenceRequest 创建推理记录请求
type CreateInferenceRequest struct {
	TaskID      uint                      `json:"task_id" binding:"required"`
	InputData   string                    `json:"input_data" binding:"required"`
	OutputData  string                    `json:"output_data"`
	Confidence  float64                   `json:"confidence"`
	Status      models.InferenceStatus    `json:"status"`
	ErrorMsg    string                    `json:"error_msg"`
	ProcessTime float64                   `json:"process_time"`
}

// UpdateInferenceRequest 更新推理记录请求
type UpdateInferenceRequest struct {
	OutputData  string                    `json:"output_data"`
	Confidence  float64                   `json:"confidence"`
	Status      models.InferenceStatus    `json:"status"`
	ErrorMsg    string                    `json:"error_msg"`
	ProcessTime float64                   `json:"process_time"`
}

// List 获取推理记录列表
func (h *InferenceHandler) List(c *gin.Context) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "10"))
	taskIDStr := c.Query("task_id")

	offset := (page - 1) * pageSize

	var records []*models.InferenceRecord
	var total int64
	var err error

	if taskIDStr != "" {
		taskID, err := strconv.ParseUint(taskIDStr, 10, 32)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
			return
		}
		records, total, err = h.inferenceService.GetByTaskID(uint(taskID), offset, pageSize)
	} else {
		records, total, err = h.inferenceService.List(offset, pageSize)
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":       records,
		"total":      total,
		"page":       page,
		"page_size":  pageSize,
		"total_page": (total + int64(pageSize) - 1) / int64(pageSize),
	})
}

// Create 创建推理记录
func (h *InferenceHandler) Create(c *gin.Context) {
	var req CreateInferenceRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	record := &models.InferenceRecord{
		TaskID:      req.TaskID,
		InputData:   req.InputData,
		OutputData:  req.OutputData,
		Confidence:  req.Confidence,
		Status:      req.Status,
		ErrorMsg:    req.ErrorMsg,
		ProcessTime: req.ProcessTime,
	}

	if record.Status == "" {
		record.Status = models.InferenceStatusPending
	}

	if err := h.inferenceService.Create(record); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, record)
}

// GetByID 根据ID获取推理记录
func (h *InferenceHandler) GetByID(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid inference record ID"})
		return
	}

	record, err := h.inferenceService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Inference record not found"})
		return
	}

	c.JSON(http.StatusOK, record)
}

// Update 更新推理记录
func (h *InferenceHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid inference record ID"})
		return
	}

	var req UpdateInferenceRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	record, err := h.inferenceService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Inference record not found"})
		return
	}

	// 更新字段
	if req.OutputData != "" {
		record.OutputData = req.OutputData
	}
	if req.Confidence != 0 {
		record.Confidence = req.Confidence
	}
	if req.Status != "" {
		record.Status = req.Status
	}
	if req.ErrorMsg != "" {
		record.ErrorMsg = req.ErrorMsg
	}
	if req.ProcessTime != 0 {
		record.ProcessTime = req.ProcessTime
	}

	if err := h.inferenceService.Update(record); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, record)
}

// Delete 删除推理记录
func (h *InferenceHandler) Delete(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid inference record ID"})
		return
	}

	if err := h.inferenceService.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Inference record deleted successfully"})
}

// GetStats 获取推理统计信息
func (h *InferenceHandler) GetStats(c *gin.Context) {
	taskIDStr := c.Query("task_id")

	var stats map[string]interface{}
	var err error

	if taskIDStr != "" {
		taskID, err := strconv.ParseUint(taskIDStr, 10, 32)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
			return
		}
		stats, err = h.inferenceService.GetStatsByTaskID(uint(taskID))
	} else {
		stats, err = h.inferenceService.GetStats()
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, stats)
}