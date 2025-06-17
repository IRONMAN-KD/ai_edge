#!/bin/bash

# AI Edge 视觉识别系统构建和运行脚本
# 使用方法: ./build_and_run.sh [build|run|stop|clean|logs]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="atlas-vision-system"
CONTAINER_NAME="atlas-vision-system"
IMAGE_NAME="atlas-vision-system:latest"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 Atlas 设备
    if [ ! -e "/dev/davinci0" ]; then
        log_warn "未检测到 Atlas NPU 设备，将使用模拟模式"
    else
        log_info "检测到 Atlas NPU 设备"
    fi
    
    log_info "依赖检查完成"
}

# 创建必要目录
create_directories() {
    log_step "创建必要目录..."
    
    mkdir -p config models alert_images logs videos tests
    log_info "目录创建完成"
}

# 检查配置文件
check_config() {
    log_step "检查配置文件..."
    
    if [ ! -f "config/config.yml" ]; then
        log_error "配置文件 config/config.yml 不存在"
        exit 1
    fi
    
    log_info "配置文件检查完成"
}

# 检查模型文件
check_model() {
    log_step "检查模型文件..."
    
    if [ ! -f "models/model.om" ]; then
        log_warn "模型文件 models/model.om 不存在，将使用模拟模式"
        log_info "请将您的 .om 模型文件放入 models/ 目录"
    else
        log_info "模型文件检查完成"
    fi
}

# 构建镜像
build_image() {
    log_step "构建 Docker 镜像..."
    
    # 检查 Dockerfile
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile 不存在"
        exit 1
    fi
    
    # 构建镜像
    docker build -t $IMAGE_NAME . --no-cache
    
    if [ $? -eq 0 ]; then
        log_info "镜像构建成功: $IMAGE_NAME"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# 运行容器
run_container() {
    log_step "启动容器..."
    
    # 检查镜像是否存在
    if ! docker image inspect $IMAGE_NAME &> /dev/null; then
        log_error "镜像 $IMAGE_NAME 不存在，请先构建镜像"
        exit 1
    fi
    
    # 停止已存在的容器
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log_warn "停止已存在的容器"
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
    fi
    
    # 运行容器
    docker run -d \
        --name $CONTAINER_NAME \
        --restart unless-stopped \
        --device=/dev/davinci0 \
        --device=/dev/davinci_manager \
        --device=/dev/hisi_hdc \
        -v $(pwd)/config:/app/config:ro \
        -v $(pwd)/models:/app/models:ro \
        -v $(pwd)/alert_images:/app/alert_images \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/videos:/app/videos:ro \
        --network host \
        -e CONTAINER_ENV=true \
        -e ASCEND_DEVICE_ID=0 \
        $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        log_info "容器启动成功: $CONTAINER_NAME"
        log_info "查看日志: docker logs -f $CONTAINER_NAME"
    else
        log_error "容器启动失败"
        exit 1
    fi
}

# 停止容器
stop_container() {
    log_step "停止容器..."
    
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        log_info "容器已停止并删除: $CONTAINER_NAME"
    else
        log_warn "容器 $CONTAINER_NAME 不存在或已停止"
    fi
}

# 查看日志
show_logs() {
    log_step "显示容器日志..."
    
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        docker logs -f $CONTAINER_NAME
    else
        log_error "容器 $CONTAINER_NAME 未运行"
        exit 1
    fi
}

# 清理资源
clean_resources() {
    log_step "清理资源..."
    
    # 停止并删除容器
    stop_container
    
    # 删除镜像
    if docker image inspect $IMAGE_NAME &> /dev/null; then
        docker rmi $IMAGE_NAME
        log_info "镜像已删除: $IMAGE_NAME"
    fi
    
    # 清理未使用的资源
    docker system prune -f
    
    log_info "资源清理完成"
}

# 显示状态
show_status() {
    log_step "系统状态..."
    
    echo "=== 容器状态 ==="
    docker ps -a -f name=$CONTAINER_NAME
    
    echo -e "\n=== 镜像状态 ==="
    docker images $IMAGE_NAME
    
    echo -e "\n=== 资源使用 ==="
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        docker stats $CONTAINER_NAME --no-stream
    fi
    
    echo -e "\n=== 目录状态 ==="
    echo "配置文件: $(ls -la config/)"
    echo "模型文件: $(ls -la models/)"
    echo "告警图片: $(ls -la alert_images/ | wc -l) 个文件"
    echo "日志文件: $(ls -la logs/ | wc -l) 个文件"
}

# 显示帮助
show_help() {
    echo "AI Edge 视觉识别系统构建和运行脚本"
    echo ""
    echo "使用方法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  build    构建 Docker 镜像"
    echo "  run      运行容器"
    echo "  stop     停止容器"
    echo "  logs     查看容器日志"
    echo "  status   显示系统状态"
    echo "  clean    清理所有资源"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 build    # 构建镜像"
    echo "  $0 run      # 运行容器"
    echo "  $0 logs     # 查看日志"
    echo "  $0 stop     # 停止容器"
}

# 主函数
main() {
    case "${1:-help}" in
        "build")
            check_dependencies
            create_directories
            check_config
            check_model
            build_image
            ;;
        "run")
            check_dependencies
            create_directories
            check_config
            check_model
            run_container
            ;;
        "stop")
            stop_container
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "clean")
            clean_resources
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@" 