#!/usr/bin/env python3
"""
启动完整的LLM Agent系统
包含FastAPI后端和所有增强功能
"""

import os
import sys
import subprocess
import asyncio
import signal
import time
from pathlib import Path

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查系统依赖...")

    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'faiss-cpu',
        'beautifulsoup4', 'aiohttp', 'redis', 'celery'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False

    print("✅ 所有依赖检查通过")
    return True

def setup_environment():
    """设置环境变量和配置"""
    print("🔧 设置运行环境...")

    # 设置环境变量
    os.environ.setdefault('PYTHONPATH', os.path.dirname(__file__))

    # 检查必要的目录
    directories = [
        'backend/uploads',
        'backend/uploads/images',
        'backend/vector_store',
        'backend/logs'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    print("✅ 环境设置完成")

def start_celery_worker():
    """启动Celery工作进程"""
    print("🚀 启动Celery工作进程...")

    celery_cmd = [
        'celery', '-A', 'app.celery_app.celery',
        'worker', '--loglevel=info', '--pool=solo'
    ]

    # 启动Celery进程
    celery_process = subprocess.Popen(
        celery_cmd,
        cwd='backend',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return celery_process

def start_redis_server():
    """启动Redis服务器"""
    print("🚀 启动Redis服务器...")

    redis_cmd = ['redis-server', '--port', '6379']

    redis_process = subprocess.Popen(
        redis_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return redis_process

def start_fastapi_server():
    """启动FastAPI服务器"""
    print("🚀 启动FastAPI服务器...")

    uvicorn_cmd = [
        'uvicorn', 'app.main:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload',
        '--log-level', 'info'
    ]

    fastapi_process = subprocess.Popen(
        uvicorn_cmd,
        cwd='backend',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return fastapi_process

def start_websocket_server():
    """启动WebSocket服务器"""
    print("🚀 启动WebSocket服务器...")

    websocket_cmd = [
        'python', '-m', 'websocket_server',
        '--host', '0.0.0.0',
        '--port', '8001'
    ]

    websocket_process = subprocess.Popen(
        websocket_cmd,
        cwd='backend',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return websocket_process

def show_system_info():
    """显示系统信息"""
    print("\n📊 LLM Agent 系统信息")
    print("=" * 50)

    try:
        from app.core.config import settings
        print(f"LLM Provider: {settings.llm_provider}")
        print(f"Text Model: {settings.text_model}")
        print(f"Vision Model: {settings.vision_model}")
        print(f"Database URL: {settings.database_url}")
        print(f"Redis URL: {settings.redis_url}")
        print(f"Vector DB Type: {settings.vector_db_type}")
        print(f"Enable Shopping Assistant: {settings.enable_shopping_assistant}")
    except Exception as e:
        print(f"配置加载错误: {e}")

    print("=" * 50)

def cleanup_processes(processes):
    """清理所有进程"""
    print("\n🧹 正在清理进程...")

    for name, process in processes.items():
        if process.poll() is None:
            print(f"停止 {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"强制停止 {name}...")
                process.kill()

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n📡 接收到信号 {signum}，正在关闭...")
    if hasattr(signal_handler, 'processes'):
        cleanup_processes(signal_handler.processes)
    sys.exit(0)

async def main():
    """主启动函数"""
    print("🚀 启动完整的LLM Agent系统")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        return False

    # 设置环境
    setup_environment()

    # 显示系统信息
    show_system_info()

    # 进程字典
    processes = {}
    signal_handler.processes = processes

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. 启动Redis
        print("\n🔴 启动Redis服务器...")
        processes['redis'] = start_redis_server()
        time.sleep(2)

        # 2. 启动Celery
        print("\n🟡 启动Celery工作进程...")
        processes['celery'] = start_celery_worker()
        time.sleep(3)

        # 3. 启动FastAPI
        print("\n🟢 启动FastAPI服务器...")
        processes['fastapi'] = start_fastapi_server()
        time.sleep(2)

        # 4. 启动WebSocket（可选）
        # processes['websocket'] = start_websocket_server()

        print("\n✅ 所有服务启动完成！")
        print("\n🌐 服务访问地址:")
        print("  • FastAPI API: http://localhost:8000")
        print("  • API文档: http://localhost:8000/docs")
        print("  • WebSocket: ws://localhost:8000/ws")
        print("\n💡 测试命令:")
        print("  • 健康检查: curl http://localhost:8000/health")
        print("  • 聊天测试: curl -X POST http://localhost:8000/api/chat -H 'Content-Type: application/json' -d '{\"message\":\"hello\"}'")
        print("  • 购物助手: curl -X POST http://localhost:8000/api/shopping/query -H 'Content-Type: application/json' -d '{\"query\":\"iPhone 15 Pro价格\"}'")

        print("\n按 Ctrl+C 停止所有服务...")

        # 保持运行
        while True:
            time.sleep(1)

            # 检查进程状态
            for name, process in processes.items():
                if process.poll() is not None:
                    print(f"⚠️  {name} 进程已退出")

    except KeyboardInterrupt:
        print("\n\n📡 接收到中断信号...")
    except Exception as e:
        print(f"\n❌ 启动过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_processes(processes)
        print("👋 系统已关闭")

if __name__ == "__main__":
    # 在Windows上使用不同的事件循环策略
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())