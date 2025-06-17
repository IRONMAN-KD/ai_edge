#!/bin/bash

echo "启动 Vue3 前端服务..."

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

# 检查 npm 是否安装
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到 npm，请先安装 npm"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "package.json" ]; then
    echo "错误: 请在 frontend 目录下运行此脚本"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
npm install

# 启动开发服务器
echo "启动开发服务器..."
npm run dev 