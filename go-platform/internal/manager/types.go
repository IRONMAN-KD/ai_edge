package manager

import (
	"time"

	"ai-edge-platform/internal/models"
)

// ManagerStatus 管理器状态
type ManagerStatus struct {
	Running           bool                   `json:"running"`
	StartTime         time.Time              `json:"start_time"`
	Uptime            time.Duration          `json:"uptime"`
	TaskScheduler     *TaskSchedulerStatus   `json:"task_scheduler"`
	Monitor           *MonitorStatus         `json:"monitor"`
	AlertManager      *AlertManagerStatus    `json:"alert_manager"`
	HealthChecker     *HealthCheckerStatus   `json:"health_checker"`
	Components        map[string]interface{} `json:"components"`
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
	Running        bool           `json:"running"`
	LastUpdate     time.Time      `json:"last_update"`
	MetricsCount   int            `json:"metrics_count"`
	CurrentMetrics *SystemMetrics `json:"current_metrics"`
}

// AlertManagerStatus 告警管理器状态
type AlertManagerStatus struct {
	Running           bool `json:"running"`
	RulesCount        int  `json:"rules_count"`
	NotifiersCount    int  `json:"notifiers_count"`
	SuppressionCount  int  `json:"suppression_count"`
}

// HealthCheckerStatus 健康检查器状态
type HealthCheckerStatus struct {
	Running      bool          `json:"running"`
	LastCheck    time.Time     `json:"last_check"`
	OverallStatus string       `json:"overall_status"`
	ComponentsCount int        `json:"components_count"`
	HealthyCount int           `json:"healthy_count"`
}

// TaskStats 任务统计
type TaskStats struct {
	ActiveTasks     int64   `json:"active_tasks"`
	CompletedTasks  int64   `json:"completed_tasks"`
	FailedTasks     int64   `json:"failed_tasks"`
	QueueSize       int     `json:"queue_size"`
	ErrorRate       float64 `json:"error_rate"`
	AvgResponseTime float64 `json:"avg_response_time"`
}

// ComponentHealth 组件健康状态
type ComponentHealth struct {
	Name         string        `json:"name"`
	Status       string        `json:"status"`
	Message      string        `json:"message"`
	LastCheck    time.Time     `json:"last_check"`
	ResponseTime time.Duration `json:"response_time"`
	Error        string        `json:"error,omitempty"`
}

// SystemInfo 系统信息
type SystemInfo struct {
	Hostname     string    `json:"hostname"`
	OS           string    `json:"os"`
	Arch         string    `json:"arch"`
	GoVersion    string    `json:"go_version"`
	StartTime    time.Time `json:"start_time"`
	Uptime       time.Duration `json:"uptime"`
	PID          int       `json:"pid"`
	Goroutines   int       `json:"goroutines"`
}

// ResourceUsage 资源使用情况
type ResourceUsage struct {
	CPUPercent    float64 `json:"cpu_percent"`
	MemoryUsed    uint64  `json:"memory_used"`
	MemoryTotal   uint64  `json:"memory_total"`
	MemoryPercent float64 `json:"memory_percent"`
	DiskUsed      uint64  `json:"disk_used"`
	DiskTotal     uint64  `json:"disk_total"`
	DiskPercent   float64 `json:"disk_percent"`
	NetworkIn     uint64  `json:"network_in"`
	NetworkOut    uint64  `json:"network_out"`
}

// DatabaseStats 数据库统计
type DatabaseStats struct {
	Connections      int     `json:"connections"`
	ActiveQueries    int     `json:"active_queries"`
	SlowQueries      int64   `json:"slow_queries"`
	AvgQueryTime     float64 `json:"avg_query_time"`
	ConnectionsUsed  int     `json:"connections_used"`
	ConnectionsIdle  int     `json:"connections_idle"`
	ConnectionsMax   int     `json:"connections_max"`
}

// RedisStats Redis 统计
type RedisStats struct {
	Connections     int     `json:"connections"`
	MemoryUsed      int64   `json:"memory_used"`
	MemoryMax       int64   `json:"memory_max"`
	MemoryPercent   float64 `json:"memory_percent"`
	KeyCount        int64   `json:"key_count"`
	HitRate         float64 `json:"hit_rate"`
	OpsPerSecond    int64   `json:"ops_per_second"`
}

// ModelStats 模型统计
type ModelStats struct {
	TotalModels       int     `json:"total_models"`
	ActiveModels      int     `json:"active_models"`
	InferenceRequests int64   `json:"inference_requests"`
	InferenceLatency  float64 `json:"inference_latency"`
	InferenceErrors   int64   `json:"inference_errors"`
	SuccessRate       float64 `json:"success_rate"`
}

// AlertStats 告警统计
type AlertStats struct {
	TotalAlerts    int64 `json:"total_alerts"`
	ActiveAlerts   int64 `json:"active_alerts"`
	CriticalAlerts int64 `json:"critical_alerts"`
	WarningAlerts  int64 `json:"warning_alerts"`
	InfoAlerts     int64 `json:"info_alerts"`
	ResolvedAlerts int64 `json:"resolved_alerts"`
}

// PerformanceMetrics 性能指标
type PerformanceMetrics struct {
	RequestsPerSecond float64 `json:"requests_per_second"`
	AvgResponseTime   float64 `json:"avg_response_time"`
	P95ResponseTime   float64 `json:"p95_response_time"`
	P99ResponseTime   float64 `json:"p99_response_time"`
	ErrorRate         float64 `json:"error_rate"`
	Throughput        float64 `json:"throughput"`
}

// ServiceEndpoint 服务端点
type ServiceEndpoint struct {
	Name        string    `json:"name"`
	URL         string    `json:"url"`
	Status      string    `json:"status"`
	LastCheck   time.Time `json:"last_check"`
	ResponseTime time.Duration `json:"response_time"`
	Error       string    `json:"error,omitempty"`
}

// ConfigInfo 配置信息
type ConfigInfo struct {
	Environment   string                 `json:"environment"`
	Version       string                 `json:"version"`
	BuildTime     string                 `json:"build_time"`
	GitCommit     string                 `json:"git_commit"`
	ConfigFile    string                 `json:"config_file"`
	LogLevel      string                 `json:"log_level"`
	Features      map[string]bool        `json:"features"`
	Settings      map[string]interface{} `json:"settings"`
}

// SecurityInfo 安全信息
type SecurityInfo struct {
	TLSEnabled       bool      `json:"tls_enabled"`
	AuthEnabled      bool      `json:"auth_enabled"`
	RateLimitEnabled bool      `json:"rate_limit_enabled"`
	LastSecurityScan time.Time `json:"last_security_scan"`
	Vulnerabilities  int       `json:"vulnerabilities"`
	SecurityLevel    string    `json:"security_level"`
}

// BackupInfo 备份信息
type BackupInfo struct {
	LastBackup    time.Time `json:"last_backup"`
	BackupSize    int64     `json:"backup_size"`
	BackupStatus  string    `json:"backup_status"`
	BackupCount   int       `json:"backup_count"`
	RetentionDays int       `json:"retention_days"`
}

// MaintenanceInfo 维护信息
type MaintenanceInfo struct {
	MaintenanceMode   bool      `json:"maintenance_mode"`
	LastMaintenance   time.Time `json:"last_maintenance"`
	NextMaintenance   time.Time `json:"next_maintenance"`
	MaintenanceWindow string    `json:"maintenance_window"`
	DowntimeMinutes   int       `json:"downtime_minutes"`
}

// ClusterInfo 集群信息（为将来扩展准备）
type ClusterInfo struct {
	NodeID       string                 `json:"node_id"`
	NodeRole     string                 `json:"node_role"`
	ClusterSize  int                    `json:"cluster_size"`
	LeaderNode   string                 `json:"leader_node"`
	Nodes        []NodeInfo             `json:"nodes"`
	ClusterState string                 `json:"cluster_state"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// NodeInfo 节点信息
type NodeInfo struct {
	ID           string    `json:"id"`
	Name         string    `json:"name"`
	Address      string    `json:"address"`
	Role         string    `json:"role"`
	Status       string    `json:"status"`
	LastSeen     time.Time `json:"last_seen"`
	Version      string    `json:"version"`
	Resources    ResourceUsage `json:"resources"`
}

// EventInfo 事件信息
type EventInfo struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Level       string                 `json:"level"`
	Message     string                 `json:"message"`
	Source      string                 `json:"source"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
	Acknowledged bool                  `json:"acknowledged"`
}

// AuditInfo 审计信息
type AuditInfo struct {
	TotalEvents    int64     `json:"total_events"`
	LastEvent      time.Time `json:"last_event"`
	EventTypes     map[string]int64 `json:"event_types"`
	RetentionDays  int       `json:"retention_days"`
	AuditEnabled   bool      `json:"audit_enabled"`
}

// LicenseInfo 许可证信息
type LicenseInfo struct {
	LicenseType   string    `json:"license_type"`
	ExpiryDate    time.Time `json:"expiry_date"`
	MaxUsers      int       `json:"max_users"`
	MaxModels     int       `json:"max_models"`
	Features      []string  `json:"features"`
	Valid         bool      `json:"valid"`
	DaysRemaining int       `json:"days_remaining"`
}

// IntegrationInfo 集成信息
type IntegrationInfo struct {
	Name         string                 `json:"name"`
	Type         string                 `json:"type"`
	Status       string                 `json:"status"`
	Version      string                 `json:"version"`
	LastSync     time.Time              `json:"last_sync"`
	Configuration map[string]interface{} `json:"configuration"`
	Enabled      bool                   `json:"enabled"`
}

// ComplianceInfo 合规信息
type ComplianceInfo struct {
	Standards     []string  `json:"standards"`
	LastAudit     time.Time `json:"last_audit"`
	ComplianceScore float64 `json:"compliance_score"`
	Violations    int       `json:"violations"`
	Recommendations []string `json:"recommendations"`
}

// CapacityInfo 容量信息
type CapacityInfo struct {
	CurrentLoad    float64 `json:"current_load"`
	MaxCapacity    int     `json:"max_capacity"`
	UsedCapacity   int     `json:"used_capacity"`
	AvailableCapacity int  `json:"available_capacity"`
	PredictedLoad  float64 `json:"predicted_load"`
	ScalingNeeded  bool    `json:"scaling_needed"`
}

// QualityMetrics 质量指标
type QualityMetrics struct {
	Accuracy      float64 `json:"accuracy"`
	Precision     float64 `json:"precision"`
	Recall        float64 `json:"recall"`
	F1Score       float64 `json:"f1_score"`
	Latency       float64 `json:"latency"`
	Throughput    float64 `json:"throughput"`
	ErrorRate     float64 `json:"error_rate"`
	DataQuality   float64 `json:"data_quality"`
}

// TrendData 趋势数据
type TrendData struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
	Metric    string    `json:"metric"`
	Unit      string    `json:"unit"`
}

// Forecast 预测数据
type Forecast struct {
	Metric      string      `json:"metric"`
	Predictions []TrendData `json:"predictions"`
	Confidence  float64     `json:"confidence"`
	Model       string      `json:"model"`
	GeneratedAt time.Time   `json:"generated_at"`
}

// Recommendation 推荐
type Recommendation struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Priority    string                 `json:"priority"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Action      string                 `json:"action"`
	Impact      string                 `json:"impact"`
	Effort      string                 `json:"effort"`
	Metadata    map[string]interface{} `json:"metadata"`
	CreatedAt   time.Time              `json:"created_at"`
	Status      string                 `json:"status"`
}