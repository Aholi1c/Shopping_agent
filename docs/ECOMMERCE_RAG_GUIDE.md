# 🛒 电商RAG知识库集成指南

本文档说明如何将电商平台数据集成到LLM Agent的RAG知识库中，实现智能商品推荐、价格分析和购物建议。

## 📋 概述

电商RAG知识库系统可以：
- 基于真实商品数据回答用户问题
- 提供智能商品推荐和价格分析
- 支持多平台价格对比
- 分析用户评价和市场趋势
- 生成个性化的购物建议

## 📊 数据格式要求

### 1. 必需的数据文件

将您的电商数据CSV文件放在 `data/ecommerce/` 目录下：

```
data/ecommerce/
├── products.csv           # 商品基本信息 (必需)
├── specifications.csv     # 规格参数 (可选)
├── price_history.csv      # 价格历史 (可选)
├── reviews.csv            # 用户评价 (可选)
└── README.md             # 数据说明
```

### 2. CSV文件格式

#### products.csv - 商品基本信息
```csv
product_id,product_name,brand,category,subcategory,current_price,original_price,discount_rate,platform,product_url,image_url,stock_status,shipping_info,created_at,updated_at
iphone_15_pro_256,Apple iPhone 15 Pro 256GB 深空黑,Apple,智能手机,旗舰机,8999,9999,10,jd,https://item.jd.com/123456.html,https://img.jd.com/iphone15.jpg,有货,免运费,2024-01-15,2024-09-25
```

#### specifications.csv - 规格参数
```csv
product_id,screen_size,processor,ram,storage,battery,camera,os,weight,material,colors,network,features
iphone_15_pro_256,6.1英寸,A17 Pro芯片,8GB,256GB,3274mAh,4800万像素,iOS 17,187g,钛金属,深空黑,5G,Face ID/灵动岛/USB-C
```

#### price_history.csv - 价格历史
```csv
product_id,price,platform,discount_type,promotion_info,date,is_stock_available,seller_info,monthly_sales
iphone_15_pro_256,9999,jd,无优惠,首发价,2024-01-15,是,Apple官方旗舰店,5000
```

#### reviews.csv - 用户评价
```csv
product_id,username,rating,content,pros,cons,purchase_date,helpful_count,verified_purchase,user_level,tags
iphone_15_pro_256,用户甲,5.0,拍照效果非常好，系统流畅,拍照好/性能强/外观漂亮,价格偏高/发热较明显,2024-02-01,45,是,VIP会员,拍照/性能/外观
```

## 🛠️ 快速开始

### 1. 准备数据文件
```bash
# 创建数据目录
mkdir -p data/ecommerce

# 将您的CSV文件复制到该目录
cp your_products.csv data/ecommerce/products.csv
cp your_specifications.csv data/ecommerce/specifications.csv
cp your_price_history.csv data/ecommerce/price_history.csv
cp your_reviews.csv data/ecommerce/reviews.csv
```

### 2. 生成示例数据（可选）
如果您需要示例数据进行测试：
```bash
cd /Users/xinyizhu/Downloads/cc-mirror/llm-agent
python scripts/generate_sample_ecommerce_data.py
```

### 3. 初始化知识库
```bash
# 完整初始化（创建数据库表 + 生成示例数据 + 构建知识库）
python scripts/init_ecommerce_rag.py --action all

# 或分步执行：
# 创建数据库表
python scripts/init_ecommerce_rag.py --action init

# 构建知识库
python scripts/init_ecommerce_rag.py --action build

# 测试功能
python scripts/init_ecommerce_rag.py --action test
```

### 4. 验证部署
检查API是否正常工作：
```bash
# 测试商品搜索
curl -X POST "http://localhost:8001/api/ecommerce/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone 15", "page": 1, "page_size": 5}'

# 测试知识库搜索
curl -X POST "http://localhost:8001/api/ecommerce/knowledge-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone 15 Pro的价格分析", "k": 3}'
```

## 🔧 配置说明

### 环境变量
在 `.env` 文件中添加以下配置：
```env
# 数据目录
ECOMMERCE_DATA_DIR=data/ecommerce

# 向量存储路径
ECOMMERCE_VECTOR_STORE_PATH=vector_store/ecommerce_knowledge

# 嵌入模型
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 数据库配置
电商数据会存储在SQLite数据库中，无需额外配置。

## 📚 API接口使用

### 1. 商品搜索
```python
import requests

# 商品搜索
response = requests.post("http://localhost:8001/api/ecommerce/search", json={
    "query": "iPhone 15 Pro",
    "category": "智能手机",
    "min_price": 5000,
    "max_price": 10000,
    "page": 1,
    "page_size": 10
})

print(response.json())
```

### 2. 商品推荐
```python
# 获取个性化推荐
response = requests.post("http://localhost:8001/api/ecommerce/recommendations", json={
    "query": "适合学生用的笔记本电脑",
    "budget": 6000,
    "preferences": {
        "brand": "Xiaomi",
        "category": "笔记本电脑"
    },
    "limit": 5
})
```

### 3. 知识库搜索
```python
# 搜索相关知识
response = requests.post("http://localhost:8001/api/ecommerce/knowledge-search", json={
    "query": "iPhone 15 Pro的价格趋势如何",
    "k": 5,
    "filter_type": "price_analysis"
})
```

### 4. 商品洞察
```python
# 获取商品洞察信息
response = requests.post("http://localhost:8001/api/ecommerce/product-insights", json={
    "product_id": "iphone_15_pro_256"
})
```

### 5. 价格对比
```python
# 多平台价格对比
response = requests.get("http://localhost:8001/api/ecommerce/price-comparison", params={
    "product_name": "iPhone 15 Pro",
    "platforms": ["jd", "taobao", "pdd"]
})
```

## 🎯 功能特性

### 1. 智能搜索
- 支持自然语言查询
- 多维度过滤（类别、品牌、价格区间、平台）
- 相关性排序

### 2. 商品推荐
- 基于用户偏好的个性化推荐
- 预算约束的推荐优化
- 多目标推荐算法

### 3. 价格分析
- 历史价格趋势分析
- 价格波动检测
- 购买时机建议

### 4. 评价分析
- 用户情感分析
- 优缺点提取
- 推荐度计算

### 5. 市场分析
- 品牌市场份额
- 价格区间分布
- 热门商品排行

## 🔄 知识库更新

### 1. 添加新数据
```bash
# 将新的CSV文件放入data/ecommerce/目录
# 重新构建知识库
python scripts/init_ecommerce_rag.py --action build --rebuild
```

### 2. 通过API更新
```python
import requests

# 触发知识库更新
response = requests.post("http://localhost:8001/api/ecommerce/init-knowledge-base", json={
    "data_dir": "data/ecommerce",
    "rebuild": True
})
```

### 3. 定期更新
建议设置定时任务定期更新知识库：
```bash
# 添加到crontab
0 2 * * * cd /path/to/llm-agent && python scripts/init_ecommerce_rag.py --action build
```

## 📈 性能优化

### 1. 数据预处理
- 清理和标准化数据格式
- 处理缺失值和异常值
- 数据去重

### 2. 向量化优化
- 选择合适的嵌入模型
- 调整文档分块大小
- 优化向量存储

### 3. 查询优化
- 使用过滤器减少搜索范围
- 缓存常用查询结果
- 批量处理请求

## 🐛 故障排除

### 1. 常见问题

#### 数据加载失败
```bash
# 检查文件格式
file data/ecommerce/products.csv

# 检查文件编码
file -I data/ecommerce/products.csv
```

#### 知识库构建失败
```bash
# 检查依赖包
pip install langchain faiss-cpu sentence-transformers

# 检查磁盘空间
df -h
```

#### API调用失败
```bash
# 检查服务状态
curl http://localhost:8001/health

# 检查日志
tail -f logs/app.log
```

### 2. 调试模式
```bash
# 启用详细日志
export PYTHONPATH=/path/to/llm-agent
python scripts/init_ecommerce_rag.py --action test
```

## 🔒 安全考虑

### 1. 数据安全
- 不存储敏感用户信息
- 数据传输使用HTTPS
- 定期备份数据库

### 2. API安全
- 实现访问控制
- 限制请求频率
- 输入数据验证
