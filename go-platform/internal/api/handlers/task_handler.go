package handlers

import (
	"net/http"
	"strconv"

	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/services"

	"github.com/gin-gonic/gin"
)

// TaskHandler 任务处理器
type TaskHandler struct {
	taskService services.TaskService
}

// NewTaskHandler 创建任务处理器
func NewTaskHandler(taskService services.TaskService) *TaskHandler {
	return &TaskHandler{
		taskService: taskService,
	}
}

// CreateTaskRequest 创建任务请求
type CreateTaskRequest struct {
	Name        string `json:"name" binding:"required"`
	Description string `json:"description"`
	ModelID     uint   `json:"model_id" binding:"required"`
	VideoSource string `json:"video_source"`
	Regions     string `json:"regions"`
	Schedule    string `json:"schedule"`
}

// UpdateTaskRequest 更新任务请求
type UpdateTaskRequest struct {
	Name        string           `json:"name"`
	Description string           `json:"description"`
	ModelID     uint             `json:"model_id"`
	VideoSource string           `json:"video_source"`
	Regions     string           `json:"regions"`
	Schedule    string           `json:"schedule"`
	IsEnabled   *bool            `json:"is_enabled"`
	Status      models.TaskStatus `json:"status"`
}

// List 获取任务列表
func (h *TaskHandler) List(c *gin.Context) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "10"))

	offset := (page - 1) * pageSize
	tasks, total, err := h.taskService.List(offset, pageSize)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":       tasks,
		"total":      total,
		"page":       page,
		"page_size":  pageSize,
		"total_page": (total + int64(pageSize) - 1) / int64(pageSize),
	})
}

// Create 创建任务
func (h *TaskHandler) Create(c *gin.Context) {
	var req CreateTaskRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	task := &models.Task{
		Name:        req.Name,
		Description: req.Description,
		ModelID:     req.ModelID,
		VideoSource: req.VideoSource,
		Regions:     req.Regions,
		Schedule:    req.Schedule,
		IsEnabled:   false,
		Status:      models.TaskStatusStopped,
	}

	if err := h.taskService.Create(task); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, task)
}

// GetByID 根据ID获取任务
func (h *TaskHandler) GetByID(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	task, err := h.taskService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Task not found"})
		return
	}

	c.JSON(http.StatusOK, task)
}

// Update 更新任务
func (h *TaskHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	var req UpdateTaskRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	task, err := h.taskService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Task not found"})
		return
	}

	// 更新字段
	if req.Name != "" {
		task.Name = req.Name
	}
	if req.Description != "" {
		task.Description = req.Description
	}
	if req.ModelID != 0 {
		task.ModelID = req.ModelID
	}
	if req.VideoSource != "" {
		task.VideoSource = req.VideoSource
	}
	if req.Regions != "" {
		task.Regions = req.Regions
	}
	if req.Schedule != "" {
		task.Schedule = req.Schedule
	}
	if req.IsEnabled != nil {
		task.IsEnabled = *req.IsEnabled
	}
	if req.Status != "" {
		task.Status = req.Status
	}

	if err := h.taskService.Update(task); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, task)
}

// Delete 删除任务
func (h *TaskHandler) Delete(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	if err := h.taskService.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Task deleted successfully"})
}

// Start 启动任务
func (h *TaskHandler) Start(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	if err := h.taskService.StartTask(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Task started successfully"})
}

// Stop 停止任务
func (h *TaskHandler) Stop(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	if err := h.taskService.StopTask(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Task stopped successfully"})
}

// Pause 暂停任务
func (h *TaskHandler) Pause(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	if err := h.taskService.PauseTask(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Task paused successfully"})
}

// Resume 恢复任务
func (h *TaskHandler) Resume(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	if err := h.taskService.ResumeTask(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Task resumed successfully"})
}