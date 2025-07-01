#!/bin/bash

# AI Edge Platform Deploy Script
# 用于部署 Golang 项目的脚本

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
ENVIRONMENT=${ENVIRONMENT:-"development"}
COMPOSE_FILE="deployments/docker-compose.yml"
CONFIG_FILE="configs/config.yaml"

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
    log_info "检查部署依赖..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或不在 PATH 中"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装或不在 PATH 中"
        exit 1
    fi
    
    # 检查 Docker 服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    if [ ! -f "${CONFIG_FILE}" ]; then
        log_error "配置文件不存在: ${CONFIG_FILE}"
        exit 1
    fi
    
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "Docker Compose 文件不存在: ${COMPOSE_FILE}"
        exit 1
    fi
    
    log_success "配置文件检查完成"
}

# 设置环境变量
setup_environment() {
    log_info "设置环境变量..."
    
    # 导出环境变量
    export PROJECT_NAME
    export VERSION
    export ENVIRONMENT
    
    # 根据环境设置不同的配置
    case $ENVIRONMENT in
        "production")
            export GIN_MODE="release"
            export LOG_LEVEL="info"
            ;;
        "staging")
            export GIN_MODE="release"
            export LOG_LEVEL="debug"
            ;;
        "development")
            export GIN_MODE="debug"
            export LOG_LEVEL="debug"
            ;;
        *)
            log_warning "未知环境: $ENVIRONMENT，使用默认配置"
            export GIN_MODE="debug"
            export LOG_LEVEL="debug"
            ;;
    esac
    
    log_success "环境变量设置完成"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."
    
    # 构建应用镜像
    docker-compose -f "${COMPOSE_FILE}" build --no-cache
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动所有服务
    docker-compose -f "${COMPOSE_FILE}" up -d
    
    log_success "服务启动完成"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    docker-compose -f "${COMPOSE_FILE}" down
    
    log_success "服务停止完成"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    
    docker-compose -f "${COMPOSE_FILE}" restart
    
    log_success "服务重启完成"
}

# 查看服务状态
show_status() {
    log_info "服务状态:"
    docker-compose -f "${COMPOSE_FILE}" ps
    
    echo
    log_info "服务日志（最近50行）:"
    docker-compose -f "${COMPOSE_FILE}" logs --tail=50
}

# 查看日志
show_logs() {
    local service=${1:-""}
    local lines=${2:-100}
    
    if [ -n "$service" ]; then
        log_info "查看 $service 服务日志（最近${lines}行）:"
        docker-compose -f "${COMPOSE_FILE}" logs --tail="$lines" -f "$service"
    else
        log_info "查看所有服务日志（最近${lines}行）:"
        docker-compose -f "${COMPOSE_FILE}" logs --tail="$lines" -f
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local api_url="http://localhost:8080/health"
    local grpc_url="localhost:9090"
    local max_attempts=30
    local attempt=1
    
    # 检查 API 服务
    log_info "检查 API 服务健康状态..."
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$api_url" > /dev/null 2>&1; then
            log_success "API 服务健康检查通过"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                log_error "API 服务健康检查失败"
                return 1
            fi
            log_info "等待 API 服务启动... (尝试 $attempt/$max_attempts)"
            sleep 2
            ((attempt++))
        fi
    done
    
    # 检查 gRPC 服务（如果安装了 grpc_health_probe）
    if command -v grpc_health_probe &> /dev/null; then
        log_info "检查 gRPC 服务健康状态..."
        if grpc_health_probe -addr="$grpc_url" > /dev/null 2>&1; then
            log_success "gRPC 服务健康检查通过"
        else
            log_warning "gRPC 服务健康检查失败"
        fi
    else
        log_warning "grpc_health_probe 未安装，跳过 gRPC 健康检查"
    fi
    
    log_success "健康检查完成"
}

# 清理资源
cleanup() {
    log_info "清理资源..."
    
    # 停止并删除容器
    docker-compose -f "${COMPOSE_FILE}" down -v
    
    # 删除未使用的镜像
    docker image prune -f
    
    # 删除未使用的卷
    docker volume prune -f
    
    log_success "资源清理完成"
}

# 备份数据
backup_data() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "备份数据到 $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # 备份 MySQL 数据
    if docker-compose -f "${COMPOSE_FILE}" ps mysql | grep -q "Up"; then
        log_info "备份 MySQL 数据..."
        docker-compose -f "${COMPOSE_FILE}" exec -T mysql mysqldump -u ai_edge -pai_edge_password ai_edge > "$backup_dir/mysql_backup.sql"
    fi
    
    # 备份 Redis 数据
    if docker-compose -f "${COMPOSE_FILE}" ps redis | grep -q "Up"; then
        log_info "备份 Redis 数据..."
        docker-compose -f "${COMPOSE_FILE}" exec -T redis redis-cli BGSAVE
        docker cp $(docker-compose -f "${COMPOSE_FILE}" ps -q redis):/data/dump.rdb "$backup_dir/redis_backup.rdb"
    fi
    
    # 备份配置文件
    cp -r configs "$backup_dir/"
    
    log_success "数据备份完成: $backup_dir"
}

# 恢复数据
restore_data() {
    local backup_dir=$1
    
    if [ -z "$backup_dir" ]; then
        log_error "请指定备份目录"
        exit 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        log_error "备份目录不存在: $backup_dir"
        exit 1
    fi
    
    log_info "从 $backup_dir 恢复数据..."
    
    # 恢复 MySQL 数据
    if [ -f "$backup_dir/mysql_backup.sql" ]; then
        log_info "恢复 MySQL 数据..."
        docker-compose -f "${COMPOSE_FILE}" exec -T mysql mysql -u ai_edge -pai_edge_password ai_edge < "$backup_dir/mysql_backup.sql"
    fi
    
    # 恢复 Redis 数据
    if [ -f "$backup_dir/redis_backup.rdb" ]; then
        log_info "恢复 Redis 数据..."
        docker cp "$backup_dir/redis_backup.rdb" $(docker-compose -f "${COMPOSE_FILE}" ps -q redis):/data/dump.rdb
        docker-compose -f "${COMPOSE_FILE}" restart redis
    fi
    
    log_success "数据恢复完成"
}

# 更新服务
update_services() {
    log_info "更新服务..."
    
    # 拉取最新镜像
    docker-compose -f "${COMPOSE_FILE}" pull
    
    # 重新构建和启动
    docker-compose -f "${COMPOSE_FILE}" up -d --build
    
    log_success "服务更新完成"
}

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [命令] [选项]

命令:
    start           启动所有服务
    stop            停止所有服务
    restart         重启所有服务
    status          查看服务状态
    logs [service]  查看日志（可指定服务名）
    health          执行健康检查
    build           构建镜像
    update          更新服务
    backup          备份数据
    restore <dir>   恢复数据
    cleanup         清理资源
    deploy          完整部署流程（构建、启动、健康检查）

选项:
    -e, --env       设置环境（development/staging/production）
    -v, --version   设置版本号
    -h, --help      显示帮助信息

示例:
    $0 deploy                           # 完整部署
    $0 start                            # 启动服务
    $0 logs api                         # 查看 API 服务日志
    $0 --env production deploy          # 生产环境部署
    $0 backup                           # 备份数据
    $0 restore backups/20231201_120000  # 恢复数据
EOF
}

# 完整部署流程
full_deploy() {
    log_info "=== 开始完整部署流程 ==="
    
    check_dependencies
    check_config
    setup_environment
    build_images
    start_services
    
    # 等待服务启动
    sleep 10
    
    health_check
    show_status
    
    log_success "=== 部署完成 ==="
    
    echo
    log_info "服务访问地址:"
    echo "  - API 服务: http://localhost:8080"
    echo "  - gRPC 服务: localhost:9090"
    echo "  - MySQL: localhost:3306"
    echo "  - Redis: localhost:6379"
    
    if command -v docker-compose &> /dev/null; then
        echo "  - Grafana: http://localhost:3000 (admin/admin)"
        echo "  - Prometheus: http://localhost:9092"
    fi
}

# 主函数
main() {
    local command=""
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            start|stop|restart|status|logs|health|build|update|backup|restore|cleanup|deploy)
                command="$1"
                shift
                break
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果没有指定命令，默认为 deploy
    if [ -z "$command" ]; then
        command="deploy"
    fi
    
    # 显示部署信息
    log_info "=== AI Edge Platform 部署脚本 ==="
    log_info "项目: ${PROJECT_NAME}"
    log_info "版本: ${VERSION}"
    log_info "环境: ${ENVIRONMENT}"
    log_info "命令: ${command}"
    echo
    
    # 执行相应命令
    case $command in
        "start")
            check_dependencies
            setup_environment
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$1" "$2"
            ;;
        "health")
            health_check
            ;;
        "build")
            check_dependencies
            setup_environment
            build_images
            ;;
        "update")
            check_dependencies
            setup_environment
            update_services
            ;;
        "backup")
            backup_data
            ;;
        "restore")
            restore_data "$1"
            ;;
        "cleanup")
            cleanup
            ;;
        "deploy")
            full_deploy
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"