# 🛍️ 智能购物助手使用指南

## 概述

智能购物助手是一个基于最新UI设计的现代化购物辅助系统，集成了多模态交互、智能推荐和专业的购物决策工具。全新的界面设计提供流畅的用户体验和强大的功能支持。

## 功能特性

### 🛍️ 核心功能

1. **多平台商品搜索**
   - 支持京东、淘宝、拼多多、小红书、抖音等主流电商平台
   - 实时价格对比和商品信息整合
   - 智能搜索意图理解

2. **图片识别与搜索**
   - 商品图片智能识别
   - 以图搜图功能
   - 相似商品推荐

3. **价格监控与对比**
   - 多平台价格实时对比
   - 价格历史追踪
   - 价格趋势预测

4. **优惠计算策略**
   - 智能优惠券匹配
   - 最优优惠组合计算
   - 节省金额最大化

5. **个性化推荐**
   - 基于用户偏好的智能推荐
   - 购买历史分析
   - 兴趣偏好学习

## 🎨 全新界面设计 (v2.2.0)

### 界面布局

#### 顶部导航栏
- **Logo和品牌**: 显示智能购物助手品牌标识
- **智能搜索**: 集成搜索框，支持商品、品牌、类别搜索
- **快捷操作**: 图片分析、语音输入、购物车快捷入口
- **购物车**: 实时显示购物车商品数量和状态
- **用户菜单**: 个人中心、设置、退出登录

#### 左侧智能推荐区
- **可折叠设计**: 点击可收起/展开侧边栏
- **商品推荐**: 基于AI算法的个性化商品推荐
- **热门搜索**: 当前热门搜索关键词标签
- **快捷分类**: 商品分类快速导航

#### 主对话区域
- **多模态输入**: 支持文本、图片、语音多种输入方式
- **实时对话**: 流畅的聊天界面，支持历史记录
- **商品卡片**: 在对话中展示商品信息卡片
- **快捷操作**: 复制、点赞、收藏等快捷功能

#### 底部信息栏
- **系统状态**: 显示在线状态和连接信息
- **帮助链接**: 使用帮助、隐私政策等快速入口
- **版权信息**: 系统版本和版权信息

### 交互特性

#### 多模态交互
1. **文本对话**
   - 自然语言购物咨询
   - 智能意图识别
   - 上下文理解

2. **图片识别**
   - 拍照识商品
   - 以图搜图功能
   - 商品图片分析

3. **语音输入**
   - 语音转文字
   - 实时语音识别
   - 多语言支持

#### 视觉效果
- **渐变配色**: 蓝紫色渐变主题，专业美观
- **流畅动画**: 打字指示器、悬浮效果、过渡动画
- **响应式设计**: 完美适配桌面端和移动端设备
- **深色模式**: 支持明暗主题切换

### 用户体验优化

#### 智能功能
- **自动补全**: 搜索框智能提示和自动补全
- **实时反馈**: 操作结果实时反馈和状态提示
- **快捷键**: 支持键盘快捷键操作
- **无障碍**: 支持屏幕阅读器和键盘导航

#### 性能优化
- **懒加载**: 组件懒加载，提升首屏加载速度
- **缓存策略**: 智能缓存，减少重复请求
- **离线支持**: 部分功能支持离线使用
- **错误恢复**: 优雅的错误处理和恢复机制

## 安装和配置

### 1. 环境要求

- Python 3.8+
- Node.js 16+
- Redis (可选，用于缓存)

### 2. 依赖安装

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 3. 数据库初始化

```bash
# 运行初始化脚本
python scripts/init_shopping_assistant.py
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并配置相关参数：

```bash
# 必填配置
LLM_PROVIDER=bigmodel
BIGMODEL_API_KEY=your_bigmodel_api_key
BIGMODEL_VLM_API_KEY=your_bigmodel_vlm_api_key

# 可选配置（第三方平台API）
JD_API_KEY=your_jd_api_key
JD_API_SECRET=your_jd_api_secret
TAOBAO_API_KEY=your_taobao_api_key
TAOBAO_API_SECRET=your_taobao_api_secret
PDD_API_KEY=your_pdd_api_key
PDD_API_SECRET=your_pdd_api_secret
```

### 5. 启动服务

```bash
# 启动后端服务
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端服务
cd frontend
npm start
```

## 使用说明

### 1. 界面切换

应用主界面有两个主要功能模块：

- **💬 智能对话**: 原有的多模态对话功能
- **🛍️ 购物助手**: 新增的购物辅助功能

### 2. 商品搜索

1. 在购物助手界面，选择要搜索的平台（京东、淘宝、拼多多等）
2. 输入商品关键词（如"iPhone 15"、"华为手机"等）
3. 点击搜索按钮
4. 查看搜索结果，包括价格、评分、评论数等信息

### 3. 图片识别

1. 切换到"图片识别"标签页
2. 输入商品图片URL
3. 点击"识别商品"进行商品识别
4. 点击"以图搜图"查找相似商品
5. 查看识别结果和相似商品推荐

### 4. 价格对比

1. 切换到"价格对比"标签页
2. 输入商品名称
3. 选择要对比的平台
4. 点击"价格对比"查看各平台价格差异
5. 查看最优价格和节省建议

### 5. 优惠计算

1. 在搜索结果中选择感兴趣的商品
2. 切换到"优惠计算"标签页
3. 查看已选择的商品
4. 点击"计算最佳优惠"获取最优购买方案

## API 接口说明

### 商品搜索相关

```bash
# 商品搜索
POST /api/shopping/search
Content-Type: application/json

{
  "query": "iPhone 15",
  "platforms": ["jd", "taobao", "pdd"],
  "page": 1,
  "page_size": 20
}

# 商品详情
GET /api/shopping/products/{product_id}

# 价格历史
GET /api/shopping/products/{product_id}/price-history?days=30

# 商品对比
POST /api/shopping/compare
Content-Type: application/json

{
  "product_ids": [1, 2, 3]
}
```

### 图片识别相关

```bash
# 图片识别
POST /api/shopping/image-recognition
Content-Type: application/json

{
  "image_url": "https://example.com/product.jpg"
}

# 以图搜图
POST /api/shopping/image-search
Content-Type: application/json

{
  "image_url": "https://example.com/product.jpg",
  "platforms": ["jd", "taobao"],
  "similarity_threshold": 0.7,
  "limit": 10
}

# 相似商品
GET /api/shopping/products/{product_id}/similar?platform=jd&limit=10
```

### 价格和优惠相关

```bash
# 价格对比
POST /api/shopping/price-comparison
Content-Type: application/json

{
  "query": "iPhone 15",
  "platforms": ["jd", "taobao", "pdd"]
}

# 最佳优惠
POST /api/shopping/best-deal
Content-Type: application/json

{
  "product_id": 1,
  "user_id": 1,
  "quantity": 1
}

# 优惠券查询
GET /api/shopping/coupons?platform=jd
```

### 个性化推荐相关

```bash
# 用户推荐
GET /api/shopping/recommendations?user_id=1&limit=20

# 购买分析
GET /api/shopping/users/{user_id}/purchase-analysis?days=30

# 优惠券统计
GET /api/shopping/users/{user_id}/coupon-statistics

# 价格提醒
GET /api/shopping/users/{user_id}/price-alerts?threshold_percent=10
```

## 数据模型

### 商品相关表

- `products`: 商品基本信息
- `product_specs`: 商品规格参数
- `price_history`: 价格历史记录
- `product_reviews`: 商品评价
- `product_images`: 商品图片

### 用户相关表

- `user_preferences`: 用户偏好设置
- `purchase_history`: 购买历史
- `search_history`: 搜索历史

### 优惠相关表

- `coupons`: 优惠券信息
- `coupon_products`: 优惠券适用商品
- `coupon_strategies`: 优惠策略

### 图像相关表

- `image_search_history`: 图片搜索历史
- `image_similarities`: 图像相似度记录

## 扩展开发

### 添加新的电商平台

1. 在 `PlatformType` 枚举中添加新平台
2. 在 `shopping_service.py` 中实现平台API调用
3. 更新前端界面显示新平台选项

### 自定义图片特征提取

1. 修改 `image_service.py` 中的 `_extract_simple_features` 方法
2. 集成更先进的CNN模型（如ResNet、VGG等）
3. 更新相似度计算算法

### 优化推荐算法

1. 修改 `shopping_service.py` 中的推荐逻辑
2. 集成机器学习模型
3. 添加更多用户行为特征

## 故障排除

### 常见问题

1. **图片识别失败**
   - 检查图片URL是否可访问
   - 确认图片格式支持（jpg、png、webp）
   - 检查VLM模型配置

2. **搜索结果为空**
   - 检查第三方平台API配置
   - 确认网络连接正常
   - 尝试更换搜索关键词

3. **价格对比不准确**
   - 检查平台API数据更新频率
   - 确认价格数据同步状态

4. **优惠计算错误**
   - 检查优惠券配置
   - 确认优惠规则设置

### 日志查看

```bash
# 查看后端日志
tail -f logs/app.log

# 查看数据库操作日志
tail -f logs/db.log
```

## 性能优化

### 缓存策略

- Redis缓存热门商品信息
- CDN加速图片加载
- 搜索结果缓存

### 数据库优化

- 添加适当的索引
- 使用数据库连接池
- 定期清理历史数据

### 前端优化

- 图片懒加载
- 分页加载
- 组件按需加载

## 安全考虑

1. **API密钥安全**
   - 不要在前端代码中暴露API密钥
   - 使用环境变量管理敏感信息

2. **用户数据保护**
   - 加密存储用户偏好数据
   - 匿名化处理用户行为数据

3. **图片上传安全**
   - 限制图片文件大小和格式
   - 扫描上传文件的恶意内容
