#!/bin/bash

# AI Edge多平台测试脚本

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

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_ROOT"

log_info "🧪 AI Edge多平台测试"
log_info "项目目录: $PROJECT_ROOT"

# 测试平台检测
test_platform_detection() {
    log_info "测试平台自动检测..."
    
    python3 -c "
import sys
sys.path.append('src')
from utils.platform_detector import auto_detect_platform, PlatformDetector

detector = PlatformDetector()
platform, score = detector.detect_best_platform()
print(f'检测到最佳平台: {platform} (置信度: {score:.2f})')

capabilities = detector.get_platform_capabilities(platform)
print(f'平台能力: {capabilities}')
"
}

# 测试推理引擎工厂
test_inference_factory() {
    log_info "测试推理引擎工厂..."
    
    python3 -c "
import sys
sys.path.append('src')
from inference.factory import InferenceFactory

print('支持的平台:', InferenceFactory.get_supported_platforms())

for platform in ['cpu_x86', 'nvidia_gpu', 'atlas_npu', 'sophon']:
    if InferenceFactory.is_platform_supported(platform):
        print(f'✅ {platform} 支持')
    else:
        print(f'❌ {platform} 不支持')
"
}

# 测试配置加载
test_config_loading() {
    log_info "测试配置文件加载..."
    
    for platform in cpu_x86 nvidia_gpu atlas_npu sophon cpu_arm; do
        config_file="configs/platforms/$platform/platform.yml"
        if [ -f "$config_file" ]; then
            log_success "✅ $platform 配置文件存在"
            
            # 验证YAML格式
            python3 -c "
import yaml
with open('$config_file', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
    print(f'  平台名称: {config.get(\"platform\", {}).get(\"display_name\", \"未知\")}')
    print(f'  推理引擎: {config.get(\"inference\", {}).get(\"engine\", \"未知\")}')
"
        else
            log_warning "⚠️  $platform 配置文件不存在"
        fi
    done
}

# 测试依赖文件
test_requirements() {
    log_info "测试依赖文件..."
    
    for req_file in base.txt cpu.txt nvidia.txt atlas.txt sophon.txt; do
        req_path="requirements/$req_file"
        if [ -f "$req_path" ]; then
            log_success "✅ $req_file 存在"
            line_count=$(wc -l < "$req_path")
            echo "  包含 $line_count 行依赖"
        else
            log_warning "⚠️  $req_file 不存在"
        fi
    done
}

# 测试API服务启动
test_api_startup() {
    log_info "测试API服务启动（模拟模式）..."
    
    # 设置环境变量进行模拟测试
    export PLATFORM=cpu_x86
    export PYTHONPATH="$PROJECT_ROOT/src"
    
    # 创建临时模型文件
    mkdir -p models
    touch models/test.onnx
    
    # 测试API导入
    python3 -c "
import sys
sys.path.append('src')

try:
    from api.main import app
    print('✅ API模块导入成功')
except Exception as e:
    print(f'❌ API模块导入失败: {e}')

try:
    from inference.factory import InferenceFactory
    print('✅ 推理工厂导入成功')
except Exception as e:
    print(f'❌ 推理工厂导入失败: {e}')

try:
    from utils.platform_detector import auto_detect_platform
    platform = auto_detect_platform()
    print(f'✅ 平台检测成功: {platform}')
except Exception as e:
    print(f'❌ 平台检测失败: {e}')
"
    
    # 清理临时文件
    rm -f models/test.onnx
}

# 主测试流程
main() {
    echo "========================================"
    echo "🚀 AI Edge多平台兼容性测试"
    echo "========================================"
    
    test_platform_detection
    echo ""
    
    test_inference_factory
    echo ""
    
    test_config_loading
    echo ""
    
    test_requirements
    echo ""
    
    test_api_startup
    echo ""
    
    log_success "🎉 测试完成！"
    echo "========================================"
}

# 运行测试
main 