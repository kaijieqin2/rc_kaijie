#!/bin/bash
# 启动脚本

echo "=========================================="
echo "HTTP通知投递系统 - 启动"
echo "=========================================="
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3"
    exit 1
fi

echo "Python版本: $(python3 --version)"
echo ""

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
else
    echo "依赖已安装"
fi
echo ""

# 启动服务
echo "启动服务..."
echo "访问 http://localhost:8000 查看服务"
echo "访问 http://localhost:8000/docs 查看API文档"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

cd "$(dirname "$0")"
python3 main.py
