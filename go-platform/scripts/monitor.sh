#!/bin/bash

# AI Edge Platform Monitor Script
# 用于监控 Golang 项目运行状态的脚本

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
PROJECT_NAME="ai-edge-platform"
COMPOSE_FILE="deployments/docker-compose.yml"
API_URL="http://localhost:8080"
GRPC_URL="localhost:9090"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
REDIS_HOST="localhost"
REDIS_PORT="6379"
MONITOR_INTERVAL=5
LOG_FILE="logs/monitor.log"

# 创建日志目录
mkdir -p logs

# 日志函数
log_info() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
    echo -e "${BLUE}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

log_success() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1"
    echo -e "${GREEN}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

log_warning() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1"
    echo -e "${YELLOW}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

log_error() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1"
    echo -e "${RED}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

log_metric() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [METRIC] $1"
    echo -e "${PURPLE}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

# 检查 Docker 容器状态
check_containers() {
    log_info "检查容器状态..."
    
    local containers=("mysql" "redis" "api" "manager")
    local all_healthy=true
    
    for container in "${containers[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" ps "$container" | grep -q "Up"; then
            log_success "容器 $container 运行正常"
        else
            log_error "容器 $container 未运行或异常"
            all_healthy=false
        fi
    done
    
    if $all_healthy; then
        log_success "所有容器运行正常"
        return 0
    else
        log_error "部分容器运行异常"
        return 1
    fi
}

# 检查 API 服务健康状态
check_api_health() {
    log_info "检查 API 服务健康状态..."
    
    local health_url="$API_URL/health"
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" "$health_url" 2>/dev/null || echo "ERROR\n000")
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        log_success "API 服务健康检查通过"
        return 0
    else
        log_error "API 服务健康检查失败 (HTTP $http_code)"
        return 1
    fi
}

# 检查 gRPC 服务健康状态
check_grpc_health() {
    log_info "检查 gRPC 服务健康状态..."
    
    if command -v grpc_health_probe &> /dev/null; then
        if grpc_health_probe -addr="$GRPC_URL" > /dev/null 2>&1; then
            log_success "gRPC 服务健康检查通过"
            return 0
        else
            log_error "gRPC 服务健康检查失败"
            return 1
        fi
    else
        log_warning "grpc_health_probe 未安装，跳过 gRPC 健康检查"
        return 0
    fi
}

# 检查 MySQL 连接
check_mysql() {
    log_info "检查 MySQL 连接..."
    
    if command -v mysql &> /dev/null; then
        if mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u ai_edge -pai_edge_password -e "SELECT 1" ai_edge > /dev/null 2>&1; then
            log_success "MySQL 连接正常"
            return 0
        else
            log_error "MySQL 连接失败"
            return 1
        fi
    else
        log_warning "mysql 客户端未安装，跳过 MySQL 连接检查"
        return 0
    fi
}

# 检查 Redis 连接
check_redis() {
    log_info "检查 Redis 连接..."
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
            log_success "Redis 连接正常"
            return 0
        else
            log_error "Redis 连接失败"
            return 1
        fi
    else
        log_warning "redis-cli 未安装，跳过 Redis 连接检查"
        return 0
    fi
}

# 获取系统资源使用情况
get_system_metrics() {
    log_info "获取系统资源使用情况..."
    
    # CPU 使用率
    local cpu_usage
    if command -v top &> /dev/null; then
        cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
        log_metric "CPU 使用率: ${cpu_usage}%"
    fi
    
    # 内存使用情况
    local memory_info
    if command -v vm_stat &> /dev/null; then
        memory_info=$(vm_stat | head -4)
        log_metric "内存使用情况:\n$memory_info"
    fi
    
    # 磁盘使用情况
    local disk_usage
    disk_usage=$(df -h / | tail -1 | awk '{print $5}')
    log_metric "磁盘使用率: $disk_usage"
    
    # 网络连接数
    local connection_count
    if command -v netstat &> /dev/null; then
        connection_count=$(netstat -an | grep ESTABLISHED | wc -l | tr -d ' ')
        log_metric "网络连接数: $connection_count"
    fi
}

# 获取容器资源使用情况
get_container_metrics() {
    log_info "获取容器资源使用情况..."
    
    if command -v docker &> /dev/null; then
        local stats
        stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null || echo "无法获取容器统计信息")
        log_metric "容器资源使用情况:\n$stats"
    fi
}

# 获取应用指标
get_app_metrics() {
    log_info "获取应用指标..."
    
    # 获取 API 指标
    local metrics_url="$API_URL/metrics"
    local metrics_response
    
    metrics_response=$(curl -s "$metrics_url" 2>/dev/null || echo "无法获取应用指标")
    
    if [ "$metrics_response" != "无法获取应用指标" ]; then
        # 解析关键指标
        local request_count
        local error_count
        local response_time
        
        request_count=$(echo "$metrics_response" | grep "http_requests_total" | tail -1 | awk '{print $2}' || echo "N/A")
        error_count=$(echo "$metrics_response" | grep "http_requests_total.*5.." | awk '{print $2}' | paste -sd+ | bc 2>/dev/null || echo "N/A")
        response_time=$(echo "$metrics_response" | grep "http_request_duration_seconds" | tail -1 | awk '{print $2}' || echo "N/A")
        
        log_metric "HTTP 请求总数: $request_count"
        log_metric "HTTP 错误数: $error_count"
        log_metric "平均响应时间: $response_time 秒"
    else
        log_warning "无法获取应用指标"
    fi
}

# 检查日志错误
check_logs_for_errors() {
    log_info "检查应用日志中的错误..."
    
    local error_patterns=("ERROR" "FATAL" "panic" "exception")
    local recent_errors=0
    
    for pattern in "${error_patterns[@]}"; do
        local count
        count=$(docker-compose -f "$COMPOSE_FILE" logs --since="5m" 2>/dev/null | grep -i "$pattern" | wc -l | tr -d ' ')
        if [ "$count" -gt 0 ]; then
            log_warning "发现 $count 个 $pattern 级别的日志"
            recent_errors=$((recent_errors + count))
        fi
    done
    
    if [ $recent_errors -eq 0 ]; then
        log_success "最近5分钟内无错误日志"
    else
        log_error "最近5分钟内发现 $recent_errors 个错误日志"
    fi
    
    return $recent_errors
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    local disk_usage_percent
    disk_usage_percent=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$disk_usage_percent" -gt 90 ]; then
        log_error "磁盘空间不足，使用率: ${disk_usage_percent}%"
        return 1
    elif [ "$disk_usage_percent" -gt 80 ]; then
        log_warning "磁盘空间紧张，使用率: ${disk_usage_percent}%"
        return 0
    else
        log_success "磁盘空间充足，使用率: ${disk_usage_percent}%"
        return 0
    fi
}

# 检查网络连通性
check_network_connectivity() {
    log_info "检查网络连通性..."
    
    local test_urls=("google.com" "github.com")
    local failed_count=0
    
    for url in "${test_urls[@]}"; do
        if ping -c 1 -W 3000 "$url" > /dev/null 2>&1; then
            log_success "网络连通性检查通过: $url"
        else
            log_error "网络连通性检查失败: $url"
            failed_count=$((failed_count + 1))
        fi
    done
    
    if [ $failed_count -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# 生成健康报告
generate_health_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="logs/health_report_$(date '+%Y%m%d_%H%M%S').txt"
    
    log_info "生成健康报告: $report_file"
    
    cat > "$report_file" << EOF
=== AI Edge Platform 健康报告 ===
生成时间: $timestamp

=== 服务状态 ===
EOF
    
    # 检查各项服务并记录结果
    echo "容器状态:" >> "$report_file"
    if check_containers >> "$report_file" 2>&1; then
        echo "✓ 通过" >> "$report_file"
    else
        echo "✗ 失败" >> "$report_file"
    fi
    
    echo "\nAPI 健康检查:" >> "$report_file"
    if check_api_health >> "$report_file" 2>&1; then
        echo "✓ 通过" >> "$report_file"
    else
        echo "✗ 失败" >> "$report_file"
    fi
    
    echo "\ngRPC 健康检查:" >> "$report_file"
    if check_grpc_health >> "$report_file" 2>&1; then
        echo "✓ 通过" >> "$report_file"
    else
        echo "✗ 失败" >> "$report_file"
    fi
    
    echo "\nMySQL 连接:" >> "$report_file"
    if check_mysql >> "$report_file" 2>&1; then
        echo "✓ 通过" >> "$report_file"
    else
        echo "✗ 失败" >> "$report_file"
    fi
    
    echo "\nRedis 连接:" >> "$report_file"
    if check_redis >> "$report_file" 2>&1; then
        echo "✓ 通过" >> "$report_file"
    else
        echo "✗ 失败" >> "$report_file"
    fi
    
    echo "\n=== 系统资源 ===" >> "$report_file"
    get_system_metrics >> "$report_file" 2>&1
    
    echo "\n=== 容器资源 ===" >> "$report_file"
    get_container_metrics >> "$report_file" 2>&1
    
    echo "\n=== 应用指标 ===" >> "$report_file"
    get_app_metrics >> "$report_file" 2>&1
    
    echo "\n=== 错误日志检查 ===" >> "$report_file"
    check_logs_for_errors >> "$report_file" 2>&1
    
    echo "\n=== 磁盘空间检查 ===" >> "$report_file"
    check_disk_space >> "$report_file" 2>&1
    
    echo "\n=== 网络连通性检查 ===" >> "$report_file"
    check_network_connectivity >> "$report_file" 2>&1
    
    log_success "健康报告已生成: $report_file"
}

# 实时监控
real_time_monitor() {
    log_info "开始实时监控（每 $MONITOR_INTERVAL 秒检查一次）..."
    log_info "按 Ctrl+C 停止监控"
    
    local check_count=0
    
    while true; do
        check_count=$((check_count + 1))
        
        echo
        log_info "=== 第 $check_count 次检查 ==="
        
        # 基础健康检查
        local health_score=0
        local total_checks=6
        
        check_containers && health_score=$((health_score + 1))
        check_api_health && health_score=$((health_score + 1))
        check_grpc_health && health_score=$((health_score + 1))
        check_mysql && health_score=$((health_score + 1))
        check_redis && health_score=$((health_score + 1))
        check_disk_space && health_score=$((health_score + 1))
        
        # 计算健康分数
        local health_percentage=$((health_score * 100 / total_checks))
        
        if [ $health_percentage -eq 100 ]; then
            log_success "系统健康状态: 优秀 ($health_percentage%)"
        elif [ $health_percentage -ge 80 ]; then
            log_warning "系统健康状态: 良好 ($health_percentage%)"
        elif [ $health_percentage -ge 60 ]; then
            log_warning "系统健康状态: 一般 ($health_percentage%)"
        else
            log_error "系统健康状态: 异常 ($health_percentage%)"
        fi
        
        # 每10次检查生成一次详细报告
        if [ $((check_count % 10)) -eq 0 ]; then
            generate_health_report
        fi
        
        sleep $MONITOR_INTERVAL
    done
}

# 快速检查
quick_check() {
    log_info "=== 快速健康检查 ==="
    
    local issues=0
    
    check_containers || issues=$((issues + 1))
    check_api_health || issues=$((issues + 1))
    check_grpc_health || issues=$((issues + 1))
    check_mysql || issues=$((issues + 1))
    check_redis || issues=$((issues + 1))
    check_disk_space || issues=$((issues + 1))
    
    echo
    if [ $issues -eq 0 ]; then
        log_success "=== 所有检查通过，系统运行正常 ==="
        return 0
    else
        log_error "=== 发现 $issues 个问题，请检查日志 ==="
        return 1
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [命令] [选项]

命令:
    check           快速健康检查
    monitor         实时监控
    report          生成详细健康报告
    metrics         显示系统和应用指标
    logs            检查错误日志
    containers      检查容器状态
    services        检查服务健康状态
    resources       显示资源使用情况

选项:
    -i, --interval  设置监控间隔（秒，默认5）
    -h, --help      显示帮助信息

示例:
    $0 check                    # 快速健康检查
    $0 monitor                  # 开始实时监控
    $0 report                   # 生成健康报告
    $0 --interval 10 monitor    # 每10秒监控一次
EOF
}

# 主函数
main() {
    local command="check"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -i|--interval)
                MONITOR_INTERVAL="$2"
                shift 2
                ;;
            check|monitor|report|metrics|logs|containers|services|resources)
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
    
    # 显示监控信息
    log_info "=== AI Edge Platform 监控脚本 ==="
    log_info "项目: ${PROJECT_NAME}"
    log_info "命令: ${command}"
    echo
    
    # 执行相应命令
    case $command in
        "check")
            quick_check
            ;;
        "monitor")
            real_time_monitor
            ;;
        "report")
            generate_health_report
            ;;
        "metrics")
            get_system_metrics
            get_container_metrics
            get_app_metrics
            ;;
        "logs")
            check_logs_for_errors
            ;;
        "containers")
            check_containers
            get_container_metrics
            ;;
        "services")
            check_api_health
            check_grpc_health
            check_mysql
            check_redis
            ;;
        "resources")
            get_system_metrics
            check_disk_space
            check_network_connectivity
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 信号处理
trap 'log_info "监控已停止"; exit 0' INT TERM

# 执行主函数
main "$@"