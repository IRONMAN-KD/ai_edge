# Go Platform 开发指南

本文档为开发者提供了详细的开发指南，包括项目结构、开发环境设置、编码规范、测试指南等。

## 目录

- [开发环境设置](#开发环境设置)
- [项目结构](#项目结构)
- [编码规范](#编码规范)
- [开发工作流](#开发工作流)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [性能优化](#性能优化)
- [贡献指南](#贡献指南)

## 开发环境设置

### 必需工具

1. **Go 1.21+**
   ```bash
   # 安装 Go
   wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
   sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
   export PATH=$PATH:/usr/local/go/bin
   ```

2. **Git**
   ```bash
   sudo apt install git
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

3. **IDE/编辑器**
   - **推荐**: VS Code + Go 扩展
   - **替代**: GoLand, Vim/Neovim + vim-go

### 开发工具

```bash
# 安装开发工具
make install-tools

# 或手动安装
go install golang.org/x/tools/cmd/goimports@latest
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install github.com/swaggo/swag/cmd/swag@latest
go install github.com/air-verse/air@latest
go install github.com/golang/mock/mockgen@latest
```

### VS Code 配置

创建 `.vscode/settings.json`：

```json
{
  "go.useLanguageServer": true,
  "go.formatTool": "goimports",
  "go.lintTool": "golangci-lint",
  "go.lintOnSave": "package",
  "go.testFlags": ["-v", "-race"],
  "go.testTimeout": "30s",
  "go.coverOnSave": true,
  "go.coverageDecorator": {
    "type": "gutter",
    "coveredHighlightColor": "rgba(64,128,128,0.5)",
    "uncoveredHighlightColor": "rgba(128,64,64,0.25)"
  },
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/vendor": true,
    "**/tmp": true
  }
}
```

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Server",
      "type": "go",
      "request": "launch",
      "mode": "auto",
      "program": "${workspaceFolder}/cmd/server/main.go",
      "env": {
        "GIN_MODE": "debug",
        "CONFIG_PATH": "${workspaceFolder}/config/config.yaml"
      },
      "args": [],
      "showLog": true
    },
    {
      "name": "Debug Test",
      "type": "go",
      "request": "launch",
      "mode": "test",
      "program": "${workspaceFolder}",
      "env": {
        "GO_ENV": "test"
      },
      "args": [
        "-test.v",
        "-test.run",
        "TestName"
      ]
    }
  ]
}
```

## 项目结构

```
go-platform/
├── cmd/                    # 应用程序入口
│   └── server/
│       └── main.go
├── internal/               # 私有应用程序代码
│   ├── api/               # API 层
│   │   ├── handlers/      # HTTP 处理器
│   │   ├── middleware/    # 中间件
│   │   └── routes/        # 路由定义
│   ├── config/            # 配置管理
│   ├── domain/            # 业务领域模型
│   │   ├── entities/      # 实体
│   │   ├── repositories/  # 仓库接口
│   │   └── services/      # 业务服务
│   ├── infrastructure/    # 基础设施层
│   │   ├── database/      # 数据库实现
│   │   ├── cache/         # 缓存实现
│   │   └── external/      # 外部服务
│   └── utils/             # 工具函数
├── pkg/                   # 公共库代码
│   ├── logger/            # 日志库
│   ├── validator/         # 验证器
│   └── response/          # 响应格式
├── config/                # 配置文件
├── docs/                  # 文档
├── scripts/               # 脚本文件
├── tests/                 # 测试文件
│   ├── integration/       # 集成测试
│   ├── unit/             # 单元测试
│   └── fixtures/         # 测试数据
├── deployments/           # 部署配置
│   ├── docker/
│   └── k8s/
├── .github/               # GitHub 配置
│   └── workflows/
├── Makefile              # 构建脚本
├── go.mod                # Go 模块文件
├── go.sum                # Go 依赖锁定
├── README.md             # 项目说明
└── .gitignore            # Git 忽略文件
```

### 架构层次

1. **API 层** (`internal/api/`)
   - 处理 HTTP 请求和响应
   - 参数验证和序列化
   - 中间件和路由

2. **业务层** (`internal/domain/`)
   - 业务逻辑和规则
   - 领域模型和服务
   - 仓库接口定义

3. **基础设施层** (`internal/infrastructure/`)
   - 数据库访问
   - 外部服务调用
   - 缓存和消息队列

4. **公共库** (`pkg/`)
   - 可复用的工具和库
   - 与业务无关的通用代码

## 编码规范

### Go 代码规范

1. **命名规范**
   ```go
   // 包名：小写，简短，有意义
   package user
   
   // 常量：大写，下划线分隔
   const (
       DEFAULT_PAGE_SIZE = 10
       MAX_PAGE_SIZE     = 100
   )
   
   // 变量：驼峰命名
   var userService *UserService
   
   // 函数：驼峰命名，公开函数首字母大写
   func GetUserByID(id uint) (*User, error) {
       // ...
   }
   
   // 私有函数首字母小写
   func validateUserInput(user *User) error {
       // ...
   }
   ```

2. **注释规范**
   ```go
   // Package user provides user management functionality.
   // It includes user creation, authentication, and profile management.
   package user
   
   // User represents a user in the system.
   type User struct {
       ID       uint   `json:"id" gorm:"primaryKey"`
       Username string `json:"username" gorm:"uniqueIndex;not null"`
       Email    string `json:"email" gorm:"uniqueIndex;not null"`
   }
   
   // GetUserByID retrieves a user by their ID.
   // It returns an error if the user is not found.
   func GetUserByID(id uint) (*User, error) {
       // Implementation...
   }
   ```

3. **错误处理**
   ```go
   // 定义自定义错误
   var (
       ErrUserNotFound     = errors.New("user not found")
       ErrInvalidCredentials = errors.New("invalid credentials")
   )
   
   // 错误包装
   func GetUser(id uint) (*User, error) {
       user, err := repo.FindByID(id)
       if err != nil {
           return nil, fmt.Errorf("failed to get user %d: %w", id, err)
       }
       return user, nil
   }
   
   // 错误检查
   if errors.Is(err, ErrUserNotFound) {
       return response.NotFound("User not found")
   }
   ```

4. **结构体标签**
   ```go
   type User struct {
       ID        uint      `json:"id" gorm:"primaryKey" validate:"required"`
       Username  string    `json:"username" gorm:"uniqueIndex;not null" validate:"required,min=3,max=50"`
       Email     string    `json:"email" gorm:"uniqueIndex;not null" validate:"required,email"`
       CreatedAt time.Time `json:"created_at" gorm:"autoCreateTime"`
       UpdatedAt time.Time `json:"updated_at" gorm:"autoUpdateTime"`
   }
   ```

### 项目规范

1. **文件组织**
   ```
   internal/domain/user/
   ├── entity.go          # 实体定义
   ├── repository.go      # 仓库接口
   ├── service.go         # 业务服务
   └── service_test.go    # 服务测试
   ```

2. **包导入顺序**
   ```go
   import (
       // 标准库
       "context"
       "fmt"
       "time"
       
       // 第三方库
       "github.com/gin-gonic/gin"
       "gorm.io/gorm"
       
       // 项目内部包
       "go-platform/internal/domain/user"
       "go-platform/pkg/logger"
   )
   ```

3. **接口设计**
   ```go
   // 接口应该小而专注
   type UserRepository interface {
       Create(ctx context.Context, user *User) error
       GetByID(ctx context.Context, id uint) (*User, error)
       Update(ctx context.Context, user *User) error
       Delete(ctx context.Context, id uint) error
   }
   
   // 使用组合而不是继承
   type UserService interface {
       UserRepository
       AuthService
   }
   ```

## 开发工作流

### 1. 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/user-management

# 2. 开发功能
# - 编写测试
# - 实现功能
# - 更新文档

# 3. 运行测试
make test

# 4. 代码检查
make lint

# 5. 提交代码
git add .
git commit -m "feat: add user management functionality"

# 6. 推送分支
git push origin feature/user-management

# 7. 创建 Pull Request
```

### 2. 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型说明**：
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**：
```
feat(user): add user registration endpoint

Implement user registration with email verification.
Includes validation, password hashing, and email sending.

Closes #123
```

### 3. 分支策略

```
main                 # 主分支，生产环境代码
├── develop          # 开发分支
├── feature/xxx      # 功能分支
├── hotfix/xxx       # 热修复分支
└── release/xxx      # 发布分支
```

## 测试指南

### 1. 测试结构

```
tests/
├── unit/              # 单元测试
│   ├── domain/
│   ├── api/
│   └── utils/
├── integration/       # 集成测试
│   ├── api/
│   └── database/
├── fixtures/          # 测试数据
│   ├── users.json
│   └── models.json
└── helpers/           # 测试辅助函数
    ├── database.go
    └── server.go
```

### 2. 单元测试

```go
// internal/domain/user/service_test.go
package user

import (
    "context"
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

// Mock 仓库
type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) Create(ctx context.Context, user *User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func (m *MockUserRepository) GetByID(ctx context.Context, id uint) (*User, error) {
    args := m.Called(ctx, id)
    return args.Get(0).(*User), args.Error(1)
}

// 测试用例
func TestUserService_CreateUser(t *testing.T) {
    // Arrange
    mockRepo := new(MockUserRepository)
    service := NewUserService(mockRepo)
    
    user := &User{
        Username: "testuser",
        Email:    "test@example.com",
    }
    
    mockRepo.On("Create", mock.Anything, user).Return(nil)
    
    // Act
    err := service.CreateUser(context.Background(), user)
    
    // Assert
    assert.NoError(t, err)
    mockRepo.AssertExpectations(t)
}

func TestUserService_GetUser_NotFound(t *testing.T) {
    // Arrange
    mockRepo := new(MockUserRepository)
    service := NewUserService(mockRepo)
    
    mockRepo.On("GetByID", mock.Anything, uint(1)).Return((*User)(nil), ErrUserNotFound)
    
    // Act
    user, err := service.GetUser(context.Background(), 1)
    
    // Assert
    assert.Nil(t, user)
    assert.ErrorIs(t, err, ErrUserNotFound)
    mockRepo.AssertExpectations(t)
}
```

### 3. 集成测试

```go
// tests/integration/api/user_test.go
package api

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"
    
    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/suite"
    
    "go-platform/tests/helpers"
)

type UserAPITestSuite struct {
    suite.Suite
    router *gin.Engine
    db     *gorm.DB
}

func (suite *UserAPITestSuite) SetupSuite() {
    // 设置测试数据库
    suite.db = helpers.SetupTestDB()
    
    // 设置路由
    suite.router = helpers.SetupTestRouter(suite.db)
}

func (suite *UserAPITestSuite) TearDownSuite() {
    helpers.CleanupTestDB(suite.db)
}

func (suite *UserAPITestSuite) SetupTest() {
    // 清理测试数据
    helpers.CleanupTestData(suite.db)
    
    // 加载测试数据
    helpers.LoadFixtures(suite.db, "users.json")
}

func (suite *UserAPITestSuite) TestCreateUser() {
    // Arrange
    user := map[string]interface{}{
        "username": "newuser",
        "email":    "newuser@example.com",
        "password": "password123",
    }
    
    body, _ := json.Marshal(user)
    req := httptest.NewRequest("POST", "/api/v1/users", bytes.NewBuffer(body))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("Authorization", "Bearer "+helpers.GetAdminToken())
    
    // Act
    w := httptest.NewRecorder()
    suite.router.ServeHTTP(w, req)
    
    // Assert
    assert.Equal(suite.T(), http.StatusCreated, w.Code)
    
    var response map[string]interface{}
    err := json.Unmarshal(w.Body.Bytes(), &response)
    assert.NoError(suite.T(), err)
    assert.Equal(suite.T(), "用户创建成功", response["message"])
}

func TestUserAPITestSuite(t *testing.T) {
    suite.Run(t, new(UserAPITestSuite))
}
```

### 4. 测试辅助函数

```go
// tests/helpers/database.go
package helpers

import (
    "gorm.io/driver/sqlite"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

func SetupTestDB() *gorm.DB {
    db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Silent),
    })
    if err != nil {
        panic("failed to connect to test database")
    }
    
    // 自动迁移
    err = db.AutoMigrate(&User{}, &Model{})
    if err != nil {
        panic("failed to migrate test database")
    }
    
    return db
}

func CleanupTestDB(db *gorm.DB) {
    sqlDB, _ := db.DB()
    sqlDB.Close()
}

func CleanupTestData(db *gorm.DB) {
    db.Exec("DELETE FROM users")
    db.Exec("DELETE FROM models")
}

func LoadFixtures(db *gorm.DB, filename string) {
    // 加载测试数据的实现
}
```

### 5. 运行测试

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行集成测试
make test-integration

# 运行测试并生成覆盖率报告
make test-coverage

# 运行竞态检测
make test-race

# 运行基准测试
make benchmark
```

## 调试技巧

### 1. 日志调试

```go
// 使用结构化日志
logger.Info("Processing user request",
    zap.String("user_id", userID),
    zap.String("action", "create"),
    zap.Duration("duration", time.Since(start)),
)

// 错误日志
logger.Error("Failed to create user",
    zap.Error(err),
    zap.String("username", user.Username),
    zap.String("email", user.Email),
)
```

### 2. 性能分析

```bash
# 启用 pprof
go run cmd/server/main.go --enable-pprof

# CPU 分析
go tool pprof http://localhost:8080/debug/pprof/profile?seconds=30

# 内存分析
go tool pprof http://localhost:8080/debug/pprof/heap

# 协程分析
go tool pprof http://localhost:8080/debug/pprof/goroutine
```

### 3. 数据库调试

```go
// 启用 SQL 日志
db.Logger = logger.Default.LogMode(logger.Info)

// 查看生成的 SQL
result := db.Debug().Where("username = ?", username).First(&user)

// 分析慢查询
db.Callback().Query().Before("gorm:query").Register("query_logger", func(db *gorm.DB) {
    start := time.Now()
    db.Set("start_time", start)
})

db.Callback().Query().After("gorm:query").Register("query_logger", func(db *gorm.DB) {
    if start, ok := db.Get("start_time"); ok {
        duration := time.Since(start.(time.Time))
        if duration > 100*time.Millisecond {
            logger.Warn("Slow query detected",
                zap.Duration("duration", duration),
                zap.String("sql", db.Statement.SQL.String()),
            )
        }
    }
})
```

## 性能优化

### 1. 数据库优化

```go
// 使用索引
type User struct {
    ID       uint   `gorm:"primaryKey"`
    Username string `gorm:"uniqueIndex;not null"`
    Email    string `gorm:"uniqueIndex;not null"`
    Status   string `gorm:"index"`
}

// 预加载关联数据
var users []User
db.Preload("Profile").Preload("Roles").Find(&users)

// 批量操作
db.CreateInBatches(users, 100)

// 使用原生 SQL 进行复杂查询
var result []map[string]interface{}
db.Raw(`
    SELECT u.id, u.username, COUNT(m.id) as model_count
    FROM users u
    LEFT JOIN models m ON u.id = m.user_id
    WHERE u.status = ?
    GROUP BY u.id, u.username
    ORDER BY model_count DESC
    LIMIT ?
`, "active", 10).Scan(&result)
```

### 2. 缓存优化

```go
// Redis 缓存
func (s *UserService) GetUser(ctx context.Context, id uint) (*User, error) {
    // 尝试从缓存获取
    cacheKey := fmt.Sprintf("user:%d", id)
    if cached, err := s.cache.Get(ctx, cacheKey); err == nil {
        var user User
        if err := json.Unmarshal([]byte(cached), &user); err == nil {
            return &user, nil
        }
    }
    
    // 从数据库获取
    user, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, err
    }
    
    // 存入缓存
    if data, err := json.Marshal(user); err == nil {
        s.cache.Set(ctx, cacheKey, string(data), time.Hour)
    }
    
    return user, nil
}

// 内存缓存
type MemoryCache struct {
    data sync.Map
    ttl  time.Duration
}

func (c *MemoryCache) Set(key string, value interface{}) {
    c.data.Store(key, cacheItem{
        value:     value,
        expiresAt: time.Now().Add(c.ttl),
    })
}
```

### 3. 并发优化

```go
// 使用 worker pool
type WorkerPool struct {
    workers int
    jobs    chan Job
    results chan Result
}

func (wp *WorkerPool) Start() {
    for i := 0; i < wp.workers; i++ {
        go wp.worker()
    }
}

func (wp *WorkerPool) worker() {
    for job := range wp.jobs {
        result := job.Process()
        wp.results <- result
    }
}

// 使用 context 控制超时
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

select {
case result := <-resultChan:
    return result, nil
case <-ctx.Done():
    return nil, ctx.Err()
}
```

## 贡献指南

### 1. 提交 Pull Request

1. **Fork 项目**
2. **创建功能分支**
3. **编写代码和测试**
4. **确保测试通过**
5. **提交 Pull Request**

### 2. 代码审查清单

- [ ] 代码符合项目规范
- [ ] 包含充分的测试
- [ ] 测试覆盖率 > 80%
- [ ] 文档已更新
- [ ] 没有安全漏洞
- [ ] 性能影响可接受
- [ ] 向后兼容

### 3. 发布流程

```bash
# 1. 更新版本号
git tag v1.2.0

# 2. 生成变更日志
git log --oneline v1.1.0..v1.2.0 > CHANGELOG.md

# 3. 构建发布包
make build-all

# 4. 推送标签
git push origin v1.2.0

# 5. 创建 GitHub Release
```

### 4. 文档维护

- API 文档使用 Swagger 自动生成
- 代码文档使用 godoc
- 用户文档使用 Markdown
- 定期更新和审查文档

---

本开发指南涵盖了 Go Platform 项目的主要开发流程和最佳实践。遵循这些指南可以确保代码质量和项目的可维护性。