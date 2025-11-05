# 商品数据管理指南

## 📋 概述

本文档说明如何向数据库中添加和管理商品数据。

## 🚀 快速上传数据

### 方法一：使用上传脚本（推荐）

1. **确保后端服务正在运行**
   ```bash
   cd backend
   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **使用上传脚本**
   ```bash
   # 上传 products_data.json
   python3 upload_products.py products_data.json
   
   # 或指定其他JSON文件
   python3 upload_products.py your_products.json
   ```

### 方法二：使用curl命令

```bash
curl -X POST "http://localhost:8000/api/product-management/products/upload" \
  -H "Content-Type: application/json" \
  -d @products_data.json
```

### 方法三：使用API端点（从文件上传）

```bash
curl -X POST "http://localhost:8000/api/product-management/products/upload/json" \
  -F "file=@products_data.json"
```

## 📝 修改 products_data.json 添加新数据

### ✅ 可以！您可以直接修改 products_data.json 文件来添加数据

**步骤：**

1. **编辑 products_data.json 文件**
   ```json
   {
     "products": [
       {
         "platform": "jd",
         "product_id": "100012043978",
         "title": "商品名称",
         "price": 7999.0,
         ...
       },
       {
         // 添加新商品...
       }
     ]
   }
   ```

2. **重新上传**
   ```bash
   python3 upload_products.py products_data.json
   ```

   **注意**：
   - 如果商品已存在（相同的 platform + product_id），系统会**更新**该商品
   - 如果是新商品，系统会**创建**新记录

### 📋 JSON格式要求

```json
{
  "products": [
    {
      "platform": "jd",                    // 必需：平台名称（jd, taobao, pdd等）
      "product_id": "100012043978",         // 必需：平台商品ID
      "title": "商品标题",                  // 必需：商品标题
      "price": 7999.0,                      // 必需：当前价格（数字）
      "original_price": 8999.0,            // 可选：原价
      "discount_rate": 11.1,               // 可选：折扣率
      "category": "手机",                   // 可选：类别
      "brand": "Apple",                     // 可选：品牌
      "description": "商品描述",           // 可选：描述
      "image_url": "https://...",           // 可选：图片URL
      "product_url": "https://...",         // 可选：商品URL
      "rating": 4.8,                       // 可选：评分（0-5）
      "review_count": 1250,                // 可选：评价数量
      "sales_count": 5000,                 // 可选：销量
      "stock_status": "有货",              // 可选：库存状态
      "specs": {                           // 可选：商品规格
        "存储容量": "256GB",
        "屏幕尺寸": "6.1英寸",
        "处理器": "A17 Pro"
      }
    }
  ]
}
```

## 📦 添加其他JSON格式的数据

### 方式一：创建新的JSON文件

1. **创建新的JSON文件**（例如：`new_products.json`）
   ```json
   {
     "products": [
       {
         "platform": "jd",
         "product_id": "999999999",
         "title": "新商品",
         "price": 2999.0
       }
     ]
   }
   ```

2. **上传新文件**
   ```bash
   python3 upload_products.py new_products.json
   ```

### 方式二：合并多个JSON文件

可以使用脚本合并多个JSON文件：

```python
import json

# 读取多个文件
files = ['products_data.json', 'new_products.json']
all_products = []

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        all_products.extend(data['products'])

# 合并并保存
merged_data = {"products": all_products}
with open('merged_products.json', 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2)

# 上传合并后的文件
print("合并完成！现在可以上传 merged_products.json")
```

## 🔄 更新现有商品数据

### 方法一：修改JSON文件后重新上传

系统会自动检测：
- 如果 `platform` + `product_id` 已存在 → **更新**商品
- 如果是新商品 → **创建**新记录

### 方法二：使用API更新单个商品

```bash
# 更新商品ID为1的商品价格
curl -X PUT "http://localhost:8000/api/product-management/products/1" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 7599.0,
    "stock_status": "有货"
  }'
```

## 📊 管理商品数据

### 查询商品列表

```bash
# 查询所有商品
curl "http://localhost:8000/api/product-management/products"

# 查询京东平台的手机
curl "http://localhost:8000/api/product-management/products?platform=jd&category=手机"

# 搜索包含"iPhone"的商品
curl "http://localhost:8000/api/product-management/products?keyword=iPhone"
```

### 查看统计信息

```bash
curl "http://localhost:8000/api/product-management/products/stats"
```

### 获取商品详情

```bash
curl "http://localhost:8000/api/product-management/products/1"
```

### 删除商品

```bash
curl -X DELETE "http://localhost:8000/api/product-management/products/1"
```

## 💡 最佳实践

### 1. 数据准备

- ✅ 确保必需字段完整：`platform`, `product_id`, `title`, `price`
- ✅ 使用相同的商品标题关键词便于比价（例如："iPhone 15 Pro 256GB"）
- ✅ 填写准确的类别和品牌信息

### 2. 批量上传

- ✅ 每次上传100-500个商品最佳
- ✅ 上传后检查统计信息确认数据完整性
- ✅ 如果上传失败，查看错误信息并修复

### 3. 数据维护

- ✅ 定期更新商品价格
- ✅ 删除下架商品
- ✅ 保持数据一致性

### 4. 比价数据准备

要实现比价功能，建议：
- ✅ 同一商品在不同平台使用相同的关键词（如"iPhone 15 Pro 256GB"）
- ✅ 确保 `category` 和 `brand` 字段准确
- ✅ 定期更新价格信息

## 🆘 常见问题

### Q: 上传时提示"商品已存在"？

A: 这是正常的。系统会根据 `platform` + `product_id` 判断商品是否已存在：
- 如果已存在 → 更新商品信息
- 如果是新商品 → 创建新记录

### Q: 如何知道上传是否成功？

A: 上传脚本会显示：
- ✅ 成功数量
- ❌ 失败数量
- ⚠️ 错误详情（如果有）

### Q: 可以修改 products_data.json 后直接使用吗？

A: 可以！修改后使用 `python3 upload_products.py products_data.json` 重新上传即可。

### Q: 如何批量添加多个商品？

A: 直接在 `products` 数组中添加更多商品对象即可：

```json
{
  "products": [
    { "platform": "jd", "product_id": "1", ... },
    { "platform": "jd", "product_id": "2", ... },
    { "platform": "taobao", "product_id": "3", ... }
  ]
}
```

### Q: 上传失败怎么办？

A: 检查：
1. 后端服务是否运行
2. JSON格式是否正确
3. 必需字段是否齐全
4. 查看错误信息

## 📚 相关文档

- API文档：http://localhost:8000/docs （查找 "Product Management" 标签）
- 使用指南：STATIC_DATABASE_GUIDE.md

