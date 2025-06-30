# AI Edge 统一框架 - 测试指南

## 概述

本文档介绍了AI Edge统一框架的测试策略、测试类型和最佳实践。

## 测试架构

### 测试目录结构

```
tests/
├── conftest.py              # pytest配置和fixtures
├── test_simple.py           # 简单验证测试
├── unit/                    # 单元测试
│   ├── inference/           # 推理引擎测试
│   │   ├── test_base.py
│   │   ├── test_factory.py
│   │   └── test_cpu_inference.py
│   ├── api/                 # API测试
│   └── utils/               # 工具类测试
│       └── test_platform_detector.py
├── integration/             # 集成测试
│   ├── platforms/
│   │   └── test_platform_integration.py
│   └── deployment/
└── performance/             # 性能测试
    └── test_inference_performance.py
```

## 测试类型

### 1. 单元测试 (Unit Tests)

测试单个组件或函数的功能。

**特点：**
- 快速执行
- 独立运行
- 模拟外部依赖
- 高覆盖率

**运行命令：**
```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定模块测试
pytest tests/unit/inference/ -v

# 生成覆盖率报告
pytest tests/unit/ --cov=src --cov-report=html
```

### 2. 集成测试 (Integration Tests)

测试组件之间的交互和集成。

**特点：**
- 测试真实交互
- 较慢执行
- 可能需要外部资源
- 端到端验证

**运行命令：**
```bash
# 运行集成测试
pytest tests/integration/ -v

# 跳过慢速测试
pytest tests/integration/ -v -m "not slow"
```

### 3. 性能测试 (Performance Tests)

测试系统性能和基准。

**特点：**
- 测量执行时间
- 内存使用分析
- 并发性能测试
- 平台对比

**运行命令：**
```bash
# 运行性能测试
pytest tests/performance/ -v

# 运行快速性能测试
pytest tests/performance/ -v -m "not slow"
```

## 测试标记 (Markers)

使用pytest标记来分类和筛选测试：

```python
@pytest.mark.unit          # 单元测试
@pytest.mark.integration   # 集成测试
@pytest.mark.performance   # 性能测试
@pytest.mark.slow          # 慢速测试
@pytest.mark.gpu           # 需要GPU的测试
@pytest.mark.npu           # 需要NPU的测试
@pytest.mark.network       # 需要网络的测试
```

**使用示例：**
```bash
# 只运行单元测试
pytest -m unit

# 排除慢速测试
pytest -m "not slow"

# 只运行GPU相关测试
pytest -m gpu
```

## 测试配置

### pytest.ini 配置

```ini
[tool:pytest]
minversion = 6.0
addopts = -ra --strict-markers --strict-config --disable-warnings -v
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: 单元测试
    integration: 集成测试
    performance: 性能测试
    slow: 慢速测试
    gpu: 需要GPU的测试
    npu: 需要NPU的测试
```

### Fixtures

在`conftest.py`中定义的常用fixtures：

```python
@pytest.fixture
def test_config():
    """测试配置"""
    return {
        'platforms': ['cpu_x86', 'cpu_arm', 'nvidia_gpu', 'atlas_npu', 'sophon'],
        'test_image_size': (640, 640),
        'confidence_threshold': 0.5
    }

@pytest.fixture
def test_image():
    """测试图像"""
    return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

@pytest.fixture
def mock_model_file(temp_dir):
    """模拟模型文件"""
    model_path = os.path.join(temp_dir, 'test_model.onnx')
    Path(model_path).touch()
    return model_path
```

## 编写测试的最佳实践

### 1. 测试命名

```python
def test_should_detect_person_when_confidence_above_threshold():
    """应该在置信度超过阈值时检测到人"""
    pass

def test_should_return_empty_list_when_no_objects_detected():
    """当没有检测到对象时应该返回空列表"""
    pass
```

### 2. 使用Mock

```python
from unittest.mock import Mock, patch

@patch('inference.cpu_inference.ort.InferenceSession')
def test_cpu_inference_with_mock(mock_session_class):
    """使用Mock测试CPU推理"""
    mock_session = Mock()
    mock_session.run.return_value = [np.zeros((1, 25200, 85))]
    mock_session_class.return_value = mock_session
    
    # 测试代码
    engine = CPUInference(config)
    result = engine.detect(test_image)
    
    assert isinstance(result, list)
```

### 3. 参数化测试

```python
@pytest.mark.parametrize("platform,expected", [
    ('cpu_x86', True),
    ('nvidia_gpu', True),
    ('unknown_platform', False),
])
def test_platform_support(platform, expected):
    """测试平台支持"""
    result = InferenceFactory.is_platform_supported(platform)
    assert result == expected
```

### 4. 异常测试

```python
def test_should_raise_error_for_invalid_model_path():
    """应该为无效模型路径抛出错误"""
    with pytest.raises(FileNotFoundError):
        engine = CPUInference(config)
        engine.load_model('nonexistent_model.onnx')
```

## 代码覆盖率

### 生成覆盖率报告

```bash
# HTML报告
pytest tests/unit/ --cov=src --cov-report=html

# 终端报告
pytest tests/unit/ --cov=src --cov-report=term-missing

# XML报告（CI/CD）
pytest tests/unit/ --cov=src --cov-report=xml
```

### 覆盖率目标

- **单元测试覆盖率**: > 90%
- **集成测试覆盖率**: > 70%
- **关键模块覆盖率**: > 95%

## 持续集成

### GitHub Actions

项目包含完整的CI/CD流水线：

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop, feature/* ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
    - name: Install dependencies
      run: pip install -r requirements/test.txt
    - name: Run tests
      run: pytest tests/unit/ --cov=src
```

## 质量检查脚本

使用内置的质量检查脚本：

```bash
# 运行所有检查
./deployments/scripts/quality_check.sh --all

# 只运行测试
./deployments/scripts/quality_check.sh --test

# 代码格式化
./deployments/scripts/quality_check.sh --format

# 生成覆盖率报告
./deployments/scripts/quality_check.sh --coverage
```

## 性能测试

### 基准测试

```python
@pytest.mark.performance
def test_inference_performance(performance_config, test_images):
    """测试推理性能"""
    engine = create_engine()
    
    # 预热
    for _ in range(3):
        engine.detect(test_images[0])
    
    # 性能测试
    start_time = time.time()
    for image in test_images:
        engine.detect(image)
    total_time = time.time() - start_time
    
    # 性能断言
    avg_time = total_time / len(test_images)
    assert avg_time < 1.0  # 平均推理时间应小于1秒
```

### 内存测试

```python
def test_memory_usage():
    """测试内存使用"""
    import psutil
    
    process = psutil.Process()
    memory_before = process.memory_info().rss
    
    # 执行测试代码
    engine = create_engine()
    engine.detect(test_image)
    
    memory_after = process.memory_info().rss
    memory_increase = memory_after - memory_before
    
    assert memory_increase < 100 * 1024 * 1024  # 不应超过100MB
```

## 调试测试

### 调试失败的测试

```bash
# 详细输出
pytest tests/unit/test_failing.py -v -s

# 进入调试器
pytest tests/unit/test_failing.py --pdb

# 只运行失败的测试
pytest --lf

# 显示最慢的测试
pytest --durations=10
```

### 日志调试

```python
import logging

def test_with_logging(caplog):
    """带日志的测试"""
    with caplog.at_level(logging.INFO):
        # 测试代码
        pass
    
    assert "期望的日志消息" in caplog.text
```

## 测试数据管理

### 测试图像

```python
@pytest.fixture
def test_image():
    """生成测试图像"""
    return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

@pytest.fixture
def test_image_file(tmp_path):
    """生成测试图像文件"""
    image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    image_path = tmp_path / "test_image.jpg"
    cv2.imwrite(str(image_path), image)
    return str(image_path)
```

### 临时文件

```python
def test_with_temp_file(tmp_path):
    """使用临时文件的测试"""
    temp_file = tmp_path / "test_file.txt"
    temp_file.write_text("test content")
    
    # 测试代码
    assert temp_file.exists()
```

## 常见问题和解决方案

### 1. 导入错误

**问题**: `ModuleNotFoundError: No module named 'src'`

**解决方案**: 在`conftest.py`中添加路径：
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```

### 2. Mock不生效

**问题**: Mock对象没有按预期工作

**解决方案**: 确保Mock的路径正确：
```python
# 错误：Mock导入路径
@patch('onnxruntime.InferenceSession')

# 正确：Mock使用路径
@patch('inference.cpu_inference.ort.InferenceSession')
```

### 3. 测试隔离

**问题**: 测试之间相互影响

**解决方案**: 使用setup/teardown或fixtures：
```python
def setup_method(self):
    """每个测试方法前执行"""
    self.engine = create_engine()

def teardown_method(self):
    """每个测试方法后执行"""
    self.engine.release_resources()
```

## 总结

良好的测试实践包括：

1. **全面的测试覆盖**: 单元测试、集成测试、性能测试
2. **清晰的测试结构**: 合理的目录组织和命名
3. **有效的Mock使用**: 隔离外部依赖
4. **持续集成**: 自动化测试流水线
5. **性能监控**: 基准测试和性能回归检测
6. **代码质量**: 覆盖率监控和质量检查

通过遵循这些最佳实践，我们可以确保AI Edge统一框架的高质量和可靠性。 