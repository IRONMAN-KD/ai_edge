package api

import (
	"ai-edge/ai-edge/ai-edge/go-platform/internal/api/handlers"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/api/middleware"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/services"

	"github.com/gin-gonic/gin"
)

// SetupRoutes 设置路由
func SetupRoutes(services *services.Services) *gin.Engine {
	router := gin.New()

	// 中间件
	router.Use(gin.Logger())
	router.Use(gin.Recovery())
	router.Use(middleware.CORS())

	// 创建处理器
	authHandler := handlers.NewAuthHandler(services.Auth)
	userHandler := handlers.NewUserHandler(services.User)
	modelHandler := handlers.NewModelHandler(services.Model)
	taskHandler := handlers.NewTaskHandler(services.Task)
	inferenceHandler := handlers.NewInferenceHandler(services.Inference)
	alertHandler := handlers.NewAlertHandler(services.Alert)

	// 健康检查
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	})

	// API v1 路由组
	v1 := router.Group("/api/v1")
	{
		// 认证相关路由（无需认证）
		auth := v1.Group("/auth")
		{
			auth.POST("/login", authHandler.Login)
			auth.POST("/refresh", authHandler.RefreshToken)
		}

		// 需要认证的路由
		protected := v1.Group("")
		protected.Use(middleware.AuthMiddleware(services.Auth))
		{
			// 用户管理
			users := protected.Group("/users")
			{
				users.GET("", userHandler.List)
				users.POST("", userHandler.Create)
				users.GET("/:id", userHandler.GetByID)
				users.PUT("/:id", userHandler.Update)
				users.DELETE("/:id", userHandler.Delete)
				users.POST("/:id/change-password", userHandler.ChangePassword)
			}

			// 模型管理
			models := protected.Group("/models")
			{
				models.GET("", modelHandler.List)
				models.POST("", modelHandler.Create)
				models.GET("/:id", modelHandler.GetByID)
				models.PUT("/:id", modelHandler.Update)
				models.DELETE("/:id", modelHandler.Delete)
				models.POST("/:id/activate", modelHandler.Activate)
				models.POST("/:id/deactivate", modelHandler.Deactivate)
				models.GET("/active", modelHandler.GetActive)
			}

			// 任务管理
			tasks := protected.Group("/tasks")
			{
				tasks.GET("", taskHandler.List)
				tasks.POST("", taskHandler.Create)
				tasks.GET("/:id", taskHandler.GetByID)
				tasks.PUT("/:id", taskHandler.Update)
				tasks.DELETE("/:id", taskHandler.Delete)
				tasks.POST("/:id/start", taskHandler.Start)
				tasks.POST("/:id/stop", taskHandler.Stop)
				tasks.POST("/:id/pause", taskHandler.Pause)
				tasks.POST("/:id/resume", taskHandler.Resume)
			}

			// 推理记录
			inferences := protected.Group("/inferences")
			{
				inferences.GET("", inferenceHandler.List)
				inferences.GET("/:id", inferenceHandler.GetByID)
				inferences.DELETE("/:id", inferenceHandler.Delete)
				inferences.GET("/statistics", inferenceHandler.GetStatistics)
			}

			// 告警管理
			alerts := protected.Group("/alerts")
			{
				alerts.GET("", alertHandler.List)
				alerts.GET("/:id", alertHandler.GetByID)
				alerts.PUT("/:id", alertHandler.Update)
				alerts.DELETE("/:id", alertHandler.Delete)
				alerts.POST("/:id/read", alertHandler.MarkAsRead)
				alerts.POST("/:id/resolve", alertHandler.MarkAsResolved)
				alerts.GET("/unread-count", alertHandler.GetUnreadCount)
				alerts.GET("/statistics", alertHandler.GetStatistics)
			}
		}
	}

	return router
}