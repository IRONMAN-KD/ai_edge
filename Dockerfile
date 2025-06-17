# AI Edge 视觉识别系统 Dockerfile
# 基于华为 Atlas 官方基础镜像

FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app:$PYTHONPATH
ENV ASCEND_DEVICE_ID=0
ENV CONTAINER_ENV=true
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    gstreamer1.0-x \
    gstreamer1.0-alsa \
    gstreamer1.0-gl \
    gstreamer1.0-gtk3 \
    gstreamer1.0-qt5 \
    gstreamer1.0-pulseaudio \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    curl \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN python3 -m pip install --upgrade pip

# 复制依赖文件并安装 Python 依赖
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/config \
    /app/models \
    /app/alert_images \
    /app/logs \
    /app/videos \
    /app/tests

# 复制项目文件
COPY . .

# 设置文件权限
RUN chmod +x main.py

# 创建非 root 用户（可选，用于安全）
RUN groupadd -r atlas && useradd -r -g atlas atlas
RUN chown -R atlas:atlas /app
USER atlas

# 暴露端口（如果需要 HTTP 服务）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# 设置启动命令
CMD ["python3", "main.py", "--config", "/app/config/config.yml"] 