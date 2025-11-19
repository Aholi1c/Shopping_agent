# 🛍️ 智能购物助手浏览器插件

这是一个浏览器插件版本的智能购物助手，可以在用户浏览购物网站时提供智能购物助手功能。

## 📋 功能特性

- ✅ **自动商品信息提取**: 自动识别并提取当前页面的商品信息
- ✅ **智能对话助手**: 在侧边栏中提供智能聊天功能
- ✅ **商品分析**: 商品价格、风险、预测分析
- ✅ **价格对比**: 多平台价格实时对比
- ✅ **价格追踪**: 商品价格变化追踪和提醒
- ✅ **智能推荐**: 基于用户偏好的商品推荐
- ✅ **浮动按钮**: 页面上的快速访问按钮

## 🚀 安装步骤

### 1. 准备文件

确保所有文件都在 `browser-extension` 目录中：
- `manifest.json`
- `background.js`
- `content.js`
- `content.css`
- `popup.html`
- `popup.js`
- `popup.css`
- `sidepanel.html`
- `sidepanel.js`
- `sidepanel.css`
- `api.js`
- `icons/` 目录（包含图标文件）

### 2. 准备图标

在 `icons/` 目录中准备以下尺寸的图标：
- `icon16.png` (16x16)
- `icon32.png` (32x32)
- `icon48.png` (48x48)
- `icon128.png` (128x128)

如果没有图标，可以使用在线工具生成或使用占位图标。

### 3. 安装插件

#### Chrome/Edge

1. 打开 Chrome/Edge 浏览器
2. 访问 `chrome://extensions/` 或 `edge://extensions/`
3. 启用"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择 `browser-extension` 目录
6. 插件安装完成

#### Firefox

1. 打开 Firefox 浏览器
2. 访问 `about:debugging`
3. 点击"此 Firefox"
4. 点击"临时载入附加组件"
5. 选择 `manifest.json` 文件

### 4. 配置后端API

1. 确保后端服务正在运行（默认 `http://localhost:8000`）
2. 点击插件图标，打开弹窗
3. 检查连接状态（应显示"已连接"）

## 🎯 使用方法

### 基本使用

1. **访问购物网站**: 打开京东、淘宝、拼多多等购物网站
2. **打开商品页面**: 浏览到具体商品页面
3. **打开助手**: 
   - 点击页面右下角的浮动按钮
   - 或点击浏览器工具栏中的插件图标

### 功能说明

#### 1. 弹窗界面（Popup）

点击浏览器工具栏中的插件图标，会打开一个小弹窗：
- 显示当前商品信息（如果已识别）
- 快速操作按钮：
  - 💬 智能聊天
  - 📊 价格追踪
  - 🔍 比价
  - ⭐ 推荐

#### 2. 侧边栏界面（Sidepanel）

点击"打开助手面板"或浮动按钮，会打开侧边栏界面：
- **💬 聊天**: 与智能助手对话，获取购物建议
- **📊 分析**: 查看商品详细分析（价格、风险、预测）
- **🔍 比价**: 对比不同平台的价格
- **📈 追踪**: 设置价格追踪和提醒

### 支持的购物网站

- ✅ 京东 (jd.com)
- ✅ 淘宝 (taobao.com)
- ✅ 天猫 (tmall.com)
- ✅ 拼多多 (pdd.com)
- ✅ 小红书 (xiaohongshu.com)
- ✅ 抖音 (douyin.com)
- ✅ 亚马逊中国 (amazon.cn)

## 🔧 配置

### API地址配置

默认API地址为 `http://localhost:8000`，如果需要更改：

1. 右键点击插件图标
2. 选择"选项"（如果有设置页面）
3. 或直接在 `background.js` 中修改 `API_BASE_URL`

### 权限说明

插件需要以下权限：
- **storage**: 存储用户配置和商品信息
- **activeTab**: 访问当前标签页
- **scripting**: 注入脚本到页面
- **sidePanel**: 打开侧边栏
- **tabs**: 管理标签页

## 📁 文件结构

```
browser-extension/
├── manifest.json          # 插件清单文件
├── background.js          # 后台服务脚本
├── content.js            # 内容脚本（注入到页面）
├── content.css           # 内容样式
├── popup.html            # 弹窗HTML
├── popup.js              # 弹窗脚本
├── popup.css             # 弹窗样式
├── sidepanel.html        # 侧边栏HTML
├── sidepanel.js          # 侧边栏脚本
├── sidepanel.css         # 侧边栏样式
├── api.js                # API客户端
├── icons/                # 图标目录
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── README.md             # 本文档
```

## 🛠️ 开发

### 修改代码

1. 修改相关文件
2. 在浏览器中重新加载插件：
   - Chrome: 点击 `chrome://extensions/` 页面中的刷新按钮
   - Firefox: 点击 `about:debugging` 页面中的重新加载按钮

### 调试

#### Content Script 调试

1. 在购物网站页面右键
2. 选择"检查"
3. 在开发者工具中可以看到 content script 的日志

#### Background Script 调试

1. 打开 `chrome://extensions/` 或 `edge://extensions/`
2. 找到插件
3. 点击"service worker"链接
4. 会打开后台脚本的开发者工具

#### Popup 调试

1. 右键点击插件图标
2. 选择"检查弹出内容"
3. 会打开弹窗的开发者工具

#### Sidepanel 调试

1. 打开侧边栏
2. 在侧边栏中右键
3. 选择"检查"
4. 会打开侧边栏的开发者工具

## 🐛 故障排除

### 插件无法加载

1. 检查 `manifest.json` 格式是否正确
2. 检查所有必需文件是否存在
3. 查看浏览器控制台的错误信息

### 无法提取商品信息

1. 检查当前页面是否在支持的购物网站列表中
2. 检查页面是否完全加载
3. 检查 content script 是否正常注入

### API连接失败

1. 检查后端服务是否运行
2. 检查API地址配置是否正确
3. 检查网络连接
4. 检查浏览器控制台的错误信息

### 侧边栏无法打开

1. 检查浏览器是否支持侧边栏（Chrome 114+, Edge 114+）
2. 检查 `manifest.json` 中的 `side_panel` 配置
3. 检查权限是否正确设置

## 📝 更新日志

### v2.1.0

- ✅ 初始版本发布
- ✅ 基础商品信息提取
- ✅ 弹窗和侧边栏界面
- ✅ API集成
- ✅ 支持多个购物平台

## 🤝 贡献

欢迎提交问题报告和功能建议！

## 📄 许可证

MIT License

---

**注意**: 本插件需要后端API服务才能正常工作。请确保后端服务正在运行。

