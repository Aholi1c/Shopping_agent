#!/bin/bash

# 增强版电商助手Agent启动脚本
# Enhanced E-commerce Assistant Agent Startup Script

echo "🚀 启动增强版电商助手Agent..."
echo "🛒 Enhanced LLM Agent Shopping Assistant v2.1.0"
echo "=================================================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "📋 Python版本: $python_version"

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "📦 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装项目依赖..."
pip install -r backend/requirements.txt

# 检查.env文件
if [ ! -f "backend/.env" ]; then
    echo "⚠️  创建.env配置文件..."
    cp backend/.env.example backend/.env
    echo "📝 请编辑backend/.env文件，填入您的API密钥"
    echo "   特别是以下配置："
    echo "   - BIGMODEL_API_KEY"
    echo "   - OPENAI_API_KEY (如果使用OpenAI)"
    echo "   - REDIS_URL (如果使用Redis)"
    echo ""
    echo "📋 配置完成后，请重新运行此脚本"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads/images
mkdir -p vector_store
mkdir -p logs

# 检查Redis是否运行（如果配置了Redis）
if grep -q "redis://" backend/.env; then
    echo "🔍 检查Redis服务..."
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "⚠️  Redis服务未运行，请启动Redis服务"
        echo "   macOS: brew services start redis"
        echo "   Linux: sudo systemctl start redis-server"
        echo "   或者可以在backend/.env中使用SQLite替代Redis"
    else
        echo "✅ Redis服务运行正常"
    fi
fi

# 初始化数据库
echo "🗄️  初始化数据库..."
cd backend
python3 -c "
from app.core.database import engine
from app.models.models import Base
from app.models.ecommerce_models import Base as EcommerceBase

print('创建数据库表...')
Base.metadata.create_all(bind=engine)
EcommerceBase.metadata.create_all(bind=engine)
print('✅ 数据库初始化完成')
"

# 启动后端服务
echo "🌐 启动后端服务..."
echo "📍 服务地址: http://localhost:8000"
echo "📖 API文档: http://localhost:8000/docs"
echo ""
echo "🔧 可用的功能模块："
echo "   💬 聊天助手 - /api/chat"
echo "   📊 价格跟踪 - /api/price-tracker"
echo "   🔍 产品比较 - /api/comparison"
echo "   🎫 优惠券 - /api/coupon"
echo "   🧠 增强RAG - /api/enhanced-rag"
echo "   📊 购物行为 - /api/shopping-behavior"
echo "   👁️ 视觉搜索 - /api/visual-search"
echo "   📱 社交商务 - /api/social-commerce"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=================================================="

# 启动FastAPI应用
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload