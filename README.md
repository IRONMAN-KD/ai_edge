# AI Edge 统一平台

## 项目概述

AI Edge 是一个统一的边缘计算视觉分析平台，支持多种硬件平台（CPU、NVIDIA GPU、Atlas NPU、Sophon等），实现视频流处理、对象检测和告警功能。

## 目录结构

```
ai_edge_unified/
├── configs/                  # 配置文件
│   ├── base/                 # 基础配置
│   └── platforms/            # 平台特定配置
│       ├── atlas_npu/
│       ├── cpu_arm/
│       ├── cpu_x86/
│       ├── nvidia_gpu/
│       └── sophon/
├── deployments/              # 部署相关文件
│   ├── atlas_npu/           # Atlas NPU部署
│   ├── cpu/                 # CPU部署
│   ├── data/                # 数据目录（模型、日志等）
│   ├── docs/                # 部署文档
│   ├── nvidia_gpu/          # NVIDIA GPU部署
│   ├── scripts/             # 部署脚本
│   └── sophon/              # Sophon部署
├── frontend/                # 前端代码
├── models/                  # 模型文件
│   ├── atlas/              # Atlas平台模型
│   ├── onnx/               # ONNX格式模型（主要使用）
│   ├── sophon/             # Sophon平台模型
│   └── tensorrt/           # TensorRT模型
├── requirements/            # 依赖文件
├── src/                     # 源代码
│   ├── api/                # API接口
│   ├── components/         # 组件
│   ├── database/           # 数据库操作
│   ├── inference/          # 推理引擎
│   └── utils/              # 工具函数
├── tests/                   # 测试代码
└── docker-compose.yml       # Docker Compose配置
```

## 项目清理说明

本项目已经进行了全面清理：

1. 删除了所有Python缓存文件（`__pycache__`目录和`.pyc`文件）
2. 清理了日志文件
3. 删除了重复的模型文件，仅保留`models/onnx`目录下的模型作为主要模型
4. 清理了临时文件和系统文件（如`.DS_Store`）
5. 备份并清理了历史归档文件

清理脚本位于项目根目录：`cleanup_project.py`，可以使用以下命令运行：

```bash
python3 cleanup_project.py [--dry-run] [--skip-archives] [--skip-pycache] [--skip-logs] [--skip-temp] [--skip-models]
```

## 模型文件

主要模型文件位于`models/onnx`目录下：

- `person.onnx` - 人员检测模型

## 部署说明

请参考`deployments/docs`目录下的文档进行部署。

## 依赖安装

```bash
# 安装基础依赖
pip install -r requirements/base.txt

# 根据平台安装特定依赖
# CPU平台
pip install -r requirements/cpu.txt
# NVIDIA GPU平台
pip install -r requirements/nvidia.txt
# Atlas NPU平台
pip install -r requirements/atlas.txt
```

## 运行

```bash
# 本地开发运行
python run_local.py

# 统一平台启动
python start_unified.py
``` 