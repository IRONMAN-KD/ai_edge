FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖和中文字体
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖（使用清华源）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY api/ /app/
COPY database/ /app/database/
COPY components/ /app/components/
COPY utils/ /app/utils/
COPY fonts/ /app/fonts/

# 暴露端口
EXPOSE 5001

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"] 