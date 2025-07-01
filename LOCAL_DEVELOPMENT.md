# AI Edge 本地开发指南

本指南将帮助你在本地环境中设置和运行AI Edge后端服务，同时使用Docker容器中的数据库和前端。

## 前提条件

- Python 3.8+
- Docker 和 Docker Compose
- Git
- 基本的命令行知识

## 设置步骤

### 1. 安装依赖

运行以下命令安装所有必要的依赖：

```bash
./setup_local_env.sh
```

这个脚本会：
- 创建Python虚拟环境
- 安装所有Python依赖
- 安装优化版的OpenCV和视频处理库
- 在macOS上安装系统依赖（如ffmpeg）

### 2. 激活虚拟环境

```bash
source venv/bin/activate
```

### 3. 启动本地后端服务

```bash
./run_local_backend.py
```

这个脚本会：
- 检查必要的Docker服务（数据库、Redis、前端）是否运行
- 如果需要，启动这些服务
- 设置正确的环境变量
- 在本地启动后端服务

## 访问服务

- **后端API**: http://localhost:8000
- **Swagger文档**: http://localhost:8000/docs
- **前端界面**: http://localhost:8080

## 开发工作流程

1. 在本地修改代码
2. 由于启用了`--reload`选项，后端服务会自动重新加载
3. 在浏览器中测试你的更改

## 调试技巧

### 查看日志

后端日志会直接输出到控制台。你也可以在`logs`目录中找到更详细的日志文件。

### 数据库访问

数据库通过端口`3307`暴露，你可以使用任何MySQL客户端连接：

```
主机: localhost
端口: 3307
用户名: ai_edge_user
密码: ai_edge_pass_2024
数据库: ai_edge
```

### 测试RTSP流

如果你需要测试RTSP流处理，可以使用之前创建的测试脚本：

```bash
python test_rtsp_container.py
```

## 故障排除

### 数据库连接问题

如果遇到数据库连接问题，请确保：
1. Docker容器正在运行：`docker ps`
2. 数据库端口已正确映射：`docker-compose ps`
3. 环境变量设置正确

### RTSP流问题

如果遇到RTSP流问题：
1. 确保ffmpeg已正确安装
2. 检查OpenCV版本和支持的编解码器
3. 尝试使用`test_rtsp_container.py`脚本进行测试

## 停止服务

按`Ctrl+C`停止本地后端服务。如果需要停止Docker容器：

```bash
docker-compose stop db redis frontend
```

或者停止所有容器：

```bash
docker-compose down
``` 