# 万邦API配置指南

## 概述

本项目已集成万邦（Onebound）API用于获取电商平台商品数据，支持淘宝、京东、拼多多等多个平台。

## 配置步骤

### 1. 获取API密钥

1. 访问万邦API官网：http://console.open.onebound.cn/console/
2. 注册账号并登录
3. 在控制台获取你的 `API Key` 和 `Secret`
4. 测试Key：`test_api_key`（可用于测试，不需要secret）

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# 万邦API配置
ONEBOUND_API_KEY=your_api_key_here
ONEBOUND_API_SECRET=your_api_secret_here  # 如果使用测试key，可以不填
```

### 3. 验证配置

启动服务后，系统会自动使用万邦API进行商品搜索。如果配置正确，会在日志中看到：

```
INFO: 万邦API搜索成功，返回 X 个商品
```

## API功能

### 已实现的功能

1. **商品搜索**
   - 支持淘宝、天猫、京东、拼多多
   - 支持价格区间、分类、排序等筛选
   - 支持分页查询

2. **商品详情**
   - 获取商品完整信息
   - 包含价格、销量、评价等数据

3. **历史价格**
   - 获取商品历史价格趋势

4. **相似商品**
   - 搜索相似商品推荐

### 支持的平台

- ✅ 淘宝 (taobao)
- ✅ 天猫 (tmall)
- ✅ 京东 (jd)
- ✅ 拼多多 (pdd)

## 使用方式

### 在代码中使用

万邦API已集成到 `ShoppingService` 中，会自动使用：

```python
from app.services.shopping_service import ShoppingService

# 搜索商品
search_request = ProductSearchRequest(
    query="手机",
    platforms=[PlatformType.TAOBAO, PlatformType.JD],
    page=1,
    page_size=20
)

results = await shopping_service.search_products(search_request)
```

### API调用优先级

系统会按以下顺序尝试获取数据：

1. **网络爬虫**（如果可用）
2. **万邦API**（优先使用）
3. **其他API**（如果配置了）
4. **数据库**（本地缓存）
5. **备用数据**（最后兜底）

## API参数说明

### 通用参数

- `key`: API密钥（必需）
- `secret`: API密钥（可选，测试key不需要）
- `lang`: 语言，`zh-CN`（中文）、`en`（英文）、`ru`（俄文）
- `result_type`: 返回格式，`json`（默认）、`xml`、`serialize`
- `cache`: 是否使用缓存，`yes`（默认）、`no`

### 搜索参数 (item_search)

- `q`: 搜索关键字（必需）
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认40，最大200）
- `start_price`: 起始价格
- `end_price`: 结束价格
- `sort`: 排序方式
  - `default`: 默认排序
  - `bid`: 总价从低到高
  - `bid2`: 商品价格从低到高
  - `_bid2`: 商品价格从高到低
  - `_sale`: 销量从高到低
  - `_credit`: 信用从高到低
- `cat`: 分类ID
- `seller_info`: 是否获取商家信息，`yes`（默认）、`no`

### 商品详情参数 (item_get)

- `num_iid`: 商品ID（必需）

## 错误处理

### 常见错误

1. **API密钥错误**
   ```
   Error: API请求失败: 401
   ```
   - 解决：检查 `ONEBOUND_API_KEY` 是否正确

2. **请求频率过高**
   ```
   Error: API请求失败: 429
   ```
   - 解决：降低请求频率，使用缓存

3. **余额不足**
   ```
   Error: 余额不足
   ```
   - 解决：在控制台充值

### 降级策略

如果万邦API失败，系统会自动：
1. 记录错误日志
2. 尝试使用其他数据源（爬虫、数据库等）
3. 返回可用数据或空结果

## 费用说明

- 测试Key（`test_api_key`）：免费，但功能受限
- 正式Key：按调用次数计费，具体价格请参考官网
- 建议：在生产环境使用正式Key，确保数据质量和稳定性

## 注意事项

1. **不要乱传参数**：即使请求失败也会扣费
2. **使用缓存**：默认启用缓存（`cache=yes`），可以节省费用和提高速度
3. **合理控制频率**：避免请求过于频繁导致限流
4. **错误处理**：始终检查返回结果中的 `error` 字段

## 更多信息

- 官方文档：https://open.onebound.cn/help/api/taobao.readme.html
- 测试界面：http://open.onebound.cn/test/?api_type=taobao&
- 控制台：http://console.open.onebound.cn/console/

## 代码位置

- API客户端：`backend/app/services/onebound_api_client.py`
- 配置：`backend/app/core/config.py`
- 集成：`backend/app/services/shopping_service.py`

