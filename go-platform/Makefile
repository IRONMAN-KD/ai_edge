# Go Platform Makefile

# 变量定义
APP_NAME := go-platform
BUILD_DIR := ./build
CMD_DIR := ./cmd/server
MAIN_FILE := $(CMD_DIR)/main.go
BINARY_NAME := $(BUILD_DIR)/$(APP_NAME)
DOCKER_IMAGE := $(APP_NAME):latest
GO_VERSION := 1.21

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

# 帮助信息
.PHONY: help
help: ## 显示帮助信息
	@echo "$(BLUE)Go Platform 项目管理命令$(RESET)"
	@echo ""
	@echo "$(YELLOW)可用命令:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# 开发相关命令
.PHONY: dev
dev: ## 启动开发服务器（热重载）
	@echo "$(BLUE)启动开发服务器...$(RESET)"
	@if command -v air > /dev/null; then \
		air; \
	else \
		echo "$(YELLOW)air 未安装，使用 'make install-tools' 安装开发工具$(RESET)"; \
		go run $(MAIN_FILE); \
	fi

.PHONY: run
run: ## 运行应用程序
	@echo "$(BLUE)运行应用程序...$(RESET)"
	@go run $(MAIN_FILE)

.PHONY: build
build: clean ## 构建应用程序
	@echo "$(BLUE)构建应用程序...$(RESET)"
	@mkdir -p $(BUILD_DIR)
	@go build -ldflags "-X main.version=$$(git describe --tags --always --dirty)" -o $(BINARY_NAME) $(MAIN_FILE)
	@echo "$(GREEN)构建完成: $(BINARY_NAME)$(RESET)"

.PHONY: build-linux
build-linux: clean ## 构建Linux版本
	@echo "$(BLUE)构建Linux版本...$(RESET)"
	@mkdir -p $(BUILD_DIR)
	@GOOS=linux GOARCH=amd64 go build -ldflags "-X main.version=$$(git describe --tags --always --dirty)" -o $(BINARY_NAME)-linux $(MAIN_FILE)
	@echo "$(GREEN)Linux版本构建完成: $(BINARY_NAME)-linux$(RESET)"

.PHONY: build-windows
build-windows: clean ## 构建Windows版本
	@echo "$(BLUE)构建Windows版本...$(RESET)"
	@mkdir -p $(BUILD_DIR)
	@GOOS=windows GOARCH=amd64 go build -ldflags "-X main.version=$$(git describe --tags --always --dirty)" -o $(BINARY_NAME)-windows.exe $(MAIN_FILE)
	@echo "$(GREEN)Windows版本构建完成: $(BINARY_NAME)-windows.exe$(RESET)"

.PHONY: build-all
build-all: build build-linux build-windows ## 构建所有平台版本
	@echo "$(GREEN)所有平台版本构建完成$(RESET)"

# 测试相关命令
.PHONY: test
test: ## 运行测试
	@echo "$(BLUE)运行测试...$(RESET)"
	@go test -v ./...

.PHONY: test-coverage
test-coverage: ## 运行测试并生成覆盖率报告
	@echo "$(BLUE)运行测试并生成覆盖率报告...$(RESET)"
	@go test -v -coverprofile=coverage.out ./...
	@go tool cover -html=coverage.out -o coverage.html
	@echo "$(GREEN)覆盖率报告生成完成: coverage.html$(RESET)"

.PHONY: test-race
test-race: ## 运行竞态检测测试
	@echo "$(BLUE)运行竞态检测测试...$(RESET)"
	@go test -race -v ./...

.PHONY: benchmark
benchmark: ## 运行基准测试
	@echo "$(BLUE)运行基准测试...$(RESET)"
	@go test -bench=. -benchmem ./...

# 代码质量相关命令
.PHONY: lint
lint: ## 运行代码检查
	@echo "$(BLUE)运行代码检查...$(RESET)"
	@if command -v golangci-lint > /dev/null; then \
		golangci-lint run; \
	else \
		echo "$(YELLOW)golangci-lint 未安装，使用 'make install-tools' 安装开发工具$(RESET)"; \
		go vet ./...; \
	fi

.PHONY: fmt
fmt: ## 格式化代码
	@echo "$(BLUE)格式化代码...$(RESET)"
	@go fmt ./...
	@if command -v goimports > /dev/null; then \
		goimports -w .; \
	fi

.PHONY: tidy
tidy: ## 整理依赖
	@echo "$(BLUE)整理依赖...$(RESET)"
	@go mod tidy
	@go mod verify

.PHONY: check
check: fmt lint test ## 运行所有检查（格式化、代码检查、测试）
	@echo "$(GREEN)所有检查完成$(RESET)"

# 依赖管理
.PHONY: deps
deps: ## 下载依赖
	@echo "$(BLUE)下载依赖...$(RESET)"
	@go mod download

.PHONY: deps-update
deps-update: ## 更新依赖
	@echo "$(BLUE)更新依赖...$(RESET)"
	@go get -u ./...
	@go mod tidy

.PHONY: install-tools
install-tools: ## 安装开发工具
	@echo "$(BLUE)安装开发工具...$(RESET)"
	@go install github.com/cosmtrek/air@latest
	@go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	@go install golang.org/x/tools/cmd/goimports@latest
	@go install github.com/swaggo/swag/cmd/swag@latest
	@echo "$(GREEN)开发工具安装完成$(RESET)"

# 数据库相关命令
.PHONY: db-migrate
db-migrate: ## 运行数据库迁移
	@echo "$(BLUE)运行数据库迁移...$(RESET)"
	@go run $(MAIN_FILE) -migrate

.PHONY: db-seed
db-seed: ## 填充测试数据
	@echo "$(BLUE)填充测试数据...$(RESET)"
	@go run $(MAIN_FILE) -seed

.PHONY: db-reset
db-reset: ## 重置数据库
	@echo "$(BLUE)重置数据库...$(RESET)"
	@go run $(MAIN_FILE) -reset

# Docker相关命令
.PHONY: docker-build
docker-build: ## 构建Docker镜像
	@echo "$(BLUE)构建Docker镜像...$(RESET)"
	@docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)Docker镜像构建完成: $(DOCKER_IMAGE)$(RESET)"

.PHONY: docker-run
docker-run: ## 运行Docker容器
	@echo "$(BLUE)运行Docker容器...$(RESET)"
	@docker run -p 8080:8080 --env-file .env $(DOCKER_IMAGE)

.PHONY: docker-compose-up
docker-compose-up: ## 启动Docker Compose服务
	@echo "$(BLUE)启动Docker Compose服务...$(RESET)"
	@docker-compose up -d

.PHONY: docker-compose-down
docker-compose-down: ## 停止Docker Compose服务
	@echo "$(BLUE)停止Docker Compose服务...$(RESET)"
	@docker-compose down

.PHONY: docker-compose-logs
docker-compose-logs: ## 查看Docker Compose日志
	@docker-compose logs -f

# 文档相关命令
.PHONY: docs
docs: ## 生成API文档
	@echo "$(BLUE)生成API文档...$(RESET)"
	@if command -v swag > /dev/null; then \
		swag init -g $(MAIN_FILE) -o ./docs; \
		echo "$(GREEN)API文档生成完成: ./docs$(RESET)"; \
	else \
		echo "$(YELLOW)swag 未安装，使用 'make install-tools' 安装开发工具$(RESET)"; \
	fi

# 清理相关命令
.PHONY: clean
clean: ## 清理构建文件
	@echo "$(BLUE)清理构建文件...$(RESET)"
	@rm -rf $(BUILD_DIR)
	@rm -f coverage.out coverage.html
	@echo "$(GREEN)清理完成$(RESET)"

.PHONY: clean-all
clean-all: clean ## 清理所有生成文件
	@echo "$(BLUE)清理所有生成文件...$(RESET)"
	@go clean -cache -modcache -testcache
	@docker system prune -f
	@echo "$(GREEN)深度清理完成$(RESET)"

# 部署相关命令
.PHONY: deploy-staging
deploy-staging: build ## 部署到测试环境
	@echo "$(BLUE)部署到测试环境...$(RESET)"
	@echo "$(YELLOW)请实现具体的部署逻辑$(RESET)"

.PHONY: deploy-prod
deploy-prod: build ## 部署到生产环境
	@echo "$(BLUE)部署到生产环境...$(RESET)"
	@echo "$(YELLOW)请实现具体的部署逻辑$(RESET)"

# 版本管理
.PHONY: version
version: ## 显示版本信息
	@echo "$(BLUE)版本信息:$(RESET)"
	@echo "Go版本: $$(go version)"
	@echo "Git版本: $$(git describe --tags --always --dirty 2>/dev/null || echo 'unknown')"
	@echo "构建时间: $$(date)"

# 安全检查
.PHONY: security
security: ## 运行安全检查
	@echo "$(BLUE)运行安全检查...$(RESET)"
	@if command -v gosec > /dev/null; then \
		gosec ./...; \
	else \
		echo "$(YELLOW)gosec 未安装，请运行: go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest$(RESET)"; \
	fi

# 性能分析
.PHONY: profile
profile: ## 运行性能分析
	@echo "$(BLUE)运行性能分析...$(RESET)"
	@go test -cpuprofile=cpu.prof -memprofile=mem.prof -bench=. ./...
	@echo "$(GREEN)性能分析完成，查看 cpu.prof 和 mem.prof$(RESET)"

# 快速开始
.PHONY: setup
setup: deps install-tools ## 项目初始化设置
	@echo "$(GREEN)项目初始化完成！$(RESET)"
	@echo "$(BLUE)运行 'make dev' 启动开发服务器$(RESET)"

.PHONY: ci
ci: deps check test-coverage ## CI/CD流水线
	@echo "$(GREEN)CI检查完成$(RESET)"