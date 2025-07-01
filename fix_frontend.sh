#!/bin/bash
# 修复前端容器的问题

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始修复前端容器...${NC}"

# 停止前端容器
echo -e "${YELLOW}停止前端容器...${NC}"
docker-compose stop frontend
docker rm -f ai_edge_unified_frontend 2>/dev/null

# 修改nginx.conf文件
echo -e "${YELLOW}修改nginx.conf文件...${NC}"
sed -i.bak 's/proxy_pass http:\/\/api:8000/proxy_pass http:\/\/backend:8000/g' frontend/nginx.conf
echo -e "${GREEN}nginx.conf文件修改完成${NC}"

# 重新构建前端镜像
echo -e "${YELLOW}重新构建前端镜像...${NC}"
docker-compose build frontend

# 启动前端容器
echo -e "${YELLOW}启动前端容器...${NC}"
docker-compose up -d frontend

# 等待前端容器启动
echo -e "${YELLOW}等待前端容器启动...${NC}"
for i in {1..10}; do
    echo -n "."
    sleep 2
    
    # 检查容器状态
    STATUS=$(docker inspect --format='{{.State.Status}}' ai_edge_unified_frontend 2>/dev/null)
    if [ "$STATUS" = "running" ]; then
        echo -e "\n${GREEN}前端容器已成功启动!${NC}"
        break
    fi
    
    if [ $i -eq 10 ]; then
        echo -e "\n${RED}前端容器未能在超时时间内启动，请检查日志:${NC}"
        docker logs ai_edge_unified_frontend
    fi
done

echo -e "${GREEN}修复过程完成${NC}"
echo -e "${YELLOW}如果前端仍然有问题，请查看日志:${NC}"
echo -e "docker logs ai_edge_unified_frontend" 