package handlers

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"ai-edge/internal/services"
	"ai-edge/pkg/response"
)

// HealthHandler 健康检查处理器
type HealthHandler struct {
	services *services.Services
	logger   *zap.Logger
}

// NewHealthHandler 创建健康检查处理器
func NewHealthHandler(services *services.Services, logger *zap.Logger) *HealthHandler {
	return &HealthHandler{
		services: services,
		logger:   logger,
	}
}

// HealthStatus 健康状态
type HealthStatus struct {
	Status      string                 `json:"status"`
	Timestamp   time.Time              `json:"timestamp"`
	Version     string                 `json:"version,omitempty"`
	Uptime      string                 `json:"uptime,omitempty"`
	Checks      map[string]CheckResult `json:"checks,omitempty"`
	Message     string                 `json:"message,omitempty"`
}

// CheckResult 检查结果
type CheckResult struct {
	Status    string        `json:"status"`
	Message   string        `json:"message,omitempty"`
	Duration  time.Duration `json:"duration,omitempty"`
	Timestamp time.Time     `json:"timestamp"`
	Error     string        `json:"error,omitempty"`
}

// DependencyStatus 依赖状态
type DependencyStatus struct {
	Name      string        `json:"name"`
	Status    string        `json:"status"`
	Message   string        `json:"message,omitempty"`
	Duration  time.Duration `json:"duration,omitempty"`
	Timestamp time.Time     `json:"timestamp"`
	Error     string        `json:"error,omitempty"`
}

var startTime = time.Now()

// Check 基本健康检查
func (h *HealthHandler) Check(c *gin.Context) {
	status := &HealthStatus{
		Status:    "healthy",
		Timestamp: time.Now(),
		Uptime:    time.Since(startTime).String(),
		Message:   "Service is running",
	}

	response.Success(c, status)
}

// Liveness 存活检查
func (h *HealthHandler) Liveness(c *gin.Context) {
	// 简单的存活检查，只要服务能响应就认为是存活的
	status := &HealthStatus{
		Status:    "alive",
		Timestamp: time.Now(),
		Uptime:    time.Since(startTime).String(),
		Message:   "Service is alive",
	}

	response.Success(c, status)
}

// Readiness 就绪检查
func (h *HealthHandler) Readiness(c *gin.Context) {
	ctx, cancel := context.WithTimeout(c.Request.Context(), 10*time.Second)
	defer cancel()

	checks := make(map[string]CheckResult)
	allHealthy := true

	// 检查数据库连接
	if h.services.DB != nil {
		start := time.Now()
		err := h.services.DB.PingContext(ctx)
		duration := time.Since(start)

		if err != nil {
			allHealthy = false
			checks["database"] = CheckResult{
				Status:    "unhealthy",
				Message:   "Database connection failed",
				Duration:  duration,
				Timestamp: time.Now(),
				Error:     err.Error(),
			}
		} else {
			checks["database"] = CheckResult{
				Status:    "healthy",
				Message:   "Database connection successful",
				Duration:  duration,
				Timestamp: time.Now(),
			}
		}
	}

	// 检查Redis连接
	if h.services.Redis != nil {
		start := time.Now()
		err := h.services.Redis.Ping(ctx).Err()
		duration := time.Since(start)

		if err != nil {
			allHealthy = false
			checks["redis"] = CheckResult{
				Status:    "unhealthy",
				Message:   "Redis connection failed",
				Duration:  duration,
				Timestamp: time.Now(),
				Error:     err.Error(),
			}
		} else {
			checks["redis"] = CheckResult{
				Status:    "healthy",
				Message:   "Redis connection successful",
				Duration:  duration,
				Timestamp: time.Now(),
			}
		}
	}

	// 检查gRPC连接池
	if h.services.GRPCPool != nil {
		start := time.Now()
		// 这里可以添加gRPC连接池的健康检查
		duration := time.Since(start)

		checks["grpc_pool"] = CheckResult{
			Status:    "healthy",
			Message:   "gRPC connection pool is available",
			Duration:  duration,
			Timestamp: time.Now(),
		}
	}

	status := "ready"
	message := "Service is ready"
	statusCode := http.StatusOK

	if !allHealthy {
		status = "not_ready"
		message = "Service is not ready"
		statusCode = http.StatusServiceUnavailable
	}

	healthStatus := &HealthStatus{
		Status:    status,
		Timestamp: time.Now(),
		Uptime:    time.Since(startTime).String(),
		Checks:    checks,
		Message:   message,
	}

	c.JSON(statusCode, response.Response{
		Code:    statusCode,
		Message: message,
		Data:    healthStatus,
	})
}

// Status 详细状态检查
func (h *HealthHandler) Status(c *gin.Context) {
	ctx, cancel := context.WithTimeout(c.Request.Context(), 15*time.Second)
	defer cancel()

	checks := make(map[string]CheckResult)
	allHealthy := true

	// 数据库检查
	if h.services.DB != nil {
		start := time.Now()
		err := h.services.DB.PingContext(ctx)
		duration := time.Since(start)

		if err != nil {
			allHealthy = false
			checks["database"] = CheckResult{
				Status:    "unhealthy",
				Message:   "Database ping failed",
				Duration:  duration,
				Timestamp: time.Now(),
				Error:     err.Error(),
			}
		} else {
			// 检查数据库统计信息
			stats := h.services.DB.Stats()
			checks["database"] = CheckResult{
				Status:    "healthy",
				Message:   fmt.Sprintf("Database healthy - Open: %d, InUse: %d, Idle: %d", stats.OpenConnections, stats.InUse, stats.Idle),
				Duration:  duration,
				Timestamp: time.Now(),
			}
		}
	}

	// Redis检查
	if h.services.Redis != nil {
		start := time.Now()
		err := h.services.Redis.Ping(ctx).Err()
		duration := time.Since(start)

		if err != nil {
			allHealthy = false
			checks["redis"] = CheckResult{
				Status:    "unhealthy",
				Message:   "Redis ping failed",
				Duration:  duration,
				Timestamp: time.Now(),
				Error:     err.Error(),
			}
		} else {
			// 检查Redis信息
			info := h.services.Redis.Info(ctx, "memory")
			checks["redis"] = CheckResult{
				Status:    "healthy",
				Message:   "Redis connection healthy",
				Duration:  duration,
				Timestamp: time.Now(),
			}
			if info.Err() == nil {
				checks["redis"].Message += " - Memory info available"
			}
		}
	}

	// 服务检查
	if h.services.Auth != nil {
		checks["auth_service"] = CheckResult{
			Status:    "healthy",
			Message:   "Auth service available",
			Timestamp: time.Now(),
		}
	}

	if h.services.User != nil {
		checks["user_service"] = CheckResult{
			Status:    "healthy",
			Message:   "User service available",
			Timestamp: time.Now(),
		}
	}

	if h.services.Model != nil {
		checks["model_service"] = CheckResult{
			Status:    "healthy",
			Message:   "Model service available",
			Timestamp: time.Now(),
		}
	}

	if h.services.Task != nil {
		checks["task_service"] = CheckResult{
			Status:    "healthy",
			Message:   "Task service available",
			Timestamp: time.Now(),
		}
	}

	if h.services.Inference != nil {
		checks["inference_service"] = CheckResult{
			Status:    "healthy",
			Message:   "Inference service available",
			Timestamp: time.Now(),
		}
	}

	if h.services.Alert != nil {
		checks["alert_service"] = CheckResult{
			Status:    "healthy",
			Message:   "Alert service available",
			Timestamp: time.Now(),
		}
	}

	status := "healthy"
	message := "All systems operational"
	statusCode := http.StatusOK

	if !allHealthy {
		status = "degraded"
		message = "Some systems are unhealthy"
		statusCode = http.StatusServiceUnavailable
	}

	healthStatus := &HealthStatus{
		Status:    status,
		Timestamp: time.Now(),
		Uptime:    time.Since(startTime).String(),
		Checks:    checks,
		Message:   message,
	}

	c.JSON(statusCode, response.Response{
		Code:    statusCode,
		Message: message,
		Data:    healthStatus,
	})
}

// Dependencies 依赖检查
func (h *HealthHandler) Dependencies(c *gin.Context) {
	ctx, cancel := context.WithTimeout(c.Request.Context(), 20*time.Second)
	defer cancel()

	dependencies := make([]DependencyStatus, 0)
	allHealthy := true

	// 数据库依赖
	if h.services.DB != nil {
		start := time.Now()
		err := h.services.DB.PingContext(ctx)
		duration := time.Since(start)

		dep := DependencyStatus{
			Name:      "PostgreSQL Database",
			Duration:  duration,
			Timestamp: time.Now(),
		}

		if err != nil {
			allHealthy = false
			dep.Status = "unhealthy"
			dep.Message = "Database connection failed"
			dep.Error = err.Error()
		} else {
			dep.Status = "healthy"
			dep.Message = "Database connection successful"
		}

		dependencies = append(dependencies, dep)
	}

	// Redis依赖
	if h.services.Redis != nil {
		start := time.Now()
		err := h.services.Redis.Ping(ctx).Err()
		duration := time.Since(start)

		dep := DependencyStatus{
			Name:      "Redis Cache",
			Duration:  duration,
			Timestamp: time.Now(),
		}

		if err != nil {
			allHealthy = false
			dep.Status = "unhealthy"
			dep.Message = "Redis connection failed"
			dep.Error = err.Error()
		} else {
			dep.Status = "healthy"
			dep.Message = "Redis connection successful"
		}

		dependencies = append(dependencies, dep)
	}

	// gRPC连接池依赖
	if h.services.GRPCPool != nil {
		dep := DependencyStatus{
			Name:      "gRPC Connection Pool",
			Status:    "healthy",
			Message:   "gRPC connection pool is available",
			Timestamp: time.Now(),
		}
		dependencies = append(dependencies, dep)
	}

	statusCode := http.StatusOK
	message := "All dependencies are healthy"

	if !allHealthy {
		statusCode = http.StatusServiceUnavailable
		message = "Some dependencies are unhealthy"
	}

	result := gin.H{
		"status":       map[string]interface{}{"healthy": allHealthy},
		"timestamp":    time.Now(),
		"dependencies": dependencies,
		"message":      message,
	}

	c.JSON(statusCode, response.Response{
		Code:    statusCode,
		Message: message,
		Data:    result,
	})
}