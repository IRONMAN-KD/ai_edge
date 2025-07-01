package logger

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/natefinch/lumberjack.v2"

	"ai-edge/internal/config"
)

var (
	globalLogger *zap.Logger
	once         sync.Once
)

// LogLevel 日志级别
type LogLevel string

const (
	DebugLevel LogLevel = "debug"
	InfoLevel  LogLevel = "info"
	WarnLevel  LogLevel = "warn"
	ErrorLevel LogLevel = "error"
	PanicLevel LogLevel = "panic"
	FatalLevel LogLevel = "fatal"
)

// LogFormat 日志格式
type LogFormat string

const (
	JSONFormat    LogFormat = "json"
	ConsoleFormat LogFormat = "console"
)

// Config 日志配置
type Config struct {
	Level      LogLevel  `yaml:"level" json:"level"`
	Format     LogFormat `yaml:"format" json:"format"`
	Output     []string  `yaml:"output" json:"output"`
	File       FileConfig `yaml:"file" json:"file"`
	Console    ConsoleConfig `yaml:"console" json:"console"`
	Fields     map[string]interface{} `yaml:"fields" json:"fields"`
	Sampling   SamplingConfig `yaml:"sampling" json:"sampling"`
	Development bool     `yaml:"development" json:"development"`
}

// FileConfig 文件日志配置
type FileConfig struct {
	Enabled    bool   `yaml:"enabled" json:"enabled"`
	Path       string `yaml:"path" json:"path"`
	MaxSize    int    `yaml:"max_size" json:"max_size"`         // MB
	MaxBackups int    `yaml:"max_backups" json:"max_backups"`   // 保留文件数
	MaxAge     int    `yaml:"max_age" json:"max_age"`           // 天数
	Compress   bool   `yaml:"compress" json:"compress"`
	LocalTime  bool   `yaml:"local_time" json:"local_time"`
}

// ConsoleConfig 控制台日志配置
type ConsoleConfig struct {
	Enabled   bool `yaml:"enabled" json:"enabled"`
	Colorized bool `yaml:"colorized" json:"colorized"`
}

// SamplingConfig 采样配置
type SamplingConfig struct {
	Enabled    bool `yaml:"enabled" json:"enabled"`
	Initial    int  `yaml:"initial" json:"initial"`
	Thereafter int  `yaml:"thereafter" json:"thereafter"`
}

// DefaultConfig 默认配置
func DefaultConfig() Config {
	return Config{
		Level:  InfoLevel,
		Format: JSONFormat,
		Output: []string{"console"},
		File: FileConfig{
			Enabled:    false,
			Path:       "logs/app.log",
			MaxSize:    100,
			MaxBackups: 10,
			MaxAge:     30,
			Compress:   true,
			LocalTime:  true,
		},
		Console: ConsoleConfig{
			Enabled:   true,
			Colorized: true,
		},
		Fields: make(map[string]interface{}),
		Sampling: SamplingConfig{
			Enabled:    false,
			Initial:    100,
			Thereafter: 100,
		},
		Development: false,
	}
}

// Init 初始化日志器
func Init(cfg Config) error {
	var err error
	once.Do(func() {
		globalLogger, err = NewLogger(cfg)
	})
	return err
}

// InitFromConfig 从配置文件初始化日志器
func InitFromConfig(cfg *config.Config) error {
	loggerConfig := Config{
		Level:       LogLevel(cfg.Log.Level),
		Format:      LogFormat(cfg.Log.Format),
		Output:      cfg.Log.Output,
		Development: cfg.Server.Environment != "production",
		File: FileConfig{
			Enabled:    cfg.Log.File.Enabled,
			Path:       cfg.Log.File.Path,
			MaxSize:    cfg.Log.File.MaxSize,
			MaxBackups: cfg.Log.File.MaxBackups,
			MaxAge:     cfg.Log.File.MaxAge,
			Compress:   cfg.Log.File.Compress,
			LocalTime:  cfg.Log.File.LocalTime,
		},
		Console: ConsoleConfig{
			Enabled:   cfg.Log.Console.Enabled,
			Colorized: cfg.Log.Console.Colorized,
		},
		Sampling: SamplingConfig{
			Enabled:    cfg.Log.Sampling.Enabled,
			Initial:    cfg.Log.Sampling.Initial,
			Thereafter: cfg.Log.Sampling.Thereafter,
		},
	}

	// 添加全局字段
	loggerConfig.Fields = map[string]interface{}{
		"service":     cfg.App.Name,
		"version":     cfg.App.Version,
		"environment": cfg.Server.Environment,
		"build_time":  cfg.App.BuildTime,
		"git_commit":  cfg.App.GitCommit,
	}

	return Init(loggerConfig)
}

// NewLogger 创建新的日志器
func NewLogger(cfg Config) (*zap.Logger, error) {
	// 设置日志级别
	level, err := parseLogLevel(cfg.Level)
	if err != nil {
		return nil, fmt.Errorf("invalid log level: %v", err)
	}

	// 创建编码器配置
	encoderConfig := createEncoderConfig(cfg)

	// 创建编码器
	var encoder zapcore.Encoder
	switch cfg.Format {
	case JSONFormat:
		encoder = zapcore.NewJSONEncoder(encoderConfig)
	case ConsoleFormat:
		encoder = zapcore.NewConsoleEncoder(encoderConfig)
	default:
		encoder = zapcore.NewJSONEncoder(encoderConfig)
	}

	// 创建写入器
	writeSyncers, err := createWriteSyncers(cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to create write syncers: %v", err)
	}

	// 创建核心
	core := zapcore.NewCore(encoder, zapcore.NewMultiWriteSyncer(writeSyncers...), level)

	// 添加采样
	if cfg.Sampling.Enabled {
		core = zapcore.NewSamplerWithOptions(
			core,
			time.Second,
			cfg.Sampling.Initial,
			cfg.Sampling.Thereafter,
		)
	}

	// 创建日志器选项
	options := []zap.Option{
		zap.AddCaller(),
		zap.AddStacktrace(zapcore.ErrorLevel),
	}

	if cfg.Development {
		options = append(options, zap.Development())
	}

	// 添加全局字段
	if len(cfg.Fields) > 0 {
		fields := make([]zap.Field, 0, len(cfg.Fields))
		for key, value := range cfg.Fields {
			fields = append(fields, zap.Any(key, value))
		}
		options = append(options, zap.Fields(fields...))
	}

	// 创建日志器
	logger := zap.New(core, options...)

	return logger, nil
}

// parseLogLevel 解析日志级别
func parseLogLevel(level LogLevel) (zapcore.Level, error) {
	switch strings.ToLower(string(level)) {
	case "debug":
		return zapcore.DebugLevel, nil
	case "info":
		return zapcore.InfoLevel, nil
	case "warn", "warning":
		return zapcore.WarnLevel, nil
	case "error":
		return zapcore.ErrorLevel, nil
	case "panic":
		return zapcore.PanicLevel, nil
	case "fatal":
		return zapcore.FatalLevel, nil
	default:
		return zapcore.InfoLevel, fmt.Errorf("unknown log level: %s", level)
	}
}

// createEncoderConfig 创建编码器配置
func createEncoderConfig(cfg Config) zapcore.EncoderConfig {
	encoderConfig := zap.NewProductionEncoderConfig()

	if cfg.Development {
		encoderConfig = zap.NewDevelopmentEncoderConfig()
	}

	// 自定义时间格式
	encoderConfig.TimeKey = "timestamp"
	encoderConfig.EncodeTime = zapcore.TimeEncoderOfLayout("2006-01-02 15:04:05.000")

	// 自定义级别格式
	encoderConfig.LevelKey = "level"
	if cfg.Format == ConsoleFormat && cfg.Console.Colorized {
		encoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	} else {
		encoderConfig.EncodeLevel = zapcore.CapitalLevelEncoder
	}

	// 自定义调用者格式
	encoderConfig.CallerKey = "caller"
	encoderConfig.EncodeCaller = zapcore.ShortCallerEncoder

	// 自定义堆栈跟踪格式
	encoderConfig.StacktraceKey = "stacktrace"

	// 自定义持续时间格式
	encoderConfig.EncodeDuration = zapcore.StringDurationEncoder

	return encoderConfig
}

// createWriteSyncers 创建写入器
func createWriteSyncers(cfg Config) ([]zapcore.WriteSyncer, error) {
	var syncers []zapcore.WriteSyncer

	for _, output := range cfg.Output {
		switch strings.ToLower(output) {
		case "console", "stdout":
			if cfg.Console.Enabled {
				syncers = append(syncers, zapcore.AddSync(os.Stdout))
			}
		case "stderr":
			if cfg.Console.Enabled {
				syncers = append(syncers, zapcore.AddSync(os.Stderr))
			}
		case "file":
			if cfg.File.Enabled {
				fileSyncer, err := createFileSyncer(cfg.File)
				if err != nil {
					return nil, err
				}
				syncers = append(syncers, fileSyncer)
			}
		default:
			// 尝试作为文件路径处理
			if strings.Contains(output, "/") || strings.Contains(output, "\\") {
				fileConfig := cfg.File
				fileConfig.Path = output
				fileConfig.Enabled = true
				fileSyncer, err := createFileSyncer(fileConfig)
				if err != nil {
					return nil, err
				}
				syncers = append(syncers, fileSyncer)
			}
		}
	}

	if len(syncers) == 0 {
		// 默认输出到控制台
		syncers = append(syncers, zapcore.AddSync(os.Stdout))
	}

	return syncers, nil
}

// createFileSyncer 创建文件写入器
func createFileSyncer(cfg FileConfig) (zapcore.WriteSyncer, error) {
	// 确保目录存在
	dir := filepath.Dir(cfg.Path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create log directory: %v", err)
	}

	// 创建lumberjack日志轮转器
	lumberjackLogger := &lumberjack.Logger{
		Filename:   cfg.Path,
		MaxSize:    cfg.MaxSize,
		MaxBackups: cfg.MaxBackups,
		MaxAge:     cfg.MaxAge,
		Compress:   cfg.Compress,
		LocalTime:  cfg.LocalTime,
	}

	return zapcore.AddSync(lumberjackLogger), nil
}

// GetLogger 获取全局日志器
func GetLogger() *zap.Logger {
	if globalLogger == nil {
		// 如果没有初始化，使用默认配置
		cfg := DefaultConfig()
		cfg.Development = true
		cfg.Format = ConsoleFormat
		logger, _ := NewLogger(cfg)
		return logger
	}
	return globalLogger
}

// SetLogger 设置全局日志器
func SetLogger(logger *zap.Logger) {
	globalLogger = logger
}

// Debug 调试日志
func Debug(msg string, fields ...zap.Field) {
	GetLogger().Debug(msg, fields...)
}

// Info 信息日志
func Info(msg string, fields ...zap.Field) {
	GetLogger().Info(msg, fields...)
}

// Warn 警告日志
func Warn(msg string, fields ...zap.Field) {
	GetLogger().Warn(msg, fields...)
}

// Error 错误日志
func Error(msg string, fields ...zap.Field) {
	GetLogger().Error(msg, fields...)
}

// Panic panic日志
func Panic(msg string, fields ...zap.Field) {
	GetLogger().Panic(msg, fields...)
}

// Fatal 致命错误日志
func Fatal(msg string, fields ...zap.Field) {
	GetLogger().Fatal(msg, fields...)
}

// Sync 同步日志
func Sync() error {
	if globalLogger != nil {
		return globalLogger.Sync()
	}
	return nil
}

// With 创建带字段的日志器
func With(fields ...zap.Field) *zap.Logger {
	return GetLogger().With(fields...)
}

// Named 创建命名日志器
func Named(name string) *zap.Logger {
	return GetLogger().Named(name)
}

// WithOptions 创建带选项的日志器
func WithOptions(opts ...zap.Option) *zap.Logger {
	return GetLogger().WithOptions(opts...)
}

// Sugar 获取Sugar日志器
func Sugar() *zap.SugaredLogger {
	return GetLogger().Sugar()
}

// Close 关闭日志器
func Close() error {
	if globalLogger != nil {
		return globalLogger.Sync()
	}
	return nil
}

// LoggerMiddleware Gin日志中间件
func LoggerMiddleware() func(*zap.Logger) gin.HandlerFunc {
	return func(logger *zap.Logger) gin.HandlerFunc {
		return gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
			logger.Info("HTTP Request",
				zap.String("method", param.Method),
				zap.String("path", param.Path),
				zap.String("query", param.Request.URL.RawQuery),
				zap.String("ip", param.ClientIP),
				zap.String("user_agent", param.Request.UserAgent()),
				zap.Int("status", param.StatusCode),
				zap.Duration("latency", param.Latency),
				zap.String("request_id", param.Request.Header.Get("X-Request-ID")),
			)
			return ""
		})
	}
}

// RequestLogger 请求日志器
type RequestLogger struct {
	logger *zap.Logger
}

// NewRequestLogger 创建请求日志器
func NewRequestLogger(logger *zap.Logger) *RequestLogger {
	return &RequestLogger{logger: logger}
}

// LogRequest 记录请求
func (rl *RequestLogger) LogRequest(method, path, query, ip, userAgent, requestID string, status int, latency time.Duration) {
	rl.logger.Info("HTTP Request",
		zap.String("method", method),
		zap.String("path", path),
		zap.String("query", query),
		zap.String("ip", ip),
		zap.String("user_agent", userAgent),
		zap.Int("status", status),
		zap.Duration("latency", latency),
		zap.String("request_id", requestID),
	)
}

// LogError 记录错误
func (rl *RequestLogger) LogError(method, path, requestID string, err error) {
	rl.logger.Error("HTTP Request Error",
		zap.String("method", method),
		zap.String("path", path),
		zap.String("request_id", requestID),
		zap.Error(err),
	)
}

// ContextLogger 上下文日志器
type ContextLogger struct {
	logger *zap.Logger
	fields []zap.Field
}

// NewContextLogger 创建上下文日志器
func NewContextLogger(logger *zap.Logger, fields ...zap.Field) *ContextLogger {
	return &ContextLogger{
		logger: logger,
		fields: fields,
	}
}

// With 添加字段
func (cl *ContextLogger) With(fields ...zap.Field) *ContextLogger {
	allFields := make([]zap.Field, 0, len(cl.fields)+len(fields))
	allFields = append(allFields, cl.fields...)
	allFields = append(allFields, fields...)
	return &ContextLogger{
		logger: cl.logger,
		fields: allFields,
	}
}

// Debug 调试日志
func (cl *ContextLogger) Debug(msg string, fields ...zap.Field) {
	allFields := append(cl.fields, fields...)
	cl.logger.Debug(msg, allFields...)
}

// Info 信息日志
func (cl *ContextLogger) Info(msg string, fields ...zap.Field) {
	allFields := append(cl.fields, fields...)
	cl.logger.Info(msg, allFields...)
}

// Warn 警告日志
func (cl *ContextLogger) Warn(msg string, fields ...zap.Field) {
	allFields := append(cl.fields, fields...)
	cl.logger.Warn(msg, allFields...)
}

// Error 错误日志
func (cl *ContextLogger) Error(msg string, fields ...zap.Field) {
	allFields := append(cl.fields, fields...)
	cl.logger.Error(msg, allFields...)
}

// Panic panic日志
func (cl *ContextLogger) Panic(msg string, fields ...zap.Field) {
	allFields := append(cl.fields, fields...)
	cl.logger.Panic(msg, allFields...)
}

// Fatal 致命错误日志
func (cl *ContextLogger) Fatal(msg string, fields ...zap.Field) {
	allFields := append(cl.fields, fields...)
	cl.logger.Fatal(msg, allFields...)
}