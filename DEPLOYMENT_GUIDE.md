# AI Edge 视觉识别系统部署指南

本文档详细说明如何在华为 AI Edge 智能小站上部署视觉识别系统。

## 部署前准备

### 1. 硬件环境检查

确保 AI Edge 设备满足以下要求：

```bash
# 检查系统信息
cat /etc/os-release
uname -a

# 检查内存
free -h

# 检查存储空间
df -h

# 检查 Atlas NPU 设备
ls -la /dev/davinci*
ls -la /dev/hisi_hdc
```

### 2. 软件环境准备

#### 安装 Docker

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
```

#### 安装 Docker Compose

```bash
# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

#### 安装华为 Atlas SDK

```bash
# 下载 CANN Toolkit
# 访问华为官方下载页面获取最新版本

# 安装 CANN Toolkit
sudo dpkg -i Ascend-cann-toolkit_*.run

# 设置环境变量
echo 'export ASCEND_HOME=/usr/local/Ascend' >> ~/.bashrc
echo 'export PATH=$ASCEND_HOME/ascend-toolkit/latest/compiler/ccec_compiler/bin:$PATH' >> ~/.bashrc
echo 'export PATH=$ASCEND_HOME/ascend-toolkit/latest/compiler/bin:$PATH' >> ~/.bashrc
echo 'export ASCEND_OPP_PATH=$ASCEND_HOME/ascend-toolkit/latest/opp' >> ~/.bashrc
echo 'export TOOLCHAIN_HOME=$ASCEND_HOME/ascend-toolkit/latest/toolkit' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$ASCEND_HOME/ascend-toolkit/latest/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export PYTHONPATH=$ASCEND_HOME/ascend-toolkit/latest/python/site-packages:$PYTHONPATH' >> ~/.bashrc

source ~/.bashrc
```

## 项目部署

### 1. 获取项目代码

```bash
# 克隆项目
git clone <repository-url>
cd atlas_vision_system

# 或者下载并解压
wget <download-url>
tar -xzf atlas_vision_system.tar.gz
cd atlas_vision_system
```

### 2. 准备模型文件

#### 模型转换

如果您有 ONNX 或 TensorFlow 模型，需要转换为 OM 格式：

```bash
# 从 ONNX 转换
atc --model=model.onnx \
    --framework=5 \
    --output=model \
    --soc_version=Ascend310 \
    --input_shape="input:1,3,640,640" \
    --input_format=NCHW \
    --output_type=FP32

# 从 TensorFlow 转换
atc --model=model.pb \
    --framework=3 \
    --output=model \
    --soc_version=Ascend310 \
    --input_shape="input:1,640,640,3" \
    --input_format=NHWC
```

#### 放置模型文件

```bash
# 创建模型目录
mkdir -p models

# 复制模型文件
cp model.om models/model.om
```

### 3. 配置系统

#### 编辑配置文件

```bash
# 编辑配置文件
vim config/config.yml
```

根据您的环境修改以下配置：

```yaml
# 视频源配置
video:
  source: "rtsp://192.168.1.100:554/stream"  # 修改为您的视频源
  # source: "/dev/video0"                    # USB 摄像头
  # source: "/app/videos/test.mp4"           # 本地视频文件

# 模型配置
model:
  path: "/app/models/model.om"               # 确保模型文件存在

# 告警配置
alert:
  debounce_time: 60                          # 防抖时间（秒）
  save_images: true                          # 是否保存告警图片

# 推送配置
mqtt:
  enabled: true
  broker: "192.168.1.200"                    # 修改为您的 MQTT 服务器
  username: "atlas_user"
  password: "atlas_pass"
  topic: "atlas/alerts"
```

### 4. 创建必要目录

```bash
# 创建目录结构
mkdir -p config models alert_images logs videos tests

# 设置权限
chmod 755 config models alert_images logs videos tests
```

## 部署方式

### 方式一：使用构建脚本（推荐）

```bash
# 给脚本执行权限
chmod +x build_and_run.sh

# 构建镜像
./build_and_run.sh build

# 运行容器
./build_and_run.sh run

# 查看日志
./build_and_run.sh logs

# 查看状态
./build_and_run.sh status

# 停止容器
./build_and_run.sh stop
```

### 方式二：使用 Docker Compose

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f atlas-vision-system

# 停止服务
docker-compose down
```

### 方式三：使用 Docker 命令

```bash
# 构建镜像
docker build -t atlas-vision-system .

# 运行容器
docker run -d \
  --name atlas-vision-system \
  --restart unless-stopped \
  --device=/dev/davinci0 \
  --device=/dev/davinci_manager \
  --device=/dev/hisi_hdc \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/models:/app/models:ro \
  -v $(pwd)/alert_images:/app/alert_images \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/videos:/app/videos:ro \
  --network host \
  -e CONTAINER_ENV=true \
  -e ASCEND_DEVICE_ID=0 \
  atlas-vision-system
```

## 验证部署

### 1. 检查容器状态

```bash
# 查看容器运行状态
docker ps

# 查看容器日志
docker logs -f atlas-vision-system

# 进入容器
docker exec -it atlas-vision-system bash
```

### 2. 检查系统功能

```bash
# 检查 Atlas NPU 设备
docker exec atlas-vision-system ls -la /dev/davinci*

# 检查模型文件
docker exec atlas-vision-system ls -la /app/models/

# 检查配置文件
docker exec atlas-vision-system cat /app/config/config.yml
```

### 3. 性能监控

```bash
# 查看容器资源使用
docker stats atlas-vision-system

# 查看系统日志
tail -f logs/atlas_vision_$(date +%Y%m%d).log

# 查看告警图片
ls -la alert_images/
```

## 故障排除

### 常见问题及解决方案

#### 1. 容器启动失败

**问题**: 容器无法启动或立即退出

**解决方案**:
```bash
# 查看详细错误信息
docker logs atlas-vision-system

# 检查配置文件语法
docker exec atlas-vision-system python3 -c "import yaml; yaml.safe_load(open('/app/config/config.yml'))"

# 检查模型文件
ls -la models/model.om
```

#### 2. Atlas NPU 设备访问失败

**问题**: 无法访问 Atlas NPU 设备

**解决方案**:
```bash
# 检查设备权限
ls -la /dev/davinci*

# 添加用户到设备组
sudo usermod -a -G video $USER

# 重新启动容器
docker restart atlas-vision-system
```

#### 3. 视频源连接失败

**问题**: 无法连接到视频源

**解决方案**:
```bash
# 测试网络连接
ping <video-source-ip>

# 测试 RTSP 流
ffmpeg -i rtsp://<ip>:<port>/stream -t 5 -f null -

# 检查 USB 摄像头
ls -la /dev/video*
```

#### 4. 推送失败

**问题**: 告警推送失败

**解决方案**:
```bash
# 检查网络连接
ping <push-server-ip>

# 测试 MQTT 连接
mosquitto_pub -h <broker-ip> -t test/topic -m "test message"

# 检查推送配置
docker exec atlas-vision-system cat /app/config/config.yml | grep -A 10 mqtt
```

#### 5. 性能问题

**问题**: 推理速度慢或 FPS 低

**解决方案**:
```bash
# 检查系统资源
htop
nvidia-smi  # 如果有 GPU

# 调整视频分辨率
# 修改 config/config.yml 中的 video.width 和 video.height

# 优化模型输入尺寸
# 修改 config/config.yml 中的 model.input_width 和 model.input_height
```

### 调试模式

启用调试日志：

```bash
# 停止当前容器
docker stop atlas-vision-system

# 以调试模式运行
docker run -it \
  --name atlas-vision-system-debug \
  --device=/dev/davinci0 \
  --device=/dev/davinci_manager \
  --device=/dev/hisi_hdc \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/models:/app/models:ro \
  -v $(pwd)/alert_images:/app/alert_images \
  -v $(pwd)/logs:/app/logs \
  --network host \
  -e CONTAINER_ENV=true \
  -e ASCEND_DEVICE_ID=0 \
  -e LOG_LEVEL=DEBUG \
  atlas-vision-system
```

## 维护和监控

### 1. 日志管理

```bash
# 查看实时日志
tail -f logs/atlas_vision_$(date +%Y%m%d).log

# 查看错误日志
grep ERROR logs/atlas_vision_*.log

# 清理旧日志
find logs/ -name "*.log" -mtime +7 -delete
```

### 2. 性能监控

```bash
# 创建监控脚本
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    docker stats atlas-vision-system --no-stream
    echo "=== 告警统计 ==="
    ls -1 alert_images/ | wc -l
    echo "=== 日志大小 ==="
    du -sh logs/
    sleep 60
done
EOF

chmod +x monitor.sh
./monitor.sh
```

### 3. 备份和恢复

```bash
# 备份配置和数据
tar -czf backup_$(date +%Y%m%d).tar.gz config/ models/ alert_images/ logs/

# 恢复备份
tar -xzf backup_20240101.tar.gz
```

### 4. 更新系统

```bash
# 停止当前服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

## 安全建议

### 1. 网络安全

```bash
# 配置防火墙
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 1883  # MQTT
sudo ufw allow 8080  # HTTP

# 使用 VPN 或内网访问
```

### 2. 容器安全

```bash
# 使用非 root 用户运行
# 已在 Dockerfile 中配置

# 限制容器资源
docker run --memory=2g --cpus=1.0 ...

# 定期更新基础镜像
docker pull ascendhub.huawei.com/public-ascendhub/infer-modelzoo:latest
```

### 3. 数据安全

```bash
# 加密敏感配置
# 使用环境变量存储密码

# 定期备份数据
# 设置自动备份脚本
```

## 性能优化

### 1. 系统优化

```bash
# 调整系统参数
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
sysctl -p

# 优化文件系统
sudo tune2fs -o journal_data_writeback /dev/sda1
```

### 2. 容器优化

```bash
# 使用多阶段构建
# 优化镜像大小

# 调整容器参数
docker run --shm-size=1g --ulimit memlock=-1 ...
```

### 3. 应用优化

```bash
# 调整视频处理参数
# 优化模型推理批次大小
# 使用异步处理
```

## 联系支持

如果遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查系统日志和容器日志
3. 提交 GitHub Issue
4. 联系技术支持团队

---

**注意**: 本文档基于 AI Edge 智能小站环境编写，在其他环境部署时可能需要相应调整。 