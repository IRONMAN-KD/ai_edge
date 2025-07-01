#!/bin/bash
# 在容器内升级OpenCV和安装必要的依赖

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始升级容器内的OpenCV和依赖...${NC}"

# 复制测试脚本到容器
echo -e "${YELLOW}复制测试脚本到容器...${NC}"
docker cp test_rtsp_container.py ai_edge_api_cpu:/app/

# 安装系统依赖
echo -e "${YELLOW}安装系统依赖...${NC}"
docker exec -it ai_edge_api_cpu apt-get update
docker exec -it ai_edge_api_cpu apt-get install -y \
    libavutil-dev \
    libavfilter-dev \
    v4l-utils \
    python3-dev

# 升级OpenCV
echo -e "${YELLOW}升级OpenCV...${NC}"
docker exec -it ai_edge_api_cpu pip uninstall -y opencv-python opencv-python-headless
docker exec -it ai_edge_api_cpu pip install opencv-contrib-python-headless>=4.10.0

# 安装额外的依赖
echo -e "${YELLOW}安装额外的依赖...${NC}"
docker exec -it ai_edge_api_cpu pip install imageio[ffmpeg] av

# 复制修改后的video_input.py到容器
echo -e "${YELLOW}复制修改后的video_input.py到容器...${NC}"
docker cp src/components/video_input.py ai_edge_api_cpu:/app/src/components/

# 运行测试脚本
echo -e "${YELLOW}运行测试脚本...${NC}"
docker exec -it ai_edge_api_cpu python /app/test_rtsp_container.py --opencv-info --ffmpeg-test

echo -e "${GREEN}升级和测试完成!${NC}"
echo -e "${YELLOW}如果测试成功，请重启容器以应用更改:${NC}"
echo -e "docker restart ai_edge_api_cpu" 