#!/usr/bin/env python3
"""
智能购物助手 LLM Agent 停止脚本
一键停止运行的agent服务
"""

import os
import sys
import signal
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
    """打印停止标题"""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🛑  智能购物助手 LLM Agent 停止程序                      ║
║     Enhanced LLM Agent Shopping Assistant - Stop Service    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}
""")

def find_processes_by_port(port=8000):
    """查找运行在指定端口的进程"""
    processes = []
    
    try:
        if platform.system() == "Windows":
            # Windows系统
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 0:
                        try:
                            pid = int(parts[-1])
                            processes.append(pid)
                        except (ValueError, IndexError):
                            pass
        else:
            # macOS/Linux系统
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for pid_str in result.stdout.strip().split('\n'):
                    if pid_str:
                        try:
                            pid = int(pid_str)
                            processes.append(pid)
                        except ValueError:
                            pass
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    return list(set(processes))  # 去重

def find_processes_by_name(pattern="uvicorn.*app.main:app"):
    """通过进程名称查找进程"""
    processes = []
    
    try:
        if platform.system() == "Windows":
            # Windows系统
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq python.exe"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # 在Windows上，我们需要更复杂的逻辑来匹配uvicorn进程
            # 这里简化处理，主要通过端口查找
            pass
        else:
            # macOS/Linux系统
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for pid_str in result.stdout.strip().split('\n'):
                    if pid_str:
                        try:
                            pid = int(pid_str)
                            processes.append(pid)
                        except ValueError:
                            pass
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    return list(set(processes))  # 去重

def get_process_info(pid):
    """获取进程信息"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.stdout.strip()
        else:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "pid,command"],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        return None

def stop_process(pid, force=False):
    """停止进程"""
    try:
        if force:
            # 强制终止
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False, timeout=5)
            else:
                os.kill(pid, signal.SIGKILL)
            return True
        else:
            # 优雅停止
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/PID", str(pid)], check=False, timeout=5)
            else:
                os.kill(pid, signal.SIGTERM)
            return True
    except (ProcessLookupError, PermissionError, OSError, subprocess.TimeoutExpired):
        return False

def stop_service(port=8000, force=False):
    """停止服务"""
    print(f"{Colors.BLUE}🔍 查找运行在端口 {port} 的服务...{Colors.RESET}")
    
    # 方法1: 通过端口查找
    processes_by_port = find_processes_by_port(port)
    
    # 方法2: 通过进程名称查找
    processes_by_name = find_processes_by_name("uvicorn.*app.main:app")
    
    # 合并所有找到的进程
    all_processes = list(set(processes_by_port + processes_by_name))
    
    if not all_processes:
        print(f"{Colors.YELLOW}⚠️  没有找到运行在端口 {port} 的服务{Colors.RESET}")
        print(f"{Colors.BLUE}💡 服务可能已经停止，或者没有在运行{Colors.RESET}")
        return False
    
    print(f"{Colors.GREEN}✅ 找到 {len(all_processes)} 个相关进程{Colors.RESET}")
    
    # 显示进程信息
    for pid in all_processes:
        info = get_process_info(pid)
        if info:
            print(f"{Colors.CYAN}   PID {pid}: {info[:100]}...{Colors.RESET}")
    
    # 停止进程
    print(f"{Colors.BLUE}🛑 正在停止服务...{Colors.RESET}")
    
    stopped_count = 0
    for pid in all_processes:
        try:
            if stop_process(pid, force=force):
                print(f"{Colors.GREEN}✅ 已停止进程 {pid}{Colors.RESET}")
                stopped_count += 1
            else:
                print(f"{Colors.YELLOW}⚠️  停止进程 {pid} 失败，尝试强制终止...{Colors.RESET}")
                if stop_process(pid, force=True):
                    print(f"{Colors.GREEN}✅ 已强制终止进程 {pid}{Colors.RESET}")
                    stopped_count += 1
                else:
                    print(f"{Colors.RED}❌ 无法停止进程 {pid}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ 停止进程 {pid} 时出错: {e}{Colors.RESET}")
    
    if stopped_count > 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ 服务已成功停止！{Colors.RESET}")
        print(f"{Colors.GREEN}   已停止 {stopped_count} 个进程{Colors.RESET}")
        return True
    else:
        print(f"\n{Colors.RED}❌ 无法停止服务{Colors.RESET}")
        return False

def verify_stopped(port=8000):
    """验证服务是否已停止"""
    print(f"{Colors.BLUE}🔍 验证服务是否已停止...{Colors.RESET}")
    
    # 等待一秒让进程完全停止
    import time
    time.sleep(1)
    
    remaining_processes = find_processes_by_port(port)
    if remaining_processes:
        print(f"{Colors.YELLOW}⚠️  仍有进程运行在端口 {port}{Colors.RESET}")
        return False
    else:
        print(f"{Colors.GREEN}✅ 确认服务已完全停止{Colors.RESET}")
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="停止智能购物助手 LLM Agent 服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 stop_agent.py          # 停止默认端口(8000)的服务
  python3 stop_agent.py -p 8080   # 停止指定端口的服务
  python3 stop_agent.py --force   # 强制停止服务
        """
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="要停止的服务端口 (默认: 8000)"
    )
    
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="强制停止服务（使用SIGKILL）"
    )
    
    args = parser.parse_args()
    
    print_header()
    
    # 停止服务
    success = stop_service(port=args.port, force=args.force)
    
    # 验证
    if success:
        verify_stopped(port=args.port)
    
    print(f"""
{Colors.CYAN}{'='*62}{Colors.RESET}
{Colors.BLUE}💡 提示:{Colors.RESET}
   - 启动服务: python3 start_agent.py
   - 停止服务: python3 stop_agent.py
   - 重启服务: python3 stop_agent.py && python3 start_agent.py
{Colors.CYAN}{'='*62}{Colors.RESET}
""")

if __name__ == "__main__":
    main()

