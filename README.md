# 华为 AI Edge 智能小站 - 视觉识别算法系统

## 项目概述

本项目是一个基于华为 AI Edge 智能小站的视觉识别算法系统，支持多种深度学习模型，实现视频流接入、实时目标识别、告警管理和多协议推送功能。系统采用模块化设计，支持容器化部署，具备高性能、高可靠性和易扩展性。

## 主要功能

### 🎯 核心功能
- **多模型支持**: 支持YOLOv5、YOLOv8、人脸检测、车辆检测等多种算法模型
- **智能模型选择**: 提供交互式和程序化模型选择，支持场景化配置
- **实时视频处理**: 支持RTSP、USB摄像头、本地视频等多种视频源
- **目标检测识别**: 基于置信度阈值的目标检测和分类
- **告警管理**: 智能告警触发、防抖机制和图片保存
- **多协议推送**: 支持MQTT、HTTP、RabbitMQ、Kafka等多种推送协议
- **可视化显示**: 实时显示检测结果和性能信息

### 🔧 模型管理功能
- **模型配置管理**: 通过YAML配置文件管理多个算法模型
- **预设配置**: 提供高精度、平衡、高召回率、实时等多种预设模式
- **场景化配置**: 支持安防监控、交通监控、通用监控等应用场景
- **动态模型切换**: 支持运行时切换不同模型和配置
- **模型比较**: 提供模型性能对比和配置分析

### Web管理系统
- **模型管理**: 模型上传、版本管理、参数配置
- **任务配置**: 算法参数配置、视频流选择、检测区域绘制
- **告警管理**: 告警列表、详情查看、状态处理、批量操作
- **实时监控**: 系统状态监控、告警趋势分析

### 数据库支持
- **MySQL数据库**: 云端数据存储，支持模型、任务、告警数据管理
- **数据持久化**: 完整的CRUD操作和查询优化

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    视觉识别算法系统                           │
├─────────────────────────────────────────────────────────────┤
│  视频输入模块  │  模型管理器  │  告警管理  │  推送通知  │  可视化  │
├─────────────────────────────────────────────────────────────┤
│  模型选择器    │  配置解析器  │  图像处理  │  日志系统  │  性能监控 │
├─────────────────────────────────────────────────────────────┤
│                   华为 AI Edge 硬件平台                    │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- **硬件**: 华为 AI Edge 智能小站
- **操作系统**: Ubuntu 18.04+ 或 CentOS 7+
- **Python**: 3.8+
- **内存**: 4GB+
- **存储**: 10GB+

### 安装部署

1. **克隆项目**
```bash
git clone <repository_url>
cd ai_edge_hw
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置系统**
```bash
# 复制配置文件
cp config/config.yml.example config/config.yml
cp config/models.yml.example config/models.yml

# 编辑配置文件
vim config/config.yml
vim config/models.yml
```

4. **运行系统**
```bash
# 交互式模型选择运行
python main.py

# 使用默认配置运行
python main.py --no-interactive

# 查看可用模型
python main.py --list-models

# 查看可用场景
python main.py --list-scenarios

# 查看可用预设
python main.py --list-presets
```

## 模型选择功能

### 交互式模型选择

系统启动时会提供交互式模型选择界面：

```bash
python main.py
```

选择流程：
1. **选择配置模式**: 场景模式或自定义模式
2. **场景模式**: 根据应用场景自动选择模型和配置
3. **自定义模式**: 手动选择模型和预设配置

### 程序化模型选择

```python
from components.model_selector import ModelSelector

# 创建模型选择器
with ModelSelector() as selector:
    # 加载场景
    selector.load_from_config({
        'mode': 'scenario',
        'scenario_id': 'security_monitoring'
    })
    
    # 或加载特定模型
    selector.load_from_config({
        'mode': 'model',
        'model_id': 'yolov8',
        'preset_id': 'high_accuracy'
    })
    
    # 获取当前模型
    model = selector.get_current_model()
```

### 模型配置

在 `config/models.yml` 中配置模型：

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

model_presets:
  high_accuracy:
    confidence_threshold: 0.8
    nms_threshold: 0.3
    description: "高精度模式"

scenarios:
  security_monitoring:
    recommended_models: ["person_detection", "intrusion_detection"]
    preset: "balanced"
    alert_rules:
      - target_class: "person"
        min_confidence: 0.6
        alert_message: "检测到人员活动"
```

## 配置说明

### 主配置文件 (config/config.yml)

```yaml
# 视频输入配置
video_input:
  source: "rtsp://localhost:554/stream"
  fps: 30
  resolution: [1920, 1080]

# 模型配置
model:
  model_id: "yolov5"
  preset_id: "balanced"
  models_config_path: "config/models.yml"

# 告警配置
alert:
  confidence_threshold: 0.5
  debounce_time: 5
  save_images: true
  image_save_path: "alerts"

# 推送通知配置
push_notification:
  mqtt:
    enabled: true
    broker: "localhost"
    port: 1883
    topic: "vision/alerts"
```

### 模型配置文件 (config/models.yml)

包含以下配置：
- **models**: 算法模型定义
- **model_presets**: 预设配置模式
- **scenarios**: 应用场景配置

## 支持的模型

| 模型名称 | 类型 | 输入尺寸 | 支持类别 | 适用场景 |
|---------|------|----------|----------|----------|
| YOLOv5 | 目标检测 | 640x640 | 通用类别 | 通用监控 |
| YOLOv8 | 目标检测 | 640x640 | 扩展类别 | 高精度检测 |
| 人脸检测 | 人脸检测 | 320x320 | 人脸 | 安防监控 |
| 车辆检测 | 车辆检测 | 512x512 | 车辆类别 | 交通监控 |
| 人员检测 | 人员检测 | 416x416 | 人员 | 安防监控 |
| 入侵检测 | 入侵检测 | 640x640 | 人员/车辆 | 周界安防 |

## 预设配置模式

| 预设名称 | 置信度阈值 | NMS阈值 | 描述 |
|---------|-----------|---------|------|
| high_accuracy | 0.8 | 0.3 | 高精度模式，减少误报 |
| balanced | 0.6 | 0.4 | 平衡模式，精度和召回率均衡 |
| high_recall | 0.4 | 0.5 | 高召回率模式，减少漏检 |
| realtime | 0.5 | 0.4 | 实时模式，优先考虑处理速度 |

## 应用场景

### 安防监控场景
- **推荐模型**: 人员检测、入侵检测
- **预设配置**: 平衡模式
- **告警规则**: 检测到人员活动时触发告警

### 交通监控场景
- **推荐模型**: 车辆检测、YOLOv8
- **预设配置**: 平衡模式
- **告警规则**: 检测到车辆时触发告警

### 通用监控场景
- **推荐模型**: YOLOv5、YOLOv8
- **预设配置**: 平衡模式
- **告警规则**: 检测到目标对象时触发告警

## 容器化部署

### 构建镜像
```bash
./build_and_run.sh build
```

### 运行容器
```bash
./build_and_run.sh run
```

### 查看日志
```bash
./build_and_run.sh logs
```

### 停止容器
```bash
./build_and_run.sh stop
```

## 开发指南

### 添加新模型

1. **在 `config/models.yml` 中添加模型配置**
```yaml
models:
  new_model:
    name: "New Detection Model"
    type: "object_detection"
    model_path: "/opt/models/new_model.om"
    input_size: [640, 640]
    confidence_threshold: 0.5
    nms_threshold: 0.4
    classes: ["class1", "class2"]
    description: "新检测模型描述"
```

2. **实现模型推理逻辑**
在 `components/model_inference.py` 中添加新模型的推理实现。

### 添加新场景

1. **在 `config/models.yml` 中添加场景配置**
```yaml
scenarios:
  new_scenario:
    recommended_models: ["model1", "model2"]
    preset: "balanced"
    alert_rules:
      - target_class: "target"
        min_confidence: 0.6
        alert_message: "检测到目标"
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_model_manager.py

# 运行模型选择器演示
python scripts/model_selector_demo.py
```

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径是否正确
   - 确认模型文件格式是否支持
   - 查看日志获取详细错误信息

2. **视频源连接失败**
   - 检查网络连接
   - 确认视频源地址是否正确
   - 检查防火墙设置

3. **告警推送失败**
   - 检查推送服务配置
   - 确认网络连接
   - 查看推送服务日志

### 日志查看

```bash
# 查看系统日志
tail -f logs/vision_system.log

# 查看容器日志
docker logs vision-system

# 查看特定级别日志
grep "ERROR" logs/vision_system.log
```

## 性能优化

### 硬件优化
- 使用SSD存储提高I/O性能
- 增加内存容量
- 优化网络配置

### 软件优化
- 调整批处理大小
- 优化线程数量
- 使用GPU加速推理

### 配置优化
- 选择合适的预设模式
- 调整置信度阈值
- 优化图像预处理参数

## 安全建议

1. **网络安全**
   - 使用HTTPS进行安全通信
   - 配置防火墙规则
   - 定期更新系统补丁

2. **数据安全**
   - 加密敏感配置信息
   - 定期备份重要数据
   - 限制文件访问权限

3. **访问控制**
   - 使用强密码
   - 配置用户权限
   - 启用审计日志

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。请确保：

1. 代码符合项目规范
2. 添加必要的测试
3. 更新相关文档
4. 遵循提交信息规范

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com
- 文档: [项目文档](https://your-docs-url.com)

---

**注意**: 本项目专为华为 AI Edge 智能小站设计，在其他硬件平台上可能需要适配。 