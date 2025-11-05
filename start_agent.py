#!/usr/bin/env python3
"""
智能购物助手 LLM Agent 启动脚本
一键启动整个agent项目
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """打印启动标题"""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🛍️  智能购物助手 LLM Agent 启动程序                      ║
║     Enhanced LLM Agent Shopping Assistant v2.1.0            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}
""")

def check_python_version():
    """检查Python版本"""
    print(f"{Colors.BLUE}📋 检查Python版本...{Colors.RESET}")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"{Colors.RED}❌ Python版本过低，需要Python 3.8或更高版本{Colors.RESET}")
        print(f"   当前版本: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"{Colors.GREEN}✅ Python版本: {version.major}.{version.minor}.{version.micro}{Colors.RESET}")
    return True

def check_and_create_venv():
    """检查并创建虚拟环境"""
    print(f"{Colors.BLUE}🔧 检查虚拟环境...{Colors.RESET}")
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print(f"{Colors.YELLOW}⚠️  虚拟环境不存在，正在创建...{Colors.RESET}")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print(f"{Colors.GREEN}✅ 虚拟环境创建成功{Colors.RESET}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}❌ 虚拟环境创建失败{Colors.RESET}")
            sys.exit(1)
    else:
        print(f"{Colors.GREEN}✅ 虚拟环境已存在{Colors.RESET}")
    
    # 确定虚拟环境中的Python路径
    if platform.system() == "Windows":
        python_path = venv_path / "Scripts" / "python.exe"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        python_path = venv_path / "bin" / "python"
        pip_path = venv_path / "bin" / "pip"
    
    return python_path, pip_path

def install_dependencies(pip_path):
    """安装依赖"""
    print(f"{Colors.BLUE}📦 检查依赖...{Colors.RESET}")
    requirements_file = Path("backend/requirements.txt")
    
    if not requirements_file.exists():
        print(f"{Colors.RED}❌ 找不到 requirements.txt 文件{Colors.RESET}")
        sys.exit(1)
    
    # 检查关键依赖
    try:
        import fastapi
        import uvicorn
        print(f"{Colors.GREEN}✅ 核心依赖已安装{Colors.RESET}")
    except ImportError:
        print(f"{Colors.YELLOW}⚠️  缺少依赖，正在安装...{Colors.RESET}")
        try:
            subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
            subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
            print(f"{Colors.GREEN}✅ 依赖安装完成{Colors.RESET}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}❌ 依赖安装失败{Colors.RESET}")
            sys.exit(1)

def check_env_file():
    """检查.env文件"""
    print(f"{Colors.BLUE}🔍 检查配置文件...{Colors.RESET}")
    env_file = Path("backend/.env")
    env_example = Path("backend/.env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print(f"{Colors.YELLOW}⚠️  .env文件不存在，从.env.example创建...{Colors.RESET}")
            try:
                import shutil
                shutil.copy(env_example, env_file)
                print(f"{Colors.GREEN}✅ 已创建.env文件{Colors.RESET}")
                print(f"{Colors.YELLOW}📝 请编辑 backend/.env 文件，填入您的API密钥{Colors.RESET}")
                print(f"   特别是以下配置：")
                print(f"   - BIGMODEL_API_KEY")
                print(f"   - BIGMODEL_VLM_API_KEY (可选)")
                print(f"   - OPENAI_API_KEY (如果使用OpenAI)")
            except Exception as e:
                print(f"{Colors.RED}❌ 创建.env文件失败: {e}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠️  .env文件不存在，请手动创建{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}✅ .env文件已存在{Colors.RESET}")

def create_directories():
    """创建必要的目录"""
    print(f"{Colors.BLUE}📁 创建必要目录...{Colors.RESET}")
    directories = [
        "backend/uploads/images",
        "backend/uploads/documents",
        "backend/vector_store",
        "logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print(f"{Colors.GREEN}✅ 目录创建完成{Colors.RESET}")

def init_database(python_path):
    """初始化数据库"""
    print(f"{Colors.BLUE}🗄️  初始化数据库...{Colors.RESET}")
    try:
        # 切换到backend目录执行初始化
        os.chdir("backend")
        init_code = """
from app.core.database import engine
from app.models.models import Base
from app.models.ecommerce_models import Base as EcommerceBase

try:
    Base.metadata.create_all(bind=engine)
    EcommerceBase.metadata.create_all(bind=engine)
    print('✅ 数据库初始化完成')
except Exception as e:
    print(f'⚠️  数据库初始化警告: {e}')
"""
        result = subprocess.run(
            [str(python_path), "-c", init_code],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        os.chdir("..")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  数据库初始化警告: {e}{Colors.RESET}")
        os.chdir("..")

def check_redis():
    """检查Redis服务（可选）"""
    print(f"{Colors.BLUE}🔍 检查Redis服务...{Colors.RESET}")
    env_file = Path("backend/.env")
    
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()
            if "redis://" in content:
                try:
                    result = subprocess.run(
                        ["redis-cli", "ping"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        print(f"{Colors.GREEN}✅ Redis服务运行正常{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}⚠️  Redis服务未运行（可选）{Colors.RESET}")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    print(f"{Colors.YELLOW}⚠️  Redis服务未运行（可选）{Colors.RESET}")

def start_server(python_path):
    """启动后端服务"""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                  🚀 启动后端服务                            ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}

{Colors.GREEN}📍 服务地址: {Colors.BOLD}http://localhost:8000{Colors.RESET}
{Colors.GREEN}📖 API文档: {Colors.BOLD}http://localhost:8000/docs{Colors.RESET}
{Colors.GREEN}🏥 健康检查: {Colors.BOLD}http://localhost:8000/health{Colors.RESET}

{Colors.CYAN}🔧 可用的功能模块：{Colors.RESET}
   💬 聊天助手 - /api/chat
   📊 商品分析 - /api/shopping/product-analysis
   💰 价格对比 - /api/shopping/price-comparison
   📦 产品管理 - /api/product-management
   📈 价格跟踪 - /api/price-tracker
   🧠 记忆系统 - /api/memory
   📚 RAG增强 - /api/rag
   🤖 多Agent - /api/agents

{Colors.YELLOW}按 Ctrl+C 停止服务{Colors.RESET}
{Colors.CYAN}{'='*62}{Colors.RESET}
""")
    
    try:
        # 切换到backend目录启动服务
        os.chdir("backend")
        subprocess.run([
            str(python_path), "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  服务已停止{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ 启动失败: {e}{Colors.RESET}")
        sys.exit(1)
    finally:
        os.chdir("..")

def main():
    """主函数"""
    print_header()
    
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # 检查Python版本
    check_python_version()
    
    # 检查并创建虚拟环境
    python_path, pip_path = check_and_create_venv()
    
    # 安装依赖
    install_dependencies(pip_path)
    
    # 检查.env文件
    check_env_file()
    
    # 创建必要目录
    create_directories()
    
    # 初始化数据库
    init_database(python_path)
    
    # 检查Redis（可选）
    check_redis()
    
    # 启动服务
    start_server(python_path)

if __name__ == "__main__":
    main()

