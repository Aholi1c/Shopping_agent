# 浏览器扩展故障排除指南

## 已修复的问题

### 1. Service Worker注册失败 (Status code: 15)
**原因**: manifest.json中缺少`contextMenus`权限
**解决**: 已在`manifest.json`中添加`"contextMenus"`权限

### 2. chrome.contextMenus.create错误
**原因**: 
- 缺少权限
- 在Service Worker中同步调用API
- 没有错误处理

**解决**: 
- 添加了权限
- 在`onInstalled`监听器中异步创建菜单
- 添加了错误处理回调

### 3. API请求错误 (Internal Server Error)
**原因**: 
- 错误处理不完整
- 没有提供详细的错误信息
- 响应解析问题

**解决**:
- 改进了错误处理，尝试解析详细的错误信息
- 添加了网络连接检查
- 改进了响应解析逻辑

## 安装和重新加载扩展

1. **在Chrome中重新加载扩展**:
   - 打开 `chrome://extensions/`
   - 找到"智能购物助手 LLM Agent"扩展
   - 点击"重新加载"按钮（刷新图标）

2. **如果问题仍然存在**:
   - 完全删除扩展
   - 重新加载未打包的扩展
   - 选择 `browser-extension` 目录

## 检查后端服务

确保后端服务正在运行：
```bash
curl http://localhost:8000/health
```

应该返回：
```json
{"status":"healthy","service":"LLM Agent API"}
```

## 调试步骤

1. **打开Service Worker调试**:
   - 在`chrome://extensions/`中找到扩展
   - 点击"Service worker"链接
   - 查看控制台错误

2. **检查权限**:
   - 在扩展详情页面，确认所有权限都已授予
   - 特别是`contextMenus`权限

3. **检查API连接**:
   - 在sidepanel中打开开发者工具
   - 查看网络请求是否成功
   - 检查CORS设置

4. **查看日志**:
   - Service Worker控制台
   - Sidepanel控制台
   - 内容脚本控制台

## 常见错误及解决

### "无法连接到服务器"
- 检查后端服务是否在`http://localhost:8000`运行
- 检查防火墙设置
- 确认Chrome允许访问`http://localhost:8000`

### "API request failed: Internal Server Error"
- 检查后端服务日志
- 验证API密钥配置
- 查看详细的错误消息（已改进错误处理）

### "Context menu creation failed"
- 确认`contextMenus`权限已添加
- 重新加载扩展
- 检查Service Worker日志

## 测试

重新加载扩展后，测试以下功能：

1. **右键菜单**: 在购物网站上右键，应该看到"分析当前商品"选项
2. **Sidepanel**: 点击扩展图标，打开侧边栏
3. **聊天功能**: 在sidepanel中发送消息，应该能正常收到回复

如果所有功能都正常，说明问题已解决！

