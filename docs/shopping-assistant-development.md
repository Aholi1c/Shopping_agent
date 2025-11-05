# 网购助手Agent开发文档

## 项目概述

基于现有的增强多模态LLM Agent框架，开发专门的网购助手Agent，集成商品信息检索、价格对比、优惠计算、用户偏好记忆、情感分析等功能，并新增图片识别和相似物品推荐功能。

## 1. 系统架构设计

### 1.1 整体架构

```
网购助手Agent架构
├── 基础框架层 (现有LLM Agent)
│   ├── FastAPI + SQLAlchemy
│   ├── WebSocket通信
│   ├── 多模态支持 (文本/图像/语音)
│   ├── 记忆系统
│   ├── RAG系统
│   └── 多Agent协作
├── 网购助手专用层
│   ├── 商品信息服务
│   ├── 价格对比引擎
│   ├── 优惠计算器
│   ├── 用户偏好管理
│   ├── 情感分析器
│   ├── 图片识别服务
│   └── 相似物品推荐
└── 数据层
    ├── 商品数据库
    ├── 用户偏好数据库
    ├── 价格历史数据库
    └── 图像特征数据库
```

### 1.2 核心模块

#### 1.2.1 商品信息检索模块
- 支持多平台商品信息抓取（京东、淘宝、拼多多、小红书、抖音）
- 商品参数结构化提取
- 实时价格监控
- 商品评价分析

#### 1.2.2 价格对比引擎
- 多平台价格实时对比
- 价格历史追踪
- 价格趋势预测
- 性价比评估

#### 1.2.3 优惠计算器
- 优惠券信息收集
- 优惠规则解析
- 叠加优惠策略
- 最佳购买时机推荐

#### 1.2.4 用户偏好记忆系统
- 购买历史分析
- 偏好特征提取
- 个性化推荐权重
- 长期偏好演化

#### 1.2.5 情感分析器
- 评论区真实性检测
- 软广识别算法
- 情感倾向分析
- 口碑质量评分

#### 1.2.6 图片识别服务
- 商品图像特征提取
- 多模态商品理解
- 视觉搜索支持
- 图像质量评估

#### 1.2.7 相似物品推荐
- 基于内容的相似度计算
- 视觉特征匹配
- 跨平台商品推荐
- 个性化相似度权重

## 2. 数据库设计扩展

### 2.1 商品相关表

```sql
-- 商品信息表
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,  -- 平台名称
    product_id VARCHAR(100) NOT NULL,  -- 平台商品ID
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10,2),
    original_price DECIMAL(10,2),
    discount_rate DECIMAL(5,2),
    image_url TEXT,
    product_url TEXT,
    rating DECIMAL(3,2),
    review_count INTEGER,
    sales_count INTEGER,
    stock_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, product_id)
);

-- 商品参数表
CREATE TABLE product_specs (
    id INTEGER PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    spec_name VARCHAR(100) NOT NULL,
    spec_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 价格历史表
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),
    discount_rate DECIMAL(5,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 商品评价表
CREATE TABLE product_reviews (
    id INTEGER PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    reviewer_name VARCHAR(100),
    rating DECIMAL(3,2),
    content TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    sentiment_score DECIMAL(5,2),
    authenticity_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 用户相关表

```sql
-- 用户偏好表
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    preference_type VARCHAR(50) NOT NULL,  -- 'category', 'brand', 'price_range', 'feature'
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    weight DECIMAL(5,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 购买历史表
CREATE TABLE purchase_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    purchase_price DECIMAL(10,2),
    purchase_date TIMESTAMP,
    satisfaction_rating DECIMAL(3,2),
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 搜索历史表
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    search_query TEXT NOT NULL,
    search_results_count INTEGER,
    click_through_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3 优惠相关表

```sql
-- 优惠券表
CREATE TABLE coupons (
    id INTEGER PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    coupon_id VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    discount_type VARCHAR(20),  -- 'fixed', 'percentage', 'cashback'
    discount_value DECIMAL(10,2),
    min_purchase_amount DECIMAL(10,2),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    terms TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, coupon_id)
);

-- 优惠券适用商品表
CREATE TABLE coupon_products (
    id INTEGER PRIMARY KEY,
    coupon_id INTEGER REFERENCES coupons(id),
    product_id INTEGER REFERENCES products(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 优惠策略表
CREATE TABLE coupon_strategies (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    strategy_data JSON,  -- 优惠券组合策略
    max_discount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.4 图像相关表

```sql
-- 商品图像表
CREATE TABLE product_images (
    id INTEGER PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    image_url TEXT NOT NULL,
    image_hash VARCHAR(64),
    features JSON,  -- 图像特征向量
    quality_score DECIMAL(5,2),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 图像相似度表
CREATE TABLE image_similarities (
    id INTEGER PRIMARY KEY,
    source_image_id INTEGER REFERENCES product_images(id),
    target_image_id INTEGER REFERENCES product_images(id),
    similarity_score DECIMAL(5,2),
    similarity_type VARCHAR(20),  -- 'visual', 'semantic', 'overall'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 以图搜图历史表
CREATE TABLE image_search_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query_image_url TEXT,
    search_results JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 3. API接口设计

### 3.1 商品信息接口

```python
# 商品搜索
@app.post("/api/shopping/search")
async def search_products(
    query: str,
    platforms: List[str] = ["jd", "taobao", "pdd"],
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    sort_by: str = "relevance",
    page: int = 1,
    page_size: int = 20
):
    """多平台商品搜索"""
    pass

# 商品详情
@app.get("/api/shopping/products/{product_id}")
async def get_product_details(product_id: str, platform: str):
    """获取商品详细信息"""
    pass

# 商品参数对比
@app.post("/api/shopping/compare")
async def compare_products(
    product_ids: List[str],
    platform: str,
    specs_only: bool = False
):
    """商品参数对比"""
    pass
```

### 3.2 价格对比接口

```python
# 价格历史
@app.get("/api/shopping/products/{product_id}/price-history")
async def get_price_history(
    product_id: str,
    platform: str,
    days: int = 30
):
    """获取价格历史"""
    pass

# 多平台价格对比
@app.post("/api/shopping/price-comparison")
async def compare_prices(
    query: str,
    platforms: List[str] = ["jd", "taobao", "pdd"]
):
    """多平台价格对比"""
    pass

# 价格趋势预测
@app.get("/api/shopping/products/{product_id}/price-trend")
async def get_price_trend(product_id: str, platform: str):
    """价格趋势预测"""
    pass
```

### 3.3 优惠计算接口

```python
# 优惠券查询
@app.get("/api/shopping/coupons")
async def get_coupons(
    product_id: Optional[str] = None,
    platform: Optional[str] = None,
    user_id: Optional[int] = None
):
    """查询可用优惠券"""
    pass

# 最佳优惠策略
@app.post("/api/shopping/best-deal")
async def get_best_deal(
    product_id: str,
    platform: str,
    user_id: Optional[int] = None,
    quantity: int = 1
):
    """计算最佳优惠策略"""
    pass

# 优惠券叠加计算
@app.post("/api/shopping/coupon-stacking")
async def calculate_coupon_stacking(
    product_ids: List[str],
    platform: str,
    coupon_ids: List[str]
):
    """优惠券叠加计算"""
    pass
```

### 3.4 图片识别接口

```python
# 商品图片识别
@app.post("/api/shopping/image-recognition")
async def recognize_product_image(
    image_file: UploadFile = File(...),
    platform: str = "multi"
):
    """商品图片识别"""
    pass

# 以图搜图
@app.post("/api/shopping/image-search")
async def search_by_image(
    image_file: UploadFile = File(...),
    platforms: List[str] = ["jd", "taobao", "pdd"],
    similarity_threshold: float = 0.7
):
    """以图搜图"""
    pass

# 相似商品推荐
@app.get("/api/shopping/products/{product_id}/similar")
async def get_similar_products(
    product_id: str,
    platform: str,
    limit: int = 10,
    include_visual: bool = True
):
    """相似商品推荐"""
    pass
```

### 3.5 用户偏好接口

```python
# 用户偏好更新
@app.post("/api/shopping/preferences/update")
async def update_user_preferences(
    user_id: int,
    preference_type: str,
    preference_data: Dict
):
    """更新用户偏好"""
    pass

# 个性化推荐
@app.get("/api/shopping/recommendations")
async def get_recommendations(
    user_id: int,
    category: Optional[str] = None,
    limit: int = 20
):
    """个性化推荐"""
    pass

# 购买历史分析
@app.get("/api/shopping/users/{user_id}/purchase-analysis")
async def get_purchase_analysis(user_id: int):
    """购买历史分析"""
    pass
```

## 4. 服务层实现

### 4.1 商品信息服务

```python
# services/shopping_service.py
class ShoppingService:
    def __init__(self, db: Session, llm_service, memory_service):
        self.db = db
        self.llm_service = llm_service
        self.memory_service = memory_service

    async def search_products(self, query: str, platforms: List[str]):
        """多平台商品搜索"""
        # 1. 使用LLM理解搜索意图
        intent = await self.llm_service.understand_search_intent(query)

        # 2. 并行搜索多个平台
        search_tasks = []
        for platform in platforms:
            task = self._search_platform(platform, query, intent)
            search_tasks.append(task)

        results = await asyncio.gather(*search_tasks)

        # 3. 结果排序和去重
        processed_results = self._process_search_results(results)

        # 4. 记录搜索历史
        await self._record_search_history(query, len(processed_results))

        return processed_results

    async def _search_platform(self, platform: str, query: str, intent: Dict):
        """单个平台搜索"""
        # 实现各个平台的搜索逻辑
        pass

    def _process_search_results(self, results: List[Dict]):
        """处理搜索结果"""
        # 去重、排序、评分
        pass
```

### 4.2 图片识别服务

```python
# services/image_service.py
class ImageService:
    def __init__(self, db: Session, vision_model):
        self.db = db
        self.vision_model = vision_model

    async def recognize_product(self, image_path: str):
        """商品图片识别"""
        # 1. 图像预处理
        processed_image = self._preprocess_image(image_path)

        # 2. 视觉特征提取
        visual_features = await self._extract_visual_features(processed_image)

        # 3. 商品识别
        product_info = await self._identify_product(visual_features)

        # 4. 相似商品搜索
        similar_products = await self._find_similar_products(visual_features)

        return {
            "product_info": product_info,
            "similar_products": similar_products,
            "confidence": product_info.get("confidence", 0)
        }

    async def _extract_visual_features(self, image):
        """提取视觉特征"""
        # 使用视觉模型提取特征
        pass

    async def _find_similar_products(self, features: List[float]):
        """查找相似商品"""
        # 向量搜索相似商品
        pass
```

### 4.3 价格监控服务

```python
# services/price_service.py
class PriceService:
    def __init__(self, db: Session):
        self.db = db

    async def track_price_changes(self, product_id: str, platform: str):
        """价格变化追踪"""
        # 1. 获取当前价格
        current_price = await self._get_current_price(product_id, platform)

        # 2. 记录价格历史
        await self._record_price_history(product_id, platform, current_price)

        # 3. 价格变化分析
        price_analysis = self._analyze_price_change(product_id, platform)

        # 4. 价格趋势预测
        trend_prediction = await self._predict_price_trend(product_id, platform)

        return {
            "current_price": current_price,
            "analysis": price_analysis,
            "trend": trend_prediction
        }

    async def _predict_price_trend(self, product_id: str, platform: str):
        """价格趋势预测"""
        # 使用机器学习模型预测价格趋势
        pass
```

### 4.4 优惠计算服务

```python
# services/coupon_service.py
class CouponService:
    def __init__(self, db: Session):
        self.db = db

    async def calculate_best_deal(self, product_id: str, user_id: Optional[int] = None):
        """计算最佳优惠"""
        # 1. 获取商品信息
        product = await self._get_product(product_id)

        # 2. 获取可用优惠券
        available_coupons = await self._get_available_coupons(product_id, user_id)

        # 3. 计算最优组合
        best_combination = self._find_best_combination(product, available_coupons)

        # 4. 生成购买建议
        purchase_suggestion = self._generate_suggestion(product, best_combination)

        return purchase_suggestion

    def _find_best_combination(self, product: Dict, coupons: List[Dict]):
        """寻找最优优惠券组合"""
        # 动态规划算法求解最优组合
        pass
```

## 5. 前端界面设计

### 5.1 购物助手主界面

```typescript
// components/ShoppingAssistant.tsx
const ShoppingAssistant: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Product[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const results = await shoppingService.searchProducts(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleImageSearch = async (imageFile: File) => {
    setLoading(true);
    try {
      const results = await shoppingService.searchByImage(imageFile);
      setSearchResults(results);
    } catch (error) {
      console.error('Image search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="shopping-assistant">
      <div className="search-section">
        <div className="text-search">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索商品..."
          />
          <button onClick={handleSearch}>搜索</button>
        </div>
        <div className="image-search">
          <ImageUpload onUpload={handleImageSearch} />
        </div>
      </div>

      <div className="results-section">
        {loading ? (
          <Spinner />
        ) : (
          <ProductList
            products={searchResults}
            onSelect={setSelectedProducts}
            selectedProducts={selectedProducts}
          />
        )}
      </div>

      <div className="comparison-section">
        {selectedProducts.length > 0 && (
          <ProductComparison products={selectedProducts} />
        )}
      </div>
    </div>
  );
};
```

### 5.2 商品详情界面

```typescript
// components/ProductDetail.tsx
const ProductDetail: React.FC<{ product: Product }> = ({ product }) => {
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [similarProducts, setSimilarProducts] = useState<Product[]>([]);

  useEffect(() => {
    loadProductData();
  }, [product.id]);

  const loadProductData = async () => {
    const [history, availableCoupons, similar] = await Promise.all([
      shoppingService.getPriceHistory(product.id),
      shoppingService.getCoupons(product.id),
      shoppingService.getSimilarProducts(product.id)
    ]);

    setPriceHistory(history);
    setCoupons(availableCoupons);
    setSimilarProducts(similar);
  };

  return (
    <div className="product-detail">
      <div className="product-header">
        <img src={product.imageUrl} alt={product.title} />
        <div className="product-info">
          <h1>{product.title}</h1>
          <div className="price-section">
            <span className="current-price">¥{product.price}</span>
            <span className="original-price">¥{product.originalPrice}</span>
          </div>
        </div>
      </div>

      <div className="price-history">
        <h2>价格走势</h2>
        <PriceChart data={priceHistory} />
      </div>

      <div className="coupons-section">
        <h2>可用优惠券</h2>
        <CouponList coupons={coupons} />
      </div>

      <div className="similar-products">
        <h2>相似商品</h2>
        <ProductGrid products={similarProducts} />
      </div>
    </div>
  );
};
```

## 6. 核心算法实现

### 6.1 商品相似度算法

```python
# algorithms/similarity.py
class ProductSimilarity:
    def __init__(self):
        self.visual_weight = 0.4
        self.semantic_weight = 0.3
        self.attribute_weight = 0.3

    def calculate_similarity(self, product1: Dict, product2: Dict) -> float:
        """计算商品相似度"""
        # 1. 视觉相似度
        visual_sim = self._calculate_visual_similarity(product1, product2)

        # 2. 语义相似度
        semantic_sim = self._calculate_semantic_similarity(product1, product2)

        # 3. 属性相似度
        attribute_sim = self._calculate_attribute_similarity(product1, product2)

        # 4. 综合相似度
        total_similarity = (
            self.visual_weight * visual_sim +
            self.semantic_weight * semantic_sim +
            self.attribute_weight * attribute_sim
        )

        return total_similarity

    def _calculate_visual_similarity(self, product1: Dict, product2: Dict) -> float:
        """计算视觉相似度"""
        if 'image_features' not in product1 or 'image_features' not in product2:
            return 0.0

        features1 = np.array(product1['image_features'])
        features2 = np.array(product2['image_features'])

        # 余弦相似度
        cosine_sim = np.dot(features1, features2) / (
            np.linalg.norm(features1) * np.linalg.norm(features2)
        )

        return cosine_sim
```

### 6.2 情感分析算法

```python
# algorithms/sentiment_analysis.py
class ReviewSentimentAnalyzer:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    async def analyze_review_authenticity(self, review: Dict) -> Dict:
        """分析评论真实性"""
        # 1. 文本特征分析
        text_features = self._extract_text_features(review['content'])

        # 2. 用户行为分析
        user_features = await self._analyze_user_behavior(review['user_id'])

        # 3. 使用LLM进行深度分析
        llm_analysis = await self.llm_service.analyze_review(review)

        # 4. 综合评分
        authenticity_score = self._calculate_authenticity_score(
            text_features, user_features, llm_analysis
        )

        return {
            'authenticity_score': authenticity_score,
            'is_genuine': authenticity_score > 0.7,
            'confidence': llm_analysis.get('confidence', 0),
            'reasons': llm_analysis.get('reasons', [])
        }

    def _extract_text_features(self, text: str) -> Dict:
        """提取文本特征"""
        # 实现文本特征提取
        pass
```

### 6.3 个性化推荐算法

```python
# algorithms/recommendation.py
class PersonalizedRecommender:
    def __init__(self, db: Session, memory_service):
        self.db = db
        self.memory_service = memory_service

    async def get_recommendations(self, user_id: int, limit: int = 20) -> List[Dict]:
        """个性化推荐"""
        # 1. 获取用户偏好
        user_preferences = await self._get_user_preferences(user_id)

        # 2. 获取购买历史
        purchase_history = await self._get_purchase_history(user_id)

        # 3. 获取浏览历史
        browsing_history = await self._get_browsing_history(user_id)

        # 4. 生成候选商品
        candidate_products = await self._generate_candidates(user_preferences)

        # 5. 排序和筛选
        recommendations = self._rank_candidates(
            candidate_products, user_preferences, purchase_history, browsing_history
        )

        return recommendations[:limit]

    def _rank_candidates(self, candidates: List[Dict], preferences: Dict,
                        purchase_history: List[Dict], browsing_history: List[Dict]) -> List[Dict]:
        """候选商品排序"""
        # 实现排序算法
        pass
```

## 7. 部署和配置

### 7.1 环境配置

```bash
# backend/.env
# 现有配置保持不变

# 网购助手相关配置
SHOPPING_PLATFORMS=jd,taobao,pdd,xiaohongshu,douyin
ENABLE_PRICE_MONITORING=true
ENABLE_IMAGE_RECOGNITION=true
IMAGE_RECOGNITION_MODEL=glm-4v
SIMILARITY_THRESHOLD=0.7

# 第三方API配置
JD_API_KEY=your_jd_api_key
TAOBAO_API_KEY=your_taobao_api_key
PDD_API_KEY=your_pdd_api_key

# Redis配置（用于缓存）
REDIS_URL=redis://localhost:6379/1
```

### 7.2 依赖包

```bash
# backend/requirements.txt
# 现有依赖保持不变

# 网购助手相关依赖
requests>=2.31.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
pillow>=10.0.0
opencv-python>=4.8.0
scikit-learn>=1.3.0
pandas>=2.1.0
numpy>=1.24.0
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.35.0
```

### 7.3 启动脚本

```bash
#!/bin/bash
# scripts/start_shopping_assistant.sh

echo "启动网购助手服务..."

# 启动后端服务
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端服务
cd ../frontend
npm start &
FRONTEND_PID=$!

# 启动价格监控服务
cd ../backend
python -m services.price_monitor &
PRICE_PID=$!

echo "服务启动完成"
echo "后端服务PID: $BACKEND_PID"
echo "前端服务PID: $FRONTEND_PID"
echo "价格监控PID: $PRICE_PID"

# 保存PID
echo $BACKEND_PID > ../backend.pid
echo $FRONTEND_PID > ../frontend.pid
echo $PRICE_PID > ../price_monitor.pid
```

## 8. 测试计划

### 8.1 单元测试

```python
# tests/test_shopping_service.py
import pytest
from app.services.shopping_service import ShoppingService

@pytest.fixture
def shopping_service(db_session):
    return ShoppingService(db_session, mock_llm_service, mock_memory_service)

@pytest.mark.asyncio
async def test_search_products(shopping_service):
    """测试商品搜索"""
    results = await shopping_service.search_products(
        query="iPhone 15",
        platforms=["jd", "taobao"]
    )

    assert len(results) > 0
    assert all('title' in product for product in results)
    assert all('price' in product for product in results)

@pytest.mark.asyncio
async def test_price_comparison(shopping_service):
    """测试价格对比"""
    comparison = await shopping_service.compare_prices(
        query="iPhone 15",
        platforms=["jd", "taobao"]
    )

    assert 'jd' in comparison
    assert 'taobao' in comparison
    assert 'lowest_price' in comparison
```

### 8.2 集成测试

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_full_shopping_workflow():
    """测试完整购物流程"""
    # 1. 搜索商品
    search_results = await shopping_service.search_products("iPhone 15")

    # 2. 选择商品进行对比
    product_ids = [result['id'] for result in search_results[:3]]
    comparison = await shopping_service.compare_products(product_ids)

    # 3. 获取价格历史
    price_history = await shopping_service.get_price_history(product_ids[0])

    # 4. 计算最佳优惠
    best_deal = await coupon_service.get_best_deal(product_ids[0])

    # 5. 获取相似商品
    similar_products = await shopping_service.get_similar_products(product_ids[0])

    # 验证流程完整性
    assert len(search_results) > 0
    assert len(comparison) == 3
    assert len(price_history) > 0
    assert 'max_discount' in best_deal
    assert len(similar_products) > 0
```

### 8.3 性能测试

```python
# tests/test_performance.py
import asyncio
import time

@pytest.mark.asyncio
async def test_concurrent_searches():
    """测试并发搜索性能"""
    start_time = time.time()

    # 并发执行10个搜索请求
    tasks = []
    for i in range(10):
        task = shopping_service.search_products(f"product_{i}")
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time

    # 验证性能指标
    assert total_time < 10  # 10秒内完成10个请求
    assert all(len(result) > 0 for result in results)
```

## 9. 监控和维护

### 9.1 性能监控

```python
# monitoring/performance_monitor.py
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}

    async def track_request(self, endpoint: str, duration: float):
        """追踪请求性能"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = []

        self.metrics[endpoint].append({
            'timestamp': datetime.now(),
            'duration': duration
        })

        # 记录到日志
        logger.info(f"Request to {endpoint} took {duration:.2f}s")

    def get_performance_stats(self, endpoint: str) -> Dict:
        """获取性能统计"""
        if endpoint not in self.metrics:
            return {}

        durations = [m['duration'] for m in self.metrics[endpoint]]

        return {
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'request_count': len(durations),
            'p95_duration': sorted(durations)[int(len(durations) * 0.95)]
        }
```

### 9.2 错误监控

```python
# monitoring/error_monitor.py
class ErrorMonitor:
    def __init__(self):
        self.errors = []

    def log_error(self, error: Exception, context: Dict):
        """记录错误"""
        error_info = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'stack_trace': traceback.format_exc()
        }

        self.errors.append(error_info)
        logger.error(f"Error occurred: {error_info}")

        # 发送告警
        self._send_alert(error_info)

    def _send_alert(self, error_info: Dict):
        """发送告警"""
        # 实现告警逻辑
        pass
```

## 10. 扩展计划

### 10.1 短期扩展（1-2个月）

1. **多平台支持扩展**
   - 增加更多电商平台支持
   - 优化现有平台的数据抓取
   - 增加跨境购物平台

2. **图片识别能力提升**
   - 增加商品细节识别
   - 支持多角度商品匹配
   - 提高图像搜索准确率

3. **用户体验优化**
   - 优化搜索结果展示
   - 增加筛选和排序功能
   - 改进移动端体验

### 10.2 中期扩展（3-6个月）

1. **智能推荐系统**
   - 基于深度学习的推荐算法
   - 实时个性化推荐
   - 社交化推荐功能

2. **价格预测系统**
   - 基于历史数据的价格预测
   - 季节性价格波动分析
   - 最佳购买时机推荐

3. **购物决策支持**
   - 购物清单智能管理
   - 预算规划和建议
   - 购物决策树生成

### 10.3 长期扩展（6个月以上）

1. **多语言支持**
   - 支持国际购物平台
   - 多语言商品信息翻译
   - 跨境购物助手

2. **AR/VR购物体验**
   - AR商品试穿/试用
   - VR购物场景体验
   - 3D商品展示

3. **区块链集成**
   - 商品溯源验证
   - 智能合约优惠
   - 去中心化购物评价

## 11. 总结

本开发文档详细介绍了基于现有LLM Agent框架构建网购助手Agent的完整方案。通过充分利用现有框架的多模态能力、记忆系统和RAG功能，结合专业的商品信息检索、价格对比、优惠计算等模块，打造了一个功能强大的智能购物助手。

主要特点：

1. **技术先进性**：基于最新的多模态LLM技术，支持文本、图像、语音交互
2. **功能完整性**：涵盖购物的各个环节，从搜索到决策支持
3. **个性化推荐**：基于用户偏好的智能推荐系统
4. **实时监控**：价格变化实时监控和趋势预测
5. **可扩展性**：模块化设计，易于功能扩展和维护

该系统将为用户提供全方位的购物辅助服务，显著提升网购体验和决策效率。