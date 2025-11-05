"""
实时购物爬虫服务
结合RAG知识库和实时爬虫的智能购物助手
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import logging
import time
import hashlib
from ..core.config import settings
from ..services.llm_service import LLMService
from ..services.enhanced_rag_service import EnhancedRAGService
from ..services.vector_service import vector_service

logger = logging.getLogger(__name__)

class ShoppingCrawlerService:
    """实时购物爬虫服务"""

    def __init__(self, db):
        self.db = db
        self.llm_service = LLMService()
        self.rag_service = EnhancedRAGService(db)
        self.session = None

        # 智能缓存系统
        self.cache = {}
        self.cache_ttl = {
            "price": 300,  # 价格缓存5分钟
            "stock": 600,  # 库存缓存10分钟
            "promotion": 1800,  # 促销信息缓存30分钟
            "search": 900,  # 搜索结果缓存15分钟
            "intent": 3600,  # 意图分析缓存1小时
            "rag": 7200  # RAG结果缓存2小时
        }

        # 重试机制配置
        self.max_retries = 3
        self.retry_delay = 1
        self.timeout = 30

        # 请求限制
        self.request_limits = {
            "jd": {"requests_per_minute": 30, "cooldown": 2},
            "taobao": {"requests_per_minute": 20, "cooldown": 3},
            "pdd": {"requests_per_minute": 25, "cooldown": 2.5}
        }

        self.request_timestamps = {platform: [] for platform in self.request_limits}

        # 支持的购物网站配置
        self.shopping_sites = {
            "jd": {
                "name": "京东",
                "base_url": "https://search.jd.com/Search",
                "product_url": "https://item.jd.com",
                "price_api": "https://p.3.cn/prices/mgets",
                "search_params": {
                    "keyword": "{query}",
                    "enc": "utf-8"
                }
            },
            "taobao": {
                "name": "淘宝",
                "base_url": "https://s.taobao.com/search",
                "product_url": "https://item.taobao.com",
                "search_params": {
                    "q": "{query}",
                    "imgfile": "",
                    "js": "1",
                    "stats_click": "search_radio_all:1",
                    "initiative_id": "staobaoz_20231101",
                    "ie": "utf8"
                }
            },
            "pdd": {
                "name": "拼多多",
                "base_url": "https://mobile.yangkeduo.com/search_result.html",
                "product_url": "https://mobile.yangkeduo.com",
                "search_params": {
                    "search_key": "{query}"
                }
            }
        }

        # User-Agent和请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def _generate_cache_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        content = "|".join(str(arg) for arg in args)
        return f"{prefix}:{hashlib.md5(content.encode()).hexdigest()}"

    def _is_cache_valid(self, cache_key: str, cache_type: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache:
            return False

        timestamp = self.cache[cache_key].get("timestamp", 0)
        ttl = self.cache_ttl.get(cache_type, 300)
        return time.time() - timestamp < ttl

    def _get_cached_data(self, cache_key: str) -> Any:
        """获取缓存数据"""
        if cache_key in self.cache:
            return self.cache[cache_key].get("data")
        return None

    def _set_cached_data(self, cache_key: str, data: Any, cache_type: str):
        """设置缓存数据"""
        self.cache[cache_key] = {
            "data": data,
            "timestamp": time.time(),
            "type": cache_type
        }

    async def _check_rate_limit(self, platform: str) -> bool:
        """检查请求频率限制"""
        if platform not in self.request_limits:
            return True

        limit = self.request_limits[platform]
        current_time = time.time()

        # 清理过期的请求记录
        self.request_timestamps[platform] = [
            timestamp for timestamp in self.request_timestamps[platform]
            if current_time - timestamp < 60
        ]

        # 检查是否超过限制
        if len(self.request_timestamps[platform]) >= limit["requests_per_minute"]:
            return False

        # 记录当前请求
        self.request_timestamps[platform].append(current_time)
        return True

    async def _wait_for_rate_limit(self, platform: str):
        """等待请求频率限制重置"""
        if not await self._check_rate_limit(platform):
            cooldown = self.request_limits[platform]["cooldown"]
            logger.info(f"Rate limit reached for {platform}, waiting {cooldown}s")
            await asyncio.sleep(cooldown)

    async def _retry_request(self, func, *args, **kwargs):
        """重试机制"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e

                delay = self.retry_delay * (2 ** attempt)  # 指数退避
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """分析用户查询意图，决定是否需要实时爬虫"""

        # 检查缓存
        cache_key = self._generate_cache_key("intent", query)
        if self._is_cache_valid(cache_key, "intent"):
            return self._get_cached_data(cache_key)

        intent_prompt = f"""
        分析用户查询的意图，判断是否需要实时数据：

        用户查询：{query}

        请分析以下方面：
        1. 是否需要实时价格信息？（如"现在多少钱"、"最低价"、"有货吗"）
        2. 是否需要库存信息？（如"有货吗"、"什么时候有货"）
        3. 是否需要促销信息？（如"有什么优惠"、"活动价格"）
        4. 是否需要比较不同平台价格？（如"哪个平台便宜"、"比价"）

        如果需要实时数据，请指出：
        - 需要爬取的商品名称
        - 需要获取的信息类型（价格/库存/促销）
        - 目标平台（京东/淘宝/拼多多）

        请以JSON格式返回：
        {{
            "needs_real_time": true/false,
            "product_name": "商品名称",
            "info_types": ["price", "stock", "promotion"],
            "target_platforms": ["jd", "taobao", "pdd"],
            "confidence": 0.85
        }}
        """

        try:
            response = await self._retry_request(
                self.llm_service.chat_completion,
                [{"role": "user", "content": intent_prompt}]
            )

            intent_text = response.get("content", "{}")
            # 尝试解析JSON
            try:
                intent_data = json.loads(intent_text)
            except json.JSONDecodeError:
                # 如果不是JSON格式，用正则表达式提取
                needs_real_time = "true" in intent_text.lower()
                intent_data = {
                    "needs_real_time": needs_real_time,
                    "product_name": query,
                    "info_types": ["price"] if needs_real_time else [],
                    "target_platforms": ["jd", "taobao"] if needs_real_time else [],
                    "confidence": 0.7
                }

            # 缓存结果
            self._set_cached_data(cache_key, intent_data, "intent")
            return intent_data

        except Exception as e:
            logger.error(f"Error analyzing query intent: {e}")
            fallback_result = {
                "needs_real_time": False,
                "product_name": query,
                "info_types": [],
                "target_platforms": [],
                "confidence": 0.0
            }
            # 缓存fallback结果以避免重复错误
            self._set_cached_data(cache_key, fallback_result, "intent")
            return fallback_result

    async def search_rag_knowledge(self, query: str) -> Dict[str, Any]:
        """从RAG知识库搜索商品信息"""

        # 检查缓存
        cache_key = self._generate_cache_key("rag", query)
        if self._is_cache_valid(cache_key, "rag"):
            return self._get_cached_data(cache_key)

        try:
            # 搜索商品基本信息
            search_results = await self._retry_request(
                self.rag_service.search_all_sources,
                query,
                limit=10,
                source_filter=["database", "rss"]
            )

            # 从数据库获取详细信息
            product_info = await self._get_product_details_from_db(query)

            # 获取历史价格数据
            price_history = await self._get_price_history_from_db(query)

            # 获取购买建议
            recommendations = await self._get_recommendations_from_db(query)

            result = {
                "rag_results": search_results,
                "product_info": product_info,
                "price_history": price_history,
                "recommendations": recommendations,
                "confidence": len(search_results) / 10.0
            }

            # 缓存结果
            self._set_cached_data(cache_key, result, "rag")
            return result

        except Exception as e:
            logger.error(f"Error searching RAG knowledge: {e}")
            fallback_result = {
                "rag_results": [],
                "product_info": {},
                "price_history": [],
                "recommendations": [],
                "confidence": 0.0
            }
            # 缓存fallback结果
            self._set_cached_data(cache_key, fallback_result, "rag")
            return fallback_result

    async def crawl_real_time_data(self, product_name: str, platforms: List[str],
                                  info_types: List[str]) -> Dict[str, Any]:
        """实时爬取商品数据"""

        results = {}
        cache_key = self._generate_cache_key("crawl", product_name, str(platforms), str(info_types))

        # 检查是否所有数据都在缓存中
        if self._is_cache_valid(cache_key, "search"):
            return self._get_cached_data(cache_key)

        for platform in platforms:
            if platform not in self.shopping_sites:
                continue

            try:
                # 检查频率限制
                await self._wait_for_rate_limit(platform)

                # 爬取平台数据
                platform_results = await self._retry_request(
                    self._crawl_platform_data,
                    platform, product_name, info_types
                )
                results[platform] = platform_results

            except Exception as e:
                logger.error(f"Error crawling {platform}: {e}")
                results[platform] = {"error": str(e)}

        # 缓存结果
        self._set_cached_data(cache_key, results, "search")
        return results

    async def _crawl_platform_data(self, platform: str, product_name: str,
                                  info_types: List[str]) -> Dict[str, Any]:
        """爬取特定平台的数据"""

        site_config = self.shopping_sites[platform]
        results = {}

        try:
            # 搜索商品
            search_url = f"{site_config['base_url']}?{self._build_search_params(site_config, product_name)}"

            async with self.session.get(search_url, timeout=self.timeout) as response:
                if response.status == 200:
                    html = await response.text()

                    # 解析搜索结果
                    search_results = self._parse_search_results(html, platform)

                    if search_results:
                        # 获取第一个商品的详细信息
                        first_product = search_results[0]

                        # 并行获取各种信息
                        tasks = []
                        if "price" in info_types:
                            tasks.append(self._get_product_price(platform, first_product["id"]))
                        if "stock" in info_types:
                            tasks.append(self._get_product_stock(platform, first_product["id"]))
                        if "promotion" in info_types:
                            tasks.append(self._get_product_promotion(platform, first_product["id"]))

                        # 等待所有任务完成
                        task_results = await asyncio.gather(*tasks, return_exceptions=True)

                        # 处理结果
                        idx = 0
                        if "price" in info_types:
                            results["price"] = task_results[idx] if not isinstance(task_results[idx], Exception) else {"error": str(task_results[idx])}
                            idx += 1
                        if "stock" in info_types:
                            results["stock"] = task_results[idx] if not isinstance(task_results[idx], Exception) else {"error": str(task_results[idx])}
                            idx += 1
                        if "promotion" in info_types:
                            results["promotion"] = task_results[idx] if not isinstance(task_results[idx], Exception) else {"error": str(task_results[idx])}

                        results["product_info"] = first_product
                        results["search_results"] = search_results
                        results["platform"] = platform
                        results["timestamp"] = datetime.now().isoformat()
                    else:
                        results["error"] = "No search results found"
                else:
                    results["error"] = f"HTTP {response.status}"

        except asyncio.TimeoutError:
            results["error"] = f"Timeout while crawling {platform}"
        except Exception as e:
            results["error"] = str(e)

        return results

    def _build_search_params(self, site_config: Dict, product_name: str) -> str:
        """构建搜索参数"""
        params = site_config.get("search_params", {})
        param_list = []

        for key, value in params.items():
            param_list.append(f"{key}={value.format(query=product_name)}")

        return "&".join(param_list)

    def _parse_search_results(self, html: str, platform: str) -> List[Dict]:
        """解析搜索结果页面"""

        soup = BeautifulSoup(html, 'html.parser')
        results = []

        try:
            if platform == "jd":
                results = self._parse_jd_results(soup)
            elif platform == "taobao":
                results = self._parse_taobao_results(soup)
            elif platform == "pdd":
                results = self._parse_pdd_results(soup)

        except Exception as e:
            logger.error(f"Error parsing {platform} results: {e}")

        return results

    def _parse_jd_results(self, soup: BeautifulSoup) -> List[Dict]:
        """解析京东搜索结果"""
        results = []

        # 查找商品列表
        items = soup.find_all('div', {'class': 'gl-item'}) or \
                soup.find_all('li', {'class': 'gl-item'})

        for item in items[:5]:  # 只取前5个结果
            try:
                # 商品ID
                item_id = item.get('data-sku', '') or item.get('sku', '')

                # 商品名称
                name_elem = item.find('div', {'class': 'p-name'}) or \
                           item.find('a', {'class': 'p-name-type-2'})
                name = name_elem.get_text(strip=True) if name_elem else ''

                # 价格
                price_elem = item.find('strong', {'class': 'J_price'}) or \
                           item.find('div', {'class': 'p-price'})
                price = price_elem.get_text(strip=True) if price_elem else '0'

                # 提取数字价格
                price_num = re.findall(r'\d+\.?\d*', price)
                price = float(price_num[0]) if price_num else 0.0

                # 商品链接
                link_elem = item.find('a', {'class': 'p-name'})
                link = link_elem.get('href', '') if link_elem else ''

                if link and not link.startswith('http'):
                    link = f"https:{link}"

                results.append({
                    "id": item_id,
                    "name": name,
                    "price": price,
                    "platform": "jd",
                    "link": link
                })

            except Exception as e:
                logger.error(f"Error parsing JD item: {e}")
                continue

        return results

    def _parse_taobao_results(self, soup: BeautifulSoup) -> List[Dict]:
        """解析淘宝搜索结果"""
        results = []

        # 淘宝页面结构较复杂，使用更通用的选择器
        items = soup.find_all('div', {'class': 'item'}) or \
                soup.find_all('div', {'data-spm': 'item'})

        for item in items[:5]:
            try:
                # 商品ID从链接中提取
                link_elem = item.find('a')
                link = link_elem.get('href', '') if link_elem else ''

                item_id = ''
                if 'id=' in link:
                    item_id = link.split('id=')[1].split('&')[0]

                # 商品名称
                name_elem = item.find('div', {'class': 'title'}) or \
                           item.find('a', {'class': 'productTitle'})
                name = name_elem.get_text(strip=True) if name_elem else ''

                # 价格
                price_elem = item.find('div', {'class': 'price'}) or \
                           item.find('span', {'class': 'price'})
                price = price_elem.get_text(strip=True) if price_elem else '0'

                # 提取数字价格
                price_num = re.findall(r'\d+\.?\d*', price)
                price = float(price_num[0]) if price_num else 0.0

                results.append({
                    "id": item_id,
                    "name": name,
                    "price": price,
                    "platform": "taobao",
                    "link": link
                })

            except Exception as e:
                logger.error(f"Error parsing Taobao item: {e}")
                continue

        return results

    def _parse_pdd_results(self, soup: BeautifulSoup) -> List[Dict]:
        """解析拼多多搜索结果"""
        results = []

        items = soup.find_all('div', {'class': 'item-goods'}) or \
                soup.find_all('a', {'class': 'goods-item'})

        for item in items[:5]:
            try:
                # 商品ID
                item_id = item.get('data-goods-id', '') or item.get('id', '')

                # 商品名称
                name_elem = item.find('div', {'class': 'goods-name'}) or \
                           item.find('span', {'class': 'name'})
                name = name_elem.get_text(strip=True) if name_elem else ''

                # 价格
                price_elem = item.find('span', {'class': 'goods-price'}) or \
                           item.find('span', {'class': 'price'})
                price = price_elem.get_text(strip=True) if price_elem else '0'

                # 提取数字价格
                price_num = re.findall(r'\d+\.?\d*', price)
                price = float(price_num[0]) if price_num else 0.0

                # 商品链接
                link_elem = item.find('a')
                link = link_elem.get('href', '') if link_elem else ''

                results.append({
                    "id": item_id,
                    "name": name,
                    "price": price,
                    "platform": "pdd",
                    "link": link
                })

            except Exception as e:
                logger.error(f"Error parsing PDD item: {e}")
                continue

        return results

    async def _get_product_price(self, platform: str, product_id: str) -> Dict[str, Any]:
        """获取商品实时价格"""

        # 检查缓存
        cache_key = self._generate_cache_key("price", platform, product_id)
        if self._is_cache_valid(cache_key, "price"):
            return self._get_cached_data(cache_key)

        if platform == "jd":
            # 京东价格API
            price_url = f"https://p.3.cn/prices/mgets?skuIds={product_id}"

            try:
                async with self.session.get(price_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            result = {
                                "current_price": float(data[0].get("p", "0")),
                                "original_price": float(data[0].get("m", "0")),
                                "discount": data[0].get("op", ""),
                                "currency": "CNY",
                                "timestamp": datetime.now().isoformat()
                            }
                            # 缓存结果
                            self._set_cached_data(cache_key, result, "price")
                            return result
            except Exception as e:
                logger.error(f"Error getting JD price: {e}")

        # 其他平台的价格解析逻辑...
        fallback_result = {
            "current_price": 0.0,
            "original_price": 0.0,
            "discount": "",
            "currency": "CNY",
            "timestamp": datetime.now().isoformat()
        }
        # 缓存fallback结果
        self._set_cached_data(cache_key, fallback_result, "price")
        return fallback_result

    async def _get_product_stock(self, platform: str, product_id: str) -> Dict[str, Any]:
        """获取商品库存信息"""

        # 检查缓存
        cache_key = self._generate_cache_key("stock", platform, product_id)
        if self._is_cache_valid(cache_key, "stock"):
            return self._get_cached_data(cache_key)

        # 这里可以实现库存查询逻辑
        result = {
            "in_stock": True,
            "stock_count": 100,
            "estimated_delivery": "现货，当天发货",
            "timestamp": datetime.now().isoformat()
        }

        # 缓存结果
        self._set_cached_data(cache_key, result, "stock")
        return result

    async def _get_product_promotion(self, platform: str, product_id: str) -> Dict[str, Any]:
        """获取商品促销信息"""

        # 检查缓存
        cache_key = self._generate_cache_key("promotion", platform, product_id)
        if self._is_cache_valid(cache_key, "promotion"):
            return self._get_cached_data(cache_key)

        # 这里可以实现促销信息查询逻辑
        result = {
            "has_promotion": False,
            "promotion_type": "",
            "discount_amount": 0.0,
            "promotion_description": "暂无促销活动",
            "valid_until": "",
            "timestamp": datetime.now().isoformat()
        }

        # 缓存结果
        self._set_cached_data(cache_key, result, "promotion")
        return result

    async def _get_product_details_from_db(self, product_name: str) -> Dict[str, Any]:
        """从数据库获取商品详细信息"""

        try:
            # 搜索商品名称
            query = f"""
            SELECT * FROM products
            WHERE name LIKE '%{product_name}%'
            OR product_id LIKE '%{product_name}%'
            LIMIT 5
            """

            # 这里应该使用数据库查询，示例返回空结果
            return {}

        except Exception as e:
            logger.error(f"Error getting product details from DB: {e}")
            return {}

    async def _get_price_history_from_db(self, product_name: str) -> List[Dict]:
        """从数据库获取价格历史"""

        try:
            # 查询价格历史
            query = f"""
            SELECT * FROM price_history
            WHERE product_id IN (
                SELECT product_id FROM products
                WHERE name LIKE '%{product_name}%'
            )
            ORDER BY date DESC
            LIMIT 10
            """

            # 这里应该使用数据库查询，示例返回空结果
            return []

        except Exception as e:
            logger.error(f"Error getting price history from DB: {e}")
            return []

    async def _get_recommendations_from_db(self, product_name: str) -> List[Dict]:
        """从数据库获取购买建议"""

        try:
            # 查询购买建议
            query = f"""
            SELECT * FROM purchase_recommendations
            WHERE recommended_product LIKE '%{product_name}%'
            LIMIT 3
            """

            # 这里应该使用数据库查询，示例返回空结果
            return []

        except Exception as e:
            logger.error(f"Error getting recommendations from DB: {e}")
            return []

    async def generate_integrated_response(self, query: str) -> Dict[str, Any]:
        """生成整合的响应"""

        try:
            # 1. 分析查询意图
            intent = await self.analyze_query_intent(query)

            # 2. 从RAG知识库搜索
            rag_data = await self.search_rag_knowledge(query)

            # 3. 如果需要实时数据，进行爬虫
            real_time_data = {}
            if intent.get("needs_real_time", False):
                product_name = intent.get("product_name", query)
                platforms = intent.get("target_platforms", ["jd", "taobao"])
                info_types = intent.get("info_types", ["price"])

                real_time_data = await self.crawl_real_time_data(
                    product_name, platforms, info_types
                )

            # 4. 生成整合响应
            response = await self._generate_response_with_ai(
                query, intent, rag_data, real_time_data
            )

            return {
                "query": query,
                "intent": intent,
                "rag_data": rag_data,
                "real_time_data": real_time_data,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating integrated response: {e}")
            return {
                "query": query,
                "error": str(e),
                "response": "抱歉，我遇到了一些问题，请稍后再试。",
                "timestamp": datetime.now().isoformat()
            }

    async def _generate_response_with_ai(self, query: str, intent: Dict,
                                       rag_data: Dict, real_time_data: Dict) -> str:
        """使用AI生成整合响应"""

        # 构建AI提示
        prompt = f"""
        你是一个专业的购物助手，需要基于以下信息为用户提供建议：

        用户问题：{query}

        查询意图分析：{json.dumps(intent, ensure_ascii=False, indent=2)}

        知识库信息（RAG）：
        - 商品基本信息：{json.dumps(rag_data.get('product_info', {}), ensure_ascii=False)}
        - 价格历史：{json.dumps(rag_data.get('price_history', []), ensure_ascii=False)}
        - 购买建议：{json.dumps(rag_data.get('recommendations', []), ensure_ascii=False)}
        - 相关知识：{len(rag_data.get('rag_results', []))}条

        实时数据：
        {json.dumps(real_time_data, ensure_ascii=False, indent=2)}

        请根据以上信息，为用户提供：
        1. 基于知识库的深度分析和建议
        2. 实时价格和库存信息（如果有）
        3. 综合购买建议
        4. 注意事项和提醒

        请用中文回答，语气友好专业，重点突出实用性建议。
        """

        try:
            response = await self.llm_service.chat_completion(
                [{"role": "user", "content": prompt}]
            )

            return response.get("content", "抱歉，我暂时无法回答这个问题。")

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "抱歉，我遇到了一些技术问题，请稍后再试。"

# 创建购物爬虫服务实例
async def get_shopping_crawler_service(db) -> ShoppingCrawlerService:
    """获取购物爬虫服务实例"""
    return ShoppingCrawlerService(db)