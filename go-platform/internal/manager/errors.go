package manager

import (
	"errors"
	"fmt"
)

// 基础错误定义
var (
	// 管理器错误
	ErrManagerNotRunning     = errors.New("manager is not running")
	ErrManagerAlreadyRunning = errors.New("manager is already running")
	ErrManagerStartFailed    = errors.New("failed to start manager")
	ErrManagerStopFailed     = errors.New("failed to stop manager")
	ErrManagerNotInitialized = errors.New("manager is not initialized")
	ErrManagerConfigInvalid  = errors.New("manager configuration is invalid")

	// 任务调度器错误
	ErrTaskSchedulerNotRunning     = errors.New("task scheduler is not running")
	ErrTaskSchedulerAlreadyRunning = errors.New("task scheduler is already running")
	ErrTaskNotFound                = errors.New("task not found")
	ErrTaskAlreadyExists           = errors.New("task already exists")
	ErrTaskInvalidConfig           = errors.New("task configuration is invalid")
	ErrTaskExecutionFailed         = errors.New("task execution failed")
	ErrTaskTimeout                 = errors.New("task execution timeout")
	ErrTaskCancelled               = errors.New("task was cancelled")
	ErrTaskQueueFull               = errors.New("task queue is full")
	ErrWorkerPoolFull              = errors.New("worker pool is full")
	ErrInvalidTaskType             = errors.New("invalid task type")
	ErrInvalidTaskAction           = errors.New("invalid task action")

	// 监控器错误
	ErrMonitorNotRunning     = errors.New("monitor is not running")
	ErrMonitorAlreadyRunning = errors.New("monitor is already running")
	ErrMetricNotFound        = errors.New("metric not found")
	ErrMetricCollectionFailed = errors.New("metric collection failed")
	ErrInvalidMetricType     = errors.New("invalid metric type")
	ErrMetricThresholdExceeded = errors.New("metric threshold exceeded")
	ErrSystemResourceUnavailable = errors.New("system resource unavailable")

	// 告警管理器错误
	ErrAlertManagerNotRunning     = errors.New("alert manager is not running")
	ErrAlertManagerAlreadyRunning = errors.New("alert manager is already running")
	ErrAlertRuleNotFound          = errors.New("alert rule not found")
	ErrAlertRuleAlreadyExists     = errors.New("alert rule already exists")
	ErrAlertRuleInvalid           = errors.New("alert rule is invalid")
	ErrAlertNotFound              = errors.New("alert not found")
	ErrAlertAlreadyResolved       = errors.New("alert is already resolved")
	ErrAlertSuppressed            = errors.New("alert is suppressed")
	ErrNotifierNotFound           = errors.New("notifier not found")
	ErrNotifierConfigInvalid      = errors.New("notifier configuration is invalid")
	ErrNotificationFailed         = errors.New("notification failed")
	ErrInvalidAlertLevel          = errors.New("invalid alert level")
	ErrInvalidAlertType           = errors.New("invalid alert type")

	// 健康检查器错误
	ErrHealthCheckerNotRunning     = errors.New("health checker is not running")
	ErrHealthCheckerAlreadyRunning = errors.New("health checker is already running")
	ErrHealthCheckFailed           = errors.New("health check failed")
	ErrHealthCheckTimeout          = errors.New("health check timeout")
	ErrComponentUnhealthy          = errors.New("component is unhealthy")
	ErrInvalidHealthCheckType      = errors.New("invalid health check type")
	ErrHealthCheckConfigInvalid    = errors.New("health check configuration is invalid")

	// 通知器错误
	ErrEmailNotifierFailed    = errors.New("email notification failed")
	ErrWebhookNotifierFailed  = errors.New("webhook notification failed")
	ErrSlackNotifierFailed    = errors.New("slack notification failed")
	ErrDingTalkNotifierFailed = errors.New("dingtalk notification failed")
	ErrSMSNotifierFailed      = errors.New("sms notification failed")
	ErrInvalidNotifierType    = errors.New("invalid notifier type")
	ErrNotifierUnavailable    = errors.New("notifier is unavailable")

	// 配置错误
	ErrConfigNotFound       = errors.New("configuration not found")
	ErrConfigInvalid        = errors.New("configuration is invalid")
	ErrConfigLoadFailed     = errors.New("failed to load configuration")
	ErrConfigSaveFailed     = errors.New("failed to save configuration")
	ErrConfigValidationFailed = errors.New("configuration validation failed")
	ErrMissingRequiredConfig = errors.New("missing required configuration")

	// 数据库错误
	ErrDatabaseConnectionFailed = errors.New("database connection failed")
	ErrDatabaseQueryFailed      = errors.New("database query failed")
	ErrDatabaseTransactionFailed = errors.New("database transaction failed")
	ErrDatabaseMigrationFailed  = errors.New("database migration failed")
	ErrDatabaseTimeout          = errors.New("database operation timeout")
	ErrDatabaseDeadlock         = errors.New("database deadlock detected")
	ErrDatabaseConstraintViolation = errors.New("database constraint violation")

	// Redis 错误
	ErrRedisConnectionFailed = errors.New("redis connection failed")
	ErrRedisOperationFailed  = errors.New("redis operation failed")
	ErrRedisTimeout          = errors.New("redis operation timeout")
	ErrRedisKeyNotFound      = errors.New("redis key not found")
	ErrRedisMemoryFull       = errors.New("redis memory is full")

	// gRPC 错误
	ErrGRPCConnectionFailed = errors.New("grpc connection failed")
	ErrGRPCCallFailed       = errors.New("grpc call failed")
	ErrGRPCTimeout          = errors.New("grpc call timeout")
	ErrGRPCUnavailable      = errors.New("grpc service unavailable")
	ErrGRPCInvalidRequest   = errors.New("grpc invalid request")
	ErrGRPCInvalidResponse  = errors.New("grpc invalid response")

	// HTTP 错误
	ErrHTTPRequestFailed    = errors.New("http request failed")
	ErrHTTPTimeout          = errors.New("http request timeout")
	ErrHTTPInvalidResponse  = errors.New("http invalid response")
	ErrHTTPUnauthorized     = errors.New("http unauthorized")
	ErrHTTPForbidden        = errors.New("http forbidden")
	ErrHTTPNotFound         = errors.New("http not found")
	ErrHTTPInternalError    = errors.New("http internal server error")
	ErrHTTPServiceUnavailable = errors.New("http service unavailable")

	// 文件系统错误
	ErrFileNotFound       = errors.New("file not found")
	ErrFilePermissionDenied = errors.New("file permission denied")
	ErrFileAlreadyExists  = errors.New("file already exists")
	ErrFileReadFailed     = errors.New("file read failed")
	ErrFileWriteFailed    = errors.New("file write failed")
	ErrFileDeleteFailed   = errors.New("file delete failed")
	ErrDirectoryNotFound  = errors.New("directory not found")
	ErrDirectoryCreateFailed = errors.New("directory creation failed")
	ErrDiskSpaceFull      = errors.New("disk space is full")

	// 网络错误
	ErrNetworkConnectionFailed = errors.New("network connection failed")
	ErrNetworkTimeout          = errors.New("network timeout")
	ErrNetworkUnavailable      = errors.New("network unavailable")
	ErrDNSResolutionFailed     = errors.New("dns resolution failed")
	ErrPortAlreadyInUse        = errors.New("port already in use")

	// 安全错误
	ErrAuthenticationFailed = errors.New("authentication failed")
	ErrAuthorizationFailed  = errors.New("authorization failed")
	ErrInvalidToken         = errors.New("invalid token")
	ErrTokenExpired         = errors.New("token expired")
	ErrInvalidCredentials   = errors.New("invalid credentials")
	ErrPermissionDenied     = errors.New("permission denied")
	ErrRateLimitExceeded    = errors.New("rate limit exceeded")
	ErrSecurityViolation    = errors.New("security violation")

	// 资源错误
	ErrResourceNotFound     = errors.New("resource not found")
	ErrResourceUnavailable  = errors.New("resource unavailable")
	ErrResourceExhausted    = errors.New("resource exhausted")
	ErrResourceLocked       = errors.New("resource is locked")
	ErrResourceConflict     = errors.New("resource conflict")
	ErrInsufficientResources = errors.New("insufficient resources")

	// 并发错误
	ErrConcurrentModification = errors.New("concurrent modification")
	ErrDeadlockDetected       = errors.New("deadlock detected")
	ErrRaceCondition          = errors.New("race condition detected")
	ErrContextCancelled       = errors.New("context cancelled")
	ErrContextTimeout         = errors.New("context timeout")

	// 序列化错误
	ErrSerializationFailed   = errors.New("serialization failed")
	ErrDeserializationFailed = errors.New("deserialization failed")
	ErrInvalidFormat         = errors.New("invalid format")
	ErrEncodingFailed        = errors.New("encoding failed")
	ErrDecodingFailed        = errors.New("decoding failed")

	// 验证错误
	ErrValidationFailed    = errors.New("validation failed")
	ErrInvalidInput        = errors.New("invalid input")
	ErrInvalidParameter    = errors.New("invalid parameter")
	ErrMissingParameter    = errors.New("missing parameter")
	ErrParameterOutOfRange = errors.New("parameter out of range")
	ErrInvalidFormat       = errors.New("invalid format")

	// 业务逻辑错误
	ErrBusinessLogicViolation = errors.New("business logic violation")
	ErrInvalidState           = errors.New("invalid state")
	ErrOperationNotAllowed    = errors.New("operation not allowed")
	ErrPreconditionFailed     = errors.New("precondition failed")
	ErrPostconditionFailed    = errors.New("postcondition failed")

	// 外部服务错误
	ErrExternalServiceUnavailable = errors.New("external service unavailable")
	ErrExternalServiceTimeout     = errors.New("external service timeout")
	ErrExternalServiceError       = errors.New("external service error")
	ErrAPIQuotaExceeded           = errors.New("api quota exceeded")
	ErrAPIRateLimited             = errors.New("api rate limited")

	// 模型相关错误
	ErrModelNotFound        = errors.New("model not found")
	ErrModelLoadFailed      = errors.New("model load failed")
	ErrModelUnloadFailed    = errors.New("model unload failed")
	ErrModelInferenceFailed = errors.New("model inference failed")
	ErrModelVersionMismatch = errors.New("model version mismatch")
	ErrModelCorrupted       = errors.New("model is corrupted")
	ErrInvalidModelFormat   = errors.New("invalid model format")

	// 数据相关错误
	ErrDataNotFound       = errors.New("data not found")
	ErrDataCorrupted      = errors.New("data is corrupted")
	ErrDataValidationFailed = errors.New("data validation failed")
	ErrDataTransformFailed = errors.New("data transformation failed")
	ErrDataSyncFailed     = errors.New("data synchronization failed")
	ErrInvalidDataFormat  = errors.New("invalid data format")

	// 缓存错误
	ErrCacheNotFound      = errors.New("cache entry not found")
	ErrCacheExpired       = errors.New("cache entry expired")
	ErrCacheOperationFailed = errors.New("cache operation failed")
	ErrCacheFull          = errors.New("cache is full")
	ErrInvalidCacheKey    = errors.New("invalid cache key")

	// 队列错误
	ErrQueueFull          = errors.New("queue is full")
	ErrQueueEmpty         = errors.New("queue is empty")
	ErrQueueOperationFailed = errors.New("queue operation failed")
	ErrInvalidQueueMessage = errors.New("invalid queue message")
	ErrMessageNotFound    = errors.New("message not found")

	// 锁错误
	ErrLockAcquisitionFailed = errors.New("lock acquisition failed")
	ErrLockAlreadyHeld       = errors.New("lock is already held")
	ErrLockNotHeld           = errors.New("lock is not held")
	ErrLockTimeout           = errors.New("lock acquisition timeout")

	// 版本错误
	ErrVersionMismatch     = errors.New("version mismatch")
	ErrUnsupportedVersion  = errors.New("unsupported version")
	ErrVersionNotFound     = errors.New("version not found")
	ErrIncompatibleVersion = errors.New("incompatible version")

	// 许可证错误
	ErrLicenseExpired     = errors.New("license expired")
	ErrLicenseInvalid     = errors.New("license is invalid")
	ErrLicenseNotFound    = errors.New("license not found")
	ErrLicenseViolation   = errors.New("license violation")
	ErrFeatureNotLicensed = errors.New("feature not licensed")

	// 集群错误
	ErrClusterNotReady      = errors.New("cluster is not ready")
	ErrNodeNotFound         = errors.New("node not found")
	ErrNodeUnavailable      = errors.New("node unavailable")
	ErrLeaderElectionFailed = errors.New("leader election failed")
	ErrClusterSplitBrain    = errors.New("cluster split brain")

	// 备份/恢复错误
	ErrBackupFailed    = errors.New("backup failed")
	ErrRestoreFailed   = errors.New("restore failed")
	ErrBackupNotFound  = errors.New("backup not found")
	ErrBackupCorrupted = errors.New("backup is corrupted")
	ErrInvalidBackup   = errors.New("invalid backup")

	// 迁移错误
	ErrMigrationFailed    = errors.New("migration failed")
	ErrMigrationRollback  = errors.New("migration rollback failed")
	ErrInvalidMigration   = errors.New("invalid migration")
	ErrMigrationConflict  = errors.New("migration conflict")

	// 插件错误
	ErrPluginNotFound     = errors.New("plugin not found")
	ErrPluginLoadFailed   = errors.New("plugin load failed")
	ErrPluginInitFailed   = errors.New("plugin initialization failed")
	ErrPluginExecutionFailed = errors.New("plugin execution failed")
	ErrIncompatiblePlugin = errors.New("incompatible plugin")
)

// 错误类型定义
type ErrorType string

const (
	ErrorTypeSystem      ErrorType = "system"
	ErrorTypeApplication ErrorType = "application"
	ErrorTypeNetwork     ErrorType = "network"
	ErrorTypeDatabase    ErrorType = "database"
	ErrorTypeSecurity    ErrorType = "security"
	ErrorTypeValidation  ErrorType = "validation"
	ErrorTypeBusiness    ErrorType = "business"
	ErrorTypeExternal    ErrorType = "external"
	ErrorTypeInternal    ErrorType = "internal"
)

// 错误严重程度
type ErrorSeverity string

const (
	ErrorSeverityLow      ErrorSeverity = "low"
	ErrorSeverityMedium   ErrorSeverity = "medium"
	ErrorSeverityHigh     ErrorSeverity = "high"
	ErrorSeverityCritical ErrorSeverity = "critical"
)

// ManagerError 管理器错误结构
type ManagerError struct {
	Type      ErrorType     `json:"type"`
	Severity  ErrorSeverity `json:"severity"`
	Code      string        `json:"code"`
	Message   string        `json:"message"`
	Details   string        `json:"details,omitempty"`
	Cause     error         `json:"cause,omitempty"`
	Timestamp int64         `json:"timestamp"`
	Component string        `json:"component"`
	Operation string        `json:"operation"`
	Context   map[string]interface{} `json:"context,omitempty"`
}

// Error 实现 error 接口
func (e *ManagerError) Error() string {
	if e.Details != "" {
		return fmt.Sprintf("%s: %s - %s", e.Code, e.Message, e.Details)
	}
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

// Unwrap 实现错误链
func (e *ManagerError) Unwrap() error {
	return e.Cause
}

// NewManagerError 创建新的管理器错误
func NewManagerError(errorType ErrorType, severity ErrorSeverity, code, message string) *ManagerError {
	return &ManagerError{
		Type:      errorType,
		Severity:  severity,
		Code:      code,
		Message:   message,
		Timestamp: time.Now().Unix(),
	}
}

// WithDetails 添加错误详情
func (e *ManagerError) WithDetails(details string) *ManagerError {
	e.Details = details
	return e
}

// WithCause 添加原因错误
func (e *ManagerError) WithCause(cause error) *ManagerError {
	e.Cause = cause
	return e
}

// WithComponent 添加组件信息
func (e *ManagerError) WithComponent(component string) *ManagerError {
	e.Component = component
	return e
}

// WithOperation 添加操作信息
func (e *ManagerError) WithOperation(operation string) *ManagerError {
	e.Operation = operation
	return e
}

// WithContext 添加上下文信息
func (e *ManagerError) WithContext(key string, value interface{}) *ManagerError {
	if e.Context == nil {
		e.Context = make(map[string]interface{})
	}
	e.Context[key] = value
	return e
}

// IsType 检查错误类型
func (e *ManagerError) IsType(errorType ErrorType) bool {
	return e.Type == errorType
}

// IsSeverity 检查错误严重程度
func (e *ManagerError) IsSeverity(severity ErrorSeverity) bool {
	return e.Severity == severity
}

// IsCode 检查错误代码
func (e *ManagerError) IsCode(code string) bool {
	return e.Code == code
}

// 错误代码常量
const (
	// 管理器错误代码
	ErrCodeManagerNotRunning     = "MANAGER_NOT_RUNNING"
	ErrCodeManagerAlreadyRunning = "MANAGER_ALREADY_RUNNING"
	ErrCodeManagerStartFailed    = "MANAGER_START_FAILED"
	ErrCodeManagerStopFailed     = "MANAGER_STOP_FAILED"
	ErrCodeManagerConfigInvalid  = "MANAGER_CONFIG_INVALID"

	// 任务错误代码
	ErrCodeTaskNotFound        = "TASK_NOT_FOUND"
	ErrCodeTaskExecutionFailed = "TASK_EXECUTION_FAILED"
	ErrCodeTaskTimeout         = "TASK_TIMEOUT"
	ErrCodeTaskQueueFull       = "TASK_QUEUE_FULL"

	// 监控错误代码
	ErrCodeMetricCollectionFailed = "METRIC_COLLECTION_FAILED"
	ErrCodeThresholdExceeded      = "THRESHOLD_EXCEEDED"

	// 告警错误代码
	ErrCodeAlertRuleInvalid   = "ALERT_RULE_INVALID"
	ErrCodeNotificationFailed = "NOTIFICATION_FAILED"

	// 健康检查错误代码
	ErrCodeHealthCheckFailed  = "HEALTH_CHECK_FAILED"
	ErrCodeComponentUnhealthy = "COMPONENT_UNHEALTHY"

	// 数据库错误代码
	ErrCodeDatabaseConnectionFailed = "DATABASE_CONNECTION_FAILED"
	ErrCodeDatabaseQueryFailed      = "DATABASE_QUERY_FAILED"
	ErrCodeDatabaseTimeout          = "DATABASE_TIMEOUT"

	// Redis 错误代码
	ErrCodeRedisConnectionFailed = "REDIS_CONNECTION_FAILED"
	ErrCodeRedisOperationFailed  = "REDIS_OPERATION_FAILED"

	// gRPC 错误代码
	ErrCodeGRPCConnectionFailed = "GRPC_CONNECTION_FAILED"
	ErrCodeGRPCCallFailed       = "GRPC_CALL_FAILED"

	// HTTP 错误代码
	ErrCodeHTTPRequestFailed = "HTTP_REQUEST_FAILED"
	ErrCodeHTTPTimeout       = "HTTP_TIMEOUT"

	// 文件系统错误代码
	ErrCodeFileNotFound     = "FILE_NOT_FOUND"
	ErrCodeFileReadFailed   = "FILE_READ_FAILED"
	ErrCodeFileWriteFailed  = "FILE_WRITE_FAILED"
	ErrCodeDiskSpaceFull    = "DISK_SPACE_FULL"

	// 网络错误代码
	ErrCodeNetworkConnectionFailed = "NETWORK_CONNECTION_FAILED"
	ErrCodeNetworkTimeout          = "NETWORK_TIMEOUT"

	// 安全错误代码
	ErrCodeAuthenticationFailed = "AUTHENTICATION_FAILED"
	ErrCodeAuthorizationFailed  = "AUTHORIZATION_FAILED"
	ErrCodeRateLimitExceeded    = "RATE_LIMIT_EXCEEDED"

	// 资源错误代码
	ErrCodeResourceNotFound    = "RESOURCE_NOT_FOUND"
	ErrCodeResourceExhausted   = "RESOURCE_EXHAUSTED"
	ErrCodeResourceUnavailable = "RESOURCE_UNAVAILABLE"

	// 验证错误代码
	ErrCodeValidationFailed = "VALIDATION_FAILED"
	ErrCodeInvalidInput     = "INVALID_INPUT"
	ErrCodeInvalidParameter = "INVALID_PARAMETER"

	// 业务逻辑错误代码
	ErrCodeBusinessLogicViolation = "BUSINESS_LOGIC_VIOLATION"
	ErrCodeInvalidState           = "INVALID_STATE"
	ErrCodeOperationNotAllowed    = "OPERATION_NOT_ALLOWED"

	// 外部服务错误代码
	ErrCodeExternalServiceUnavailable = "EXTERNAL_SERVICE_UNAVAILABLE"
	ErrCodeAPIQuotaExceeded           = "API_QUOTA_EXCEEDED"

	// 模型错误代码
	ErrCodeModelNotFound        = "MODEL_NOT_FOUND"
	ErrCodeModelLoadFailed      = "MODEL_LOAD_FAILED"
	ErrCodeModelInferenceFailed = "MODEL_INFERENCE_FAILED"

	// 数据错误代码
	ErrCodeDataNotFound         = "DATA_NOT_FOUND"
	ErrCodeDataValidationFailed = "DATA_VALIDATION_FAILED"
	ErrCodeDataCorrupted        = "DATA_CORRUPTED"

	// 缓存错误代码
	ErrCodeCacheNotFound        = "CACHE_NOT_FOUND"
	ErrCodeCacheOperationFailed = "CACHE_OPERATION_FAILED"

	// 队列错误代码
	ErrCodeQueueFull            = "QUEUE_FULL"
	ErrCodeQueueOperationFailed = "QUEUE_OPERATION_FAILED"

	// 版本错误代码
	ErrCodeVersionMismatch     = "VERSION_MISMATCH"
	ErrCodeUnsupportedVersion  = "UNSUPPORTED_VERSION"
	ErrCodeIncompatibleVersion = "INCOMPATIBLE_VERSION"

	// 许可证错误代码
	ErrCodeLicenseExpired   = "LICENSE_EXPIRED"
	ErrCodeLicenseInvalid   = "LICENSE_INVALID"
	ErrCodeLicenseViolation = "LICENSE_VIOLATION"

	// 集群错误代码
	ErrCodeClusterNotReady      = "CLUSTER_NOT_READY"
	ErrCodeNodeUnavailable      = "NODE_UNAVAILABLE"
	ErrCodeLeaderElectionFailed = "LEADER_ELECTION_FAILED"

	// 备份错误代码
	ErrCodeBackupFailed    = "BACKUP_FAILED"
	ErrCodeRestoreFailed   = "RESTORE_FAILED"
	ErrCodeBackupCorrupted = "BACKUP_CORRUPTED"

	// 插件错误代码
	ErrCodePluginNotFound       = "PLUGIN_NOT_FOUND"
	ErrCodePluginLoadFailed     = "PLUGIN_LOAD_FAILED"
	ErrCodePluginExecutionFailed = "PLUGIN_EXECUTION_FAILED"
)

// 预定义的管理器错误
var (
	// 系统错误
	ErrSystemResourceExhausted = NewManagerError(
		ErrorTypeSystem, ErrorSeverityCritical,
		ErrCodeResourceExhausted, "System resources exhausted",
	)

	ErrSystemOverloaded = NewManagerError(
		ErrorTypeSystem, ErrorSeverityHigh,
		"SYSTEM_OVERLOADED", "System is overloaded",
	)

	// 应用错误
	ErrApplicationStartupFailed = NewManagerError(
		ErrorTypeApplication, ErrorSeverityCritical,
		"APPLICATION_STARTUP_FAILED", "Application startup failed",
	)

	ErrApplicationShutdownFailed = NewManagerError(
		ErrorTypeApplication, ErrorSeverityHigh,
		"APPLICATION_SHUTDOWN_FAILED", "Application shutdown failed",
	)

	// 网络错误
	ErrNetworkConnectivityLost = NewManagerError(
		ErrorTypeNetwork, ErrorSeverityHigh,
		"NETWORK_CONNECTIVITY_LOST", "Network connectivity lost",
	)

	// 数据库错误
	ErrDatabaseConnectionPoolExhausted = NewManagerError(
		ErrorTypeDatabase, ErrorSeverityHigh,
		"DATABASE_CONNECTION_POOL_EXHAUSTED", "Database connection pool exhausted",
	)

	// 安全错误
	ErrSecurityBreach = NewManagerError(
		ErrorTypeSecurity, ErrorSeverityCritical,
		"SECURITY_BREACH", "Security breach detected",
	)

	ErrUnauthorizedAccess = NewManagerError(
		ErrorTypeSecurity, ErrorSeverityHigh,
		"UNAUTHORIZED_ACCESS", "Unauthorized access attempt",
	)
)

// 错误处理工具函数

// IsManagerError 检查是否为管理器错误
func IsManagerError(err error) bool {
	_, ok := err.(*ManagerError)
	return ok
}

// AsManagerError 转换为管理器错误
func AsManagerError(err error) (*ManagerError, bool) {
	managerErr, ok := err.(*ManagerError)
	return managerErr, ok
}

// WrapError 包装错误为管理器错误
func WrapError(err error, errorType ErrorType, severity ErrorSeverity, code, message string) *ManagerError {
	return NewManagerError(errorType, severity, code, message).WithCause(err)
}

// IsRetryableError 检查错误是否可重试
func IsRetryableError(err error) bool {
	if managerErr, ok := AsManagerError(err); ok {
		// 某些类型的错误可以重试
		return managerErr.IsType(ErrorTypeNetwork) ||
			managerErr.IsType(ErrorTypeExternal) ||
			managerErr.IsCode(ErrCodeDatabaseTimeout) ||
			managerErr.IsCode(ErrCodeHTTPTimeout)
	}
	return false
}

// IsCriticalError 检查错误是否为关键错误
func IsCriticalError(err error) bool {
	if managerErr, ok := AsManagerError(err); ok {
		return managerErr.IsSeverity(ErrorSeverityCritical)
	}
	return false
}

// GetErrorSeverity 获取错误严重程度
func GetErrorSeverity(err error) ErrorSeverity {
	if managerErr, ok := AsManagerError(err); ok {
		return managerErr.Severity
	}
	return ErrorSeverityMedium
}

// GetErrorType 获取错误类型
func GetErrorType(err error) ErrorType {
	if managerErr, ok := AsManagerError(err); ok {
		return managerErr.Type
	}
	return ErrorTypeInternal
}

// GetErrorCode 获取错误代码
func GetErrorCode(err error) string {
	if managerErr, ok := AsManagerError(err); ok {
		return managerErr.Code
	}
	return "UNKNOWN_ERROR"
}