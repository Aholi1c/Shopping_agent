# 商品信息提取调试指南

## 修复内容

### 1. Content Script (content.js)
✅ **改进商品信息提取**：
- 增加了更多的CSS选择器，提高提取成功率
- 京东、淘宝、拼多多都支持多个备用选择器
- 提取失败时自动重试

✅ **改进消息传递**：
- 提取商品信息后立即保存到storage（不等待background响应）
- 同时保存到 `product_{tabId}` 和 `product_current`
- 通知background商品信息已提取

✅ **分析流程优化**：
- analyzeCurrentPage 函数改为异步
- 添加重试机制
- 如果提取失败，显示友好的提示

### 2. Background Script (background.js)
✅ **改进消息处理**：
- 添加 `productInfoExtracted` 消息处理
- 使用轮询方式检查商品信息（最多5次，每次间隔500ms）
- 创建 `triggerAnalysis` 辅助函数统一处理分析触发

✅ **改进等待机制**：
- 不再固定等待1秒，而是使用轮询检查
- 即使找不到商品信息，也打开侧边栏让用户手动操作

## 调试步骤

### 1. 检查Content Script是否正确注入

打开商品页面，按F12打开开发者工具，在控制台输入：
```javascript
// 检查content script是否加载
console.log('Content script loaded:', typeof chrome !== 'undefined');

// 检查商品信息提取
// 在控制台可以看到日志输出
```

### 2. 检查Storage中的商品信息

在Background Service Worker的控制台中（chrome://extensions/ -> service worker链接），输入：
```javascript
// 检查storage
chrome.storage.local.get(null, (items) => {
  console.log('All storage items:', items);
  // 查看是否有 product_ 开头的键
});
```

### 3. 查看日志输出

查看以下位置的日志：
- **Content Script**: 商品页面的控制台
  - `开始提取商品信息，URL: ...`
  - `提取到的商品信息: ...`
  - `商品信息已直接保存到storage`

- **Background**: Service Worker控制台
  - `右键菜单点击: analyzeProduct`
  - `检查商品信息 (1/5)...`
  - `找到商品信息，触发分析: ...`

## 常见问题排查

### 问题1: "发送消息失败"
**可能原因**:
- Content script未加载或已卸载
- 页面是iframe或特殊结构

**解决方案**:
1. 检查manifest.json中的content_scripts配置
2. 确认页面URL匹配content_scripts的matches规则
3. 检查页面控制台是否有content script的错误

### 问题2: "未找到商品信息"
**可能原因**:
- 商品页面结构改变，选择器不匹配
- 页面是动态加载的，需要等待
- 不在商品详情页

**解决方案**:
1. 查看content script的控制台，看提取到的信息
2. 如果是动态页面，增加等待时间
3. 手动在侧边栏输入商品信息

### 问题3: 商品信息提取不完整
**解决方案**:
1. 在content.js中添加更多选择器
2. 使用通用的extractGenericProductInfo函数
3. 检查页面DOM结构，添加匹配的选择器

## 手动测试方法

如果自动提取失败，可以手动测试：

1. **在商品页面控制台手动提取**:
```javascript
// 在商品页面按F12，控制台输入：
const info = {};
const nameEl = document.querySelector('h1') || document.querySelector('.sku-name');
if (nameEl) info.name = nameEl.textContent.trim();

const priceEl = document.querySelector('.price') || document.querySelector('[data-price]');
if (priceEl) {
  const priceText = priceEl.textContent.trim().replace(/[^\d.]/g, '');
  info.price = parseFloat(priceText);
}

console.log('提取的商品信息:', info);
```

2. **手动保存到Storage**:
```javascript
// 在Background Service Worker控制台：
chrome.storage.local.set({
  'product_current': {
    name: '测试商品',
    price: 99,
    platform: 'jd',
    url: window.location.href
  }
}, () => {
  console.log('已保存');
});
```

3. **然后打开侧边栏手动触发分析**

## 预期日志输出

### 成功的流程应该看到：

**Content Script**:
```
开始提取商品信息，URL: https://item.jd.com/...
提取到的商品信息: {name: "...", price: 99, ...}
商品信息已直接保存到storage
商品信息已发送到background
开始分析当前页面...
商品信息: {...}
商品信息已保存到storage: product_123
分析成功: {...}
```

**Background**:
```
右键菜单点击: analyzeProduct {...}
检查商品信息 (1/5)...
找到商品信息，触发分析: {...}
商品信息已保存: product_123
分析请求已保存到storage
```

**Sidepanel**:
```
侧边栏初始化...
发现分析请求: {...}
自动触发分析...
```

