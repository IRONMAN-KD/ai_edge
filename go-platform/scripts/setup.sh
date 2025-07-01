#!/bin/bash

# Go Platform 项目设置脚本
# 用于快速设置开发环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查 Go 版本
check_go_version() {
    if ! command_exists go; then
        log_error "Go 未安装，请先安装 Go 1.21 或更高版本"
        exit 1
    fi
    
    GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
    REQUIRED_VERSION="1.21"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$GO_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        log_error "Go 版本过低，需要 $REQUIRED_VERSION 或更高版本，当前版本: $GO_VERSION"
        exit 1
    fi
    
    log_success "Go 版本检查通过: $GO_VERSION"
}

# 安装开发工具
install_dev_tools() {
    log_info "安装开发工具..."
    
    # Air - 热重载工具
    if ! command_exists air; then
        log_info "安装 Air (热重载工具)..."
        go install github.com/cosmtrek/air@latest
    else
        log_success "Air 已安装"
    fi
    
    # golangci-lint - 代码检查工具
    if ! command_exists golangci-lint; then
        log_info "安装 golangci-lint (代码检查工具)..."
        curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin v1.54.2
    else
        log_success "golangci-lint 已安装"
    fi
    
    # Wire - 依赖注入工具
    if ! command_exists wire; then
        log_info "安装 Wire (依赖注入工具)..."
        go install github.com/google/wire/cmd/wire@latest
    else
        log_success "Wire 已安装"
    fi
    
    # Mockery - Mock 生成工具
    if ! command_exists mockery; then
        log_info "安装 Mockery (Mock 生成工具)..."
        go install github.com/vektra/mockery/v2@latest
    else
        log_success "Mockery 已安装"
    fi
    
    # Swag - Swagger 文档生成工具
    if ! command_exists swag; then
        log_info "安装 Swag (Swagger 文档生成工具)..."
        go install github.com/swaggo/swag/cmd/swag@latest
    else
        log_success "Swag 已安装"
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    directories=(
        "tmp"
        "data"
        "logs"
        "uploads"
        "tests/fixtures"
        "tests/mocks"
        "deployments/docker"
        "deployments/k8s"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_success "创建目录: $dir"
        else
            log_info "目录已存在: $dir"
        fi
    done
}

# 复制配置文件
setup_config() {
    log_info "设置配置文件..."
    
    if [ ! -f "config.yaml" ] && [ -f "config.example.yaml" ]; then
        cp config.example.yaml config.yaml
        log_success "复制配置文件: config.yaml"
        log_warning "请根据需要修改 config.yaml 中的配置"
    else
        log_info "配置文件已存在或示例文件不存在"
    fi
}

# 下载依赖
download_dependencies() {
    log_info "下载 Go 模块依赖..."
    go mod download
    go mod tidy
    log_success "依赖下载完成"
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    if go test ./... -v; then
        log_success "所有测试通过"
    else
        log_warning "部分测试失败，请检查代码"
    fi
}

# 生成文档
generate_docs() {
    log_info "生成 API 文档..."
    if command_exists swag; then
        swag init -g cmd/server/main.go -o docs/swagger
        log_success "API 文档生成完成"
    else
        log_warning "Swag 未安装，跳过文档生成"
    fi
}

# 主函数
main() {
    log_info "开始设置 Go Platform 开发环境..."
    
    # 检查 Go 版本
    check_go_version
    
    # 安装开发工具
    install_dev_tools
    
    # 创建目录
    create_directories
    
    # 设置配置
    setup_config
    
    # 下载依赖
    download_dependencies
    
    # 运行测试
    if [ "${1:-}" != "--skip-tests" ]; then
        run_tests
    fi
    
    # 生成文档
    generate_docs
    
    log_success "开发环境设置完成！"
    echo
    log_info "接下来你可以:"
    echo "  1. 修改 config.yaml 配置文件"
    echo "  2. 运行 'make dev' 启动开发服务器"
    echo "  3. 运行 'make test' 执行测试"
    echo "  4. 运行 'make lint' 检查代码质量"
    echo "  5. 访问 http://localhost:8080/health 检查服务状态"
}

# 执行主函数
main "$@"