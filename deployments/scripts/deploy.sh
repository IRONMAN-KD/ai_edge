#!/bin/bash

# AI Edge统一部署脚本
# 支持多平台部署

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

# 显示使用帮助
show_usage() {
    echo "使用方法: $0 [平台] [部署模式] [选项]"
    echo ""
    echo "平台:"
    echo "  cpu_x86      - x86 CPU平台"
    echo "  cpu_arm      - ARM CPU平台"
    echo "  nvidia_gpu   - NVIDIA GPU平台"
    echo "  atlas_npu    - 华为Atlas NPU平台"
    echo "  sophon       - 算能平台"
    echo ""
    echo "部署模式:"
    echo "  docker       - Docker容器部署（默认）"
    echo "  host         - 主机直接部署"
    echo ""
    echo "选项:"
    echo "  --build      - 构建镜像"
    echo "  --clean      - 清理旧容器"
    echo "  --dev        - 开发模式"
    echo ""
    echo "示例:"
    echo "  $0 atlas_npu docker --build"
    echo "  $0 cpu_x86 host"
}

# 解析参数
PLATFORM=${1:-cpu_x86}
DEPLOY_MODE=${2:-docker}
BUILD_FLAG=false
CLEAN_FLAG=false
DEV_MODE=false

# 解析选项
for arg in "${@:3}"; do
    case $arg in
        --build)
            BUILD_FLAG=true
            ;;
        --clean)
            CLEAN_FLAG=true
            ;;
        --dev)
            DEV_MODE=true
            ;;
        *)
            log_error "未知选项: $arg"
            show_usage
            exit 1
            ;;
    esac
done

# 验证平台
VALID_PLATFORMS=("cpu_x86" "cpu_arm" "nvidia_gpu" "atlas_npu" "sophon")
if [[ ! " ${VALID_PLATFORMS[@]} " =~ " ${PLATFORM} " ]]; then
    log_error "无效的平台: $PLATFORM"
    show_usage
    exit 1
fi

# 验证部署模式
VALID_MODES=("docker" "host")
if [[ ! " ${VALID_MODES[@]} " =~ " ${DEPLOY_MODE} " ]]; then
    log_error "无效的部署模式: $DEPLOY_MODE"
    show_usage
    exit 1
fi

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_ROOT"

log_info "🚀 AI Edge系统部署"
log_info "平台: $PLATFORM"
log_info "部署模式: $DEPLOY_MODE"
log_info "项目目录: $PROJECT_ROOT"

# 加载平台配置
PLATFORM_CONFIG="configs/platforms/$PLATFORM/platform.yml"
if [ ! -f "$PLATFORM_CONFIG" ]; then
    log_error "平台配置文件不存在: $PLATFORM_CONFIG"
    exit 1
fi

# Docker部署
if [ "$DEPLOY_MODE" = "docker" ]; then
    log_info "使用Docker部署模式"
    
    # 清理旧容器
    if [ "$CLEAN_FLAG" = true ]; then
        log_info "清理旧容器..."
        docker-compose -f configs/platforms/$PLATFORM/docker-compose.yml down || true
    fi
    
    # 构建镜像
    if [ "$BUILD_FLAG" = true ]; then
        log_info "构建Docker镜像..."
        
        # 创建临时构建目录
        BUILD_DIR="/tmp/ai_edge_build_$$"
        mkdir -p "$BUILD_DIR"
        
        # 复制源代码
        cp -r src "$BUILD_DIR/"
        cp -r requirements "$BUILD_DIR/"
        cp configs/platforms/$PLATFORM/Dockerfile "$BUILD_DIR/"
        
        # 构建镜像
        docker build -t ai-edge-$PLATFORM:latest "$BUILD_DIR"
        
        # 清理临时目录
        rm -rf "$BUILD_DIR"
        
        log_success "镜像构建完成: ai-edge-$PLATFORM:latest"
    fi
    
    # 启动服务
    log_info "启动Docker服务..."
    
    # 设置环境变量
    export PLATFORM=$PLATFORM
    export PROJECT_ROOT=$PROJECT_ROOT
    
    # 使用docker-compose启动
    if [ "$DEV_MODE" = true ]; then
        docker-compose -f configs/platforms/$PLATFORM/docker-compose.yml up
    else
        docker-compose -f configs/platforms/$PLATFORM/docker-compose.yml up -d
        log_success "服务已在后台启动"
    fi
    
# 主机部署
else
    log_info "使用主机部署模式"
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请先安装Python 3.8+"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip install -r requirements/base.txt
    
    # 安装平台特定依赖
    case $PLATFORM in
        cpu_x86|cpu_arm)
            if [ -f "requirements/cpu.txt" ]; then
                pip install -r requirements/cpu.txt
            fi
            ;;
        nvidia_gpu)
            if [ -f "requirements/nvidia.txt" ]; then
                pip install -r requirements/nvidia.txt
            fi
            ;;
        atlas_npu)
            if [ -f "requirements/atlas.txt" ]; then
                pip install -r requirements/atlas.txt
            fi
            ;;
        sophon)
            if [ -f "requirements/sophon.txt" ]; then
                pip install -r requirements/sophon.txt
            fi
            ;;
    esac
    
    # 检查模型文件
    log_info "检查模型文件..."
    if [ ! -d "models" ]; then
        mkdir -p models
        log_warning "请将模型文件放置在 models/ 目录中"
    fi
    
    # 启动API服务
    log_info "启动API服务..."
    export PLATFORM=$PLATFORM
    export PYTHONPATH=$PROJECT_ROOT/src:$PYTHONPATH
    
    if [ "$DEV_MODE" = true ]; then
        python src/api/main.py --platform $PLATFORM --debug
    else
        python src/api/main.py --platform $PLATFORM
    fi
fi

log_success "部署完成！"

# 显示访问信息
case $PLATFORM in
    atlas_npu)
        log_info "API服务地址: http://localhost:8000"
        log_info "前端地址: http://localhost:80"
        ;;
    *)
        log_info "API服务地址: http://localhost:8000"
        log_info "前端地址: http://localhost:3000"
        ;;
esac 