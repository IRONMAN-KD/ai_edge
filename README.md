# 兆慧 AI Edge 边缘视觉识别算法系统

## 项目简介

本项目为"兆慧 AI Edge 智能小站"视觉识别算法系统，支持多种深度学习模型，实现视频流接入、实时目标检测、告警管理、推送通知、Web 可视化管理等功能。系统采用前后端分离架构，支持容器化一键部署，适用于安防、交通、工业等多场景。

---

## 主要功能

- **多模型支持**：支持 YOLOv5、YOLOv8、人脸检测、车辆检测等多种算法模型
- **智能模型选择**：支持场景化配置与动态切换
- **实时视频处理**：支持 RTSP、USB 摄像头、本地视频等多种输入
- **目标检测与告警**：基于置信度阈值的目标检测、智能告警、防抖机制、图片快照
- **多协议推送**：支持 MQTT、HTTP、RabbitMQ、Kafka 等
- **Web 管理系统**：模型管理、任务配置、告警管理、系统监控
- **数据库持久化**：MySQL 存储模型、任务、告警等数据

---

## 系统架构

```
┌──────────────────────────────────────────────┐
│                前端 Web 管理系统              │
│  Vue3 + Element Plus，实时监控与配置管理      │
└──────────────────────────────────────────────┘
                │         ↑
                │ RESTful│
                ↓         │
┌──────────────────────────────────────────────┐
│                后端服务 API                  │
│  FastAPI + MySQL，模型推理、告警、推送        │
└──────────────────────────────────────────────┘
                │
                ↓
┌──────────────────────────────────────────────┐
│                AI 推理服务                   │
│  多模型推理、视频流处理、图片分析             │
└──────────────────────────────────────────────┘
                │
                ↓
┌──────────────────────────────────────────────┐
│                数据库（MySQL）               │
└──────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 环境准备

- 推荐硬件：华为 AI Edge 智能小站或 x86_64 服务器
- 操作系统：Ubuntu 18.04+/CentOS 7+/macOS
- Python 3.8+
- Docker & Docker Compose

### 2. 一键部署

```bash
git clone <your_repo_url>
cd ai_edge_hw
# 推荐使用 Docker Compose 部署
docker-compose up -d
```

### 3. 手动开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库（如需本地开发）
python scripts/init_database.py
```

### 4. 前端启动（开发模式）

```bash
cd frontend
npm install
npm run dev
```

### 5. 访问系统

- 前端管理页面：http://localhost:8080
- 后端 API 文档：http://localhost:5001/docs

---

## 配置说明

### 1. 主配置文件 `config/config.yml`

```yaml
video_input:
  source: "rtsp://localhost:554/stream"
  fps: 30
  resolution: [1920, 1080]

model:
  model_id: "yolov5"
  preset_id: "balanced"
  models_config_path: "config/models.yml"

alert:
  confidence_threshold: 0.5
  debounce_time: 5
  save_images: true
  image_save_path: "alerts"

push_notification:
  mqtt:
    enabled: true
    broker: "localhost"
```

### 2. 模型配置文件 `config/models.yml`

```yaml
models:
  yolov5:
    name: "YOLOv5 Object Detection"
    type: "object_detection"
    model_path: "/opt/models/yolov5s.om"
    input_size: [640, 640]
    confidence_threshold: 0.5
    nms_threshold: 0.4
    classes: ["person", "car", "truck"]
    description: "YOLOv5目标检测模型"
```

---

## 前端说明

- 技术栈：Vue3 + Element Plus + Vite
- 主要页面：模型管理、任务配置、告警管理、系统设置、实时监控
- 代码入口：`frontend/src/main.js`
- 运行命令：`npm run dev`（开发）/ `npm run build`（生产）

---

## 后端说明

- 技术栈：FastAPI + MySQL + SQLAlchemy
- 主要目录：
  - `api/`：后端主服务
  - `components/`：推理、告警、推送等核心模块
  - `database/`：数据库模型与操作
  - `inference/`：推理服务
  - `config/`：配置文件
- 运行命令：`python api/main.py`（开发）

---

## 数据库说明

- 使用 MySQL 8，表结构和初始化脚本见 `database/init.sql`
- 支持自动建表和初始化数据

---

## 常见问题

- **数据库连接失败**：请确保数据库容器已启动，配置文件中的主机、端口、用户名、密码正确。
- **模型推理失败**：请检查模型文件路径和格式，确保模型已正确加载。
- **前端无法访问**：请确认前端容器已启动，或本地开发端口未被占用。

---

## 贡献与反馈

欢迎提交 Issue 或 PR，或通过邮件联系开发团队。

---

## License

MIT

---

如需更详细的定制内容或补充，请告知！ 