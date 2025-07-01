package handlers

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"

	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/services"
	"ai-edge/ai-edge/ai-edge/go-platform/pkg/errors"
	"ai-edge/ai-edge/ai-edge/go-platform/pkg/logger"
	"ai-edge/ai-edge/ai-edge/go-platform/pkg/response"
	"ai-edge/ai-edge/ai-edge/go-platform/pkg/validator"
)

// AuthHandler 认证处理器
type AuthHandler struct {
	userService *services.UserService
	jwtSecret   string
	logger      *logger.Logger
}

// NewAuthHandler 创建认证处理器
func NewAuthHandler(userService *services.UserService, jwtSecret string, logger *logger.Logger) *AuthHandler {
	return &AuthHandler{
		userService: userService,
		jwtSecret:   jwtSecret,
		logger:      logger,
	}
}

// LoginRequest 登录请求
type LoginRequest struct {
	Username string `json:"username" validate:"required,min=3,max=50" label:"用户名"`
	Password string `json:"password" validate:"required,min=6,max=100" label:"密码"`
}

// LoginResponse 登录响应
type LoginResponse struct {
	Token        string    `json:"token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
	User         UserInfo  `json:"user"`
}

// UserInfo 用户信息
type UserInfo struct {
	ID       uint   `json:"id"`
	Username string `json:"username"`
	Email    string `json:"email"`
	Role     string `json:"role"`
	Status   string `json:"status"`
}

// RefreshTokenRequest 刷新令牌请求
type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required" label:"刷新令牌"`
}

// ChangePasswordRequest 修改密码请求
type ChangePasswordRequest struct {
	OldPassword string `json:"old_password" validate:"required,min=6,max=100" label:"旧密码"`
	NewPassword string `json:"new_password" validate:"required,min=6,max=100,password" label:"新密码"`
}

// JWTClaims JWT声明
type JWTClaims struct {
	UserID   uint   `json:"user_id"`
	Username string `json:"username"`
	Role     string `json:"role"`
	jwt.RegisteredClaims
}

// Login 用户登录
func (h *AuthHandler) Login(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定登录请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("登录请求验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 查找用户
	user, err := h.userService.GetByUsername(req.Username)
	if err != nil {
		h.logger.Error("查找用户失败", "username", req.Username, "error", err)
		response.Unauthorized(c, "用户名或密码错误")
		return
	}

	// 验证密码
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password)); err != nil {
		h.logger.Error("密码验证失败", "username", req.Username, "error", err)
		response.Unauthorized(c, "用户名或密码错误")
		return
	}

	// 检查用户状态
	if user.Status != "active" {
		h.logger.Warn("用户状态异常", "username", req.Username, "status", user.Status)
		response.Forbidden(c, "用户账户已被禁用")
		return
	}

	// 生成JWT令牌
	token, refreshToken, expiresAt, err := h.generateTokens(user)
	if err != nil {
		h.logger.Error("生成令牌失败", "user_id", user.ID, "error", err)
		response.InternalServerError(c, "生成令牌失败")
		return
	}

	// 更新用户最后登录时间
	now := time.Now()
	user.LastLoginAt = &now
	if err := h.userService.Update(user); err != nil {
		h.logger.Error("更新用户登录时间失败", "user_id", user.ID, "error", err)
		// 不影响登录流程，只记录错误
	}

	// 记录登录日志
	h.logger.Info("用户登录成功", "user_id", user.ID, "username", user.Username, "ip", c.ClientIP())

	// 返回登录响应
	response.Success(c, LoginResponse{
		Token:        token,
		RefreshToken: refreshToken,
		ExpiresAt:    expiresAt,
		User: UserInfo{
			ID:       user.ID,
			Username: user.Username,
			Email:    user.Email,
			Role:     user.Role,
			Status:   user.Status,
		},
	})
}

// RefreshToken 刷新令牌
func (h *AuthHandler) RefreshToken(c *gin.Context) {
	var req RefreshTokenRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定刷新令牌请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("刷新令牌请求验证失败", "error", err)
		response.ValidationError(c, err)
		return
	}

	// 解析刷新令牌
	claims, err := h.parseToken(req.RefreshToken)
	if err != nil {
		h.logger.Error("解析刷新令牌失败", "error", err)
		response.Unauthorized(c, "无效的刷新令牌")
		return
	}

	// 查找用户
	user, err := h.userService.GetByID(claims.UserID)
	if err != nil {
		h.logger.Error("查找用户失败", "user_id", claims.UserID, "error", err)
		response.Unauthorized(c, "用户不存在")
		return
	}

	// 检查用户状态
	if user.Status != "active" {
		h.logger.Warn("用户状态异常", "user_id", user.ID, "status", user.Status)
		response.Forbidden(c, "用户账户已被禁用")
		return
	}

	// 生成新的令牌
	token, refreshToken, expiresAt, err := h.generateTokens(user)
	if err != nil {
		h.logger.Error("生成新令牌失败", "user_id", user.ID, "error", err)
		response.InternalServerError(c, "生成令牌失败")
		return
	}

	// 记录刷新令牌日志
	h.logger.Info("令牌刷新成功", "user_id", user.ID, "username", user.Username, "ip", c.ClientIP())

	// 返回新令牌
	response.Success(c, LoginResponse{
		Token:        token,
		RefreshToken: refreshToken,
		ExpiresAt:    expiresAt,
		User: UserInfo{
			ID:       user.ID,
			Username: user.Username,
			Email:    user.Email,
			Role:     user.Role,
			Status:   user.Status,
		},
	})
}

// Logout 用户登出
func (h *AuthHandler) Logout(c *gin.Context) {
	// 从上下文获取用户信息
	userID, exists := c.Get("user_id")
	if !exists {
		response.Unauthorized(c, "未认证的用户")
		return
	}

	username, _ := c.Get("username")

	// 记录登出日志
	h.logger.Info("用户登出", "user_id", userID, "username", username, "ip", c.ClientIP())

	// TODO: 将令牌加入黑名单（可选实现）

	response.Success(c, gin.H{"message": "登出成功"})
}

// ChangePassword 修改密码
func (h *AuthHandler) ChangePassword(c *gin.Context) {
	var req ChangePasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.Error("绑定修改密码请求失败", "error", err)
		response.BadRequest(c, "请求参数格式错误")
		return
	}

	// 验证请求参数
	if err := validator.Validate(&req); err != nil {
		h.logger.Error("修改密码请求验证失败", "error", err)
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

	// 验证旧密码
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.OldPassword)); err != nil {
		h.logger.Error("旧密码验证失败", "user_id", userID, "error", err)
		response.BadRequest(c, "旧密码错误")
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
		h.logger.Error("更新密码失败", "user_id", userID, "error", err)
		response.InternalServerError(c, "更新密码失败")
		return
	}

	// 记录密码修改日志
	h.logger.Info("用户修改密码成功", "user_id", userID, "username", user.Username, "ip", c.ClientIP())

	response.Success(c, gin.H{"message": "密码修改成功"})
}

// GetProfile 获取用户资料
func (h *AuthHandler) GetProfile(c *gin.Context) {
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

	// 返回用户信息
	response.Success(c, UserInfo{
		ID:       user.ID,
		Username: user.Username,
		Email:    user.Email,
		Role:     user.Role,
		Status:   user.Status,
	})
}

// generateTokens 生成访问令牌和刷新令牌
func (h *AuthHandler) generateTokens(user *models.User) (string, string, time.Time, error) {
	now := time.Now()
	expiresAt := now.Add(24 * time.Hour) // 访问令牌24小时有效
	refreshExpiresAt := now.Add(7 * 24 * time.Hour) // 刷新令牌7天有效

	// 生成访问令牌
	accessClaims := JWTClaims{
		UserID:   user.ID,
		Username: user.Username,
		Role:     user.Role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expiresAt),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "ai-edge-platform",
			Subject:   strconv.Itoa(int(user.ID)),
		},
	}

	accessToken := jwt.NewWithClaims(jwt.SigningMethodHS256, accessClaims)
	accessTokenString, err := accessToken.SignedString([]byte(h.jwtSecret))
	if err != nil {
		return "", "", time.Time{}, errors.Wrap(err, errors.ErrCodeAuthTokenGeneration, "生成访问令牌失败")
	}

	// 生成刷新令牌
	refreshClaims := JWTClaims{
		UserID:   user.ID,
		Username: user.Username,
		Role:     user.Role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(refreshExpiresAt),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "ai-edge-platform",
			Subject:   strconv.Itoa(int(user.ID)),
		},
	}

	refreshToken := jwt.NewWithClaims(jwt.SigningMethodHS256, refreshClaims)
	refreshTokenString, err := refreshToken.SignedString([]byte(h.jwtSecret))
	if err != nil {
		return "", "", time.Time{}, errors.Wrap(err, errors.ErrCodeAuthTokenGeneration, "生成刷新令牌失败")
	}

	return accessTokenString, refreshTokenString, expiresAt, nil
}

// parseToken 解析JWT令牌
func (h *AuthHandler) parseToken(tokenString string) (*JWTClaims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New(errors.ErrCodeAuthInvalidToken, "无效的签名方法")
		}
		return []byte(h.jwtSecret), nil
	})

	if err != nil {
		return nil, errors.Wrap(err, errors.ErrCodeAuthInvalidToken, "解析令牌失败")
	}

	if claims, ok := token.Claims.(*JWTClaims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New(errors.ErrCodeAuthInvalidToken, "无效的令牌")
}

// ValidateToken 验证JWT令牌（中间件使用）
func (h *AuthHandler) ValidateToken(tokenString string) (*JWTClaims, error) {
	return h.parseToken(tokenString)
}