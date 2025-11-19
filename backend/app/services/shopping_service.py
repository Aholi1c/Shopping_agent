import asyncio
import aiohttp
import json
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from ..models.models import (
    Product, ProductSpec, PriceHistory, ProductReview,
    UserPreference, PurchaseHistory, SearchHistory,
    Coupon, CouponProduct, CouponStrategy,
    ProductImage, ImageSimilarity, ImageSearchHistory,
    User, Memory
)
from ..models.schemas import (
    ProductCreate, ProductSearchRequest, ProductResponse,
    PlatformType, DiscountType, SimilarityType,
    ImageRecognitionRequest, ImageSearchRequest,
    BestDealRequest, SimilarProductRequest,
    RecommendationRequest, PurchaseAnalysisRequest
)
from ..core.config import settings
from .llm_service import LLMService
from .memory_service import MemoryService
from .media_service import MediaService
from .web_scraper_service import web_scraper_service
from .fallback_data_service import fallback_data_service
from .onebound_api_client import onebound_api_client

logger = logging.getLogger(__name__)

class ShoppingService:
    def __init__(self, db: Session, llm_service: LLMService, memory_service: MemoryService, media_service: MediaService):
        self.db = db
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.media_service = media_service

        # 平台API配置
        self.platform_apis = {
            PlatformType.JD: {
                "base_url": "https://api.jd.com/routerjson",
                "app_key": settings.jd_api_key,
                "secret": settings.jd_api_secret
            },
            PlatformType.TAOBAO: {
                "base_url": "https://eco.taobao.com/router/rest",
                "app_key": settings.taobao_api_key,
                "secret": settings.taobao_api_secret
            },
            PlatformType.PDD: {
                "base_url": "https://api.pinduoduo.com/api/router",
                "app_key": settings.pdd_api_key,
                "secret": settings.pdd_api_secret
            }
        }

        # 启动网络爬虫服务
        self.web_scraper = web_scraper_service
        asyncio.create_task(self._initialize_scraper_service())
        
        # 万邦API客户端
        self.onebound_client = onebound_api_client

    async def _initialize_scraper_service(self):
        """初始化爬虫服务"""
        try:
            await self.web_scraper.start()
            logger.info("Web scraper service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize web scraper service: {e}")

    async def search_products(self, request: ProductSearchRequest, user_id: Optional[int] = None) -> Dict:
        """多平台商品搜索"""
        start_time = datetime.now()

        # 1. 使用LLM理解搜索意图
        intent = await self._understand_search_intent(request.query)

        # 2. 优先从数据库获取（如果数据库中有数据）
        platform_results = await self._search_database(request)
        db_product_count = sum(len(platform_products) for platform_products in platform_results.values())
        logger.info(f"数据库搜索结果: {db_product_count} 个商品")

        # 3. 如果数据库结果不足，尝试使用爬虫获取（可选，需要启用）
        if db_product_count < request.page_size and getattr(settings, 'enable_scraper', False):
            try:
                scraper_platforms = []
                platform_mapping = {
                    PlatformType.TAOBAO: 'taobao',
                }
                for platform in request.platforms:
                    if platform in platform_mapping:
                        scraper_platforms.append(platform_mapping[platform])
                
                if scraper_platforms:
                    logger.info(f"数据库结果不足，尝试使用爬虫获取更多数据...")
                    scraper_results = await self.web_scraper.search_products(
                        keyword=request.query,
                        platforms=scraper_platforms,
                        max_pages=min(request.page_size // 20 + 1, 3)
                    )
                    scraper_results_dict = await self._convert_scraper_results(scraper_results, intent)
                    # 合并爬虫结果
                    for platform, products in scraper_results_dict.items():
                        if platform not in platform_results:
                            platform_results[platform] = []
                        platform_results[platform].extend(products)
                    db_product_count = sum(len(platform_products) for platform_products in platform_results.values())
            except Exception as e:
                logger.warning(f"爬虫搜索失败: {e}，继续使用数据库数据")

        # 4. 如果数据库和爬虫结果不足，尝试使用万邦API（如果配置了）
        # 注意：如果用户只想使用静态数据库，可以不配置万邦API密钥
        if db_product_count < request.page_size and settings.onebound_api_key and settings.onebound_api_key != "test_api_key":
            # 优先使用万邦API搜索
            try:
                onebound_tasks = []
                for platform in request.platforms:
                    if platform == PlatformType.TAOBAO:
                        task = self._search_taobao({}, request.query, intent)
                        onebound_tasks.append((platform, task))
                
                if onebound_tasks:
                    # 并行执行万邦API搜索
                    results = await asyncio.gather(
                        *[task for _, task in onebound_tasks],
                        return_exceptions=True
                    )
                    
                    for i, (platform, _) in enumerate(onebound_tasks):
                        result = results[i]
                        if not isinstance(result, Exception) and result:
                            if platform not in platform_results:
                                platform_results[platform] = []
                            platform_results[platform].extend(result)
                            
            except Exception as e:
                logger.error(f"万邦API搜索异常: {e}")
            
            # 如果万邦API结果不足，尝试其他API
            if sum(len(platform_products) for platform_products in platform_results.values()) < 5:
                search_tasks = []
                for platform in request.platforms:
                    if platform in self.platform_apis:
                        task = self._search_platform(platform, request.query, intent)
                        search_tasks.append(task)

                if search_tasks:
                    results = await asyncio.gather(*search_tasks, return_exceptions=True)
                    api_results = {}
                    for i, result in enumerate(results):
                        if not isinstance(result, Exception):
                            platform = request.platforms[i]
                            api_results[platform] = result

                    # 合并结果
                    for platform, results in api_results.items():
                        if platform not in platform_results:
                            platform_results[platform] = []
                        platform_results[platform].extend(results)
            else:
                # 如果没有配置API，使用数据库搜索
                db_results = await self._search_database(request)
                platform_results.update(db_results)

        # 4. 如果所有来源都失败或结果不足，使用备用数据
        if not platform_results or sum(len(results) for results in platform_results.values()) < 3:
            logger.warning("所有数据源获取失败，使用备用数据源")
            fallback_products = fallback_data_service.get_fallback_products(
                request.query,
                count=request.page_size
            )
            if fallback_products:
                # 将备用数据添加到结果中
                platform_results['fallback'] = fallback_products
                logger.info(f"添加了 {len(fallback_products)} 个备用商品")

        # 5. 结果处理和排序
        processed_results = self._process_search_results(platform_results, request)

        # 6. 记录搜索历史
        if user_id:
            await self._record_search_history(user_id, request.query, len(processed_results))

        # 7. 更新用户偏好
        if user_id and intent.get('category'):
            await self._update_user_preferences(user_id, intent)

        search_time = (datetime.now() - start_time).total_seconds()

        return {
            "products": processed_results,
            "total_count": len(processed_results),
            "page": request.page,
            "page_size": request.page_size,
            "has_next": len(processed_results) >= request.page_size,
            "search_time": search_time
        }

    async def _understand_search_intent(self, query: str) -> Dict:
        """使用LLM理解搜索意图"""
        prompt = f"""
        分析以下搜索查询，提取关键信息：
        查询: {query}

        请返回JSON格式的分析结果，包含：
        1. 主要产品类型
        2. 品牌偏好
        3. 价格范围
        4. 关键特征
        5. 产品类别
        6. 搜索意图类型

        格式：
        {{
            "product_type": "...",
            "brand": "...",
            "price_range": {{"min": ..., "max": ...}},
            "key_features": ["...", "..."],
            "category": "...",
            "intent_type": "product_search/specification_comparison/price_comparison"
        }}
        """

        try:
            response = await self.llm_service.generate_response(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error understanding search intent: {e}")
            return {}

    async def _convert_scraper_results(self, scraper_results: Dict, intent: Dict) -> Dict:
        """转换爬虫结果为内部格式"""
        platform_mapping = {
            'taobao': PlatformType.TAOBAO,
        }

        converted_results = {}

        for scraper_platform, products in scraper_results.items():
            if scraper_platform in platform_mapping:
                internal_platform = platform_mapping[scraper_platform]
                converted_products = []

                for product in products:
                    # 转换为内部Product模型格式
                    converted_product = {
                        'platform': internal_platform,
                        'product_id': product.get('product_id', ''),
                        'title': product.get('title', ''),
                        'description': product.get('description', ''),
                        'category': intent.get('category', ''),
                        'brand': product.get('shop_name', ''),
                        'price': product.get('price', 0),
                        'original_price': product.get('original_price') or product.get('price', 0),
                        'discount_rate': 0,
                        'image_url': product.get('image_url', ''),
                        'product_url': product.get('product_url', ''),
                        'rating': 0,
                        'review_count': product.get('comment_count', 0),
                        'sales_count': product.get('sales_count', 0),
                        'stock_status': 'in_stock',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }

                    # 计算折扣率
                    if converted_product['original_price'] and converted_product['price']:
                        converted_product['discount_rate'] = (converted_product['original_price'] - converted_product['price']) / converted_product['original_price']

                    converted_products.append(converted_product)

                converted_results[internal_platform] = converted_products

        return converted_results

    async def _search_platform(self, platform: PlatformType, query: str, intent: Dict) -> List[Dict]:
        """单个平台搜索"""
        try:
            if platform not in self.platform_apis:
                return []

            api_config = self.platform_apis[platform]

            # 这里实现具体的平台API调用
            # 由于API密钥和具体实现因平台而异，这里提供框架
            if platform == PlatformType.JD:
                return await self._search_jd(api_config, query, intent)
            elif platform == PlatformType.TAOBAO:
                return await self._search_taobao(api_config, query, intent)
            elif platform == PlatformType.PDD:
                return await self._search_pdd(api_config, query, intent)

        except Exception as e:
            logger.error(f"Error searching {platform}: {e}")
            return []

    async def _search_jd(self, api_config: Dict, query: str, intent: Dict) -> List[Dict]:
        """京东搜索 - 使用万邦API"""
        try:
            # 使用万邦API搜索
            result = await self.onebound_client.search_products(
                query=query,
                platform="jd",
                page=1,
                page_size=20
            )
            
            if "error" in result:
                logger.warning(f"万邦API京东搜索失败: {result.get('error')}, 使用备用数据")
                return []
            
            # 转换万邦API结果格式
            products = []
            for product in result.get("products", []):
                products.append({
                    "platform": PlatformType.JD,
                    "product_id": product.get("product_id", ""),
                    "title": product.get("title", ""),
                    "price": product.get("price", 0),
                    "original_price": product.get("original_price", product.get("price", 0)),
                    "discount_rate": product.get("discount_rate", 0),
                    "rating": product.get("rating", 0),
                    "review_count": product.get("review_count", 0),
                    "sales_count": product.get("sales_count", 0),
                    "image_url": product.get("image_url", ""),
                    "product_url": product.get("product_url", ""),
                    "shop_name": product.get("shop_name", ""),
                    "category": product.get("category", ""),
                    "stock_status": product.get("stock_status", "in_stock")
                })
            
            logger.info(f"万邦API京东搜索成功，返回 {len(products)} 个商品")
            return products
            
        except Exception as e:
            logger.error(f"万邦API京东搜索异常: {e}")
            # 返回空列表，让系统回退到其他数据源
            return []

    async def _search_taobao(self, api_config: Dict, query: str, intent: Dict) -> List[Dict]:
        """淘宝搜索 - 使用万邦API"""
        try:
            logger.info(f"开始使用万邦API搜索淘宝商品: {query}")
            
            # 检查万邦API配置
            from ..core.config import settings
            if not settings.onebound_api_key or settings.onebound_api_key == "test_api_key":
                logger.warning("万邦API密钥未配置或使用测试key，功能可能受限")
            
            # 使用万邦API搜索
            result = await self.onebound_client.search_products(
                query=query,
                platform="taobao",
                page=1,
                page_size=20
            )
            
            logger.debug(f"万邦API返回结果: {result}")
            
            if "error" in result:
                error_msg = result.get('error', '未知错误')
                error_detail = result.get('detail', '')
                logger.warning(f"万邦API搜索失败: {error_msg}, 详情: {error_detail}")
                # 记录详细错误以便调试
                if error_detail:
                    logger.warning(f"万邦API错误详情: {error_detail[:500]}")
                return []
            
            # 转换万邦API结果格式
            products = []
            products_raw = result.get("products", [])
            
            if not products_raw:
                logger.warning(f"万邦API返回了结果但没有商品数据，原始结果: {result.keys() if isinstance(result, dict) else type(result)}")
                # 检查是否有其他格式的数据
                if "items" in result:
                    logger.info("发现items字段，尝试解析")
                    products_raw = result["items"]
            
            for product in products_raw:
                try:
                    products.append({
                        "platform": PlatformType.TAOBAO,
                        "product_id": product.get("product_id", ""),
                        "title": product.get("title", ""),
                        "price": product.get("price", 0),
                        "original_price": product.get("original_price", product.get("price", 0)),
                        "discount_rate": product.get("discount_rate", 0),
                        "rating": product.get("rating", 0),
                        "review_count": product.get("review_count", 0),
                        "sales_count": product.get("sales_count", 0),
                        "image_url": product.get("image_url", ""),
                        "product_url": product.get("product_url", ""),
                        "shop_name": product.get("shop_name", ""),
                        "category": product.get("category", ""),
                        "stock_status": product.get("stock_status", "in_stock")
                    })
                except Exception as e:
                    logger.warning(f"转换商品数据失败: {e}, 商品数据: {product}")
                    continue
            
            logger.info(f"万邦API搜索成功，返回 {len(products)} 个商品")
            if len(products) == 0:
                logger.warning(f"万邦API未返回商品，原始结果结构: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            
            return products
            
        except Exception as e:
            logger.error(f"万邦API搜索异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 返回空列表，让系统回退到其他数据源
            return []

    async def _search_pdd(self, api_config: Dict, query: str, intent: Dict) -> List[Dict]:
        """拼多多搜索 - 使用万邦API"""
        try:
            # 使用万邦API搜索
            result = await self.onebound_client.search_products(
                query=query,
                platform="pdd",
                page=1,
                page_size=20
            )
            
            if "error" in result:
                logger.warning(f"万邦API拼多多搜索失败: {result.get('error')}, 使用备用数据")
                return []
            
            # 转换万邦API结果格式
            products = []
            for product in result.get("products", []):
                products.append({
                    "platform": PlatformType.PDD,
                    "product_id": product.get("product_id", ""),
                    "title": product.get("title", ""),
                    "price": product.get("price", 0),
                    "original_price": product.get("original_price", product.get("price", 0)),
                    "discount_rate": product.get("discount_rate", 0),
                    "rating": product.get("rating", 0),
                    "review_count": product.get("review_count", 0),
                    "sales_count": product.get("sales_count", 0),
                    "image_url": product.get("image_url", ""),
                    "product_url": product.get("product_url", ""),
                    "shop_name": product.get("shop_name", ""),
                    "category": product.get("category", ""),
                    "stock_status": product.get("stock_status", "in_stock")
                })
            
            logger.info(f"万邦API拼多多搜索成功，返回 {len(products)} 个商品")
            return products
            
        except Exception as e:
            logger.error(f"万邦API拼多多搜索异常: {e}")
            # 返回空列表，让系统回退到其他数据源
            return []

    async def _search_database(self, request: ProductSearchRequest) -> Dict:
        """数据库搜索"""
        query = self.db.query(Product)

        # 应用过滤条件
        if request.platforms:
            query = query.filter(Product.platform.in_(request.platforms))

        if request.category:
            query = query.filter(Product.category == request.category)

        if request.price_min is not None:
            query = query.filter(Product.price >= request.price_min)

        if request.price_max is not None:
            query = query.filter(Product.price <= request.price_max)

        # 文本搜索
        if request.query:
            query = query.filter(
                or_(
                    Product.title.contains(request.query),
                    Product.description.contains(request.query)
                )
            )

        # 排序
        if request.sort_by == "price_asc":
            query = query.order_by(Product.price.asc())
        elif request.sort_by == "price_desc":
            query = query.order_by(Product.price.desc())
        elif request.sort_by == "rating":
            query = query.order_by(Product.rating.desc())
        elif request.sort_by == "sales":
            query = query.order_by(Product.sales_count.desc())
        else:  # relevance
            query = query.order_by(Product.created_at.desc())

        # 分页
        offset = (request.page - 1) * request.page_size
        products = query.offset(offset).limit(request.page_size).all()

        return {"database": [self._product_to_dict(p) for p in products]}

    def _process_search_results(self, platform_results: Dict, request: ProductSearchRequest) -> List[ProductResponse]:
        """处理搜索结果"""
        all_products = []

        # 合法的平台枚举值集合，用于规范化平台字符串
        valid_platform_values = {p.value for p in PlatformType}

        for platform_key, products in platform_results.items():
            # 规范化平台标识
            if isinstance(platform_key, PlatformType):
                platform_str = platform_key.value
            else:
                platform_str = str(platform_key)

            if platform_str not in valid_platform_values:
                # 对于备用数据等未知平台，统一归为 other
                platform_str = PlatformType.OTHER.value

            for product_data in products:
                # 模拟/备用数据(platform='mock')不写入数据库，避免唯一约束和字段不匹配问题
                if isinstance(product_data, dict) and product_data.get("platform") == "mock":
                    continue

                existing_product = self.db.query(Product).filter(
                    and_(
                        Product.platform == platform_str,
                        Product.product_id == product_data["product_id"]
                    )
                ).first()

                if existing_product:
                    # 更新现有产品信息
                    for key, value in product_data.items():
                        if hasattr(existing_product, key):
                            setattr(existing_product, key, value)
                    existing_product.updated_at = datetime.now()
                    product = existing_product
                else:
                    # 创建新产品
                    product_dict = {**product_data, "platform": platform_str}
                    product_dict.pop("shop_name", None)
                    product_dict.pop("search_keyword", None)
                    product_dict.pop("crawl_time", None)
                    product = Product(**product_dict)
                    self.db.add(product)

                all_products.append(product)

        self.db.commit()

        # 应用分页
        offset = (request.page - 1) * request.page_size
        paginated_products = all_products[offset:offset + request.page_size]

        return [ProductResponse.from_orm(p) for p in paginated_products]

    def _product_to_dict(self, product: Product) -> Dict:
        """产品对象转字典"""
        return {
            "id": product.id,
            "platform": product.platform,
            "product_id": product.product_id,
            "title": product.title,
            "description": product.description,
            "category": product.category,
            "brand": product.brand,
            "price": product.price,
            "original_price": product.original_price,
            "discount_rate": product.discount_rate,
            "image_url": product.image_url,
            "product_url": product.product_url,
            "rating": product.rating,
            "review_count": product.review_count,
            "sales_count": product.sales_count,
            "stock_status": product.stock_status,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        }

    async def _record_search_history(self, user_id: int, query: str, results_count: int):
        """记录搜索历史"""
        search_history = SearchHistory(
            user_id=user_id,
            search_query=query,
            search_results_count=results_count
        )
        self.db.add(search_history)
        self.db.commit()

    async def _update_user_preferences(self, user_id: int, intent: Dict):
        """更新用户偏好"""
        if intent.get('category'):
            # 更新类别偏好
            existing = self.db.query(UserPreference).filter(
                and_(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_type == "category",
                    UserPreference.preference_key == intent['category']
                )
            ).first()

            if existing:
                existing.weight = min(existing.weight + 0.1, 1.0)
                existing.updated_at = datetime.now()
            else:
                preference = UserPreference(
                    user_id=user_id,
                    preference_type="category",
                    preference_key=intent['category'],
                    preference_value=intent['category'],
                    weight=0.5
                )
                self.db.add(preference)

        if intent.get('brand'):
            # 更新品牌偏好
            existing = self.db.query(UserPreference).filter(
                and_(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_type == "brand",
                    UserPreference.preference_key == intent['brand']
                )
            ).first()

            if existing:
                existing.weight = min(existing.weight + 0.1, 1.0)
                existing.updated_at = datetime.now()
            else:
                preference = UserPreference(
                    user_id=user_id,
                    preference_type="brand",
                    preference_key=intent['brand'],
                    preference_value=intent['brand'],
                    weight=0.5
                )
                self.db.add(preference)

        self.db.commit()

    async def get_product_details(self, product_id: int) -> Optional[ProductResponse]:
        """获取商品详情"""
        # 首先从数据库获取
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            return ProductResponse.from_orm(product)

        # 如果数据库中没有，尝试使用万邦API获取
        try:
            # 从URL或ID中提取平台信息
            product_from_db = self.db.query(Product).filter(Product.id == product_id).first()
            if product_from_db:
                platform_mapping = {
                    PlatformType.JD: 'jd',
                    PlatformType.TAOBAO: 'taobao',
                    PlatformType.PDD: 'pdd'
                }
                scraper_platform = platform_mapping.get(product_from_db.platform)

                if scraper_platform:
                    # 优先使用万邦API获取商品详情
                    try:
                        logger.info(f"使用万邦API获取商品详情: {product_from_db.product_id} from {scraper_platform}")
                        onebound_details = await self.onebound_client.get_product_details(
                            product_id=product_from_db.product_id,
                            platform=scraper_platform
                        )
                        
                        if onebound_details and "error" not in onebound_details:
                            # 更新数据库中的商品信息
                            await self._update_product_from_onebound(product_from_db, onebound_details)
                            return ProductResponse.from_orm(product_from_db)
                    except Exception as e:
                        logger.warning(f"万邦API获取商品详情失败: {e}，尝试使用爬虫")
                    
                    # 如果万邦API失败，使用爬虫获取最新详情
                    logger.info(f"使用网络爬虫获取商品详情: {product_from_db.product_id} from {scraper_platform}")
                    scraper_details = await self.web_scraper.get_product_details(
                        product_id=product_from_db.product_id,
                        platform=scraper_platform,
                        force_refresh=True
                    )

                    if scraper_details:
                        # 更新数据库中的商品信息
                        await self._update_product_from_scraper(product_from_db, scraper_details)
                        return ProductResponse.from_orm(product_from_db)

        except Exception as e:
            logger.error(f"获取商品详情失败: {e}")

        return None

    async def _update_product_from_scraper(self, product: Product, scraper_details: Dict):
        """从爬虫数据更新商品信息"""
        try:
            # 更新基本信息
            if scraper_details.get('title'):
                product.title = scraper_details['title']
            if scraper_details.get('description'):
                product.description = scraper_details['description']
            if scraper_details.get('price'):
                product.price = scraper_details['price']
            if scraper_details.get('original_price'):
                product.original_price = scraper_details['original_price']

            # 更新其他字段
            for key, value in scraper_details.items():
                if hasattr(product, key) and value is not None:
                    setattr(product, key, value)

            product.updated_at = datetime.now()
            self.db.commit()

            logger.info(f"商品信息已更新: {product.id} - {product.title}")
        except Exception as e:
            logger.error(f"更新商品信息失败: {e}")
            self.db.rollback()
    
    async def _update_product_from_onebound(self, product: Product, onebound_details: Dict):
        """从万邦API数据更新商品信息"""
        try:
            # 更新基本信息
            if onebound_details.get('title'):
                product.title = onebound_details['title']
            if onebound_details.get('description'):
                product.description = onebound_details['description']
            if onebound_details.get('price'):
                product.price = float(onebound_details['price'])
            if onebound_details.get('original_price'):
                product.original_price = float(onebound_details['original_price'])
            if onebound_details.get('discount_rate'):
                product.discount_rate = float(onebound_details['discount_rate'])
            if onebound_details.get('image_url'):
                product.image_url = onebound_details['image_url']
            if onebound_details.get('product_url'):
                product.product_url = onebound_details['product_url']
            if onebound_details.get('rating'):
                product.rating = float(onebound_details['rating'])
            if onebound_details.get('review_count'):
                product.review_count = int(onebound_details['review_count'])
            if onebound_details.get('sales_count'):
                product.sales_count = int(onebound_details['sales_count'])
            if onebound_details.get('category'):
                product.category = onebound_details['category']
            if onebound_details.get('brand'):
                product.brand = onebound_details['brand']
            if onebound_details.get('stock_status'):
                product.stock_status = onebound_details['stock_status']

            product.updated_at = datetime.now()
            self.db.commit()

            logger.info(f"商品信息已从万邦API更新: {product.id} - {product.title}")
        except Exception as e:
            logger.error(f"从万邦API更新商品信息失败: {e}")
            self.db.rollback()

    async def get_price_history(self, product_id: int, days: int = 30) -> List[Dict]:
        """获取价格历史"""
        since_date = datetime.now() - timedelta(days=days)
        history = self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.product_id == product_id,
                PriceHistory.timestamp >= since_date
            )
        ).order_by(PriceHistory.timestamp.desc()).all()

        return [
            {
                "date": h.timestamp.strftime("%Y-%m-%d"),
                "price": h.price,
                "original_price": h.original_price
            }
            for h in history
        ]

    async def compare_products(self, product_ids: List[int]) -> Dict:
        """商品对比"""
        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()

        comparison = {
            "products": [ProductResponse.from_orm(p) for p in products],
            "specs": {}
        }

        # 获取所有规格
        for product in products:
            specs = self.db.query(ProductSpec).filter(ProductSpec.product_id == product.id).all()
            comparison["specs"][product.id] = [
                {"name": spec.spec_name, "value": spec.spec_value}
                for spec in specs
            ]

        return comparison

    async def get_user_recommendations(self, request: RecommendationRequest) -> Dict:
        """获取用户推荐"""
        # 获取用户偏好
        preferences = self.db.query(UserPreference).filter(
            UserPreference.user_id == request.user_id
        ).all()

        # 获取购买历史
        purchase_history = self.db.query(PurchaseHistory).filter(
            PurchaseHistory.user_id == request.user_id
        ).order_by(PurchaseHistory.purchase_date.desc()).limit(10).all()

        # 生成推荐
        recommended_products = []
        reasons = []
        scores = []

        # 基于偏好的推荐
        for pref in preferences:
            if pref.preference_type == "category":
                products = self.db.query(Product).filter(
                    Product.category == pref.preference_key
                ).limit(5).all()

                for product in products:
                    recommended_products.append(product)
                    reasons.append(f"基于您对{pref.preference_key}的偏好")
                    scores.append(pref.weight)

        # 基于购买历史的推荐
        if purchase_history:
            favorite_category = max(set([p.product.category for p in purchase_history if p.product]),
                                   key=lambda x: sum(1 for p in purchase_history if p.product and p.product.category == x))

            similar_products = self.db.query(Product).filter(
                and_(
                    Product.category == favorite_category,
                    ~Product.id.in_([p.product_id for p in purchase_history])
                )
            ).limit(5).all()

            for product in similar_products:
                recommended_products.append(product)
                reasons.append(f"基于您购买的{favorite_category}商品")
                scores.append(0.8)

        # 去重和排序
        seen_products = set()
        final_recommendations = []
        final_reasons = []
        final_scores = []

        for product, reason, score in zip(recommended_products, reasons, scores):
            if product.id not in seen_products:
                seen_products.add(product.id)
                final_recommendations.append(product)
                final_reasons.append(reason)
                final_scores.append(score)

        # 按分数排序
        sorted_data = sorted(zip(final_recommendations, final_reasons, final_scores),
                           key=lambda x: x[2], reverse=True)

        return {
            "user_id": request.user_id,
            "recommendations": [ProductResponse.from_orm(p) for p, _, _ in sorted_data[:request.limit]],
            "reasons": [r for _, r, _ in sorted_data[:request.limit]],
            "scores": [s for _, _, s in sorted_data[:request.limit]]
        }

    async def analyze_purchase_behavior(self, request: PurchaseAnalysisRequest) -> Dict:
        """分析用户购买行为"""
        since_date = datetime.now() - timedelta(days=request.days)

        purchases = self.db.query(PurchaseHistory).filter(
            and_(
                PurchaseHistory.user_id == request.user_id,
                PurchaseHistory.purchase_date >= since_date
            )
        ).all()

        if not purchases:
            return {
                "user_id": request.user_id,
                "total_purchases": 0,
                "total_amount": 0.0,
                "average_satisfaction": 0.0,
                "favorite_categories": [],
                "favorite_brands": [],
                "price_preference": {"min": 0, "max": 0, "avg": 0},
                "purchase_trends": []
            }

        # 基础统计
        total_purchases = len(purchases)
        total_amount = sum(p.purchase_price for p in purchases)
        avg_satisfaction = sum(p.satisfaction_rating or 0 for p in purchases) / total_purchases

        # 类别统计
        categories = [p.product.category for p in purchases if p.product]
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        favorite_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # 品牌统计
        brands = [p.product.brand for p in purchases if p.product]
        brand_counts = {}
        for brand in brands:
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
        favorite_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # 价格偏好
        prices = [p.purchase_price for p in purchases]
        price_preference = {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices)
        }

        # 购买趋势
        purchase_trends = []
        for i in range(request.days):
            date = datetime.now() - timedelta(days=i)
            day_purchases = [p for p in purchases if p.purchase_date.date() == date.date()]
            purchase_trends.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": len(day_purchases),
                "amount": sum(p.purchase_price for p in day_purchases)
            })

        return {
            "user_id": request.user_id,
            "total_purchases": total_purchases,
            "total_amount": total_amount,
            "average_satisfaction": avg_satisfaction,
            "favorite_categories": [cat for cat, _ in favorite_categories],
            "favorite_brands": [brand for brand, _ in favorite_brands],
            "price_preference": price_preference,
            "purchase_trends": purchase_trends
        }

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """创建商品"""
        # 检查是否已存在
        existing = self.db.query(Product).filter(
            and_(
                Product.platform == product_data.platform,
                Product.product_id == product_data.product_id
            )
        ).first()

        if existing:
            # 更新现有产品
            for key, value in product_data.dict(exclude_unset=True).items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now()
            self.db.commit()
            return ProductResponse.from_orm(existing)

        # 创建新产品
        product = Product(**product_data.dict())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        return ProductResponse.from_orm(product)

    async def update_product_price(self, product_id: int, new_price: float) -> bool:
        """更新商品价格"""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False

        # 记录价格历史
        price_history = PriceHistory(
            product_id=product_id,
            price=new_price,
            original_price=product.original_price,
            discount_rate=(product.original_price - new_price) / product.original_price if product.original_price else 0
        )
        self.db.add(price_history)

        # 更新产品价格
        product.price = new_price
        product.discount_rate = (product.original_price - new_price) / product.original_price if product.original_price else 0
        product.updated_at = datetime.now()

        self.db.commit()
        return True

    async def delete_product(self, product_id: int) -> bool:
        """删除商品"""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False

        self.db.delete(product)
        self.db.commit()
        return True
