package middleware

import (
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"golang.org/x/time/rate"

	"ai-edge/ai-edge/go-platform/internal/api/handlers"
	"ai-edge/ai-edge/go-platform/internal/services"
	"ai-edge/ai-edge/go-platform/pkg/logger"
	"ai-edge/ai-edge/go-platform/pkg/response"
)

// Middleware 中间件结构体
type Middleware struct {
	authService *services.AuthService
	userService *services.UserService
	logger      *logger.Logger
	limiter     *rate.Limiter
}

// NewMiddleware 创建中间件实例
func NewMiddleware(
	authService *services.AuthService,
	userService *services.UserService,
	logger *logger.Logger,
) *Middleware {
	return &Middleware{
		authService: authService,
		userService: userService,
		logger:      logger,
		limiter:     rate.NewLimiter(rate.Every(time.Second), 100), // 每秒100个请求
	}
}

// CORS 跨域中间件
func (m *Middleware) CORS() gin.HandlerFunc {
	config := cors.DefaultConfig()
	config.AllowOrigins = []string{"*"} // 生产环境应该配置具体的域名
	config.AllowMethods = []string{"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Length", "Content-Type", "Authorization", "X-Requested-With"}
	config.ExposeHeaders = []string{"Content-Length", "X-Total-Count"}
	config.AllowCredentials = true
	config.MaxAge = 12 * time.Hour

	return cors.New(config)
}

// RequestLogger 请求日志中间件
func (m *Middleware) RequestLogger() gin.HandlerFunc {
	return gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
		m.logger.Info("HTTP请求",
			"method", param.Method,
			"path", param.Path,
			"status", param.StatusCode,
			"latency", param.Latency,
			"client_ip", param.ClientIP,
			"user_agent", param.Request.UserAgent(),
			"error", param.ErrorMessage,
		)
		return ""
	})
}

// Recovery 恢复中间件
func (m *Middleware) Recovery() gin.HandlerFunc {
	return gin.CustomRecovery(func(c *gin.Context, recovered interface{}) {
		m.logger.Error("服务器内部错误",
			"error", recovered,
			"method", c.Request.Method,
			"path", c.Request.URL.Path,
			"client_ip", c.ClientIP(),
		)
		response.InternalServerError(c, "服务器内部错误")
	})
}

// RateLimit 限流中间件
func (m *Middleware) RateLimit() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !m.limiter.Allow() {
			m.logger.Warn("请求频率过高",
				"client_ip", c.ClientIP(),
				"path", c.Request.URL.Path,
			)
			response.TooManyRequests(c, "请求频率过高，请稍后再试")
			c.Abort()
			return
		}
		c.Next()
	}
}

// JWTAuth JWT认证中间件
func (m *Middleware) JWTAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从请求头获取token
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			m.logger.Warn("缺少Authorization头", "path", c.Request.URL.Path, "client_ip", c.ClientIP())
			response.Unauthorized(c, "缺少认证信息")
			c.Abort()
			return
		}

		// 检查Bearer前缀
		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			m.logger.Warn("无效的Authorization头格式", "header", authHeader, "client_ip", c.ClientIP())
			response.Unauthorized(c, "无效的认证格式")
			c.Abort()
			return
		}

		token := parts[1]

		// 验证token
		claims, err := handlers.ValidateToken(token)
		if err != nil {
			m.logger.Warn("Token验证失败", "error", err, "client_ip", c.ClientIP())
			response.Unauthorized(c, "无效的认证信息")
			c.Abort()
			return
		}

		// 检查用户是否存在且活跃
		user, err := m.userService.GetByID(claims.UserID)
		if err != nil {
			m.logger.Warn("用户不存在", "user_id", claims.UserID, "client_ip", c.ClientIP())
			response.Unauthorized(c, "用户不存在")
			c.Abort()
			return
		}

		if user.Status != "active" {
			m.logger.Warn("用户账户已被禁用", "user_id", claims.UserID, "status", user.Status)
			response.Forbidden(c, "账户已被禁用")
			c.Abort()
			return
		}

		// 将用户信息存储到上下文
		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Set("role", claims.Role)
		c.Set("user", user)

		c.Next()
	}
}

// AdminAuth 管理员权限中间件
func (m *Middleware) AdminAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		role, exists := c.Get("role")
		if !exists {
			m.logger.Error("无法获取用户角色信息")
			response.InternalServerError(c, "认证信息错误")
			c.Abort()
			return
		}

		if role != "admin" && role != "super_admin" {
			userID, _ := c.Get("user_id")
			m.logger.Warn("用户尝试访问管理员功能",
				"user_id", userID,
				"role", role,
				"path", c.Request.URL.Path,
			)
			response.Forbidden(c, "权限不足")
			c.Abort()
			return
		}

		c.Next()
	}
}

// SuperAdminAuth 超级管理员权限中间件
func (m *Middleware) SuperAdminAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		role, exists := c.Get("role")
		if !exists {
			m.logger.Error("无法获取用户角色信息")
			response.InternalServerError(c, "认证信息错误")
			c.Abort()
			return
		}

		if role != "super_admin" {
			userID, _ := c.Get("user_id")
			m.logger.Warn("用户尝试访问超级管理员功能",
				"user_id", userID,
				"role", role,
				"path", c.Request.URL.Path,
			)
			response.Forbidden(c, "权限不足")
			c.Abort()
			return
		}

		c.Next()
	}
}

// OwnerOrAdminAuth 资源所有者或管理员权限中间件
func (m *Middleware) OwnerOrAdminAuth(resourceUserIDParam string) gin.HandlerFunc {
	return func(c *gin.Context) {
		currentUserID, exists := c.Get("user_id")
		if !exists {
			response.Unauthorized(c, "未认证的用户")
			c.Abort()
			return
		}

		currentRole, _ := c.Get("role")

		// 管理员可以访问所有资源
		if currentRole == "admin" || currentRole == "super_admin" {
			c.Next()
			return
		}

		// 检查是否为资源所有者
		resourceUserIDStr := c.Param(resourceUserIDParam)
		if resourceUserIDStr == "" {
			response.BadRequest(c, "缺少用户ID参数")
			c.Abort()
			return
		}

		resourceUserID, err := strconv.ParseUint(resourceUserIDStr, 10, 32)
		if err != nil {
			response.BadRequest(c, "无效的用户ID")
			c.Abort()
			return
		}

		if uint(resourceUserID) != currentUserID.(uint) {
			m.logger.Warn("用户尝试访问其他用户的资源",
				"current_user_id", currentUserID,
				"resource_user_id", resourceUserID,
				"path", c.Request.URL.Path,
			)
			response.Forbidden(c, "权限不足")
			c.Abort()
			return
		}

		c.Next()
	}
}

// ContentType 内容类型验证中间件
func (m *Middleware) ContentType(contentType string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if c.Request.Method == http.MethodPost || c.Request.Method == http.MethodPut || c.Request.Method == http.MethodPatch {
			if c.GetHeader("Content-Type") != contentType {
				m.logger.Warn("无效的Content-Type",
					"expected", contentType,
					"actual", c.GetHeader("Content-Type"),
					"path", c.Request.URL.Path,
				)
				response.BadRequest(c, "无效的Content-Type")
				c.Abort()
				return
			}
		}
		c.Next()
	}
}

// SecurityHeaders 安全头中间件
func (m *Middleware) SecurityHeaders() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("X-Frame-Options", "DENY")
		c.Header("X-XSS-Protection", "1; mode=block")
		c.Header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		c.Header("Content-Security-Policy", "default-src 'self'")
		c.Header("Referrer-Policy", "strict-origin-when-cross-origin")
		c.Next()
	}
}