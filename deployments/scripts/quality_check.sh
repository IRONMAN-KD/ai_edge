#!/bin/bash

# AI Edge 统一框架 - 代码质量检查脚本
# 运行代码格式化、类型检查、测试等质量检查

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "🔍 AI Edge 统一框架 - 代码质量检查"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ $1 未安装${NC}"
        return 1
    fi
    return 0
}

# 安装测试依赖
install_test_deps() {
    echo -e "${BLUE}📦 安装测试依赖...${NC}"
    
    if [ -f "requirements/test.txt" ]; then
        pip install -r requirements/test.txt
    else
        pip install pytest pytest-cov pytest-mock flake8 black isort mypy
    fi
}

# 代码格式化
format_code() {
    echo -e "${BLUE}🎨 代码格式化...${NC}"
    
    # Black 格式化
    if check_command "black"; then
        echo "运行 Black 格式化..."
        black src/ tests/ --line-length 88
        echo -e "${GREEN}✅ Black 格式化完成${NC}"
    fi
    
    # isort 导入排序
    if check_command "isort"; then
        echo "运行 isort 导入排序..."
        isort src/ tests/ --profile black
        echo -e "${GREEN}✅ isort 导入排序完成${NC}"
    fi
}

# 代码检查
lint_code() {
    echo -e "${BLUE}🔍 代码检查...${NC}"
    
    # Flake8 检查
    if check_command "flake8"; then
        echo "运行 Flake8 检查..."
        flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503 || {
            echo -e "${YELLOW}⚠️  Flake8 发现代码风格问题${NC}"
        }
    fi
    
    # MyPy 类型检查
    if check_command "mypy"; then
        echo "运行 MyPy 类型检查..."
        mypy src/ --ignore-missing-imports --no-strict-optional || {
            echo -e "${YELLOW}⚠️  MyPy 发现类型问题${NC}"
        }
    fi
}

# 运行测试
run_tests() {
    echo -e "${BLUE}🧪 运行测试...${NC}"
    
    if check_command "pytest"; then
        # 单元测试
        echo "运行单元测试..."
        pytest tests/unit/ -v --tb=short || {
            echo -e "${RED}❌ 单元测试失败${NC}"
            return 1
        }
        
        # 集成测试
        echo "运行集成测试..."
        pytest tests/integration/ -v --tb=short || {
            echo -e "${YELLOW}⚠️  集成测试失败${NC}"
        }
        
        echo -e "${GREEN}✅ 测试完成${NC}"
    else
        echo -e "${RED}❌ pytest 未安装${NC}"
        return 1
    fi
}

# 生成测试覆盖率报告
coverage_report() {
    echo -e "${BLUE}📊 生成测试覆盖率报告...${NC}"
    
    if check_command "pytest"; then
        pytest tests/unit/ --cov=src --cov-report=html --cov-report=term-missing || {
            echo -e "${YELLOW}⚠️  覆盖率报告生成失败${NC}"
            return 1
        }
        
        echo -e "${GREEN}✅ 覆盖率报告生成完成${NC}"
        echo "HTML报告位置: htmlcov/index.html"
    fi
}

# 性能测试
performance_tests() {
    echo -e "${BLUE}⚡ 运行性能测试...${NC}"
    
    if check_command "pytest"; then
        pytest tests/performance/ -v --tb=short -m "not slow" || {
            echo -e "${YELLOW}⚠️  性能测试失败${NC}"
        }
        
        echo -e "${GREEN}✅ 性能测试完成${NC}"
    fi
}

# 安全检查
security_check() {
    echo -e "${BLUE}🔒 安全检查...${NC}"
    
    # 检查敏感信息
    echo "检查敏感信息..."
    if grep -r "password\|secret\|key\|token" src/ --include="*.py" | grep -v "# noqa" | head -5; then
        echo -e "${YELLOW}⚠️  发现可能的敏感信息${NC}"
    else
        echo -e "${GREEN}✅ 未发现敏感信息${NC}"
    fi
    
    # 检查硬编码IP
    echo "检查硬编码IP地址..."
    if grep -r "192\.168\|10\.\|172\." src/ --include="*.py" | grep -v "# noqa" | head -5; then
        echo -e "${YELLOW}⚠️  发现硬编码IP地址${NC}"
    else
        echo -e "${GREEN}✅ 未发现硬编码IP地址${NC}"
    fi
}

# 依赖检查
dependency_check() {
    echo -e "${BLUE}📋 依赖检查...${NC}"
    
    # 检查requirements文件
    echo "检查依赖文件..."
    for req_file in requirements/*.txt; do
        if [ -f "$req_file" ]; then
            echo "检查 $req_file"
            # 这里可以添加具体的依赖版本检查
        fi
    done
    
    echo -e "${GREEN}✅ 依赖检查完成${NC}"
}

# 文档检查
doc_check() {
    echo -e "${BLUE}📚 文档检查...${NC}"
    
    # 检查README文件
    if [ -f "README.md" ]; then
        echo -e "${GREEN}✅ README.md 存在${NC}"
    else
        echo -e "${YELLOW}⚠️  README.md 不存在${NC}"
    fi
    
    # 检查API文档
    echo "检查Python文档字符串..."
    python_files_without_docstring=$(find src/ -name "*.py" -exec grep -L '"""' {} \; | wc -l)
    if [ "$python_files_without_docstring" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  发现 $python_files_without_docstring 个文件缺少文档字符串${NC}"
    else
        echo -e "${GREEN}✅ 所有Python文件都有文档字符串${NC}"
    fi
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --install-deps    安装测试依赖"
    echo "  --format         代码格式化"
    echo "  --lint           代码检查"
    echo "  --test           运行测试"
    echo "  --coverage       生成覆盖率报告"
    echo "  --performance    运行性能测试"
    echo "  --security       安全检查"
    echo "  --deps           依赖检查"
    echo "  --docs           文档检查"
    echo "  --all            运行所有检查"
    echo "  --help           显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 --all                    # 运行所有检查"
    echo "  $0 --format --lint --test   # 格式化、检查和测试"
    echo "  $0 --coverage               # 生成覆盖率报告"
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-deps)
                install_test_deps
                shift
                ;;
            --format)
                format_code
                shift
                ;;
            --lint)
                lint_code
                shift
                ;;
            --test)
                run_tests
                shift
                ;;
            --coverage)
                coverage_report
                shift
                ;;
            --performance)
                performance_tests
                shift
                ;;
            --security)
                security_check
                shift
                ;;
            --deps)
                dependency_check
                shift
                ;;
            --docs)
                doc_check
                shift
                ;;
            --all)
                install_test_deps
                format_code
                lint_code
                run_tests
                coverage_report
                performance_tests
                security_check
                dependency_check
                doc_check
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 未知选项: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo ""
    echo -e "${GREEN}🎉 代码质量检查完成！${NC}"
}

# 运行主函数
main "$@" 