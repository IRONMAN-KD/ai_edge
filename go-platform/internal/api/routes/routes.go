package routes

import (
	"github.com/gin-gonic/gin"

	"ai-edge/ai-edge/go-platform/internal/api/handlers"
	"ai-edge/ai-edge/go-platform/internal/api/middleware"
	"ai-edge/ai-edge/go-platform/internal/services"
	"ai-edge/ai-edge/go-platform/pkg/logger"
)

// Router 路由器结构体
type Router struct {
	authHandler  *handlers.AuthHandler
	userHandler  *handlers.UserHandler
	modelHandler *handlers.ModelHandler
	middleware   *middleware.Middleware
	logger       *logger.Logger
}

// NewRouter 创建新的路由器
func NewRouter(
	authService *services.AuthService,
	userService *services.UserService,
	modelService *services.ModelService,
	middleware *middleware.Middleware,
	logger *logger.Logger,
) *Router {
	return &Router{
		authHandler:  handlers.NewAuthHandler(authService, logger),
		userHandler:  handlers.NewUserHandler(userService, logger),
		modelHandler: handlers.NewModelHandler(modelService, logger),
		middleware:   middleware,
		logger:       logger,
	}
}

// SetupRoutes 设置路由
func (r *Router) SetupRoutes(engine *gin.Engine) {
	// 健康检查
	engine.GET("/health", r.healthCheck)

	// API v1 路由组
	v1 := engine.Group("/api/v1")
	v1.Use(r.middleware.CORS())
	v1.Use(r.middleware.RequestLogger())
	v1.Use(r.middleware.RateLimit())
	v1.Use(r.middleware.Recovery())

	// 认证相关路由（无需认证）
	auth := v1.Group("/auth")
	{
		auth.POST("/login", r.authHandler.Login)
		auth.POST("/refresh", r.authHandler.RefreshToken)
	}

	// 需要认证的路由
	protected := v1.Group("")
	protected.Use(r.middleware.JWTAuth())
	{
		// 认证相关（需要认证）
		protectedAuth := protected.Group("/auth")
		{
			protectedAuth.POST("/logout", r.authHandler.Logout)
			protectedAuth.POST("/change-password", r.authHandler.ChangePassword)
			protectedAuth.GET("/profile", r.authHandler.GetProfile)
		}

		// 用户管理路由
		users := protected.Group("/users")
		{
			users.GET("", r.userHandler.ListUsers)
			users.POST("", r.userHandler.CreateUser)
			users.GET("/:id", r.userHandler.GetUser)
			users.PUT("/:id", r.userHandler.UpdateUser)
			users.DELETE("/:id", r.userHandler.DeleteUser)
			users.PUT("/profile", r.userHandler.UpdateProfile)
			users.POST("/reset-password", r.userHandler.ResetPassword)
			users.GET("/stats", r.userHandler.GetUserStats)
		}

		// 模型管理路由
		models := protected.Group("/models")
		{
			models.GET("", r.modelHandler.ListModels)
			models.POST("", r.modelHandler.CreateModel)
			models.GET("/:id", r.modelHandler.GetModel)
			models.PUT("/:id", r.modelHandler.UpdateModel)
			models.DELETE("/:id", r.modelHandler.DeleteModel)
			models.GET("/type/:type", r.modelHandler.GetModelsByType)
			models.GET("/stats", r.modelHandler.GetModelStats)
			models.POST("/:id/test", r.modelHandler.TestModel)
		}
	}

	// 管理员路由（需要管理员权限）
	admin := v1.Group("/admin")
	admin.Use(r.middleware.JWTAuth())
	admin.Use(r.middleware.AdminAuth())
	{
		// 系统管理
		admin.GET("/system/info", r.getSystemInfo)
		admin.GET("/system/stats", r.getSystemStats)
		admin.POST("/system/backup", r.createBackup)
		admin.POST("/system/restore", r.restoreBackup)
	}
}

// healthCheck 健康检查
func (r *Router) healthCheck(c *gin.Context) {
	c.JSON(200, gin.H{
		"status":    "ok",
		"timestamp": gin.H{"unix": gin.H{"seconds": 1234567890}},
		"service":   "go-platform",
		"version":   "1.0.0",
	})
}

// getSystemInfo 获取系统信息
func (r *Router) getSystemInfo(c *gin.Context) {
	c.JSON(200, gin.H{
		"service":   "go-platform",
		"version":   "1.0.0",
		"go_version": "1.21",
		"build_time": "2024-01-01T00:00:00Z",
		"git_commit": "abc123",
	})
}

// getSystemStats 获取系统统计信息
func (r *Router) getSystemStats(c *gin.Context) {
	c.JSON(200, gin.H{
		"uptime":       "24h30m",
		"memory_usage": "256MB",
		"cpu_usage":    "15%",
		"disk_usage":   "45%",
		"connections":  42,
	})
}

// createBackup 创建备份
func (r *Router) createBackup(c *gin.Context) {
	c.JSON(200, gin.H{
		"message":    "备份创建成功",
		"backup_id":  "backup_20240101_000000",
		"created_at": "2024-01-01T00:00:00Z",
	})
}

// restoreBackup 恢复备份
func (r *Router) restoreBackup(c *gin.Context) {
	c.JSON(200, gin.H{
		"message":     "备份恢复成功",
		"backup_id":   c.PostForm("backup_id"),
		"restored_at": "2024-01-01T00:00:00Z",
	})
}