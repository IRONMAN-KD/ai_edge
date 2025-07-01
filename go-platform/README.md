# Go Platform

一个基于 Go 语言开发的现代化 AI 模型管理平台，提供用户认证、模型管理、API 接口等功能。

## 🚀 特性

- **用户管理**: 完整的用户注册、登录、权限管理系统
- **JWT 认证**: 基于 JWT 的安全认证机制
- **模型管理**: AI 模型的增删改查、状态管理
- **RESTful API**: 标准的 REST API 接口设计
- **中间件支持**: CORS、日志、限流、恢复等中间件
- **数据库迁移**: 自动数据库结构迁移
- **配置管理**: 灵活的配置文件管理
- **日志系统**: 结构化日志记录
- **优雅关闭**: 支持优雅关闭和信号处理
- **Docker 支持**: 容器化部署支持

## 📋 技术栈

- **语言**: Go 1.21+
- **Web 框架**: Gin
- **数据库**: GORM (支持 MySQL, PostgreSQL, SQLite)
- **认证**: JWT
- **日志**: 结构化日志
- **配置**: YAML 配置文件
- **容器**: Docker & Docker Compose

## 🛠️ 快速开始

### 环境要求

- Go 1.21 或更高版本
- MySQL 5.7+ / PostgreSQL 12+ / SQLite 3
- Git

### 安装

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd go-platform
   ```

2. **安装依赖**
   ```bash
   make setup
   ```

3. **配置环境**
   ```bash
   cp config/config.example.yaml config/config.yaml
   # 编辑配置文件
   ```

4. **启动开发服务器**
   ```bash
   make dev
   ```

服务器将在 `http://localhost:8080` 启动。

## 📁 项目结构

```
go-platform/
├── cmd/
│   └── server/
│       └── main.go              # 应用程序入口
├── internal/
│   ├── api/
│   │   ├── handlers/            # HTTP 处理器
│   │   │   ├── auth_handler.go  # 认证处理器
│   │   │   ├── user_handler.go  # 用户处理器
│   │   │   └── model_handler.go # 模型处理器
│   │   ├── middleware/          # 中间件
│   │   │   └── middleware.go
│   │   └── routes/              # 路由定义
│   │       └── routes.go
│   ├── config/                  # 配置管理
│   │   └── config.go
│   ├── models/                  # 数据模型
│   │   ├── user.go
│   │   └── model.go
│   ├── repositories/            # 数据访问层
│   │   ├── user_repository.go
│   │   └── model_repository.go
│   └── services/                # 业务逻辑层
│       ├── auth_service.go
│       ├── user_service.go
│       └── model_service.go
├── pkg/
│   ├── database/                # 数据库工具
│   │   └── database.go
│   ├── logger/                  # 日志工具
│   │   └── logger.go
│   └── validator/               # 验证工具
│       └── validator.go
├── config/
│   ├── config.yaml              # 配置文件
│   └── config.example.yaml      # 配置示例
├── docs/                        # API 文档
├── scripts/                     # 脚本文件
├── docker-compose.yml           # Docker Compose 配置
├── Dockerfile                   # Docker 镜像构建
├── Makefile                     # 构建脚本
├── go.mod                       # Go 模块定义
├── go.sum                       # Go 模块校验
└── README.md                    # 项目说明
```

## 🔧 配置

### 配置文件示例

```yaml
server:
  port: 8080
  mode: debug
  read_timeout: 30
  write_timeout: 30
  idle_timeout: 60
  max_header_bytes: 1048576

database:
  driver: mysql
  host: localhost
  port: 3306
  username: root
  password: password
  database: go_platform
  charset: utf8mb4
  parse_time: true
  loc: Local
  max_idle_conns: 10
  max_open_conns: 100
  conn_max_lifetime: 3600

jwt:
  secret: your-secret-key
  access_token_expire: 3600
  refresh_token_expire: 604800
  issuer: go-platform

logger:
  level: info
  format: json
  output: stdout
  file_path: logs/app.log
  max_size: 100
  max_backups: 3
  max_age: 28
  compress: true
```

### 环境变量

可以通过环境变量覆盖配置文件中的设置：

```bash
export SERVER_PORT=8080
export DATABASE_HOST=localhost
export DATABASE_PASSWORD=your-password
export JWT_SECRET=your-jwt-secret
```

## 📚 API 文档

### 认证接口

#### 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

#### 刷新令牌
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

#### 用户登出
```http
POST /api/v1/auth/logout
Authorization: Bearer your-access-token
```

### 用户管理接口

#### 获取用户列表
```http
GET /api/v1/users?page=1&limit=10
Authorization: Bearer your-access-token
```

#### 创建用户
```http
POST /api/v1/users
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "role": "user"
}
```

### 模型管理接口

#### 获取模型列表
```http
GET /api/v1/models?page=1&limit=10
Authorization: Bearer your-access-token
```

#### 创建模型
```http
POST /api/v1/models
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "name": "GPT-4",
  "type": "language_model",
  "provider": "OpenAI",
  "endpoint": "https://api.openai.com/v1",
  "api_key": "your-api-key"
}
```

## 🚀 部署

### Docker 部署

1. **构建镜像**
   ```bash
   make docker-build
   ```

2. **运行容器**
   ```bash
   make docker-run
   ```

### Docker Compose 部署

1. **启动服务**
   ```bash
   make docker-compose-up
   ```

2. **查看日志**
   ```bash
   make docker-compose-logs
   ```

3. **停止服务**
   ```bash
   make docker-compose-down
   ```

### 生产环境部署

1. **构建生产版本**
   ```bash
   make build
   ```

2. **配置生产环境**
   ```bash
   # 设置生产配置
   export GIN_MODE=release
   export SERVER_MODE=release
   ```

3. **启动服务**
   ```bash
   ./build/go-platform
   ```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-coverage

# 运行竞态检测测试
make test-race

# 运行基准测试
make benchmark
```

### 代码质量检查
```bash
# 代码格式化
make fmt

# 代码检查
make lint

# 运行所有检查
make check
```

## 📖 开发指南

### 添加新的 API 接口

1. **定义数据模型** (`internal/models/`)
2. **创建仓库接口** (`internal/repositories/`)
3. **实现业务逻辑** (`internal/services/`)
4. **添加 HTTP 处理器** (`internal/api/handlers/`)
5. **注册路由** (`internal/api/routes/`)
6. **编写测试**

### 数据库迁移

```bash
# 运行迁移
make db-migrate

# 填充测试数据
make db-seed

# 重置数据库
make db-reset
```

### 日志记录

```go
// 在服务中使用日志
logger.Info("用户登录成功", 
    "user_id", user.ID,
    "username", user.Username,
)

logger.Error("数据库连接失败", "error", err)
```

## 🤝 贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 🆘 支持

如果您遇到任何问题或有任何建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索现有的 [Issues](../../issues)
3. 创建新的 [Issue](../../issues/new)

## 🔗 相关链接

- [API 文档](docs/api.md)
- [部署指南](docs/deployment.md)
- [开发指南](docs/development.md)
- [更新日志](CHANGELOG.md)

---

**Go Platform** - 让 AI 模型管理更简单 🚀