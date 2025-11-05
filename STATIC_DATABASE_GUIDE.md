# 静态商品数据库使用指南

## 📋 概述

本系统支持使用静态数据库来存储和管理商品数据，无需依赖万邦API或其他外部API。您可以：
1. 批量上传商品数据（JSON或CSV格式）
2. 管理商品数据（查询、更新、删除）
3. 使用数据库数据进行比价和分析

## 🚀 快速开始

### 1. 上传商品数据

#### 方式一：通过API上传（JSON格式）

**API端点**：`POST /api/product-management/products/upload`

**请求示例**：
```bash
curl -X POST "http://localhost:8000/api/product-management/products/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {
        "platform": "jd",
        "product_id": "123456",
        "title": "iPhone 15 Pro 256GB",
        "price": 7999.0,
        "original_price": 8999.0,
        "discount_rate": 11.1,
        "category": "手机",
        "brand": "Apple",
        "description": "iPhone 15 Pro 256GB 深空黑色",
        "image_url": "https://example.com/image.jpg",
        "product_url": "https://item.jd.com/123456.html",
        "rating": 4.8,
        "review_count": 1250,
        "sales_count": 5000,
        "stock_status": "有货",
        "specs": {
          "存储容量": "256GB",
          "屏幕尺寸": "6.1英寸",
          "处理器": "A17 Pro",
          "内存": "8GB"
        }
      },
      {
        "platform": "taobao",
        "product_id": "789012",
        "title": "iPhone 15 Pro 256GB",
        "price": 7899.0,
        "original_price": 8999.0,
        "discount_rate": 12.2,
        "category": "手机",
        "brand": "Apple",
        "description": "iPhone 15 Pro 256GB 官方正品",
        "image_url": "https://example.com/image2.jpg",
        "product_url": "https://item.taobao.com/789012.html",
        "rating": 4.7,
        "review_count": 890,
        "sales_count": 3200,
        "stock_status": "有货"
      }
    ]
  }'
```

#### 方式二：通过JSON文件上传

**API端点**：`POST /api/product-management/products/upload/json`

**请求示例**：
```bash
curl -X POST "http://localhost:8000/api/product-management/products/upload/json" \
  -F "file=@products.json"
```

**products.json 格式**：
```json
{
  "products": [
    {
      "platform": "jd",
      "product_id": "123456",
      "title": "iPhone 15 Pro 256GB",
      "price": 7999.0,
      "category": "手机",
      "brand": "Apple"
    }
  ]
}
```

#### 方式三：通过CSV文件上传

**API端点**：`POST /api/product-management/products/upload/csv`

**请求示例**：
```bash
curl -X POST "http://localhost:8000/api/product-management/products/upload/csv" \
  -F "file=@products.csv"
```

**products.csv 格式**（需要包含以下列）：
```csv
platform,product_id,title,price,original_price,discount_rate,category,brand,description,image_url,product_url,rating,review_count,sales_count,stock_status
jd,123456,iPhone 15 Pro 256GB,7999.0,8999.0,11.1,手机,Apple,iPhone 15 Pro 256GB 深空黑色,https://example.com/image.jpg,https://item.jd.com/123456.html,4.8,1250,5000,有货
taobao,789012,iPhone 15 Pro 256GB,7899.0,8999.0,12.2,手机,Apple,iPhone 15 Pro 256GB 官方正品,https://example.com/image2.jpg,https://item.taobao.com/789012.html,4.7,890,3200,有货
```

### 2. 查询商品数据

#### 查询商品列表

**API端点**：`GET /api/product-management/products`

**查询参数**：
- `platform`：平台过滤（可选）
- `category`：类别过滤（可选）
- `brand`：品牌过滤（可选）
- `keyword`：关键词搜索（可选）
- `page`：页码（默认1）
- `page_size`：每页数量（默认20，最大100）

**示例**：
```bash
# 查询所有商品
curl "http://localhost:8000/api/product-management/products"

# 查询京东平台的手机
curl "http://localhost:8000/api/product-management/products?platform=jd&category=手机"

# 搜索包含"iPhone"的商品
curl "http://localhost:8000/api/product-management/products?keyword=iPhone"
```

#### 获取商品详情

**API端点**：`GET /api/product-management/products/{product_id}`

**示例**：
```bash
curl "http://localhost:8000/api/product-management/products/1"
```

### 3. 更新商品数据

**API端点**：`PUT /api/product-management/products/{product_id}`

**示例**：
```bash
curl -X PUT "http://localhost:8000/api/product-management/products/1" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 7599.0,
    "stock_status": "有货"
  }'
```

### 4. 删除商品

**API端点**：`DELETE /api/product-management/products/{product_id}`

**示例**：
```bash
curl -X DELETE "http://localhost:8000/api/product-management/products/1"
```

### 5. 获取统计信息

**API端点**：`GET /api/product-management/products/stats`

**示例**：
```bash
curl "http://localhost:8000/api/product-management/products/stats"
```

## 🔍 使用数据库数据进行比价和分析

### 比价功能

系统会自动优先使用数据库中的数据进行比较。如果数据库中有多个平台的相同商品数据，比价功能会自动对比：

```bash
# 前端比价功能会自动使用数据库数据
# 在浏览器扩展侧边栏的"比价"标签中搜索商品即可
```

### 分析功能

商品分析功能也会优先使用数据库中的数据：

```bash
# 在商品详情页面右键选择"分析当前商品"
# 或打开侧边栏 → "分析"标签 → 点击"分析商品"
```

## 📊 数据库结构

### Product 表字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键 |
| platform | String | 平台名称（jd, taobao, pdd等） |
| product_id | String | 平台商品ID |
| title | String | 商品标题 |
| description | Text | 商品描述 |
| category | String | 商品类别 |
| brand | String | 品牌 |
| price | Float | 当前价格 |
| original_price | Float | 原价 |
| discount_rate | Float | 折扣率 |
| image_url | Text | 图片URL |
| product_url | Text | 商品URL |
| rating | Float | 评分 |
| review_count | Integer | 评价数量 |
| sales_count | Integer | 销量 |
| stock_status | String | 库存状态 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### ProductSpec 表（商品规格）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键 |
| product_id | Integer | 商品ID（外键） |
| spec_name | String | 规格名称 |
| spec_value | Text | 规格值 |

### PriceHistory 表（价格历史）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键 |
| product_id | Integer | 商品ID（外键） |
| price | Float | 价格 |
| timestamp | DateTime | 时间戳 |

## 💡 使用建议

### 1. 数据准备

建议准备包含以下信息的商品数据：
- **必需字段**：platform, product_id, title, price
- **推荐字段**：category, brand, description, image_url
- **可选字段**：rating, review_count, sales_count, specs

### 2. 批量上传

对于大量商品数据，建议：
- 使用CSV格式上传（更易编辑）
- 分批上传（每批100-500个商品）
- 上传后检查统计信息确认数据完整性

### 3. 数据维护

- 定期更新商品价格（使用PUT API）
- 删除下架商品（使用DELETE API）
- 查看统计信息了解数据分布

### 4. 比价数据准备

要实现比价功能，建议：
- 同一商品在不同平台的数据使用相同的 `title` 或包含相同的关键词
- 确保 `category` 和 `brand` 字段准确
- 定期更新价格信息

## 🔧 配置说明

### 禁用外部API（仅使用数据库）

如果您想完全禁用外部API（万邦API、爬虫等），只使用数据库数据：

1. **修改 shopping_service.py**：
   - 注释掉或删除万邦API调用代码
   - 注释掉爬虫调用代码

2. **确保数据库中有足够的数据**：
   - 上传您需要的商品数据
   - 确保覆盖您要比较的平台

## 📝 示例数据

### 完整的商品数据示例

```json
{
  "products": [
    {
      "platform": "jd",
      "product_id": "100012043978",
      "title": "Apple iPhone 15 Pro (A3104) 256GB 原色钛金属 支持移动联通电信5G 双卡双待手机",
      "price": 7999.0,
      "original_price": 8999.0,
      "discount_rate": 11.1,
      "category": "手机",
      "brand": "Apple",
      "description": "Apple iPhone 15 Pro采用钛金属设计，配备A17 Pro芯片，支持Action按钮，全新4800万像素主摄像头。",
      "image_url": "https://img14.360buyimg.com/n1/jfs/t1/123456/...",
      "product_url": "https://item.jd.com/100012043978.html",
      "rating": 4.8,
      "review_count": 1250,
      "sales_count": 5000,
      "stock_status": "有货",
      "specs": {
        "存储容量": "256GB",
        "屏幕尺寸": "6.1英寸",
        "处理器": "A17 Pro",
        "内存": "8GB",
        "后置摄像头": "4800万像素",
        "前置摄像头": "1200万像素",
        "电池容量": "3274mAh",
        "网络制式": "5G",
        "颜色": "原色钛金属"
      }
    },
    {
      "platform": "taobao",
      "product_id": "12345678901",
      "title": "Apple iPhone 15 Pro 256GB 原色钛金属 官方正品",
      "price": 7899.0,
      "original_price": 8999.0,
      "discount_rate": 12.2,
      "category": "手机",
      "brand": "Apple",
      "description": "Apple iPhone 15 Pro 256GB 原色钛金属 官方正品 全国联保",
      "image_url": "https://img.alicdn.com/imgextra/i1/...",
      "product_url": "https://item.taobao.com/item.htm?id=12345678901",
      "rating": 4.7,
      "review_count": 890,
      "sales_count": 3200,
      "stock_status": "有货"
    }
  ]
}
```

## 🆘 常见问题

### Q: 如何知道数据库中是否有数据？

A: 使用统计API：
```bash
curl "http://localhost:8000/api/product-management/products/stats"
```

### Q: 上传失败怎么办？

A: 检查：
1. JSON/CSV格式是否正确
2. 必需字段是否齐全
3. 数据类型是否正确（price是数字，不是字符串）
4. 查看API返回的错误信息

### Q: 如何更新商品价格？

A: 使用PUT API更新特定商品的价格，系统会自动记录到价格历史表。

### Q: 比价功能找不到数据？

A: 确保：
1. 数据库中有所需平台的商品数据
2. 商品标题包含相同的关键词
3. 使用keyword搜索时输入正确的关键词

## 📚 API文档

完整的API文档可以在以下地址查看：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

查找 `Product Management` 标签下的API端点。

