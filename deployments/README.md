# AI Edge 多平台部署指南

## 概述

AI Edge 支持多种推理平台的部署，包括：
- **CPU**: 基于ONNX Runtime的CPU推理
- **NVIDIA GPU**: 基于TensorRT和ONNX Runtime GPU的加速推理  
- **华为Atlas NPU**: 基于昇腾AI处理器的NPU推理

## 目录结构

```
deployments/
├── config.yml              # 全局部署配置
├── deploy.py               # 部署管理脚本
├── start.sh                # 快速启动脚本
├── README.md               # 本文档
├── data/                   # 数据持久化目录
│   ├── mysql/             # MySQL数据
│   ├── redis/             # Redis数据
│   ├── models/            # 模型存储
│   ├── alert_images/      # 告警图片
│   └── logs/              # 日志文件
├── cpu/                    # CPU版本
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── config.yml
│   └── init.sql
├── nvidia_gpu/             # NVIDIA GPU版本
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── config.yml
│   └── init.sql
└── atlas_npu/              # 华为Atlas NPU版本
    ├── docker-compose.yml
    ├── Dockerfile.api
    ├── config.yml
    └── init.sql
```

## 快速开始

### 1. 使用快速启动脚本（推荐）

```bash
# 进入部署目录
cd deployments

# 快速启动（会提示选择平台）
./start.sh

# 指定平台启动
./start.sh --platform cpu

# 重新构建并启动
./start.sh --platform cpu --build

# 前台运行（查看日志）
./start.sh --platform cpu --foreground
```

### 2. 使用部署管理脚本

```bash
# 查看可用平台
python3 deploy.py list

# 设置当前平台
python3 deploy.py set cpu

# 查看平台信息
python3 deploy.py info

# 检查平台要求
python3 deploy.py check

# 部署
python3 deploy.py deploy

# 查看服务状态
python3 deploy.py status

# 查看日志
python3 deploy.py logs

# 停止服务
python3 deploy.py stop
```

## 平台要求

### CPU平台
- Docker和Docker Compose
- 无特殊硬件要求

### NVIDIA GPU平台
- Docker和Docker Compose
- NVIDIA GPU (计算能力 >= 6.0)
- NVIDIA Docker运行时
- NVIDIA驱动程序

### 华为Atlas NPU平台
- Docker和Docker Compose
- 华为Atlas系列NPU
- 昇腾CANN工具链
- Atlas驱动程序

## 配置说明

### 全局配置 (config.yml)

```yaml
deployment:
  platform: "cpu"          # 当前平台
  mode: "production"        # 部署模式
  ports:                    # 端口配置
    api: 8000
    frontend: 3000
    mysql: 3306
    redis: 6379
```

### 平台特定配置

每个平台都有自己的配置文件，位于对应目录下的 `config.yml`：

- `cpu/config.yml`: CPU推理配置
- `nvidia_gpu/config.yml`: GPU推理配置  
- `atlas_npu/config.yml`: NPU推理配置

## 服务访问

部署成功后，可以通过以下地址访问服务：

- **前端界面**: http://localhost:3000
- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **MySQL**: localhost:3306
- **Redis**: localhost:6379

## 模型管理

系统启动时不包含任何推理模型，需要通过前端界面上传和配置模型：

1. 访问前端界面 http://localhost:3000
2. 登录系统（默认用户名：admin，密码：admin123）
3. 进入模型管理页面
4. 上传对应平台的模型文件：
   - CPU: ONNX格式 (.onnx)
   - NVIDIA GPU: ONNX或TensorRT格式 (.onnx, .trt)
   - Atlas NPU: OM格式 (.om)
5. 配置模型参数并激活

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :8000
   # 停止其他服务或修改配置文件中的端口
   ```

2. **Docker权限问题**
   ```bash
   # 将用户添加到docker组
   sudo usermod -aG docker $USER
   # 重新登录或使用sudo运行
   ```

3. **NVIDIA GPU不可用**
   ```bash
   # 检查GPU状态
   nvidia-smi
   # 检查Docker GPU支持
   docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
   ```

4. **Atlas NPU设备不存在**
   ```bash
   # 检查NPU设备
   ls -la /dev/davinci*
   # 检查驱动安装
   ls /usr/local/Ascend/
   ```

### 日志查看

```bash
# 查看所有服务日志
python3 deploy.py logs

# 查看特定服务日志
python3 deploy.py logs --service api

# 跟踪日志
python3 deploy.py logs -f
```

### 数据备份

重要数据存储在 `data/` 目录下，建议定期备份：

```bash
# 备份数据目录
tar -czf ai_edge_backup_$(date +%Y%m%d).tar.gz data/

# 恢复数据
tar -xzf ai_edge_backup_YYYYMMDD.tar.gz
```

## 平台切换

系统支持在不同平台间切换：

```bash
# 停止当前平台
python3 deploy.py stop

# 切换到新平台
python3 deploy.py set nvidia_gpu

# 检查新平台要求
python3 deploy.py check

# 部署新平台
python3 deploy.py deploy
```

**注意**: 切换平台时，数据库中的模型配置可能需要重新设置，因为不同平台支持的模型格式不同。

## 生产环境建议

1. **安全配置**
   - 修改默认密码
   - 配置防火墙规则
   - 使用HTTPS

2. **性能优化**
   - 根据硬件调整并发配置
   - 配置合适的内存限制
   - 启用日志轮转

3. **监控告警**
   - 配置健康检查
   - 设置资源监控
   - 配置日志收集

4. **备份策略**
   - 定期备份数据库
   - 备份模型文件
   - 配置自动备份 