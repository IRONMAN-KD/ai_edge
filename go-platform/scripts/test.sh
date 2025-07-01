#!/bin/bash

# AI Edge Platform Test Script
# 用于测试 Golang 项目的脚本

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="ai-edge-platform"
PROJECT_ROOT=$(pwd)
COVERAGE_DIR="coverage"
TEST_RESULTS_DIR="test-results"
BENCH_RESULTS_DIR="bench-results"
COVERAGE_THRESHOLD=80
TEST_TIMEOUT="10m"

# 创建必要的目录
mkdir -p "$COVERAGE_DIR" "$TEST_RESULTS_DIR" "$BENCH_RESULTS_DIR"

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

log_test() {
    echo -e "${PURPLE}[TEST]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查测试依赖..."
    
    # 检查 Go
    if ! command -v go &> /dev/null; then
        log_error "Go 未安装或不在 PATH 中"
        exit 1
    fi
    
    # 检查 Go 版本
    local go_version
    go_version=$(go version | awk '{print $3}' | sed 's/go//')
    log_info "Go 版本: $go_version"
    
    # 检查测试工具
    local tools=("gofmt" "go" "goimports")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            log_success "$tool 可用"
        else
            log_warning "$tool 不可用"
        fi
    done
    
    log_success "依赖检查完成"
}

# 代码格式检查
check_format() {
    log_info "检查代码格式..."
    
    local format_issues=0
    
    # 检查 gofmt
    log_test "运行 gofmt 检查..."
    local gofmt_files
    gofmt_files=$(gofmt -l . 2>/dev/null || true)
    
    if [ -n "$gofmt_files" ]; then
        log_error "以下文件格式不正确:"
        echo "$gofmt_files"
        format_issues=$((format_issues + 1))
    else
        log_success "gofmt 检查通过"
    fi
    
    # 检查 goimports（如果可用）
    if command -v goimports &> /dev/null; then
        log_test "运行 goimports 检查..."
        local goimports_files
        goimports_files=$(goimports -l . 2>/dev/null || true)
        
        if [ -n "$goimports_files" ]; then
            log_error "以下文件导入格式不正确:"
            echo "$goimports_files"
            format_issues=$((format_issues + 1))
        else
            log_success "goimports 检查通过"
        fi
    fi
    
    if [ $format_issues -eq 0 ]; then
        log_success "代码格式检查通过"
        return 0
    else
        log_error "代码格式检查失败，发现 $format_issues 个问题"
        return 1
    fi
}

# 代码静态分析
static_analysis() {
    log_info "运行静态分析..."
    
    local analysis_issues=0
    
    # go vet
    log_test "运行 go vet..."
    if go vet ./...; then
        log_success "go vet 检查通过"
    else
        log_error "go vet 检查失败"
        analysis_issues=$((analysis_issues + 1))
    fi
    
    # golint（如果可用）
    if command -v golint &> /dev/null; then
        log_test "运行 golint..."
        local lint_output
        lint_output=$(golint ./... 2>/dev/null || true)
        
        if [ -n "$lint_output" ]; then
            log_warning "golint 发现以下问题:"
            echo "$lint_output"
        else
            log_success "golint 检查通过"
        fi
    fi
    
    # golangci-lint（如果可用）
    if command -v golangci-lint &> /dev/null; then
        log_test "运行 golangci-lint..."
        if golangci-lint run; then
            log_success "golangci-lint 检查通过"
        else
            log_error "golangci-lint 检查失败"
            analysis_issues=$((analysis_issues + 1))
        fi
    fi
    
    if [ $analysis_issues -eq 0 ]; then
        log_success "静态分析通过"
        return 0
    else
        log_error "静态分析失败，发现 $analysis_issues 个问题"
        return 1
    fi
}

# 运行单元测试
run_unit_tests() {
    log_info "运行单元测试..."
    
    local test_output_file="$TEST_RESULTS_DIR/unit_tests.out"
    local test_json_file="$TEST_RESULTS_DIR/unit_tests.json"
    
    log_test "执行单元测试（超时: $TEST_TIMEOUT）..."
    
    # 运行测试并生成输出
    if go test -v -timeout="$TEST_TIMEOUT" -json ./... > "$test_json_file" 2>&1; then
        log_success "单元测试通过"
        
        # 解析测试结果
        local total_tests
        local passed_tests
        local failed_tests
        local skipped_tests
        
        total_tests=$(grep '"Action":"run"' "$test_json_file" | wc -l | tr -d ' ')
        passed_tests=$(grep '"Action":"pass"' "$test_json_file" | wc -l | tr -d ' ')
        failed_tests=$(grep '"Action":"fail"' "$test_json_file" | wc -l | tr -d ' ')
        skipped_tests=$(grep '"Action":"skip"' "$test_json_file" | wc -l | tr -d ' ')
        
        log_info "测试统计:"
        log_info "  总计: $total_tests"
        log_info "  通过: $passed_tests"
        log_info "  失败: $failed_tests"
        log_info "  跳过: $skipped_tests"
        
        return 0
    else
        log_error "单元测试失败"
        
        # 显示失败的测试
        log_error "失败的测试:"
        grep '"Action":"fail"' "$test_json_file" | jq -r '.Test' 2>/dev/null || cat "$test_json_file"
        
        return 1
    fi
}

# 运行集成测试
run_integration_tests() {
    log_info "运行集成测试..."
    
    local integration_test_dir="tests/integration"
    
    if [ ! -d "$integration_test_dir" ]; then
        log_warning "集成测试目录不存在: $integration_test_dir"
        return 0
    fi
    
    local test_output_file="$TEST_RESULTS_DIR/integration_tests.out"
    
    log_test "执行集成测试..."
    
    if go test -v -timeout="$TEST_TIMEOUT" -tags=integration "$integration_test_dir/..." > "$test_output_file" 2>&1; then
        log_success "集成测试通过"
        return 0
    else
        log_error "集成测试失败"
        cat "$test_output_file"
        return 1
    fi
}

# 生成测试覆盖率
generate_coverage() {
    log_info "生成测试覆盖率报告..."
    
    local coverage_file="$COVERAGE_DIR/coverage.out"
    local coverage_html="$COVERAGE_DIR/coverage.html"
    local coverage_summary="$COVERAGE_DIR/coverage_summary.txt"
    
    log_test "运行覆盖率测试..."
    
    # 生成覆盖率数据
    if go test -coverprofile="$coverage_file" -covermode=atomic ./...; then
        log_success "覆盖率数据生成完成"
        
        # 生成 HTML 报告
        go tool cover -html="$coverage_file" -o="$coverage_html"
        log_success "HTML 覆盖率报告: $coverage_html"
        
        # 生成覆盖率摘要
        go tool cover -func="$coverage_file" > "$coverage_summary"
        
        # 计算总覆盖率
        local total_coverage
        total_coverage=$(go tool cover -func="$coverage_file" | grep "total:" | awk '{print $3}' | sed 's/%//')
        
        log_info "总覆盖率: ${total_coverage}%"
        
        # 检查覆盖率阈值
        if (( $(echo "$total_coverage >= $COVERAGE_THRESHOLD" | bc -l) )); then
            log_success "覆盖率达到要求（>= ${COVERAGE_THRESHOLD}%）"
            return 0
        else
            log_error "覆盖率未达到要求（< ${COVERAGE_THRESHOLD}%）"
            return 1
        fi
    else
        log_error "覆盖率测试失败"
        return 1
    fi
}

# 运行性能测试
run_benchmarks() {
    log_info "运行性能测试..."
    
    local bench_output="$BENCH_RESULTS_DIR/benchmarks.out"
    local bench_mem_output="$BENCH_RESULTS_DIR/benchmarks_mem.out"
    
    log_test "执行性能测试..."
    
    # 运行基准测试
    if go test -bench=. -benchmem -run=^$ ./... > "$bench_output" 2>&1; then
        log_success "性能测试完成"
        
        # 显示性能测试结果摘要
        log_info "性能测试结果摘要:"
        grep "Benchmark" "$bench_output" | head -10
        
        # 运行内存分析
        log_test "运行内存分析..."
        go test -bench=. -benchmem -memprofile="$BENCH_RESULTS_DIR/mem.prof" -run=^$ ./... > "$bench_mem_output" 2>&1
        
        return 0
    else
        log_error "性能测试失败"
        cat "$bench_output"
        return 1
    fi
}

# 运行竞态条件检测
run_race_tests() {
    log_info "运行竞态条件检测..."
    
    local race_output="$TEST_RESULTS_DIR/race_tests.out"
    
    log_test "执行竞态条件检测..."
    
    if go test -race -timeout="$TEST_TIMEOUT" ./... > "$race_output" 2>&1; then
        log_success "竞态条件检测通过"
        return 0
    else
        log_error "发现竞态条件"
        cat "$race_output"
        return 1
    fi
}

# 检查依赖安全性
check_security() {
    log_info "检查依赖安全性..."
    
    # 检查 go.mod 和 go.sum
    if [ ! -f "go.mod" ]; then
        log_warning "go.mod 文件不存在"
        return 0
    fi
    
    # 运行 go mod verify
    log_test "验证模块完整性..."
    if go mod verify; then
        log_success "模块完整性验证通过"
    else
        log_error "模块完整性验证失败"
        return 1
    fi
    
    # 检查已知漏洞（如果 govulncheck 可用）
    if command -v govulncheck &> /dev/null; then
        log_test "检查已知漏洞..."
        if govulncheck ./...; then
            log_success "未发现已知漏洞"
        else
            log_error "发现安全漏洞"
            return 1
        fi
    else
        log_warning "govulncheck 不可用，跳过漏洞检查"
    fi
    
    return 0
}

# 生成测试报告
generate_test_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="$TEST_RESULTS_DIR/test_report_$(date '+%Y%m%d_%H%M%S').html"
    
    log_info "生成测试报告: $report_file"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>AI Edge Platform 测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background-color: #d4edda; border-color: #c3e6cb; }
        .warning { background-color: #fff3cd; border-color: #ffeaa7; }
        .error { background-color: #f8d7da; border-color: #f5c6cb; }
        .code { background-color: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Edge Platform 测试报告</h1>
        <p>生成时间: $timestamp</p>
        <p>项目: $PROJECT_NAME</p>
    </div>
EOF
    
    # 添加测试结果摘要
    echo "    <div class='section'>" >> "$report_file"
    echo "        <h2>测试结果摘要</h2>" >> "$report_file"
    echo "        <table>" >> "$report_file"
    echo "            <tr><th>测试类型</th><th>状态</th><th>详情</th></tr>" >> "$report_file"
    
    # 这里可以添加各种测试结果的状态
    echo "            <tr><td>代码格式</td><td>-</td><td>请查看日志</td></tr>" >> "$report_file"
    echo "            <tr><td>静态分析</td><td>-</td><td>请查看日志</td></tr>" >> "$report_file"
    echo "            <tr><td>单元测试</td><td>-</td><td>请查看日志</td></tr>" >> "$report_file"
    echo "            <tr><td>覆盖率</td><td>-</td><td>请查看覆盖率报告</td></tr>" >> "$report_file"
    echo "            <tr><td>性能测试</td><td>-</td><td>请查看性能报告</td></tr>" >> "$report_file"
    
    echo "        </table>" >> "$report_file"
    echo "    </div>" >> "$report_file"
    
    # 添加覆盖率信息
    if [ -f "$COVERAGE_DIR/coverage_summary.txt" ]; then
        echo "    <div class='section'>" >> "$report_file"
        echo "        <h2>覆盖率详情</h2>" >> "$report_file"
        echo "        <div class='code'>" >> "$report_file"
        echo "            <pre>" >> "$report_file"
        cat "$COVERAGE_DIR/coverage_summary.txt" >> "$report_file"
        echo "            </pre>" >> "$report_file"
        echo "        </div>" >> "$report_file"
        echo "    </div>" >> "$report_file"
    fi
    
    # 添加性能测试结果
    if [ -f "$BENCH_RESULTS_DIR/benchmarks.out" ]; then
        echo "    <div class='section'>" >> "$report_file"
        echo "        <h2>性能测试结果</h2>" >> "$report_file"
        echo "        <div class='code'>" >> "$report_file"
        echo "            <pre>" >> "$report_file"
        grep "Benchmark" "$BENCH_RESULTS_DIR/benchmarks.out" >> "$report_file"
        echo "            </pre>" >> "$report_file"
        echo "        </div>" >> "$report_file"
        echo "    </div>" >> "$report_file"
    fi
    
    echo "</body>" >> "$report_file"
    echo "</html>" >> "$report_file"
    
    log_success "测试报告已生成: $report_file"
}

# 清理测试文件
cleanup_test_files() {
    log_info "清理测试文件..."
    
    # 清理临时文件
    find . -name "*.test" -delete 2>/dev/null || true
    find . -name "*.prof" -delete 2>/dev/null || true
    
    # 清理旧的测试结果（保留最近5次）
    if [ -d "$TEST_RESULTS_DIR" ]; then
        find "$TEST_RESULTS_DIR" -name "test_report_*.html" -type f | sort -r | tail -n +6 | xargs rm -f 2>/dev/null || true
    fi
    
    log_success "测试文件清理完成"
}

# 完整测试流程
full_test_suite() {
    log_info "=== 开始完整测试流程 ==="
    
    local start_time=$(date +%s)
    local failed_tests=0
    
    # 执行各项测试
    check_format || failed_tests=$((failed_tests + 1))
    static_analysis || failed_tests=$((failed_tests + 1))
    run_unit_tests || failed_tests=$((failed_tests + 1))
    generate_coverage || failed_tests=$((failed_tests + 1))
    run_benchmarks || failed_tests=$((failed_tests + 1))
    run_race_tests || failed_tests=$((failed_tests + 1))
    check_security || failed_tests=$((failed_tests + 1))
    
    # 运行集成测试（可选）
    run_integration_tests || true
    
    # 生成报告
    generate_test_report
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo
    log_info "=== 测试完成 ==="
    log_info "总耗时: ${duration} 秒"
    
    if [ $failed_tests -eq 0 ]; then
        log_success "所有测试通过！"
        return 0
    else
        log_error "$failed_tests 项测试失败"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [命令] [选项]

命令:
    all             运行完整测试套件
    format          检查代码格式
    lint            运行静态分析
    unit            运行单元测试
    integration     运行集成测试
    coverage        生成覆盖率报告
    bench           运行性能测试
    race            运行竞态条件检测
    security        检查安全性
    report          生成测试报告
    clean           清理测试文件

选项:
    -t, --timeout   设置测试超时时间（默认10m）
    -c, --coverage  设置覆盖率阈值（默认80）
    -h, --help      显示帮助信息

示例:
    $0 all                      # 运行完整测试套件
    $0 unit                     # 只运行单元测试
    $0 coverage                 # 生成覆盖率报告
    $0 --timeout 5m unit        # 设置5分钟超时运行单元测试
    $0 --coverage 90 coverage   # 设置90%覆盖率阈值
EOF
}

# 主函数
main() {
    local command="all"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -t|--timeout)
                TEST_TIMEOUT="$2"
                shift 2
                ;;
            -c|--coverage)
                COVERAGE_THRESHOLD="$2"
                shift 2
                ;;
            all|format|lint|unit|integration|coverage|bench|race|security|report|clean)
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
    
    # 显示测试信息
    log_info "=== AI Edge Platform 测试脚本 ==="
    log_info "项目: ${PROJECT_NAME}"
    log_info "命令: ${command}"
    log_info "超时: ${TEST_TIMEOUT}"
    log_info "覆盖率阈值: ${COVERAGE_THRESHOLD}%"
    echo
    
    # 检查依赖
    check_dependencies
    echo
    
    # 执行相应命令
    case $command in
        "all")
            full_test_suite
            ;;
        "format")
            check_format
            ;;
        "lint")
            static_analysis
            ;;
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "coverage")
            generate_coverage
            ;;
        "bench")
            run_benchmarks
            ;;
        "race")
            run_race_tests
            ;;
        "security")
            check_security
            ;;
        "report")
            generate_test_report
            ;;
        "clean")
            cleanup_test_files
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