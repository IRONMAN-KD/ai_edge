package manager

import (
	"context"
	"fmt"
	"log"
	"runtime"
	"sync"
	"sync/atomic"
	"time"

	"ai-edge-platform/internal/models"
	"ai-edge-platform/internal/services"
	"ai-edge-platform/pkg/database"
	"ai-edge-platform/pkg/redis"
)

// Monitor 系统监控器
type Monitor struct {
	config         *MonitorConfig
	db             *database.DB
	redis          *redis.Client
	alertService   services.AlertService
	modelService   services.ModelService
	taskService    services.TaskService

	// 监控指标
	metrics        *SystemMetrics
	metricsHistory []*SystemMetrics
	maxHistory     int

	// 控制
	ctx     context.Context
	cancel  context.CancelFunc
	wg      sync.WaitGroup
	mu      sync.RWMutex
	running bool
}

// MonitorConfig 监控配置
type MonitorConfig struct {
	Interval         time.Duration
	MetricsRetention int
	AlertThresholds  *AlertThresholds
}

// AlertThresholds 告警阈值
type AlertThresholds struct {
	CPUUsage       float64 `json:"cpu_usage"`
	MemoryUsage    float64 `json:"memory_usage"`
	DiskUsage      float64 `json:"disk_usage"`
	ErrorRate      float64 `json:"error_rate"`
	ResponseTime   float64 `json:"response_time"`
	ActiveTasks    int     `json:"active_tasks"`
	FailedTasks    int     `json:"failed_tasks"`
	QueueSize      int     `json:"queue_size"`
}

// SystemMetrics 系统指标
type SystemMetrics struct {
	Timestamp time.Time `json:"timestamp"`

	// 系统资源
	CPUUsage    float64 `json:"cpu_usage"`
	MemoryUsage float64 `json:"memory_usage"`
	DiskUsage   float64 `json:"disk_usage"`
	Goroutines  int     `json:"goroutines"`

	// 应用指标
	ActiveTasks    int64   `json:"active_tasks"`
	CompletedTasks int64   `json:"completed_tasks"`
	FailedTasks    int64   `json:"failed_tasks"`
	QueueSize      int     `json:"queue_size"`
	ErrorRate      float64 `json:"error_rate"`
	ResponseTime   float64 `json:"response_time"`

	// 数据库指标
	DBConnections     int     `json:"db_connections"`
	DBActiveQueries   int     `json:"db_active_queries"`
	DBSlowQueries     int64   `json:"db_slow_queries"`
	DBQueryTime       float64 `json:"db_query_time"`

	// Redis 指标
	RedisConnections  int     `json:"redis_connections"`
	RedisMemoryUsage  int64   `json:"redis_memory_usage"`
	RedisKeyCount     int64   `json:"redis_key_count"`
	RedisHitRate      float64 `json:"redis_hit_rate"`

	// 模型指标
	ActiveModels      int     `json:"active_models"`
	InferenceRequests int64   `json:"inference_requests"`
	InferenceLatency  float64 `json:"inference_latency"`
	InferenceErrors   int64   `json:"inference_errors"`
}

// NewMonitor 创建新的监控器
func NewMonitor(config *MonitorConfig, db *database.DB, redis *redis.Client, alertService services.AlertService, modelService services.ModelService, taskService services.TaskService) *Monitor {
	return &Monitor{
		config:         config,
		db:             db,
		redis:          redis,
		alertService:   alertService,
		modelService:   modelService,
		taskService:    taskService,
		metrics:        &SystemMetrics{},
		metricsHistory: make([]*SystemMetrics, 0, config.MetricsRetention),
		maxHistory:     config.MetricsRetention,
	}
}

// Start 启动监控器
func (m *Monitor) Start(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.running {
		return fmt.Errorf("monitor is already running")
	}

	log.Println("Starting system monitor...")

	m.ctx, m.cancel = context.WithCancel(ctx)
	m.running = true

	// 启动监控循环
	m.wg.Add(1)
	go m.monitorLoop()

	log.Printf("System monitor started with interval: %v", m.config.Interval)

	// 等待上下文取消
	<-m.ctx.Done()

	// 等待监控循环完成
	m.wg.Wait()

	m.mu.Lock()
	m.running = false
	m.mu.Unlock()

	log.Println("System monitor stopped")
	return nil
}

// Stop 停止监控器
func (m *Monitor) Stop() {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.running {
		return
	}

	log.Println("Stopping system monitor...")

	if m.cancel != nil {
		m.cancel()
	}
}

// GetMetrics 获取当前指标
func (m *Monitor) GetMetrics() *SystemMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// 返回指标副本
	metrics := *m.metrics
	return &metrics
}

// GetMetricsHistory 获取指标历史
func (m *Monitor) GetMetricsHistory() []*SystemMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// 返回历史副本
	history := make([]*SystemMetrics, len(m.metricsHistory))
	copy(history, m.metricsHistory)
	return history
}

// GetStatus 获取监控器状态
func (m *Monitor) GetStatus() *MonitorStatus {
	m.mu.RLock()
	defer m.mu.RUnlock()

	return &MonitorStatus{
		Running:       m.running,
		LastUpdate:    m.metrics.Timestamp,
		MetricsCount:  len(m.metricsHistory),
		CurrentMetrics: m.metrics,
	}
}

// monitorLoop 监控主循环
func (m *Monitor) monitorLoop() {
	defer m.wg.Done()

	ticker := time.NewTicker(m.config.Interval)
	defer ticker.Stop()

	log.Printf("Monitor loop started with interval: %v", m.config.Interval)

	for {
		select {
		case <-m.ctx.Done():
			log.Println("Monitor loop context cancelled")
			return
		case <-ticker.C:
			m.collectMetrics()
			m.checkAlerts()
		}
	}
}

// collectMetrics 收集系统指标
func (m *Monitor) collectMetrics() {
	start := time.Now()

	metrics := &SystemMetrics{
		Timestamp: start,
	}

	// 收集系统资源指标
	m.collectSystemMetrics(metrics)

	// 收集应用指标
	m.collectApplicationMetrics(metrics)

	// 收集数据库指标
	m.collectDatabaseMetrics(metrics)

	// 收集 Redis 指标
	m.collectRedisMetrics(metrics)

	// 收集模型指标
	m.collectModelMetrics(metrics)

	// 更新当前指标
	m.mu.Lock()
	m.metrics = metrics

	// 添加到历史记录
	m.metricsHistory = append(m.metricsHistory, metrics)
	if len(m.metricsHistory) > m.maxHistory {
		m.metricsHistory = m.metricsHistory[1:]
	}
	m.mu.Unlock()

	duration := time.Since(start)
	log.Printf("Metrics collection completed in %v", duration)
}

// collectSystemMetrics 收集系统资源指标
func (m *Monitor) collectSystemMetrics(metrics *SystemMetrics) {
	// 获取内存统计
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)

	// 计算内存使用率（简化版本）
	metrics.MemoryUsage = float64(memStats.Alloc) / float64(memStats.Sys) * 100

	// 获取 Goroutine 数量
	metrics.Goroutines = runtime.NumGoroutine()

	// CPU 使用率需要通过系统调用获取，这里使用模拟值
	metrics.CPUUsage = m.getCPUUsage()

	// 磁盘使用率需要通过系统调用获取，这里使用模拟值
	metrics.DiskUsage = m.getDiskUsage()
}

// collectApplicationMetrics 收集应用指标
func (m *Monitor) collectApplicationMetrics(metrics *SystemMetrics) {
	// 获取任务统计
	if taskStats, err := m.taskService.GetTaskStats(m.ctx); err == nil {
		metrics.ActiveTasks = taskStats.ActiveTasks
		metrics.CompletedTasks = taskStats.CompletedTasks
		metrics.FailedTasks = taskStats.FailedTasks
		metrics.QueueSize = taskStats.QueueSize
		metrics.ErrorRate = taskStats.ErrorRate
		metrics.ResponseTime = taskStats.AvgResponseTime
	} else {
		log.Printf("Failed to get task stats: %v", err)
	}
}

// collectDatabaseMetrics 收集数据库指标
func (m *Monitor) collectDatabaseMetrics(metrics *SystemMetrics) {
	if m.db != nil {
		// 获取数据库连接池统计
		dbStats := m.db.Stats()
		metrics.DBConnections = dbStats.OpenConnections
		metrics.DBActiveQueries = dbStats.InUse

		// 查询时间统计（需要自定义实现）
		metrics.DBQueryTime = m.getDBQueryTime()
		metrics.DBSlowQueries = m.getDBSlowQueries()
	}
}

// collectRedisMetrics 收集 Redis 指标
func (m *Monitor) collectRedisMetrics(metrics *SystemMetrics) {
	if m.redis != nil {
		// 获取 Redis 统计信息
		if info, err := m.redis.Info(m.ctx, "memory").Result(); err == nil {
			// 解析内存使用信息
			metrics.RedisMemoryUsage = m.parseRedisMemoryUsage(info)
		}

		if info, err := m.redis.Info(m.ctx, "stats").Result(); err == nil {
			// 解析统计信息
			metrics.RedisHitRate = m.parseRedisHitRate(info)
		}

		// 获取键数量
		if size, err := m.redis.DBSize(m.ctx).Result(); err == nil {
			metrics.RedisKeyCount = size
		}

		// 连接数统计
		metrics.RedisConnections = m.getRedisConnections()
	}
}

// collectModelMetrics 收集模型指标
func (m *Monitor) collectModelMetrics(metrics *SystemMetrics) {
	// 获取活跃模型数量
	if activeModels, err := m.modelService.GetActiveModels(m.ctx); err == nil {
		metrics.ActiveModels = len(activeModels)
	} else {
		log.Printf("Failed to get active models: %v", err)
	}

	// 推理指标（需要从推理服务获取）
	metrics.InferenceRequests = m.getInferenceRequests()
	metrics.InferenceLatency = m.getInferenceLatency()
	metrics.InferenceErrors = m.getInferenceErrors()
}

// checkAlerts 检查告警条件
func (m *Monitor) checkAlerts() {
	if m.config.AlertThresholds == nil {
		return
	}

	thresholds := m.config.AlertThresholds
	metrics := m.metrics

	// 检查 CPU 使用率
	if metrics.CPUUsage > thresholds.CPUUsage {
		m.createAlert("high_cpu_usage", fmt.Sprintf("CPU usage is %.2f%%, exceeding threshold %.2f%%", metrics.CPUUsage, thresholds.CPUUsage), "warning")
	}

	// 检查内存使用率
	if metrics.MemoryUsage > thresholds.MemoryUsage {
		m.createAlert("high_memory_usage", fmt.Sprintf("Memory usage is %.2f%%, exceeding threshold %.2f%%", metrics.MemoryUsage, thresholds.MemoryUsage), "warning")
	}

	// 检查磁盘使用率
	if metrics.DiskUsage > thresholds.DiskUsage {
		m.createAlert("high_disk_usage", fmt.Sprintf("Disk usage is %.2f%%, exceeding threshold %.2f%%", metrics.DiskUsage, thresholds.DiskUsage), "warning")
	}

	// 检查错误率
	if metrics.ErrorRate > thresholds.ErrorRate {
		m.createAlert("high_error_rate", fmt.Sprintf("Error rate is %.2f%%, exceeding threshold %.2f%%", metrics.ErrorRate, thresholds.ErrorRate), "critical")
	}

	// 检查响应时间
	if metrics.ResponseTime > thresholds.ResponseTime {
		m.createAlert("high_response_time", fmt.Sprintf("Response time is %.2fms, exceeding threshold %.2fms", metrics.ResponseTime, thresholds.ResponseTime), "warning")
	}

	// 检查活跃任务数
	if int(metrics.ActiveTasks) > thresholds.ActiveTasks {
		m.createAlert("too_many_active_tasks", fmt.Sprintf("Active tasks count is %d, exceeding threshold %d", metrics.ActiveTasks, thresholds.ActiveTasks), "warning")
	}

	// 检查失败任务数
	if int(metrics.FailedTasks) > thresholds.FailedTasks {
		m.createAlert("too_many_failed_tasks", fmt.Sprintf("Failed tasks count is %d, exceeding threshold %d", metrics.FailedTasks, thresholds.FailedTasks), "critical")
	}

	// 检查队列大小
	if metrics.QueueSize > thresholds.QueueSize {
		m.createAlert("large_queue_size", fmt.Sprintf("Queue size is %d, exceeding threshold %d", metrics.QueueSize, thresholds.QueueSize), "warning")
	}
}

// createAlert 创建告警
func (m *Monitor) createAlert(alertType, message, level string) {
	alert := &models.Alert{
		Type:      alertType,
		Level:     level,
		Message:   message,
		Source:    "system_monitor",
		Status:    "active",
		CreatedAt: time.Now(),
	}

	if err := m.alertService.CreateAlert(m.ctx, alert); err != nil {
		log.Printf("Failed to create alert: %v", err)
	} else {
		log.Printf("Alert created: %s - %s", alertType, message)
	}
}

// 以下是辅助方法，实际实现需要根据具体环境调整

// getCPUUsage 获取 CPU 使用率
func (m *Monitor) getCPUUsage() float64 {
	// 这里需要实现实际的 CPU 使用率获取逻辑
	// 可以使用 github.com/shirou/gopsutil 库
	return 0.0
}

// getDiskUsage 获取磁盘使用率
func (m *Monitor) getDiskUsage() float64 {
	// 这里需要实现实际的磁盘使用率获取逻辑
	return 0.0
}

// getDBQueryTime 获取数据库查询时间
func (m *Monitor) getDBQueryTime() float64 {
	// 这里需要实现数据库查询时间统计
	return 0.0
}

// getDBSlowQueries 获取慢查询数量
func (m *Monitor) getDBSlowQueries() int64 {
	// 这里需要实现慢查询统计
	return 0
}

// parseRedisMemoryUsage 解析 Redis 内存使用
func (m *Monitor) parseRedisMemoryUsage(info string) int64 {
	// 解析 Redis INFO 命令返回的内存信息
	return 0
}

// parseRedisHitRate 解析 Redis 命中率
func (m *Monitor) parseRedisHitRate(info string) float64 {
	// 解析 Redis INFO 命令返回的统计信息
	return 0.0
}

// getRedisConnections 获取 Redis 连接数
func (m *Monitor) getRedisConnections() int {
	// 获取 Redis 连接池统计
	return 0
}

// getInferenceRequests 获取推理请求数
func (m *Monitor) getInferenceRequests() int64 {
	// 从推理服务获取请求统计
	return 0
}

// getInferenceLatency 获取推理延迟
func (m *Monitor) getInferenceLatency() float64 {
	// 从推理服务获取延迟统计
	return 0.0
}

// getInferenceErrors 获取推理错误数
func (m *Monitor) getInferenceErrors() int64 {
	// 从推理服务获取错误统计
	return 0
}