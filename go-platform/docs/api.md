# Go Platform API 文档

## 概述

Go Platform 提供了一套完整的 RESTful API，用于管理用户、AI 模型和系统配置。所有 API 都遵循 REST 规范，使用 JSON 格式进行数据交换。

## 基础信息

- **Base URL**: `http://localhost:8080/api/v1`
- **Content-Type**: `application/json`
- **认证方式**: JWT Bearer Token

## 认证

### 登录

获取访问令牌和刷新令牌。

**请求**
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**响应**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "status": "active"
    }
  }
}
```

### 刷新令牌

使用刷新令牌获取新的访问令牌。

**请求**
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**
```json
{
  "code": 200,
  "message": "令牌刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

### 登出

注销当前用户会话。

**请求**
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "登出成功"
}
```

## 用户管理

### 获取用户列表

获取系统中的用户列表（需要管理员权限）。

**请求**
```http
GET /users?page=1&limit=10&search=admin&role=admin&status=active
Authorization: Bearer <access_token>
```

**查询参数**
- `page`: 页码（默认：1）
- `limit`: 每页数量（默认：10，最大：100）
- `search`: 搜索关键词（用户名或邮箱）
- `role`: 角色筛选（admin, user）
- `status`: 状态筛选（active, inactive, suspended）

**响应**
```json
{
  "code": 200,
  "message": "获取用户列表成功",
  "data": {
    "users": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 1,
      "pages": 1
    }
  }
}
```

### 创建用户

创建新用户（需要管理员权限）。

**请求**
```http
POST /users
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "role": "user",
  "status": "active"
}
```

**响应**
```json
{
  "code": 201,
  "message": "用户创建成功",
  "data": {
    "id": 2,
    "username": "newuser",
    "email": "newuser@example.com",
    "role": "user",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 获取用户详情

获取指定用户的详细信息。

**请求**
```http
GET /users/{id}
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "获取用户详情成功",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 更新用户

更新用户信息。

**请求**
```http
PUT /users/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "role": "admin",
  "status": "active"
}
```

**响应**
```json
{
  "code": 200,
  "message": "用户更新成功",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "newemail@example.com",
    "role": "admin",
    "status": "active",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 删除用户

删除指定用户（需要管理员权限）。

**请求**
```http
DELETE /users/{id}
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "用户删除成功"
}
```

### 修改密码

修改当前用户密码。

**请求**
```http
POST /auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "oldpassword123",
  "new_password": "newpassword123"
}
```

**响应**
```json
{
  "code": 200,
  "message": "密码修改成功"
}
```

## AI 模型管理

### 获取模型列表

获取系统中的 AI 模型列表。

**请求**
```http
GET /models?page=1&limit=10&search=gpt&type=text&provider=openai&status=active
Authorization: Bearer <access_token>
```

**查询参数**
- `page`: 页码（默认：1）
- `limit`: 每页数量（默认：10，最大：100）
- `search`: 搜索关键词（模型名称或描述）
- `type`: 模型类型（text, image, audio, video）
- `provider`: 提供商（openai, anthropic, google, etc.）
- `status`: 状态筛选（active, inactive）

**响应**
```json
{
  "code": 200,
  "message": "获取模型列表成功",
  "data": {
    "models": [
      {
        "id": 1,
        "name": "gpt-4",
        "display_name": "GPT-4",
        "description": "OpenAI GPT-4 模型",
        "type": "text",
        "provider": "openai",
        "version": "1.0.0",
        "status": "active",
        "config": {
          "max_tokens": 4096,
          "temperature": 0.7,
          "top_p": 1.0
        },
        "pricing": {
          "input_price": 0.03,
          "output_price": 0.06,
          "currency": "USD",
          "unit": "1K tokens"
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 1,
      "pages": 1
    }
  }
}
```

### 创建模型

添加新的 AI 模型（需要管理员权限）。

**请求**
```http
POST /models
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "claude-3",
  "display_name": "Claude 3",
  "description": "Anthropic Claude 3 模型",
  "type": "text",
  "provider": "anthropic",
  "version": "1.0.0",
  "status": "active",
  "config": {
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "pricing": {
    "input_price": 0.015,
    "output_price": 0.075,
    "currency": "USD",
    "unit": "1K tokens"
  },
  "api_config": {
    "base_url": "https://api.anthropic.com",
    "api_key": "your-api-key",
    "timeout": 30
  }
}
```

**响应**
```json
{
  "code": 201,
  "message": "模型创建成功",
  "data": {
    "id": 2,
    "name": "claude-3",
    "display_name": "Claude 3",
    "description": "Anthropic Claude 3 模型",
    "type": "text",
    "provider": "anthropic",
    "version": "1.0.0",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 获取模型详情

获取指定模型的详细信息。

**请求**
```http
GET /models/{id}
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "获取模型详情成功",
  "data": {
    "id": 1,
    "name": "gpt-4",
    "display_name": "GPT-4",
    "description": "OpenAI GPT-4 模型",
    "type": "text",
    "provider": "openai",
    "version": "1.0.0",
    "status": "active",
    "config": {
      "max_tokens": 4096,
      "temperature": 0.7,
      "top_p": 1.0
    },
    "pricing": {
      "input_price": 0.03,
      "output_price": 0.06,
      "currency": "USD",
      "unit": "1K tokens"
    },
    "api_config": {
      "base_url": "https://api.openai.com/v1",
      "timeout": 30
    },
    "stats": {
      "total_requests": 1000,
      "success_requests": 950,
      "error_requests": 50,
      "avg_response_time": 1.5,
      "last_used_at": "2024-01-01T00:00:00Z"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 更新模型

更新模型信息。

**请求**
```http
PUT /models/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "display_name": "GPT-4 Turbo",
  "description": "OpenAI GPT-4 Turbo 模型",
  "status": "active",
  "config": {
    "max_tokens": 8192,
    "temperature": 0.7
  }
}
```

**响应**
```json
{
  "code": 200,
  "message": "模型更新成功",
  "data": {
    "id": 1,
    "name": "gpt-4",
    "display_name": "GPT-4 Turbo",
    "description": "OpenAI GPT-4 Turbo 模型",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 删除模型

删除指定模型（需要管理员权限）。

**请求**
```http
DELETE /models/{id}
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "模型删除成功"
}
```

### 测试模型连接

测试模型的 API 连接是否正常。

**请求**
```http
POST /models/{id}/test
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "Hello, this is a test message."
}
```

**响应**
```json
{
  "code": 200,
  "message": "模型连接测试成功",
  "data": {
    "status": "success",
    "response_time": 1.2,
    "response": "Hello! I received your test message successfully.",
    "usage": {
      "input_tokens": 8,
      "output_tokens": 12,
      "total_tokens": 20
    }
  }
}
```

### 获取模型统计信息

获取模型的使用统计信息。

**请求**
```http
GET /models/{id}/stats?period=7d
Authorization: Bearer <access_token>
```

**查询参数**
- `period`: 统计周期（1h, 24h, 7d, 30d）

**响应**
```json
{
  "code": 200,
  "message": "获取模型统计成功",
  "data": {
    "period": "7d",
    "total_requests": 1000,
    "success_requests": 950,
    "error_requests": 50,
    "success_rate": 95.0,
    "avg_response_time": 1.5,
    "total_tokens": 50000,
    "total_cost": 15.75,
    "daily_stats": [
      {
        "date": "2024-01-01",
        "requests": 150,
        "tokens": 7500,
        "cost": 2.25
      }
    ]
  }
}
```

## 系统管理

### 健康检查

检查系统健康状态。

**请求**
```http
GET /health
```

**响应**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "uptime": "24h30m15s",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "external_apis": "healthy"
  }
}
```

### 系统信息

获取系统信息（需要管理员权限）。

**请求**
```http
GET /admin/system/info
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "获取系统信息成功",
  "data": {
    "version": "1.0.0",
    "build_time": "2024-01-01T00:00:00Z",
    "go_version": "go1.21.0",
    "os": "linux",
    "arch": "amd64",
    "uptime": "24h30m15s",
    "memory": {
      "allocated": "50MB",
      "total_allocated": "100MB",
      "system": "200MB"
    },
    "goroutines": 25,
    "database": {
      "driver": "mysql",
      "version": "8.0.35",
      "max_connections": 100,
      "open_connections": 5
    }
  }
}
```

### 系统统计

获取系统统计信息（需要管理员权限）。

**请求**
```http
GET /admin/system/stats
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "获取系统统计成功",
  "data": {
    "users": {
      "total": 100,
      "active": 85,
      "new_today": 5
    },
    "models": {
      "total": 10,
      "active": 8,
      "requests_today": 1000
    },
    "api": {
      "total_requests": 50000,
      "requests_today": 1500,
      "avg_response_time": 0.5,
      "error_rate": 0.02
    }
  }
}
```

## 错误响应

所有错误响应都遵循统一格式：

```json
{
  "code": 400,
  "message": "请求参数错误",
  "error": "validation_error",
  "details": {
    "field": "username",
    "message": "用户名不能为空"
  }
}
```

### 常见错误码

- `400` - 请求参数错误
- `401` - 未授权（令牌无效或过期）
- `403` - 禁止访问（权限不足）
- `404` - 资源不存在
- `409` - 资源冲突（如用户名已存在）
- `422` - 数据验证失败
- `429` - 请求过于频繁（触发限流）
- `500` - 服务器内部错误
- `503` - 服务不可用

## 限流

系统实施了请求限流机制：

- **默认限制**: 每秒 100 个请求
- **突发限制**: 200 个请求
- **限流头部**:
  - `X-RateLimit-Limit`: 限制数量
  - `X-RateLimit-Remaining`: 剩余数量
  - `X-RateLimit-Reset`: 重置时间

## 分页

列表接口支持分页：

- `page`: 页码（从 1 开始）
- `limit`: 每页数量（默认 10，最大 100）

分页响应包含：

```json
{
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "pages": 10
  }
}
```

## SDK 和工具

### cURL 示例

```bash
# 登录
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取用户列表
curl -X GET http://localhost:8080/api/v1/users \
  -H "Authorization: Bearer <access_token>"

# 创建模型
curl -X POST http://localhost:8080/api/v1/models \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"gpt-4","display_name":"GPT-4","type":"text"}'
```

### Postman 集合

我们提供了 Postman 集合文件，包含所有 API 的示例请求。请查看 `docs/postman/` 目录。

## 版本控制

API 使用版本控制，当前版本为 `v1`。未来版本将保持向后兼容性，重大变更将发布新版本。

## 支持

如有问题或建议，请：

1. 查看本文档
2. 检查 [GitHub Issues](https://github.com/your-org/go-platform/issues)
3. 联系技术支持

---

*最后更新: 2024-01-01*