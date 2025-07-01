package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"

	"ai-edge/ai-edge/go-platform/internal/api/middleware"
	"ai-edge/ai-edge/go-platform/internal/api/routes"
	"ai-edge/ai-edge/go-platform/internal/config"
	"ai-edge/ai-edge/go-platform/internal/models"
	"ai-edge/ai-edge/go-platform/internal/repositories"
	"ai-edge/ai-edge/go-platform/internal/services"
	"ai-edge/ai-edge/go-platform/pkg/database"
	"ai-edge/ai-edge/go-platform/pkg/logger"
	"ai-edge/ai-edge/go-platform/pkg/validator"
)

// Application 应用程序结构体
type Application struct {
	config       *config.Config
	logger       *logger.Logger
	database     *database.Database
	server       *http.Server
	userRepo     repositories.UserRepository
	modelRepo    repositories.ModelRepository
	authService  *services.AuthService
	userService  *services.UserService
	modelService *services.ModelService
	middleware   *middleware.Middleware
	router       *routes.Router
}

// NewApplication 创建新的应用程序实例
func NewApplication() (*Application, error) {
	// 加载配置
	cfg, err := config.Load()
	if err != nil {
		return nil, fmt.Errorf("加载配置失败: %w", err)
	}

	// 初始化日志器
	logger, err := logger.New(cfg.Logger)
	if err != nil {
		return nil, fmt.Errorf("初始化日志器失败: %w", err)
	}

	// 初始化数据库
	db, err := database.New(cfg.Database)
	if err != nil {
		return nil, fmt.Errorf("初始化数据库失败: %w", err)
	}

	// 自动迁移数据库
	if err := db.AutoMigrate(
		&models.User{},
		&models.Model{},
	); err != nil {
		return nil, fmt.Errorf("数据库迁移失败: %w", err)
	}

	// 初始化仓库
	userRepo := repositories.NewUserRepository(db)
	modelRepo := repositories.NewModelRepository(db)

	// 初始化服务
	authService := services.NewAuthService(userRepo, cfg.JWT, logger)
	userService := services.NewUserService(userRepo, logger)
	modelService := services.NewModelService(modelRepo, logger)

	// 初始化中间件
	middleware := middleware.NewMiddleware(authService, userService, logger)

	// 初始化路由
	router := routes.NewRouter(authService, userService, modelService, middleware, logger)

	app := &Application{
		config:       cfg,
		logger:       logger,
		database:     db,
		userRepo:     userRepo,
		modelRepo:    modelRepo,
		authService:  authService,
		userService:  userService,
		modelService: modelService,
		middleware:   middleware,
		router:       router,
	}

	return app, nil
}

// Start 启动应用程序
func (app *Application) Start() error {
	// 设置Gin模式
	if app.config.Server.Mode == "release" {
		gin.SetMode(gin.ReleaseMode)
	} else {
		gin.SetMode(gin.DebugMode)
	}

	// 创建Gin引擎
	engine := gin.New()

	// 设置路由
	app.router.SetupRoutes(engine)

	// 创建HTTP服务器
	app.server = &http.Server{
		Addr:           fmt.Sprintf(":%d", app.config.Server.Port),
		Handler:        engine,
		ReadTimeout:    time.Duration(app.config.Server.ReadTimeout) * time.Second,
		WriteTimeout:   time.Duration(app.config.Server.WriteTimeout) * time.Second,
		IdleTimeout:    time.Duration(app.config.Server.IdleTimeout) * time.Second,
		MaxHeaderBytes: app.config.Server.MaxHeaderBytes,
	}

	// 启动服务器
	app.logger.Info("启动HTTP服务器",
		"port", app.config.Server.Port,
		"mode", app.config.Server.Mode,
		"version", "1.0.0",
	)

	go func() {
		if err := app.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			app.logger.Error("HTTP服务器启动失败", "error", err)
			os.Exit(1)
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	app.logger.Info("正在关闭服务器...")

	// 优雅关闭
	return app.Shutdown()
}

// Shutdown 优雅关闭应用程序
func (app *Application) Shutdown() error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 关闭HTTP服务器
	if err := app.server.Shutdown(ctx); err != nil {
		app.logger.Error("HTTP服务器关闭失败", "error", err)
		return err
	}

	// 关闭数据库连接
	if err := app.database.Close(); err != nil {
		app.logger.Error("数据库连接关闭失败", "error", err)
		return err
	}

	app.logger.Info("服务器已优雅关闭")
	return nil
}

// Health 健康检查
func (app *Application) Health() error {
	// 检查数据库连接
	if err := app.database.Health(); err != nil {
		return fmt.Errorf("数据库健康检查失败: %w", err)
	}

	return nil
}

// CreateDefaultAdmin 创建默认管理员用户
func (app *Application) CreateDefaultAdmin() error {
	// 检查是否已存在管理员用户
	adminUser, err := app.userService.GetByUsername("admin")
	if err == nil && adminUser != nil {
		app.logger.Info("默认管理员用户已存在")
		return nil
	}

	// 创建默认管理员用户
	user := &models.User{
		Username: "admin",
		Email:    "admin@example.com",
		Password: "admin123", // 默认密码，生产环境应该修改
		Role:     "super_admin",
		Status:   "active",
	}

	if err := app.userService.Create(user); err != nil {
		return fmt.Errorf("创建默认管理员用户失败: %w", err)
	}

	app.logger.Info("默认管理员用户创建成功",
		"username", user.Username,
		"email", user.Email,
		"user_id", user.ID,
	)

	return nil
}

func main() {
	// 初始化验证器
	if err := validator.Init(); err != nil {
		log.Fatalf("初始化验证器失败: %v", err)
	}

	// 创建应用程序实例
	app, err := NewApplication()
	if err != nil {
		log.Fatalf("创建应用程序失败: %v", err)
	}

	// 健康检查
	if err := app.Health(); err != nil {
		log.Fatalf("应用程序健康检查失败: %v", err)
	}

	// 创建默认管理员用户
	if err := app.CreateDefaultAdmin(); err != nil {
		app.logger.Error("创建默认管理员用户失败", "error", err)
		// 不退出程序，只记录错误
	}

	// 启动应用程序
	if err := app.Start(); err != nil {
		log.Fatalf("启动应用程序失败: %v", err)
	}
}