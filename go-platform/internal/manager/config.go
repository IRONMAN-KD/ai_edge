package manager

import (
	"time"
)

// ManagerConfig 管理器配置
type ManagerConfig struct {
	Enabled         bool                   `yaml:"enabled" json:"enabled"`
	TaskScheduler   *TaskSchedulerConfig   `yaml:"task_scheduler" json:"task_scheduler"`
	Monitor         *MonitorConfig         `yaml:"monitor" json:"monitor"`
	AlertManager    *AlertManagerConfig    `yaml:"alert_manager" json:"alert_manager"`
	HealthChecker   *HealthCheckerConfig   `yaml:"health_checker" json:"health_checker"`
	GracefulTimeout time.Duration          `yaml:"graceful_timeout" json:"graceful_timeout"`
	ShutdownTimeout time.Duration          `yaml:"shutdown_timeout" json:"shutdown_timeout"`
	Metrics         *MetricsConfig         `yaml:"metrics" json:"metrics"`
	Logging         *LoggingConfig         `yaml:"logging" json:"logging"`
	Security        *SecurityConfig        `yaml:"security" json:"security"`
	Performance     *PerformanceConfig     `yaml:"performance" json:"performance"`
	Features        map[string]bool        `yaml:"features" json:"features"`
	Extensions      map[string]interface{} `yaml:"extensions" json:"extensions"`
}

// TaskSchedulerConfig 任务调度器配置
type TaskSchedulerConfig struct {
	Enabled           bool          `yaml:"enabled" json:"enabled"`
	WorkerPoolSize    int           `yaml:"worker_pool_size" json:"worker_pool_size"`
	QueueSize         int           `yaml:"queue_size" json:"queue_size"`
	TaskTimeout       time.Duration `yaml:"task_timeout" json:"task_timeout"`
	MaxRetries        int           `yaml:"max_retries" json:"max_retries"`
	RetryDelay        time.Duration `yaml:"retry_delay" json:"retry_delay"`
	CleanupInterval   time.Duration `yaml:"cleanup_interval" json:"cleanup_interval"`
	MetricsInterval   time.Duration `yaml:"metrics_interval" json:"metrics_interval"`
	PersistTasks      bool          `yaml:"persist_tasks" json:"persist_tasks"`
	TaskRetention     time.Duration `yaml:"task_retention" json:"task_retention"`
	ConcurrencyLimit  int           `yaml:"concurrency_limit" json:"concurrency_limit"`
	PriorityEnabled   bool          `yaml:"priority_enabled" json:"priority_enabled"`
	DeadLetterQueue   bool          `yaml:"dead_letter_queue" json:"dead_letter_queue"`
	BatchProcessing   *BatchConfig  `yaml:"batch_processing" json:"batch_processing"`
	SchedulePatterns  []string      `yaml:"schedule_patterns" json:"schedule_patterns"`
}

// MonitorConfig 监控配置
type MonitorConfig struct {
	Enabled             bool                   `yaml:"enabled" json:"enabled"`
	Interval            time.Duration          `yaml:"interval" json:"interval"`
	MetricsRetention    time.Duration          `yaml:"metrics_retention" json:"metrics_retention"`
	SystemMetrics       *SystemMetricsConfig   `yaml:"system_metrics" json:"system_metrics"`
	ApplicationMetrics  *AppMetricsConfig      `yaml:"application_metrics" json:"application_metrics"`
	DatabaseMetrics     *DatabaseMetricsConfig `yaml:"database_metrics" json:"database_metrics"`
	RedisMetrics        *RedisMetricsConfig    `yaml:"redis_metrics" json:"redis_metrics"`
	ModelMetrics        *ModelMetricsConfig    `yaml:"model_metrics" json:"model_metrics"`
	CustomMetrics       []CustomMetricConfig   `yaml:"custom_metrics" json:"custom_metrics"`
	Thresholds          map[string]float64     `yaml:"thresholds" json:"thresholds"`
	Aggregation         *AggregationConfig     `yaml:"aggregation" json:"aggregation"`
	Export              *ExportConfig          `yaml:"export" json:"export"`
	Storage             *StorageConfig         `yaml:"storage" json:"storage"`
}

// AlertManagerConfig 告警管理器配置
type AlertManagerConfig struct {
	Enabled           bool                    `yaml:"enabled" json:"enabled"`
	RulesFile         string                  `yaml:"rules_file" json:"rules_file"`
	RulesReloadInterval time.Duration         `yaml:"rules_reload_interval" json:"rules_reload_interval"`
	EvaluationInterval time.Duration          `yaml:"evaluation_interval" json:"evaluation_interval"`
	AlertRetention    time.Duration           `yaml:"alert_retention" json:"alert_retention"`
	CooldownPeriod    time.Duration           `yaml:"cooldown_period" json:"cooldown_period"`
	Grouping          *GroupingConfig         `yaml:"grouping" json:"grouping"`
	Suppression       *SuppressionConfig      `yaml:"suppression" json:"suppression"`
	Notifiers         map[string]NotifierConfig `yaml:"notifiers" json:"notifiers"`
	Routing           *RoutingConfig          `yaml:"routing" json:"routing"`
	Templates         *TemplateConfig         `yaml:"templates" json:"templates"`
	Webhooks          []WebhookConfig         `yaml:"webhooks" json:"webhooks"`
	Escalation        *EscalationConfig       `yaml:"escalation" json:"escalation"`
}

// HealthCheckerConfig 健康检查器配置
type HealthCheckerConfig struct {
	Enabled         bool                    `yaml:"enabled" json:"enabled"`
	Interval        time.Duration           `yaml:"interval" json:"interval"`
	Timeout         time.Duration           `yaml:"timeout" json:"timeout"`
	Retries         int                     `yaml:"retries" json:"retries"`
	FailureThreshold int                    `yaml:"failure_threshold" json:"failure_threshold"`
	SuccessThreshold int                    `yaml:"success_threshold" json:"success_threshold"`
	Checks          map[string]HealthCheckConfig `yaml:"checks" json:"checks"`
	Endpoints       []EndpointConfig        `yaml:"endpoints" json:"endpoints"`
	Dependencies    []DependencyConfig      `yaml:"dependencies" json:"dependencies"`
	Notifications   *NotificationConfig     `yaml:"notifications" json:"notifications"`
	Recovery        *RecoveryConfig         `yaml:"recovery" json:"recovery"`
}

// BatchConfig 批处理配置
type BatchConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Size        int           `yaml:"size" json:"size"`
	Timeout     time.Duration `yaml:"timeout" json:"timeout"`
	MaxWait     time.Duration `yaml:"max_wait" json:"max_wait"`
	Concurrency int           `yaml:"concurrency" json:"concurrency"`
}

// SystemMetricsConfig 系统指标配置
type SystemMetricsConfig struct {
	Enabled         bool     `yaml:"enabled" json:"enabled"`
	CPU             bool     `yaml:"cpu" json:"cpu"`
	Memory          bool     `yaml:"memory" json:"memory"`
	Disk            bool     `yaml:"disk" json:"disk"`
	Network         bool     `yaml:"network" json:"network"`
	Process         bool     `yaml:"process" json:"process"`
	Goroutines      bool     `yaml:"goroutines" json:"goroutines"`
	GC              bool     `yaml:"gc" json:"gc"`
	Interfaces      []string `yaml:"interfaces" json:"interfaces"`
	MountPoints     []string `yaml:"mount_points" json:"mount_points"`
}

// AppMetricsConfig 应用指标配置
type AppMetricsConfig struct {
	Enabled         bool     `yaml:"enabled" json:"enabled"`
	HTTP            bool     `yaml:"http" json:"http"`
	GRPC            bool     `yaml:"grpc" json:"grpc"`
	Database        bool     `yaml:"database" json:"database"`
	Cache           bool     `yaml:"cache" json:"cache"`
	Queue           bool     `yaml:"queue" json:"queue"`
	Custom          bool     `yaml:"custom" json:"custom"`
	Endpoints       []string `yaml:"endpoints" json:"endpoints"`
	ExcludePatterns []string `yaml:"exclude_patterns" json:"exclude_patterns"`
}

// DatabaseMetricsConfig 数据库指标配置
type DatabaseMetricsConfig struct {
	Enabled         bool     `yaml:"enabled" json:"enabled"`
	Connections     bool     `yaml:"connections" json:"connections"`
	Queries         bool     `yaml:"queries" json:"queries"`
	SlowQueries     bool     `yaml:"slow_queries" json:"slow_queries"`
	Deadlocks       bool     `yaml:"deadlocks" json:"deadlocks"`
	TableSizes      bool     `yaml:"table_sizes" json:"table_sizes"`
	IndexUsage      bool     `yaml:"index_usage" json:"index_usage"`
	Replication     bool     `yaml:"replication" json:"replication"`
	Tables          []string `yaml:"tables" json:"tables"`
	SlowQueryThreshold time.Duration `yaml:"slow_query_threshold" json:"slow_query_threshold"`
}

// RedisMetricsConfig Redis指标配置
type RedisMetricsConfig struct {
	Enabled         bool     `yaml:"enabled" json:"enabled"`
	Connections     bool     `yaml:"connections" json:"connections"`
	Memory          bool     `yaml:"memory" json:"memory"`
	Keys            bool     `yaml:"keys" json:"keys"`
	Commands        bool     `yaml:"commands" json:"commands"`
	Replication     bool     `yaml:"replication" json:"replication"`
	Persistence     bool     `yaml:"persistence" json:"persistence"`
	Cluster         bool     `yaml:"cluster" json:"cluster"`
	KeyPatterns     []string `yaml:"key_patterns" json:"key_patterns"`
	Databases       []int    `yaml:"databases" json:"databases"`
}

// ModelMetricsConfig 模型指标配置
type ModelMetricsConfig struct {
	Enabled         bool     `yaml:"enabled" json:"enabled"`
	Inferences      bool     `yaml:"inferences" json:"inferences"`
	Latency         bool     `yaml:"latency" json:"latency"`
	Accuracy        bool     `yaml:"accuracy" json:"accuracy"`
	Throughput      bool     `yaml:"throughput" json:"throughput"`
	Errors          bool     `yaml:"errors" json:"errors"`
	ResourceUsage   bool     `yaml:"resource_usage" json:"resource_usage"`
	ModelVersions   bool     `yaml:"model_versions" json:"model_versions"`
	Models          []string `yaml:"models" json:"models"`
	MetricTypes     []string `yaml:"metric_types" json:"metric_types"`
}

// CustomMetricConfig 自定义指标配置
type CustomMetricConfig struct {
	Name        string            `yaml:"name" json:"name"`
	Type        string            `yaml:"type" json:"type"`
	Description string            `yaml:"description" json:"description"`
	Labels      []string          `yaml:"labels" json:"labels"`
	Query       string            `yaml:"query" json:"query"`
	Interval    time.Duration     `yaml:"interval" json:"interval"`
	Timeout     time.Duration     `yaml:"timeout" json:"timeout"`
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	Parameters  map[string]string `yaml:"parameters" json:"parameters"`
}

// AggregationConfig 聚合配置
type AggregationConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Interval    time.Duration `yaml:"interval" json:"interval"`
	Retention   time.Duration `yaml:"retention" json:"retention"`
	Functions   []string      `yaml:"functions" json:"functions"`
	GroupBy     []string      `yaml:"group_by" json:"group_by"`
	Downsampling map[string]time.Duration `yaml:"downsampling" json:"downsampling"`
}

// ExportConfig 导出配置
type ExportConfig struct {
	Enabled     bool                   `yaml:"enabled" json:"enabled"`
	Prometheus  *PrometheusConfig      `yaml:"prometheus" json:"prometheus"`
	InfluxDB    *InfluxDBConfig        `yaml:"influxdb" json:"influxdb"`
	Elasticsearch *ElasticsearchConfig `yaml:"elasticsearch" json:"elasticsearch"`
	Custom      []CustomExportConfig   `yaml:"custom" json:"custom"`
}

// StorageConfig 存储配置
type StorageConfig struct {
	Type        string        `yaml:"type" json:"type"`
	Path        string        `yaml:"path" json:"path"`
	Retention   time.Duration `yaml:"retention" json:"retention"`
	Compression bool          `yaml:"compression" json:"compression"`
	Encryption  bool          `yaml:"encryption" json:"encryption"`
	Backup      *BackupConfig `yaml:"backup" json:"backup"`
}

// GroupingConfig 分组配置
type GroupingConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	By          []string      `yaml:"by" json:"by"`
	Wait        time.Duration `yaml:"wait" json:"wait"`
	Interval    time.Duration `yaml:"interval" json:"interval"`
	RepeatInterval time.Duration `yaml:"repeat_interval" json:"repeat_interval"`
}

// SuppressionConfig 抑制配置
type SuppressionConfig struct {
	Enabled     bool                    `yaml:"enabled" json:"enabled"`
	Rules       []SuppressionRule       `yaml:"rules" json:"rules"`
	DefaultTTL  time.Duration           `yaml:"default_ttl" json:"default_ttl"`
	MaxTTL      time.Duration           `yaml:"max_ttl" json:"max_ttl"`
}

// SuppressionRule 抑制规则
type SuppressionRule struct {
	Name        string            `yaml:"name" json:"name"`
	Matchers    map[string]string `yaml:"matchers" json:"matchers"`
	TTL         time.Duration     `yaml:"ttl" json:"ttl"`
	Enabled     bool              `yaml:"enabled" json:"enabled"`
}

// NotifierConfig 通知器配置
type NotifierConfig struct {
	Type        string                 `yaml:"type" json:"type"`
	Enabled     bool                   `yaml:"enabled" json:"enabled"`
	Settings    map[string]interface{} `yaml:"settings" json:"settings"`
	Timeout     time.Duration          `yaml:"timeout" json:"timeout"`
	Retries     int                    `yaml:"retries" json:"retries"`
	RetryDelay  time.Duration          `yaml:"retry_delay" json:"retry_delay"`
	RateLimit   *RateLimitConfig       `yaml:"rate_limit" json:"rate_limit"`
	Filters     []FilterConfig         `yaml:"filters" json:"filters"`
	Template    string                 `yaml:"template" json:"template"`
}

// RoutingConfig 路由配置
type RoutingConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Rules       []RoutingRule `yaml:"rules" json:"rules"`
	Default     []string      `yaml:"default" json:"default"`
	Fallback    []string      `yaml:"fallback" json:"fallback"`
}

// RoutingRule 路由规则
type RoutingRule struct {
	Name        string            `yaml:"name" json:"name"`
	Matchers    map[string]string `yaml:"matchers" json:"matchers"`
	Notifiers   []string          `yaml:"notifiers" json:"notifiers"`
	Continue    bool              `yaml:"continue" json:"continue"`
	Enabled     bool              `yaml:"enabled" json:"enabled"`
}

// TemplateConfig 模板配置
type TemplateConfig struct {
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	Path        string            `yaml:"path" json:"path"`
	Templates   map[string]string `yaml:"templates" json:"templates"`
	Functions   []string          `yaml:"functions" json:"functions"`
	Reload      bool              `yaml:"reload" json:"reload"`
}

// WebhookConfig Webhook配置
type WebhookConfig struct {
	Name        string            `yaml:"name" json:"name"`
	URL         string            `yaml:"url" json:"url"`
	Method      string            `yaml:"method" json:"method"`
	Headers     map[string]string `yaml:"headers" json:"headers"`
	Timeout     time.Duration     `yaml:"timeout" json:"timeout"`
	Retries     int               `yaml:"retries" json:"retries"`
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	TLS         *TLSConfig        `yaml:"tls" json:"tls"`
	Auth        *AuthConfig       `yaml:"auth" json:"auth"`
}

// EscalationConfig 升级配置
type EscalationConfig struct {
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	Levels      []EscalationLevel `yaml:"levels" json:"levels"`
	MaxLevel    int               `yaml:"max_level" json:"max_level"`
	Cooldown    time.Duration     `yaml:"cooldown" json:"cooldown"`
}

// EscalationLevel 升级级别
type EscalationLevel struct {
	Level       int           `yaml:"level" json:"level"`
	Delay       time.Duration `yaml:"delay" json:"delay"`
	Notifiers   []string      `yaml:"notifiers" json:"notifiers"`
	Conditions  []string      `yaml:"conditions" json:"conditions"`
	Enabled     bool          `yaml:"enabled" json:"enabled"`
}

// HealthCheckConfig 健康检查配置
type HealthCheckConfig struct {
	Type        string            `yaml:"type" json:"type"`
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	Interval    time.Duration     `yaml:"interval" json:"interval"`
	Timeout     time.Duration     `yaml:"timeout" json:"timeout"`
	Retries     int               `yaml:"retries" json:"retries"`
	Parameters  map[string]string `yaml:"parameters" json:"parameters"`
	Thresholds  map[string]float64 `yaml:"thresholds" json:"thresholds"`
	DependsOn   []string          `yaml:"depends_on" json:"depends_on"`
}

// EndpointConfig 端点配置
type EndpointConfig struct {
	Name        string            `yaml:"name" json:"name"`
	URL         string            `yaml:"url" json:"url"`
	Method      string            `yaml:"method" json:"method"`
	Headers     map[string]string `yaml:"headers" json:"headers"`
	Body        string            `yaml:"body" json:"body"`
	ExpectedStatus []int          `yaml:"expected_status" json:"expected_status"`
	ExpectedBody string           `yaml:"expected_body" json:"expected_body"`
	Timeout     time.Duration     `yaml:"timeout" json:"timeout"`
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	TLS         *TLSConfig        `yaml:"tls" json:"tls"`
}

// DependencyConfig 依赖配置
type DependencyConfig struct {
	Name        string        `yaml:"name" json:"name"`
	Type        string        `yaml:"type" json:"type"`
	Address     string        `yaml:"address" json:"address"`
	Timeout     time.Duration `yaml:"timeout" json:"timeout"`
	Critical    bool          `yaml:"critical" json:"critical"`
	Enabled     bool          `yaml:"enabled" json:"enabled"`
}

// NotificationConfig 通知配置
type NotificationConfig struct {
	Enabled     bool     `yaml:"enabled" json:"enabled"`
	Channels    []string `yaml:"channels" json:"channels"`
	OnFailure   bool     `yaml:"on_failure" json:"on_failure"`
	OnRecovery  bool     `yaml:"on_recovery" json:"on_recovery"`
	OnDegraded  bool     `yaml:"on_degraded" json:"on_degraded"`
}

// RecoveryConfig 恢复配置
type RecoveryConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Actions     []string      `yaml:"actions" json:"actions"`
	Timeout     time.Duration `yaml:"timeout" json:"timeout"`
	Retries     int           `yaml:"retries" json:"retries"`
	Cooldown    time.Duration `yaml:"cooldown" json:"cooldown"`
}

// MetricsConfig 指标配置
type MetricsConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Path        string        `yaml:"path" json:"path"`
	Port        int           `yaml:"port" json:"port"`
	Interval    time.Duration `yaml:"interval" json:"interval"`
	Retention   time.Duration `yaml:"retention" json:"retention"`
	Namespace   string        `yaml:"namespace" json:"namespace"`
	Subsystem   string        `yaml:"subsystem" json:"subsystem"`
	Labels      map[string]string `yaml:"labels" json:"labels"`
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Level       string        `yaml:"level" json:"level"`
	Format      string        `yaml:"format" json:"format"`
	Output      string        `yaml:"output" json:"output"`
	File        string        `yaml:"file" json:"file"`
	MaxSize     int           `yaml:"max_size" json:"max_size"`
	MaxBackups  int           `yaml:"max_backups" json:"max_backups"`
	MaxAge      int           `yaml:"max_age" json:"max_age"`
	Compress    bool          `yaml:"compress" json:"compress"`
	Rotation    *RotationConfig `yaml:"rotation" json:"rotation"`
	Structured  bool          `yaml:"structured" json:"structured"`
	Sampling    *SamplingConfig `yaml:"sampling" json:"sampling"`
}

// SecurityConfig 安全配置
type SecurityConfig struct {
	Enabled         bool              `yaml:"enabled" json:"enabled"`
	Authentication  *AuthConfig       `yaml:"authentication" json:"authentication"`
	Authorization   *AuthzConfig      `yaml:"authorization" json:"authorization"`
	Encryption      *EncryptionConfig `yaml:"encryption" json:"encryption"`
	TLS             *TLSConfig        `yaml:"tls" json:"tls"`
	RateLimit       *RateLimitConfig  `yaml:"rate_limit" json:"rate_limit"`
	Audit           *AuditConfig      `yaml:"audit" json:"audit"`
	Firewall        *FirewallConfig   `yaml:"firewall" json:"firewall"`
	Secrets         *SecretsConfig    `yaml:"secrets" json:"secrets"`
}

// PerformanceConfig 性能配置
type PerformanceConfig struct {
	Enabled         bool              `yaml:"enabled" json:"enabled"`
	Profiling       *ProfilingConfig  `yaml:"profiling" json:"profiling"`
	Caching         *CachingConfig    `yaml:"caching" json:"caching"`
	Compression     *CompressionConfig `yaml:"compression" json:"compression"`
	ConnectionPool  *PoolConfig       `yaml:"connection_pool" json:"connection_pool"`
	Optimizations   map[string]bool   `yaml:"optimizations" json:"optimizations"`
	Limits          *LimitsConfig     `yaml:"limits" json:"limits"`
	Tuning          *TuningConfig     `yaml:"tuning" json:"tuning"`
}

// 辅助配置结构

// PrometheusConfig Prometheus配置
type PrometheusConfig struct {
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	Endpoint    string            `yaml:"endpoint" json:"endpoint"`
	Namespace   string            `yaml:"namespace" json:"namespace"`
	Labels      map[string]string `yaml:"labels" json:"labels"`
	Timeout     time.Duration     `yaml:"timeout" json:"timeout"`
}

// InfluxDBConfig InfluxDB配置
type InfluxDBConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	URL         string        `yaml:"url" json:"url"`
	Database    string        `yaml:"database" json:"database"`
	Username    string        `yaml:"username" json:"username"`
	Password    string        `yaml:"password" json:"password"`
	Retention   string        `yaml:"retention" json:"retention"`
	Precision   string        `yaml:"precision" json:"precision"`
	Timeout     time.Duration `yaml:"timeout" json:"timeout"`
	BatchSize   int           `yaml:"batch_size" json:"batch_size"`
}

// ElasticsearchConfig Elasticsearch配置
type ElasticsearchConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	URLs        []string      `yaml:"urls" json:"urls"`
	Index       string        `yaml:"index" json:"index"`
	Username    string        `yaml:"username" json:"username"`
	Password    string        `yaml:"password" json:"password"`
	Timeout     time.Duration `yaml:"timeout" json:"timeout"`
	BatchSize   int           `yaml:"batch_size" json:"batch_size"`
	FlushInterval time.Duration `yaml:"flush_interval" json:"flush_interval"`
}

// CustomExportConfig 自定义导出配置
type CustomExportConfig struct {
	Name        string                 `yaml:"name" json:"name"`
	Type        string                 `yaml:"type" json:"type"`
	Enabled     bool                   `yaml:"enabled" json:"enabled"`
	Settings    map[string]interface{} `yaml:"settings" json:"settings"`
	Interval    time.Duration          `yaml:"interval" json:"interval"`
	Timeout     time.Duration          `yaml:"timeout" json:"timeout"`
}

// BackupConfig 备份配置
type BackupConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Interval    time.Duration `yaml:"interval" json:"interval"`
	Retention   time.Duration `yaml:"retention" json:"retention"`
	Path        string        `yaml:"path" json:"path"`
	Compression bool          `yaml:"compression" json:"compression"`
	Encryption  bool          `yaml:"encryption" json:"encryption"`
}

// RateLimitConfig 限流配置
type RateLimitConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Rate        int           `yaml:"rate" json:"rate"`
	Burst       int           `yaml:"burst" json:"burst"`
	Window      time.Duration `yaml:"window" json:"window"`
	Strategy    string        `yaml:"strategy" json:"strategy"`
}

// FilterConfig 过滤器配置
type FilterConfig struct {
	Type        string            `yaml:"type" json:"type"`
	Parameters  map[string]string `yaml:"parameters" json:"parameters"`
	Enabled     bool              `yaml:"enabled" json:"enabled"`
}

// TLSConfig TLS配置
type TLSConfig struct {
	Enabled     bool   `yaml:"enabled" json:"enabled"`
	CertFile    string `yaml:"cert_file" json:"cert_file"`
	KeyFile     string `yaml:"key_file" json:"key_file"`
	CAFile      string `yaml:"ca_file" json:"ca_file"`
	Insecure    bool   `yaml:"insecure" json:"insecure"`
	ServerName  string `yaml:"server_name" json:"server_name"`
}

// AuthConfig 认证配置
type AuthConfig struct {
	Type        string            `yaml:"type" json:"type"`
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	Parameters  map[string]string `yaml:"parameters" json:"parameters"`
}

// AuthzConfig 授权配置
type AuthzConfig struct {
	Enabled     bool              `yaml:"enabled" json:"enabled"`
	Provider    string            `yaml:"provider" json:"provider"`
	Rules       []AuthzRule       `yaml:"rules" json:"rules"`
	Default     string            `yaml:"default" json:"default"`
}

// AuthzRule 授权规则
type AuthzRule struct {
	Resource    string   `yaml:"resource" json:"resource"`
	Actions     []string `yaml:"actions" json:"actions"`
	Subjects    []string `yaml:"subjects" json:"subjects"`
	Effect      string   `yaml:"effect" json:"effect"`
	Conditions  []string `yaml:"conditions" json:"conditions"`
}

// EncryptionConfig 加密配置
type EncryptionConfig struct {
	Enabled     bool   `yaml:"enabled" json:"enabled"`
	Algorithm   string `yaml:"algorithm" json:"algorithm"`
	KeyFile     string `yaml:"key_file" json:"key_file"`
	KeySize     int    `yaml:"key_size" json:"key_size"`
}

// AuditConfig 审计配置
type AuditConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Level       string        `yaml:"level" json:"level"`
	Output      string        `yaml:"output" json:"output"`
	Retention   time.Duration `yaml:"retention" json:"retention"`
	Format      string        `yaml:"format" json:"format"`
}

// FirewallConfig 防火墙配置
type FirewallConfig struct {
	Enabled     bool     `yaml:"enabled" json:"enabled"`
	Whitelist   []string `yaml:"whitelist" json:"whitelist"`
	Blacklist   []string `yaml:"blacklist" json:"blacklist"`
	Rules       []string `yaml:"rules" json:"rules"`
}

// SecretsConfig 密钥配置
type SecretsConfig struct {
	Provider    string            `yaml:"provider" json:"provider"`
	Path        string            `yaml:"path" json:"path"`
	Encryption  bool              `yaml:"encryption" json:"encryption"`
	Rotation    bool              `yaml:"rotation" json:"rotation"`
	Parameters  map[string]string `yaml:"parameters" json:"parameters"`
}

// ProfilingConfig 性能分析配置
type ProfilingConfig struct {
	Enabled     bool   `yaml:"enabled" json:"enabled"`
	CPU         bool   `yaml:"cpu" json:"cpu"`
	Memory      bool   `yaml:"memory" json:"memory"`
	Goroutine   bool   `yaml:"goroutine" json:"goroutine"`
	Block       bool   `yaml:"block" json:"block"`
	Mutex       bool   `yaml:"mutex" json:"mutex"`
	Trace       bool   `yaml:"trace" json:"trace"`
	Port        int    `yaml:"port" json:"port"`
	Path        string `yaml:"path" json:"path"`
}

// CachingConfig 缓存配置
type CachingConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Provider    string        `yaml:"provider" json:"provider"`
	Size        int           `yaml:"size" json:"size"`
	TTL         time.Duration `yaml:"ttl" json:"ttl"`
	Eviction    string        `yaml:"eviction" json:"eviction"`
	Compression bool          `yaml:"compression" json:"compression"`
}

// CompressionConfig 压缩配置
type CompressionConfig struct {
	Enabled     bool   `yaml:"enabled" json:"enabled"`
	Algorithm   string `yaml:"algorithm" json:"algorithm"`
	Level       int    `yaml:"level" json:"level"`
	Threshold   int    `yaml:"threshold" json:"threshold"`
}

// PoolConfig 连接池配置
type PoolConfig struct {
	MaxSize     int           `yaml:"max_size" json:"max_size"`
	MinSize     int           `yaml:"min_size" json:"min_size"`
	MaxIdle     int           `yaml:"max_idle" json:"max_idle"`
	IdleTimeout time.Duration `yaml:"idle_timeout" json:"idle_timeout"`
	MaxLifetime time.Duration `yaml:"max_lifetime" json:"max_lifetime"`
}

// LimitsConfig 限制配置
type LimitsConfig struct {
	MaxMemory       int64         `yaml:"max_memory" json:"max_memory"`
	MaxCPU          float64       `yaml:"max_cpu" json:"max_cpu"`
	MaxConnections  int           `yaml:"max_connections" json:"max_connections"`
	MaxRequests     int           `yaml:"max_requests" json:"max_requests"`
	MaxFileSize     int64         `yaml:"max_file_size" json:"max_file_size"`
	MaxRequestSize  int64         `yaml:"max_request_size" json:"max_request_size"`
	MaxResponseSize int64         `yaml:"max_response_size" json:"max_response_size"`
	Timeout         time.Duration `yaml:"timeout" json:"timeout"`
}

// TuningConfig 调优配置
type TuningConfig struct {
	GCPercent       int           `yaml:"gc_percent" json:"gc_percent"`
	MaxProcs        int           `yaml:"max_procs" json:"max_procs"`
	ReadBufferSize  int           `yaml:"read_buffer_size" json:"read_buffer_size"`
	WriteBufferSize int           `yaml:"write_buffer_size" json:"write_buffer_size"`
	KeepAlive       time.Duration `yaml:"keep_alive" json:"keep_alive"`
	IdleTimeout     time.Duration `yaml:"idle_timeout" json:"idle_timeout"`
}

// RotationConfig 日志轮转配置
type RotationConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	MaxSize     int           `yaml:"max_size" json:"max_size"`
	MaxAge      time.Duration `yaml:"max_age" json:"max_age"`
	MaxBackups  int           `yaml:"max_backups" json:"max_backups"`
	Compress    bool          `yaml:"compress" json:"compress"`
}

// SamplingConfig 采样配置
type SamplingConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	Initial     int           `yaml:"initial" json:"initial"`
	Thereafter  int           `yaml:"thereafter" json:"thereafter"`
	Tick        time.Duration `yaml:"tick" json:"tick"`
}

// DefaultManagerConfig 返回默认管理器配置
func DefaultManagerConfig() *ManagerConfig {
	return &ManagerConfig{
		Enabled: true,
		TaskScheduler: &TaskSchedulerConfig{
			Enabled:          true,
			WorkerPoolSize:   DefaultWorkerPoolSize,
			QueueSize:        DefaultQueueSize,
			TaskTimeout:      DefaultTaskTimeout,
			MaxRetries:       DefaultTaskRetries,
			RetryDelay:       DefaultRetryDelay,
			CleanupInterval:  DefaultCleanupInterval,
			MetricsInterval:  DefaultMonitorInterval,
			PersistTasks:     true,
			TaskRetention:    DefaultDataRetention,
			ConcurrencyLimit: DefaultWorkerPoolSize * 2,
			PriorityEnabled:  true,
			DeadLetterQueue:  true,
			BatchProcessing: &BatchConfig{
				Enabled:     true,
				Size:        DefaultBatchSize,
				Timeout:     DefaultBatchTimeout,
				MaxWait:     DefaultBatchMaxWait,
				Concurrency: 5,
			},
		},
		Monitor: &MonitorConfig{
			Enabled:          true,
			Interval:         DefaultMonitorInterval,
			MetricsRetention: DefaultMetricsRetention,
			SystemMetrics: &SystemMetricsConfig{
				Enabled:    true,
				CPU:        true,
				Memory:     true,
				Disk:       true,
				Network:    true,
				Process:    true,
				Goroutines: true,
				GC:         true,
			},
			ApplicationMetrics: &AppMetricsConfig{
				Enabled:  true,
				HTTP:     true,
				GRPC:     true,
				Database: true,
				Cache:    true,
				Queue:    true,
				Custom:   true,
			},
			Thresholds: map[string]float64{
				"cpu_usage":    CPUWarningThreshold,
				"memory_usage": MemoryWarningThreshold,
				"disk_usage":   DiskWarningThreshold,
				"error_rate":   ErrorRateWarningThreshold,
			},
		},
		AlertManager: &AlertManagerConfig{
			Enabled:            true,
			EvaluationInterval: 30 * time.Second,
			AlertRetention:     DefaultAlertRetention,
			CooldownPeriod:     DefaultAlertCooldown,
			Grouping: &GroupingConfig{
				Enabled:        true,
				By:             []string{"alertname", "instance"},
				Wait:           10 * time.Second,
				Interval:       5 * time.Minute,
				RepeatInterval: 12 * time.Hour,
			},
			Notifiers: map[string]NotifierConfig{
				"console": {
					Type:    NotifierTypeConsole,
					Enabled: true,
					Timeout: 5 * time.Second,
					Retries: 3,
				},
			},
		},
		HealthChecker: &HealthCheckerConfig{
			Enabled:          true,
			Interval:         DefaultHealthCheckTimeout,
			Timeout:          DefaultHealthCheckTimeout,
			Retries:          3,
			FailureThreshold: 3,
			SuccessThreshold: 1,
			Checks: map[string]HealthCheckConfig{
				"database": {
					Type:     HealthCheckTypeDatabase,
					Enabled:  true,
					Interval: 30 * time.Second,
					Timeout:  5 * time.Second,
					Retries:  3,
				},
				"redis": {
					Type:     HealthCheckTypeRedis,
					Enabled:  true,
					Interval: 30 * time.Second,
					Timeout:  5 * time.Second,
					Retries:  3,
				},
			},
		},
		GracefulTimeout: 30 * time.Second,
		ShutdownTimeout: 60 * time.Second,
		Metrics: &MetricsConfig{
			Enabled:   true,
			Path:      "/metrics",
			Port:      9090,
			Interval:  DefaultMonitorInterval,
			Retention: DefaultMetricsRetention,
			Namespace: "ai_edge",
			Subsystem: "manager",
		},
		Logging: &LoggingConfig{
			Level:      DefaultLogLevel,
			Format:     "json",
			Output:     "stdout",
			MaxSize:    DefaultLogMaxSize,
			MaxBackups: DefaultLogMaxBackups,
			MaxAge:     DefaultLogMaxAge,
			Compress:   true,
			Structured: true,
		},
		Security: &SecurityConfig{
			Enabled: true,
			RateLimit: &RateLimitConfig{
				Enabled: true,
				Rate:    DefaultRateLimit,
				Burst:   DefaultBurstLimit,
				Window:  DefaultRateLimitWindow,
			},
		},
		Performance: &PerformanceConfig{
			Enabled: true,
			Caching: &CachingConfig{
				Enabled:  true,
				Provider: "memory",
				Size:     DefaultCacheSize,
				TTL:      DefaultCacheTTL,
				Eviction: "lru",
			},
			ConnectionPool: &PoolConfig{
				MaxSize:     DefaultMaxConnections,
				MinSize:     DefaultMinConnections,
				MaxIdle:     DefaultMaxIdleConnections,
				IdleTimeout: DefaultIdleTimeout,
				MaxLifetime: DefaultConnectionLifetime,
			},
		},
		Features: map[string]bool{
			"task_scheduling": true,
			"monitoring":      true,
			"alerting":        true,
			"health_check":    true,
			"metrics":         true,
			"logging":         true,
			"security":        true,
			"performance":     true,
		},
	}
}

// Validate 验证配置
func (c *ManagerConfig) Validate() error {
	if c.TaskScheduler != nil && c.TaskScheduler.Enabled {
		if c.TaskScheduler.WorkerPoolSize <= 0 {
			return fmt.Errorf("task scheduler worker pool size must be positive")
		}
		if c.TaskScheduler.QueueSize <= 0 {
			return fmt.Errorf("task scheduler queue size must be positive")
		}
		if c.TaskScheduler.TaskTimeout <= 0 {
			return fmt.Errorf("task scheduler task timeout must be positive")
		}
	}

	if c.Monitor != nil && c.Monitor.Enabled {
		if c.Monitor.Interval <= 0 {
			return fmt.Errorf("monitor interval must be positive")
		}
		if c.Monitor.MetricsRetention <= 0 {
			return fmt.Errorf("monitor metrics retention must be positive")
		}
	}

	if c.AlertManager != nil && c.AlertManager.Enabled {
		if c.AlertManager.EvaluationInterval <= 0 {
			return fmt.Errorf("alert manager evaluation interval must be positive")
		}
		if c.AlertManager.AlertRetention <= 0 {
			return fmt.Errorf("alert manager alert retention must be positive")
		}
	}

	if c.HealthChecker != nil && c.HealthChecker.Enabled {
		if c.HealthChecker.Interval <= 0 {
			return fmt.Errorf("health checker interval must be positive")
		}
		if c.HealthChecker.Timeout <= 0 {
			return fmt.Errorf("health checker timeout must be positive")
		}
	}

	return nil
}