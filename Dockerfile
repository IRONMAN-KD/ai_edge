# AI Edge 视觉识别系统 Dockerfile
# 基于华为 Atlas 官方基础镜像

# Stage 1: Base Image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables to prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# Install system dependencies that might be needed by Python packages
# For example, if you were using a library that needed gcc
# RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Define the command to run the application
# Use the reloader in development, but not in production
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5001"]

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

# 创建必要的目录
RUN mkdir -p /app/config \
    /app/models \
    /app/alert_images \
    /app/logs \
    /app/videos \
    /app/tests

# 设置文件权限
RUN chmod +x main.py

# 创建非 root 用户（可选，用于安全）
RUN groupadd -r atlas && useradd -r -g atlas atlas
RUN chown -R atlas:atlas /app
USER atlas

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# 设置启动命令
CMD ["python3", "main.py", "--config", "/app/config/config.yml"] 