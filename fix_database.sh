#!/bin/bash
# 修复数据库容器的问题

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始修复数据库容器...${NC}"

# 停止数据库容器
echo -e "${YELLOW}停止数据库容器...${NC}"
docker-compose stop db
docker rm -f ai_edge_unified_db 2>/dev/null

# 备份数据卷
echo -e "${YELLOW}备份数据卷(如果存在)...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backup_db_${TIMESTAMP}"
mkdir -p $BACKUP_DIR

# 检查数据卷是否存在
if docker volume inspect ai_edge_unified_db_data &>/dev/null; then
    echo -e "${YELLOW}找到数据卷，创建临时容器进行备份...${NC}"
    docker run --rm -v ai_edge_unified_db_data:/data -v $(pwd)/$BACKUP_DIR:/backup busybox tar -czf /backup/db_data.tar.gz -C /data .
    echo -e "${GREEN}数据卷已备份到 ${BACKUP_DIR}/db_data.tar.gz${NC}"
    
    # 删除旧的数据卷
    echo -e "${YELLOW}删除旧的数据卷...${NC}"
    docker volume rm ai_edge_unified_db_data
else
    echo -e "${YELLOW}未找到数据卷，将创建新的数据卷${NC}"
fi

# 创建新的数据库容器
echo -e "${YELLOW}创建新的数据库容器...${NC}"
docker-compose up -d db

# 等待数据库启动
echo -e "${YELLOW}等待数据库启动(最多60秒)...${NC}"
for i in {1..30}; do
    echo -n "."
    sleep 2
    
    # 检查健康状态
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ai_edge_unified_db 2>/dev/null)
    if [ "$HEALTH" = "healthy" ]; then
        echo -e "\n${GREEN}数据库已成功启动并处于健康状态!${NC}"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo -e "\n${RED}数据库未能在超时时间内启动，请检查日志:${NC}"
        docker logs ai_edge_unified_db
    fi
done

# 显示数据库容器信息
echo -e "${YELLOW}数据库容器信息:${NC}"
docker inspect ai_edge_unified_db | grep -A 5 "Health"

echo -e "${GREEN}修复过程完成${NC}"
echo -e "${YELLOW}如果数据库仍然有问题，请查看日志:${NC}"
echo -e "docker logs ai_edge_unified_db"
echo -e "${YELLOW}或者使用以下命令启动本地后端服务:${NC}"
echo -e "./run_local_backend.py --show-db-logs" 