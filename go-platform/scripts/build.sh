#!/bin/bash

# AI Edge Platform Build Script
# 用于构建 Golang 项目的脚本

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="ai-edge-platform"
VERSION=${VERSION:-"latest"}
BUILD_TIME=$(date -u '+%Y-%m-%d_%H:%M:%S')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GO_VERSION=$(go version | awk '{print $3}' 2>/dev/null || echo "unknown")

# 构建目录
BUILD_DIR="build"
BIN_DIR="${BUILD_DIR}/bin"
DIST_DIR="${BUILD_DIR}/dist"

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

# 检查依赖
check_dependencies() {
    log_info "检查构建依赖..."
    
    # 检查 Go
    if ! command -v go &> /dev/null; then
        log_error "Go 未安装或不在 PATH 中"
        exit 1
    fi
    
    # 检查 Git
    if ! command -v git &> /dev/null; then
        log_warning "Git 未安装，将使用默认版本信息"
    fi
    
    log_success "依赖检查完成"
}

# 清理构建目录
clean() {
    log_info "清理构建目录..."
    rm -rf ${BUILD_DIR}
    mkdir -p ${BIN_DIR}
    mkdir -p ${DIST_DIR}
    log_success "构建目录清理完成"
}

# 下载依赖
download_deps() {
    log_info "下载 Go 模块依赖..."
    go mod download
    go mod verify
    log_success "依赖下载完成"
}

# 运行测试
run_tests() {
    log_info "运行单元测试..."
    go test -v ./... -cover
    log_success "测试完成"
}

# 构建二进制文件
build_binary() {
    local app_name=$1
    local main_path=$2
    local output_path="${BIN_DIR}/${app_name}"
    
    log_info "构建 ${app_name}..."
    
    # 构建标志
    local ldflags="
        -X main.Version=${VERSION} \
        -X main.BuildTime=${BUILD_TIME} \
        -X main.GitCommit=${GIT_COMMIT} \
        -X main.GoVersion=${GO_VERSION} \
        -w -s
    "
    
    # 构建
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
        -a -installsuffix cgo \
        -ldflags "${ldflags}" \
        -o "${output_path}" \
        "${main_path}"
    
    # 检查构建结果
    if [ -f "${output_path}" ]; then
        log_success "${app_name} 构建成功: ${output_path}"
        # 显示文件信息
        ls -lh "${output_path}"
    else
        log_error "${app_name} 构建失败"
        exit 1
    fi
}

# 构建所有应用
build_all() {
    log_info "开始构建所有应用..."
    
    # 构建 API 服务
    build_binary "api" "./cmd/api"
    
    # 构建管理服务
    build_binary "manager" "./cmd/manager"
    
    log_success "所有应用构建完成"
}

# 生成 protobuf 文件
generate_proto() {
    log_info "生成 protobuf 文件..."
    
    # 检查 protoc
    if ! command -v protoc &> /dev/null; then
        log_warning "protoc 未安装，跳过 protobuf 生成"
        return
    fi
    
    # 检查 protoc-gen-go
    if ! command -v protoc-gen-go &> /dev/null; then
        log_info "安装 protoc-gen-go..."
        go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
    fi
    
    # 检查 protoc-gen-go-grpc
    if ! command -v protoc-gen-go-grpc &> /dev/null; then
        log_info "安装 protoc-gen-go-grpc..."
        go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
    fi
    
    # 生成 protobuf 文件
    protoc --go_out=. --go_opt=paths=source_relative \
           --go-grpc_out=. --go-grpc_opt=paths=source_relative \
           api/proto/*.proto
    
    log_success "protobuf 文件生成完成"
}

# 创建发布包
create_release() {
    log_info "创建发布包..."
    
    local release_name="${PROJECT_NAME}-${VERSION}-linux-amd64"
    local release_dir="${DIST_DIR}/${release_name}"
    
    # 创建发布目录
    mkdir -p "${release_dir}"
    
    # 复制二进制文件
    cp -r ${BIN_DIR}/* "${release_dir}/"
    
    # 复制配置文件
    cp -r configs "${release_dir}/"
    
    # 复制部署文件
    mkdir -p "${release_dir}/deployments"
    cp deployments/Dockerfile "${release_dir}/deployments/"
    cp deployments/docker-compose.yml "${release_dir}/deployments/"
    cp deployments/init.sql "${release_dir}/deployments/"
    
    # 复制脚本
    mkdir -p "${release_dir}/scripts"
    cp scripts/*.sh "${release_dir}/scripts/"
    
    # 创建 README
    cat > "${release_dir}/README.md" << EOF
# ${PROJECT_NAME} v${VERSION}

## 构建信息
- 版本: ${VERSION}
- 构建时间: ${BUILD_TIME}
- Git 提交: ${GIT_COMMIT}
- Go 版本: ${GO_VERSION}

## 快速启动

### 使用 Docker Compose
\`\`\`bash
cd deployments
docker-compose up -d
\`\`\`

### 直接运行
\`\`\`bash
# 启动 API 服务
./api

# 启动管理服务
./manager
\`\`\`

## 配置

配置文件位于 \`configs/config.yaml\`，请根据实际环境修改相关配置。

## 端口说明

- API 服务: 8080
- gRPC 管理服务: 9090
- MySQL: 3306
- Redis: 6379
EOF
    
    # 创建压缩包
    cd "${DIST_DIR}"
    tar -czf "${release_name}.tar.gz" "${release_name}"
    
    # 计算校验和
    sha256sum "${release_name}.tar.gz" > "${release_name}.tar.gz.sha256"
    
    cd - > /dev/null
    
    log_success "发布包创建完成: ${DIST_DIR}/${release_name}.tar.gz"
}

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [选项]

选项:
    -h, --help          显示帮助信息
    -c, --clean         清理构建目录
    -t, --test          运行测试
    -p, --proto         生成 protobuf 文件
    -b, --build         构建二进制文件
    -r, --release       创建发布包
    -a, --all           执行完整构建流程（清理、测试、构建、发布）
    -v, --version       设置版本号（默认: latest）

示例:
    $0 --all                    # 完整构建流程
    $0 --build                  # 仅构建二进制文件
    $0 --version v1.0.0 --all   # 指定版本号的完整构建
EOF
}

# 主函数
main() {
    local clean_only=false
    local test_only=false
    local proto_only=false
    local build_only=false
    local release_only=false
    local all=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--clean)
                clean_only=true
                shift
                ;;
            -t|--test)
                test_only=true
                shift
                ;;
            -p|--proto)
                proto_only=true
                shift
                ;;
            -b|--build)
                build_only=true
                shift
                ;;
            -r|--release)
                release_only=true
                shift
                ;;
            -a|--all)
                all=true
                shift
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 显示构建信息
    log_info "=== AI Edge Platform 构建脚本 ==="
    log_info "项目: ${PROJECT_NAME}"
    log_info "版本: ${VERSION}"
    log_info "构建时间: ${BUILD_TIME}"
    log_info "Git 提交: ${GIT_COMMIT}"
    log_info "Go 版本: ${GO_VERSION}"
    echo
    
    # 检查依赖
    check_dependencies
    
    # 执行相应操作
    if [[ "$all" == true ]]; then
        clean
        download_deps
        generate_proto
        run_tests
        build_all
        create_release
    elif [[ "$clean_only" == true ]]; then
        clean
    elif [[ "$test_only" == true ]]; then
        run_tests
    elif [[ "$proto_only" == true ]]; then
        generate_proto
    elif [[ "$build_only" == true ]]; then
        clean
        download_deps
        generate_proto
        build_all
    elif [[ "$release_only" == true ]]; then
        create_release
    else
        # 默认执行构建
        clean
        download_deps
        generate_proto
        build_all
    fi
    
    log_success "构建完成！"
}

# 执行主函数
main "$@"