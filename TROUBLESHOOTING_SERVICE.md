# 服务连接问题排查指南

## 🔍 问题诊断

如果遇到"无法连接到服务器"错误，请按以下步骤排查：

### 1. 检查服务是否运行

```bash
# 检查端口是否被占用
lsof -ti:8000

# 检查进程
ps aux | grep uvicorn
```

### 2. 测试服务连接

```bash
# 健康检查
curl http://localhost:8000/health

# 访问首页
curl http://localhost:8000/
```

### 3. 重启服务

如果服务无法访问，请重启：

```bash
# 停止服务
pkill -f "uvicorn.*app.main:app"

# 启动服务
cd backend
source ../venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 检查浏览器扩展配置

确保浏览器扩展可以访问 localhost：
1. 打开 `chrome://extensions/`
2. 找到您的扩展
3. 确保权限中包含 `http://localhost:8000/*`

### 5. 检查CORS配置

如果服务启动但浏览器无法访问，可能是CORS问题。检查 `backend/app/main.py` 中的CORS配置。

## 🚀 快速修复

### 方法一：完全重启服务

```bash
# 1. 停止所有相关进程
pkill -f uvicorn

# 2. 等待端口释放
sleep 2

# 3. 重新启动
cd backend
source ../venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方法二：检查服务日志

查看服务启动时的错误信息，通常会有详细的错误提示。

### 方法三：使用不同的端口

如果8000端口有问题，可以：
1. 修改 `backend/app/core/config.py` 中的端口
2. 修改 `browser-extension/api.js` 中的 `API_BASE_URL`

## 📝 常见问题

### Q: 服务显示运行但无法访问？

A: 可能是：
- 服务绑定到错误的地址（应该是 0.0.0.0，不是 127.0.0.1）
- 防火墙阻止了连接
- 服务启动时出错但没有退出

### Q: 浏览器扩展无法连接？

A: 检查：
1. 扩展权限是否包含 `http://localhost:8000/*`
2. 浏览器是否允许访问 localhost
3. 是否有其他扩展或代理拦截了请求

### Q: 如何查看服务日志？

A: 服务在后台运行时，日志会输出到启动它的终端。如果需要查看详细日志，可以：
- 在前台运行服务（不添加后台运行）
- 查看系统日志

