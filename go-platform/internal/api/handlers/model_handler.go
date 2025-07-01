package handlers

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"

	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/services"
	"ai-edge/ai-edge/ai-edge/go-platform/pkg/logger"
	"ai-edge/ai-edge/ai-edge/go-platform/pkg/response"
	"ai-edge/ai-edge/ai-edge/go-platform/pkg/validator"
)

// ModelHandler 模型处理器
type ModelHandler struct {
	modelService *services.ModelService
	logger       *logger.Logger
}

// NewModelHandler 创建模型处理器
func NewModelHandler(modelService *services.ModelService, logger *logger.Logger) *ModelHandler {
	return &ModelHandler{
		modelService: modelService,
		logger:       logger,
	}
}

// CreateModelRequest 创建模型请求
type CreateModelRequest struct {
	Name        string                 `json:"name" validate:"required,min=1,max=100,model_name" label:"模型名称"`
	Description string                 `json:"description" validate:"omitempty,max=500" label:"模型描述"`
	Type        string                 `json:"type" validate:"required,oneof=llm embedding vision audio multimodal" label:"模型类型"`
	Provider    string                 `json:"provider" validate:"required,min=1,max=50" label:"模型提供商"`
	Version     string                 `json:"version" validate:"omitempty,version" label:"模型版本"`
	Config      map[string]interface{} `json:"config" validate:"omitempty" label:"模型配置"`
	Status      string                 `json:"status" validate:"omitempty,oneof=active inactive maintenance" label:"状态"`
	Tags        []string               `json:"tags" validate:"omitempty,dive,min=1,max=20" label:"标签"`
}

// UpdateModelRequest 更新模型请求
type UpdateModelRequest struct {
	Description string                 `json:"description" validate:"omitempty,max=500" label:"模型描述"`
	Config      map[string]interface{} `json:"config" validate:"omitempty" label:"模型配置"`
	Status      string                 `json:"status" validate:"omitempty,oneof=active inactive maintenance" label:"状态"`
	Tags        []string               `json:"tags" validate:"omitempty,dive,min=1,max=20" label:"标签"`
}

// ModelResponse 模型响应
type ModelResponse struct {
	ID          uint                   `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Type        string                 `json:"type"`
	Provider    string                 `json:"provider"`
	Version     string                 `json:"version"`
	Config      map[string]interface{} `json:"config"`
	Status      string                 `json:"status"`
	Tags        []string               `json:"tags"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	CreatedBy   uint                   `json:"created_by"`
	UpdatedBy   uint                   `json:"updated_by"`
}

// ModelListQuery 模型列表查询参数
type ModelListQuery struct {
	Page     int      `form:"page" validate:"omitempty,min=1" label:"页码"`
	PageSize int      `form:"page_size" validate:"omitempty,min=1,max=100" label:"每页数量"`
	Type     string   `form:"type" validate:"omitempty,oneof=llm embedding vision audio multimodal" label:"模型类型"`
	Provider string   `form:"provider" validate:"omitempty,max=50" label:"模型提供商"`
	Status   string   `form:"status" validate:"omitempty,oneof=active inactive maintenance" label:"状态"`
	Keyword  string   `form:"keyword" validate:"omitempty,max=50" label:"关键词"`
	Tags     []string `form:"tags" validate:"omitempty,dive,min=1,max=20" label:"标签"`
	SortBy   string   `form:"sort_by" validate:"omitempty,oneof=id name type provider created_at updated_at" label:"排序字段"`
	SortDesc bool     `form:"sort_desc" label:"降序排列"`
}

// CreateModel 创建模型
func (h *ModelHandler) CreateModel(c *gin.Context) {
	var req CreateModelRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定创建模型请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("创建模型请求验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 检查模型名称是否已存在
	if _, err := h.modelService.GetByName(req.Name); err == nil {
		h.logger.Warn("模型名称已存在", "name", req.Name)
		response.Conflict(c, "模型名称已存在")
		return
	}

	// 从上下文获取用户ID
	userID, exists := c.Get("user_id")
	if !exists {
		response.Unauthorized(c, "未认证的用户")
		return
	}

	// 设置默认状态
	status := req.Status
	if status == "" {
		status = "active"
	}

	// 创建模型
	model := &models.Model{
		Name:        req.Name,
		Description: req.Description,
		Type:        req.Type,
		Provider:    req.Provider,
		Version:     req.Version,
		Config:      req.Config,
		Status:      status,
		Tags:        req.Tags,
		CreatedBy:   userID.(uint),
		UpdatedBy:   userID.(uint),
	}

	if err := h.modelService.Create(model); err != nil {
		h.logger.Error("创建模型失败", "name", req.Name, "error", err)
		response.InternalServerError(c, "创建模型失败")
		return
	}

	// 记录操作日志
	h.logger.Info("模型创建成功", "model_id", model.ID, "name", model.Name, "user_id", userID)

	response.Created(c, h.toModelResponse(model))
}

// GetModel 获取模型详情
func (h *ModelHandler) GetModel(c *gin.Context) {
	modelID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		h.logger.Error("模型ID格式错误", "id", c.Param("id"), "error", err)
		response.BadRequest(c, "模型ID格式错误")
		return
	}

	model, err := h.modelService.GetByID(uint(modelID))
	if err != nil {
		h.logger.Error("查找模型失败", "model_id", modelID, "error", err)
		response.NotFound(c, "模型不存在")
		return
	}

	response.Success(c, h.toModelResponse(model))
}

// UpdateModel 更新模型
func (h *ModelHandler) UpdateModel(c *gin.Context) {
	modelID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		h.logger.Error("模型ID格式错误", "id", c.Param("id"), "error", err)
		response.BadRequest(c, "模型ID格式错误")
		return
	}

	var req UpdateModelRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定更新模型请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("更新模型请求验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 查找模型
	model, err := h.modelService.GetByID(uint(modelID))
	if err != nil {
		h.logger.Error("查找模型失败", "model_id", modelID, "error", err)
		response.NotFound(c, "模型不存在")
		return
	}

	// 从上下文获取用户ID
	userID, exists := c.Get("user_id")
	if !exists {
		response.Unauthorized(c, "未认证的用户")
		return
	}

	// 更新模型信息
	if req.Description != "" {
		model.Description = req.Description
	}
	if req.Config != nil {
		model.Config = req.Config
	}
	if req.Status != "" {
		model.Status = req.Status
	}
	if req.Tags != nil {
		model.Tags = req.Tags
	}
	model.UpdatedBy = userID.(uint)

	if err := h.modelService.Update(model); err != nil {
		h.logger.Error("更新模型失败", "model_id", modelID, "error", err)
		response.InternalServerError(c, "更新模型失败")
		return
	}

	// 记录操作日志
	h.logger.Info("模型更新成功", "model_id", modelID, "user_id", userID)

	response.Success(c, h.toModelResponse(model))
}

// DeleteModel 删除模型
func (h *ModelHandler) DeleteModel(c *gin.Context) {
	modelID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		h.logger.Error("模型ID格式错误", "id", c.Param("id"), "error", err)
		response.BadRequest(c, "模型ID格式错误")
		return
	}

	// 查找模型
	model, err := h.modelService.GetByID(uint(modelID))
	if err != nil {
		h.logger.Error("查找模型失败", "model_id", modelID, "error", err)
		response.NotFound(c, "模型不存在")
		return
	}

	// 删除模型
	if err := h.modelService.Delete(uint(modelID)); err != nil {
		h.logger.Error("删除模型失败", "model_id", modelID, "error", err)
		response.InternalServerError(c, "删除模型失败")
		return
	}

	// 记录操作日志
	userID, _ := c.Get("user_id")
	h.logger.Info("模型删除成功", "model_id", modelID, "name", model.Name, "user_id", userID)

	response.NoContent(c)
}

// ListModels 获取模型列表
func (h *ModelHandler) ListModels(c *gin.Context) {
	var query ModelListQuery
	if err := c.ShouldBindQuery(&query); err != nil {
		h.logger.Error("绑定模型列表查询参数失败", "error", err)
		response.BadRequest(c, "查询参数格式错误")
		return
	}

	// 验证查询参数
	if err := validator.Validate(&query); err != nil {
		h.logger.Error("模型列表查询参数验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 设置默认值
	if query.Page <= 0 {
		query.Page = 1
	}
	if query.PageSize <= 0 {
		query.PageSize = 20
	}
	if query.SortBy == "" {
		query.SortBy = "created_at"
	}

	// 构建查询条件
	filters := make(map[string]interface{})
	if query.Type != "" {
		filters["type"] = query.Type
	}
	if query.Provider != "" {
		filters["provider"] = query.Provider
	}
	if query.Status != "" {
		filters["status"] = query.Status
	}
	if len(query.Tags) > 0 {
		filters["tags"] = query.Tags
	}

	// 获取模型列表
	models, total, err := h.modelService.List(query.Page, query.PageSize, filters, query.Keyword, query.SortBy, query.SortDesc)
	if err != nil {
		h.logger.Error("获取模型列表失败", "error", err)
		response.InternalServerError(c, "获取模型列表失败")
		return
	}

	// 转换为响应格式
	modelResponses := make([]ModelResponse, len(models))
	for i, model := range models {
		modelResponses[i] = h.toModelResponse(&model)
	}

	// 返回分页结果
	response.Paginated(c, modelResponses, total, query.Page, query.PageSize)
}

// GetModelsByType 根据类型获取模型列表
func (h *ModelHandler) GetModelsByType(c *gin.Context) {
	modelType := c.Param("type")
	if modelType == "" {
		h.logger.Error("模型类型不能为空")
		response.BadRequest(c, "模型类型不能为空")
		return
	}

	// 验证模型类型
	validTypes := []string{"llm", "embedding", "vision", "audio", "multimodal"}
	valid := false
	for _, validType := range validTypes {
		if modelType == validType {
			valid = true
			break
		}
	}
	if !valid {
		h.logger.Error("无效的模型类型", "type", modelType)
		response.BadRequest(c, "无效的模型类型")
		return
	}

	// 获取指定类型的模型
	models, err := h.modelService.GetByType(modelType)
	if err != nil {
		h.logger.Error("获取指定类型模型失败", "type", modelType, "error", err)
		response.InternalServerError(c, "获取模型列表失败")
		return
	}

	// 转换为响应格式
	modelResponses := make([]ModelResponse, len(models))
	for i, model := range models {
		modelResponses[i] = h.toModelResponse(&model)
	}

	response.Success(c, modelResponses)
}

// GetModelStats 获取模型统计信息
func (h *ModelHandler) GetModelStats(c *gin.Context) {
	stats, err := h.modelService.GetStats()
	if err != nil {
		h.logger.Error("获取模型统计信息失败", "error", err)
		response.InternalServerError(c, "获取模型统计信息失败")
		return
	}

	response.Success(c, stats)
}

// TestModel 测试模型连接
func (h *ModelHandler) TestModel(c *gin.Context) {
	modelID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		h.logger.Error("模型ID格式错误", "id", c.Param("id"), "error", err)
		response.BadRequest(c, "模型ID格式错误")
		return
	}

	// 查找模型
	model, err := h.modelService.GetByID(uint(modelID))
	if err != nil {
		h.logger.Error("查找模型失败", "model_id", modelID, "error", err)
		response.NotFound(c, "模型不存在")
		return
	}

	// 测试模型连接
	result, err := h.modelService.TestConnection(model)
	if err != nil {
		h.logger.Error("测试模型连接失败", "model_id", modelID, "error", err)
		response.InternalServerError(c, "测试模型连接失败")
		return
	}

	// 记录操作日志
	userID, _ := c.Get("user_id")
	h.logger.Info("模型连接测试完成", "model_id", modelID, "result", result.Success, "user_id", userID)

	response.Success(c, result)
}

// toModelResponse 转换为模型响应格式
func (h *ModelHandler) toModelResponse(model *models.Model) ModelResponse {
	return ModelResponse{
		ID:          model.ID,
		Name:        model.Name,
		Description: model.Description,
		Type:        model.Type,
		Provider:    model.Provider,
		Version:     model.Version,
		Config:      model.Config,
		Status:      model.Status,
		Tags:        model.Tags,
		CreatedAt:   model.CreatedAt,
		UpdatedAt:   model.UpdatedAt,
		CreatedBy:   model.CreatedBy,
		UpdatedBy:   model.UpdatedBy,
	}
}