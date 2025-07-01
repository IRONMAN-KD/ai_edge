package database

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"time"

	"gorm.io/driver/mysql"
	"gorm.io/driver/postgres"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"gorm.io/gorm/schema"

	"ai-edge/pkg/logger"
)

// Config 数据库配置
type Config struct {
	Driver          string        `yaml:"driver" json:"driver"`                     // mysql, postgres, sqlite
	DSN             string        `yaml:"dsn" json:"dsn"`                           // 数据源名称
	Host            string        `yaml:"host" json:"host"`
	Port            int           `yaml:"port" json:"port"`
	Username        string        `yaml:"username" json:"username"`
	Password        string        `yaml:"password" json:"password"`
	Database        string        `yaml:"database" json:"database"`
	Charset         string        `yaml:"charset" json:"charset"`
	Timezone        string        `yaml:"timezone" json:"timezone"`
	SSLMode         string        `yaml:"ssl_mode" json:"ssl_mode"`
	MaxOpenConns    int           `yaml:"max_open_conns" json:"max_open_conns"`
	MaxIdleConns    int           `yaml:"max_idle_conns" json:"max_idle_conns"`
	ConnMaxLifetime time.Duration `yaml:"conn_max_lifetime" json:"conn_max_lifetime"`
	ConnMaxIdleTime time.Duration `yaml:"conn_max_idle_time" json:"conn_max_idle_time"`
	LogLevel        string        `yaml:"log_level" json:"log_level"`               // silent, error, warn, info
	SlowThreshold   time.Duration `yaml:"slow_threshold" json:"slow_threshold"`
	Colorful        bool          `yaml:"colorful" json:"colorful"`
	AutoMigrate     bool          `yaml:"auto_migrate" json:"auto_migrate"`
	TablePrefix     string        `yaml:"table_prefix" json:"table_prefix"`
	SingularTable   bool          `yaml:"singular_table" json:"singular_table"`
}

// DefaultConfig 默认数据库配置
func DefaultConfig() Config {
	return Config{
		Driver:          "sqlite",
		DSN:             "data/ai_edge.db",
		Host:            "localhost",
		Port:            3306,
		Username:        "root",
		Password:        "",
		Database:        "ai_edge",
		Charset:         "utf8mb4",
		Timezone:        "Asia/Shanghai",
		SSLMode:         "disable",
		MaxOpenConns:    100,
		MaxIdleConns:    10,
		ConnMaxLifetime: time.Hour,
		ConnMaxIdleTime: 10 * time.Minute,
		LogLevel:        "warn",
		SlowThreshold:   200 * time.Millisecond,
		Colorful:        true,
		AutoMigrate:     true,
		TablePrefix:     "ai_",
		SingularTable:   false,
	}
}

// Database 数据库包装器
type Database struct {
	DB     *gorm.DB
	config Config
}

// New 创建数据库连接
func New(cfg Config) (*Database, error) {
	// 构建DSN
	dsn := cfg.DSN
	if dsn == "" {
		dsn = buildDSN(cfg)
	}

	// 选择数据库驱动
	var dialector gorm.Dialector
	switch cfg.Driver {
	case "mysql":
		dialector = mysql.Open(dsn)
	case "postgres":
		dialector = postgres.Open(dsn)
	case "sqlite":
		dialector = sqlite.Open(dsn)
	default:
		return nil, fmt.Errorf("unsupported database driver: %s", cfg.Driver)
	}

	// 配置GORM
	gormConfig := &gorm.Config{
		Logger: createLogger(cfg),
		NamingStrategy: schema.NamingStrategy{
			TablePrefix:   cfg.TablePrefix,
			SingularTable: cfg.SingularTable,
		},
		NowFunc: func() time.Time {
			return time.Now().Local()
		},
		DisableForeignKeyConstraintWhenMigrating: true,
	}

	// 连接数据库
	db, err := gorm.Open(dialector, gormConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to connect database: %v", err)
	}

	// 获取底层sql.DB
	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get sql.DB: %v", err)
	}

	// 设置连接池
	sqlDB.SetMaxOpenConns(cfg.MaxOpenConns)
	sqlDB.SetMaxIdleConns(cfg.MaxIdleConns)
	sqlDB.SetConnMaxLifetime(cfg.ConnMaxLifetime)
	sqlDB.SetConnMaxIdleTime(cfg.ConnMaxIdleTime)

	// 测试连接
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := sqlDB.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("failed to ping database: %v", err)
	}

	return &Database{
		DB:     db,
		config: cfg,
	}, nil
}

// buildDSN 构建数据源名称
func buildDSN(cfg Config) string {
	switch cfg.Driver {
	case "mysql":
		return fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?charset=%s&parseTime=True&loc=%s",
			cfg.Username, cfg.Password, cfg.Host, cfg.Port, cfg.Database, cfg.Charset, cfg.Timezone)
	case "postgres":
		return fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s TimeZone=%s",
			cfg.Host, cfg.Port, cfg.Username, cfg.Password, cfg.Database, cfg.SSLMode, cfg.Timezone)
	case "sqlite":
		return cfg.Database
	default:
		return ""
	}
}

// createLogger 创建GORM日志器
func createLogger(cfg Config) logger.Interface {
	// 解析日志级别
	var logLevel logger.LogLevel
	switch cfg.LogLevel {
	case "silent":
		logLevel = logger.Silent
	case "error":
		logLevel = logger.Error
	case "warn":
		logLevel = logger.Warn
	case "info":
		logLevel = logger.Info
	default:
		logLevel = logger.Warn
	}

	return logger.New(
		log.New(logger.NewGormLogWriter(), "\r\n", log.LstdFlags),
		logger.Config{
			SlowThreshold:             cfg.SlowThreshold,
			LogLevel:                  logLevel,
			IgnoreRecordNotFoundError: true,
			Colorful:                  cfg.Colorful,
		},
	)
}

// AutoMigrate 自动迁移
func (d *Database) AutoMigrate(models ...interface{}) error {
	if !d.config.AutoMigrate {
		return nil
	}

	logger.Info("Starting database auto migration")
	for _, model := range models {
		if err := d.DB.AutoMigrate(model); err != nil {
			return fmt.Errorf("failed to migrate model %T: %v", model, err)
		}
		logger.Info(fmt.Sprintf("Migrated model: %T", model))
	}
	logger.Info("Database auto migration completed")

	return nil
}

// Close 关闭数据库连接
func (d *Database) Close() error {
	sqlDB, err := d.DB.DB()
	if err != nil {
		return err
	}
	return sqlDB.Close()
}

// Health 健康检查
func (d *Database) Health(ctx context.Context) error {
	sqlDB, err := d.DB.DB()
	if err != nil {
		return err
	}
	return sqlDB.PingContext(ctx)
}

// Stats 获取连接池统计信息
func (d *Database) Stats() sql.DBStats {
	sqlDB, _ := d.DB.DB()
	return sqlDB.Stats()
}

// Transaction 事务处理
func (d *Database) Transaction(fn func(*gorm.DB) error) error {
	return d.DB.Transaction(fn)
}

// WithContext 使用上下文
func (d *Database) WithContext(ctx context.Context) *gorm.DB {
	return d.DB.WithContext(ctx)
}

// Begin 开始事务
func (d *Database) Begin() *gorm.DB {
	return d.DB.Begin()
}

// Commit 提交事务
func (d *Database) Commit(tx *gorm.DB) error {
	return tx.Commit().Error
}

// Rollback 回滚事务
func (d *Database) Rollback(tx *gorm.DB) error {
	return tx.Rollback().Error
}

// Repository 基础仓库接口
type Repository[T any] interface {
	Create(ctx context.Context, entity *T) error
	Update(ctx context.Context, entity *T) error
	Delete(ctx context.Context, id interface{}) error
	FindByID(ctx context.Context, id interface{}) (*T, error)
	FindAll(ctx context.Context) ([]*T, error)
	FindWithPagination(ctx context.Context, page, pageSize int) ([]*T, int64, error)
	Count(ctx context.Context) (int64, error)
	Exists(ctx context.Context, id interface{}) (bool, error)
}

// BaseRepository 基础仓库实现
type BaseRepository[T any] struct {
	db *Database
}

// NewBaseRepository 创建基础仓库
func NewBaseRepository[T any](db *Database) *BaseRepository[T] {
	return &BaseRepository[T]{db: db}
}

// Create 创建实体
func (r *BaseRepository[T]) Create(ctx context.Context, entity *T) error {
	return r.db.WithContext(ctx).Create(entity).Error
}

// Update 更新实体
func (r *BaseRepository[T]) Update(ctx context.Context, entity *T) error {
	return r.db.WithContext(ctx).Save(entity).Error
}

// Delete 删除实体
func (r *BaseRepository[T]) Delete(ctx context.Context, id interface{}) error {
	var entity T
	return r.db.WithContext(ctx).Delete(&entity, id).Error
}

// FindByID 根据ID查找实体
func (r *BaseRepository[T]) FindByID(ctx context.Context, id interface{}) (*T, error) {
	var entity T
	err := r.db.WithContext(ctx).First(&entity, id).Error
	if err != nil {
		return nil, err
	}
	return &entity, nil
}

// FindAll 查找所有实体
func (r *BaseRepository[T]) FindAll(ctx context.Context) ([]*T, error) {
	var entities []*T
	err := r.db.WithContext(ctx).Find(&entities).Error
	return entities, err
}

// FindWithPagination 分页查找实体
func (r *BaseRepository[T]) FindWithPagination(ctx context.Context, page, pageSize int) ([]*T, int64, error) {
	var entities []*T
	var total int64

	// 计算总数
	var entity T
	if err := r.db.WithContext(ctx).Model(&entity).Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// 分页查询
	offset := (page - 1) * pageSize
	err := r.db.WithContext(ctx).Offset(offset).Limit(pageSize).Find(&entities).Error
	return entities, total, err
}

// Count 统计实体数量
func (r *BaseRepository[T]) Count(ctx context.Context) (int64, error) {
	var count int64
	var entity T
	err := r.db.WithContext(ctx).Model(&entity).Count(&count).Error
	return count, err
}

// Exists 检查实体是否存在
func (r *BaseRepository[T]) Exists(ctx context.Context, id interface{}) (bool, error) {
	var count int64
	var entity T
	err := r.db.WithContext(ctx).Model(&entity).Where("id = ?", id).Count(&count).Error
	return count > 0, err
}

// QueryBuilder 查询构建器
type QueryBuilder struct {
	db    *gorm.DB
	query *gorm.DB
}

// NewQueryBuilder 创建查询构建器
func NewQueryBuilder(db *Database) *QueryBuilder {
	return &QueryBuilder{
		db:    db.DB,
		query: db.DB,
	}
}

// Table 指定表名
func (qb *QueryBuilder) Table(name string) *QueryBuilder {
	qb.query = qb.query.Table(name)
	return qb
}

// Select 选择字段
func (qb *QueryBuilder) Select(fields ...string) *QueryBuilder {
	qb.query = qb.query.Select(fields)
	return qb
}

// Where 添加WHERE条件
func (qb *QueryBuilder) Where(query interface{}, args ...interface{}) *QueryBuilder {
	qb.query = qb.query.Where(query, args...)
	return qb
}

// Or 添加OR条件
func (qb *QueryBuilder) Or(query interface{}, args ...interface{}) *QueryBuilder {
	qb.query = qb.query.Or(query, args...)
	return qb
}

// Join 添加JOIN
func (qb *QueryBuilder) Join(query string, args ...interface{}) *QueryBuilder {
	qb.query = qb.query.Joins(query, args...)
	return qb
}

// Group 添加GROUP BY
func (qb *QueryBuilder) Group(name string) *QueryBuilder {
	qb.query = qb.query.Group(name)
	return qb
}

// Having 添加HAVING条件
func (qb *QueryBuilder) Having(query interface{}, args ...interface{}) *QueryBuilder {
	qb.query = qb.query.Having(query, args...)
	return qb
}

// Order 添加ORDER BY
func (qb *QueryBuilder) Order(value interface{}) *QueryBuilder {
	qb.query = qb.query.Order(value)
	return qb
}

// Limit 限制结果数量
func (qb *QueryBuilder) Limit(limit int) *QueryBuilder {
	qb.query = qb.query.Limit(limit)
	return qb
}

// Offset 设置偏移量
func (qb *QueryBuilder) Offset(offset int) *QueryBuilder {
	qb.query = qb.query.Offset(offset)
	return qb
}

// Find 查找结果
func (qb *QueryBuilder) Find(dest interface{}) error {
	return qb.query.Find(dest).Error
}

// First 查找第一个结果
func (qb *QueryBuilder) First(dest interface{}) error {
	return qb.query.First(dest).Error
}

// Count 统计数量
func (qb *QueryBuilder) Count(count *int64) error {
	return qb.query.Count(count).Error
}

// Scan 扫描结果
func (qb *QueryBuilder) Scan(dest interface{}) error {
	return qb.query.Scan(dest).Error
}

// Raw 执行原生SQL
func (qb *QueryBuilder) Raw(sql string, values ...interface{}) *QueryBuilder {
	qb.query = qb.db.Raw(sql, values...)
	return qb
}

// Exec 执行SQL
func (qb *QueryBuilder) Exec() error {
	return qb.query.Error
}

// Paginate 分页查询
func (qb *QueryBuilder) Paginate(page, pageSize int) *QueryBuilder {
	offset := (page - 1) * pageSize
	return qb.Offset(offset).Limit(pageSize)
}

// Migration 数据库迁移工具
type Migration struct {
	db *Database
}

// NewMigration 创建迁移工具
func NewMigration(db *Database) *Migration {
	return &Migration{db: db}
}

// CreateTable 创建表
func (m *Migration) CreateTable(model interface{}) error {
	return m.db.DB.AutoMigrate(model)
}

// DropTable 删除表
func (m *Migration) DropTable(model interface{}) error {
	return m.db.DB.Migrator().DropTable(model)
}

// HasTable 检查表是否存在
func (m *Migration) HasTable(model interface{}) bool {
	return m.db.DB.Migrator().HasTable(model)
}

// AddColumn 添加列
func (m *Migration) AddColumn(model interface{}, field string) error {
	return m.db.DB.Migrator().AddColumn(model, field)
}

// DropColumn 删除列
func (m *Migration) DropColumn(model interface{}, field string) error {
	return m.db.DB.Migrator().DropColumn(model, field)
}

// HasColumn 检查列是否存在
func (m *Migration) HasColumn(model interface{}, field string) bool {
	return m.db.DB.Migrator().HasColumn(model, field)
}

// CreateIndex 创建索引
func (m *Migration) CreateIndex(model interface{}, name string) error {
	return m.db.DB.Migrator().CreateIndex(model, name)
}

// DropIndex 删除索引
func (m *Migration) DropIndex(model interface{}, name string) error {
	return m.db.DB.Migrator().DropIndex(model, name)
}

// HasIndex 检查索引是否存在
func (m *Migration) HasIndex(model interface{}, name string) bool {
	return m.db.DB.Migrator().HasIndex(model, name)
}

// 辅助函数

// IsRecordNotFound 检查是否为记录未找到错误
func IsRecordNotFound(err error) bool {
	return err == gorm.ErrRecordNotFound
}

// IsDuplicateEntry 检查是否为重复条目错误
func IsDuplicateEntry(err error) bool {
	if err == nil {
		return false
	}
	// MySQL
	if fmt.Sprintf("%v", err) == "Error 1062: Duplicate entry" {
		return true
	}
	// PostgreSQL
	if fmt.Sprintf("%v", err) == "duplicate key value violates unique constraint" {
		return true
	}
	return false
}

// Paginate 分页辅助函数
func Paginate(page, pageSize int) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		if page <= 0 {
			page = 1
		}
		if pageSize <= 0 {
			pageSize = 10
		}
		if pageSize > 100 {
			pageSize = 100
		}

		offset := (page - 1) * pageSize
		return db.Offset(offset).Limit(pageSize)
	}
}

// OrderBy 排序辅助函数
func OrderBy(field, direction string) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		if direction != "asc" && direction != "desc" {
			direction = "desc"
		}
		return db.Order(fmt.Sprintf("%s %s", field, direction))
	}
}

// Search 搜索辅助函数
func Search(fields []string, keyword string) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		if keyword == "" || len(fields) == 0 {
			return db
		}

		for i, field := range fields {
			if i == 0 {
				db = db.Where(fmt.Sprintf("%s LIKE ?", field), "%"+keyword+"%")
			} else {
				db = db.Or(fmt.Sprintf("%s LIKE ?", field), "%"+keyword+"%")
			}
		}
		return db
	}
}

// DateRange 日期范围辅助函数
func DateRange(field string, start, end *time.Time) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		if start != nil {
			db = db.Where(fmt.Sprintf("%s >= ?", field), start)
		}
		if end != nil {
			db = db.Where(fmt.Sprintf("%s <= ?", field), end)
		}
		return db
	}
}

// InArray 数组包含辅助函数
func InArray(field string, values []interface{}) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		if len(values) == 0 {
			return db
		}
		return db.Where(fmt.Sprintf("%s IN ?", field), values)
	}
}

// NotInArray 数组不包含辅助函数
func NotInArray(field string, values []interface{}) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		if len(values) == 0 {
			return db
		}
		return db.Where(fmt.Sprintf("%s NOT IN ?", field), values)
	}
}

// IsNull 空值辅助函数
func IsNull(field string) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		return db.Where(fmt.Sprintf("%s IS NULL", field))
	}
}

// IsNotNull 非空值辅助函数
func IsNotNull(field string) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		return db.Where(fmt.Sprintf("%s IS NOT NULL", field))
	}
}

// GormLogWriter GORM日志写入器
type GormLogWriter struct{}

// Write 实现io.Writer接口
func (w GormLogWriter) Write(p []byte) (n int, err error) {
	logger.Info(string(p))
	return len(p), nil
}

// NewGormLogWriter 创建GORM日志写入器
func NewGormLogWriter() *GormLogWriter {
	return &GormLogWriter{}
}