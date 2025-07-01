package manager

import "time"

// Manager 状态常量
const (
	// 管理器状态
	ManagerStatusRunning = "running"
	ManagerStatusStopped = "stopped"
	ManagerStatusError   = "error"

	// 组件状态
	ComponentStatusHealthy   = "healthy"
	ComponentStatusUnhealthy = "unhealthy"
	ComponentStatusUnknown   = "unknown"
	ComponentStatusStarting  = "starting"
	ComponentStatusStopping  = "stopping"

	// 任务状态
	TaskStatusPending   = "pending"
	TaskStatusRunning   = "running"
	TaskStatusCompleted = "completed"
	TaskStatusFailed    = "failed"
	TaskStatusCancelled = "cancelled"
	TaskStatusTimeout   = "timeout"

	// 任务类型
	TaskTypeScheduled  = "scheduled"
	TaskTypeContinuous = "continuous"
	TaskTypeTrigger    = "trigger"
	TaskTypeOneTime    = "one_time"

	// 任务动作
	TaskActionInference    = "inference"
	TaskActionModelUpdate  = "model_update"
	TaskActionDataCleanup  = "data_cleanup"
	TaskActionHealthCheck  = "health_check"
	TaskActionBackup       = "backup"
	TaskActionMaintenance  = "maintenance"
	TaskActionMonitoring   = "monitoring"
	TaskActionAlert        = "alert"

	// 告警级别
	AlertLevelInfo     = "info"
	AlertLevelWarning  = "warning"
	AlertLevelError    = "error"
	AlertLevelCritical = "critical"

	// 告警状态
	AlertStatusActive    = "active"
	AlertStatusResolved  = "resolved"
	AlertStatusSuppressed = "suppressed"
	AlertStatusAcknowledged = "acknowledged"

	// 告警类型
	AlertTypeSystem      = "system"
	AlertTypeApplication = "application"
	AlertTypeDatabase    = "database"
	AlertTypeNetwork     = "network"
	AlertTypeSecurity    = "security"
	AlertTypePerformance = "performance"
	AlertTypeCapacity    = "capacity"

	// 通知渠道
	NotifierTypeEmail    = "email"
	NotifierTypeWebhook  = "webhook"
	NotifierTypeSlack    = "slack"
	NotifierTypeDingTalk = "dingtalk"
	NotifierTypeConsole  = "console"
	NotifierTypeSMS      = "sms"

	// 健康检查类型
	HealthCheckTypeHTTP     = "http"
	HealthCheckTypeTCP      = "tcp"
	HealthCheckTypeDatabase = "database"
	HealthCheckTypeRedis    = "redis"
	HealthCheckTypeGRPC     = "grpc"
	HealthCheckTypeDisk     = "disk"
	HealthCheckTypeMemory   = "memory"
	HealthCheckTypeCPU      = "cpu"

	// 监控指标类型
	MetricTypeCounter   = "counter"
	MetricTypeGauge     = "gauge"
	MetricTypeHistogram = "histogram"
	MetricTypeSummary   = "summary"

	// 系统指标名称
	MetricCPUUsage       = "cpu_usage"
	MetricMemoryUsage    = "memory_usage"
	MetricDiskUsage      = "disk_usage"
	MetricNetworkIn      = "network_in"
	MetricNetworkOut     = "network_out"
	MetricGoroutines     = "goroutines"
	MetricHeapSize       = "heap_size"
	MetricGCPause        = "gc_pause"

	// 应用指标名称
	MetricRequestsTotal     = "requests_total"
	MetricRequestDuration   = "request_duration"
	MetricErrorsTotal       = "errors_total"
	MetricActiveConnections = "active_connections"
	MetricQueueSize         = "queue_size"
	MetricThroughput        = "throughput"

	// 数据库指标名称
	MetricDBConnections    = "db_connections"
	MetricDBActiveQueries  = "db_active_queries"
	MetricDBSlowQueries    = "db_slow_queries"
	MetricDBQueryDuration  = "db_query_duration"
	MetricDBDeadlocks      = "db_deadlocks"
	MetricDBTableSize      = "db_table_size"

	// Redis 指标名称
	MetricRedisConnections = "redis_connections"
	MetricRedisMemoryUsage = "redis_memory_usage"
	MetricRedisKeyCount    = "redis_key_count"
	MetricRedisHitRate     = "redis_hit_rate"
	MetricRedisOpsPerSec   = "redis_ops_per_sec"

	// 模型指标名称
	MetricModelInferences  = "model_inferences"
	MetricModelLatency     = "model_latency"
	MetricModelErrors      = "model_errors"
	MetricModelAccuracy    = "model_accuracy"
	MetricModelThroughput  = "model_throughput"

	// 事件类型
	EventTypeStartup     = "startup"
	EventTypeShutdown    = "shutdown"
	EventTypeError       = "error"
	EventTypeWarning     = "warning"
	EventTypeInfo        = "info"
	EventTypeDebug       = "debug"
	EventTypeAudit       = "audit"
	EventTypeSecurity    = "security"
	EventTypePerformance = "performance"

	// 日志级别
	LogLevelDebug = "debug"
	LogLevelInfo  = "info"
	LogLevelWarn  = "warn"
	LogLevelError = "error"
	LogLevelFatal = "fatal"

	// 环境类型
	EnvironmentDevelopment = "development"
	EnvironmentTesting     = "testing"
	EnvironmentStaging     = "staging"
	EnvironmentProduction  = "production"

	// 服务角色
	RoleAPI     = "api"
	RoleManager = "manager"
	RoleWorker  = "worker"
	RoleMonitor = "monitor"

	// 协议类型
	ProtocolHTTP  = "http"
	ProtocolHTTPS = "https"
	ProtocolGRPC  = "grpc"
	ProtocolTCP   = "tcp"
	ProtocolUDP   = "udp"

	// 数据格式
	FormatJSON = "json"
	FormatXML  = "xml"
	FormatYAML = "yaml"
	FormatTOML = "toml"
	FormatCSV  = "csv"

	// 压缩类型
	CompressionGzip   = "gzip"
	CompressionDeflate = "deflate"
	CompressionBrotli = "brotli"
	CompressionLZ4    = "lz4"

	// 加密类型
	EncryptionAES256 = "aes256"
	EncryptionRSA    = "rsa"
	EncryptionECDSA  = "ecdsa"

	// 认证类型
	AuthTypeJWT    = "jwt"
	AuthTypeBasic  = "basic"
	AuthTypeBearer = "bearer"
	AuthTypeOAuth2 = "oauth2"
	AuthTypeAPIKey = "apikey"

	// 缓存策略
	CacheStrategyLRU = "lru"
	CacheStrategyLFU = "lfu"
	CacheStrategyTTL = "ttl"

	// 负载均衡策略
	LoadBalanceRoundRobin = "round_robin"
	LoadBalanceWeighted   = "weighted"
	LoadBalanceLeastConn  = "least_conn"
	LoadBalanceIPHash     = "ip_hash"

	// 重试策略
	RetryStrategyFixed       = "fixed"
	RetryStrategyExponential = "exponential"
	RetryStrategyLinear      = "linear"

	// 限流策略
	RateLimitFixed   = "fixed"
	RateLimitSliding = "sliding"
	RateLimitToken   = "token"

	// 存储类型
	StorageTypeLocal = "local"
	StorageTypeS3    = "s3"
	StorageTypeOSS   = "oss"
	StorageTypeCOS   = "cos"
	StorageTypeGCS   = "gcs"

	// 队列类型
	QueueTypeMemory = "memory"
	QueueTypeRedis  = "redis"
	QueueTypeRabbit = "rabbit"
	QueueTypeKafka  = "kafka"

	// 序列化类型
	SerializationJSON    = "json"
	SerializationMsgPack = "msgpack"
	SerializationProtobuf = "protobuf"
	SerializationAvro    = "avro"
)

// 默认配置常量
const (
	// 默认超时时间
	DefaultTimeout        = 30 * time.Second
	DefaultConnectTimeout = 10 * time.Second
	DefaultReadTimeout    = 15 * time.Second
	DefaultWriteTimeout   = 15 * time.Second
	DefaultIdleTimeout    = 60 * time.Second

	// 默认重试配置
	DefaultMaxRetries    = 3
	DefaultRetryDelay    = 1 * time.Second
	DefaultRetryMaxDelay = 30 * time.Second

	// 默认缓存配置
	DefaultCacheSize = 1000
	DefaultCacheTTL  = 5 * time.Minute

	// 默认连接池配置
	DefaultMaxConnections     = 100
	DefaultMinConnections     = 10
	DefaultMaxIdleConnections = 20
	DefaultConnectionLifetime = 1 * time.Hour

	// 默认监控配置
	DefaultMonitorInterval    = 30 * time.Second
	DefaultMetricsRetention   = 24 * time.Hour
	DefaultHealthCheckTimeout = 5 * time.Second

	// 默认告警配置
	DefaultAlertCooldown     = 5 * time.Minute
	DefaultAlertRetention    = 7 * 24 * time.Hour
	DefaultNotificationDelay = 1 * time.Minute

	// 默认任务配置
	DefaultTaskTimeout     = 10 * time.Minute
	DefaultTaskRetries     = 3
	DefaultWorkerPoolSize  = 10
	DefaultQueueSize       = 1000

	// 默认日志配置
	DefaultLogLevel      = LogLevelInfo
	DefaultLogMaxSize    = 100 // MB
	DefaultLogMaxBackups = 10
	DefaultLogMaxAge     = 30 // days

	// 默认安全配置
	DefaultJWTExpiration = 24 * time.Hour
	DefaultSessionTTL    = 2 * time.Hour
	DefaultPasswordMinLength = 8

	// 默认限流配置
	DefaultRateLimit       = 1000 // requests per minute
	DefaultBurstLimit      = 100
	DefaultRateLimitWindow = 1 * time.Minute

	// 默认文件配置
	DefaultMaxFileSize   = 10 * 1024 * 1024 // 10MB
	DefaultMaxFiles      = 1000
	DefaultFileRetention = 30 * 24 * time.Hour

	// 默认数据库配置
	DefaultDBMaxOpenConns    = 25
	DefaultDBMaxIdleConns    = 5
	DefaultDBConnMaxLifetime = 1 * time.Hour
	DefaultDBConnMaxIdleTime = 10 * time.Minute

	// 默认 Redis 配置
	DefaultRedisPoolSize     = 10
	DefaultRedisMinIdleConns = 5
	DefaultRedisDialTimeout  = 5 * time.Second
	DefaultRedisReadTimeout  = 3 * time.Second
	DefaultRedisWriteTimeout = 3 * time.Second

	// 默认 gRPC 配置
	DefaultGRPCMaxRecvMsgSize = 4 * 1024 * 1024 // 4MB
	DefaultGRPCMaxSendMsgSize = 4 * 1024 * 1024 // 4MB
	DefaultGRPCKeepaliveTime  = 30 * time.Second
	DefaultGRPCKeepaliveTimeout = 5 * time.Second

	// 默认 HTTP 配置
	DefaultHTTPMaxHeaderBytes = 1 << 20 // 1MB
	DefaultHTTPMaxBodySize    = 10 * 1024 * 1024 // 10MB
	DefaultHTTPReadHeaderTimeout = 10 * time.Second

	// 默认批处理配置
	DefaultBatchSize     = 100
	DefaultBatchTimeout  = 5 * time.Second
	DefaultBatchMaxWait  = 10 * time.Second

	// 默认压缩配置
	DefaultCompressionLevel     = 6
	DefaultCompressionThreshold = 1024 // bytes

	// 默认分页配置
	DefaultPageSize    = 20
	DefaultMaxPageSize = 1000

	// 默认搜索配置
	DefaultSearchLimit   = 100
	DefaultSearchTimeout = 10 * time.Second

	// 默认导出配置
	DefaultExportBatchSize = 1000
	DefaultExportTimeout   = 30 * time.Minute

	// 默认备份配置
	DefaultBackupRetention = 30 * 24 * time.Hour
	DefaultBackupInterval  = 24 * time.Hour
	DefaultBackupTimeout   = 2 * time.Hour

	// 默认清理配置
	DefaultCleanupInterval = 1 * time.Hour
	DefaultCleanupBatchSize = 1000
	DefaultDataRetention   = 90 * 24 * time.Hour
)

// 阈值常量
const (
	// CPU 阈值
	CPUWarningThreshold  = 70.0 // %
	CPUCriticalThreshold = 90.0 // %

	// 内存阈值
	MemoryWarningThreshold  = 80.0 // %
	MemoryCriticalThreshold = 95.0 // %

	// 磁盘阈值
	DiskWarningThreshold  = 80.0 // %
	DiskCriticalThreshold = 95.0 // %

	// 网络阈值
	NetworkWarningThreshold  = 80.0 // % of bandwidth
	NetworkCriticalThreshold = 95.0 // % of bandwidth

	// 响应时间阈值
	ResponseTimeWarningThreshold  = 1000.0 // ms
	ResponseTimeCriticalThreshold = 5000.0 // ms

	// 错误率阈值
	ErrorRateWarningThreshold  = 5.0  // %
	ErrorRateCriticalThreshold = 10.0 // %

	// 队列长度阈值
	QueueWarningThreshold  = 100
	QueueCriticalThreshold = 1000

	// 连接数阈值
	ConnectionWarningThreshold  = 80.0 // % of max connections
	ConnectionCriticalThreshold = 95.0 // % of max connections

	// 数据库阈值
	DBSlowQueryThreshold = 1000.0 // ms
	DBDeadlockThreshold  = 10     // per minute
	DBConnectionThreshold = 80.0  // % of max connections

	// Redis 阈值
	RedisMemoryThreshold = 80.0 // % of max memory
	RedisConnectionThreshold = 80.0 // % of max connections
	RedisHitRateThreshold = 90.0 // %

	// 模型推理阈值
	ModelLatencyThreshold = 2000.0 // ms
	ModelErrorRateThreshold = 5.0  // %
	ModelAccuracyThreshold = 90.0  // %

	// 文件系统阈值
	FileCountThreshold = 10000
	FileSizeThreshold  = 1024 * 1024 * 1024 // 1GB

	// 日志阈值
	LogErrorRateThreshold = 1.0 // % of total logs
	LogSizeThreshold      = 100 * 1024 * 1024 // 100MB

	// 安全阈值
	FailedLoginThreshold = 5  // attempts per minute
	SessionTimeoutThreshold = 30 * time.Minute
	PasswordExpiryThreshold = 90 * 24 * time.Hour
)

// 优先级常量
const (
	PriorityLow    = 1
	PriorityNormal = 5
	PriorityHigh   = 8
	PriorityUrgent = 10
)

// 权重常量
const (
	WeightLow    = 1
	WeightNormal = 5
	WeightHigh   = 10
)

// 状态码常量
const (
	StatusCodeOK                  = 200
	StatusCodeCreated             = 201
	StatusCodeAccepted            = 202
	StatusCodeNoContent           = 204
	StatusCodeBadRequest          = 400
	StatusCodeUnauthorized        = 401
	StatusCodeForbidden           = 403
	StatusCodeNotFound            = 404
	StatusCodeMethodNotAllowed    = 405
	StatusCodeConflict            = 409
	StatusCodeUnprocessableEntity = 422
	StatusCodeTooManyRequests     = 429
	StatusCodeInternalServerError = 500
	StatusCodeBadGateway          = 502
	StatusCodeServiceUnavailable  = 503
	StatusCodeGatewayTimeout      = 504
)

// 版本常量
const (
	APIVersion = "v1"
	AppVersion = "1.0.0"
	MinGoVersion = "1.19"
)

// 特殊值常量
const (
	UnknownValue = "unknown"
	DefaultValue = "default"
	NullValue    = "null"
	EmptyValue   = ""
	AllValue     = "*"
)