package handlers

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"

	"ai-edge/ai-edge/go-platform/internal/models"
	"ai-edge/ai-edge/go-platform/internal/services"
	"ai-edge/ai-edge/go-platform/pkg/errors"
	"ai-edge/ai-edge/go-platform/pkg/logger"
	"ai-edge/ai-edge/go-platform/pkg/response"
	"ai-edge/ai-edge/go-platform/pkg/validator"
)

// UserHandler 用户处理器
type UserHandler struct {
	userService *services.UserService
	logger      *logger.Logger
}

// NewUserHandler 创建用户处理器
func NewUserHandler(userService *services.UserService, logger *logger.Logger) *UserHandler {
	return &UserHandler{
		userService: userService,
		logger:      logger,
	}
}

// CreateUserRequest 创建用户请求
type CreateUserRequest struct {
	Username string `json:"username" validate:"required,min=3,max=50,username" label:"用户名"`
	Email    string `json:"email" validate:"required,email,max=100" label:"邮箱"`
	Password string `json:"password" validate:"required,min=6,max=100,password" label:"密码"`
	Role     string `json:"role" validate:"required,oneof=admin user viewer" label:"角色"`
	Status   string `json:"status" validate:"omitempty,oneof=active inactive" label:"状态"`
}

// UpdateUserRequest 更新用户请求
type UpdateUserRequest struct {
	Email  string `json:"email" validate:"omitempty,email,max=100" label:"邮箱"`
	Role   string `json:"role" validate:"omitempty,oneof=admin user viewer" label:"角色"`
	Status string `json:"status" validate:"omitempty,oneof=active inactive" label:"状态"`
}

// UpdateProfileRequest 更新个人资料请求
type UpdateProfileRequest struct {
	Email string `json:"email" validate:"omitempty,email,max=100" label:"邮箱"`
}

// UserResponse 用户响应
type UserResponse struct {
	ID          uint       `json:"id"`
	Username    string     `json:"username"`
	Email       string     `json:"email"`
	Role        string     `json:"role"`
	Status      string     `json:"status"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
	LastLoginAt *time.Time `json:"last_login_at"`
}

// UserListQuery 用户列表查询参数
type UserListQuery struct {
	Page     int    `form:"page" validate:"omitempty,min=1" label:"页码"`
	PageSize int    `form:"page_size" validate:"omitempty,min=1,max=100" label:"每页数量"`
	Role     string `form:"role" validate:"omitempty,oneof=admin user viewer" label:"角色"`
	Status   string `form:"status" validate:"omitempty,oneof=active inactive" label:"状态"`
	Keyword  string `form:"keyword" validate:"omitempty,max=50" label:"关键词"`
	SortBy   string `form:"sort_by" validate:"omitempty,oneof=id username email created_at updated_at last_login_at" label:"排序字段"`
	SortDesc bool   `form:"sort_desc" label:"降序排列"`
}

// CreateUser 创建用户
func (h *UserHandler) CreateUser(c *gin.Context) {
	var req CreateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定创建用户请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("创建用户请求验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 检查用户名是否已存在
	if _, err := h.userService.GetByUsername(req.Username); err == nil {
		h.logger.Warn("用户名已存在", "username", req.Username)
		response.Conflict(c, "用户名已存在")
		return
	}

	// 检查邮箱是否已存在
	if _, err := h.userService.GetByEmail(req.Email); err == nil {
		h.logger.Warn("邮箱已存在", "email", req.Email)
		response.Conflict(c, "邮箱已存在")
		return
	}

	// 加密密码
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		h.logger.Error("密码加密失败", "error", err)
		response.InternalServerError(c, "密码加密失败")
		return
	}

	// 设置默认状态
	status := req.Status
	if status == "" {
		status = "active"
	}

	// 创建用户
	user := &models.User{
		Username: req.Username,
		Email:    req.Email,
		Password: string(hashedPassword),
		Role:     req.Role,
		Status:   status,
	}

	if err := h.userService.Create(user); err != nil {
		h.logger.Error("创建用户失败", "username", req.Username, "error", err)
		response.InternalServerError(c, "创建用户失败")
		return
	}

	// 记录操作日志
	operatorID, _ := c.Get("user_id")
	h.logger.Info("用户创建成功", "user_id", user.ID, "username", user.Username, "operator_id", operatorID)

	// 返回用户信息（不包含密码）
	response.Created(c, h.toUserResponse(user))
}

// GetUser 获取用户详情
func (h *UserHandler) GetUser(c *gin.Context) {
	userID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		h.logger.Error("用户ID格式错误", "id", c.Param("id"), "error", err)
		response.BadRequest(c, "用户ID格式错误")
		return
	}

	user, err := h.userService.GetByID(uint(userID))
	if err != nil {
		h.logger.Error("查找用户失败", "user_id", userID, "error", err)
		response.NotFound(c, "用户不存在")
		return
	}

	response.Success(c, h.toUserResponse(user))
}

// UpdateUser 更新用户
func (h *UserHandler) UpdateUser(c *gin.Context) {
	userID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		h.logger.Error("用户ID格式错误", "id", c.Param("id"), "error", err)
		response.BadRequest(c, "用户ID格式错误")
		return
	}

	var req UpdateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定更新用户请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("更新用户请求验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 查找用户
	user, err := h.userService.GetByID(uint(userID))
	if err != nil {
		h.logger.Error("查找用户失败", "user_id", userID, "error", err)
		response.NotFound(c, "用户不存在")
		return
	}

	// 检查邮箱是否已被其他用户使用
	if req.Email != "" && req.Email != user.Email {
		if existingUser, err := h.userService.GetByEmail(req.Email); err == nil && existingUser.ID != user.ID {
			h.logger.Warn("邮箱已被其他用户使用", "email", req.Email, "existing_user_id", existingUser.ID)
			response.Conflict(c, "邮箱已被其他用户使用")
			return
		}
	}

	// 更新用户信息
	if req.Email != "" {
		user.Email = req.Email
	}
	if req.Role != "" {
		user.Role = req.Role
	}
	if req.Status != "" {
		user.Status = req.Status
	}

	if err := h.userService.Update(user); err != nil {
		h.logger.Error("更新用户失败", "user_id", userID, "error", err)
		response.InternalServerError(c, "更新用户失败")
		return
	}

	// 记录操作日志
	operatorID, _ := c.Get("user_id")
	h.logger.Info("用户更新成功", "user_id", userID, "operator_id", operatorID)

	response.Success(c, h.toUserResponse(user))
}

// DeleteUser 删除用户
func (h *UserHandler) DeleteUser(c *gin.Context) {
	userID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		h.logger.Error("用户ID格式错误", "id", c.Param("id"), "error", err)
		response.BadRequest(c, "用户ID格式错误")
		return
	}

	// 检查是否为当前用户
	currentUserID, _ := c.Get("user_id")
	if currentUserID == uint(userID) {
		h.logger.Warn("尝试删除自己的账户", "user_id", userID)
		response.BadRequest(c, "不能删除自己的账户")
		return
	}

	// 查找用户
	user, err := h.userService.GetByID(uint(userID))
	if err != nil {
		h.logger.Error("查找用户失败", "user_id", userID, "error", err)
		response.NotFound(c, "用户不存在")
		return
	}

	// 删除用户
	if err := h.userService.Delete(uint(userID)); err != nil {
		h.logger.Error("删除用户失败", "user_id", userID, "error", err)
		response.InternalServerError(c, "删除用户失败")
		return
	}

	// 记录操作日志
	operatorID, _ := c.Get("user_id")
	h.logger.Info("用户删除成功", "user_id", userID, "username", user.Username, "operator_id", operatorID)

	response.NoContent(c)
}

// ListUsers 获取用户列表
func (h *UserHandler) ListUsers(c *gin.Context) {
	var query UserListQuery
	if err := c.ShouldBindQuery(&query); err != nil {
		h.logger.Error("绑定用户列表查询参数失败", "error", err)
		response.BadRequest(c, "查询参数格式错误")
		return
	}

	// 验证查询参数
	if err := validator.Validate(&query); err != nil {
		h.logger.Error("用户列表查询参数验证失败", "error", err)
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
	if query.Role != "" {
		filters["role"] = query.Role
	}
	if query.Status != "" {
		filters["status"] = query.Status
	}

	// 获取用户列表
	users, total, err := h.userService.List(query.Page, query.PageSize, filters, query.Keyword, query.SortBy, query.SortDesc)
	if err != nil {
		h.logger.Error("获取用户列表失败", "error", err)
		response.InternalServerError(c, "获取用户列表失败")
		return
	}

	// 转换为响应格式
	userResponses := make([]UserResponse, len(users))
	for i, user := range users {
		userResponses[i] = h.toUserResponse(&user)
	}

	// 返回分页结果
	response.Paginated(c, userResponses, total, query.Page, query.PageSize)
}

// UpdateProfile 更新个人资料
func (h *UserHandler) UpdateProfile(c *gin.Context) {
	var req UpdateProfileRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定更新个人资料请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("更新个人资料请求验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 从上下文获取用户ID
	userID, exists := c.Get("user_id")
	if !exists {
		response.Unauthorized(c, "未认证的用户")
		return
	}

	// 查找用户
	user, err := h.userService.GetByID(userID.(uint))
	if err != nil {
		h.logger.Error("查找用户失败", "user_id", userID, "error", err)
		response.NotFound(c, "用户不存在")
		return
	}

	// 检查邮箱是否已被其他用户使用
	if req.Email != "" && req.Email != user.Email {
		if existingUser, err := h.userService.GetByEmail(req.Email); err == nil && existingUser.ID != user.ID {
			h.logger.Warn("邮箱已被其他用户使用", "email", req.Email, "existing_user_id", existingUser.ID)
			response.Conflict(c, "邮箱已被其他用户使用")
			return
		}
	}

	// 更新用户信息
	if req.Email != "" {
		user.Email = req.Email
	}

	if err := h.userService.Update(user); err != nil {
		h.logger.Error("更新个人资料失败", "user_id", userID, "error", err)
		response.InternalServerError(c, "更新个人资料失败")
		return
	}

	// 记录操作日志
	h.logger.Info("个人资料更新成功", "user_id", userID)

	response.Success(c, h.toUserResponse(user))
}

// ResetPassword 重置用户密码（管理员功能）
func (h *UserHandler) ResetPassword(c *gin.Context) {
	userID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		h.logger.Error("用户ID格式错误", "id", c.Param("id"), "error", err)
		response.BadRequest(c, "用户ID格式错误")
		return
	}

	type ResetPasswordRequest struct {
		NewPassword string `json:"new_password" validate:"required,min=6,max=100,password" label:"新密码"`
	}

	var req ResetPasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定重置密码请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("重置密码请求验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 查找用户
	user, err := h.userService.GetByID(uint(userID))
	if err != nil {
		h.logger.Error("查找用户失败", "user_id", userID, "error", err)
		response.NotFound(c, "用户不存在")
		return
	}

	// 加密新密码
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.NewPassword), bcrypt.DefaultCost)
	if err != nil {
		h.logger.Error("加密新密码失败", "user_id", userID, "error", err)
		response.InternalServerError(c, "密码加密失败")
		return
	}

	// 更新密码
	user.Password = string(hashedPassword)
	if err := h.userService.Update(user); err != nil {
		h.logger.Error("重置密码失败", "user_id", userID, "error", err)
		response.InternalServerError(c, "重置密码失败")
		return
	}

	// 记录操作日志
	operatorID, _ := c.Get("user_id")
	h.logger.Info("用户密码重置成功", "user_id", userID, "username", user.Username, "operator_id", operatorID)

	response.Success(c, gin.H{"message": "密码重置成功"})
}

// GetUserStats 获取用户统计信息
func (h *UserHandler) GetUserStats(c *gin.Context) {
	stats, err := h.userService.GetStats()
	if err != nil {
		h.logger.Error("获取用户统计信息失败", "error", err)
		response.InternalServerError(c, "获取用户统计信息失败")
		return
	}

	response.Success(c, stats)
}

// toUserResponse 转换为用户响应格式
func (h *UserHandler) toUserResponse(user *models.User) UserResponse {
	return UserResponse{
		ID:          user.ID,
		Username:    user.Username,
		Email:       user.Email,
		Role:        user.Role,
		Status:      user.Status,
		CreatedAt:   user.CreatedAt,
		UpdatedAt:   user.UpdatedAt,
		LastLoginAt: user.LastLoginAt,
	}
}