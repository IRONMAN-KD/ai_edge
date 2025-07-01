#!/bin/bash

# 数据库迁移脚本
# 用于管理数据库迁移和种子数据

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

# 配置文件路径
CONFIG_FILE="config.yaml"

# 检查配置文件是否存在
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件 $CONFIG_FILE 不存在"
        exit 1
    fi
}

# 运行迁移
run_migration() {
    log_info "运行数据库迁移..."
    
    # 使用 Go 程序运行迁移
    go run cmd/migrate/main.go
    
    if [ $? -eq 0 ]; then
        log_success "数据库迁移完成"
    else
        log_error "数据库迁移失败"
        exit 1
    fi
}

# 创建种子数据
create_seed_data() {
    log_info "创建种子数据..."
    
    # 使用 Go 程序创建种子数据
    go run cmd/seed/main.go
    
    if [ $? -eq 0 ]; then
        log_success "种子数据创建完成"
    else
        log_error "种子数据创建失败"
        exit 1
    fi
}

# 重置数据库
reset_database() {
    log_warning "这将删除所有数据并重新创建数据库！"
    read -p "确定要继续吗？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "重置数据库..."
        
        # 删除数据库文件（如果使用 SQLite）
        if [ -f "data/app.db" ]; then
            rm -f data/app.db
            log_info "删除 SQLite 数据库文件"
        fi
        
        # 运行迁移
        run_migration
        
        # 创建种子数据
        create_seed_data
        
        log_success "数据库重置完成"
    else
        log_info "操作已取消"
    fi
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."
    
    BACKUP_DIR="backups"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    
    # 备份 SQLite 数据库
    if [ -f "data/app.db" ]; then
        BACKUP_FILE="$BACKUP_DIR/app_$TIMESTAMP.db"
        cp "data/app.db" "$BACKUP_FILE"
        log_success "数据库备份到: $BACKUP_FILE"
    else
        log_warning "未找到 SQLite 数据库文件"
    fi
    
    # 备份配置文件
    if [ -f "$CONFIG_FILE" ]; then
        CONFIG_BACKUP="$BACKUP_DIR/config_$TIMESTAMP.yaml"
        cp "$CONFIG_FILE" "$CONFIG_BACKUP"
        log_success "配置文件备份到: $CONFIG_BACKUP"
    fi
}

# 恢复数据库
restore_database() {
    if [ -z "$1" ]; then
        log_error "请指定备份文件路径"
        echo "用法: $0 restore <backup_file>"
        exit 1
    fi
    
    BACKUP_FILE="$1"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "备份文件不存在: $BACKUP_FILE"
        exit 1
    fi
    
    log_warning "这将覆盖当前数据库！"
    read -p "确定要继续吗？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "恢复数据库..."
        
        # 创建数据目录
        mkdir -p data
        
        # 恢复数据库文件
        cp "$BACKUP_FILE" "data/app.db"
        
        log_success "数据库恢复完成"
    else
        log_info "操作已取消"
    fi
}

# 检查数据库状态
check_database() {
    log_info "检查数据库状态..."
    
    # 使用 Go 程序检查数据库
    go run cmd/check/main.go
    
    if [ $? -eq 0 ]; then
        log_success "数据库状态正常"
    else
        log_error "数据库状态异常"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "数据库迁移脚本"
    echo
    echo "用法:"
    echo "  $0 migrate          运行数据库迁移"
    echo "  $0 seed             创建种子数据"
    echo "  $0 reset            重置数据库（删除所有数据）"
    echo "  $0 backup           备份数据库"
    echo "  $0 restore <file>   从备份文件恢复数据库"
    echo "  $0 check            检查数据库状态"
    echo "  $0 help             显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 migrate"
    echo "  $0 seed"
    echo "  $0 backup"
    echo "  $0 restore backups/app_20231201_120000.db"
}

# 主函数
main() {
    case "${1:-}" in
        "migrate")
            check_config
            run_migration
            ;;
        "seed")
            check_config
            create_seed_data
            ;;
        "reset")
            check_config
            reset_database
            ;;
        "backup")
            backup_database
            ;;
        "restore")
            restore_database "$2"
            ;;
        "check")
            check_config
            check_database
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        "")
            log_error "请指定操作"
            show_help
            exit 1
            ;;
        *)
            log_error "未知操作: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"