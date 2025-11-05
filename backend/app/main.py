from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import uvicorn
import os
from dotenv import load_dotenv

from .core.config import settings
from .core.database import get_db, engine
from .models.models import Base
from .models.ecommerce_models import Base as EcommerceBase
from .api import chat, media, memory, rag, agents, shopping, advanced_features, ecommerce, price_tracker, product_comparison, coupon, enhanced_rag, shopping_behavior, visual_search, social_commerce, mcp, product_management
from .api.websocket import handle_websocket_chat, manager

# 加载环境变量
load_dotenv()

# 创建数据库表
Base.metadata.create_all(bind=engine)
EcommerceBase.metadata.create_all(bind=engine)

app = FastAPI(
    title="增强多模态LLM Agent API",
    description="具备记忆系统、RAG增强和多Agent协作的智能AI助手API",
    version="2.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 包含API路由
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(media.router, prefix="/api/media", tags=["Media"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])
app.include_router(enhanced_rag.router, prefix="/api/enhanced-rag", tags=["Enhanced RAG"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(shopping.router, prefix="/api/shopping", tags=["Shopping"])
app.include_router(advanced_features.router, prefix="/api/advanced", tags=["Advanced Features"])
app.include_router(ecommerce.router, prefix="/api/ecommerce", tags=["Ecommerce"])
app.include_router(price_tracker.router, prefix="/api/price-tracker", tags=["Price Tracker"])
app.include_router(product_comparison.router, prefix="/api/comparison", tags=["Product Comparison"])
app.include_router(coupon.router, prefix="/api/coupon", tags=["Coupon"])
app.include_router(shopping_behavior.router, prefix="/api/shopping-behavior", tags=["Shopping Behavior"])
app.include_router(visual_search.router, prefix="/api/visual-search", tags=["Visual Search"])
app.include_router(social_commerce.router, prefix="/api/social-commerce", tags=["Social Commerce"])
app.include_router(product_management.router, prefix="/api/product-management", tags=["Product Management"])

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    根路径 - 返回友好的欢迎页面
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>多模态LLM Agent API</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
                max-width: 600px;
                width: 100%;
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            .version {
                color: #667eea;
                font-size: 1.2em;
                margin-bottom: 30px;
                font-weight: 600;
            }
            .description {
                color: #666;
                margin-bottom: 40px;
                line-height: 1.6;
            }
            .links {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            .link {
                display: block;
                padding: 15px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .link:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
            }
            .link.secondary {
                background: #f0f0f0;
                color: #333;
            }
            .link.secondary:hover {
                background: #e0e0e0;
            }
            .info {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                color: #666;
                font-size: 0.9em;
            }
            .status {
                display: inline-block;
                padding: 5px 15px;
                background: #28a745;
                color: white;
                border-radius: 20px;
                font-size: 0.9em;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <span class="status">● 服务运行中</span>
            <h1>🚀 LLM Agent API</h1>
            <div class="version">版本 2.1.0</div>
            <p class="description">
                具备记忆系统、RAG增强和多Agent协作的智能AI助手API<br>
                支持多模态交互、购物助手、价格跟踪等功能
            </p>
            <div class="links">
                <a href="/docs" class="link">📖 查看API文档 (Swagger UI)</a>
                <a href="/redoc" class="link secondary">📚 查看API文档 (ReDoc)</a>
                <a href="/health" class="link secondary">🏥 健康检查</a>
            </div>
            <div class="info">
                <strong>快速开始：</strong><br>
                • API文档: <a href="/docs" style="color: #667eea;">/docs</a><br>
                • 健康检查: <a href="/health" style="color: #667eea;">/health</a><br>
                • WebSocket: /ws/{client_id}
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """
    健康检查
    """
    return {"status": "healthy", "service": "LLM Agent API"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket端点
    """
    await handle_websocket_chat(websocket, client_id)

@app.get("/api/connections")
async def get_connections():
    """
    获取当前连接数
    """
    return {
        "active_connections": len(manager.active_connections),
        "clients": list(manager.active_connections.keys())
    }

@app.on_event("startup")
async def startup_event():
    """
    启动事件
    """
    print("LLM Agent API starting up...")
    print(f"Upload directory: {settings.upload_dir}")
    print(f"Database URL: {settings.database_url}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    关闭事件
    """
    print("LLM Agent API shutting down...")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )