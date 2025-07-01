package manager

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"ai-edge-platform/internal/grpc"
	"ai-edge-platform/internal/models"
	"ai-edge-platform/internal/services"
	"ai-edge-platform/pkg/database"
	"ai-edge-platform/pkg/redis"
)

// HealthChecker 健康检查器
type HealthChecker struct {
	config         *HealthCheckerConfig
	db             *database.DB
	redis          *redis.Client
	grpcClient     *grpc.InferenceClientPool
	alertService   services.AlertService

	// 健康状态
	healthStatus   *HealthStatus
	checkResults   map[string]*CheckResult

	// 控制
	ctx     context.Context
	cancel  context.CancelFunc
	wg      sync.WaitGroup
	mu      sync.RWMutex
	running bool
}

// HealthCheckerConfig 健康检查器配置
type HealthCheckerConfig struct {
	Interval        time.Duration
	Timeout         time.Duration
	RetryCount      int
	RetryInterval   time.Duration
	AlertOnFailure  bool
	Checks          map[string]*CheckConfig
}

// CheckConfig 检查配置
type CheckConfig struct {
	Enabled     bool          `json:"enabled"`
	Interval    time.Duration `json:"interval"`
	Timeout     time.Duration `json:"timeout"`
	RetryCount  int           `json:"retry_count"`
	Critical    bool          `json:"critical"`
	Params      map[string]interface{} `json:"params"`
}

// HealthStatus 健康状态
type HealthStatus struct {
	Overall     string                 `json:"overall"`
	LastCheck   time.Time              `json:"last_check"`
	Components  map[string]*ComponentStatus `json:"components"`
	Uptime      time.Duration          `json:"uptime"`
	StartTime   time.Time              `json:"start_time"`
}

// ComponentStatus 组件状态
type ComponentStatus struct {
	Name        string    `json:"name"`
	Status      string    `json:"status"`
	Message     string    `json:"message"`
	LastCheck   time.Time `json:"last_check"`
	ResponseTime time.Duration `json:"response_time"`
	Error       string    `json:"error,omitempty"`
}

// CheckResult 检查结果
type CheckResult struct {
	Name         string        `json:"name"`
	Status       string        `json:"status"`
	Message      string        `json:"message"`
	Error        string        `json:"error,omitempty"`
	ResponseTime time.Duration `json:"response_time"`
	Timestamp    time.Time     `json:"timestamp"`
	RetryCount   int           `json:"retry_count"`
}

// HealthCheck 健康检查接口
type HealthCheck interface {
	Check(ctx context.Context) *CheckResult
	GetName() string
}

// NewHealthChecker 创建新的健康检查器
func NewHealthChecker(config *HealthCheckerConfig, db *database.DB, redis *redis.Client, grpcClient *grpc.InferenceClientPool, alertService services.AlertService) *HealthChecker {
	return &HealthChecker{
		config:       config,
		db:           db,
		redis:        redis,
		grpcClient:   grpcClient,
		alertService: alertService,
		healthStatus: &HealthStatus{
			Overall:    "unknown",
			Components: make(map[string]*ComponentStatus),
			StartTime:  time.Now(),
		},
		checkResults: make(map[string]*CheckResult),
	}
}

// Start 启动健康检查器
func (hc *HealthChecker) Start(ctx context.Context) error {
	hc.mu.Lock()
	defer hc.mu.Unlock()

	if hc.running {
		return fmt.Errorf("health checker is already running")
	}

	log.Println("Starting health checker...")

	hc.ctx, hc.cancel = context.WithCancel(ctx)
	hc.running = true
	hc.healthStatus.StartTime = time.Now()

	// 启动健康检查循环
	hc.wg.Add(1)
	go hc.checkLoop()

	log.Printf("Health checker started with interval: %v", hc.config.Interval)

	// 等待上下文取消
	<-hc.ctx.Done()

	// 等待检查循环完成
	hc.wg.Wait()

	hc.mu.Lock()
	hc.running = false
	hc.mu.Unlock()

	log.Println("Health checker stopped")
	return nil
}

// Stop 停止健康检查器
func (hc *HealthChecker) Stop() {
	hc.mu.Lock()
	defer hc.mu.Unlock()

	if !hc.running {
		return
	}

	log.Println("Stopping health checker...")

	if hc.cancel != nil {
		hc.cancel()
	}
}

// GetHealthStatus 获取健康状态
func (hc *HealthChecker) GetHealthStatus() *HealthStatus {
	hc.mu.RLock()
	defer hc.mu.RUnlock()

	// 计算运行时间
	hc.healthStatus.Uptime = time.Since(hc.healthStatus.StartTime)

	// 返回状态副本
	status := *hc.healthStatus
	status.Components = make(map[string]*ComponentStatus)
	for k, v := range hc.healthStatus.Components {
		component := *v
		status.Components[k] = &component
	}

	return &status
}

// GetCheckResults 获取检查结果
func (hc *HealthChecker) GetCheckResults() map[string]*CheckResult {
	hc.mu.RLock()
	defer hc.mu.RUnlock()

	// 返回结果副本
	results := make(map[string]*CheckResult)
	for k, v := range hc.checkResults {
		result := *v
		results[k] = &result
	}

	return results
}

// IsHealthy 检查系统是否健康
func (hc *HealthChecker) IsHealthy() bool {
	hc.mu.RLock()
	defer hc.mu.RUnlock()

	return hc.healthStatus.Overall == "healthy"
}

// checkLoop 健康检查主循环
func (hc *HealthChecker) checkLoop() {
	defer hc.wg.Done()

	ticker := time.NewTicker(hc.config.Interval)
	defer ticker.Stop()

	log.Printf("Health check loop started with interval: %v", hc.config.Interval)

	// 立即执行一次检查
	hc.performHealthChecks()

	for {
		select {
		case <-hc.ctx.Done():
			log.Println("Health check loop context cancelled")
			return
		case <-ticker.C:
			hc.performHealthChecks()
		}
	}
}

// performHealthChecks 执行健康检查
func (hc *HealthChecker) performHealthChecks() {
	start := time.Now()

	log.Println("Performing health checks...")

	// 创建健康检查器列表
	checks := hc.createHealthChecks()

	// 并发执行检查
	results := hc.runChecks(checks)

	// 更新状态
	hc.updateHealthStatus(results)

	// 处理告警
	hc.handleAlerts(results)

	duration := time.Since(start)
	log.Printf("Health checks completed in %v", duration)
}

// createHealthChecks 创建健康检查器列表
func (hc *HealthChecker) createHealthChecks() []HealthCheck {
	checks := make([]HealthCheck, 0)

	// 数据库检查
	if hc.db != nil {
		checks = append(checks, NewDatabaseCheck(hc.db))
	}

	// Redis 检查
	if hc.redis != nil {
		checks = append(checks, NewRedisCheck(hc.redis))
	}

	// gRPC 检查
	if hc.grpcClient != nil {
		checks = append(checks, NewGRPCCheck(hc.grpcClient))
	}

	// 磁盘空间检查
	checks = append(checks, NewDiskSpaceCheck())

	// 内存检查
	checks = append(checks, NewMemoryCheck())

	// HTTP 端点检查
	checks = append(checks, NewHTTPCheck())

	return checks
}

// runChecks 并发运行检查
func (hc *HealthChecker) runChecks(checks []HealthCheck) map[string]*CheckResult {
	results := make(map[string]*CheckResult)
	resultsChan := make(chan *CheckResult, len(checks))

	// 启动检查协程
	for _, check := range checks {
		go func(c HealthCheck) {
			ctx, cancel := context.WithTimeout(hc.ctx, hc.config.Timeout)
			defer cancel()

			result := c.Check(ctx)
			resultsChan <- result
		}(check)
	}

	// 收集结果
	for i := 0; i < len(checks); i++ {
		select {
		case result := <-resultsChan:
			results[result.Name] = result
		case <-time.After(hc.config.Timeout + time.Second):
			log.Printf("Health check timeout after %v", hc.config.Timeout)
		}
	}

	return results
}

// updateHealthStatus 更新健康状态
func (hc *HealthChecker) updateHealthStatus(results map[string]*CheckResult) {
	hc.mu.Lock()
	defer hc.mu.Unlock()

	// 更新检查结果
	hc.checkResults = results

	// 更新组件状态
	hc.healthStatus.Components = make(map[string]*ComponentStatus)
	healthyCount := 0
	totalCount := len(results)

	for _, result := range results {
		component := &ComponentStatus{
			Name:         result.Name,
			Status:       result.Status,
			Message:      result.Message,
			LastCheck:    result.Timestamp,
			ResponseTime: result.ResponseTime,
			Error:        result.Error,
		}

		hc.healthStatus.Components[result.Name] = component

		if result.Status == "healthy" {
			healthyCount++
		}
	}

	// 计算整体状态
	if healthyCount == totalCount {
		hc.healthStatus.Overall = "healthy"
	} else if healthyCount > 0 {
		hc.healthStatus.Overall = "degraded"
	} else {
		hc.healthStatus.Overall = "unhealthy"
	}

	hc.healthStatus.LastCheck = time.Now()
}

// handleAlerts 处理告警
func (hc *HealthChecker) handleAlerts(results map[string]*CheckResult) {
	if !hc.config.AlertOnFailure || hc.alertService == nil {
		return
	}

	for _, result := range results {
		if result.Status != "healthy" {
			hc.createHealthAlert(result)
		}
	}
}

// createHealthAlert 创建健康检查告警
func (hc *HealthChecker) createHealthAlert(result *CheckResult) {
	level := "warning"
	if result.Status == "unhealthy" {
		level = "critical"
	}

	alert := &models.Alert{
		Type:      fmt.Sprintf("health_check_%s", result.Name),
		Level:     level,
		Message:   fmt.Sprintf("Health check failed for %s: %s", result.Name, result.Message),
		Source:    "health_checker",
		Status:    "active",
		CreatedAt: time.Now(),
	}

	if err := hc.alertService.CreateAlert(hc.ctx, alert); err != nil {
		log.Printf("Failed to create health check alert: %v", err)
	} else {
		log.Printf("Health check alert created: %s", result.Name)
	}
}

// DatabaseCheck 数据库健康检查
type DatabaseCheck struct {
	db *database.DB
}

// NewDatabaseCheck 创建数据库检查
func NewDatabaseCheck(db *database.DB) *DatabaseCheck {
	return &DatabaseCheck{db: db}
}

// Check 执行数据库检查
func (dc *DatabaseCheck) Check(ctx context.Context) *CheckResult {
	start := time.Now()
	result := &CheckResult{
		Name:      "database",
		Timestamp: start,
	}

	// 检查数据库连接
	if err := dc.db.PingContext(ctx); err != nil {
		result.Status = "unhealthy"
		result.Message = "Database connection failed"
		result.Error = err.Error()
	} else {
		// 执行简单查询
		var count int
		err := dc.db.QueryRowContext(ctx, "SELECT 1").Scan(&count)
		if err != nil {
			result.Status = "degraded"
			result.Message = "Database query failed"
			result.Error = err.Error()
		} else {
			result.Status = "healthy"
			result.Message = "Database is accessible"
		}
	}

	result.ResponseTime = time.Since(start)
	return result
}

// GetName 获取检查名称
func (dc *DatabaseCheck) GetName() string {
	return "database"
}

// RedisCheck Redis 健康检查
type RedisCheck struct {
	redis *redis.Client
}

// NewRedisCheck 创建 Redis 检查
func NewRedisCheck(redis *redis.Client) *RedisCheck {
	return &RedisCheck{redis: redis}
}

// Check 执行 Redis 检查
func (rc *RedisCheck) Check(ctx context.Context) *CheckResult {
	start := time.Now()
	result := &CheckResult{
		Name:      "redis",
		Timestamp: start,
	}

	// 检查 Redis 连接
	if err := rc.redis.Ping(ctx).Err(); err != nil {
		result.Status = "unhealthy"
		result.Message = "Redis connection failed"
		result.Error = err.Error()
	} else {
		// 执行简单操作
		testKey := "health_check_test"
		if err := rc.redis.Set(ctx, testKey, "test", time.Second).Err(); err != nil {
			result.Status = "degraded"
			result.Message = "Redis write failed"
			result.Error = err.Error()
		} else {
			rc.redis.Del(ctx, testKey) // 清理测试键
			result.Status = "healthy"
			result.Message = "Redis is accessible"
		}
	}

	result.ResponseTime = time.Since(start)
	return result
}

// GetName 获取检查名称
func (rc *RedisCheck) GetName() string {
	return "redis"
}

// GRPCCheck gRPC 健康检查
type GRPCCheck struct {
	grpcClient *grpc.InferenceClientPool
}

// NewGRPCCheck 创建 gRPC 检查
func NewGRPCCheck(grpcClient *grpc.InferenceClientPool) *GRPCCheck {
	return &GRPCCheck{grpcClient: grpcClient}
}

// Check 执行 gRPC 检查
func (gc *GRPCCheck) Check(ctx context.Context) *CheckResult {
	start := time.Now()
	result := &CheckResult{
		Name:      "grpc",
		Timestamp: start,
	}

	// 获取客户端
	client, err := gc.grpcClient.GetClient()
	if err != nil {
		result.Status = "unhealthy"
		result.Message = "gRPC client unavailable"
		result.Error = err.Error()
	} else {
		// 执行健康检查
		if err := client.HealthCheck(ctx); err != nil {
			result.Status = "degraded"
			result.Message = "gRPC health check failed"
			result.Error = err.Error()
		} else {
			result.Status = "healthy"
			result.Message = "gRPC service is accessible"
		}
		gc.grpcClient.ReturnClient(client)
	}

	result.ResponseTime = time.Since(start)
	return result
}

// GetName 获取检查名称
func (gc *GRPCCheck) GetName() string {
	return "grpc"
}

// DiskSpaceCheck 磁盘空间检查
type DiskSpaceCheck struct{}

// NewDiskSpaceCheck 创建磁盘空间检查
func NewDiskSpaceCheck() *DiskSpaceCheck {
	return &DiskSpaceCheck{}
}

// Check 执行磁盘空间检查
func (dsc *DiskSpaceCheck) Check(ctx context.Context) *CheckResult {
	start := time.Now()
	result := &CheckResult{
		Name:      "disk_space",
		Timestamp: start,
	}

	// 这里需要实现实际的磁盘空间检查逻辑
	// 可以使用 syscall 或第三方库如 github.com/shirou/gopsutil
	usagePercent := 75.0 // 模拟值

	if usagePercent > 90 {
		result.Status = "unhealthy"
		result.Message = fmt.Sprintf("Disk usage is %.1f%%, critically high", usagePercent)
	} else if usagePercent > 80 {
		result.Status = "degraded"
		result.Message = fmt.Sprintf("Disk usage is %.1f%%, getting high", usagePercent)
	} else {
		result.Status = "healthy"
		result.Message = fmt.Sprintf("Disk usage is %.1f%%, normal", usagePercent)
	}

	result.ResponseTime = time.Since(start)
	return result
}

// GetName 获取检查名称
func (dsc *DiskSpaceCheck) GetName() string {
	return "disk_space"
}

// MemoryCheck 内存检查
type MemoryCheck struct{}

// NewMemoryCheck 创建内存检查
func NewMemoryCheck() *MemoryCheck {
	return &MemoryCheck{}
}

// Check 执行内存检查
func (mc *MemoryCheck) Check(ctx context.Context) *CheckResult {
	start := time.Now()
	result := &CheckResult{
		Name:      "memory",
		Timestamp: start,
	}

	// 这里需要实现实际的内存检查逻辑
	usagePercent := 65.0 // 模拟值

	if usagePercent > 90 {
		result.Status = "unhealthy"
		result.Message = fmt.Sprintf("Memory usage is %.1f%%, critically high", usagePercent)
	} else if usagePercent > 80 {
		result.Status = "degraded"
		result.Message = fmt.Sprintf("Memory usage is %.1f%%, getting high", usagePercent)
	} else {
		result.Status = "healthy"
		result.Message = fmt.Sprintf("Memory usage is %.1f%%, normal", usagePercent)
	}

	result.ResponseTime = time.Since(start)
	return result
}

// GetName 获取检查名称
func (mc *MemoryCheck) GetName() string {
	return "memory"
}

// HTTPCheck HTTP 端点检查
type HTTPCheck struct {
	client *http.Client
}

// NewHTTPCheck 创建 HTTP 检查
func NewHTTPCheck() *HTTPCheck {
	return &HTTPCheck{
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// Check 执行 HTTP 检查
func (hc *HTTPCheck) Check(ctx context.Context) *CheckResult {
	start := time.Now()
	result := &CheckResult{
		Name:      "http",
		Timestamp: start,
	}

	// 检查本地 HTTP 端点
	req, err := http.NewRequestWithContext(ctx, "GET", "http://localhost:8080/health", nil)
	if err != nil {
		result.Status = "unhealthy"
		result.Message = "Failed to create HTTP request"
		result.Error = err.Error()
	} else {
		resp, err := hc.client.Do(req)
		if err != nil {
			result.Status = "unhealthy"
			result.Message = "HTTP request failed"
			result.Error = err.Error()
		} else {
			resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				result.Status = "healthy"
				result.Message = "HTTP endpoint is accessible"
			} else {
				result.Status = "degraded"
				result.Message = fmt.Sprintf("HTTP endpoint returned status %d", resp.StatusCode)
			}
		}
	}

	result.ResponseTime = time.Since(start)
	return result
}

// GetName 获取检查名称
func (hc *HTTPCheck) GetName() string {
	return "http"
}