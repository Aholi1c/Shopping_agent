# 比价功能和价格追踪功能使用指南

## 📊 功能概述

### 1. 比价功能（Price Comparison）

**作用：**
- **多平台价格对比**：自动搜索京东、淘宝、拼多多等多个平台，找出同一商品在不同平台的价格
- **节省金额计算**：计算在各平台购买可以节省多少钱
- **最佳购买推荐**：推荐价格最优惠的平台
- **价格差异分析**：展示价格差异百分比和绝对金额

**使用场景：**
- 购买前想了解哪个平台最便宜
- 想要找到性价比最高的购买渠道
- 需要比较多个平台的价格和优惠情况

### 2. 价格追踪功能（Price Tracking）

**作用：**
- **价格历史记录**：记录商品价格的变化历史
- **价格趋势分析**：分析价格是上升、下降还是稳定
- **价格预测**：基于历史数据预测未来7天的价格趋势
- **降价提醒**：设置目标价格，当商品降到目标价格时收到提醒
- **价格变化统计**：显示最高价、最低价、平均价等统计信息

**使用场景：**
- 想等待商品降价再购买
- 需要监控心仪商品的价格变化
- 想了解商品价格的波动规律
- 需要设置降价提醒，不错过优惠

---

## 🚀 使用方法

### 方法一：通过浏览器扩展使用（推荐）

#### 使用比价功能：

1. **打开侧边栏**
   - 在任意购物网站（京东、淘宝、拼多多、Amazon等）浏览商品
   - 点击浏览器扩展图标，打开侧边栏

2. **输入商品名称**
   - 在侧边栏中找到"比价"标签页
   - 在搜索框输入商品名称（例如："iPhone 15 Pro"）
   - 或者直接点击当前页面的商品进行比价

3. **开始比价**
   - 点击"开始比价"或"搜索"按钮
   - 系统会自动搜索京东、淘宝、拼多多等平台
   - 等待几秒钟，系统会显示各平台的价格对比结果

4. **查看结果**
   - **价格对比表**：显示各平台的价格、优惠、销量等信息
   - **最佳推荐**：系统会标记价格最低的平台
   - **节省金额**：显示如果选择最便宜的平台可以节省多少钱

#### 使用价格追踪功能：

1. **打开商品详情页**
   - 在京东、淘宝等购物网站打开你想追踪的商品页面

2. **打开侧边栏**
   - 点击浏览器扩展图标，打开侧边栏
   - 切换到"追踪"或"价格追踪"标签页

3. **查看价格历史**
   - 系统会自动显示该商品的价格历史记录
   - 可以看到过去30天的价格变化趋势图

4. **设置价格提醒（可选）**
   - 在"目标价格"输入框中输入你期望的价格
   - 点击"开始追踪"或"设置提醒"按钮
   - 当商品价格降到目标价格时，系统会通知你

5. **查看价格预测**
   - 系统会基于历史数据预测未来7天的价格趋势
   - 显示预测价格和置信度

---

### 方法二：通过API直接调用

#### 比价API：

**端点：** `POST /api/shopping/price-comparison`

**请求示例：**
```javascript
// JavaScript (浏览器扩展)
const result = await window.apiClient.comparePrices(
  "iPhone 15 Pro",
  ['jd', 'taobao', 'pdd']
);
```

**或者使用fetch：**
```javascript
fetch('http://localhost:8000/api/shopping/price-comparison', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: "iPhone 15 Pro",
    platforms: ["jd", "taobao", "pdd"]
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

**返回结果示例：**
```json
{
  "query": "iPhone 15 Pro",
  "comparison": {
    "iPhone 15 Pro": {
      "products": [
        {
          "title": "iPhone 15 Pro 256GB",
          "price": 8999,
          "platform": "jd",
          "original_price": 9999
        },
        {
          "title": "iPhone 15 Pro 256GB",
          "price": 8799,
          "platform": "taobao",
          "original_price": 9999
        }
      ],
      "min_price": 8799,
      "max_price": 8999,
      "price_difference": 200,
      "savings_percentage": 2.22,
      "best_platform": "taobao"
    }
  },
  "total_products": 20,
  "search_time": 2.5
}
```

#### 价格追踪API：

**1. 查看价格历史：**
**端点：** `GET /api/shopping/products/{product_id}/price-tracking?days=30`

**请求示例：**
```javascript
// JavaScript
const result = await window.apiClient.getPriceHistory(12345, 30);
```

**返回结果示例：**
```json
{
  "product_id": 12345,
  "current_price": 8999,
  "start_price": 9999,
  "min_price": 8499,
  "max_price": 9999,
  "average_price": 9249,
  "price_change": -1000,
  "price_change_percent": -10.01,
  "trend": "下降",
  "prediction": {
    "predicted_price": 8699,
    "confidence": 0.85,
    "trend_direction": "下降",
    "days_predicted": 7
  },
  "history": [
    {
      "date": "2024-01-01 10:00",
      "price": 9999,
      "original_price": 9999
    },
    {
      "date": "2024-01-05 10:00",
      "price": 9499,
      "original_price": 9999
    }
  ]
}
```

**2. 设置价格提醒：**
**端点：** `POST /api/price-tracker/alerts?user_id={user_id}`

**请求示例：**
```javascript
const result = await fetch('http://localhost:8000/api/price-tracker/alerts?user_id=123', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    product_id: "12345",
    target_price: 8500,
    alert_type: "below_target",
    notification_method: "app"
  })
});
```

**3. 启动价格追踪：**
**端点：** `POST /api/price-tracker/track`

**请求示例：**
```javascript
const result = await fetch('http://localhost:8000/api/price-tracker/track', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    product_ids: ["12345", "67890"],
    force_update: false
  })
});
```

---

## 💡 使用技巧

### 比价功能：

1. **使用具体商品名称**
   - ✅ 好：`iPhone 15 Pro 256GB 深空黑色`
   - ❌ 差：`手机`（太模糊，结果不准确）

2. **比较多个平台**
   - 系统默认比较：京东、淘宝、拼多多
   - 可以根据需要选择特定平台进行比较

3. **关注综合成本**
   - 不仅看价格，还要考虑：
     - 运费
     - 优惠券
     - 售后服务
     - 物流速度

4. **查看详细信息**
   - 点击比价结果中的商品可以查看详情
   - 检查商品规格是否完全一致

### 价格追踪功能：

1. **合理设置目标价格**
   - 参考历史最低价设置目标
   - 不要设置过低，可能永远达不到

2. **关注价格趋势**
   - 如果趋势是"上升"，建议尽快购买
   - 如果趋势是"下降"，可以等待降价

3. **结合价格预测**
   - 查看系统预测的未来价格
   - 注意预测的置信度（confidence）
   - 置信度高（>0.8）的预测更可靠

4. **定期检查追踪列表**
   - 定期查看你设置的价格提醒
   - 删除不再感兴趣的商品追踪

---

## 📱 前端界面说明

### 比价界面（Comparison View）

在浏览器扩展侧边栏的"比价"标签页，你会看到：

- **搜索框**：输入商品名称
- **平台选择**：选择要比较的平台（默认全选）
- **比价结果卡片**：
  - 商品图片
  - 商品名称
  - 价格（原价/现价）
  - 平台标识
  - 节省金额标签
- **最佳推荐标识**：价格最低的商品会有特殊标记

### 价格追踪界面（Tracker View）

在浏览器扩展侧边栏的"追踪"标签页，你会看到：

- **当前商品信息**：名称、当前价格
- **价格趋势图**：显示过去30天的价格变化曲线
- **统计信息卡片**：
  - 当前价格
  - 历史最低价
  - 历史最高价
  - 平均价格
  - 价格变化百分比
- **目标价格设置**：
  - 输入目标价格
  - "开始追踪"按钮
- **价格预测**：
  - 未来7天预测价格
  - 置信度显示
  - 趋势方向（上升/下降/稳定）

---

## ⚠️ 注意事项

### 比价功能：

1. **价格可能有延迟**
   - 商品价格实时变化，比价结果可能不是最新价格
   - 建议在购买前再次确认价格

2. **商品规格要一致**
   - 不同平台的同款商品可能有不同规格
   - 确认比较的是完全相同的商品

3. **库存情况**
   - 价格最便宜的商品可能缺货
   - 需要检查库存状态

### 价格追踪功能：

1. **需要商品ID**
   - 价格追踪需要商品的唯一ID
   - 确保商品已在系统中注册

2. **价格历史数据**
   - 新商品可能没有足够的历史数据
   - 价格预测需要至少2个历史价格点

3. **提醒通知**
   - 价格提醒功能需要后端任务调度（Celery）
   - 确保后端服务正在运行

---

## 🔧 技术实现

### 比价功能流程：

```
用户输入商品名
    ↓
ShoppingService.search_products() - 多平台搜索
    ↓
OneboundAPI / Web Scraper - 获取实时价格
    ↓
PriceService.compare_prices() - 价格对比计算
    ↓
返回对比结果（最低价、节省金额、最佳平台）
```

### 价格追踪功能流程：

```
用户设置追踪
    ↓
PriceTrackerService.track_product_prices() - 记录当前价格
    ↓
存储到PriceHistory表
    ↓
PriceService.track_price_changes() - 分析历史数据
    ↓
计算趋势、统计信息、预测未来价格
    ↓
返回价格历史和预测结果
```

---

## 📞 常见问题

**Q: 比价结果显示"未找到商品"怎么办？**
A: 
- 检查商品名称是否准确
- 尝试使用更通用的商品名称
- 检查网络连接
- 确认万邦API配置正确

**Q: 价格追踪显示"无历史数据"？**
A:
- 该商品可能是新添加的，还没有价格历史
- 系统会从设置追踪时开始记录
- 等待几天后就会有历史数据

**Q: 价格预测不准确？**
A:
- 价格预测基于历史数据，价格波动大的商品预测不准确
- 查看置信度（confidence），置信度低（<0.5）的预测不可靠
- 预测只是参考，实际购买时仍需确认价格

**Q: 如何取消价格追踪？**
A:
- 在追踪列表中找到要取消的商品
- 点击"取消追踪"或删除按钮
- 或者调用API删除提醒

---

## 📚 相关API文档

详细的API文档请参考：
- 后端API文档：`http://localhost:8000/docs`
- 价格服务文档：`backend/app/services/price_service.py`
- 价格追踪服务：`backend/app/services/price_tracker_service.py`

---

## 🎯 总结

- **比价功能**：帮助你在购买前找到最便宜的平台，节省开支
- **价格追踪功能**：帮你监控商品价格变化，在最佳时机购买

两个功能可以结合使用：
1. 先用比价功能找到最便宜的平台
2. 然后设置价格追踪，等待进一步降价

这样既能买到最便宜的商品，又不会错过更好的优惠！

