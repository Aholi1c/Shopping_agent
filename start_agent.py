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
║     🛍️  智能购物助手 LLM Agent 启动程序                         ║
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
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 虚拟环境创建失败: {e}{Colors.RESET}")
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
    
    # 验证Python路径是否存在
    if not python_path.exists():
        print(f"{Colors.RED}❌ 虚拟环境Python路径不存在: {python_path}{Colors.RESET}")
        print(f"{Colors.YELLOW}⚠️  重新创建虚拟环境...{Colors.RESET}")
        try:
            # 删除旧的虚拟环境
            import shutil
            if venv_path.exists():
                shutil.rmtree(venv_path)
            # 重新创建
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print(f"{Colors.GREEN}✅ 虚拟环境重新创建成功{Colors.RESET}")
            # 重新检查路径
            if not python_path.exists():
                print(f"{Colors.RED}❌ 虚拟环境Python路径仍然不存在: {python_path}{Colors.RESET}")
                print(f"{Colors.YELLOW}💡 请手动创建虚拟环境: python3 -m venv venv{Colors.RESET}")
                sys.exit(1)
        except Exception as e:
            print(f"{Colors.RED}❌ 重新创建虚拟环境失败: {e}{Colors.RESET}")
            sys.exit(1)
    
    # 验证pip路径是否存在
    if not pip_path.exists():
        print(f"{Colors.YELLOW}⚠️  pip路径不存在，尝试使用python -m pip{Colors.RESET}")
        pip_path = python_path  # 使用python -m pip作为备选
    
    print(f"{Colors.GREEN}✅ 虚拟环境Python路径: {python_path}{Colors.RESET}")
    return python_path, pip_path

def install_dependencies(pip_path, python_path):
    """安装依赖"""
    print(f"{Colors.BLUE}📦 检查依赖...{Colors.RESET}")
    requirements_file = Path("backend/requirements.txt")
    
    if not requirements_file.exists():
        print(f"{Colors.RED}❌ 找不到 requirements.txt 文件{Colors.RESET}")
        sys.exit(1)
    
    # 使用虚拟环境的Python检查关键依赖
    check_code = """
try:
    import fastapi
    import uvicorn
    print('OK')
except ImportError as e:
    print(f'MISSING: {e}')
    sys.exit(1)
"""
    
    try:
        result = subprocess.run(
            [str(python_path), "-c", check_code],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and "OK" in result.stdout:
            print(f"{Colors.GREEN}✅ 核心依赖已安装{Colors.RESET}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # 需要安装依赖
    print(f"{Colors.YELLOW}⚠️  缺少依赖，正在安装...{Colors.RESET}")
    print(f"{Colors.BLUE}   这可能需要几分钟，请耐心等待...{Colors.RESET}")
    
    try:
        # 升级pip
        print(f"{Colors.BLUE}   升级pip...{Colors.RESET}")
        upgrade_result = subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if upgrade_result.returncode != 0:
            print(f"{Colors.YELLOW}⚠️  pip升级警告: {upgrade_result.stderr[:200]}{Colors.RESET}")
        
        # 安装依赖
        print(f"{Colors.BLUE}   安装依赖包（这可能需要几分钟）...{Colors.RESET}")
        install_result = subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )
        
        if install_result.returncode != 0:
            print(f"{Colors.RED}❌ 依赖安装失败{Colors.RESET}")
            print(f"{Colors.RED}错误信息:{Colors.RESET}")
            print(install_result.stderr[:500])
            print(f"\n{Colors.YELLOW}💡 提示:{Colors.RESET}")
            print(f"   1. 检查网络连接")
            print(f"   2. 尝试手动安装: {pip_path} install -r {requirements_file}")
            print(f"   3. 某些依赖可能失败，可以尝试安装核心依赖:")
            print(f"      {pip_path} install fastapi uvicorn sqlalchemy pydantic")
            print(f"   4. 查看详细错误信息，可能需要安装系统依赖")
            sys.exit(1)
        
        # 验证核心依赖是否安装成功
        print(f"{Colors.BLUE}   验证安装...{Colors.RESET}")
        verify_result = subprocess.run(
            [str(python_path), "-c", check_code],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if verify_result.returncode == 0 and "OK" in verify_result.stdout:
            print(f"{Colors.GREEN}✅ 核心依赖安装成功{Colors.RESET}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  核心依赖验证失败，但继续尝试启动...{Colors.RESET}")
            print(f"{Colors.YELLOW}   如果启动失败，请手动安装依赖{Colors.RESET}")
            return True
            
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}❌ 依赖安装超时{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 安装时间过长，请检查网络连接或手动安装依赖{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ 依赖安装出错: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 请手动安装依赖: {pip_path} install -r {requirements_file}{Colors.RESET}")
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
    # 确保使用绝对路径（但不要解析符号链接，保持使用虚拟环境的Python）
    script_dir = Path(__file__).parent.absolute()
    
    # 如果是相对路径，转换为相对于脚本目录的绝对路径
    if isinstance(python_path, Path):
        if not python_path.is_absolute():
            # 相对路径，转换为相对于脚本目录的绝对路径
            python_path = script_dir / python_path
    else:
        python_path = Path(python_path)
        if not python_path.is_absolute():
            python_path = script_dir / python_path
    
    # 确保路径存在（不要使用resolve()，因为会解析符号链接到系统Python）
    # 使用absolute()而不是resolve()，保持符号链接
    if not python_path.is_absolute():
        python_path = python_path.absolute()
    
    # 验证Python路径是否存在（检查符号链接或实际文件）
    if not python_path.exists() and not python_path.is_symlink():
        print(f"{Colors.RED}❌ Python路径不存在: {python_path}{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 请检查虚拟环境是否正确创建{Colors.RESET}")
        sys.exit(1)
    
    # 验证Python是否可执行
    try:
        result = subprocess.run(
            [str(python_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"{Colors.RED}❌ Python无法执行: {python_path}{Colors.RESET}")
            sys.exit(1)
        print(f"{Colors.GREEN}✅ Python版本验证成功{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Python验证失败: {e}{Colors.RESET}")
        sys.exit(1)
    
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
        # 确保在正确的目录
        backend_dir = script_dir / "backend"
        
        if not backend_dir.exists():
            print(f"{Colors.RED}❌ backend目录不存在: {backend_dir}{Colors.RESET}")
            sys.exit(1)
        
        # 切换到backend目录启动服务
        original_dir = os.getcwd()
        os.chdir(str(backend_dir))
        
        print(f"{Colors.BLUE}📂 工作目录: {os.getcwd()}{Colors.RESET}")
        print(f"{Colors.BLUE}🐍 Python路径: {python_path}{Colors.RESET}")
        
        # 验证Python是否在虚拟环境中
        python_str = str(python_path)
        if "venv" not in python_str and "virtualenv" not in python_str:
            print(f"{Colors.YELLOW}⚠️  警告: Python路径可能不在虚拟环境中{Colors.RESET}")
        
        # 启动服务（使用绝对路径，但不解析符号链接）
        print(f"{Colors.BLUE}🚀 正在启动服务...{Colors.RESET}")
        result = subprocess.run([
            str(python_path), "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=False)
        
        if result.returncode != 0:
            # 如果启动失败，尝试显示更详细的错误
            print(f"{Colors.RED}❌ 服务启动失败，退出码: {result.returncode}{Colors.RESET}")
            print(f"{Colors.YELLOW}💡 尝试手动测试导入...{Colors.RESET}")
            # 尝试直接运行Python查看错误
            test_result = subprocess.run(
                [str(python_path), "-c", "from app.main import app; print('导入成功')"],
                capture_output=True,
                text=True,
                cwd=str(backend_dir)
            )
            if test_result.returncode != 0:
                print(f"{Colors.RED}导入错误:{Colors.RESET}")
                print(test_result.stderr[:500])
            raise subprocess.CalledProcessError(result.returncode, str(python_path))
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  服务已停止{Colors.RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ 启动失败: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 请检查:{Colors.RESET}")
        print(f"   1. 依赖是否安装: {python_path} -m pip list | grep fastapi")
        print(f"   2. backend目录是否存在")
        print(f"   3. app.main:app 是否可以正常导入")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ 启动失败: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 错误详情: {type(e).__name__}: {str(e)}{Colors.RESET}")
        import traceback
        print(f"{Colors.RED}详细错误:{Colors.RESET}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 返回到原始目录
        try:
            os.chdir(original_dir)
        except:
            os.chdir(str(script_dir))

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
    install_dependencies(pip_path, python_path)
    
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

