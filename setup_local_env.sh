#!/bin/bash
# 在本地环境安装必要的依赖

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始安装本地环境依赖...${NC}"

# 检查Python版本
python_version=$(python --version 2>&1)
if [[ $python_version == *"Python 3"* ]]; then
    echo -e "${GREEN}检测到Python版本: $python_version${NC}"
else
    echo -e "${RED}未检测到Python 3，请确保安装了Python 3${NC}"
    exit 1
fi

# 检查pip
if ! command -v pip &> /dev/null; then
    echo -e "${RED}未检测到pip，请先安装pip${NC}"
    exit 1
fi

# 创建虚拟环境
echo -e "${YELLOW}创建Python虚拟环境...${NC}"
python -m venv venv
source venv/bin/activate

# 升级pip
echo -e "${YELLOW}升级pip...${NC}"
pip install --upgrade pip

# 安装基础依赖
echo -e "${YELLOW}安装基础依赖...${NC}"
pip install -r requirements/base.txt

# 安装CPU依赖
echo -e "${YELLOW}安装CPU依赖...${NC}"
pip install -r requirements/cpu.txt

# 安装优化的OpenCV
echo -e "${YELLOW}安装优化的OpenCV...${NC}"
pip uninstall -y opencv-python opencv-python-headless
pip install opencv-contrib-python-headless>=4.10.0

# 安装额外的视频处理依赖
echo -e "${YELLOW}安装额外的视频处理依赖...${NC}"
pip install imageio[ffmpeg] av

# 安装开发工具
echo -e "${YELLOW}安装开发工具...${NC}"
pip install pytest pytest-cov black flake8 isort

# 安装系统依赖（仅限macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}检测到macOS，使用brew安装系统依赖...${NC}"
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo -e "${RED}未检测到Homebrew，请先安装Homebrew: https://brew.sh/${NC}"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${YELLOW}检测到Linux，请确保已安装ffmpeg和其他系统依赖${NC}"
    echo -e "${YELLOW}可以使用以下命令安装（Ubuntu/Debian）:${NC}"
    echo -e "sudo apt-get update && sudo apt-get install -y ffmpeg libavcodec-dev libavformat-dev libswscale-dev libavdevice-dev libavutil-dev libavfilter-dev"
fi

echo -e "${GREEN}本地环境依赖安装完成!${NC}"
echo -e "${YELLOW}请使用以下命令激活虚拟环境:${NC}"
echo -e "source venv/bin/activate"
echo -e "${YELLOW}然后运行以下命令启动本地后端:${NC}"
echo -e "python run_local_backend.py" 