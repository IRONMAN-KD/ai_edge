package manager

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"ai-edge-platform/internal/services"
)

// Manager 管理器结构体
type Manager struct {
	config   *Config
	services *services.Services

	// 组件
	taskScheduler *TaskScheduler
	monitor       *Monitor
	alertManager  *AlertManager
	healthChecker *HealthChecker

	// 控制
	ctx    context.Context
	cancel context.CancelFunc
	wg     sync.WaitGroup
	mu     sync.RWMutex

	// 状态
	running bool
	started time.Time
}

// Config 管理器配置
type Config struct {
	// 任务调度器配置
	TaskSchedulerInterval  time.Duration
	TaskSchedulerWorkers   int
	TaskSchedulerQueueSize int

	// 监控配置
	MonitoringInterval       time.Duration
	MonitoringRetentionDays  int
	HealthCheckInterval      time.Duration
	MetricsCollectionInterval time.Duration

	// 告警配置
	AlertCheckInterval time.Duration
	AlertRetentionDays int
}

// NewManager 创建新的管理器实例
func NewManager(config *Config, services *services.Services) *Manager {
	return &Manager{
		config:   config,
		services: services,
	}
}

// Start 启动管理器
func (m *Manager) Start(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.running {
		return fmt.Errorf("manager is already running")
	}

	log.Println("Starting AI Edge Platform Manager...")

	// 创建上下文
	m.ctx, m.cancel = context.WithCancel(ctx)
	m.started = time.Now()

	// 初始化组件
	if err := m.initComponents(); err != nil {
		return fmt.Errorf("failed to initialize components: %w", err)
	}

	// 启动组件
	if err := m.startComponents(); err != nil {
		return fmt.Errorf("failed to start components: %w", err)
	}

	m.running = true
	log.Println("AI Edge Platform Manager started successfully")

	// 等待上下文取消
	<-m.ctx.Done()

	return nil
}

// Stop 停止管理器
func (m *Manager) Stop(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.running {
		return nil
	}

	log.Println("Stopping AI Edge Platform Manager...")

	// 取消上下文
	if m.cancel != nil {
		m.cancel()
	}

	// 等待所有 goroutine 完成
	done := make(chan struct{})
	go func() {
		m.wg.Wait()
		close(done)
	}()

	// 等待完成或超时
	select {
	case <-done:
		log.Println("All components stopped gracefully")
	case <-ctx.Done():
		log.Println("Stop timeout, forcing shutdown")
	}

	m.running = false
	log.Println("AI Edge Platform Manager stopped")

	return nil
}

// IsRunning 检查管理器是否正在运行
func (m *Manager) IsRunning() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.running
}

// GetStatus 获取管理器状态
func (m *Manager) GetStatus() *ManagerStatus {
	m.mu.RLock()
	defer m.mu.RUnlock()

	status := &ManagerStatus{
		Running:   m.running,
		StartTime: m.started,
		Uptime:    time.Since(m.started),
	}

	if m.running {
		status.Components = &ComponentStatus{
			TaskScheduler: m.taskScheduler.GetStatus(),
			Monitor:       m.monitor.GetStatus(),
			AlertManager:  m.alertManager.GetStatus(),
			HealthChecker: m.healthChecker.GetStatus(),
		}
	}

	return status
}

// initComponents 初始化所有组件
func (m *Manager) initComponents() error {
	log.Println("Initializing manager components...")

	// 初始化任务调度器
	m.taskScheduler = NewTaskScheduler(&TaskSchedulerConfig{
		Interval:  m.config.TaskSchedulerInterval,
		Workers:   m.config.TaskSchedulerWorkers,
		QueueSize: m.config.TaskSchedulerQueueSize,
	}, m.services.Task, m.services.Inference)

	// 初始化监控器
	m.monitor = NewMonitor(&MonitorConfig{
		Interval:                 m.config.MonitoringInterval,
		RetentionDays:            m.config.MonitoringRetentionDays,
		MetricsCollectionInterval: m.config.MetricsCollectionInterval,
	}, m.services)

	// 初始化告警管理器
	m.alertManager = NewAlertManager(&AlertManagerConfig{
		CheckInterval: m.config.AlertCheckInterval,
		RetentionDays: m.config.AlertRetentionDays,
	}, m.services.Alert, m.services.Task, m.services.Model)

	// 初始化健康检查器
	m.healthChecker = NewHealthChecker(&HealthCheckerConfig{
		Interval: m.config.HealthCheckInterval,
	}, m.services)

	log.Println("Manager components initialized successfully")
	return nil
}

// startComponents 启动所有组件
func (m *Manager) startComponents() error {
	log.Println("Starting manager components...")

	// 启动任务调度器
	m.wg.Add(1)
	go func() {
		defer m.wg.Done()
		if err := m.taskScheduler.Start(m.ctx); err != nil {
			log.Printf("Task scheduler error: %v", err)
		}
	}()

	// 启动监控器
	m.wg.Add(1)
	go func() {
		defer m.wg.Done()
		if err := m.monitor.Start(m.ctx); err != nil {
			log.Printf("Monitor error: %v", err)
		}
	}()

	// 启动告警管理器
	m.wg.Add(1)
	go func() {
		defer m.wg.Done()
		if err := m.alertManager.Start(m.ctx); err != nil {
			log.Printf("Alert manager error: %v", err)
		}
	}()

	// 启动健康检查器
	m.wg.Add(1)
	go func() {
		defer m.wg.Done()
		if err := m.healthChecker.Start(m.ctx); err != nil {
			log.Printf("Health checker error: %v", err)
		}
	}()

	log.Println("Manager components started successfully")
	return nil
}

// ManagerStatus 管理器状态
type ManagerStatus struct {
	Running    bool               `json:"running"`
	StartTime  time.Time          `json:"start_time"`
	Uptime     time.Duration      `json:"uptime"`
	Components *ComponentStatus   `json:"components,omitempty"`
}

// ComponentStatus 组件状态
type ComponentStatus struct {
	TaskScheduler *TaskSchedulerStatus `json:"task_scheduler"`
	Monitor       *MonitorStatus       `json:"monitor"`
	AlertManager  *AlertManagerStatus  `json:"alert_manager"`
	HealthChecker *HealthCheckerStatus `json:"health_checker"`
}

// TaskSchedulerStatus 任务调度器状态
type TaskSchedulerStatus struct {
	Running        bool      `json:"running"`
	ActiveWorkers  int       `json:"active_workers"`
	QueueSize      int       `json:"queue_size"`
	ProcessedTasks int64     `json:"processed_tasks"`
	FailedTasks    int64     `json:"failed_tasks"`
	LastRun        time.Time `json:"last_run"`
}

// MonitorStatus 监控器状态
type MonitorStatus struct {
	Running              bool      `json:"running"`
	LastMetricsCollection time.Time `json:"last_metrics_collection"`
	MetricsCount         int64     `json:"metrics_count"`
	LastCleanup          time.Time `json:"last_cleanup"`
}

// AlertManagerStatus 告警管理器状态
type AlertManagerStatus struct {
	Running       bool      `json:"running"`
	ActiveAlerts  int       `json:"active_alerts"`
	TotalAlerts   int64     `json:"total_alerts"`
	LastCheck     time.Time `json:"last_check"`
	LastCleanup   time.Time `json:"last_cleanup"`
}

// HealthCheckerStatus 健康检查器状态
type HealthCheckerStatus struct {
	Running     bool      `json:"running"`
	LastCheck   time.Time `json:"last_check"`
	Healthy     bool      `json:"healthy"`
	CheckCount  int64     `json:"check_count"`
	FailedCount int64     `json:"failed_count"`
}