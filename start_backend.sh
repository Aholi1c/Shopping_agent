#!/bin/bash

# 启动后端服务的脚本

cd "$(dirname "$0")"

echo "🚀 启动LLM Agent后端服务..."
echo "======================================"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv venv"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
python -c "import fastapi, uvicorn, sentence_transformers" 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖，正在安装..."
    pip install -q -r backend/requirements.txt 2>&1 | tail -5
fi

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p backend/uploads/images
mkdir -p backend/uploads/documents
mkdir -p backend/vector_store
mkdir -p logs

# 初始化数据库
echo "🗄️  初始化数据库..."
cd backend
python -c "
from app.core.database import engine
from app.models.models import Base
from app.models.ecommerce_models import Base as EcommerceBase
try:
    Base.metadata.create_all(bind=engine)
    EcommerceBase.metadata.create_all(bind=engine)
    print('✅ 数据库初始化完成')
except Exception as e:
    print(f'⚠️  数据库初始化警告: {e}')
" 2>&1

# 启动服务
echo ""
echo "🌐 启动后端服务..."
echo "📍 服务地址: http://localhost:8000"
echo "📖 API文档: http://localhost:8000/docs"
echo "🏥 健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================================"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

